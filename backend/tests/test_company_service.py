import csv
from datetime import date

from sqlmodel import Session, select

from app.models.company import Company
from app.services.company_service import CompanyService


def test_get_companies(test_session: Session):
    # Setup
    c1 = Company(code="A", name="A Co", industry="Tech", market_type="Listed")
    c2 = Company(code="B", name="B Co", industry="Finance", market_type="OTC")
    test_session.add(c1)
    test_session.add(c2)
    test_session.commit()

    service = CompanyService()

    # Test basic get
    results, total = service.get_companies(test_session)
    assert total == 2
    assert len(results) == 2

    # Test filter by market_type
    results, total = service.get_companies(
        test_session, filters={"market_type": ["Listed"]}
    )
    assert total == 1
    assert results[0].code == "A"

    # Test filter by name
    results, total = service.get_companies(test_session, filters={"name": "B"})
    assert total == 1
    assert results[0].code == "B"

    # Test sort
    results, total = service.get_companies(test_session, sorts=["-code"])
    assert results[0].code == "B"


def test_get_catalog(test_session: Session):
    c1 = Company(code="C", name="C Co", market_type="Listed", capital=1000)
    test_session.add(c1)
    test_session.commit()

    service = CompanyService()
    catalog = service.get_catalog(test_session)

    assert len(catalog) == 1
    assert catalog[0]["code"] == "C"
    assert catalog[0]["capital"] == 1000.0


def test_parse_money():
    service = CompanyService()
    assert service._parse_money("10000") == 10000
    assert service._parse_money("新台幣 20,000元") == 20000
    assert service._parse_money(None) is None
    assert service._parse_money("invalid") is None


def test_parse_roc_date():
    service = CompanyService()
    assert service._parse_roc_date("1120101") == date(2023, 1, 1)
    assert service._parse_roc_date("990101") == date(2010, 1, 1)
    assert service._parse_roc_date(None) is None
    assert service._parse_roc_date("invalid") is None


def test_sync_companies(test_session: Session, tmp_path):
    # Create dummy csv
    csv_file = tmp_path / "Listed.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["出表日期:1120101"])
        writer.writerow(
            ["公司代號", "公司名稱", "公司簡稱", "產業別", "上市日期", "實收資本額"]
        )
        writer.writerow(["1101", "台泥", "台泥", "水泥工業", "510209", "10000"])

    service = CompanyService()

    # We need to mock the session used inside sync_companies,
    # because sync_companies creates its OWN session using engine directly.
    # To make it use OUR test_session/test_engine, we need to mock Session(engine)
    # OR we can extract the parsing logic to test clearly and only integration test the full sync.

    # Let's test _parse_csv directly first
    companies = service._parse_csv(csv_file, "Listed")
    assert len(companies) == 1
    assert companies[0].code == "1101"
    assert companies[0].market_type == "Listed"

    # Test _upsert_companies
    service._upsert_companies(test_session, companies)
    test_session.commit()

    c = test_session.exec(select(Company).where(Company.code == "1101")).first()
    assert c is not None
    assert c.name == "台泥"

    # Test update
    companies[0].name = "台泥更新"
    service._upsert_companies(test_session, companies)
    test_session.commit()
    test_session.refresh(c)
    assert c.name == "台泥更新"
