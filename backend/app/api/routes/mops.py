"""
MOPS 員工薪資/福利資料 API Routes

Endpoints:
- GET /mops/employee-benefits - 財務報告附註揭露之員工福利(薪資)資訊
- GET /mops/non-manager-salaries - 非擔任主管職務之全時員工薪資資訊  
- GET /mops/welfare-policies - 員工福利政策及權益維護措施
- GET /mops/salary-adjustments - 基層員工調整薪資或分派酬勞
"""
import math
from typing import List, Optional

from fastapi import APIRouter, Query
from sqlmodel import Session, select, col, asc, desc, func

from app.api.deps import SessionDep
from app.models.employee_benefit import EmployeeBenefit
from app.models.non_manager_salary import NonManagerSalary
from app.models.welfare_policy import WelfarePolicy
from app.models.salary_adjustment import SalaryAdjustment
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    WelfarePolicyResponse,
    SalaryAdjustmentResponse,
)
from app.schemas.company import PaginatedResponse

router = APIRouter()


def apply_pagination_and_sort(query, model, page: int, size: int, sorts: Optional[List[str]], session: Session):
    """
    Apply sorting and pagination to a query.
    Returns (results, total_count).
    """
    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    
    # Apply sorts
    if sorts:
        for sort_field in sorts:
            direction = desc if sort_field.startswith("-") else asc
            field_name = sort_field.lstrip("-")
            if hasattr(model, field_name):
                query = query.order_by(direction(getattr(model, field_name)))
    else:
        # Default sort by year desc, id desc
        query = query.order_by(desc(model.year), desc(model.id))
    
    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    
    results = session.exec(query).all()
    total_pages = math.ceil(total / size) if size > 0 else 0
    
    return results, total, total_pages


# ========== Employee Benefits (t100sb14) ==========
@router.get("/employee-benefits", response_model=PaginatedResponse[EmployeeBenefitResponse])
def read_employee_benefits(
    session: SessionDep,
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位 (e.g. -year, company_code)"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    year: Optional[List[int]] = Query(None, description="民國年過濾"),
    market_type: Optional[List[str]] = Query(None, description="市場別過濾 (sii/otc)"),
    industry: Optional[List[str]] = Query(None, description="產業類別過濾"),
):
    """
    查詢財務報告附註揭露之員工福利(薪資)資訊 (t100sb14)
    """
    query = select(EmployeeBenefit)
    
    if company_code:
        query = query.where(col(EmployeeBenefit.company_code).in_(company_code))
    if year:
        query = query.where(col(EmployeeBenefit.year).in_(year))
    if market_type:
        query = query.where(col(EmployeeBenefit.market_type).in_(market_type))
    if industry:
        query = query.where(col(EmployeeBenefit.industry).in_(industry))
    
    results, total, total_pages = apply_pagination_and_sort(
        query, EmployeeBenefit, page, size, sort, session
    )
    
    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


# ========== Non-Manager Salaries (t100sb15) ==========
@router.get("/non-manager-salaries", response_model=PaginatedResponse[NonManagerSalaryResponse])
def read_non_manager_salaries(
    session: SessionDep,
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位 (e.g. -year, company_code)"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    year: Optional[List[int]] = Query(None, description="民國年過濾"),
    market_type: Optional[List[str]] = Query(None, description="市場別過濾 (sii/otc)"),
    industry: Optional[List[str]] = Query(None, description="產業類別過濾"),
):
    """
    查詢非擔任主管職務之全時員工薪資資訊 (t100sb15)
    """
    query = select(NonManagerSalary)
    
    if company_code:
        query = query.where(col(NonManagerSalary.company_code).in_(company_code))
    if year:
        query = query.where(col(NonManagerSalary.year).in_(year))
    if market_type:
        query = query.where(col(NonManagerSalary.market_type).in_(market_type))
    if industry:
        query = query.where(col(NonManagerSalary.industry).in_(industry))
    
    results, total, total_pages = apply_pagination_and_sort(
        query, NonManagerSalary, page, size, sort, session
    )
    
    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


# ========== Welfare Policies (t100sb13) ==========
@router.get("/welfare-policies", response_model=PaginatedResponse[WelfarePolicyResponse])
def read_welfare_policies(
    session: SessionDep,
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位 (e.g. -year, company_code)"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    year: Optional[List[int]] = Query(None, description="民國年過濾"),
    market_type: Optional[List[str]] = Query(None, description="市場別過濾 (sii/otc)"),
):
    """
    查詢員工福利政策及權益維護措施揭露 (t100sb13)
    """
    query = select(WelfarePolicy)
    
    if company_code:
        query = query.where(col(WelfarePolicy.company_code).in_(company_code))
    if year:
        query = query.where(col(WelfarePolicy.year).in_(year))
    if market_type:
        query = query.where(col(WelfarePolicy.market_type).in_(market_type))
    
    results, total, total_pages = apply_pagination_and_sort(
        query, WelfarePolicy, page, size, sort, session
    )
    
    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


# ========== Salary Adjustments (t222sb01) ==========
@router.get("/salary-adjustments", response_model=PaginatedResponse[SalaryAdjustmentResponse])
def read_salary_adjustments(
    session: SessionDep,
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位 (e.g. -year, company_code)"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    year: Optional[List[int]] = Query(None, description="民國年過濾"),
    market_type: Optional[List[str]] = Query(None, description="市場別過濾 (sii/otc)"),
    industry: Optional[List[str]] = Query(None, description="產業類別過濾"),
):
    """
    查詢基層員工調整薪資或分派酬勞 (t222sb01)
    """
    query = select(SalaryAdjustment)
    
    if company_code:
        query = query.where(col(SalaryAdjustment.company_code).in_(company_code))
    if year:
        query = query.where(col(SalaryAdjustment.year).in_(year))
    if market_type:
        query = query.where(col(SalaryAdjustment.market_type).in_(market_type))
    if industry:
        query = query.where(col(SalaryAdjustment.industry).in_(industry))
    
    results, total, total_pages = apply_pagination_and_sort(
        query, SalaryAdjustment, page, size, sort, session
    )
    
    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )
