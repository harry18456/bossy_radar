from typing import Generic, TypeVar

from pydantic import BaseModel

from app.models.company import CompanyBase

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    total_pages: int


class CompanyResponse(CompanyBase):
    code: str


class CompanyCatalogItem(BaseModel):
    code: str
    name: str
    abbreviation: str | None = None
    market_type: str
    industry: str | None = None
    tax_id: str | None = None  # 統一編號
    capital: float | None = None  # 資本額
    establishment_date: str | None = None  # 成立日期 (如 1987-02-21)
    listing_date: str | None = None  # 上市日期 (如 1994-09-05)
