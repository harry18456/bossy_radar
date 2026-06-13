"""Connection-level PRAGMA enforcement (BACKEND_AUDIT M6/M7).

Covers spec: SQLite connections SHALL enforce runtime PRAGMAs.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from app.db.session import _configure_sqlite, archive_engine, engine
from app.models.company import Company
from app.models.violation import Violation


def _temp_engine(tmp_path):
    eng = create_engine(
        f"sqlite:///{tmp_path / 'pragma.db'}",
        connect_args={"check_same_thread": False},
    )
    event.listens_for(eng, "connect")(_configure_sqlite)
    return eng


class TestPragmas:
    def test_pragmas_applied_on_connect(self, tmp_path):
        eng = _temp_engine(tmp_path)
        with eng.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
            assert conn.exec_driver_sql("PRAGMA busy_timeout").scalar() == 5000
            assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1

    def test_real_engines_have_listener(self):
        assert event.contains(engine, "connect", _configure_sqlite)
        assert event.contains(archive_engine, "connect", _configure_sqlite)

    def test_foreign_keys_enforced(self, tmp_path):
        eng = _temp_engine(tmp_path)
        SQLModel.metadata.create_all(eng)
        with Session(eng) as s:
            s.add(
                Violation(
                    company_code="NONEXISTENT",
                    company_name="幽靈公司",
                    data_source="LaborStandards",
                )
            )
            with pytest.raises(IntegrityError):
                s.commit()

    def test_null_foreign_key_allowed(self, tmp_path):
        eng = _temp_engine(tmp_path)
        SQLModel.metadata.create_all(eng)
        with Session(eng) as s:
            s.add(
                Violation(
                    company_code=None,
                    company_name="未比對公司",
                    data_source="LaborStandards",
                )
            )
            s.commit()
        with Session(eng) as s:
            assert s.get(Company, "NONEXISTENT") is None
