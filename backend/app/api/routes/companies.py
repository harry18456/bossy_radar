from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from app.api.deps import SessionDep
from app.schemas.company import CompanyResponse, PaginatedResponse
from app.services.company_service import CompanyService
import math

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[CompanyResponse])
def read_companies(
    session: SessionDep,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, le=100, description="Page size"),
    sort: Optional[List[str]] = Query(None, description="Sort fields (e.g. -capital, listing_date)"),
    market_type: Optional[List[str]] = Query(None, description="Filter by market type (Listed, OTC, Emerging)"),
    industry: Optional[List[str]] = Query(None, description="Filter by industry"),
    code: Optional[List[str]] = Query(None, description="Filter by company code"),
    name: Optional[str] = Query(None, description="Filter by company name (partial match)"),
):
    """
    Retrieve companies with pagination, sorting, and filtering.
    """
    service = CompanyService()
    
    filters = {
        "market_type": market_type,
        "industry": industry,
        "code": code,
        "name": name
    }
    
    results, total = service.get_companies(
        session=session,
        page=page,
        size=size,
        filters=filters,
        sorts=sort
    )
    
    total_pages = math.ceil(total / size) if size > 0 else 0
    
    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )
