"""
Shared test fixtures for bossy_radar backend tests.

Uses in-memory SQLite to avoid touching production data.
Each test gets a fresh database to prevent data collisions.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models import Company


@pytest.fixture
def test_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def more_companies(test_session):
    """Seed comprehensive company data for filtering/sorting tests."""
    companies = [
        Company(
            code="1101",
            name="台灣水泥",
            abbreviation="台泥",
            market_type="Listed",
            industry="水泥工業",
            capital=10000,
            listing_date=date(1962, 2, 9),
        ),
        Company(
            code="2330",
            name="台灣積體電路",
            abbreviation="台積電",
            market_type="Listed",
            industry="半導體業",
            capital=50000,
            listing_date=date(1994, 9, 5),
        ),
        Company(
            code="2454",
            name="聯發科技",
            abbreviation="聯發科",
            market_type="Listed",
            industry="半導體業",
            capital=20000,
            listing_date=date(2001, 7, 23),
        ),
        Company(
            code="6510",
            name="精測科技",
            abbreviation="精測",
            market_type="OTC",
            industry="半導體業",
            capital=5000,
            listing_date=date(2016, 3, 24),
        ),
        Company(
            code="1234",
            name="測試電腦",
            abbreviation="測試",
            market_type="OTC",
            industry="電腦及週邊設備業",
            capital=1000,
            listing_date=date(2020, 1, 1),
        ),
        Company(
            code="9999",
            name="未上市好公司",
            abbreviation="未上市",
            market_type="Public",
            industry="其他",
            capital=500,
            listing_date=date(2022, 12, 31),
        ),
    ]
    for c in companies:
        test_session.add(c)
    test_session.commit()
    return companies


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
