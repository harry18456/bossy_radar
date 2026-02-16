from datetime import date, datetime

from sqlmodel import Field, SQLModel


class CompanyBase(SQLModel):
    # 基本資料
    name: str = Field(index=True, description="公司名稱")
    abbreviation: str | None = Field(default=None, description="公司簡稱")
    market_type: str = Field(index=True, description="市場別 (listed/otc/emerging)")
    industry: str | None = Field(default=None, description="產業別")

    # 聯絡/官方資料
    tax_id: str | None = Field(default=None, index=True, description="營利事業統一編號")
    chairman: str | None = Field(default=None, description="董事長")
    manager: str | None = Field(default=None, description="總經理")

    # 日期相關
    establishment_date: date | None = Field(default=None, description="成立日期")
    listing_date: date | None = Field(default=None, description="上市/上櫃日期")

    # 財務/其他
    capital: int | None = Field(default=None, description="實收資本額")
    address: str | None = Field(default=None, description="住址")
    website: str | None = Field(default=None, description="網址")
    email: str | None = Field(default=None, description="電子郵件")

    # MOPS 補充資料 (t05st03)
    stakeholder_url: str | None = Field(default=None, description="利害關係人專區網址")
    governance_url: str | None = Field(default=None, description="公司治理資訊專區網址")

    # 系統欄位
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最後更新時間"
    )


class Company(CompanyBase, table=True):
    # 公司代號 (Primary Key)
    code: str = Field(primary_key=True, description="公司代號")
