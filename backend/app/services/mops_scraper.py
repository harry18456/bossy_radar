"""
MOPS (公開資訊觀測站) 員工薪資/福利資料爬蟲服務

Endpoints:
- t100sb14: 財務報告附註揭露之員工福利(薪資)資訊
- t100sb15: 非擔任主管職務之全時員工薪資資訊
- t100sb13: 員工福利政策及權益維護措施揭露-彙總資料查詢
- t222sb01: 基層員工調整薪資或分派酬勞
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, SQLModel

from app.db.session import archive_engine, engine
from app.models.employee_benefit import EmployeeBenefit
from app.models.non_manager_salary import NonManagerSalary
from app.models.salary_adjustment import SalaryAdjustment
from app.models.welfare_policy import WelfarePolicy
from app.services.company_matcher import CompanyMatcher
from app.services.db_upsert import model_values, upsert_on_conflict
from app.services.sync_report import SourceResult, SyncReport

logger = logging.getLogger(__name__)

# MOPS Base URL
MOPS_BASE_URL = "https://mopsov.twse.com.tw/mops/web"

# HTTP Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://mopsov.twse.com.tw/mops/web/index",
    "Origin": "https://mopsov.twse.com.tw",
    "Content-Type": "application/x-www-form-urlencoded",
}

# Data Source Config
DATA_SOURCES = {
    "t100sb14": {
        "name": "財務報告附註揭露之員工福利(薪資)資訊",
        "endpoint": "ajax_t100sb14",
        "year_param": "RYEAR",
        "step": "1",
        "firstin": "1",
        "extra_params": {"code": ""},
        "model": EmployeeBenefit,
    },
    "t100sb15": {
        "name": "非擔任主管職務之全時員工薪資資訊",
        "endpoint": "ajax_t100sb15",
        "year_param": "RYEAR",  # 使用 RYEAR 而非 year
        "step": "1",
        "firstin": "1",
        "extra_params": {"code": ""},
        "model": NonManagerSalary,
    },
    "t100sb13": {
        "name": "員工福利政策及權益維護措施揭露",
        "endpoint": "ajax_t100sb13",
        "year_param": "year",  # t100sb13 使用 year
        "step": "0",  # t100sb13 使用 step=0
        "firstin": "ture",  # 網站有 typo，必須用 'ture' 而非 'true'
        "extra_params": {"off": "1"},
        "model": WelfarePolicy,
    },
    "t222sb01": {
        "name": "基層員工調整薪資或分派酬勞",
        "endpoint": "ajax_t222sb01",
        "year_param": "RYEAR",  # 使用 RYEAR
        "step": "1",
        "firstin": "1",
        "extra_params": {"CODE": ""},  # 注意是大寫 CODE
        "model": SalaryAdjustment,
    },
}


class MopsScraper:
    def __init__(self, data_dir: Path | None = None):
        """Initialize MOPS Scraper.

        Args:
            data_dir: Base directory for raw data caching (default: data/raw/mops)
        """
        self.data_dir = data_dir or Path("data/raw/mops")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_current_roc_year(self) -> int:
        """Get current ROC year (民國年)."""
        return datetime.now().year - 1911

    def sync_all(self, start_year: int | None = None, end_year: int | None = None):
        """Sync all MOPS data sources.

        Args:
            start_year: Start ROC year (default: current_year - 4)
            end_year: End ROC year (default: current_year)
        """
        current_roc = self.get_current_roc_year()
        start_year = start_year or 107
        end_year = end_year or current_roc

        years = list(range(start_year, end_year + 1))
        markets = ["sii", "otc"]

        logger.info(f"Starting MOPS sync for years {years}, markets {markets}")

        report = SyncReport()
        report.add(self.sync_employee_benefit(years, markets))
        report.add(self.sync_non_manager_salary(years, markets))
        report.add(self.sync_welfare_policy(years, markets))
        report.add(self.sync_salary_adjustment(years, markets))

        logger.info("MOPS sync completed")
        return report

    def sync_employee_benefit(
        self, years: list[int], markets: list[str]
    ) -> SourceResult:
        """Sync t100sb14 data."""
        return self._sync_data_source("t100sb14", years, markets)

    def sync_non_manager_salary(
        self, years: list[int], markets: list[str]
    ) -> SourceResult:
        """Sync t100sb15 data."""
        return self._sync_data_source("t100sb15", years, markets)

    def sync_welfare_policy(self, years: list[int], markets: list[str]) -> SourceResult:
        """Sync t100sb13 data."""
        return self._sync_data_source("t100sb13", years, markets)

    def sync_salary_adjustment(
        self, years: list[int], markets: list[str]
    ) -> SourceResult:
        """Sync t222sb01 data."""
        return self._sync_data_source("t222sb01", years, markets)

    def _sync_data_source(
        self,
        source_key: str,
        years: list[int],
        markets: list[str],
        session: Session | None = None,
        archive_session: Session | None = None,
    ) -> SourceResult:
        """Generic sync for one data source. Returns a SourceResult.

        Each (year, market) unit is committed on its own; a unit that raises
        rolls back BOTH sessions before the next unit runs, so a failure can
        never poison later units with a PendingRollbackError (BACKEND_AUDIT
        M4/NF3).
        """
        config = DATA_SOURCES[source_key]
        logger.info(f"Syncing {config['name']} ({source_key})")

        # When sessions are injected the caller owns the schema; only touch the
        # real engines when we create our own sessions.
        if session is not None and archive_session is not None:
            return self._sync_units(
                source_key, config, years, markets, session, archive_session
            )

        # Schema is managed by Alembic migrations (run `alembic upgrade head`).
        with Session(engine) as own_session, Session(archive_engine) as own_archive:
            return self._sync_units(
                source_key, config, years, markets, own_session, own_archive
            )

    def _sync_units(
        self,
        source_key: str,
        config: dict,
        years: list[int],
        markets: list[str],
        session: Session,
        archive_session: Session,
    ) -> SourceResult:
        # Single shared matcher (change 5b): MOPS raw_company_code uses the
        # code layer; name/branch share the same implementation as labor/env.
        matcher = CompanyMatcher(session)

        written = 0
        skipped = 0
        failed_units: list[str] = []

        for year in years:
            for market in markets:
                try:
                    unit_written, unit_skipped = self._fetch_and_process(
                        source_key=source_key,
                        config=config,
                        year=year,
                        market=market,
                        session=session,
                        archive_session=archive_session,
                        matcher=matcher,
                    )
                    session.commit()
                    archive_session.commit()
                    written += unit_written
                    skipped += unit_skipped
                except Exception as e:
                    # Roll both sessions back so the next unit starts clean.
                    session.rollback()
                    archive_session.rollback()
                    logger.error(f"Error processing {source_key} {market} {year}: {e}")
                    failed_units.append(f"{market}/{year}: {e}")
                    continue

        error = None
        if failed_units:
            error = f"{len(failed_units)} unit(s) failed: " + "; ".join(
                failed_units[:5]
            )
        return SourceResult(
            name=f"{source_key} ({config['name']})",
            success=not failed_units,
            rows_written=written,
            rows_skipped=skipped,
            error=error,
        )

    def _fetch_and_process(
        self,
        source_key: str,
        config: dict,
        year: int,
        market: str,
        session: Session,
        archive_session: Session,
        matcher: CompanyMatcher,
    ):
        """Fetch HTML from MOPS and process data."""
        # Build payload using config
        payload = {
            "encodeURIComponent": "1",
            "step": config.get("step", "1"),
            "firstin": config.get("firstin", "1"),
            "TYPEK": market,
            config["year_param"]: str(year),
        }

        # Add extra params from config
        if "extra_params" in config:
            payload.update(config["extra_params"])

        url = f"{MOPS_BASE_URL}/{config['endpoint']}"

        # Cache path
        date_str = datetime.now().strftime("%Y%m%d")
        cache_dir = self.data_dir / date_str
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{source_key}_{market}_{year}.html"

        if cache_path.exists():
            logger.info(f"Loading from cache: {cache_path}")
            html = cache_path.read_text(encoding="utf-8")
            records = self._parse_table(html, source_key, year, market)
            if not records:
                # A cached file that parses to nothing may be a stale maintenance
                # page or garbage from a prior bad run; drop it and refetch once
                # (BACKEND_AUDIT M5).
                logger.warning(
                    f"Cache {cache_path.name} parsed 0 records; refetching once."
                )
                cache_path.unlink(missing_ok=True)
                html = self._fetch_html(url, payload)
                self._write_cache(cache_path, html)
                records = self._parse_table(html, source_key, year, market)
        else:
            html = self._fetch_html(url, payload)
            self._write_cache(cache_path, html)
            records = self._parse_table(html, source_key, year, market)

        logger.info(f"Parsed {len(records)} records from {source_key} {market} {year}")

        if not records:
            # A genuinely empty unit (no data for this year/market) is not a
            # failure; only invalid/maintenance content (rejected by _write_cache)
            # raises.
            return (0, 0)

        # Upsert to DB
        return self._upsert_data(
            session=session,
            archive_session=archive_session,
            records=records,
            model_class=config["model"],
            matcher=matcher,
        )

    @staticmethod
    def _is_valid_mops_html(html: str) -> bool:
        """MOPS serves rate-limit/maintenance notices as HTTP 200 pages."""
        if not html or not html.strip():
            return False
        if "服務暫時無法提供" in html or "請稍後再試" in html:
            return False
        return "<table" in html.lower()

    def _fetch_html(self, url: str, payload: dict) -> str:
        logger.info(f"Fetching {url} ...")
        try:
            with httpx.Client(timeout=60, follow_redirects=True) as client:
                response = client.post(url, headers=HEADERS, data=payload)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"HTTP error: {e}")
            raise

    def _write_cache(self, cache_path: Path, html: str) -> None:
        """Persist HTML only after validating it; reject maintenance/garbage."""
        if not self._is_valid_mops_html(html):
            raise ValueError(
                f"Refusing to cache invalid/maintenance MOPS content: {cache_path.name}"
            )
        cache_path.write_text(html, encoding="utf-8")
        logger.info(f"Cached to {cache_path}")

    def _parse_table(
        self, html: str, source_key: str, year: int, market: str
    ) -> list[dict]:
        """Parse MOPS HTML table to records."""
        soup = BeautifulSoup(html, "html.parser")

        # Find data table - look for tables with width:100% style or tables with tblHead class headers
        tables = soup.find_all("table")
        table = None

        for t in tables:
            # Check for tr with tblHead class (t100sb13, t222sb01 style)
            if t.find("tr", class_="tblHead"):
                table = t
                break
            # Check if this table has data rows (td elements with text-align styling)
            if t.find("td", style=lambda x: x and "text-align" in x):
                table = t
                break
            # Or check for th with tblHead class
            if t.find("th", class_="tblHead"):
                table = t
                break

        if not table:
            logger.warning(f"No data table found for {source_key}")
            return []

        # Parse based on source type
        if source_key == "t100sb14":
            return self._parse_t100sb14(table, year, market)
        elif source_key == "t100sb15":
            return self._parse_t100sb15(table, year, market)
        elif source_key == "t100sb13":
            return self._parse_t100sb13(table, year, market)
        elif source_key == "t222sb01":
            return self._parse_t222sb01(table, year, market)

        return []

    def _parse_t100sb14(self, table, year: int, market: str) -> list[dict]:
        """Parse t100sb14 table - 員工福利及薪資統計."""
        records = []
        rows = table.find_all("tr")

        for row in rows:
            cells = row.find_all("td")
            num_cells = len(cells)

            # 107 year has 13 columns, 108+ has 15 columns
            if num_cells < 13:
                continue

            try:
                # Check if this is a data row by looking for company code pattern (4 digits)
                raw_code = self._clean_text(cells[1])
                if not raw_code or not raw_code.isdigit():
                    continue

                # Base fields (0-8 are same for 13/15 cols)
                # 0:Industry, 1:Code, 2:Name, 3:Category, 4:BenefitExp, 5:SalaryExp, 6:Count, 7:AvgBen, 8:AvgSal
                record = {
                    "year": year,
                    "market_type": market,
                    "industry": self._clean_text(cells[0]),
                    "raw_company_code": raw_code,
                    "company_name": self._clean_text(cells[2]),
                    "company_category": self._clean_text(cells[3])
                    if num_cells > 3
                    else None,
                    "employee_benefit_expense": self._parse_number(cells[4])
                    if num_cells > 4
                    else None,
                    "employee_salary_expense": self._parse_number(cells[5])
                    if num_cells > 5
                    else None,
                    "employee_count": self._parse_number(cells[6])
                    if num_cells > 6
                    else None,
                    "avg_benefit_per_employee": self._parse_number(cells[7])
                    if num_cells > 7
                    else None,
                    "avg_salary_current_year": self._parse_number(cells[8])
                    if num_cells > 8
                    else None,
                }

                if num_cells >= 15:
                    # V2 (108+): Has Prev Year & Change
                    record.update(
                        {
                            "avg_salary_previous_year": self._parse_number(cells[9]),
                            "salary_change_rate": self._parse_float(cells[10]),
                            "eps": self._parse_float(cells[11]),
                            "industry_avg_benefit": self._parse_number(cells[12]),
                            "industry_avg_salary": self._parse_number(cells[13]),
                            "industry_avg_eps": self._parse_float(cells[14]),
                        }
                    )
                elif num_cells >= 13:
                    # V1 (107): No Prev Year & Change
                    # 9: EPS, 10: IndAvgBen, 11: IndAvgSal, 12: IndAvgEPS
                    record.update(
                        {
                            "avg_salary_previous_year": None,
                            "salary_change_rate": None,
                            "eps": self._parse_float(cells[9]),
                            "industry_avg_benefit": self._parse_number(cells[10]),
                            "industry_avg_salary": self._parse_number(cells[11]),
                            "industry_avg_eps": self._parse_float(cells[12]),
                        }
                    )

                if record["raw_company_code"] and record["company_name"]:
                    records.append(record)
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue

        return records

    def _parse_t100sb15(self, table, year: int, market: str) -> list[dict]:
        """Parse t100sb15 table."""
        records = []
        rows = table.find_all("tr")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 6:
                continue

            try:
                # Dynamic column detection
                num_cells = len(cells)

                # Base fields (Classic V1: 13 cols)
                # 0:Industry, 1:Code, 2:Name, 3:Total, 4:Count, 5:Avg, 6:EPS, 7:IndAvgSal, 8:IndAvgEPS, 9-12:Flags

                # V2 (16 cols): V1 + Median(6,7,8 shift) ->
                # 0-5 Same
                # 6: Avg Prev (New)
                # 7: Median (New)
                # 8: Median Prev (New)
                # 9: EPS (Was 6)
                # 10: Ind Avg Sal (Was 7)
                # 11: Ind Avg EPS (Was 8)
                # 12-15: Flags

                # V3 (19 cols): V2 + Change(7,10) + Notes(17,18) ->
                # 0-6 Same
                # 7: Avg Change (New)
                # 8: Median (Was 7)
                # 9: Median Prev (Was 8)
                # 10: Median Change (New)
                # 11: EPS (Was 9)
                # ...

                record = {
                    "year": year,
                    "market_type": market,
                    "industry": self._clean_text(cells[0]) if num_cells > 0 else None,
                    "raw_company_code": self._clean_text(cells[1])
                    if num_cells > 1
                    else None,
                    "company_name": self._clean_text(cells[2])
                    if num_cells > 2
                    else None,
                    "total_salary": self._parse_number(cells[3])
                    if num_cells > 3
                    else None,
                    "employee_count": self._parse_number(cells[4])
                    if num_cells > 4
                    else None,
                    "avg_salary": self._parse_number(cells[5])
                    if num_cells > 5
                    else None,
                }

                # Mapping based on version
                if num_cells >= 19:
                    # V3 (113+)
                    record.update(
                        {
                            "avg_salary_previous_year": self._parse_number(cells[6]),
                            "avg_salary_change": self._parse_float(cells[7]),
                            "median_salary": self._parse_number(cells[8]),
                            "median_salary_previous_year": self._parse_number(cells[9]),
                            "median_salary_change": self._parse_float(cells[10]),
                            "eps": self._parse_float(cells[11]),
                            "industry_avg_salary": self._parse_number(cells[12]),
                            "industry_avg_eps": self._parse_float(cells[13]),
                            "is_avg_salary_under_500k": self._clean_text(cells[14]),
                            "is_better_eps_lower_salary": self._clean_text(cells[15]),
                            "is_eps_growth_salary_decrease": self._clean_text(
                                cells[16]
                            ),
                            "performance_salary_relation_note": self._clean_text(
                                cells[17]
                            ),
                            "improvement_measures_note": self._clean_text(cells[18]),
                        }
                    )
                elif num_cells >= 16:
                    # V2 (108-112): 16 columns
                    # 0-Industry, 1-Code, 2-Name, 3-Total, 4-Count, 5-AvgSal, 6-AvgSalPrev
                    # 7-Median, 8-MedianPrev, 9-EPS, 10-IndAvgSal, 11-IndAvgEPS
                    # 12-IsUnder500k, 13-IsBetterEpsLower, 14-IsEpsGrowthDecrease, 15-Note
                    record.update(
                        {
                            "avg_salary_previous_year": self._parse_number(cells[6]),
                            "median_salary": self._parse_number(cells[7]),
                            "median_salary_previous_year": self._parse_number(cells[8]),
                            "eps": self._parse_float(cells[9]),
                            "industry_avg_salary": self._parse_number(cells[10]),
                            "industry_avg_eps": self._parse_float(cells[11]),
                            "is_avg_salary_under_500k": self._clean_text(cells[12]),
                            "is_better_eps_lower_salary": self._clean_text(cells[13]),
                            "is_eps_growth_salary_decrease": self._clean_text(
                                cells[14]
                            ),
                            "performance_salary_relation_note": self._clean_text(
                                cells[15]
                            )
                            if num_cells > 15
                            else None,
                        }
                    )
                elif num_cells >= 13:
                    # V1 (107): 13 columns
                    # ... 9-IsUnder500k, 10-IsBetterEpsLower, 11-IsEpsGrowthDecrease, 12-Note
                    record.update(
                        {
                            "eps": self._parse_float(cells[6]),
                            "industry_avg_salary": self._parse_number(cells[7]),
                            "industry_avg_eps": self._parse_float(cells[8]),
                            "is_avg_salary_under_500k": self._clean_text(cells[9]),
                            "is_better_eps_lower_salary": self._clean_text(cells[10]),
                            "is_eps_growth_salary_decrease": self._clean_text(
                                cells[11]
                            ),
                            "performance_salary_relation_note": self._clean_text(
                                cells[12]
                            )
                            if num_cells > 12
                            else None,
                        }
                    )
                else:
                    logger.warning(
                        f"Skipping row with unexpected column count {num_cells}: {self._clean_text(cells[1])}"
                    )
                    continue

                if record.get("raw_company_code") and record.get("company_name"):
                    records.append(record)
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue

        return records

    def _parse_t100sb13(self, table, year: int, market: str) -> list[dict]:
        """Parse t100sb13 table - 員工福利政策及權益維護措施揭露."""
        records = []
        rows = table.find_all("tr")

        for row in rows:
            # Skip header rows
            if row.find("th") or row.get("class") == ["tblHead"]:
                continue

            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            try:
                # Check if this is a data row by looking for company code pattern
                raw_code = self._clean_text(cells[0])
                if not raw_code or not raw_code.isdigit():
                    continue

                record = {
                    "year": year,
                    "market_type": market,
                    "raw_company_code": raw_code,
                    "company_name": self._clean_text(cells[1])
                    if len(cells) > 1
                    else None,
                    # 平均員工薪資調整情形 (經常性薪資)
                    "planned_salary_increase": self._clean_text(cells[2])
                    if len(cells) > 2
                    else None,
                    "planned_salary_increase_note": self._clean_text(cells[3])
                    if len(cells) > 3
                    else None,
                    "actual_salary_increase": self._clean_text(cells[4])
                    if len(cells) > 4
                    else None,
                    "actual_salary_increase_note": self._clean_text(cells[5])
                    if len(cells) > 5
                    else None,
                    "non_manager_salary_increase": self._clean_text(cells[6])
                    if len(cells) > 6
                    else None,
                    "non_manager_salary_increase_note": self._clean_text(cells[7])
                    if len(cells) > 7
                    else None,
                    "manager_salary_increase": self._clean_text(cells[8])
                    if len(cells) > 8
                    else None,
                    "manager_salary_increase_note": self._clean_text(cells[9])
                    if len(cells) > 9
                    else None,
                    # 新進員工之平均起薪金額
                    "entry_salary_master": self._clean_text(cells[10])
                    if len(cells) > 10
                    else None,
                    "entry_salary_bachelor": self._clean_text(cells[11])
                    if len(cells) > 11
                    else None,
                    "entry_salary_highschool": self._clean_text(cells[12])
                    if len(cells) > 12
                    else None,
                    "entry_salary_note": self._clean_text(cells[13])
                    if len(cells) > 13
                    else None,
                }

                if record.get("raw_company_code") and record.get("company_name"):
                    records.append(record)
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue

        return records

    def _parse_t222sb01(self, table, year: int, market: str) -> list[dict]:
        """Parse t222sb01 table - 基層員工調整薪資或分派酬勞."""
        # This table only exists starting from year 113
        if year < 113:
            return []

        records = []
        rows = table.find_all("tr")

        for row in rows:
            # Skip header rows
            if row.find("th") or "tblHead" in row.get("class", []):
                continue

            cells = row.find_all("td")
            if len(cells) < 6:
                continue

            try:
                # Check if this is a data row by looking for company code pattern
                raw_code = self._clean_text(cells[0])
                if not raw_code or not raw_code.isdigit():
                    continue

                record = {
                    "year": year,
                    "market_type": market,
                    "raw_company_code": raw_code,
                    "company_name": self._clean_text(cells[1])
                    if len(cells) > 1
                    else None,
                    "industry": self._clean_text(cells[2]) if len(cells) > 2 else None,
                    "pretax_net_profit": self._parse_number(cells[3])
                    if len(cells) > 3
                    else None,
                    # 章程訂定提撥比率
                    "allocation_ratio_min": self._clean_text(cells[4])
                    if len(cells) > 4
                    else None,
                    "allocation_ratio_max": self._clean_text(cells[5])
                    if len(cells) > 5
                    else None,
                    "board_resolution_date": self._clean_text(cells[6])
                    if len(cells) > 6
                    else None,
                    "actual_allocation_ratio": self._clean_text(cells[7])
                    if len(cells) > 7
                    else None,
                    "basic_employee_definition": self._clean_text(cells[8])
                    if len(cells) > 8
                    else None,
                    "basic_employee_count": self._parse_number(cells[9])
                    if len(cells) > 9
                    else None,
                    "total_allocation_amount": self._parse_number(cells[10])
                    if len(cells) > 10
                    else None,
                    "allocation_method": self._clean_text(cells[11])
                    if len(cells) > 11
                    else None,
                    # 差異相關
                    "difference_amount": self._clean_text(cells[12])
                    if len(cells) > 12
                    else None,
                    "difference_reason": self._clean_text(cells[13])
                    if len(cells) > 13
                    else None,
                    "difference_handling": self._clean_text(cells[14])
                    if len(cells) > 14
                    else None,
                    "note": self._clean_text(cells[15]) if len(cells) > 15 else None,
                }

                if record.get("raw_company_code") and record.get("company_name"):
                    records.append(record)
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue

        return records

    def _upsert_data(
        self,
        session: Session,
        archive_session: Session,
        records: list[dict],
        model_class: type[SQLModel],
        matcher: CompanyMatcher,
    ) -> tuple[int, int]:
        """Upsert records to main or archive DB.

        A row that fails to build or persist is logged and skipped so it cannot
        abort the whole batch (BACKEND_AUDIT M4). Committing is the caller's
        responsibility (the (year, market) boundary), so this method NEVER
        commits. Returns (written, skipped).
        """
        written = 0
        skipped = 0
        linked_count = 0

        for record in records:
            try:
                # Match company
                matched_code = matcher.match(
                    company_code=record.get("raw_company_code", ""),
                    company_name=record.get("company_name", ""),
                )

                record["company_code"] = matched_code

                if matched_code:
                    linked_count += 1
                    target_session = session
                else:
                    target_session = archive_session

                # Build values via a model instance (so defaults are populated)
                # and upsert on the natural key — the DB enforces idempotency.
                instance = model_class(**record)
                values = model_values(instance)
                upsert_on_conflict(
                    target_session,
                    model_class,
                    values,
                    conflict_cols=("raw_company_code", "year", "market_type"),
                )

                written += 1
            except Exception as e:
                skipped += 1
                logger.warning(
                    f"Skipped MOPS row (raw_code={record.get('raw_company_code')}, "
                    f"year={record.get('year')}, "
                    f"market={record.get('market_type')}): {e}"
                )
                continue

        logger.info(
            f"Upserted {written} records ({skipped} skipped). "
            f"Linked {linked_count} to companies."
        )
        return (written, skipped)

    def _clean_text(self, cell) -> str:
        """Extract and clean text from a table cell."""
        if cell is None:
            return ""
        text = cell.get_text(strip=True)
        return text.strip()

    def _parse_number(self, cell) -> int | None:
        """Parse integer from cell."""
        text = self._clean_text(cell)
        if not text or text == "-" or text == "N/A":
            return None
        try:
            # Remove commas and other non-digit characters except minus
            cleaned = re.sub(r"[^\d-]", "", text)
            if cleaned:
                return int(cleaned)
            return None
        except Exception:
            return None

    def _parse_float(self, cell) -> float | None:
        """Parse float from cell."""
        text = self._clean_text(cell)
        if not text or text == "-" or text == "N/A":
            return None
        try:
            # Remove commas
            cleaned = text.replace(",", "").replace("%", "")
            if cleaned:
                return float(cleaned)
            return None
        except Exception:
            return None
