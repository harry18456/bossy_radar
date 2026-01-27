"""
MOPS 員工薪資/福利資料相關 Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ========== Employee Benefit (t100sb14) ==========
class EmployeeBenefitResponse(BaseModel):
    id: int
    company_code: Optional[str] = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    employee_salary: Optional[int] = None
    salary_per_employee: Optional[int] = None
    supervisor_salary: Optional[int] = None
    median_employee_salary: Optional[int] = None
    non_supervisor_count: Optional[int] = None
    non_supervisor_salary: Optional[int] = None
    salary_per_non_supervisor: Optional[int] = None
    salary_change_rate: Optional[float] = None
    company_category: Optional[str] = None
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ========== Non-Manager Salary (t100sb15) ==========
class NonManagerSalaryResponse(BaseModel):
    id: int
    company_code: Optional[str] = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None
    avg_salary: Optional[int] = None
    median_salary: Optional[int] = None
    avg_salary_change: Optional[float] = None
    median_salary_change: Optional[float] = None
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ========== Welfare Policy (t100sb13) ==========
class WelfarePolicyResponse(BaseModel):
    id: int
    company_code: Optional[str] = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    planned_salary_increase: Optional[str] = None
    planned_salary_increase_note: Optional[str] = None
    actual_salary_increase: Optional[str] = None
    actual_salary_increase_note: Optional[str] = None
    non_manager_salary_increase: Optional[str] = None
    non_manager_salary_increase_note: Optional[str] = None
    manager_salary_increase: Optional[str] = None
    manager_salary_increase_note: Optional[str] = None
    entry_salary_master: Optional[str] = None
    entry_salary_bachelor: Optional[str] = None
    entry_salary_highschool: Optional[str] = None
    entry_salary_note: Optional[str] = None
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ========== Salary Adjustment (t222sb01) ==========
class SalaryAdjustmentResponse(BaseModel):
    id: int
    company_code: Optional[str] = None
    raw_company_code: str
    company_name: str
    year: int
    market_type: str
    industry: Optional[str] = None
    pretax_net_profit: Optional[int] = None
    allocation_ratio_min: Optional[str] = None
    allocation_ratio_max: Optional[str] = None
    board_resolution_date: Optional[str] = None
    actual_allocation_ratio: Optional[str] = None
    basic_employee_definition: Optional[str] = None
    basic_employee_count: Optional[int] = None
    total_allocation_amount: Optional[int] = None
    allocation_method: Optional[str] = None
    difference_amount: Optional[str] = None
    difference_reason: Optional[str] = None
    difference_handling: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True
