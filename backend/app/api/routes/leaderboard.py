"""
Leaderboard API Routes

Endpoints:
- GET /api/v1/leaderboards - 取得所有排行榜資料

組裝邏輯與靜態 exporter 共用（見 app/services/leaderboard_builder.py），
route 與 export 的輸出由 parity 測試鎖定不得 drift。
"""

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.leaderboard import LeaderboardResponse
from app.services.leaderboard_builder import build_leaderboard_response

router = APIRouter()


@router.get("", response_model=LeaderboardResponse)
def get_leaderboards(session: SessionDep):
    """
    取得所有排行榜資料

    回傳：
    - violation_all_time: 歷年累計違規排行榜
    - violation_yearly: 最近 3 年違規排行榜
    - salary: 最近 3 年薪資排行榜
    - salary_by_industry: 最近 3 年各產業薪資排行榜
    """
    return build_leaderboard_response(session)
