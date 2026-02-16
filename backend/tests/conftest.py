"""
Shared test fixtures for bossy_radar backend tests.

Uses in-memory SQLite to avoid touching production data.
Each test gets a fresh database to prevent data collisions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models import Company  # noqa: F401 - triggers all model registrations


@pytest.fixture
def test_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """Provide a session bound to the test engine."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client(test_engine):
    """FastAPI TestClient with DB dependency overridden to use test engine."""

    def _override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_companies(test_session):
    """Insert sample companies for testing."""
    companies = [
        Company(
            code="2330",
            name="台灣積體電路製造股份有限公司",
            abbreviation="台積電",
            market_type="Listed",
            industry="半導體業",
            tax_id="22099131",
            chairman="魏哲家",
            capital=259303805000,
            address="新竹科學園區力行六路8號",
        ),
        Company(
            code="2317",
            name="鴻海精密工業股份有限公司",
            abbreviation="鴻海",
            market_type="Listed",
            industry="其他電子業",
            tax_id="04541302",
            chairman="劉揚偉",
            capital=138642750000,
        ),
        Company(
            code="6510",
            name="精測科技股份有限公司",
            abbreviation="精測",
            market_type="OTC",
            industry="半導體業",
            tax_id="54387236",
            chairman="林聖翔",
            capital=419880000,
        ),
    ]

    for c in companies:
        test_session.add(c)
    test_session.commit()

    for c in companies:
        test_session.refresh(c)

    return companies
