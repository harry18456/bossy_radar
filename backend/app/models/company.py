from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Company(SQLModel, table=True):
    # 公司代號 (Primary Key)
    code: str = Field(primary_key=True, description="公司代號")
    
    # 基本資料
    name: str = Field(index=True, description="公司名稱")
    abbreviation: Optional[str] = Field(default=None, description="公司簡稱")
    market_type: str = Field(index=True, description="市場別 (listed/otc/emerging)")
    industry: Optional[str] = Field(default=None, description="產業別")
    
    # 聯絡/官方資料
    tax_id: Optional[str] = Field(default=None, index=True, description="營利事業統一編號")
    chairman: Optional[str] = Field(default=None, description="董事長")
    manager: Optional[str] = Field(default=None, description="總經理")
    
    # 日期相關
    establishment_date: Optional[date] = Field(default=None, description="成立日期")
    listing_date: Optional[date] = Field(default=None, description="上市/上櫃日期")
    
    # 財務/其他
    capital: Optional[int] = Field(default=None, description="實收資本額")
    address: Optional[str] = Field(default=None, description="住址")
    website: Optional[str] = Field(default=None, description="網址")
    email: Optional[str] = Field(default=None, description="電子郵件")
    
    # MOPS 補充資料 (t05st03)
    stakeholder_url: Optional[str] = Field(default=None, description="利害關係人專區網址")
    governance_url: Optional[str] = Field(default=None, description="公司治理資訊專區網址")
    
    # 系統欄位
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
