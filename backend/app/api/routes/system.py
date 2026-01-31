from fastapi import APIRouter
from sqlmodel import select, func
from app.api.deps import SessionDep
from app.models.company import Company
from app.models.violation import Violation
from app.models.environmental_violation import EnvironmentalViolation
from app.models.employee_benefit import EmployeeBenefit
from app.models.non_manager_salary import NonManagerSalary
from app.models.welfare_policy import WelfarePolicy
from app.models.salary_adjustment import SalaryAdjustment
from app.schemas.system import SyncStatusResponse, SyncStatusItem

router = APIRouter()

@router.get("/sync-status", response_model=SyncStatusResponse)
def get_sync_status(session: SessionDep):
    # Company Sync Status
    companies_status = {}
    company_query = session.exec(
        select(
            Company.market_type,
            func.max(Company.last_updated).label("last_updated"),
            func.count(Company.code).label("count")
        ).group_by(Company.market_type)
    ).all()
    for row in company_query:
        companies_status[row[0]] = SyncStatusItem(last_updated=row[1], count=row[2])

    # Violation Sync Status
    violations_status = {}
    violation_query = session.exec(
        select(
            Violation.data_source,
            func.max(Violation.last_updated).label("last_updated"),
            func.count(Violation.id).label("count")
        ).group_by(Violation.data_source)
    ).all()
    for row in violation_query:
        violations_status[row[0]] = SyncStatusItem(last_updated=row[1], count=row[2])

    # MOPS Sync Status
    mops_status = {}
    
    # Non-manager Salary
    salary_data = session.exec(
        select(func.max(NonManagerSalary.last_updated), func.count(NonManagerSalary.id))
    ).first()
    if salary_data:
        mops_status["Salary"] = SyncStatusItem(last_updated=salary_data[0], count=salary_data[1])

    # Employee Benefit
    benefit_data = session.exec(
        select(func.max(EmployeeBenefit.last_updated), func.count(EmployeeBenefit.id))
    ).first()
    if benefit_data:
        mops_status["Benefit"] = SyncStatusItem(last_updated=benefit_data[0], count=benefit_data[1])

    # Welfare Policy
    welfare_data = session.exec(
        select(func.max(WelfarePolicy.last_updated), func.count(WelfarePolicy.id))
    ).first()
    if welfare_data:
        mops_status["Welfare"] = SyncStatusItem(last_updated=welfare_data[0], count=welfare_data[1])

    # Salary Adjustment
    adjustment_data = session.exec(
        select(func.max(SalaryAdjustment.last_updated), func.count(SalaryAdjustment.id))
    ).first()
    if adjustment_data:
        mops_status["Adjustment"] = SyncStatusItem(last_updated=adjustment_data[0], count=adjustment_data[1])

    # Environmental Violation Sync Status
    env_status = {}
    env_query = session.exec(
        select(
            EnvironmentalViolation.violation_type,
            func.max(EnvironmentalViolation.last_updated).label("last_updated"),
            func.count(EnvironmentalViolation.id).label("count")
        ).group_by(EnvironmentalViolation.violation_type)
    ).all()
    for row in env_query:
        # violation_type might be None, handle gracefully
        key = row[0] or "Unknown"
        env_status[key] = SyncStatusItem(last_updated=row[1], count=row[2])

    return SyncStatusResponse(
        companies=companies_status,
        violations=violations_status,
        environmental_violations=env_status,
        mops=mops_status
    )
