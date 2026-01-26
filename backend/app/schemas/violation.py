from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel

class ViolationBase(SQLModel):
    company_name: str
    data_source: str
    authority: Optional[str] = None
    penalty_date: Optional[date] = None
    announcement_date: Optional[date] = None
    disposition_no: Optional[str] = None
    law_article: Optional[str] = None
    violation_content: Optional[str] = None
    fine_amount: int = 0
    company_code: Optional[str] = None

class ViolationPublic(ViolationBase):
    id: int
    created_at: datetime
    last_updated: datetime
