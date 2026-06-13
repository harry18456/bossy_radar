"""Atomicity tests for ExportService.

Covers specs:
- Static export SHALL be all-or-nothing
- Single JSON file writes SHALL be atomic
- Export deletions SHALL be restricted to service-owned paths
"""

import json
from pathlib import Path

import pytest

from app.services.export_service import ExportService


def snapshot_dir(d: Path) -> dict[str, bytes]:
    """Map of relative path -> bytes for every file under d."""
    return {
        str(p.relative_to(d)): p.read_bytes()
        for p in sorted(d.rglob("*"))
        if p.is_file()
    }


def seed_old_output(out: Path) -> dict[str, bytes]:
    """Create a pre-existing output directory with stale content."""
    (out / "companies").mkdir(parents=True)
    (out / "company-catalog.json").write_text('[{"code": "OLD"}]', encoding="utf-8")
    (out / "companies" / "0001.json").write_text('{"old": true}', encoding="utf-8")
    (out / "stale.json").write_text("{}", encoding="utf-8")
    return snapshot_dir(out)


def service_siblings(out: Path) -> list[str]:
    """Names of leftover service-owned siblings (.tmp/.bak) next to out."""
    return [
        p.name
        for p in out.parent.iterdir()
        if p.name.startswith(out.name + ".") and p.name != out.name
    ]


class TestAllOrNothing:
    def test_failure_preserves_existing_output(
        self, tmp_path, test_session, seed_companies, monkeypatch
    ):
        out = tmp_path / "data"
        before = seed_old_output(out)

        svc = ExportService(out)

        def boom(session):
            raise RuntimeError("injected failure")

        monkeypatch.setattr(svc, "export_leaderboards", boom)

        with pytest.raises(RuntimeError, match="injected failure"):
            svc.export_all(session=test_session)

        assert snapshot_dir(out) == before, "output dir must be byte-identical"
        assert service_siblings(out) == [], "temp dir must be cleaned up"

    def test_success_replaces_output_completely(
        self, tmp_path, test_session, seed_companies
    ):
        out = tmp_path / "data"
        seed_old_output(out)

        svc = ExportService(out)
        svc.export_all(session=test_session)

        files = snapshot_dir(out)
        assert "company-catalog.json" in files
        assert "stale.json" not in files, "stale files must not survive the swap"
        catalog = json.loads(files["company-catalog.json"])
        assert {c["code"] for c in catalog} == {"2330", "2317", "6510"}
        assert service_siblings(out) == [], "no .tmp/.bak residue after success"

    def test_leftover_tmp_and_bak_are_cleaned(
        self, tmp_path, test_session, seed_companies
    ):
        out = tmp_path / "data"
        seed_old_output(out)
        leftover_tmp = out.parent / (out.name + ".tmp")
        leftover_bak = out.parent / (out.name + ".bak")
        leftover_tmp.mkdir()
        (leftover_tmp / "junk.json").write_text("{}", encoding="utf-8")
        leftover_bak.mkdir()
        (leftover_bak / "junk.json").write_text("{}", encoding="utf-8")

        svc = ExportService(out)
        svc.export_all(session=test_session)

        assert not leftover_tmp.exists()
        assert not leftover_bak.exists()
        assert (out / "company-catalog.json").exists()

    def test_first_export_without_existing_output(
        self, tmp_path, test_session, seed_companies
    ):
        out = tmp_path / "data"

        svc = ExportService(out)
        svc.export_all(session=test_session)

        assert (out / "company-catalog.json").exists()
        assert service_siblings(out) == []


class TestAtomicJsonWrite:
    def test_target_is_valid_json_and_no_tmp_residue(self, tmp_path):
        out = tmp_path / "data"
        svc = ExportService(out)
        target = tmp_path / "single.json"

        svc._save_json(target, {"hello": "世界"})

        assert json.loads(target.read_text(encoding="utf-8")) == {"hello": "世界"}
        residue = [p for p in tmp_path.iterdir() if p.name.startswith("single.json.")]
        assert residue == [], "no temp file may remain next to the target"

    def test_failed_serialization_leaves_old_content_intact(self, tmp_path):
        out = tmp_path / "data"
        svc = ExportService(out)
        target = tmp_path / "single.json"
        target.write_text('{"old": "content"}', encoding="utf-8")

        with pytest.raises(TypeError):
            svc._save_json(target, {"bad": object()})

        assert json.loads(target.read_text(encoding="utf-8")) == {"old": "content"}
        residue = [p for p in tmp_path.iterdir() if p.name.startswith("single.json.")]
        assert residue == [], "failed write must clean its temp file"


class TestRestrictedDeletions:
    def test_foreign_path_is_rejected(self, tmp_path):
        out = tmp_path / "data"
        svc = ExportService(out)

        foreign = tmp_path / "precious"
        foreign.mkdir()
        (foreign / "keep.txt").write_text("keep", encoding="utf-8")

        with pytest.raises(ValueError):
            svc._remove_service_dir(foreign)

        assert foreign.exists()
        assert (foreign / "keep.txt").read_text(encoding="utf-8") == "keep"

    def test_live_output_dir_is_rejected(self, tmp_path):
        out = tmp_path / "data"
        out.mkdir()
        svc = ExportService(out)

        with pytest.raises(ValueError):
            svc._remove_service_dir(out)

        assert out.exists()
