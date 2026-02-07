"""
Leaderboard API Routes

Endpoints:
- GET /api/v1/leaderboards - 取得所有排行榜資料
"""
from typing import Dict, List
from datetime import date
from collections import defaultdict

from fastapi import APIRouter
from sqlmodel import select, func
from sqlalchemy import extract, text

from app.api.deps import SessionDep
from app.models.company import Company
from app.models.violation import Violation
from app.models.environmental_violation import EnvironmentalViolation
from app.models.non_manager_salary import NonManagerSalary
from app.schemas.leaderboard import (
    LeaderboardResponse,
    ViolationLeaderboard,
    ViolationLeaderboardItem,
    SalaryLeaderboard,
    SalaryLeaderboardItem,
    IndustrySalaryLeaderboard,
    IndustrySalaryLeaderboardItem,
)

router = APIRouter()

# 常數
LIMIT = 10
YEARS_TO_INCLUDE = 3  # 只回傳最近 N 年


def _get_recent_years(current_year: int) -> List[int]:
    """取得最近 N 年的年份列表 (民國年)"""
    return [current_year - i for i in range(YEARS_TO_INCLUDE)]


@router.get("", response_model=LeaderboardResponse)
def get_leaderboards(session: SessionDep):
    """
    取得所有排行榜資料 (優化版)
    
    回傳：
    - violation_all_time: 歷年累計違規排行榜
    - violation_yearly: 最近 3 年違規排行榜
    - salary: 最近 3 年薪資排行榜
    - salary_by_industry: 最近 3 年各產業薪資排行榜
    """
    # 計算年份範圍
    current_year = date.today().year - 1911  # 今年民國年
    recent_years = _get_recent_years(current_year)
    recent_years_ad = [y + 1911 for y in recent_years]  # 西元年
    
    # ========== Step 1: 取得必要的公司名稱 (只取有資料的) ==========
    # 先用 subquery 找出有違規或薪資資料的公司
    company_codes_with_data = set()
    
    # ========== Step 2: 歷年累計違規 - 使用 SQL 排序取 Top/Bottom ==========
    # 勞動違規 - Top by count
    labor_top_count = session.exec(
        select(
            Violation.company_code,
            func.count(Violation.id).label("count"),
            func.sum(Violation.fine_amount).label("fine"),
        )
        .where(Violation.company_code.isnot(None))
        .group_by(Violation.company_code)
        .order_by(text("count DESC"))
        .limit(LIMIT * 2)  # 多取一些以便合併
    ).all()
    
    # 勞動違規 - Top by fine
    labor_top_fine = session.exec(
        select(
            Violation.company_code,
            func.count(Violation.id).label("count"),
            func.sum(Violation.fine_amount).label("fine"),
        )
        .where(Violation.company_code.isnot(None))
        .group_by(Violation.company_code)
        .order_by(text("fine DESC"))
        .limit(LIMIT * 2)
    ).all()
    
    # 環境違規 - Top by count
    env_top_count = session.exec(
        select(
            EnvironmentalViolation.company_code,
            func.count(EnvironmentalViolation.id).label("count"),
            func.sum(EnvironmentalViolation.fine_amount).label("fine"),
        )
        .where(EnvironmentalViolation.company_code.isnot(None))
        .group_by(EnvironmentalViolation.company_code)
        .order_by(text("count DESC"))
        .limit(LIMIT * 2)
    ).all()
    
    # 環境違規 - Top by fine
    env_top_fine = session.exec(
        select(
            EnvironmentalViolation.company_code,
            func.count(EnvironmentalViolation.id).label("count"),
            func.sum(EnvironmentalViolation.fine_amount).label("fine"),
        )
        .where(EnvironmentalViolation.company_code.isnot(None))
        .group_by(EnvironmentalViolation.company_code)
        .order_by(text("fine DESC"))
        .limit(LIMIT * 2)
    ).all()
    
    # 收集需要查詢的公司代碼
    for row in labor_top_count + labor_top_fine + env_top_count + env_top_fine:
        company_codes_with_data.add(row[0])
    
    # ========== Step 3: 按年度違規 (只取最近 N 年) ==========
    yearly_violation_data = {}
    for year_roc in recent_years:
        year_ad = year_roc + 1911
        
        # 勞動違規該年度
        labor_year = session.exec(
            select(
                Violation.company_code,
                func.count(Violation.id).label("count"),
                func.sum(Violation.fine_amount).label("fine"),
            )
            .where(Violation.company_code.isnot(None))
            .where(extract('year', Violation.penalty_date) == year_ad)
            .group_by(Violation.company_code)
            .order_by(text("count DESC"))
            .limit(LIMIT * 2)
        ).all()
        
        # 環境違規該年度
        env_year = session.exec(
            select(
                EnvironmentalViolation.company_code,
                func.count(EnvironmentalViolation.id).label("count"),
                func.sum(EnvironmentalViolation.fine_amount).label("fine"),
            )
            .where(EnvironmentalViolation.company_code.isnot(None))
            .where(extract('year', EnvironmentalViolation.penalty_date) == year_ad)
            .group_by(EnvironmentalViolation.company_code)
            .order_by(text("count DESC"))
            .limit(LIMIT * 2)
        ).all()
        
        yearly_violation_data[year_roc] = {"labor": labor_year, "env": env_year}
        for row in labor_year + env_year:
            company_codes_with_data.add(row[0])
    
    # ========== Step 4: 薪資排行 (只取最近 N 年) ==========
    salary_data = {}
    salary_by_industry_data = {}
    
    for year_roc in recent_years:
        # 整體 Top by avg
        top_avg = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.avg_salary.isnot(None))
            .order_by(NonManagerSalary.avg_salary.desc())
            .limit(LIMIT)
        ).all()
        
        # 整體 Bottom by avg
        bottom_avg = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.avg_salary.isnot(None))
            .order_by(NonManagerSalary.avg_salary.asc())
            .limit(LIMIT)
        ).all()
        
        # 整體 Top by median
        top_median = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.median_salary.isnot(None))
            .order_by(NonManagerSalary.median_salary.desc())
            .limit(LIMIT)
        ).all()
        
        # 整體 Bottom by median
        bottom_median = session.exec(
            select(NonManagerSalary)
            .where(NonManagerSalary.company_code.isnot(None))
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.median_salary.isnot(None))
            .order_by(NonManagerSalary.median_salary.asc())
            .limit(LIMIT)
        ).all()
        
        salary_data[year_roc] = {
            "top_avg": top_avg,
            "bottom_avg": bottom_avg,
            "top_median": top_median,
            "bottom_median": bottom_median,
        }
        
        for s in top_avg + bottom_avg + top_median + bottom_median:
            company_codes_with_data.add(s.company_code)
        
        # 按產業分組 (只取該年度所有產業，每個產業 top/bottom)
        industries = session.exec(
            select(NonManagerSalary.industry)
            .where(NonManagerSalary.year == year_roc)
            .where(NonManagerSalary.industry.isnot(None))
            .distinct()
        ).all()
        
        salary_by_industry_data[year_roc] = {}
        for (industry,) in [(i,) if isinstance(i, str) else i for i in industries]:
            if not industry:
                continue
            
            ind_top = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.industry == industry)
                .where(NonManagerSalary.avg_salary.isnot(None))
                .order_by(NonManagerSalary.avg_salary.desc())
                .limit(LIMIT)
            ).all()
            
            ind_bottom = session.exec(
                select(NonManagerSalary)
                .where(NonManagerSalary.company_code.isnot(None))
                .where(NonManagerSalary.year == year_roc)
                .where(NonManagerSalary.industry == industry)
                .where(NonManagerSalary.avg_salary.isnot(None))
                .order_by(NonManagerSalary.avg_salary.asc())
                .limit(LIMIT)
            ).all()
            
            salary_by_industry_data[year_roc][industry] = {
                "top": ind_top,
                "bottom": ind_bottom,
            }
            for s in ind_top + ind_bottom:
                company_codes_with_data.add(s.company_code)
    
    # ========== Step 5: 只查詢需要的公司名稱 ==========
    company_map = {}
    if company_codes_with_data:
        companies = session.exec(
            select(Company).where(Company.code.in_(list(company_codes_with_data)))
        ).all()
        company_map = {c.code: c for c in companies}
    
    # ========== Step 6: 建構回應 ==========
    # 合併勞動+環境違規 (歷年累計)
    all_time_stats: Dict[str, dict] = defaultdict(lambda: {
        "name": "", "labor_count": 0, "labor_fine": 0, "env_count": 0, "env_fine": 0
    })
    for row in labor_top_count + labor_top_fine:
        code = row[0]
        all_time_stats[code]["name"] = company_map.get(code, Company(name="")).name
        all_time_stats[code]["labor_count"] = max(all_time_stats[code]["labor_count"], row[1])
        all_time_stats[code]["labor_fine"] = max(all_time_stats[code]["labor_fine"], row[2] or 0)
    for row in env_top_count + env_top_fine:
        code = row[0]
        all_time_stats[code]["name"] = company_map.get(code, Company(name="")).name
        all_time_stats[code]["env_count"] = max(all_time_stats[code]["env_count"], row[1])
        all_time_stats[code]["env_fine"] = max(all_time_stats[code]["env_fine"], row[2] or 0)
    
    violation_all_time = _build_violation_leaderboard(all_time_stats)
    
    # 各年度違規
    violation_yearly = {}
    for year_roc, data in yearly_violation_data.items():
        yearly_stats: Dict[str, dict] = defaultdict(lambda: {
            "name": "", "labor_count": 0, "labor_fine": 0, "env_count": 0, "env_fine": 0
        })
        for row in data["labor"]:
            code = row[0]
            yearly_stats[code]["name"] = company_map.get(code, Company(name="")).name
            yearly_stats[code]["labor_count"] = row[1]
            yearly_stats[code]["labor_fine"] = row[2] or 0
        for row in data["env"]:
            code = row[0]
            yearly_stats[code]["name"] = company_map.get(code, Company(name="")).name
            yearly_stats[code]["env_count"] = row[1]
            yearly_stats[code]["env_fine"] = row[2] or 0
        
        if yearly_stats:
            violation_yearly[year_roc] = _build_violation_leaderboard(yearly_stats)
    
    # 各年度薪資
    salary = {}
    for year_roc, data in salary_data.items():
        salary[year_roc] = SalaryLeaderboard(
            top_by_avg=[_to_salary_item(s, company_map) for s in data["top_avg"]],
            bottom_by_avg=[_to_salary_item(s, company_map) for s in data["bottom_avg"]],
            top_by_median=[_to_salary_item(s, company_map) for s in data["top_median"]],
            bottom_by_median=[_to_salary_item(s, company_map) for s in data["bottom_median"]],
        )
    
    # 各年度各產業薪資
    salary_by_industry = {}
    for year_roc, industries in salary_by_industry_data.items():
        salary_by_industry[year_roc] = {}
        for industry, data in industries.items():
            salary_by_industry[year_roc][industry] = IndustrySalaryLeaderboard(
                top_by_avg=[_to_industry_salary_item(s, company_map) for s in data["top"]],
                bottom_by_avg=[_to_industry_salary_item(s, company_map) for s in data["bottom"]],
            )
    
    return LeaderboardResponse(
        latest_year=current_year,
        violation_all_time=violation_all_time,
        violation_yearly=violation_yearly,
        salary=salary,
        salary_by_industry=salary_by_industry,
    )


def _build_violation_leaderboard(data: Dict[str, dict]) -> ViolationLeaderboard:
    """從違規統計資料建構 ViolationLeaderboard"""
    items = [
        ViolationLeaderboardItem(
            company_code=code,
            company_name=info["name"],
            labor_count=info["labor_count"],
            labor_fine=info["labor_fine"],
            env_count=info["env_count"],
            env_fine=info["env_fine"],
            total_count=info["labor_count"] + info["env_count"],
            total_fine=info["labor_fine"] + info["env_fine"],
        )
        for code, info in data.items()
        if info["labor_count"] + info["env_count"] > 0
    ]
    
    by_count = sorted(items, key=lambda x: x.total_count, reverse=True)
    by_fine = sorted(items, key=lambda x: x.total_fine, reverse=True)
    
    return ViolationLeaderboard(
        top_by_count=by_count[:LIMIT],
        bottom_by_count=by_count[-LIMIT:][::-1] if len(by_count) >= LIMIT else by_count[::-1],
        top_by_fine=by_fine[:LIMIT],
        bottom_by_fine=by_fine[-LIMIT:][::-1] if len(by_fine) >= LIMIT else by_fine[::-1],
    )


def _to_salary_item(s: NonManagerSalary, company_map: Dict[str, Company]) -> SalaryLeaderboardItem:
    return SalaryLeaderboardItem(
        company_code=s.company_code,
        company_name=company_map.get(s.company_code, Company(name=s.company_name)).name,
        avg_salary=s.avg_salary,
        median_salary=s.median_salary,
    )


def _to_industry_salary_item(s: NonManagerSalary, company_map: Dict[str, Company]) -> IndustrySalaryLeaderboardItem:
    return IndustrySalaryLeaderboardItem(
        company_code=s.company_code,
        company_name=company_map.get(s.company_code, Company(name=s.company_name)).name,
        industry=s.industry or "",
        avg_salary=s.avg_salary,
        median_salary=s.median_salary,
    )
