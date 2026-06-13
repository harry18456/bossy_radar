"""Bounded-retry and circuit-breaker tests for CompanyDetailScraper.

Covers specs:
- Retry loops SHALL have an absolute attempt ceiling
- Consecutive maintenance pages SHALL trip a circuit breaker
"""

import httpx
import pytest

from app.models.company import Company
from app.services.company_detail_scraper import CompanyDetailScraper


class FakeResponse:
    def __init__(self, text: str):
        self.text = text
        self.request = httpx.Request("GET", "https://example.test")

    def raise_for_status(self):
        return None


def make_fake_client(behavior):
    """Build a fake httpx.Client class whose get() delegates to behavior()."""

    class FakeClient:
        calls = 0

        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, *args, **kwargs):
            FakeClient.calls += 1
            return behavior()

    return FakeClient


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr(
        "app.services.company_detail_scraper.time.sleep", lambda s: None
    )


class TestAttemptCeiling:
    @pytest.mark.parametrize(
        ("retries", "expected_attempts"),
        [
            (3, 4),
            (0, 1),
            (-1, 50),
        ],
    )
    def test_permanent_failure_attempt_counts(
        self, tmp_path, monkeypatch, no_sleep, retries, expected_attempts
    ):
        def always_fail():
            raise httpx.RequestError("connection refused")

        fake_client = make_fake_client(always_fail)
        monkeypatch.setattr(
            "app.services.company_detail_scraper.httpx.Client", fake_client
        )

        scraper = CompanyDetailScraper(data_dir=tmp_path)
        result = scraper._fetch_with_retry(
            "https://example.test", {"co_id": "9001"}, retries=retries, delay=0.01
        )

        assert result is None
        assert fake_client.calls == expected_attempts


class TestMaintenanceCircuitBreaker:
    def test_consecutive_maintenance_pages_trip_breaker(
        self, tmp_path, monkeypatch, no_sleep, test_session
    ):
        for k in range(1, 9):
            test_session.add(
                Company(code=f"90{k:02d}", name=f"測試公司{k}", market_type="Listed")
            )
        test_session.commit()

        def maintenance_page():
            return FakeResponse("<html>服務暫時無法提供，請稍後再試</html>")

        fake_client = make_fake_client(maintenance_page)
        monkeypatch.setattr(
            "app.services.company_detail_scraper.httpx.Client", fake_client
        )

        scraper = CompanyDetailScraper(data_dir=tmp_path)
        report = scraper.sync_all_details(retries=0, delay=0.01, session=test_session)

        assert report.circuit_broken is True
        assert report.has_failures is True
        # 5 consecutive maintenance companies x 1 attempt each, then no
        # further requests are issued.
        assert fake_client.calls == 5
        assert "circuit" in report.render_summary().lower()

    def test_successful_fetch_resets_breaker_counter(
        self, tmp_path, monkeypatch, no_sleep, test_session
    ):
        for k in range(1, 9):
            test_session.add(
                Company(code=f"91{k:02d}", name=f"重置測試{k}", market_type="Listed")
            )
        test_session.commit()

        valid_html = (
            "<html><table><tr><td>公司網站內利害關係人專區網址</td></tr></table>"
            + ("x" * 1200)
        )
        state = {"n": 0}

        def alternating():
            state["n"] += 1
            # 4 maintenance pages, then one success, repeatedly: the breaker
            # threshold of 5 consecutive failures is never reached.
            if state["n"] % 5 == 0:
                return FakeResponse(valid_html)
            return FakeResponse("<html>服務暫時無法提供</html>")

        fake_client = make_fake_client(alternating)
        monkeypatch.setattr(
            "app.services.company_detail_scraper.httpx.Client", fake_client
        )

        scraper = CompanyDetailScraper(data_dir=tmp_path)
        report = scraper.sync_all_details(retries=0, delay=0.01, session=test_session)

        assert report.circuit_broken is False
        # All 8 companies were attempted (no early abort).
        assert fake_client.calls == 8
