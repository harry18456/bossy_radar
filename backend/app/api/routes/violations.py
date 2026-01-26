from typing import List, Optional, Any
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select, col

from app.db.session import get_session
from app.models.violation import Violation
from app.schemas.violation import ViolationPublic
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=List[ViolationPublic])
def read_violations(
    session: Session = Depends(get_session),
    company_code: Optional[str] = Query(None, description="Filter by company code"),
    data_source: List[str] = Query(None, description="Filter by data source (e.g. LaborStandards)"),
    authority: List[str] = Query(None, description="Filter by authority (e.g. Taipei)"),
    start_date: Optional[date] = Query(None, description="Filter by penalty_date >= start_date"),
    end_date: Optional[date] = Query(None, description="Filter by penalty_date <= end_date"),
    min_fine: Optional[int] = Query(None, description="Filter by fine_amount >= min_fine"),
    max_fine: Optional[int] = Query(None, description="Filter by fine_amount <= max_fine"),
    sort: Optional[str] = Query(None, description="Sort field (prefix with - for desc, e.g. -fine_amount)"),
    offset: int = 0,
    limit: int = Query(default=100, le=1000),
) -> Any:
    """
    Retrieve violations from the Main DB (Listed/OTC companies only).
    """
    statement = select(Violation)
    
    # Filters
    if company_code:
        statement = statement.where(Violation.company_code == company_code)
    
    if data_source:
        statement = statement.where(col(Violation.data_source).in_(data_source))
        
    if authority:
        statement = statement.where(col(Violation.authority).in_(authority))
        
    if start_date:
        statement = statement.where(Violation.penalty_date >= start_date)
    
    if end_date:
        statement = statement.where(Violation.penalty_date <= end_date)
        
    if min_fine is not None:
        statement = statement.where(Violation.fine_amount >= min_fine)
        
    if max_fine is not None:
        statement = statement.where(Violation.fine_amount <= max_fine)
        
    # Sorting
    if sort:
        sort_fields = sort.split(",")
        for field in sort_fields:
            field = field.strip()
            if field.startswith("-"):
                field_name = field[1:]
                if hasattr(Violation, field_name):
                    statement = statement.order_by(getattr(Violation, field_name).desc())
            else:
                if hasattr(Violation, field):
                    statement = statement.order_by(getattr(Violation, field).asc())
    else:
        # Default sort
        statement = statement.order_by(Violation.penalty_date.desc(), Violation.id.desc())
        
    statement = statement.offset(offset).limit(limit)
    violations = session.exec(statement).all()
    
    return violations
