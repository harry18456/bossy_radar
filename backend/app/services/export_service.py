import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, func, select

from app.db.session import engine
from app.models.company import Company
from app.models.employee_benefit import EmployeeBenefit
from app.models.environmental_violation import EnvironmentalViolation
from app.models.non_manager_salary import NonManagerSalary
from app.models.salary_adjustment import SalaryAdjustment
from app.models.violation import Violation
from app.models.welfare_policy import WelfarePolicy
from app.schemas.aggregation import (
    CompanyProfileResponse,
    YearlySummaryItem,
)
from app.schemas.company import CompanyCatalogItem, CompanyResponse
from app.schemas.environmental_violation import EnvironmentalViolationPublic
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    SalaryAdjustmentResponse,
    WelfarePolicyResponse,
)
from app.schemas.system import SyncStatusItem, SyncStatusResponse
from app.services.leaderboard_builder import build_leaderboard_response
from app.services.yearly_summary_builder import build_yearly_summary_items

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(self, output_dir: Path):
        # The live directory is only ever renamed during the swap, never
        # deleted recursively; all writes go to a temp sibling first.
        self._final_output_dir = Path(output_dir)
        self.output_dir = self._final_output_dir
        self.companies_dir = self.output_dir / "companies"

    def _save_json(self, path: Path, data: Any):
        """Write JSON atomically: temp file in the same dir, then os.replace."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Check if it's a Pydantic model (or list of them) or dict
        if isinstance(data, list):
            # If list of models, dump each
            json_data = [
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                for item in data
            ]
        elif hasattr(data, "model_dump"):
            json_data = data.model_dump(mode="json")
        else:
            json_data = data

        tmp_path = path.with_name(path.name + ".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise

    def _service_dir(self, suffix: str) -> Path:
        return self._final_output_dir.with_name(self._final_output_dir.name + suffix)

    def _remove_service_dir(self, path: Path):
        """Delete a directory only if it is one of our own .tmp/.bak siblings."""
        resolved = Path(path).resolve()
        allowed = {
            self._service_dir(".tmp").resolve(),
            self._service_dir(".bak").resolve(),
        }
        if resolved not in allowed:
            raise ValueError(f"Refusing to delete non-service-owned path: {resolved}")
        if resolved.exists():
            shutil.rmtree(resolved)

    def export_all(self, session: Session | None = None):
        if session is not None:
            self._export_all(session)
            return
        with Session(engine) as own_session:
            self._export_all(own_session)

    def _export_all(self, session: Session):
        final_dir = self._final_output_dir
        tmp_dir = self._service_dir(".tmp")
        bak_dir = self._service_dir(".bak")

        # Recover leftovers from a previously crashed run.
        self._remove_service_dir(tmp_dir)
        self._remove_service_dir(bak_dir)

        tmp_dir.mkdir(parents=True)
        original_output_dir = self.output_dir
        original_companies_dir = self.companies_dir
        self.output_dir = tmp_dir
        self.companies_dir = tmp_dir / "companies"
        self.companies_dir.mkdir()

        try:
            logger.info("Starting Full Export...")
            self.export_company_catalog(session)
            self.export_yearly_summaries(session)
            self.export_system_status(session)
            self.export_company_details(session)
            self.export_leaderboards(session)
        except BaseException:
            self._remove_service_dir(tmp_dir)
            raise
        finally:
            self.output_dir = original_output_dir
            self.companies_dir = original_companies_dir

        # Atomic swap: the live dir always exists either under its own name
        # or as the complete .bak copy at every point in this sequence.
        if final_dir.exists():
            final_dir.rename(bak_dir)
        tmp_dir.rename(final_dir)
        self._remove_service_dir(bak_dir)
        logger.info("Full Export Completed.")

    def export_company_catalog(self, session: Session):
        logger.info("Exporting Company Catalog...")
        companies = session.exec(select(Company)).all()
        catalog_items = []
        for c in companies:
            catalog_items.append(
                CompanyCatalogItem(
                    code=c.code,
                    name=c.name,
                    abbreviation=c.abbreviation,
                    market_type=c.market_type,
                    industry=c.industry,
                    tax_id=c.tax_id,
                    capital=float(c.capital) if c.capital is not None else None,
                    establishment_date=c.establishment_date.isoformat()
                    if c.establishment_date
                    else None,
                    listing_date=c.listing_date.isoformat() if c.listing_date else None,
                )
            )

        self._save_json(self.output_dir / "company-catalog.json", catalog_items)
        logger.info(f"Exported {len(catalog_items)} companies to company-catalog.json")

    def export_company_details(self, session: Session):
        logger.info("Exporting Company Details...")
        self.companies_dir.mkdir(parents=True, exist_ok=True)
        companies = session.exec(select(Company)).all()
        count = 0

        for company in companies:
            profile = self._get_company_profile_data(session, company)
            self._save_json(self.companies_dir / f"{company.code}.json", profile)
            count += 1
            if count % 100 == 0:
                logger.info(f"Exported {count} company profiles...")

        logger.info(f"Exported {count} company profiles total.")

    def _get_company_profile_data(
        self, session: Session, company: Company
    ) -> CompanyProfileResponse:
        # Reusing logic from app/api/routes/aggregation.py
        company_code = company.code

        violations = session.exec(
            select(Violation)
            .where(Violation.company_code == company_code)
            .order_by(Violation.penalty_date.desc())
        ).all()

        employee_benefits = session.exec(
            select(EmployeeBenefit)
            .where(EmployeeBenefit.company_code == company_code)
            .order_by(EmployeeBenefit.year.desc())
        ).all()

        non_manager_salaries = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code == company_code)
            .order_by(NonManagerSalary.year.desc())
        ).all()

        welfare_policies = session.exec(
            select(WelfarePolicy)
            .where(WelfarePolicy.company_code == company_code)
            .order_by(WelfarePolicy.year.desc())
        ).all()

        salary_adjustments = session.exec(
            select(SalaryAdjustment)
            .where(SalaryAdjustment.company_code == company_code)
            .order_by(SalaryAdjustment.year.desc())
        ).all()

        environmental_violations = session.exec(
            select(EnvironmentalViolation)
            .where(EnvironmentalViolation.company_code == company_code)
            .order_by(EnvironmentalViolation.penalty_date.desc())
        ).all()

        return CompanyProfileResponse(
            company=CompanyResponse.model_validate(company),
            violations=violations,
            employee_benefits=[
                EmployeeBenefitResponse.model_validate(x) for x in employee_benefits
            ],
            non_manager_salaries=[
                NonManagerSalaryResponse.model_validate(x) for x in non_manager_salaries
            ],
            welfare_policies=[
                WelfarePolicyResponse.model_validate(x) for x in welfare_policies
            ],
            salary_adjustments=[
                SalaryAdjustmentResponse.model_validate(x) for x in salary_adjustments
            ],
            environmental_violations=[
                EnvironmentalViolationPublic.model_validate(x)
                for x in environmental_violations
            ],
        )

    def export_yearly_summaries(self, session: Session):
        logger.info("Exporting Yearly Summaries...")
        # Assembly is shared with the aggregation route via
        # app/services/yearly_summary_builder.py; the exporter is the
        # include=all full dump grouped by year (BACKEND_AUDIT NF1/H8).
        yearly_summaries_dir = self.output_dir / "yearly-summaries"
        yearly_summaries_dir.mkdir(parents=True, exist_ok=True)

        items = build_yearly_summary_items(session, include=["all"])

        items_by_year: dict[int, list[YearlySummaryItem]] = {}
        for item in items:
            items_by_year.setdefault(item.year, []).append(item)

        # Index metadata is derived from the builder output, never re-queried.
        years_desc = sorted(items_by_year, reverse=True)
        year_stats = []
        total_count = 0
        for year in years_desc:
            year_items = items_by_year[year]
            self._save_json(yearly_summaries_dir / f"{year}.json", year_items)
            year_stats.append({"year": year, "count": len(year_items)})
            total_count += len(year_items)
            logger.info(f"Exported {len(year_items)} items for year {year}")

        index_data = {
            "years": years_desc,
            "year_stats": year_stats,
            "total_count": total_count,
            "generated_at": datetime.now().isoformat(),
        }
        self._save_json(yearly_summaries_dir / "index.json", index_data)

        logger.info(
            f"Exported {total_count} yearly summary items across "
            f"{len(years_desc)} years."
        )

    def export_system_status(self, session: Session):
        logger.info("Exporting System Status...")

        status_response = SyncStatusResponse(
            companies={}, violations={}, environmental_violations={}, mops={}
        )

        # Check companies
        last_company = session.exec(
            select(Company).order_by(Company.last_updated.desc())
        ).first()
        company_count = session.exec(select(func.count(Company.code))).one()
        status_response.companies["all"] = SyncStatusItem(
            last_updated=last_company.last_updated if last_company else None,
            count=company_count,
        )

        # Check violations
        last_violation = session.exec(
            select(Violation).order_by(Violation.last_updated.desc())
        ).first()
        violation_count = session.exec(select(func.count(Violation.id))).one()
        status_response.violations["all"] = SyncStatusItem(
            last_updated=last_violation.last_updated if last_violation else None,
            count=violation_count,
        )

        # Check environmental violations
        last_env = session.exec(
            select(EnvironmentalViolation).order_by(
                EnvironmentalViolation.last_updated.desc()
            )
        ).first()
        env_count = session.exec(select(func.count(EnvironmentalViolation.id))).one()
        status_response.environmental_violations["all"] = SyncStatusItem(
            last_updated=last_env.last_updated if last_env else None, count=env_count
        )

        # Check MOPS
        last_benefit = session.exec(
            select(EmployeeBenefit).order_by(EmployeeBenefit.last_updated.desc())
        ).first()
        benefit_count = session.exec(select(func.count(EmployeeBenefit.id))).one()
        status_response.mops["employee_benefit"] = SyncStatusItem(
            last_updated=last_benefit.last_updated if last_benefit else None,
            count=benefit_count,
        )

        self._save_json(self.output_dir / "system-status.json", status_response)
        logger.info("Exported system-status.json")

    def export_leaderboards(self, session: Session):
        """匯出首頁排行榜資料（與 leaderboard route 共用 builder，見
        app/services/leaderboard_builder.py；parity 測試鎖定兩者一致）"""
        logger.info("Exporting Leaderboards...")
        response = build_leaderboard_response(session)
        self._save_json(self.output_dir / "leaderboards.json", response)
        logger.info("Exported leaderboards.json")
