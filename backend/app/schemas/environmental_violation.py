from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel

class EnvironmentalViolationBase(SQLModel):
    # Company Link
    company_code: Optional[str] = None
    
    # 識別資料
    tax_id: Optional[str] = None
    control_no: Optional[str] = None
    disposition_no: Optional[str] = None
    
    # 事業資料
    company_name: str
    company_address: Optional[str] = None
    violation_address: Optional[str] = None
    
    # 違規資訊
    violation_type: Optional[str] = None
    violation_date: Optional[date] = None
    violation_reason: Optional[str] = None
    law_article: Optional[str] = None
    
    # 裁處資訊
    authority: Optional[str] = None
    penalty_date: Optional[date] = None
    fine_amount: int = 0
    penalty_reason: Optional[str] = None
    
    # 後續處理
    limit_date: Optional[date] = None
    is_improved: Optional[bool] = None
    is_appeal: Optional[bool] = None
    appeal_result: Optional[str] = None
    is_paid: Optional[bool] = None
    
    # 其他
    illegal_profit: Optional[int] = None
    other_penalty: Optional[str] = None
    is_serious: Optional[bool] = None

class EnvironmentalViolationPublic(EnvironmentalViolationBase):
    id: int
    created_at: datetime
    last_updated: datetime
