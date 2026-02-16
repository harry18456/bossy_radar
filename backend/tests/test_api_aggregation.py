from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.company import Company
from app.models.employee_benefit import EmployeeBenefit
from app.models.non_manager_salary import NonManagerSalary
from app.models.violation import Violation


def test_get_company_profile(test_session: Session, client: TestClient):
    # Setup test data
    company = Company(
        code="TEST_001",
        name="測試公司",
        industry="科技業",
        market_type="上市",
        status="營業中",
    )
    test_session.add(company)
    test_session.commit()
    test_session.refresh(company)

    violation = Violation(
        company_code="TEST_001",
        penalty_date=date(2023, 1, 1),
        fine_amount=10000,
        law_article="勞基法",
        violation_content="逾時加班",
        # Required fields in Violation model
        company_name="測試公司",
        data_source="Test",
    )
    test_session.add(violation)
    test_session.commit()

    response = client.get("/api/v1/companies/TEST_001/profile")
    assert response.status_code == 200
    data = response.json()

    assert data["company"]["code"] == "TEST_001"
    assert len(data["violations"]) == 1
    assert data["violations"][0]["fine_amount"] == 10000


def test_get_company_profile_not_found(client: TestClient):
    response = client.get("/api/v1/companies/NONEXISTENT/profile")
    assert response.status_code == 404


def test_get_yearly_summary(test_session: Session, client: TestClient):
    # Setup test data
    company = Company(
        code="TEST_002",
        name="測試公司2",
        industry="服務業",
        market_type="上櫃",
        status="營業中",
    )
    test_session.add(company)

    benefit = EmployeeBenefit(
        company_code="TEST_002",
        year=112,
        employee_count=100,
        avg_benefit_per_employee=50000,
        # Required fields
        raw_company_code="TEST_002",
        company_name="測試公司2",
        market_type="上櫃",
        industry="服務業",
    )
    test_session.add(benefit)

    salary = NonManagerSalary(
        company_code="TEST_002",
        year=112,
        employee_count=80,
        avg_salary=45000,
        median_salary=40000,
        # Required fields
        raw_company_code="TEST_002",
        company_name="測試公司2",
        market_type="上櫃",
        industry="服務業",
    )
    test_session.add(salary)
    test_session.commit()

    # Test basic query
    response = client.get("/api/v1/companies/yearly-summary", params={"year": [112]})
    assert response.status_code == 200
    data = response.json()
    items = [i for i in data["items"] if i["company_code"] == "TEST_002"]
    assert len(items) == 1
    assert items[0]["company_code"] == "TEST_002"

    # Test include query
    response = client.get(
        "/api/v1/companies/yearly-summary",
        params={"year": [112], "include": ["employee_benefit", "non_manager_salary"]},
    )
    assert response.status_code == 200
    data = response.json()
    items = [i for i in data["items"] if i["company_code"] == "TEST_002"]
    assert items[0]["employee_benefit"]["avg_benefit_per_employee"] == 50000
    assert items[0]["non_manager_salary"]["median_salary"] == 40000
