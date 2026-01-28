"""
Violations API Routes

GET /violations - 查詢勞動違規記錄
"""
import math
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Query
from sqlmodel import select, col, asc, desc, func

from app.api.deps import SessionDep
from app.models.violation import Violation
from app.schemas.violation import ViolationPublic
from app.schemas.company import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ViolationPublic])
def read_violations(
    session: SessionDep,
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位 (e.g. -fine_amount, penalty_date)"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    data_source: Optional[List[str]] = Query(None, description="資料來源過濾 (e.g. LaborStandards)"),
    authority: Optional[List[str]] = Query(None, description="主管機關過濾 (e.g. Taipei)"),
    start_date: Optional[date] = Query(None, description="處分日期起始"),
    end_date: Optional[date] = Query(None, description="處分日期結束"),
    min_fine: Optional[int] = Query(None, description="最低罰款金額"),
    max_fine: Optional[int] = Query(None, description="最高罰款金額"),
):
    """
    查詢勞動違規記錄（僅上市櫃公司）
    """
    query = select(Violation)
    
    # Filters
    if company_code:
        query = query.where(col(Violation.company_code).in_(company_code))
    
    if data_source:
        query = query.where(col(Violation.data_source).in_(data_source))
        
    if authority:
        query = query.where(col(Violation.authority).in_(authority))
        
    if start_date:
        query = query.where(Violation.penalty_date >= start_date)
    
    if end_date:
        query = query.where(Violation.penalty_date <= end_date)
        
    if min_fine is not None:
        query = query.where(Violation.fine_amount >= min_fine)
        
    if max_fine is not None:
        query = query.where(Violation.fine_amount <= max_fine)
    
    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
        
    # Sorting
    if sort:
        for sort_field in sort:
            direction = desc if sort_field.startswith("-") else asc
            field_name = sort_field.lstrip("-")
            if hasattr(Violation, field_name):
                query = query.order_by(direction(getattr(Violation, field_name)))
    else:
        # Default sort
        query = query.order_by(desc(Violation.penalty_date), desc(Violation.id))
    
    # Pagination
    query = query.offset((page - 1) * size).limit(size)
    violations = session.exec(query).all()
    
    total_pages = math.ceil(total / size) if size > 0 else 0
    
    return PaginatedResponse(
        items=violations,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )
