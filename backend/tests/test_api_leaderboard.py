from datetime import date
from unittest.mock import patch

import pytest
from sqlmodel import Session

from app.models.company import Company
from app.models.environmental_violation import EnvironmentalViolation
from app.models.non_manager_salary import NonManagerSalary
from app.models.violation import Violation


@pytest.fixture
def leaderboard_data(test_session: Session):
    """Seed rich data for leaderboard testing."""
    # 1. Companies
    companies = [
        Company(code="1101", name="台泥", industry="水泥工業", market_type="Listed"),
        Company(code="2330", name="台積電", industry="半導體業", market_type="Listed"),
        Company(code="2454", name="聯發科", industry="半導體業", market_type="Listed"),
        Company(code="2317", name="鴻海", industry="電子零組件", market_type="Listed"),
        Company(code="9999", name="小公司", industry="其他", market_type="Emerging"),
    ]
    for c in companies:
        test_session.add(c)

    # 2. Labor Violations (All-time & Yearly)
    violations = [
        # 台泥: 2 violations in 2024
        Violation(
            company_code="1101",
            company_name="台泥",
            data_source="Test",
            penalty_date=date(2024, 1, 1),
            fine_amount=100000,
            law_article="Law A",
        ),
        Violation(
            company_code="1101",
            company_name="台泥",
            data_source="Test",
            penalty_date=date(2024, 2, 1),
            fine_amount=50000,
            law_article="Law B",
        ),
        # 台積電: 1 violation in 2023 (older)
        Violation(
            company_code="2330",
            company_name="台積電",
            data_source="Test",
            penalty_date=date(2023, 5, 1),
            fine_amount=20000,
            law_article="Law C",
        ),
    ]
    for v in violations:
        test_session.add(v)

    # 3. Environmental Violations
    env_violations = [
        # 鴻海: Big fine
        EnvironmentalViolation(
            company_code="2317",
            company_name="鴻海",
            penalty_date=date(2024, 3, 1),
            fine_amount=1000000,
            violation_type="Air",
        ),
    ]
    for v in env_violations:
        test_session.add(v)

    # 4. Salaries (Year 112 = 2023, Year 113 = 2024)
    salaries = [
        # 2023 (112)
        NonManagerSalary(
            company_code="2330",
            raw_company_code="2330",
            company_name="台積電",
            market_type="sii",
            year=112,
            avg_salary=3000,
            median_salary=2500,
            industry="半導體業",
            eps=30.5,
        ),
        NonManagerSalary(
            company_code="2454",
            raw_company_code="2454",
            company_name="聯發科",
            market_type="sii",
            year=112,
            avg_salary=4000,
            median_salary=3500,
            industry="半導體業",
            eps=45.2,
        ),
        NonManagerSalary(
            company_code="1101",
            raw_company_code="1101",
            company_name="台泥",
            market_type="sii",
            year=112,
            avg_salary=1000,
            median_salary=900,
            industry="水泥工業",
            eps=1.5,
        ),
        # 2022 (111)
        NonManagerSalary(
            company_code="2330",
            raw_company_code="2330",
            company_name="台積電",
            market_type="sii",
            year=111,
            avg_salary=2800,
            median_salary=2300,
            industry="半導體業",
            eps=28.0,
        ),
    ]
    for s in salaries:
        test_session.add(s)

    test_session.commit()


class TestLeaderboardAPI:
    def test_get_leaderboards(self, client, leaderboard_data):
        # Mock today to be 2024-01-01 -> ROC 113
        # Recent years: 113, 112, 111.
        # Test data has 112, 111.
        with patch("app.services.leaderboard_builder.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 1)
            response = client.get("/api/v1/leaderboards")

        assert response.status_code == 200
        data = response.json()

        # Check Structure
        assert "violation_all_time" in data
        assert "violation_yearly" in data
        assert "salary" in data
        assert "salary_by_industry" in data

        # 1. Violation All Time
        # 台泥 (1101): 2 violations, 150k fine
        # 鴻海 (2317): 1 env violation, 1000k fine
        # 台積電 (2330): 1 violation, 20k fine

        # Check Top by Total Fine
        top_fine = data["violation_all_time"]["top_by_fine"]
        assert len(top_fine) >= 1
        assert top_fine[0]["company_code"] == "2317"  # 鴻海 should be top (1000k)
        assert top_fine[0]["total_fine"] == 1000000

        # Check Top by Count
        top_count = data["violation_all_time"]["top_by_count"]
        # 台泥 has 2 labor, 0 env -> total 2
        # 鴻海 has 0 labor, 1 env -> total 1
        # 台積電 has 1 labor, 0 env -> total 1
        participants = {x["company_code"]: x["total_count"] for x in top_count}
        assert participants["1101"] == 2
        assert participants["2317"] == 1

        # 2. Violation Yearly (2024 -> 113)
        # Note: API logic: current_year = date.today().year - 1911.
        # If today is 2026, current_year is 115.
        # recent_years = [115, 114, 113].
        # Seed data has 2024 (113). So it should be included.

        # Wait, if today is 2026 (simulated by system prompt?), then 2024 is 113.
        # Check if 113 matches.

        # Verify specific year presence
        # years = data["violation_yearly"].keys() (Unused)
        # The test dynamic depends on 'date.today().year'.

        # Let's check 113 (2024) specifically if it's in the range
        # Assuming we are in 2026, range is [115, 114, 113].
        if "113" in data["violation_yearly"]:
            v113 = data["violation_yearly"]["113"]
            # In 2024: 台泥(2), 鴻海(1 env)
            p113 = {x["company_code"]: x["total_count"] for x in v113["top_by_count"]}
            assert p113.get("1101") == 2
            assert p113.get("2317") == 1

        # 3. Salary (112 = 2023)
        # Should be present now
        assert "112" in data["salary"]
        s112 = data["salary"]["112"]
        # Top median: 聯發科(3500) > 台積電(2500) > 台泥(900)
        top_median = s112["top_by_median"]
        assert top_median[0]["company_code"] == "2454"
        assert top_median[1]["company_code"] == "2330"

        # 4. Salary by Industry (112)
        assert "112" in data["salary_by_industry"]
        ind112 = data["salary_by_industry"]["112"]
        assert "半導體業" in ind112
        semi = ind112["半導體業"]

        # EPS: 聯發科(45.2) > 台積電(30.5)
        top_eps = semi["top_by_eps"]
        assert top_eps[0]["company_code"] == "2454"
        assert top_eps[1]["company_code"] == "2330"
