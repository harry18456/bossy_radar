"""
t100sb13 - 員工福利政策及權益維護措施揭露-彙總資料查詢
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class WelfarePolicy(SQLModel, table=True):
    """員工福利政策及權益維護措施揭露-彙總資料"""
    __tablename__ = "welfare_policy"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Company Link (Nullable - 無法比對時存入 archive)
    company_code: Optional[str] = Field(
        default=None, foreign_key="company.code", index=True,
        description="公司代號 (關聯)"
    )
    
    # Raw Data Identifiers
    raw_company_code: str = Field(index=True, description="原始公司代號")
    company_name: str = Field(index=True, description="公司名稱 (原始資料)")
    year: int = Field(index=True, description="民國年")
    market_type: str = Field(index=True, description="市場別 (sii/otc)")
    
    # 平均員工薪資調整情形 (經常性薪資)
    planned_salary_increase: Optional[str] = Field(default=None, description="預計調薪")
    planned_salary_increase_note: Optional[str] = Field(default=None, description="預計調薪備註")
    actual_salary_increase: Optional[str] = Field(default=None, description="實際調薪")
    actual_salary_increase_note: Optional[str] = Field(default=None, description="實際調薪備註")
    non_manager_salary_increase: Optional[str] = Field(default=None, description="非經理人員工調薪")
    non_manager_salary_increase_note: Optional[str] = Field(default=None, description="非經理人員工調薪備註")
    manager_salary_increase: Optional[str] = Field(default=None, description="經理人員工調薪")
    manager_salary_increase_note: Optional[str] = Field(default=None, description="經理人員工調薪備註")
    
    # 新進員工之平均起薪金額
    entry_salary_master: Optional[str] = Field(default=None, description="碩士及以上起薪")
    entry_salary_bachelor: Optional[str] = Field(default=None, description="大專校院起薪")
    entry_salary_highschool: Optional[str] = Field(default=None, description="高中及以下起薪")
    entry_salary_note: Optional[str] = Field(default=None, description="起薪備註")
    
    # System
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
