"""
Environmental Violations API Routes

GET /environmental-violations - 查詢環境違規記錄
"""
import math
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Query
from sqlmodel import select, col, asc, desc, func
from sqlalchemy import extract

from app.api.deps import SessionDep
from app.models.environmental_violation import EnvironmentalViolation
from app.schemas.environmental_violation import EnvironmentalViolationPublic
from app.schemas.company import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[EnvironmentalViolationPublic])
def read_environmental_violations(
    session: SessionDep,
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位 (e.g. -fine_amount, penalty_date)"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    violation_type: Optional[List[str]] = Query(None, description="污染類別過濾"),
    authority: Optional[List[str]] = Query(None, description="裁處機關過濾"),
    year: Optional[List[int]] = Query(None, description="年度過濾 (西元年)"),
    start_date: Optional[date] = Query(None, description="處分日期起始"),
    end_date: Optional[date] = Query(None, description="處分日期結束"),
    min_fine: Optional[int] = Query(None, description="最低罰款金額"),
    max_fine: Optional[int] = Query(None, description="最高罰款金額"),
):
    """
    查詢環境違規記錄（僅上市櫃公司）
    
    支援多重篩選與排序，行為與 /violations 保持一致。
    """
    query = select(EnvironmentalViolation)
    
    # Filters
    if company_code:
        query = query.where(col(EnvironmentalViolation.company_code).in_(company_code))
    
    if violation_type:
        query = query.where(col(EnvironmentalViolation.violation_type).in_(violation_type))
        
    if authority:
        query = query.where(col(EnvironmentalViolation.authority).in_(authority))
    
    if year:
        query = query.where(extract('year', EnvironmentalViolation.penalty_date).in_(year))
        
    if start_date:
        query = query.where(EnvironmentalViolation.penalty_date >= start_date)
    
    if end_date:
        query = query.where(EnvironmentalViolation.penalty_date <= end_date)
        
    if min_fine is not None:
        query = query.where(EnvironmentalViolation.fine_amount >= min_fine)
        
    if max_fine is not None:
        query = query.where(EnvironmentalViolation.fine_amount <= max_fine)
    
    # Count total before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
        
    # Sorting
    if sort:
        for sort_field in sort:
            direction = desc if sort_field.startswith("-") else asc
            field_name = sort_field.lstrip("-")
            if hasattr(EnvironmentalViolation, field_name):
                query = query.order_by(direction(getattr(EnvironmentalViolation, field_name)))
    else:
        # Default sort
        query = query.order_by(desc(EnvironmentalViolation.penalty_date), desc(EnvironmentalViolation.id))
    
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
