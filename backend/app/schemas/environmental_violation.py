from datetime import date, datetime

from sqlmodel import SQLModel


class EnvironmentalViolationBase(SQLModel):
    # Company Link
    company_code: str | None = None

    # 識別資料
    tax_id: str | None = None
    control_no: str | None = None
    disposition_no: str | None = None

    # 事業資料
    company_name: str
    company_address: str | None = None
    violation_address: str | None = None

    # 違規資訊
    violation_type: str | None = None
    violation_date: date | None = None
    violation_reason: str | None = None
    law_article: str | None = None

    # 裁處資訊
    authority: str | None = None
    penalty_date: date | None = None
    fine_amount: int = 0
    penalty_reason: str | None = None

    # 後續處理
    limit_date: date | None = None
    is_improved: bool | None = None
    is_appeal: bool | None = None
    appeal_result: str | None = None
    is_paid: bool | None = None

    # 其他
    illegal_profit: int | None = None
    other_penalty: str | None = None
    is_serious: bool | None = None


class EnvironmentalViolationPublic(EnvironmentalViolationBase):
    id: int
    created_at: datetime
    last_updated: datetime
