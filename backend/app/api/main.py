from fastapi import APIRouter
from app.api.routes import companies, violations, mops, aggregation, system, environmental_violations

api_router = APIRouter()

# 注意：aggregation 的 /companies/yearly-summary 必須在 companies 的動態路由之前註冊
# 所以先註冊 aggregation，再註冊 companies
api_router.include_router(aggregation.router, prefix="/companies", tags=["aggregation"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(violations.router, prefix="/violations", tags=["violations"])
api_router.include_router(environmental_violations.router, prefix="/environmental-violations", tags=["environmental-violations"])
api_router.include_router(mops.router, prefix="/mops", tags=["mops"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
