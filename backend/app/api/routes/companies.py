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
    page: int = Query(1, ge=1, description="頁碼"),
    size: int = Query(20, le=100, description="每頁筆數"),
    sort: Optional[List[str]] = Query(None, description="排序欄位 (e.g. -capital, listing_date)"),
    market_type: Optional[List[str]] = Query(None, description="市場別過濾 (Listed, OTC, Emerging)"),
    industry: Optional[List[str]] = Query(None, description="產業類別過濾"),
    company_code: Optional[List[str]] = Query(None, description="公司代號過濾"),
    name: Optional[str] = Query(None, description="公司名稱過濾 (模糊比對)"),
):
    """
    查詢公司資料（分頁、排序、過濾）
    """
    service = CompanyService()
    
    filters = {
        "market_type": market_type,
        "industry": industry,
        "code": company_code,  # 內部仍用 code，僅 API 參數統一
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
