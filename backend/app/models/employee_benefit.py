"""
t100sb14 - 財務報告附註揭露之員工福利(薪資)資訊
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class EmployeeBenefit(SQLModel, table=True):
    """財務報告附註揭露之員工福利(薪資)資訊"""
    __tablename__ = "employee_benefit"
    
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
    company_category: Optional[str] = Field(default=None, description="公司類別")
    
    # 員工福利資訊
    employee_benefit_expense: Optional[int] = Field(default=None, description="員工福利費用(仟元)")
    employee_salary_expense: Optional[int] = Field(default=None, description="員工薪資費用(仟元)")
    employee_count: Optional[int] = Field(default=None, description="員工人數(人)")
    avg_benefit_per_employee: Optional[int] = Field(default=None, description="平均員工福利費用(仟元/人)")
    
    # 平均員工薪資費用
    avg_salary_current_year: Optional[int] = Field(default=None, description="本年度平均員工薪資費用(仟元/人)")
    avg_salary_previous_year: Optional[int] = Field(default=None, description="上年度平均員工薪資費用(仟元/人)")
    salary_change_rate: Optional[float] = Field(default=None, description="調整變動情形(%)")
    
    # 每股盈餘
    eps: Optional[float] = Field(default=None, description="每股盈餘(元/股)")
    
    # 同產業公司比較
    industry_avg_benefit: Optional[int] = Field(default=None, description="同產業平均員工福利費用(仟元/人)")
    industry_avg_salary: Optional[int] = Field(default=None, description="同產業平均員工薪資費用(仟元/人)")
    industry_avg_eps: Optional[float] = Field(default=None, description="同產業平均每股盈餘(元/股)")
    
    # System
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
    
    class Config:
        # Unique constraint: (raw_company_code, year, market_type)
        pass
