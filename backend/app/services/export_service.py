import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlmodel import Session, select, func, col, extract
from app.db.session import engine

from app.models.company import Company
from app.models.violation import Violation
from app.models.employee_benefit import EmployeeBenefit
from app.models.non_manager_salary import NonManagerSalary
from app.models.welfare_policy import WelfarePolicy
from app.models.salary_adjustment import SalaryAdjustment

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

    def export_all(self):
        with Session(engine) as session:
            logger.info("Starting Full Export...")
            self.export_company_catalog(session)
            self.export_yearly_summaries(session)
            self.export_system_status(session)
            self.export_company_details(session)
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
                    industry=c.industry
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
        
        return CompanyProfileResponse(
            company=CompanyResponse.model_validate(company),
            violations=violations,
            employee_benefits=[EmployeeBenefitResponse.model_validate(x) for x in employee_benefits],
            non_manager_salaries=[NonManagerSalaryResponse.model_validate(x) for x in non_manager_salaries],
            welfare_policies=[WelfarePolicyResponse.model_validate(x) for x in welfare_policies],
            salary_adjustments=[SalaryAdjustmentResponse.model_validate(x) for x in salary_adjustments],
        )

    def export_yearly_summaries(self, session: Session):
        logger.info("Exporting Yearly Summaries...")
        # Adapted from app/api/routes/aggregation.py get_yearly_summary
        # But we want ALL data, so no pagination filters
        
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

        # Step 5: Assemble
        items = []
        for y in available_years:
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

                if benefit: item.employee_benefit = EmployeeBenefitResponse.model_validate(benefit)
                if salary: item.non_manager_salary = NonManagerSalaryResponse.model_validate(salary)
                if policy: item.welfare_policy = WelfarePolicyResponse.model_validate(policy)
                if adjustment: item.salary_adjustment = SalaryAdjustmentResponse.model_validate(adjustment)

                items.append(item)

        self._save_json(self.output_dir / "yearly-summaries.json", items)
        logger.info(f"Exported {len(items)} yearly summary items.")

    def export_system_status(self, session: Session):
        logger.info("Exporting System Status...")
        
        status_response = SyncStatusResponse(
            companies={}, 
            violations={},
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

        # Check MOPS
        last_benefit = session.exec(select(EmployeeBenefit).order_by(EmployeeBenefit.last_updated.desc())).first()
        benefit_count = session.exec(select(func.count(EmployeeBenefit.id))).one()
        status_response.mops["employee_benefit"] = SyncStatusItem(
            last_updated=last_benefit.last_updated if last_benefit else None, 
            count=benefit_count
        )

        self._save_json(self.output_dir / "system-status.json", status_response)
        logger.info("Exported system-status.json")
