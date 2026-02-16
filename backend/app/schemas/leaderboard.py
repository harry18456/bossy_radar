"""
Leaderboard 相關 schemas
"""

from pydantic import BaseModel


class LeaderboardItem(BaseModel):
    """排行榜基本項目"""

    company_code: str
    company_name: str


class ViolationLeaderboardItem(LeaderboardItem):
    """違規排行榜項目"""

    labor_count: int = 0
    labor_fine: int = 0
    env_count: int = 0
    env_fine: int = 0
    total_count: int = 0
    total_fine: int = 0


class SalaryLeaderboardItem(LeaderboardItem):
    """薪資排行榜項目"""

    avg_salary: int | None = None
    median_salary: int | None = None


class ViolationLeaderboard(BaseModel):
    """違規排行榜 (包含次數與罰鍰的最高/最低)"""

    top_by_count: list[ViolationLeaderboardItem]
    bottom_by_count: list[ViolationLeaderboardItem]
    top_by_fine: list[ViolationLeaderboardItem]
    bottom_by_fine: list[ViolationLeaderboardItem]


class SalaryLeaderboard(BaseModel):
    """薪資排行榜 (包含平均與中位數的最高/最低)"""

    top_by_avg: list[SalaryLeaderboardItem]
    bottom_by_avg: list[SalaryLeaderboardItem]
    top_by_median: list[SalaryLeaderboardItem]
    bottom_by_median: list[SalaryLeaderboardItem]


class IndustrySalaryLeaderboardItem(LeaderboardItem):
    """同產業薪資排行榜項目"""

    industry: str
    avg_salary: int | None = None
    median_salary: int | None = None
    eps: float | None = None


class IndustrySalaryLeaderboard(BaseModel):
    """同產業薪資排行榜"""

    top_by_median: list[IndustrySalaryLeaderboardItem]
    bottom_by_median: list[IndustrySalaryLeaderboardItem]
    top_by_eps: list[IndustrySalaryLeaderboardItem]
    bottom_by_eps: list[IndustrySalaryLeaderboardItem]


class LeaderboardResponse(BaseModel):
    """排行榜 API 回應"""

    latest_year: int  # 最新年度 (民國年)
    violation_all_time: ViolationLeaderboard  # 歷年累計違規
    violation_yearly: dict[int, ViolationLeaderboard]  # 各年度違規
    salary: dict[int, SalaryLeaderboard]  # 各年度薪資
    salary_by_industry: dict[
        int, dict[str, IndustrySalaryLeaderboard]
    ]  # 各年度各產業薪資
