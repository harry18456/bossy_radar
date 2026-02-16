from app.services.company_service import CompanyService


class TestCompanyServiceSorting:
    def test_sort_by_capital_desc(self, test_session, more_companies):
        service = CompanyService()
        results, total = service.get_companies(test_session, sorts=["-capital"])

        # Expected order: 台積電(50000) -> 聯發科(20000) -> 台泥(10000) -> 精測(5000) -> 測試(1000) -> 未上市(500)
        assert results[0].name == "台灣積體電路"
        assert results[1].name == "聯發科技"
        assert results[-1].name == "未上市好公司"

    def test_sort_by_capital_asc(self, test_session, more_companies):
        service = CompanyService()
        results, total = service.get_companies(test_session, sorts=["capital"])

        # Expected order: 未上市(500) -> 測試(1000) -> ...
        assert results[0].name == "未上市好公司"
        assert results[1].name == "測試電腦"

    def test_sort_by_listing_date(self, test_session, more_companies):
        service = CompanyService()
        # 1962, 1994, 2001, 2016, 2020, 2022

        # Newest first
        results, total = service.get_companies(test_session, sorts=["-listing_date"])
        assert results[0].listing_date.year == 2022

        # Oldest first
        results, total = service.get_companies(test_session, sorts=["listing_date"])
        assert results[0].listing_date.year == 1962

    def test_ignore_invalid_sort_field(self, test_session, more_companies):
        service = CompanyService()
        # "invalid_field" should be ignored, fallback to default code asc
        results, total = service.get_companies(test_session, sorts=["invalid_field"])

        # Default sort is by code asc: 1101 -> 1234 -> 2330
        assert results[0].code == "1101"
        assert results[1].code == "1234"
