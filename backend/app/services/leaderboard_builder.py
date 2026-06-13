"""Single shared assembly for the leaderboards response.

Both the leaderboard route and the static exporter MUST obtain the response
from build_leaderboard_response so their output cannot drift (BACKEND_AUDIT
H8). Violation boards aggregate the FULL company population (no truncated
top pool), so bottom boards are the true global ascending slice
(BACKEND_AUDIT NF2) and top boards are the exact descending slice.
"""

from collections import defaultdict
from datetime import date

from sqlalchemy import extract
from sqlmodel import Session, func, select

from app.models.company import Company
from app.models.environmental_violation import EnvironmentalViolation
from app.models.non_manager_salary import NonManagerSalary
from app.models.violation import Violation
from app.schemas.leaderboard import (
    IndustrySalaryLeaderboard,
    IndustrySalaryLeaderboardItem,
    LeaderboardResponse,
    SalaryLeaderboard,
    SalaryLeaderboardItem,
    ViolationLeaderboard,
    ViolationLeaderboardItem,
)

DEFAULT_LIMIT = 10
DEFAULT_YEARS_TO_INCLUDE = 3  # 只回傳最近 N 年


def _violation_aggregates(session: Session, model, year_ad: int | None = None):
    """Full (no-limit) per-company aggregation; row count is bounded by the
    number of companies, so slicing happens in Python with exact semantics."""
    query = (
        select(
            model.company_code,
            func.count(model.id).label("count"),
            func.sum(model.fine_amount).label("fine"),
        )
        .where(model.company_code.isnot(None))
        .group_by(model.company_code)
    )
    if year_ad is not None:
        query = query.where(extract("year", model.penalty_date) == year_ad)
    return session.exec(query).all()


def _merge_violation_stats(labor_rows, env_rows) -> dict[str, dict]:
    stats: dict[str, dict] = defaultdict(
        lambda: {
            "labor_count": 0,
            "labor_fine": 0,
            "env_count": 0,
            "env_fine": 0,
        }
    )
    for code, count, fine in labor_rows:
        stats[code]["labor_count"] = count
        stats[code]["labor_fine"] = fine or 0
    for code, count, fine in env_rows:
        stats[code]["env_count"] = count
        stats[code]["env_fine"] = fine or 0
    return stats


def build_leaderboard_response(
    session: Session,
    limit: int = DEFAULT_LIMIT,
    years_to_include: int = DEFAULT_YEARS_TO_INCLUDE,
) -> LeaderboardResponse:
    current_year = date.today().year - 1911  # 今年民國年
    recent_years = [current_year - i for i in range(years_to_include)]

    # ========== 違規彙總（全量，歷年累計與各年度） ==========
    all_time_stats = _merge_violation_stats(
        _violation_aggregates(session, Violation),
        _violation_aggregates(session, EnvironmentalViolation),
    )

    yearly_stats_by_year: dict[int, dict[str, dict]] = {}
    for year_roc in recent_years:
        year_ad = year_roc + 1911
        stats = _merge_violation_stats(
            _violation_aggregates(session, Violation, year_ad),
            _violation_aggregates(session, EnvironmentalViolation, year_ad),
        )
        if stats:
            yearly_stats_by_year[year_roc] = stats

    company_codes_with_data: set[str] = set(all_time_stats.keys())
    for stats in yearly_stats_by_year.values():
        company_codes_with_data.update(stats.keys())

    # ========== 薪資排行（最近 N 年） ==========
    salary_data: dict[int, dict] = {}
    salary_by_industry_data: dict[int, dict] = {}

    for year_roc in recent_years:
        top_avg = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.avg_salary.isnot(None))
            .order_by(NonManagerSalary.avg_salary.desc())
            .limit(limit)
        ).all()

        bottom_avg = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.avg_salary.isnot(None))
            .order_by(NonManagerSalary.avg_salary.asc())
            .limit(limit)
        ).all()

        top_median = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.median_salary.isnot(None))
            .order_by(NonManagerSalary.median_salary.desc())
            .limit(limit)
        ).all()

        bottom_median = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.median_salary.isnot(None))
            .order_by(NonManagerSalary.median_salary.asc())
            .limit(limit)
        ).all()

        salary_data[year_roc] = {
            "top_avg": top_avg,
            "bottom_avg": bottom_avg,
            "top_median": top_median,
            "bottom_median": bottom_median,
        }

        for s in top_avg + bottom_avg + top_median + bottom_median:
            company_codes_with_data.add(s.company_code)

        # 按產業分組
        industries = session.exec(
            select(NonManagerSalary.industry)
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.industry.isnot(None))
            .distinct()
        ).all()

        salary_by_industry_data[year_roc] = {}
        for industry_result in industries:
            industry = (
                industry_result
                if isinstance(industry_result, str)
                else industry_result[0]
            )
            if not industry:
                continue

            ind_top = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.industry == industry)
                .where(NonManagerSalary.median_salary.isnot(None))
                .order_by(NonManagerSalary.median_salary.desc())
                .limit(limit)
            ).all()

            ind_bottom = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.industry == industry)
                .where(NonManagerSalary.median_salary.isnot(None))
                .order_by(NonManagerSalary.median_salary.asc())
                .limit(limit)
            ).all()

            ind_top_eps = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.industry == industry)
                .where(NonManagerSalary.eps.isnot(None))
                .order_by(NonManagerSalary.eps.desc())
                .limit(limit)
            ).all()

            ind_bottom_eps = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.industry == industry)
                .where(NonManagerSalary.eps.isnot(None))
                .order_by(NonManagerSalary.eps.asc())
                .limit(limit)
            ).all()

            salary_by_industry_data[year_roc][industry] = {
                "top": ind_top,
                "bottom": ind_bottom,
                "top_eps": ind_top_eps,
                "bottom_eps": ind_bottom_eps,
            }
            for s in ind_top + ind_bottom + ind_top_eps + ind_bottom_eps:
                company_codes_with_data.add(s.company_code)

    # ========== 公司名稱 ==========
    company_map: dict[str, Company] = {}
    if company_codes_with_data:
        companies = session.exec(
            select(Company).where(Company.code.in_(list(company_codes_with_data)))
        ).all()
        company_map = {c.code: c for c in companies}

    # ========== 建構回應 ==========
    def build_violation_leaderboard(stats: dict[str, dict]) -> ViolationLeaderboard:
        items = [
            ViolationLeaderboardItem(
                company_code=code,
                company_name=company_map.get(code, Company(name="")).name,
                labor_count=info["labor_count"],
                labor_fine=info["labor_fine"],
                env_count=info["env_count"],
                env_fine=info["env_fine"],
                total_count=info["labor_count"] + info["env_count"],
                total_fine=info["labor_fine"] + info["env_fine"],
            )
            for code, info in stats.items()
            if info["labor_count"] + info["env_count"] > 0
        ]

        # Exact global slices over the full population; company_code breaks
        # ties so rankings are deterministic across runs.
        return ViolationLeaderboard(
            top_by_count=sorted(items, key=lambda x: (-x.total_count, x.company_code))[
                :limit
            ],
            bottom_by_count=sorted(
                items, key=lambda x: (x.total_count, x.company_code)
            )[:limit],
            top_by_fine=sorted(items, key=lambda x: (-x.total_fine, x.company_code))[
                :limit
            ],
            bottom_by_fine=sorted(items, key=lambda x: (x.total_fine, x.company_code))[
                :limit
            ],
        )

    def to_salary_item(s: NonManagerSalary) -> SalaryLeaderboardItem:
        return SalaryLeaderboardItem(
            company_code=s.company_code,
            company_name=company_map.get(
                s.company_code, Company(name=s.company_name)
            ).name,
            avg_salary=s.avg_salary,
            median_salary=s.median_salary,
        )

    def to_industry_salary_item(s: NonManagerSalary) -> IndustrySalaryLeaderboardItem:
        return IndustrySalaryLeaderboardItem(
            company_code=s.company_code,
            company_name=company_map.get(
                s.company_code, Company(name=s.company_name)
            ).name,
            industry=s.industry or "",
            avg_salary=s.avg_salary,
            median_salary=s.median_salary,
            eps=s.eps,
        )

    violation_all_time = build_violation_leaderboard(all_time_stats)

    violation_yearly = {
        year_roc: build_violation_leaderboard(stats)
        for year_roc, stats in yearly_stats_by_year.items()
    }

    salary = {}
    for year_roc, data in salary_data.items():
        salary[year_roc] = SalaryLeaderboard(
            top_by_avg=[to_salary_item(s) for s in data["top_avg"]],
            bottom_by_avg=[to_salary_item(s) for s in data["bottom_avg"]],
            top_by_median=[to_salary_item(s) for s in data["top_median"]],
            bottom_by_median=[to_salary_item(s) for s in data["bottom_median"]],
        )

    salary_by_industry = {}
    for year_roc, industries_data in salary_by_industry_data.items():
        salary_by_industry[year_roc] = {}
        for industry, data in industries_data.items():
            salary_by_industry[year_roc][industry] = IndustrySalaryLeaderboard(
                top_by_median=[to_industry_salary_item(s) for s in data["top"]],
                bottom_by_median=[to_industry_salary_item(s) for s in data["bottom"]],
                top_by_eps=[to_industry_salary_item(s) for s in data["top_eps"]],
                bottom_by_eps=[to_industry_salary_item(s) for s in data["bottom_eps"]],
            )

    return LeaderboardResponse(
        latest_year=current_year,
        violation_all_time=violation_all_time,
        violation_yearly=violation_yearly,
        salary=salary,
        salary_by_industry=salary_by_industry,
    )
