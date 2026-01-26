from fastapi import APIRouter
from app.api.routes import companies, violations

api_router = APIRouter()
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(violations.router, prefix="/violations", tags=["violations"])
