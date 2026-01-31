from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class EnvironmentalViolation(SQLModel, table=True):
    """環境部裁罰紀錄 (EMS_P_46)"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Company Link (Nullable - 比對成功時填入)
    company_code: Optional[str] = Field(
        default=None, 
        foreign_key="company.code", 
        index=True, 
        description="公司代號 (關聯)"
    )
    
    # 識別資料
    tax_id: Optional[str] = Field(default=None, index=True, description="統一編號")
    control_no: Optional[str] = Field(default=None, description="管制事業編號")
    disposition_no: Optional[str] = Field(default=None, index=True, description="裁處書字號")
    
    # 事業資料
    company_name: str = Field(index=True, description="事業名稱 (原始資料)")
    company_address: Optional[str] = Field(default=None, description="公司（工廠）地址")
    violation_address: Optional[str] = Field(default=None, description="違反地址")
    
    # 違規資訊
    violation_type: Optional[str] = Field(default=None, index=True, description="污染類別")
    violation_date: Optional[date] = Field(default=None, index=True, description="違反時間")
    violation_reason: Optional[str] = Field(default=None, description="違反事實")
    law_article: Optional[str] = Field(default=None, description="違反法令")
    
    # 裁處資訊
    authority: Optional[str] = Field(default=None, description="裁處機關")
    penalty_date: Optional[date] = Field(default=None, index=True, description="裁處時間")
    fine_amount: int = Field(default=0, description="裁處金額")
    penalty_reason: Optional[str] = Field(default=None, description="裁處理由及法令")
    
    # 後續處理
    limit_date: Optional[date] = Field(default=None, description="限改日期")
    is_improved: Optional[bool] = Field(default=None, description="改善完妥與否")
    is_appeal: Optional[bool] = Field(default=None, description="是否訴願訴訟")
    appeal_result: Optional[str] = Field(default=None, description="訴願訴訟結果")
    is_paid: Optional[bool] = Field(default=None, description="罰鍰是否繳清")
    
    # 其他
    illegal_profit: Optional[int] = Field(default=None, description="不法利得")
    other_penalty: Optional[str] = Field(default=None, description="其他處罰方式")
    is_serious: Optional[bool] = Field(default=None, description="情節重大")
    
    # 系統欄位
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
