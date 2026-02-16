"""
API integration tests using FastAPI TestClient.

Tests actual HTTP endpoints against an in-memory SQLite database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models import Company  # noqa: F401 - import triggers all model registrations


@pytest.fixture
def seeded_client():
    """
    TestClient with its own in-memory DB pre-seeded with test companies.
    This avoids fixture dependency issues between client and seed_companies.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    # Seed data
    with Session(engine) as session:
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
            session.add(c)
        session.commit()

    def _override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


class TestRootEndpoint:
    def test_read_root(self, client):
        """GET / should return 200."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello": "World"}


class TestCompaniesAPI:
    """Tests for /api/v1/companies endpoints."""

    def test_list_companies(self, seeded_client):
        """GET /api/v1/companies should return paginated response."""
        response = seeded_client.get("/api/v1/companies")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "total_pages" in data
        assert data["total"] == 3

    def test_pagination_params(self, seeded_client):
        """Page and size query params should work."""
        response = seeded_client.get("/api/v1/companies?page=1&size=2")
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) == 2

    def test_filter_by_market_type(self, seeded_client):
        """Filter by market_type should narrow results."""
        response = seeded_client.get("/api/v1/companies?market_type=OTC")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        for item in data["items"]:
            assert item["market_type"] == "OTC"

    def test_filter_by_name(self, seeded_client):
        """Name filter should do partial match."""
        response = seeded_client.get("/api/v1/companies?name=積體電路")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert "積體電路" in data["items"][0]["name"]

    def test_catalog_endpoint(self, seeded_client):
        """GET /api/v1/companies/catalog should return list."""
        response = seeded_client.get("/api/v1/companies/catalog")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify catalog item structure
        item = data[0]
        assert "code" in item
        assert "name" in item
        assert "market_type" in item
