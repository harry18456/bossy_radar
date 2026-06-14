"""Deterministic dedup keys and DB-enforced idempotent upserts.

Covers specs:
- Empty disposition numbers SHALL use a deterministic dedup key
- Natural keys SHALL be unique at the database layer
"""

from datetime import date

from sqlmodel import select

from app.models.non_manager_salary import NonManagerSalary
from app.models.violation import Violation
from app.services.company_matcher import CompanyMatcher
from app.services.dedup import env_violation_dedup_key, violation_dedup_key
from app.services.mops_scraper import MopsScraper
from app.services.violation_service import ViolationService


class TestDedupKey:
    def test_violation_non_empty_disposition_uses_natural_key(self):
        key = violation_dedup_key(
            data_source="LaborStandards",
            disposition_no="北市勞動字第123號",
            company_name="台積電",
            penalty_date=date(2024, 3, 1),
            law_article="勞基法第32條",
            fine_amount=50000,
        )
        assert key == "LaborStandards|北市勞動字第123號"
        assert not key.startswith("syn:")

    def test_violation_empty_disposition_is_synthetic_and_deterministic(self):
        args = {
            "data_source": "LaborStandards",
            "disposition_no": "",
            "company_name": "台積電",
            "penalty_date": date(2024, 3, 1),
            "law_article": "勞基法第32條",
            "fine_amount": 50000,
        }
        k1 = violation_dedup_key(**args)
        k2 = violation_dedup_key(**args)
        assert k1 == k2
        assert k1.startswith("syn:")

    def test_violation_empty_disposition_differs_on_different_fields(self):
        base = {
            "data_source": "LaborStandards",
            "disposition_no": "",
            "company_name": "台積電",
            "penalty_date": date(2024, 3, 1),
            "law_article": "勞基法第32條",
            "fine_amount": 50000,
        }
        k1 = violation_dedup_key(**base)
        k2 = violation_dedup_key(**{**base, "fine_amount": 99999})
        assert k1 != k2

    def test_violation_none_disposition_treated_as_empty(self):
        with_none = violation_dedup_key(
            data_source="LaborStandards",
            disposition_no=None,
            company_name="台積電",
            penalty_date=date(2024, 3, 1),
            law_article="勞基法第32條",
            fine_amount=50000,
        )
        assert with_none.startswith("syn:")

    def test_env_non_empty_disposition_uses_disposition(self):
        key = env_violation_dedup_key(
            disposition_no="環署字第456號",
            company_name="某工廠",
            penalty_date=date(2024, 2, 2),
            violation_reason="排放超標",
            fine_amount=12000,
        )
        assert key == "環署字第456號"
        assert not key.startswith("syn:")

    def test_env_empty_disposition_is_synthetic(self):
        key = env_violation_dedup_key(
            disposition_no=None,
            company_name="某工廠",
            penalty_date=date(2024, 2, 2),
            violation_reason="排放超標",
            fine_amount=12000,
        )
        assert key.startswith("syn:")


class TestDbIdempotentUpsert:
    def test_mops_natural_key_dedupes_and_updates(self, test_session):
        scraper = MopsScraper()
        base = {
            "raw_company_code": "9999",
            "company_name": "測試",
            "year": 113,
            "market_type": "sii",
            "avg_salary": 100,
        }
        matcher = CompanyMatcher(test_session)
        scraper._upsert_data(
            session=test_session,
            archive_session=test_session,
            records=[dict(base)],
            model_class=NonManagerSalary,
            matcher=matcher,
        )
        test_session.commit()
        scraper._upsert_data(
            session=test_session,
            archive_session=test_session,
            records=[{**base, "avg_salary": 200}],
            model_class=NonManagerSalary,
            matcher=matcher,
        )
        test_session.commit()

        rows = test_session.exec(select(NonManagerSalary)).all()
        assert len(rows) == 1
        assert rows[0].avg_salary == 200

    def test_empty_disposition_violation_dedupes(self, test_session):
        svc = ViolationService()
        matcher = CompanyMatcher(test_session)

        def make():
            return Violation(
                company_name="某公司",
                data_source="LaborStandards",
                penalty_date=date(2024, 1, 1),
                law_article="勞基法",
                fine_amount=100,
                disposition_no="",
            )

        svc._upsert_violations(test_session, test_session, [make()], matcher)
        test_session.commit()
        svc._upsert_violations(test_session, test_session, [make()], matcher)
        test_session.commit()

        rows = test_session.exec(select(Violation)).all()
        assert len(rows) == 1

    def test_non_empty_disposition_violation_dedupes(self, test_session):
        svc = ViolationService()
        matcher = CompanyMatcher(test_session)

        def make():
            return Violation(
                company_name="某公司",
                data_source="LaborStandards",
                disposition_no="北勞字第1號",
                fine_amount=100,
            )

        svc._upsert_violations(test_session, test_session, [make()], matcher)
        test_session.commit()
        svc._upsert_violations(test_session, test_session, [make()], matcher)
        test_session.commit()

        rows = test_session.exec(select(Violation)).all()
        assert len(rows) == 1
