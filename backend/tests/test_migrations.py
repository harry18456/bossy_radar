"""Alembic migration tests (BACKEND_AUDIT M8).

Covers specs:
- Schema SHALL be managed by versioned migrations
- Existing databases SHALL migrate in place without data loss
"""

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

BACKEND = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "company",
    "violation",
    "environmentalviolation",
    "non_manager_salary",
    "employee_benefit",
    "welfare_policy",
    "salary_adjustment",
}


def _cfg(db_url: str) -> Config:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _count(db: Path, table: str) -> int:
    con = sqlite3.connect(db)
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        con.close()


class TestMigrations:
    def test_clean_upgrade_creates_tables_and_unique_constraints(self, tmp_path):
        db = tmp_path / "clean.db"
        command.upgrade(_cfg(f"sqlite:///{db}"), "head")

        insp = inspect(create_engine(f"sqlite:///{db}"))
        assert set(insp.get_table_names()) >= EXPECTED_TABLES

        mops_uniques = insp.get_unique_constraints("non_manager_salary")
        assert any(
            set(u["column_names"]) == {"raw_company_code", "year", "market_type"}
            for u in mops_uniques
        )

        violation_cols = {c["name"] for c in insp.get_columns("violation")}
        assert "dedup_key" in violation_cols
        assert any(
            u["column_names"] == ["dedup_key"]
            for u in insp.get_unique_constraints("violation")
        )

    def test_downgrade_reverts_to_baseline(self, tmp_path):
        db = tmp_path / "down.db"
        cfg = _cfg(f"sqlite:///{db}")
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "0001")

        insp = inspect(create_engine(f"sqlite:///{db}"))
        violation_cols = {c["name"] for c in insp.get_columns("violation")}
        assert "dedup_key" not in violation_cols

    def test_stamp_then_upgrade_preserves_rows_and_backfills(self, tmp_path):
        db = tmp_path / "existing.db"
        url = f"sqlite:///{db}"
        cfg = _cfg(url)

        # Build the OLD (baseline) schema, then simulate a real database that
        # carries that schema but is not yet tracked by Alembic.
        command.upgrade(cfg, "0001")
        eng = create_engine(url)
        with eng.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO violation "
                    "(company_name, data_source, fine_amount, disposition_no, "
                    "created_at, last_updated) "
                    "VALUES ('甲公司','LaborStandards',100,'D1',"
                    "'2024-01-01','2024-01-01')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO violation "
                    "(company_name, data_source, fine_amount, disposition_no, "
                    "penalty_date, law_article, created_at, last_updated) "
                    "VALUES ('乙公司','LaborStandards',200,'',"
                    "'2024-02-02','勞基法','2024-01-01','2024-01-01')"
                )
            )
            conn.execute(text("DELETE FROM alembic_version"))

        before = _count(db, "violation")
        command.stamp(cfg, "0001")
        command.upgrade(cfg, "head")
        after = _count(db, "violation")

        assert before == after == 2

        con = sqlite3.connect(db)
        try:
            nulls = con.execute(
                "SELECT COUNT(*) FROM violation WHERE dedup_key IS NULL"
            ).fetchone()[0]
        finally:
            con.close()
        assert nulls == 0
