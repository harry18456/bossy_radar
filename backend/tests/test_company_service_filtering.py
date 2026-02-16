from app.services.company_service import CompanyService


class TestCompanyServiceFiltering:
    def test_filter_by_market_type(self, test_session, more_companies):
        service = CompanyService()

        # Test Listed
        results, total = service.get_companies(
            test_session, filters={"market_type": ["Listed"]}
        )
        assert total == 3
        assert all(c.market_type == "Listed" for c in results)

        # Test OTC
        results, total = service.get_companies(
            test_session, filters={"market_type": ["OTC"]}
        )
        assert total == 2
        assert all(c.market_type == "OTC" for c in results)

        # Test Multiple (Listed + OTC)
        results, total = service.get_companies(
            test_session, filters={"market_type": ["Listed", "OTC"]}
        )
        assert total == 5

    def test_filter_by_industry(self, test_session, more_companies):
        service = CompanyService()

        # Test Semiconductor
        results, total = service.get_companies(
            test_session, filters={"industry": ["半導體業"]}
        )
        assert total == 3
        codes = {c.code for c in results}
        assert codes == {"2330", "2454", "6510"}

        # Test Cement
        results, total = service.get_companies(
            test_session, filters={"industry": ["水泥工業"]}
        )
        assert total == 1
        assert results[0].code == "1101"

    def test_filter_by_name_partial(self, test_session, more_companies):
        service = CompanyService()

        # Test "科技" -> 聯發科技, 精測科技
        results, total = service.get_companies(test_session, filters={"name": "科技"})
        assert total == 2
        assert "2454" in {c.code for c in results}
        assert "6510" in {c.code for c in results}

        # Test "台灣" -> 台灣水泥, 台灣積體電路
        results, total = service.get_companies(test_session, filters={"name": "台灣"})
        assert total == 2

    def test_filter_by_code(self, test_session, more_companies):
        service = CompanyService()

        # Single code
        results, total = service.get_companies(test_session, filters={"code": ["2330"]})
        assert total == 1
        assert results[0].name == "台灣積體電路"

        # Multiple codes
        results, total = service.get_companies(
            test_session, filters={"code": ["1101", "9999"]}
        )
        assert total == 2

    def test_composite_filters(self, test_session, more_companies):
        service = CompanyService()

        # Listed + Semiconductor -> 台積電, 聯發科 (不含精測-OTC)
        filters = {"market_type": ["Listed"], "industry": ["半導體業"]}
        results, total = service.get_companies(test_session, filters=filters)
        assert total == 2
        assert "6510" not in {c.code for c in results}

        # OTC + Computer -> 測試電腦
        filters = {"market_type": ["OTC"], "industry": ["電腦及週邊設備業"]}
        results, total = service.get_companies(test_session, filters=filters)
        assert total == 1
        assert results[0].code == "1234"
