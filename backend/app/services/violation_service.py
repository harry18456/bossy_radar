import json
import logging
import re
from datetime import date
from pathlib import Path

from sqlmodel import Session, select

from app.db.session import engine
from app.models.company import Company
from app.models.violation import Violation
from app.services.db_upsert import model_values, upsert_on_conflict
from app.services.dedup import violation_dedup_key
from app.services.sync_report import SourceResult, SyncReport

logger = logging.getLogger(__name__)


class ViolationService:
    def __init__(self):
        # Source Mapping for logging/debugging
        self.sources = [
            "LaborStandards",
            "GenderEquality",
            "Pension",
            "EmploymentService",
            "OccupationalSafety",
            "Insurance",
            "MiddleAged",
            "Union",
        ]

    def sync_violations(self, data_dir: Path, target_sources: list[str]) -> SyncReport:
        """Sync violations from downloaded JSONs to DB.

        Returns a SyncReport. Each source is committed independently; a source
        that raises rolls back both sessions and is recorded as failed so the
        CLI can exit non-zero (BACKEND_AUDIT M11).
        """
        # Schema is managed by Alembic migrations (run `alembic upgrade head`).
        from app.db.session import archive_engine

        report = SyncReport()

        with Session(engine) as session, Session(archive_engine) as archive_session:
            # 1. Pre-load companies for linking optimization
            # Fetch essential fields: code, name, abbreviation, chairman
            # For 2000 companies this is fine. If 100k+, need smarter lookup.
            companies = session.exec(select(Company)).all()

            # Index companies for fast lookup
            company_map = {}  # name -> code
            company_branch_map = []  # (name, code) list for startswith check
            company_chairman_map = {}  # chairman -> list of (name, code)

            for c in companies:
                # Exact Match
                company_map[c.name] = c.code
                if c.abbreviation:
                    company_map[c.abbreviation] = c.code

                # Branch Match Prep
                # Remove generic suffixes for cleaner matching? For now use full name
                company_branch_map.append((c.name, c.code))

                # Chairman Match Prep
                if c.chairman:
                    if c.chairman not in company_chairman_map:
                        company_chairman_map[c.chairman] = []
                    company_chairman_map[c.chairman].append((c.name, c.code))

            for source in target_sources:
                file_path = data_dir / f"{source}.json"
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    report.add(
                        SourceResult(name=source, success=False, error="file not found")
                    )
                    continue

                try:
                    logger.info(f"Processing {source} violations from {file_path}")
                    violations, skipped = self._parse_json(file_path, source)
                    logger.info(
                        f"Parsed {len(violations)} records "
                        f"({skipped} skipped). Linking and upserting..."
                    )

                    written = self._upsert_violations(
                        session,
                        archive_session,
                        violations,
                        company_map,
                        company_branch_map,
                        company_chairman_map,
                    )
                    session.commit()
                    archive_session.commit()
                    report.add(
                        SourceResult(
                            name=source,
                            success=True,
                            rows_written=written,
                            rows_skipped=skipped,
                        )
                    )
                except Exception as e:
                    session.rollback()
                    archive_session.rollback()
                    logger.error(f"Error syncing {source}: {e}")
                    report.add(SourceResult(name=source, success=False, error=str(e)))

        return report

    def _parse_json(self, file_path: Path, source: str) -> tuple[list[Violation], int]:
        records = []
        skipped = 0
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning(f"{source} data is not a list")
                return [], 0

            for i, row in enumerate(data):
                try:
                    # 1. Company Name Strategy
                    c_name = (
                        row.get("事業單位名稱(公佈版)")
                        or row.get("事業單位名稱")
                        or row.get("事業單位名稱或負責人")
                        or ""
                    ).strip()

                    if not c_name:
                        continue

                    # 2. Date Parsing
                    penalty_date = self._parse_roc_date(row.get("處分日期"))
                    announcement_date = self._parse_roc_date(row.get("公告日期"))

                    # 3. Fine Parsing
                    fine = self._parse_fine(row.get("罰鍰金額"))

                    # 4. Other fields
                    violation = Violation(
                        company_name=c_name,
                        data_source=source,
                        authority=row.get("主管機關"),
                        penalty_date=penalty_date,
                        announcement_date=announcement_date,
                        disposition_no=(row.get("處分字號") or "").strip(),
                        law_article=(
                            row.get("違反法規條款") or row.get("違法法規法條") or ""
                        ).strip(),
                        violation_content=(row.get("違反法規內容") or "").strip(),
                        fine_amount=fine,
                    )
                    records.append(violation)
                except Exception as e:
                    skipped += 1
                    logger.warning(f"Skipped {source} row {i}: {e}")
                    continue
        except Exception as e:
            # A whole-file parse failure (unreadable / corrupt / non-JSON) is a
            # source failure, not an empty success — surface it so the caller
            # records the source as failed and the CLI exits non-zero (M11).
            logger.error(f"Error parsing {source}: {e}")
            raise

        return records, skipped

    def _upsert_violations(
        self,
        session: Session,
        archive_session: Session,
        violations: list[Violation],
        company_map: dict[str, str],
        company_branch_map: list[tuple],
        company_chairman_map: dict[str, list],
    ) -> int:
        count = 0
        linked_count = 0

        for v in violations:
            # 1. Linking Logic
            matched_code = None

            # Level 1: Exact Match
            if v.company_name in company_map:
                matched_code = company_map[v.company_name]

            # Level 2: Branch Match (StartsWith)
            if not matched_code:
                # Iterate all companies (slow? 1000 companies * 50000 violations = 50M checks. might need optimization)
                # But typically violation batch is per-day or file based.
                # Optimization: Only check if c_name is longer than company name
                for c_name, c_code in company_branch_map:
                    if v.company_name.startswith(c_name) and len(v.company_name) > len(
                        c_name
                    ):
                        matched_code = c_code
                        break

            # Level 3: Chairman Match (Only for specific sources or "Person Names")
            if not matched_code and v.company_name in company_chairman_map:
                candidates = company_chairman_map[v.company_name]
                if len(candidates) == 1:
                    # Only link if unique chairman. If multiple "Chen, Tai-Ming", don't guess.
                    matched_code = candidates[0][1]

            if matched_code:
                v.company_code = matched_code
                linked_count += 1
                target_session = session
            else:
                target_session = archive_session

            # 2. Upsert Logic — a deterministic dedup_key (synthetic when the
            # disposition number is empty) makes every violation idempotent at
            # the DB layer, including the empty-disposition rows that used to be
            # re-inserted on every sync (BACKEND_AUDIT H5).
            v.dedup_key = violation_dedup_key(
                data_source=v.data_source,
                disposition_no=v.disposition_no,
                company_name=v.company_name,
                penalty_date=v.penalty_date,
                law_article=v.law_article,
                fine_amount=v.fine_amount,
            )
            upsert_on_conflict(
                target_session,
                Violation,
                model_values(v),
                conflict_cols=("dedup_key",),
                no_update=("id", "created_at", "dedup_key"),
            )
            count += 1

            # Progress tracking only; commits are owned by the per-source
            # caller so a failed source can be rolled back cleanly.
            if count % 1000 == 0:
                logger.info(f"Processed {count} records...")

        logger.info(
            f"Processed {count} violations. Linked {linked_count} to companies."
        )
        return count

    def _parse_roc_date(self, date_str: str) -> date | None:
        """
        Convert ROC date string (e.g. '1150126') to date object.
        Reusing similar logic but handling int/str inputs.
        """
        if not date_str:
            return None

        try:
            s = str(date_str).strip()
            if not s or s.lower() == "null" or s == "0":
                return None

            # Sometimes format is YYYYMMDD? Mol usually ROC.
            if len(s) < 6:
                return None

            year_len = len(s) - 4
            year_roc = int(s[:year_len])
            month = int(s[year_len : year_len + 2])
            day = int(s[year_len + 2 :])
            actual_year = year_roc + 1911 if year_roc < 1000 else year_roc
            return date(actual_year, month, day)
        except Exception:
            return None

    def _parse_fine(self, fine_str: str) -> int:
        if not fine_str:
            return 0
        try:
            # Remove non-digits
            digits = re.sub(r"[^\d]", "", str(fine_str))
            if digits:
                return int(digits)
            return 0
        except Exception:
            return 0
