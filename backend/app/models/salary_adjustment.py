"""
t222sb01 - 基層員工調整薪資或分派酬勞
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class SalaryAdjustment(SQLModel, table=True):
    """基層員工調整薪資或分派酬勞"""
    __tablename__ = "salary_adjustment"
    
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
    
    # 基本資料
    industry: Optional[str] = Field(default=None, description="產業類別")
    pretax_net_profit: Optional[int] = Field(default=None, description="年度稅前淨利(元)")
    
    # 章程訂定提撥比率
    allocation_ratio_min: Optional[str] = Field(default=None, description="章程訂定提撥比率下限")
    allocation_ratio_max: Optional[str] = Field(default=None, description="章程訂定提撥比率上限")
    
    # 實際提撥資訊
    board_resolution_date: Optional[str] = Field(default=None, description="董事會決議提撥日期")
    actual_allocation_ratio: Optional[str] = Field(default=None, description="實際提撥比率")
    basic_employee_definition: Optional[str] = Field(default=None, description="基層員工認定範圍說明")
    basic_employee_count: Optional[int] = Field(default=None, description="基層員工人數(人)")
    total_allocation_amount: Optional[int] = Field(default=None, description="提撥總金額(元)")
    allocation_method: Optional[str] = Field(default=None, description="方式：調整薪資或分派酬勞")
    
    # 差異相關
    difference_amount: Optional[str] = Field(default=None, description="差異數(元)")
    difference_reason: Optional[str] = Field(default=None, description="原因")
    difference_handling: Optional[str] = Field(default=None, description="處理情形")
    note: Optional[str] = Field(default=None, description="備註")
    
    # System
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
