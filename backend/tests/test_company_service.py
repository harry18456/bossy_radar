"""
Unit tests for CompanyService helper methods.

Tests pure functions that don't require database access.
"""

from datetime import date

import pytest

from app.services.company_service import CompanyService


@pytest.fixture
def service():
    return CompanyService()


# ---------- _parse_roc_date ----------

class TestParseRocDate:
    """Tests for ROC date string → Python date conversion."""

    def test_standard_7digit(self, service):
        """Standard 7-digit ROC date: 1150126 → 2026-01-26"""
        result = service._parse_roc_date("1150126")
        assert result == date(2026, 1, 26)

    def test_6digit(self, service):
        """6-digit ROC date: 990101 → 2010-01-01"""
        result = service._parse_roc_date("990101")
        assert result == date(2010, 1, 1)

    def test_early_date(self, service):
        """Early ROC date: 760221 → 1987-02-21"""
        result = service._parse_roc_date("760221")
        assert result == date(1987, 2, 21)

    def test_empty_string(self, service):
        assert service._parse_roc_date("") is None

    def test_none(self, service):
        assert service._parse_roc_date(None) is None

    def test_whitespace(self, service):
        """Should handle leading/trailing whitespace."""
        result = service._parse_roc_date("  1150126  ")
        assert result == date(2026, 1, 26)

    def test_too_short(self, service):
        """Strings shorter than 6 chars should return None."""
        assert service._parse_roc_date("12345") is None

    def test_invalid_chars(self, service):
        """Non-numeric input should return None."""
        assert service._parse_roc_date("abc") is None

    def test_invalid_month(self, service):
        """Invalid month (13) should return None."""
        assert service._parse_roc_date("1151301") is None

    def test_invalid_day(self, service):
        """Invalid day (32) should return None."""
        assert service._parse_roc_date("1150132") is None


# ---------- _parse_money ----------

class TestParseMoney:
    """Tests for money string → int conversion."""

    def test_with_chinese_prefix(self, service):
        """'新台幣 10000元' → 10000"""
        assert service._parse_money("新台幣 10000元") == 10000

    def test_digits_only(self, service):
        """Pure digit string."""
        assert service._parse_money("50000") == 50000

    def test_with_commas(self, service):
        """Numbers with thousand separators."""
        assert service._parse_money("1,000,000") == 1000000

    def test_large_capital(self, service):
        """Real-world large capital value."""
        assert service._parse_money("259,303,805,000") == 259303805000

    def test_empty_string(self, service):
        assert service._parse_money("") is None

    def test_none(self, service):
        assert service._parse_money(None) is None

    def test_no_digits(self, service):
        """String with no digit characters should return None."""
        assert service._parse_money("新台幣 元") is None
