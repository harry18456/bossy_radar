"""
t100sb15 - 非擔任主管職務之全時員工薪資資訊
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class NonManagerSalary(SQLModel, table=True):
    """非擔任主管職務之全時員工薪資資訊"""
    __tablename__ = "non_manager_salary"
    
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
    
    # 非擔任主管職務之全時員工薪資資訊
    employee_count: Optional[int] = Field(default=None, description="員工人數(人)")
    
    # 薪資統計
    total_salary: Optional[int] = Field(default=None, description="薪資總額(仟元)")
    avg_salary: Optional[int] = Field(default=None, description="平均薪資(仟元)")
    median_salary: Optional[int] = Field(default=None, description="薪資中位數(仟元)")
    
    # 年度比較
    avg_salary_previous_year: Optional[int] = Field(default=None, description="上年度平均薪資(仟元)")
    avg_salary_change: Optional[float] = Field(default=None, description="平均薪資變動情形(%)")
    
    # 中位數相關
    median_salary_previous_year: Optional[int] = Field(default=None, description="上年度薪資中位數(仟元)")
    median_salary_change: Optional[float] = Field(default=None, description="薪資中位數變動情形(%)")
    
    #EPS 相關
    industry_avg_salary: Optional[int] = Field(default=None, description="同產業平均薪資(仟元)")
    industry_median_salary: Optional[int] = Field(default=None, description="同產業薪資中位數(仟元)")
    
    # EPS 相關
    eps: Optional[float] = Field(default=None, description="每股盈餘(元/股)")
    industry_avg_eps: Optional[float] = Field(default=None, description="同產業平均每股盈餘(元/股)")
    
    # 經營績效與薪酬關聯 (質化指標)
    is_avg_salary_under_500k: Optional[str] = Field(default=None, description="平均薪資未達50萬元 (Y/N)")
    is_better_eps_lower_salary: Optional[str] = Field(default=None, description="EPS較同業佳但薪資低於同業 (Y/N)")
    is_eps_growth_salary_decrease: Optional[str] = Field(default=None, description="EPS成長但薪資減少 (Y/N)")
    performance_salary_relation_note: Optional[str] = Field(default=None, description="經營績效與薪酬關聯性說明")
    improvement_measures_note: Optional[str] = Field(default=None, description="具體改善措施說明")
    
    # System
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
