from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Violation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Company Link (Nullable)
    company_code: Optional[str] = Field(default=None, foreign_key="company.code", index=True, description="公司代號 (關聯)")
    
    # Raw Data
    company_name: str = Field(index=True, description="事業單位名稱 (原始資料)")
    data_source: str = Field(index=True, description="資料來源 (e.g., LaborStandards)")
    authority: Optional[str] = Field(default=None, description="主管機關")
    
    # Dates
    penalty_date: Optional[date] = Field(default=None, index=True, description="處分日期")
    announcement_date: Optional[date] = Field(default=None, index=True, description="公告日期")
    
    # Violation Details
    disposition_no: Optional[str] = Field(default=None, index=True, description="處分字號")
    law_article: Optional[str] = Field(default=None, description="違反法規條款")
    violation_content: Optional[str] = Field(default=None, description="違反法規內容")
    fine_amount: int = Field(default=0, description="罰鍰金額")
    
    # System
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
