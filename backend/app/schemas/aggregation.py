"""
公司聚合 API Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.company import CompanyResponse
from app.schemas.violation import ViolationPublic
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    WelfarePolicyResponse,
    SalaryAdjustmentResponse,
)


# ========== Company Profile ==========
class CompanyProfileResponse(BaseModel):
    """單一公司完整資料"""
    company: CompanyResponse
    violations: List[ViolationPublic]
    employee_benefits: List[EmployeeBenefitResponse]
    non_manager_salaries: List[NonManagerSalaryResponse]
    welfare_policies: List[WelfarePolicyResponse]
    salary_adjustments: List[SalaryAdjustmentResponse]


# ========== Yearly Summary ==========
class YearlySummaryItem(BaseModel):
    """公司年度摘要"""
    # 公司基本資料
    company_code: str
    company_name: str
    market_type: Optional[str] = None
    industry: Optional[str] = None
    year: int
    
    # 違規統計 - 當年度
    violations_year_count: int = 0
    violations_year_fine: int = 0
    
    # 違規統計 - 歷年累計
    violations_total_count: int = 0
    violations_total_fine: int = 0
    
    # 員工福利 (t100sb14)
    employee_count: Optional[int] = None
    salary_per_employee: Optional[int] = None
    median_employee_salary: Optional[int] = None
    
    # 非主管薪資 (t100sb15)
    avg_salary: Optional[int] = None
    median_salary: Optional[int] = None
    
    # 福利政策 (t100sb13)
    planned_salary_increase: Optional[str] = None
    actual_salary_increase: Optional[str] = None
    
    # 調薪 (t222sb01)
    has_salary_adjustment: bool = False


class YearlySummaryResponse(BaseModel):
    """年度摘要分頁回應"""
    items: List[YearlySummaryItem]
    total: int
    page: int
    size: int
    total_pages: int
