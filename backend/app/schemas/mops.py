"""
MOPS 員工薪資/福利資料相關 Schemas
"""

from datetime import datetime

from pydantic import BaseModel


# ========== Employee Benefit (t100sb14) ==========
class EmployeeBenefitResponse(BaseModel):
    id: int
    company_code: str | None = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    industry: str | None = None
    company_category: str | None = None

    # Matching EmployeeBenefit model fields
    employee_benefit_expense: int | None = None
    employee_salary_expense: int | None = None
    employee_count: int | None = None
    avg_benefit_per_employee: int | None = None
    avg_salary_current_year: int | None = None
    avg_salary_previous_year: int | None = None
    salary_change_rate: float | None = None
    eps: float | None = None
    industry_avg_benefit: int | None = None
    industry_avg_salary: int | None = None
    industry_avg_eps: float | None = None

    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ========== Non-Manager Salary (t100sb15) ==========
class NonManagerSalaryResponse(BaseModel):
    id: int
    company_code: str | None = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    industry: str | None = None
    employee_count: int | None = None

    # 薪資統計
    total_salary: int | None = None  # 員工薪資總額(仟元)
    avg_salary: int | None = None
    median_salary: int | None = None

    # 年度比較
    avg_salary_previous_year: int | None = None
    avg_salary_change: float | None = None
    median_salary_previous_year: int | None = None
    median_salary_change: float | None = None

    # 同業比較
    industry_avg_salary: int | None = None  # 同產業平均薪資(仟元)
    industry_median_salary: int | None = None  # 同產業薪資中位數(仟元)

    # EPS 相關
    eps: float | None = None
    industry_avg_eps: float | None = None

    # 薪資統計情形 (Y/N flags)
    is_avg_salary_under_500k: str | None = None
    is_better_eps_lower_salary: str | None = None
    is_eps_growth_salary_decrease: str | None = None

    # 經營績效與薪酬關聯 (質化指標)
    performance_salary_relation_note: str | None = None
    improvement_measures_note: str | None = None

    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ========== Welfare Policy (t100sb13) ==========
class WelfarePolicyResponse(BaseModel):
    id: int
    company_code: str | None = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    planned_salary_increase: str | None = None
    planned_salary_increase_note: str | None = None
    actual_salary_increase: str | None = None
    actual_salary_increase_note: str | None = None
    non_manager_salary_increase: str | None = None
    non_manager_salary_increase_note: str | None = None
    manager_salary_increase: str | None = None
    manager_salary_increase_note: str | None = None
    entry_salary_master: str | None = None
    entry_salary_bachelor: str | None = None
    entry_salary_highschool: str | None = None
    entry_salary_note: str | None = None
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ========== Salary Adjustment (t222sb01) ==========
class SalaryAdjustmentResponse(BaseModel):
    id: int
    company_code: str | None = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    industry: str | None = None
    pretax_net_profit: int | None = None
    allocation_ratio_min: str | None = None
    allocation_ratio_max: str | None = None
    board_resolution_date: str | None = None
    actual_allocation_ratio: str | None = None
    basic_employee_definition: str | None = None
    basic_employee_count: int | None = None
    total_allocation_amount: int | None = None
    allocation_method: str | None = None
    difference_amount: str | None = None
    difference_reason: str | None = None
    difference_handling: str | None = None
    note: str | None = None
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True
