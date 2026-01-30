from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel
from app.models.company import Company

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    total_pages: int

class CompanyResponse(Company):
    pass

class CompanyCatalogItem(BaseModel):
    code: str
    name: str
    abbreviation: Optional[str] = None
    market_type: str
    industry: Optional[str] = None
