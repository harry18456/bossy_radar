"""
Leaderboard 相關 schemas
"""
from typing import Dict, List, Optional
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
    avg_salary: Optional[int] = None
    median_salary: Optional[int] = None


class ViolationLeaderboard(BaseModel):
    """違規排行榜 (包含次數與罰鍰的最高/最低)"""
    top_by_count: List[ViolationLeaderboardItem]
    bottom_by_count: List[ViolationLeaderboardItem]
    top_by_fine: List[ViolationLeaderboardItem]
    bottom_by_fine: List[ViolationLeaderboardItem]


class SalaryLeaderboard(BaseModel):
    """薪資排行榜 (包含平均與中位數的最高/最低)"""
    top_by_avg: List[SalaryLeaderboardItem]
    bottom_by_avg: List[SalaryLeaderboardItem]
    top_by_median: List[SalaryLeaderboardItem]
    bottom_by_median: List[SalaryLeaderboardItem]


class IndustrySalaryLeaderboardItem(LeaderboardItem):
    """同產業薪資排行榜項目"""
    industry: str
    avg_salary: Optional[int] = None
    median_salary: Optional[int] = None


class IndustrySalaryLeaderboard(BaseModel):
    """同產業薪資排行榜"""
    top_by_avg: List[IndustrySalaryLeaderboardItem]
    bottom_by_avg: List[IndustrySalaryLeaderboardItem]


class LeaderboardResponse(BaseModel):
    """排行榜 API 回應"""
    latest_year: int  # 最新年度 (民國年)
    violation_all_time: ViolationLeaderboard  # 歷年累計違規
    violation_yearly: Dict[int, ViolationLeaderboard]  # 各年度違規
    salary: Dict[int, SalaryLeaderboard]  # 各年度薪資
    salary_by_industry: Dict[int, Dict[str, IndustrySalaryLeaderboard]]  # 各年度各產業薪資
