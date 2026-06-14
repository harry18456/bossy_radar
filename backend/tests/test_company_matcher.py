"""
Unit tests for CompanyMatcher.

Uses in-memory SQLite with seeded company data to verify matching logic.
"""

import pytest

from app.services.company_matcher import CompanyMatcher


class TestCompanyMatcher:
    """Tests for multi-strategy company matching."""

    @pytest.fixture
    def matcher(self, test_session, seed_companies):
        """Create a matcher pre-loaded with seed companies."""
        return CompanyMatcher(test_session)

    # --- Tax ID matching ---

    def test_match_by_tax_id(self, matcher):
        """Exact tax ID match should return company code."""
        assert matcher.match_by_tax_id("22099131") == "2330"

    def test_match_by_tax_id_with_whitespace(self, matcher):
        """Should handle whitespace in tax ID."""
        assert matcher.match_by_tax_id("  22099131  ") == "2330"

    def test_match_by_tax_id_not_found(self, matcher):
        """Unknown tax ID should return None."""
        assert matcher.match_by_tax_id("99999999") is None

    def test_match_by_tax_id_none(self, matcher):
        assert matcher.match_by_tax_id(None) is None

    def test_match_by_tax_id_empty(self, matcher):
        assert matcher.match_by_tax_id("") is None

    # --- Name matching ---

    def test_match_by_name_full(self, matcher):
        """Full company name exact match."""
        assert matcher.match_by_name("台灣積體電路製造股份有限公司") == "2330"

    def test_match_by_name_abbreviation(self, matcher):
        """Abbreviation should also match."""
        assert matcher.match_by_name("台積電") == "2330"

    def test_match_by_name_not_found(self, matcher):
        assert matcher.match_by_name("不存在的公司") is None

    def test_match_by_name_none(self, matcher):
        assert matcher.match_by_name(None) is None

    # --- Branch matching ---

    def test_match_by_branch(self, matcher):
        """Branch name starting with parent company name should match."""
        assert matcher.match_by_branch("台灣積體電路製造股份有限公司新竹廠") == "2330"

    def test_match_by_branch_exact_name_no_match(self, matcher):
        """Exact company name (without branch suffix) should NOT match branch logic."""
        assert matcher.match_by_branch("台灣積體電路製造股份有限公司") is None

    def test_match_by_branch_not_found(self, matcher):
        assert matcher.match_by_branch("完全不相關的名稱") is None

    # --- Composite match (priority tests) ---

    def test_match_tax_id_has_highest_priority(self, matcher):
        """When both tax_id and name are provided, tax_id should win."""
        # Provide TSMC tax ID but Foxconn name
        result = matcher.match(
            tax_id="22099131",
            company_name="鴻海精密工業股份有限公司",
        )
        assert result == "2330"  # tax_id wins

    def test_match_by_name_fallback(self, matcher):
        """When tax_id is None, should fall back to name matching."""
        result = matcher.match(tax_id=None, company_name="鴻海")
        assert result == "2317"

    def test_match_by_branch_fallback(self, matcher):
        """When exact name fails, should try branch matching."""
        result = matcher.match(
            tax_id=None,
            company_name="鴻海精密工業股份有限公司土城廠",
        )
        assert result == "2317"

    def test_match_no_match(self, matcher):
        """When nothing matches, should return None."""
        result = matcher.match(tax_id="00000000", company_name="完全不存在")
        assert result is None
