"""
公司聚合 API Routes

Endpoints:
- GET /companies/{company_code}/profile - 單一公司完整資料
- GET /companies/yearly-summary - 公司年度摘要列表
"""
import math
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Query, HTTPException
from sqlmodel import select, col, func
from sqlalchemy import extract, case, literal

from app.api.deps import SessionDep
from app.models.company import Company
from app.models.violation import Violation
from app.models.employee_benefit import EmployeeBenefit
from app.models.non_manager_salary import NonManagerSalary
from app.models.welfare_policy import WelfarePolicy
from app.models.salary_adjustment import SalaryAdjustment
from app.models.environmental_violation import EnvironmentalViolation
from app.schemas.aggregation import (
    CompanyProfileResponse,
    YearlySummaryItem,
    YearlySummaryResponse,
)
from app.schemas.company import CompanyResponse
from app.schemas.violation import ViolationPublic
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    WelfarePolicyResponse,
    SalaryAdjustmentResponse,
)

router = APIRouter()


# ========== Company Profile ==========
@router.get("/{company_code}/profile", response_model=CompanyProfileResponse)
def get_company_profile(
    company_code: str,
    session: SessionDep,
):
    """
    取得單一公司的完整資料（公司基本資料 + 所有關聯資料）
    """
    # 查詢公司
    company = session.exec(
        select(Company).where(Company.code == company_code)
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {company_code} not found")
    
    # 查詢違規
    violations = session.exec(
        select(Violation)
        .where(Violation.company_code == company_code)
        .order_by(Violation.penalty_date.desc())
    ).all()
    
    # 查詢員工福利
    employee_benefits = session.exec(
        select(EmployeeBenefit)
        .where(EmployeeBenefit.company_code == company_code)
        .order_by(EmployeeBenefit.year.desc())
    ).all()
    
    # 查詢非主管薪資
    non_manager_salaries = session.exec(
        select(NonManagerSalary)
        .where(NonManagerSalary.company_code == company_code)
        .order_by(NonManagerSalary.year.desc())
    ).all()
    
    # 查詢福利政策
    welfare_policies = session.exec(
        select(WelfarePolicy)
        .where(WelfarePolicy.company_code == company_code)
        .order_by(WelfarePolicy.year.desc())
    ).all()
    
    # 查詢調薪
    salary_adjustments = session.exec(
        select(SalaryAdjustment)
        .where(SalaryAdjustment.company_code == company_code)
        .order_by(SalaryAdjustment.year.desc())
    ).all()
    
    # 查詢環境違規
    environmental_violations = session.exec(
        select(EnvironmentalViolation)
        .where(EnvironmentalViolation.company_code == company_code)
        .order_by(EnvironmentalViolation.penalty_date.desc())
    ).all()
    
    return CompanyProfileResponse(
        company=company,
        violations=violations,
        employee_benefits=employee_benefits,
        non_manager_salaries=non_manager_salaries,
        welfare_policies=welfare_policies,
        salary_adjustments=salary_adjustments,
        environmental_violations=environmental_violations,
    )


# ========== Yearly Summary ==========
@router.get("/yearly-summary", response_model=YearlySummaryResponse)
def get_yearly_summary(
    session: SessionDep,
    page: int = Query(1, ge=1, description="頁碼 (從 1 開始)"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位"),
    year: Optional[List[int]] = Query(None, description="民國年過濾"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    market_type: Optional[List[str]] = Query(None, description="市場別過濾"),
    industry: Optional[List[str]] = Query(None, description="產業過濾"),
    include: Optional[List[str]] = Query(
        None, 
        description="要包含的資料：violations, employee_benefit, non_manager_salary, welfare_policy, salary_adjustment, all"
    ),
):
    """
    取得公司年度摘要列表（公司×年份矩陣）
    
    include 參數說明：
    - 不設定：只回傳公司基本資料 + year
    - violations：加入違規統計
    - employee_benefit：加入員工福利完整資料
    - non_manager_salary：加入非主管薪資完整資料
    - welfare_policy：加入福利政策完整資料
    - salary_adjustment：加入調薪完整資料
    - all：包含所有資料
    """
    # 解析 include 參數
    include_set = set(include) if include else set()
    include_all = "all" in include_set
    include_violations = include_all or "violations" in include_set
    include_env_violations = include_all or "env_violations" in include_set
    include_employee_benefit = include_all or "employee_benefit" in include_set
    include_non_manager_salary = include_all or "non_manager_salary" in include_set
    include_welfare_policy = include_all or "welfare_policy" in include_set
    include_salary_adjustment = include_all or "salary_adjustment" in include_set
    
    # Step 1: 取得所有年份（從 employee_benefit 和 non_manager_salary）
    years_query = select(EmployeeBenefit.year).distinct()
    if year:
        years_query = years_query.where(col(EmployeeBenefit.year).in_(year))
    available_years = [r for r in session.exec(years_query).all()]
    
    if not available_years:
        return YearlySummaryResponse(items=[], total=0, page=page, size=size, total_pages=0)
    
    # Step 2: 取得公司列表
    companies_query = select(Company)
    if company_code:
        companies_query = companies_query.where(col(Company.code).in_(company_code))
    if market_type:
        companies_query = companies_query.where(col(Company.market_type).in_(market_type))
    if industry:
        companies_query = companies_query.where(col(Company.industry).in_(industry))
    
    companies = session.exec(companies_query).all()
    
    if not companies:
        return YearlySummaryResponse(items=[], total=0, page=page, size=size, total_pages=0)
    
    # Step 3: 建立公司代號集合
    company_codes = [c.code for c in companies]
    company_map = {c.code: c for c in companies}
    
    # Step 4: 預先查詢關聯資料（根據 include 參數）
    violations_total = {}
    violations_by_year = {}
    if include_violations:
        # 違規 - 歷年累計
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
        
        # 違規 - 按年度
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
            key = (row[0], int(row[1]) - 1911 if row[1] else None)  # 西元轉民國
            violations_by_year[key] = {"count": row[2], "fine": row[3] or 0}
            
    # 環境違規
    env_violations_total = {}
    env_violations_by_year = {}
    if include_env_violations:
        # 環境違規 - 歷年累計
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
        
        # 環境違規 - 按年度
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
            key = (row[0], int(row[1]) - 1911 if row[1] else None)  # 西元轉民國
            env_violations_by_year[key] = {"count": row[2], "fine": row[3] or 0}
    
    # 員工福利（必須查詢用於判斷資料是否存在）
    benefits_map = {}
    benefits = session.exec(
        select(EmployeeBenefit)
        .where(col(EmployeeBenefit.company_code).in_(company_codes))
    ).all()
    for b in benefits:
        benefits_map[(b.company_code, b.year)] = b
    
    # 非主管薪資
    salaries_map = {}
    salaries = session.exec(
        select(NonManagerSalary)
        .where(col(NonManagerSalary.company_code).in_(company_codes))
    ).all()
    for s in salaries:
        salaries_map[(s.company_code, s.year)] = s
    
    # 福利政策
    policies_map = {}
    policies = session.exec(
        select(WelfarePolicy)
        .where(col(WelfarePolicy.company_code).in_(company_codes))
    ).all()
    for p in policies:
        policies_map[(p.company_code, p.year)] = p
    
    # 調薪
    adjustments_map = {}
    adjustments = session.exec(
        select(SalaryAdjustment)
        .where(col(SalaryAdjustment.company_code).in_(company_codes))
    ).all()
    for a in adjustments:
        adjustments_map[(a.company_code, a.year)] = a
    
    # Step 5: 組合結果
    items = []
    for y in sorted(available_years, reverse=True):
        for code in company_codes:
            company = company_map.get(code)
            if not company:
                continue
            
            # 檢查是否有該年度資料
            benefit = benefits_map.get((code, y))
            salary = salaries_map.get((code, y))
            policy = policies_map.get((code, y))
            adjustment = adjustments_map.get((code, y))
            
            # 如果沒有任何資料，跳過
            if not benefit and not salary and not policy and not adjustment:
                continue
            
            # 建立基本資料
            item = YearlySummaryItem(
                company_code=code,
                company_name=company.name,
                market_type=company.market_type,
                industry=company.industry,
                year=y,
            )
            
            # 加入違規統計
            if include_violations:
                vio_year = violations_by_year.get((code, y), {"count": 0, "fine": 0})
                vio_total = violations_total.get(code, {"count": 0, "fine": 0})
                item.violations_year_count = vio_year["count"]
                item.violations_year_fine = vio_year["fine"]
                item.violations_total_count = vio_total["count"]
                item.violations_total_fine = vio_total["fine"]
                
             # 加入環境違規統計
            if include_env_violations:
                env_year = env_violations_by_year.get((code, y), {"count": 0, "fine": 0})
                env_total = env_violations_total.get(code, {"count": 0, "fine": 0})
                item.env_violations_year_count = env_year["count"]
                item.env_violations_year_fine = env_year["fine"]
                item.env_violations_total_count = env_total["count"]
                item.env_violations_total_fine = env_total["fine"]
            
            # 加入 MOPS 完整物件
            if include_employee_benefit and benefit:
                item.employee_benefit = EmployeeBenefitResponse.model_validate(benefit)
            
            if include_non_manager_salary and salary:
                item.non_manager_salary = NonManagerSalaryResponse.model_validate(salary)
            
            if include_welfare_policy and policy:
                item.welfare_policy = WelfarePolicyResponse.model_validate(policy)
            
            if include_salary_adjustment and adjustment:
                item.salary_adjustment = SalaryAdjustmentResponse.model_validate(adjustment)
            
            items.append(item)
    
    # Step 6: 排序
    if sort:
        for sort_field in reversed(sort):
            desc_order = sort_field.startswith("-")
            field_name = sort_field.lstrip("-")
            if hasattr(YearlySummaryItem, field_name):
                items.sort(
                    key=lambda x: (getattr(x, field_name) is None, getattr(x, field_name) or 0),
                    reverse=desc_order
                )
    
    # Step 7: 分頁
    total = len(items)
    start = (page - 1) * size
    end = start + size
    items = items[start:end]
    total_pages = math.ceil(total / size) if size > 0 else 0
    
    return YearlySummaryResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
    )

