"""Regression: environmental ingestion attribution under the shared matcher
(change 5b).

EnvironmentalService keeps delegating to CompanyMatcher; these tests confirm
the new rules do not degrade env behavior:
- a record still links by tax_id (env's strongest signal), and
- a bare personal name (equal to a chairman) is NO LONGER auto-linked — it
  goes to archive, since the chairman fallback was removed.
"""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Company
from app.models.environmental_violation import EnvironmentalViolation
from app.services.company_matcher import CompanyMatcher
from app.services.environmental_service import EnvironmentalService


@pytest.fixture
def main_and_archive():
    """Two independent in-memory DBs so we can assert which one a row lands in."""
    main_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    arch_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(main_engine)
    SQLModel.metadata.create_all(arch_engine)
    with Session(main_engine) as main, Session(arch_engine) as arch:
        main.add(
            Company(
                code="5874",
                name="南山人壽保險股份有限公司",
                market_type="Listed",
                tax_id="11456006",
                chairman="尹崇堯",
            )
        )
        main.commit()
        yield main, arch
    main_engine.dispose()
    arch_engine.dispose()


def test_env_links_by_tax_id(main_and_archive):
    main, arch = main_and_archive
    matcher = CompanyMatcher(main)
    v = EnvironmentalViolation(
        company_name="某不在清單的工廠",
        tax_id="11456006",
        disposition_no="環字第1號",
        fine_amount=1000,
    )
    EnvironmentalService()._upsert_violations(main, arch, [v], matcher)
    main.commit()
    arch.commit()

    main_rows = main.exec(select(EnvironmentalViolation)).all()
    assert len(main_rows) == 1
    assert main_rows[0].company_code == "5874"  # linked by tax_id
    assert arch.exec(select(EnvironmentalViolation)).all() == []


def test_env_bare_personal_name_goes_to_archive(main_and_archive):
    main, arch = main_and_archive
    matcher = CompanyMatcher(main)
    # Bare chairman name with no tax_id: must NOT auto-link (regression vs the
    # removed chairman fallback). Goes to archive, unlinked.
    v = EnvironmentalViolation(
        company_name="尹崇堯",
        tax_id=None,
        disposition_no="環字第2號",
        fine_amount=1000,
    )
    EnvironmentalService()._upsert_violations(main, arch, [v], matcher)
    main.commit()
    arch.commit()

    assert main.exec(select(EnvironmentalViolation)).all() == []
    arch_rows = arch.exec(select(EnvironmentalViolation)).all()
    assert len(arch_rows) == 1
    assert arch_rows[0].company_code is None
