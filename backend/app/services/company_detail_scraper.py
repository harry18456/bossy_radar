import logging
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.db.session import engine
from app.models.company import Company
from app.services.sync_report import SourceResult, SyncReport

logger = logging.getLogger(__name__)

# MOPS Base URL (mopsov supports direct GET with parameters)
MOPSOV_BASE_URL = "https://mopsov.twse.com.tw/mops/web"

# Absolute attempt ceiling so a negative `retries` can never spin forever
# (BACKEND_AUDIT H3). After this many consecutive maintenance pages the whole
# detail sync aborts via a circuit breaker.
MAX_TOTAL_ATTEMPTS = 50
MAINTENANCE_BREAK_THRESHOLD = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://mopsov.twse.com.tw/mops/web/index",
}


class CompanyDetailScraper:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path("data/raw/company_details")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_urls(self):
        """Re-validate and normalize all URL fields in the company table.

        Sets invalid placeholder values to None and adds https:// prefix
        to bare domains. This is a one-time migration for existing data.
        """
        url_fields = ["stakeholder_url", "governance_url", "website"]

        with Session(engine) as session:
            companies = session.exec(select(Company)).all()
            fixed = 0

            for company in companies:
                changed = False
                for field in url_fields:
                    raw = getattr(company, field)
                    normalized = self._normalize_url(raw)
                    if raw != normalized:
                        setattr(company, field, normalized)
                        changed = True
                        logger.info(
                            f"[{company.code}] {field}: {raw!r} -> {normalized!r}"
                        )

                if changed:
                    session.add(company)
                    fixed += 1

            session.commit()
            logger.info(
                f"URL cleanup completed. {fixed}/{len(companies)} companies updated."
            )

    def sync_all_details(
        self,
        limit: int | None = None,
        force: bool = False,
        company_code: str | None = None,
        retries: int = 3,
        delay: float = 2.0,
        session: Session | None = None,
    ) -> SyncReport:
        """Sync detailed info (Stakeholder/Governance URLs) for companies.

        Returns a SyncReport. Individual company failures are expected during a
        long crawl and do not by themselves fail the run; the run is reported
        failed only when every attempted company failed or when the maintenance
        circuit breaker trips (BACKEND_AUDIT H3).
        """
        owns_session = session is None
        if owns_session:
            session = Session(engine)
        try:
            if company_code:
                query = select(Company).where(Company.code == company_code)
            else:
                query = select(Company)
                if not force:
                    # Only sync companies missing these URLs
                    query = query.where(
                        (Company.stakeholder_url.is_(None))
                        | (Company.governance_url.is_(None))
                    )

            companies = session.exec(query).all()
            if limit:
                companies = companies[:limit]

            retries_label = (
                retries if retries >= 0 else f"capped at {MAX_TOTAL_ATTEMPTS}"
            )
            logger.info(
                f"Starting detail sync for {len(companies)} companies... "
                f"(Retries: {retries_label}, Delay: {delay}s)"
            )

            updated = failed = maintenance = 0
            consecutive_maintenance = 0
            circuit_broken = False

            for i, company in enumerate(companies):
                try:
                    outcome = self._fetch_and_update_company(
                        session, company, retries=retries, retry_delay=delay
                    )
                except Exception as e:
                    logger.error(f"Error processing company {company.code}: {e}")
                    outcome = "failed"

                if outcome == "maintenance":
                    maintenance += 1
                    consecutive_maintenance += 1
                    if consecutive_maintenance >= MAINTENANCE_BREAK_THRESHOLD:
                        circuit_broken = True
                        logger.error(
                            f"Circuit breaker tripped after "
                            f"{consecutive_maintenance} consecutive maintenance "
                            f"pages; aborting detail sync."
                        )
                        break
                elif outcome == "updated":
                    updated += 1
                    consecutive_maintenance = 0
                else:
                    failed += 1
                    consecutive_maintenance = 0

                # MOPS has strict rate limiting, stay safe
                time.sleep(1.5)

                if (i + 1) % 10 == 0:
                    session.commit()
                    logger.info(
                        f"Progress: {i + 1}/{len(companies)} companies processed."
                    )

            session.commit()
            logger.info("Company detail sync completed.")

            report = SyncReport(circuit_broken=circuit_broken)
            attempted = updated + failed + maintenance
            error = None
            if circuit_broken:
                error = "circuit breaker tripped on consecutive maintenance pages"
            elif attempted > 0 and updated == 0:
                error = "all attempted companies failed"
            report.add(
                SourceResult(
                    name="company-details",
                    success=error is None,
                    rows_written=updated,
                    rows_skipped=failed + maintenance,
                    error=error,
                )
            )
            return report
        finally:
            if owns_session:
                session.close()

    def _fetch_and_update_company(
        self,
        session: Session,
        company: Company,
        retries: int = 3,
        retry_delay: float = 2.0,
    ) -> str:
        """Fetch t05st03 for a company and update its URLs.

        Returns an outcome string: "updated", "maintenance", or "failed".
        """
        # Pattern verified: mopsov supports direct GET
        url = f"{MOPSOV_BASE_URL}/t05st03"
        params = {
            "step": "1",
            "firstin": "1",
            "off": "1",
            "queryName": "co_id",
            "t05st03_ck": "1",
            "co_id": company.code,
        }

        # Cache path
        cache_path = self.data_dir / f"{company.code}.html"

        # 1. Check Cache (Skip if exists and not empty)
        from_cache = cache_path.exists() and cache_path.stat().st_size > 1000
        if from_cache:
            logger.debug(f"Using cache for {company.code}")
            html = cache_path.read_text(encoding="utf-8")
        else:
            # 2. Fetch from Network with bounded retry
            html = self._fetch_with_retry(
                url, params, retries=retries, delay=retry_delay
            )
            if html is None:
                logger.warning(f"Failed to fetch data for {company.code}")
                return "failed"

        # A maintenance page is HTTP 200 but carries no real data: never cache
        # or parse it, and surface it so the circuit breaker can react.
        if self._is_maintenance_page(html):
            logger.warning(f"Maintenance page returned for {company.code}")
            return "maintenance"

        if not from_cache:
            cache_path.write_text(html, encoding="utf-8")

        # 3. Parse
        soup = BeautifulSoup(html, "html.parser")

        # The page uses a structure with labels in spans/tds
        stakeholder_url = self._extract_url_by_label(
            soup, "公司網站內利害關係人專區網址"
        )
        governance_url = self._extract_url_by_label(
            soup, "公司網站內公司治理資訊專區網址"
        )

        # Always update (even to None) so invalid values get cleared
        company.stakeholder_url = stakeholder_url
        company.governance_url = governance_url

        session.add(company)
        return "updated"

    @staticmethod
    def _is_maintenance_page(html: str) -> bool:
        """MOPS serves rate-limit / maintenance notices as HTTP 200 pages."""
        return "服務暫時無法提供" in html or "請稍後再試" in html

    def _fetch_with_retry(
        self,
        url: str,
        params: dict,
        retries: int = 3,
        delay: float = 2.0,
        max_delay: float = 60.0,
    ) -> str | None:
        """Fetch a URL with bounded exponential-backoff retry.

        A non-negative `retries` yields up to ``retries + 1`` attempts. A
        negative `retries` means "retry hard", but is still capped at
        MAX_TOTAL_ATTEMPTS so the loop can never spin forever (BACKEND_AUDIT
        H3). Maintenance pages are HTTP 200 and are returned verbatim here; the
        caller detects them so a rate-limited host is not retried into the
        ground. Returns the response text, or None when every attempt failed.
        """
        max_attempts = (retries + 1) if retries >= 0 else MAX_TOTAL_ATTEMPTS
        for attempt in range(1, max_attempts + 1):
            try:
                with httpx.Client(timeout=30, follow_redirects=True) as client:
                    response = client.get(url, headers=HEADERS, params=params)
                    response.raise_for_status()
                    return response.text
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt >= max_attempts:
                    logger.error(f"Failed after {attempt} attempt(s): {e}")
                    return None

                wait_time = min(delay * (2 ** (attempt - 1)), max_delay)
                logger.warning(
                    f"Attempt {attempt}/{max_attempts} failed: {e}. "
                    f"Retrying in {wait_time}s... (Target: {params.get('co_id')})"
                )
                time.sleep(wait_time)

        return None

    # Values that MOPS uses as placeholders instead of real URLs
    INVALID_URL_VALUES = frozenset(
        {
            "無",
            "不適用",
            "na",
            "n/a",
            "n.a.",
            "none",
            "nil",
            "no",
            "0",
            "-",
            "尚未設置",
            "建置中",
            "尚未建置",
            "尚未建立",
            "待完成",
            "架設中",
            "/",
            "..",
            ".",
        }
    )

    @staticmethod
    def _normalize_url(value: str | None) -> str | None:
        """Validate and normalize a URL value from MOPS.

        Returns None for invalid/placeholder values, auto-prefixes https://
        for bare domains, and returns valid URLs as-is.
        """
        if not value:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        # Check against known placeholder values (case-insensitive)
        lower = cleaned.lower()
        if lower in CompanyDetailScraper.INVALID_URL_VALUES:
            return None

        # Reject dangerous protocols (defense-in-depth against XSS)
        if any(lower.startswith(p) for p in ("javascript:", "data:", "vbscript:")):
            return None

        # Already a proper URL
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            return cleaned

        # Looks like a bare domain (contains a dot) → add https://
        if "." in cleaned:
            return f"https://{cleaned}"

        # No protocol and no dot → not a valid URL
        return None

    def _extract_url_by_label(self, soup: BeautifulSoup, label_text: str) -> str | None:
        """Find the link corresponding to a label in the MOPS layout."""
        # Some labels have <br> in them, so we strip them when comparing
        # OR we search for partial matches.

        target_cells = soup.find_all(["th", "td"])
        value = None

        for cell in target_cells:
            # Get text and clean it (including internal whitespace/newlines)
            cell_text = "".join(cell.get_text().split())
            if label_text in cell_text:
                # Value is usually in the next sibling td
                next_td = cell.find_next_sibling("td")
                if next_td:
                    link = next_td.find("a")
                    if link and "href" in link.attrs:
                        value = link["href"]
                    else:
                        value = next_td.get_text(strip=True).replace(
                            "\xa0", ""
                        )  # Remove &nbsp;
                    break

        return self._normalize_url(value)
