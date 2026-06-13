"""Fail-loud tests for sync reporting and CLI exit codes.

Covers specs:
- Sync commands SHALL exit non-zero when any source fails
- Sync commands SHALL print a per-source summary
- Skipped parse rows SHALL be logged and counted
"""

import json
import logging
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from app.cli.main import app
from app.services.sync_report import SourceResult, SyncReport
from app.services.violation_service import ViolationService

runner = CliRunner()


def _report(*results: SourceResult) -> SyncReport:
    report = SyncReport()
    for r in results:
        report.add(r)
    return report


class TestSyncReport:
    def test_no_failures_when_all_sources_succeed(self):
        report = SyncReport()
        report.add(SourceResult(name="A", success=True, rows_written=10))
        report.add(SourceResult(name="B", success=True, rows_written=5))

        assert report.has_failures is False

    def test_failures_detected(self):
        report = SyncReport()
        report.add(SourceResult(name="A", success=True, rows_written=10))
        report.add(SourceResult(name="B", success=False, error="HTTP 500"))

        assert report.has_failures is True

    def test_circuit_broken_counts_as_failure(self):
        report = SyncReport()
        report.add(SourceResult(name="A", success=True, rows_written=10))
        report.circuit_broken = True

        assert report.has_failures is True

    def test_summary_has_one_line_per_source(self):
        report = SyncReport()
        report.add(
            SourceResult(name="A", success=True, rows_written=10, rows_skipped=2)
        )
        report.add(SourceResult(name="B", success=False, error="HTTP 500"))

        summary = report.render_summary()
        source_lines = [
            line for line in summary.splitlines() if "A" in line or "B" in line
        ]
        assert len(source_lines) == 2

    def test_summary_marks_failures_with_error(self):
        report = SyncReport()
        report.add(SourceResult(name="GenderEquality", success=False, error="HTTP 500"))

        summary = report.render_summary()
        assert "GenderEquality" in summary
        assert "FAILED" in summary
        assert "HTTP 500" in summary

    def test_summary_shows_written_and_skipped_counts(self):
        report = SyncReport()
        report.add(
            SourceResult(
                name="LaborStandards", success=True, rows_written=120, rows_skipped=3
            )
        )

        summary = report.render_summary()
        assert "LaborStandards" in summary
        assert "120" in summary
        assert "3" in summary
        assert "FAILED" not in summary


class TestCliFailLoud:
    """CLI commands exit non-zero and print a summary when a source fails."""

    def test_sync_violations_exits_nonzero_on_failure(self):
        failing = _report(
            SourceResult(name="LaborStandards", success=False, error="HTTP 500")
        )
        with (
            patch("app.cli.main.CrawlerService") as crawler,
            patch("app.cli.main.ViolationService") as svc,
        ):
            crawler.return_value.download_file.return_value = True
            svc.return_value.sync_violations.return_value = failing
            result = runner.invoke(
                app, ["sync-violations", "--source", "LaborStandards"]
            )

        assert result.exit_code == 1
        assert "FAILED" in result.stdout

    def test_sync_violations_exits_zero_on_success(self):
        ok = _report(SourceResult(name="LaborStandards", success=True, rows_written=5))
        with (
            patch("app.cli.main.CrawlerService") as crawler,
            patch("app.cli.main.ViolationService") as svc,
        ):
            crawler.return_value.download_file.return_value = True
            svc.return_value.sync_violations.return_value = ok
            result = runner.invoke(
                app, ["sync-violations", "--source", "LaborStandards"]
            )

        assert result.exit_code == 0

    def test_sync_violations_download_failure_is_a_failure(self):
        ok = _report(SourceResult(name="LaborStandards", success=True, rows_written=0))
        with (
            patch("app.cli.main.CrawlerService") as crawler,
            patch("app.cli.main.ViolationService") as svc,
        ):
            # Download returns False -> the source must be counted as failed even
            # though the sync step itself reports success.
            crawler.return_value.download_file.return_value = False
            svc.return_value.sync_violations.return_value = ok
            result = runner.invoke(
                app, ["sync-violations", "--source", "LaborStandards"]
            )

        assert result.exit_code == 1

    def test_sync_companies_exits_nonzero_on_failure(self):
        failing = _report(SourceResult(name="Listed", success=False, error="boom"))
        with (
            patch("app.cli.main.CrawlerService") as crawler,
            patch("app.cli.main.CompanyService") as svc,
        ):
            crawler.return_value.download_file.return_value = True
            svc.return_value.sync_companies.return_value = failing
            result = runner.invoke(app, ["sync-companies", "--type", "listed"])

        assert result.exit_code == 1
        assert "FAILED" in result.stdout

    def test_sync_mops_exits_nonzero_on_failure(self):
        failing = _report(
            SourceResult(name="t100sb15", success=False, error="1 unit(s) failed")
        )
        with patch("app.cli.main.MopsScraper") as scraper:
            scraper.return_value.sync_all.return_value = failing
            result = runner.invoke(
                app, ["sync-mops", "--start-year", "113", "--end-year", "113"]
            )

        assert result.exit_code == 1
        assert "FAILED" in result.stdout

    def test_sync_mops_exits_zero_on_success(self):
        ok = _report(SourceResult(name="t100sb15", success=True, rows_written=10))
        with patch("app.cli.main.MopsScraper") as scraper:
            scraper.return_value.sync_all.return_value = ok
            result = runner.invoke(
                app, ["sync-mops", "--start-year", "113", "--end-year", "113"]
            )

        assert result.exit_code == 0


class TestViolationParserSkipLog:
    """violation_service parse loop logs and counts dropped rows (no silent pass)."""

    def test_parse_logs_and_counts_skipped_rows(self, tmp_path, caplog):
        svc = ViolationService()
        path = tmp_path / "LaborStandards.json"
        path.write_text(
            json.dumps(
                [
                    {"事業單位名稱": "好公司甲", "處分字號": "A1", "罰鍰金額": "10000"},
                    "this-row-is-not-a-dict",
                    {"事業單位名稱": "好公司乙", "處分字號": "A2", "罰鍰金額": "20000"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger="app.services.violation_service"):
            records, skipped = svc._parse_json(path, "LaborStandards")

        assert len(records) == 2
        assert skipped == 1
        assert "LaborStandards" in caplog.text

    def test_parse_raises_on_corrupt_file(self, tmp_path):
        """A whole-file parse failure must raise (so the source is failed),
        not silently return an empty success."""
        svc = ViolationService()
        path = tmp_path / "LaborStandards.json"
        path.write_text("{ this is not valid json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            svc._parse_json(path, "LaborStandards")
