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
