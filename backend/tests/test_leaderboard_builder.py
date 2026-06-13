"""Bottom-board semantics tests for the shared leaderboard builder.

Covers spec: Violation bottom leaderboards SHALL reflect the true ascending
order over all companies.
"""

from datetime import date

import pytest

from app.models.company import Company
from app.models.environmental_violation import EnvironmentalViolation
from app.models.violation import Violation
from app.services.leaderboard_builder import build_leaderboard_response


@pytest.fixture
def companies_1_to_25(test_session):
    """25 companies where company Ck has exactly k labor violations.

    Violations are dated in the current ROC year so they land in both the
    all-time board and the latest yearly board.
    """
    today = date.today()
    for k in range(1, 26):
        code = f"{1000 + k}"
        test_session.add(
            Company(
                code=code,
                name=f"C{k}",
                market_type="Listed",
                industry="測試",
            )
        )
        for i in range(k):
            test_session.add(
                Violation(
                    company_code=code,
                    company_name=f"C{k}",
                    data_source="LaborStandards",
                    penalty_date=date(today.year, 1 + (i % 12), 1),
                    fine_amount=1000 * k,
                )
            )
    test_session.commit()


class TestBottomBoardSemantics:
    def test_bottom_by_count_is_true_ascending_slice(
        self, test_session, companies_1_to_25
    ):
        response = build_leaderboard_response(test_session, limit=10)

        board = response.violation_all_time
        assert [i.company_name for i in board.bottom_by_count] == [
            f"C{k}" for k in range(1, 11)
        ], "bottom must be the global ascending slice C1..C10"
        assert [i.total_count for i in board.bottom_by_count] == list(range(1, 11))

        assert [i.company_name for i in board.top_by_count] == [
            f"C{k}" for k in range(25, 15, -1)
        ], "top must be the global descending slice C25..C16"
        assert [i.total_count for i in board.top_by_count] == list(range(25, 15, -1))

    def test_bottom_by_fine_is_true_ascending_slice(
        self, test_session, companies_1_to_25
    ):
        response = build_leaderboard_response(test_session, limit=10)

        board = response.violation_all_time
        # Ck total fine = k violations * 1000k = 1000 * k^2 (strictly increasing)
        assert [i.company_name for i in board.bottom_by_fine] == [
            f"C{k}" for k in range(1, 11)
        ]
        assert [i.total_fine for i in board.bottom_by_fine] == [
            1000 * k * k for k in range(1, 11)
        ]

    def test_yearly_board_uses_same_semantics(self, test_session, companies_1_to_25):
        response = build_leaderboard_response(test_session, limit=10)
        current_roc_year = date.today().year - 1911

        yearly = response.violation_yearly[current_roc_year]
        assert [i.company_name for i in yearly.bottom_by_count] == [
            f"C{k}" for k in range(1, 11)
        ]


class TestCombinedTotals:
    def test_labor_and_env_counts_combine(self, test_session, seed_companies):
        today = date.today()
        for _ in range(2):
            test_session.add(
                Violation(
                    company_code="2330",
                    company_name="台灣積體電路製造股份有限公司",
                    data_source="LaborStandards",
                    penalty_date=date(today.year, 3, 1),
                    fine_amount=100,
                )
            )
        for i in range(3):
            test_session.add(
                EnvironmentalViolation(
                    company_code="2330",
                    company_name="台灣積體電路製造股份有限公司",
                    penalty_date=date(today.year, 4 + i, 1),
                    disposition_no=f"ENV-{i}",
                    law_article="水污染防治法",
                    violation_reason="排放超標",
                    fine_amount=200,
                    authority="環境部",
                )
            )
        test_session.commit()

        response = build_leaderboard_response(test_session, limit=10)
        board = response.violation_all_time
        item = next(i for i in board.top_by_count if i.company_code == "2330")

        assert item.total_count == 5
        assert item.labor_count == 2
        assert item.env_count == 3
        assert item.total_fine == 2 * 100 + 3 * 200
