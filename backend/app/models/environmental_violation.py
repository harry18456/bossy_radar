from datetime import date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class EnvironmentalViolation(SQLModel, table=True):
    """環境部裁罰紀錄 (EMS_P_46)"""

    __table_args__ = (
        UniqueConstraint("dedup_key", name="uq_environmentalviolation_dedup_key"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # Deterministic dedup key (BACKEND_AUDIT H5).
    dedup_key: str | None = Field(default=None, index=True, description="去重合成鍵")

    # Company Link (Nullable - 比對成功時填入)
    company_code: str | None = Field(
        default=None,
        foreign_key="company.code",
        index=True,
        description="公司代號 (關聯)",
    )

    # 識別資料
    tax_id: str | None = Field(default=None, index=True, description="統一編號")
    control_no: str | None = Field(default=None, description="管制事業編號")
    disposition_no: str | None = Field(
        default=None, index=True, description="裁處書字號"
    )

    # 事業資料
    company_name: str = Field(index=True, description="事業名稱 (原始資料)")
    company_address: str | None = Field(default=None, description="公司（工廠）地址")
    violation_address: str | None = Field(default=None, description="違反地址")

    # 違規資訊
    violation_type: str | None = Field(default=None, index=True, description="污染類別")
    violation_date: date | None = Field(
        default=None, index=True, description="違反時間"
    )
    violation_reason: str | None = Field(default=None, description="違反事實")
    law_article: str | None = Field(default=None, description="違反法令")

    # 裁處資訊
    authority: str | None = Field(default=None, description="裁處機關")
    penalty_date: date | None = Field(default=None, index=True, description="裁處時間")
    fine_amount: int = Field(default=0, description="裁處金額")
    penalty_reason: str | None = Field(default=None, description="裁處理由及法令")

    # 後續處理
    limit_date: date | None = Field(default=None, description="限改日期")
    is_improved: bool | None = Field(default=None, description="改善完妥與否")
    is_appeal: bool | None = Field(default=None, description="是否訴願訴訟")
    appeal_result: str | None = Field(default=None, description="訴願訴訟結果")
    is_paid: bool | None = Field(default=None, description="罰鍰是否繳清")

    # 其他
    illegal_profit: int | None = Field(default=None, description="不法利得")
    other_penalty: str | None = Field(default=None, description="其他處罰方式")
    is_serious: bool | None = Field(default=None, description="情節重大")

    # 系統欄位
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
