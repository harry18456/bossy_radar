"""Single shared assembly for yearly summary items.

Both the aggregation route and the static exporter MUST obtain items from
build_yearly_summary_items so their output cannot drift (BACKEND_AUDIT NF1/H8).
The route layers sorting and pagination on top; the exporter groups by year.
"""

from sqlalchemy import extract
from sqlmodel import Session, col, func, select

from app.models.company import Company
from app.models.employee_benefit import EmployeeBenefit
from app.models.environmental_violation import EnvironmentalViolation
from app.models.non_manager_salary import NonManagerSalary
from app.models.salary_adjustment import SalaryAdjustment
from app.models.violation import Violation
from app.models.welfare_policy import WelfarePolicy
from app.schemas.aggregation import YearlySummaryItem
from app.schemas.mops import (
    EmployeeBenefitResponse,
    NonManagerSalaryResponse,
    SalaryAdjustmentResponse,
    WelfarePolicyResponse,
)

ALL_INCLUDES = frozenset(
    {
        "violations",
        "env_violations",
        "employee_benefit",
        "non_manager_salary",
        "welfare_policy",
        "salary_adjustment",
    }
)


def resolve_include_set(include: list[str] | set[str] | None) -> set[str]:
    """Expand the include parameter; "all" selects every data category."""
    include_set = set(include) if include else set()
    if "all" in include_set:
        return set(ALL_INCLUDES)
    return include_set & ALL_INCLUDES


def build_yearly_summary_items(
    session: Session,
    include: list[str] | set[str] | None = None,
    year: list[int] | None = None,
    company_code: list[str] | None = None,
    market_type: list[str] | None = None,
    industry: list[str] | None = None,
) -> list[YearlySummaryItem]:
    """Assemble the company × year summary matrix.

    Semantics (kept identical for route and exporter):
    - Year set derives from EmployeeBenefit ROC years plus violation /
      environmental-violation penalty_date AD years minus 1911.
    - total counts/fines span all years; yearly buckets key on ROC year;
      null penalty_date rows count only toward totals.
    - A (company, year) item exists only when at least one source has data.
    - Items are ordered year descending, company order stable.
    """
    include_set = resolve_include_set(include)
    include_violations = "violations" in include_set
    include_env_violations = "env_violations" in include_set
    include_employee_benefit = "employee_benefit" in include_set
    include_non_manager_salary = "non_manager_salary" in include_set
    include_welfare_policy = "welfare_policy" in include_set
    include_salary_adjustment = "salary_adjustment" in include_set

    # Step 1: 取得所有年份（從 MOPS + 違規資料）
    years_set: set[int] = set()

    eb_years_query = select(EmployeeBenefit.year).distinct()
    if year:
        eb_years_query = eb_years_query.where(col(EmployeeBenefit.year).in_(year))
    years_set.update(session.exec(eb_years_query).all())

    if include_violations:
        vio_years_query = (
            select(extract("year", Violation.penalty_date).label("year"))
            .distinct()
            .where(Violation.penalty_date.is_not(None))
        )
        vio_years_raw = session.exec(vio_years_query).all()
        vio_years_roc = {int(y) - 1911 for y in vio_years_raw if y}
        if year:
            vio_years_roc = {y for y in vio_years_roc if y in year}
        years_set.update(vio_years_roc)

    if include_env_violations:
        env_years_query = (
            select(extract("year", EnvironmentalViolation.penalty_date).label("year"))
            .distinct()
            .where(EnvironmentalViolation.penalty_date.is_not(None))
        )
        env_years_raw = session.exec(env_years_query).all()
        env_years_roc = {int(y) - 1911 for y in env_years_raw if y}
        if year:
            env_years_roc = {y for y in env_years_roc if y in year}
        years_set.update(env_years_roc)

    available_years = sorted(years_set, reverse=True)
    if not available_years:
        return []

    # Step 2: 取得公司列表
    companies_query = select(Company)
    if company_code:
        companies_query = companies_query.where(col(Company.code).in_(company_code))
    if market_type:
        companies_query = companies_query.where(
            col(Company.market_type).in_(market_type)
        )
    if industry:
        companies_query = companies_query.where(col(Company.industry).in_(industry))

    companies = session.exec(companies_query).all()
    if not companies:
        return []

    # Step 3: 建立公司代號集合
    company_codes = [c.code for c in companies]
    company_map = {c.code: c for c in companies}

    # Step 4: 預先查詢關聯資料（根據 include 參數）
    violations_total: dict[str, dict] = {}
    violations_by_year: dict[tuple, dict] = {}
    if include_violations:
        violations_total_query = session.exec(
            select(
                Violation.company_code,
                func.count(Violation.id).label("count"),
                func.sum(Violation.fine_amount).label("fine"),
            )
            .where(col(Violation.company_code).in_(company_codes))
            .group_by(Violation.company_code)
        ).all()
        for row in violations_total_query:
            violations_total[row[0]] = {"count": row[1], "fine": row[2] or 0}

        violations_year_query = session.exec(
            select(
                Violation.company_code,
                extract("year", Violation.penalty_date).label("year"),
                func.count(Violation.id).label("count"),
                func.sum(Violation.fine_amount).label("fine"),
            )
            .where(col(Violation.company_code).in_(company_codes))
            .group_by(Violation.company_code, extract("year", Violation.penalty_date))
        ).all()
        for row in violations_year_query:
            key = (row[0], int(row[1]) - 1911 if row[1] else None)  # 西元轉民國
            violations_by_year[key] = {"count": row[2], "fine": row[3] or 0}

    env_violations_total: dict[str, dict] = {}
    env_violations_by_year: dict[tuple, dict] = {}
    if include_env_violations:
        env_violations_total_query = session.exec(
            select(
                EnvironmentalViolation.company_code,
                func.count(EnvironmentalViolation.id).label("count"),
                func.sum(EnvironmentalViolation.fine_amount).label("fine"),
            )
            .where(col(EnvironmentalViolation.company_code).in_(company_codes))
            .group_by(EnvironmentalViolation.company_code)
        ).all()
        for row in env_violations_total_query:
            env_violations_total[row[0]] = {"count": row[1], "fine": row[2] or 0}

        env_violations_year_query = session.exec(
            select(
                EnvironmentalViolation.company_code,
                extract("year", EnvironmentalViolation.penalty_date).label("year"),
                func.count(EnvironmentalViolation.id).label("count"),
                func.sum(EnvironmentalViolation.fine_amount).label("fine"),
            )
            .where(col(EnvironmentalViolation.company_code).in_(company_codes))
            .group_by(
                EnvironmentalViolation.company_code,
                extract("year", EnvironmentalViolation.penalty_date),
            )
        ).all()
        for row in env_violations_year_query:
            key = (row[0], int(row[1]) - 1911 if row[1] else None)  # 西元轉民國
            env_violations_by_year[key] = {"count": row[2], "fine": row[3] or 0}

    # 員工福利（必須查詢用於判斷資料是否存在）
    benefits_map = {}
    benefits = session.exec(
        select(EmployeeBenefit).where(
            col(EmployeeBenefit.company_code).in_(company_codes)
        )
    ).all()
    for b in benefits:
        benefits_map[(b.company_code, b.year)] = b

    salaries_map = {}
    salaries = session.exec(
        select(NonManagerSalary).where(
            col(NonManagerSalary.company_code).in_(company_codes)
        )
    ).all()
    for s in salaries:
        salaries_map[(s.company_code, s.year)] = s

    policies_map = {}
    policies = session.exec(
        select(WelfarePolicy).where(col(WelfarePolicy.company_code).in_(company_codes))
    ).all()
    for p in policies:
        policies_map[(p.company_code, p.year)] = p

    adjustments_map = {}
    adjustments = session.exec(
        select(SalaryAdjustment).where(
            col(SalaryAdjustment.company_code).in_(company_codes)
        )
    ).all()
    for a in adjustments:
        adjustments_map[(a.company_code, a.year)] = a

    # Step 5: 組合結果
    items: list[YearlySummaryItem] = []
    for y in available_years:
        for code in company_codes:
            company = company_map.get(code)
            if not company:
                continue

            benefit = benefits_map.get((code, y))
            salary = salaries_map.get((code, y))
            policy = policies_map.get((code, y))
            adjustment = adjustments_map.get((code, y))

            has_violations = violations_by_year.get((code, y), {}).get("count", 0) > 0
            has_env_violations = (
                env_violations_by_year.get((code, y), {}).get("count", 0) > 0
            )

            if (
                not benefit
                and not salary
                and not policy
                and not adjustment
                and not has_violations
                and not has_env_violations
            ):
                continue

            item = YearlySummaryItem(
                company_code=code,
                company_name=company.name,
                market_type=company.market_type,
                industry=company.industry,
                year=y,
            )

            if include_violations:
                vio_year = violations_by_year.get((code, y), {"count": 0, "fine": 0})
                vio_total = violations_total.get(code, {"count": 0, "fine": 0})
                item.violations_year_count = vio_year["count"]
                item.violations_year_fine = vio_year["fine"]
                item.violations_total_count = vio_total["count"]
                item.violations_total_fine = vio_total["fine"]

            if include_env_violations:
                env_year = env_violations_by_year.get(
                    (code, y), {"count": 0, "fine": 0}
                )
                env_total = env_violations_total.get(code, {"count": 0, "fine": 0})
                item.env_violations_year_count = env_year["count"]
                item.env_violations_year_fine = env_year["fine"]
                item.env_violations_total_count = env_total["count"]
                item.env_violations_total_fine = env_total["fine"]

            if include_employee_benefit and benefit:
                item.employee_benefit = EmployeeBenefitResponse.model_validate(benefit)

            if include_non_manager_salary and salary:
                item.non_manager_salary = NonManagerSalaryResponse.model_validate(
                    salary
                )

            if include_welfare_policy and policy:
                item.welfare_policy = WelfarePolicyResponse.model_validate(policy)

            if include_salary_adjustment and adjustment:
                item.salary_adjustment = SalaryAdjustmentResponse.model_validate(
                    adjustment
                )

            items.append(item)

    return items
