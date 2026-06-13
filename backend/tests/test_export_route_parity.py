"""Parity tests: exported static JSON must equal the corresponding API responses.

Covers specs:
- Yearly summary assembly SHALL have a single shared implementation
- Exported yearly summary index SHALL be derived from builder output
- Leaderboard assembly SHALL have a single shared implementation
"""

import json
from datetime import date
from pathlib import Path

import pytest

from app.models.employee_benefit import EmployeeBenefit
from app.models.environmental_violation import EnvironmentalViolation
from app.models.non_manager_salary import NonManagerSalary
from app.models.salary_adjustment import SalaryAdjustment
from app.models.violation import Violation
from app.models.welfare_policy import WelfarePolicy
from app.services.export_service import ExportService


@pytest.fixture
def seed_full_dataset(test_session, seed_companies):
    """Violations, env violations, and all four MOPS tables across years."""
    rows = [
        # 2330: violations in AD 2024 (ROC 113) and AD 2022 (ROC 111)
        Violation(
            company_code="2330",
            company_name="台灣積體電路製造股份有限公司",
            data_source="OccupationalSafety",
            penalty_date=date(2024, 3, 1),
            fine_amount=50000,
        ),
        Violation(
            company_code="2330",
            company_name="台灣積體電路製造股份有限公司",
            data_source="OccupationalSafety",
            penalty_date=date(2024, 8, 15),
            fine_amount=0,
        ),
        Violation(
            company_code="2330",
            company_name="台灣積體電路製造股份有限公司",
            data_source="LaborStandards",
            penalty_date=date(2022, 7, 15),
            fine_amount=20000,
        ),
        # 2317: one violation without penalty_date (totals only) + one in 2024
        Violation(
            company_code="2317",
            company_name="鴻海精密工業股份有限公司",
            data_source="LaborStandards",
            penalty_date=None,
            fine_amount=999,
        ),
        Violation(
            company_code="2317",
            company_name="鴻海精密工業股份有限公司",
            data_source="LaborStandards",
            penalty_date=date(2024, 1, 5),
            fine_amount=30000,
        ),
        # Environmental violations: 2330 in 2023 (ROC 112), 6510 two in 2024
        EnvironmentalViolation(
            company_code="2330",
            company_name="台灣積體電路製造股份有限公司",
            penalty_date=date(2023, 6, 1),
            disposition_no="ENV-1",
            law_article="水污染防治法",
            violation_reason="排放超標",
            fine_amount=5000,
            authority="環境部",
        ),
        EnvironmentalViolation(
            company_code="6510",
            company_name="精測科技股份有限公司",
            penalty_date=date(2024, 2, 2),
            disposition_no="ENV-2",
            law_article="空氣污染防制法",
            violation_reason="逸散排放",
            fine_amount=12000,
            authority="環境部",
        ),
        EnvironmentalViolation(
            company_code="6510",
            company_name="精測科技股份有限公司",
            penalty_date=date(2024, 9, 9),
            disposition_no="ENV-3",
            law_article="廢棄物清理法",
            violation_reason="未妥善處理",
            fine_amount=8000,
            authority="環境部",
        ),
        # MOPS tables
        EmployeeBenefit(
            company_code="2330",
            raw_company_code="2330",
            company_name="台積電",
            year=113,
            market_type="sii",
            employee_count=5000,
            eps=1.5,
        ),
        NonManagerSalary(
            company_code="2330",
            raw_company_code="2330",
            company_name="台積電",
            year=113,
            market_type="sii",
            industry="半導體業",
            avg_salary=2000,
            median_salary=1800,
            eps=1.5,
        ),
        NonManagerSalary(
            company_code="2330",
            raw_company_code="2330",
            company_name="台積電",
            year=112,
            market_type="sii",
            industry="半導體業",
            avg_salary=1900,
            median_salary=1700,
            eps=1.2,
        ),
        NonManagerSalary(
            company_code="2317",
            raw_company_code="2317",
            company_name="鴻海",
            year=113,
            market_type="sii",
            industry="其他電子業",
            avg_salary=1200,
            median_salary=1100,
            eps=0.8,
        ),
        WelfarePolicy(
            company_code="2317",
            raw_company_code="2317",
            company_name="鴻海",
            year=113,
            market_type="sii",
            planned_salary_increase="3%",
        ),
        SalaryAdjustment(
            company_code="6510",
            raw_company_code="6510",
            company_name="精測",
            year=112,
            market_type="otc",
            pretax_net_profit=1000,
        ),
    ]
    for row in rows:
        test_session.add(row)
    test_session.commit()


@pytest.fixture
def exported(tmp_path, test_session, seed_full_dataset) -> Path:
    out = tmp_path / "data"
    ExportService(out).export_all(session=test_session)
    return out


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class TestYearlySummaryParity:
    def test_exported_year_files_equal_route_items(self, exported, client):
        response = client.get(
            "/api/v1/companies/yearly-summary",
            params={"include": ["all"], "size": 100, "page": 1},
        )
        assert response.status_code == 200
        route_payload = response.json()
        route_items = route_payload["items"]
        assert route_payload["total"] == len(route_items), "seed must fit one page"
        assert route_items, "seed data must produce items"

        index = load(exported / "yearly-summaries" / "index.json")
        exported_items = []
        for year in index["years"]:
            exported_items.extend(load(exported / "yearly-summaries" / f"{year}.json"))

        assert exported_items == route_items

    def test_index_is_derived_from_exported_items(self, exported):
        yearly_dir = exported / "yearly-summaries"
        index = load(yearly_dir / "index.json")

        file_years = sorted(
            int(p.stem) for p in yearly_dir.glob("*.json") if p.stem.isdigit()
        )
        assert sorted(index["years"]) == file_years
        assert index["years"] == sorted(file_years, reverse=True)

        stats = {s["year"]: s["count"] for s in index["year_stats"]}
        total = 0
        for year in file_years:
            items = load(yearly_dir / f"{year}.json")
            assert stats[year] == len(items)
            total += len(items)
        assert index["total_count"] == total


class TestLeaderboardParity:
    def test_exported_leaderboards_equal_route_response(self, exported, client):
        response = client.get("/api/v1/leaderboards")
        assert response.status_code == 200

        exported_payload = load(exported / "leaderboards.json")
        assert exported_payload == response.json()
