"""
公司聚合 API Routes

Endpoints:
- GET /companies/{company_code}/profile - 單一公司完整資料
- GET /companies/yearly-summary - 公司年度摘要列表
"""

import math

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.api.deps import SessionDep
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
    YearlySummaryResponse,
)
from app.services.yearly_summary_builder import build_yearly_summary_items

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
    company = session.exec(select(Company).where(Company.code == company_code)).first()

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
    sort: list[str] | None = Query(None, description="排序欄位"),
    year: list[int] | None = Query(None, description="民國年過濾"),
    company_code: list[str] | None = Query(None, description="公司代號過濾"),
    market_type: list[str] | None = Query(None, description="市場別過濾"),
    industry: list[str] | None = Query(None, description="產業過濾"),
    include: list[str] | None = Query(
        None,
        description="要包含的資料：violations, employee_benefit, non_manager_salary, welfare_policy, salary_adjustment, all",
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
    # 組裝邏輯與 exporter 共用（見 app/services/yearly_summary_builder.py）
    items = build_yearly_summary_items(
        session,
        include=include,
        year=year,
        company_code=company_code,
        market_type=market_type,
        industry=industry,
    )

    # Step 6: 排序
    if sort:
        for sort_field in reversed(sort):
            desc_order = sort_field.startswith("-")
            field_name = sort_field.lstrip("-")
            if hasattr(YearlySummaryItem, field_name):
                items.sort(
                    key=lambda x: (
                        getattr(x, field_name) is None,
                        getattr(x, field_name) or 0,
                    ),
                    reverse=desc_order,
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
