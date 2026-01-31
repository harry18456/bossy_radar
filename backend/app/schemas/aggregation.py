"""
公司聚合 API Schemas
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.company import CompanyResponse
from app.schemas.violation import ViolationPublic
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    WelfarePolicyResponse,
    SalaryAdjustmentResponse,
)
from app.schemas.environmental_violation import EnvironmentalViolationPublic


# ========== Company Profile ==========
class CompanyProfileResponse(BaseModel):
    """單一公司完整資料"""
    company: CompanyResponse
    violations: List[ViolationPublic]
    employee_benefits: List[EmployeeBenefitResponse]
    non_manager_salaries: List[NonManagerSalaryResponse]
    welfare_policies: List[WelfarePolicyResponse]
    salary_adjustments: List[SalaryAdjustmentResponse]
    environmental_violations: List[EnvironmentalViolationPublic] = Field(description="環境違規紀錄")


# ========== Yearly Summary ==========
class YearlySummaryItem(BaseModel):
    """公司年度摘要"""
    # 公司基本資料（必定回傳）
    company_code: str
    company_name: str
    market_type: Optional[str] = None
    industry: Optional[str] = None
    year: int
    
    # 違規統計（include=violations 時回傳）
    violations_year_count: Optional[int] = None
    violations_year_fine: Optional[int] = None
    violations_total_count: Optional[int] = None
    violations_total_fine: Optional[int] = None
    
    # 環境違規統計
    env_violations_year_count: Optional[int] = None
    env_violations_year_fine: Optional[int] = None
    env_violations_total_count: Optional[int] = None
    env_violations_total_fine: Optional[int] = None
    
    # 完整 MOPS 物件（根據 include 參數回傳）
    employee_benefit: Optional[EmployeeBenefitResponse] = None
    non_manager_salary: Optional[NonManagerSalaryResponse] = None
    welfare_policy: Optional[WelfarePolicyResponse] = None
    salary_adjustment: Optional[SalaryAdjustmentResponse] = None


class YearlySummaryResponse(BaseModel):
    """年度摘要分頁回應"""
    items: List[YearlySummaryItem]
    total: int
    page: int
    size: int
    total_pages: int
