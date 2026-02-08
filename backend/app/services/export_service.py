import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict

from sqlmodel import Session, select, func, col, extract
from app.db.session import engine

from app.models.company import Company
from app.models.violation import Violation
from app.models.employee_benefit import EmployeeBenefit
from app.models.non_manager_salary import NonManagerSalary
from app.models.welfare_policy import WelfarePolicy
from app.models.salary_adjustment import SalaryAdjustment
from app.models.environmental_violation import EnvironmentalViolation

from app.schemas.company import CompanyCatalogItem, CompanyResponse
from app.schemas.aggregation import (
    CompanyProfileResponse, 
    YearlySummaryItem, 
    YearlySummaryResponse
)
from app.schemas.system import SyncStatusResponse, SyncStatusItem
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    WelfarePolicyResponse,
    SalaryAdjustmentResponse,
)

from app.schemas.environmental_violation import EnvironmentalViolationPublic
from app.schemas.leaderboard import (
    LeaderboardResponse,
    ViolationLeaderboard,
    ViolationLeaderboardItem,
    SalaryLeaderboard,
    SalaryLeaderboardItem,
    IndustrySalaryLeaderboard,
    IndustrySalaryLeaderboardItem,
)

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.companies_dir = self.output_dir / "companies"
        self.companies_dir.mkdir(exist_ok=True)

    def _save_json(self, path: Path, data: Any):
        """Helper to save Pydantic models or dicts to JSON"""
        with open(path, "w", encoding="utf-8") as f:
            # Check if it's a Pydantic model (or list of them) or dict
            if isinstance(data, list):
                # If list of models, dump each
                json_data = [
                    item.model_dump(mode='json') if hasattr(item, "model_dump") else item 
                    for item in data
                ]
            elif hasattr(data, "model_dump"):
                json_data = data.model_dump(mode='json')
            else:
                json_data = data
                
            json.dump(json_data, f, ensure_ascii=False, indent=2)

    def _clean_output_dir(self):
        """Clean the output directory before exporting"""
        if self.output_dir.exists():
            logger.info(f"Cleaning output directory: {self.output_dir}")
            shutil.rmtree(self.output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.companies_dir.mkdir(exist_ok=True)

    def export_all(self):
        # Clean directory first
        self._clean_output_dir()
        
        with Session(engine) as session:
            logger.info("Starting Full Export...")
            self.export_company_catalog(session)
            self.export_yearly_summaries(session)
            self.export_system_status(session)
            self.export_company_details(session)
            self.export_leaderboards(session)
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
                    capital=float(c.capital) if c.capital is not None else None,
                    establishment_date=c.establishment_date.isoformat() if c.establishment_date else None,
                    listing_date=c.listing_date.isoformat() if c.listing_date else None
                )
            )
        
        self._save_json(self.output_dir / "company-catalog.json", catalog_items)
        logger.info(f"Exported {len(catalog_items)} companies to company-catalog.json")

    def export_company_details(self, session: Session):
        logger.info("Exporting Company Details...")
        companies = session.exec(select(Company)).all()
        count = 0
        
        for company in companies:
            profile = self._get_company_profile_data(session, company)
            self._save_json(self.companies_dir / f"{company.code}.json", profile)
            count += 1
            if count % 100 == 0:
                logger.info(f"Exported {count} company profiles...")
        
        logger.info(f"Exported {count} company profiles total.")

    def _get_company_profile_data(self, session: Session, company: Company) -> CompanyProfileResponse:
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
            employee_benefits=[EmployeeBenefitResponse.model_validate(x) for x in employee_benefits],
            non_manager_salaries=[NonManagerSalaryResponse.model_validate(x) for x in non_manager_salaries],
            welfare_policies=[WelfarePolicyResponse.model_validate(x) for x in welfare_policies],
            salary_adjustments=[SalaryAdjustmentResponse.model_validate(x) for x in salary_adjustments],
            environmental_violations=[EnvironmentalViolationPublic.model_validate(x) for x in environmental_violations],
        )

    def export_yearly_summaries(self, session: Session):
        logger.info("Exporting Yearly Summaries...")
        # Adapted from app/api/routes/aggregation.py get_yearly_summary
        # But we want ALL data, so no pagination filters
        
        # Create yearly-summaries directory
        yearly_summaries_dir = self.output_dir / "yearly-summaries"
        yearly_summaries_dir.mkdir(exist_ok=True)
        
        # Step 1: Get all years
        years_query = select(EmployeeBenefit.year).distinct()
        available_years = [r for r in session.exec(years_query).all()]
        available_years.sort(reverse=True)
        
        # Step 2: Get all companies
        companies = session.exec(select(Company)).all()
        company_map = {c.code: c for c in companies}
        company_codes = list(company_map.keys())
        
        # Step 4: Pre-fetch related data (Include ALL types)
        # Violations (Total & Yearly)
        violations_total = {}
        violations_total_query = session.exec(
            select(
                Violation.company_code,
                func.count(Violation.id).label("count"),
                func.sum(Violation.fine_amount).label("fine")
            )
            .where(col(Violation.company_code).in_(company_codes))
            .group_by(Violation.company_code)
        ).all()
        for row in violations_total_query:
            violations_total[row[0]] = {"count": row[1], "fine": row[2] or 0}
            
        violations_by_year = {}
        violations_year_query = session.exec(
            select(
                Violation.company_code,
                extract('year', Violation.penalty_date).label("year"),
                func.count(Violation.id).label("count"),
                func.sum(Violation.fine_amount).label("fine")
            )
            .where(col(Violation.company_code).in_(company_codes))
            .group_by(Violation.company_code, extract('year', Violation.penalty_date))
        ).all()
        for row in violations_year_query:
            key = (row[0], int(row[1]) - 1911 if row[1] else None)
            violations_by_year[key] = {"count": row[2], "fine": row[3] or 0}

        # Environmental Violations (Total & Yearly)
        env_violations_total = {}
        env_violations_total_query = session.exec(
            select(
                EnvironmentalViolation.company_code,
                func.count(EnvironmentalViolation.id).label("count"),
                func.sum(EnvironmentalViolation.fine_amount).label("fine")
            )
            .where(col(EnvironmentalViolation.company_code).in_(company_codes))
            .group_by(EnvironmentalViolation.company_code)
        ).all()
        for row in env_violations_total_query:
            env_violations_total[row[0]] = {"count": row[1], "fine": row[2] or 0}
            
        env_violations_by_year = {}
        env_violations_year_query = session.exec(
            select(
                EnvironmentalViolation.company_code,
                extract('year', EnvironmentalViolation.penalty_date).label("year"),
                func.count(EnvironmentalViolation.id).label("count"),
                func.sum(EnvironmentalViolation.fine_amount).label("fine")
            )
            .where(col(EnvironmentalViolation.company_code).in_(company_codes))
            .group_by(EnvironmentalViolation.company_code, extract('year', EnvironmentalViolation.penalty_date))
        ).all()
        for row in env_violations_year_query:
            key = (row[0], int(row[1]) - 1911 if row[1] else None)
            env_violations_by_year[key] = {"count": row[2], "fine": row[3] or 0}

        # MOPS Data Maps
        def fetch_map(model):
            result_map = {}
            results = session.exec(select(model).where(col(model.company_code).in_(company_codes))).all()
            for r in results:
                result_map[(r.company_code, r.year)] = r
            return result_map

        benefits_map = fetch_map(EmployeeBenefit)
        salaries_map = fetch_map(NonManagerSalary)
        policies_map = fetch_map(WelfarePolicy)
        adjustments_map = fetch_map(SalaryAdjustment)

        # Step 5: Assemble items by year
        items_by_year: Dict[int, List[YearlySummaryItem]] = {}
        total_count = 0
        
        for y in available_years:
            items_by_year[y] = []
            for code in company_codes:
                company = company_map.get(code)
                if not company: continue

                benefit = benefits_map.get((code, y))
                salary = salaries_map.get((code, y))
                policy = policies_map.get((code, y))
                adjustment = adjustments_map.get((code, y))

                # If no data for this year, skip
                if not benefit and not salary and not policy and not adjustment:
                    continue

                item = YearlySummaryItem(
                    company_code=code,
                    company_name=company.name,
                    market_type=company.market_type,
                    industry=company.industry,
                    year=y,
                )

                # Violations
                vio_year = violations_by_year.get((code, y), {"count": 0, "fine": 0})
                vio_total = violations_total.get(code, {"count": 0, "fine": 0})
                item.violations_year_count = vio_year["count"]
                item.violations_year_fine = vio_year["fine"]
                item.violations_total_count = vio_total["count"]
                item.violations_total_fine = vio_total["fine"]
                
                # Env Violations
                env_year = env_violations_by_year.get((code, y), {"count": 0, "fine": 0})
                env_total = env_violations_total.get(code, {"count": 0, "fine": 0})
                item.env_violations_year_count = env_year["count"]
                item.env_violations_year_fine = env_year["fine"]
                item.env_violations_total_count = env_total["count"]
                item.env_violations_total_fine = env_total["fine"]

                if benefit: item.employee_benefit = EmployeeBenefitResponse.model_validate(benefit)
                if salary: item.non_manager_salary = NonManagerSalaryResponse.model_validate(salary)
                if policy: item.welfare_policy = WelfarePolicyResponse.model_validate(policy)
                if adjustment: item.salary_adjustment = SalaryAdjustmentResponse.model_validate(adjustment)

                items_by_year[y].append(item)
                total_count += 1

        # Step 6: Save per-year files
        year_stats = []
        for year, items in items_by_year.items():
            if items:  # Only save if there are items
                self._save_json(yearly_summaries_dir / f"{year}.json", items)
                year_stats.append({"year": year, "count": len(items)})
                logger.info(f"Exported {len(items)} items for year {year}")

        # Step 7: Save index.json with metadata
        index_data = {
            "years": available_years,
            "year_stats": year_stats,
            "total_count": total_count,
            "generated_at": datetime.now().isoformat()
        }
        self._save_json(yearly_summaries_dir / "index.json", index_data)
        
        logger.info(f"Exported {total_count} yearly summary items across {len(available_years)} years.")

    def export_system_status(self, session: Session):
        logger.info("Exporting System Status...")
        
        status_response = SyncStatusResponse(
            companies={}, 
            violations={},
            environmental_violations={},
            mops={}
        )

        # Check companies
        last_company = session.exec(select(Company).order_by(Company.last_updated.desc())).first()
        company_count = session.exec(select(func.count(Company.code))).one()
        status_response.companies["all"] = SyncStatusItem(
            last_updated=last_company.last_updated if last_company else None,
            count=company_count
        )

        # Check violations
        last_violation = session.exec(select(Violation).order_by(Violation.last_updated.desc())).first()
        violation_count = session.exec(select(func.count(Violation.id))).one()
        status_response.violations["all"] = SyncStatusItem(
            last_updated=last_violation.last_updated if last_violation else None,
            count=violation_count
        )
        
        # Check environmental violations
        last_env = session.exec(select(EnvironmentalViolation).order_by(EnvironmentalViolation.last_updated.desc())).first()
        env_count = session.exec(select(func.count(EnvironmentalViolation.id))).one()
        status_response.environmental_violations["all"] = SyncStatusItem(
            last_updated=last_env.last_updated if last_env else None,
            count=env_count
        )

        # Check MOPS
        last_benefit = session.exec(select(EmployeeBenefit).order_by(EmployeeBenefit.last_updated.desc())).first()
        benefit_count = session.exec(select(func.count(EmployeeBenefit.id))).one()
        status_response.mops["employee_benefit"] = SyncStatusItem(
            last_updated=last_benefit.last_updated if last_benefit else None, 
            count=benefit_count
        )

        self._save_json(self.output_dir / "system-status.json", status_response)
        logger.info("Exported system-status.json")

    def export_leaderboards(self, session: Session):
        """匯出首頁排行榜資料 (複用 leaderboard.py 邏輯)"""
        from sqlalchemy import extract, text
        
        logger.info("Exporting Leaderboards...")
        
        LIMIT = 10
        YEARS_TO_INCLUDE = 3
        
        # 計算年份範圍
        current_year = date.today().year - 1911  # 今年民國年
        recent_years = [current_year - i for i in range(YEARS_TO_INCLUDE)]
        
        # ========== Step 1: 取得必要的公司名稱 ==========
        company_codes_with_data = set()
        
        # ========== Step 2: 歷年累計違規 ==========
        labor_top_count = session.exec(
            select(
                Violation.company_code,
                func.count(Violation.id).label("count"),
                func.sum(Violation.fine_amount).label("fine"),
            )
            .where(Violation.company_code.isnot(None))
            .group_by(Violation.company_code)
            .order_by(text("count DESC"))
            .limit(LIMIT * 2)
        ).all()
        
        labor_top_fine = session.exec(
            select(
                Violation.company_code,
                func.count(Violation.id).label("count"),
                func.sum(Violation.fine_amount).label("fine"),
            )
            .where(Violation.company_code.isnot(None))
            .group_by(Violation.company_code)
            .order_by(text("fine DESC"))
            .limit(LIMIT * 2)
        ).all()
        
        env_top_count = session.exec(
            select(
                EnvironmentalViolation.company_code,
                func.count(EnvironmentalViolation.id).label("count"),
                func.sum(EnvironmentalViolation.fine_amount).label("fine"),
            )
            .where(EnvironmentalViolation.company_code.isnot(None))
            .group_by(EnvironmentalViolation.company_code)
            .order_by(text("count DESC"))
            .limit(LIMIT * 2)
        ).all()
        
        env_top_fine = session.exec(
            select(
                EnvironmentalViolation.company_code,
                func.count(EnvironmentalViolation.id).label("count"),
                func.sum(EnvironmentalViolation.fine_amount).label("fine"),
            )
            .where(EnvironmentalViolation.company_code.isnot(None))
            .group_by(EnvironmentalViolation.company_code)
            .order_by(text("fine DESC"))
            .limit(LIMIT * 2)
        ).all()
        
        for row in labor_top_count + labor_top_fine + env_top_count + env_top_fine:
            company_codes_with_data.add(row[0])
        
        # ========== Step 3: 按年度違規 ==========
        yearly_violation_data = {}
        for year_roc in recent_years:
            year_ad = year_roc + 1911
            
            labor_year = session.exec(
                select(
                    Violation.company_code,
                    func.count(Violation.id).label("count"),
                    func.sum(Violation.fine_amount).label("fine"),
                )
                .where(Violation.company_code.isnot(None))
                .where(extract('year', Violation.penalty_date) == year_ad)
                .group_by(Violation.company_code)
                .order_by(text("count DESC"))
                .limit(LIMIT * 2)
            ).all()
            
            env_year = session.exec(
                select(
                    EnvironmentalViolation.company_code,
                    func.count(EnvironmentalViolation.id).label("count"),
                    func.sum(EnvironmentalViolation.fine_amount).label("fine"),
                )
                .where(EnvironmentalViolation.company_code.isnot(None))
                .where(extract('year', EnvironmentalViolation.penalty_date) == year_ad)
                .group_by(EnvironmentalViolation.company_code)
                .order_by(text("count DESC"))
                .limit(LIMIT * 2)
            ).all()
            
            yearly_violation_data[year_roc] = {"labor": labor_year, "env": env_year}
            for row in labor_year + env_year:
                company_codes_with_data.add(row[0])
        
        # ========== Step 4: 薪資排行 ==========
        salary_data = {}
        salary_by_industry_data = {}
        
        for year_roc in recent_years:
            top_avg = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.avg_salary.isnot(None))
                .order_by(NonManagerSalary.avg_salary.desc())
                .limit(LIMIT)
            ).all()
            
            bottom_avg = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.avg_salary.isnot(None))
                .order_by(NonManagerSalary.avg_salary.asc())
                .limit(LIMIT)
            ).all()
            
            top_median = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.median_salary.isnot(None))
                .order_by(NonManagerSalary.median_salary.desc())
                .limit(LIMIT)
            ).all()
            
            bottom_median = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.median_salary.isnot(None))
                .order_by(NonManagerSalary.median_salary.asc())
                .limit(LIMIT)
            ).all()
            
            salary_data[year_roc] = {
                "top_avg": top_avg,
                "bottom_avg": bottom_avg,
                "top_median": top_median,
                "bottom_median": bottom_median,
            }
            
            for s in top_avg + bottom_avg + top_median + bottom_median:
                company_codes_with_data.add(s.company_code)
            
            # 按產業分組
            industries = session.exec(
                select(NonManagerSalary.industry)
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.industry.isnot(None))
                .distinct()
            ).all()
            
            salary_by_industry_data[year_roc] = {}
            for industry_result in industries:
                industry = industry_result if isinstance(industry_result, str) else industry_result[0]
                if not industry:
                    continue
                
                ind_top = session.exec(
                    select(NonManagerSalary)
                    .where(NonManagerSalary.company_code.isnot(None))
                    .where(NonManagerSalary.year == year_roc)
                    .where(NonManagerSalary.industry == industry)
                    .where(NonManagerSalary.median_salary.isnot(None))
                    .order_by(NonManagerSalary.median_salary.desc())
                    .limit(LIMIT)
                ).all()
                
                ind_bottom = session.exec(
                    select(NonManagerSalary)
                    .where(NonManagerSalary.company_code.isnot(None))
                    .where(NonManagerSalary.year == year_roc)
                    .where(NonManagerSalary.industry == industry)
                    .where(NonManagerSalary.median_salary.isnot(None))
                    .order_by(NonManagerSalary.median_salary.asc())
                    .limit(LIMIT)
                ).all()
                
                ind_top_eps = session.exec(
                    select(NonManagerSalary)
                    .where(NonManagerSalary.company_code.isnot(None))
                    .where(NonManagerSalary.year == year_roc)
                    .where(NonManagerSalary.industry == industry)
                    .where(NonManagerSalary.eps.isnot(None))
                    .order_by(NonManagerSalary.eps.desc())
                    .limit(LIMIT)
                ).all()
                
                ind_bottom_eps = session.exec(
                    select(NonManagerSalary)
                    .where(NonManagerSalary.company_code.isnot(None))
                    .where(NonManagerSalary.year == year_roc)
                    .where(NonManagerSalary.industry == industry)
                    .where(NonManagerSalary.eps.isnot(None))
                    .order_by(NonManagerSalary.eps.asc())
                    .limit(LIMIT)
                ).all()
                
                salary_by_industry_data[year_roc][industry] = {
                    "top": ind_top,
                    "bottom": ind_bottom,
                    "top_eps": ind_top_eps,
                    "bottom_eps": ind_bottom_eps,
                }
                for s in ind_top + ind_bottom + ind_top_eps + ind_bottom_eps:
                    company_codes_with_data.add(s.company_code)
        
        # ========== Step 5: 查詢公司名稱 ==========
        company_map = {}
        if company_codes_with_data:
            companies = session.exec(
                select(Company).where(Company.code.in_(list(company_codes_with_data)))
            ).all()
            company_map = {c.code: c for c in companies}
        
        # ========== Step 6: 建構回應 ==========
        def build_violation_leaderboard(data: Dict[str, dict]) -> ViolationLeaderboard:
            items = [
                ViolationLeaderboardItem(
                    company_code=code,
                    company_name=info["name"],
                    labor_count=info["labor_count"],
                    labor_fine=info["labor_fine"],
                    env_count=info["env_count"],
                    env_fine=info["env_fine"],
                    total_count=info["labor_count"] + info["env_count"],
                    total_fine=info["labor_fine"] + info["env_fine"],
                )
                for code, info in data.items()
                if info["labor_count"] + info["env_count"] > 0
            ]
            
            by_count = sorted(items, key=lambda x: x.total_count, reverse=True)
            by_fine = sorted(items, key=lambda x: x.total_fine, reverse=True)
            
            return ViolationLeaderboard(
                top_by_count=by_count[:LIMIT],
                bottom_by_count=by_count[-LIMIT:][::-1] if len(by_count) >= LIMIT else by_count[::-1],
                top_by_fine=by_fine[:LIMIT],
                bottom_by_fine=by_fine[-LIMIT:][::-1] if len(by_fine) >= LIMIT else by_fine[::-1],
            )
        
        def to_salary_item(s: NonManagerSalary) -> SalaryLeaderboardItem:
            return SalaryLeaderboardItem(
                company_code=s.company_code,
                company_name=company_map.get(s.company_code, Company(name=s.company_name)).name,
                avg_salary=s.avg_salary,
                median_salary=s.median_salary,
            )
        
        def to_industry_salary_item(s: NonManagerSalary) -> IndustrySalaryLeaderboardItem:
            return IndustrySalaryLeaderboardItem(
                company_code=s.company_code,
                company_name=company_map.get(s.company_code, Company(name=s.company_name)).name,
                industry=s.industry or "",
                avg_salary=s.avg_salary,
                median_salary=s.median_salary,
                eps=s.eps,
            )
        
        # 合併歷年違規
        all_time_stats: Dict[str, dict] = defaultdict(lambda: {
            "name": "", "labor_count": 0, "labor_fine": 0, "env_count": 0, "env_fine": 0
        })
        for row in labor_top_count + labor_top_fine:
            code = row[0]
            all_time_stats[code]["name"] = company_map.get(code, Company(name="")).name
            all_time_stats[code]["labor_count"] = max(all_time_stats[code]["labor_count"], row[1])
            all_time_stats[code]["labor_fine"] = max(all_time_stats[code]["labor_fine"], row[2] or 0)
        for row in env_top_count + env_top_fine:
            code = row[0]
            all_time_stats[code]["name"] = company_map.get(code, Company(name="")).name
            all_time_stats[code]["env_count"] = max(all_time_stats[code]["env_count"], row[1])
            all_time_stats[code]["env_fine"] = max(all_time_stats[code]["env_fine"], row[2] or 0)
        
        violation_all_time = build_violation_leaderboard(all_time_stats)
        
        # 各年度違規
        violation_yearly = {}
        for year_roc, data in yearly_violation_data.items():
            yearly_stats: Dict[str, dict] = defaultdict(lambda: {
                "name": "", "labor_count": 0, "labor_fine": 0, "env_count": 0, "env_fine": 0
            })
            for row in data["labor"]:
                code = row[0]
                yearly_stats[code]["name"] = company_map.get(code, Company(name="")).name
                yearly_stats[code]["labor_count"] = row[1]
                yearly_stats[code]["labor_fine"] = row[2] or 0
            for row in data["env"]:
                code = row[0]
                yearly_stats[code]["name"] = company_map.get(code, Company(name="")).name
                yearly_stats[code]["env_count"] = row[1]
                yearly_stats[code]["env_fine"] = row[2] or 0
            
            if yearly_stats:
                violation_yearly[year_roc] = build_violation_leaderboard(yearly_stats)
        
        # 各年度薪資
        salary = {}
        for year_roc, data in salary_data.items():
            salary[year_roc] = SalaryLeaderboard(
                top_by_avg=[to_salary_item(s) for s in data["top_avg"]],
                bottom_by_avg=[to_salary_item(s) for s in data["bottom_avg"]],
                top_by_median=[to_salary_item(s) for s in data["top_median"]],
                bottom_by_median=[to_salary_item(s) for s in data["bottom_median"]],
            )
        
        # 各年度各產業薪資
        salary_by_industry = {}
        for year_roc, industries in salary_by_industry_data.items():
            salary_by_industry[year_roc] = {}
            for industry, data in industries.items():
                salary_by_industry[year_roc][industry] = IndustrySalaryLeaderboard(
                    top_by_median=[to_industry_salary_item(s) for s in data["top"]],
                    bottom_by_median=[to_industry_salary_item(s) for s in data["bottom"]],
                    top_by_eps=[to_industry_salary_item(s) for s in data["top_eps"]],
                    bottom_by_eps=[to_industry_salary_item(s) for s in data["bottom_eps"]],
                )
        
        response = LeaderboardResponse(
            latest_year=current_year,
            violation_all_time=violation_all_time,
            violation_yearly=violation_yearly,
            salary=salary,
            salary_by_industry=salary_by_industry,
        )
        
        self._save_json(self.output_dir / "leaderboards.json", response)
        logger.info("Exported leaderboards.json")

