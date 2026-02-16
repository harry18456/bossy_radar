from datetime import date, datetime

from sqlmodel import SQLModel


class ViolationBase(SQLModel):
    company_name: str
    data_source: str
    authority: str | None = None
    penalty_date: date | None = None
    announcement_date: date | None = None
    disposition_no: str | None = None
    law_article: str | None = None
    violation_content: str | None = None
    fine_amount: int = 0
    company_code: str | None = None


class ViolationPublic(ViolationBase):
    id: int
    created_at: datetime
    last_updated: datetime
