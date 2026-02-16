"""
公司聚合 API Schemas
"""

from pydantic import BaseModel, Field

from app.schemas.company import CompanyResponse
from app.schemas.environmental_violation import EnvironmentalViolationPublic
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    SalaryAdjustmentResponse,
    WelfarePolicyResponse,
)
from app.schemas.violation import ViolationPublic


# ========== Company Profile ==========
class CompanyProfileResponse(BaseModel):
    """單一公司完整資料"""

    company: CompanyResponse
    violations: list[ViolationPublic]
    employee_benefits: list[EmployeeBenefitResponse]
    non_manager_salaries: list[NonManagerSalaryResponse]
    welfare_policies: list[WelfarePolicyResponse]
    salary_adjustments: list[SalaryAdjustmentResponse]
    environmental_violations: list[EnvironmentalViolationPublic] = Field(
        description="環境違規紀錄"
    )


# ========== Yearly Summary ==========
class YearlySummaryItem(BaseModel):
    """公司年度摘要"""

    # 公司基本資料（必定回傳）
    company_code: str
    company_name: str
    market_type: str | None = None
    industry: str | None = None
    year: int

    # 違規統計（include=violations 時回傳）
    violations_year_count: int | None = None
    violations_year_fine: int | None = None
    violations_total_count: int | None = None
    violations_total_fine: int | None = None

    # 環境違規統計
    env_violations_year_count: int | None = None
    env_violations_year_fine: int | None = None
    env_violations_total_count: int | None = None
    env_violations_total_fine: int | None = None

    # 完整 MOPS 物件（根據 include 參數回傳）
    employee_benefit: EmployeeBenefitResponse | None = None
    non_manager_salary: NonManagerSalaryResponse | None = None
    welfare_policy: WelfarePolicyResponse | None = None
    salary_adjustment: SalaryAdjustmentResponse | None = None


class YearlySummaryResponse(BaseModel):
    """年度摘要分頁回應"""

    items: list[YearlySummaryItem]
    total: int
    page: int
    size: int
    total_pages: int
