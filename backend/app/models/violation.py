from datetime import date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Violation(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_violation_dedup_key"),)

    id: int | None = Field(default=None, primary_key=True)

    # Deterministic dedup key (BACKEND_AUDIT H5): natural key when
    # disposition_no is present, else a synthetic hash of identifying fields.
    dedup_key: str | None = Field(default=None, index=True, description="去重合成鍵")

    # Company Link (Nullable)
    company_code: str | None = Field(
        default=None,
        foreign_key="company.code",
        index=True,
        description="公司代號 (關聯)",
    )

    # Raw Data
    company_name: str = Field(index=True, description="事業單位名稱 (原始資料)")
    data_source: str = Field(index=True, description="資料來源 (e.g., LaborStandards)")
    authority: str | None = Field(default=None, description="主管機關")

    # Dates
    penalty_date: date | None = Field(default=None, index=True, description="處分日期")
    announcement_date: date | None = Field(
        default=None, index=True, description="公告日期"
    )

    # Violation Details
    disposition_no: str | None = Field(default=None, index=True, description="處分字號")
    law_article: str | None = Field(default=None, description="違反法規條款")
    violation_content: str | None = Field(default=None, description="違反法規內容")
    fine_amount: int = Field(default=0, description="罰鍰金額")

    # System
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
