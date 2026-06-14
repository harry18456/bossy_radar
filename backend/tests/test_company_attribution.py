"""Company attribution matching tests (change 5b).

Validates the deterministic, conservative attribution rules:
- company-code / tax-id / full-name exact layers
- longest-prefix branch matching (trailing brackets / sites / missing suffix
  resolve to the same company)
- reject when multiple companies tie for the longest prefix
- no auto-link from bare personal names (chairman layer removed)
- no fuzzy/normalized recall

See openspec/changes/backend-violation-attribution-correctness.
"""

import pytest

from app.models import Company
from app.services.company_matcher import CompanyMatcher

# code, name, abbreviation, tax_id, chairman
ATTR_COMPANIES = [
    ("2330", "台灣積體電路製造股份有限公司", "台積電", "22099131", "魏哲家"),
    ("5874", "南山人壽保險股份有限公司", "南山人壽", "11456006", "尹崇堯"),
    ("9963", "台灣電力股份有限公司", None, "03795904", "曾文生"),
    ("5857", "臺灣土地銀行", None, "03700301", "何英明"),  # master omits 後綴
    ("4171", "瑞基海洋生物科技股份有限公司", "瑞基", "27489806", "劉正忠"),
    ("2354", "鴻準精密工業股份有限公司", "鴻準", "23707801", "陳國寶"),
    ("2382", "廣達電腦股份有限公司", "廣達", "23708071", "林百里"),
]


@pytest.fixture
def matcher(test_session):
    for code, name, abbr, tax_id, chairman in ATTR_COMPANIES:
        test_session.add(
            Company(
                code=code,
                name=name,
                abbreviation=abbr,
                market_type="Listed",
                tax_id=tax_id,
                chairman=chairman,
            )
        )
    test_session.commit()
    return CompanyMatcher(test_session)


# label, match() kwargs, expected code (None = archive)
CASES = [
    ("code-layer-mops", {"company_code": "2330"}, "2330"),
    ("tax-id-layer", {"tax_id": "22099131"}, "2330"),
    ("name-exact", {"company_name": "台灣積體電路製造股份有限公司"}, "2330"),
    ("name-abbreviation", {"company_name": "台積電"}, "2330"),
    (
        "bracket-representative",
        {"company_name": "南山人壽保險股份有限公司(尹崇堯)"},
        "5874",
    ),
    ("site-suffix", {"company_name": "台灣電力股份有限公司南區營業處"}, "9963"),
    (
        "suffix-missing-master",
        {"company_name": "臺灣土地銀行股份有限公司(何英明)"},
        "5857",
    ),
    ("bare-name-chairman-liu", {"company_name": "劉正忠"}, None),
    ("bare-name-chairman-chen", {"company_name": "陳國寶"}, None),
    ("fuzzy-recall-guarded", {"company_name": "廣達有限公司(曾坤升)"}, None),
    ("plain-no-match", {"company_name": "完全不存在的某某企業社"}, None),
]


@pytest.mark.parametrize("label,kwargs,expected", CASES, ids=[c[0] for c in CASES])
def test_attribution_cases(matcher, label, kwargs, expected):
    assert matcher.match(**kwargs) == expected


def test_reject_when_multiple_companies_tie(test_session):
    """Two distinct codes share the same full name -> ambiguous -> archive."""
    for code in ("8001", "8002"):
        test_session.add(Company(code=code, name="同名測試", market_type="Listed"))
    test_session.commit()
    m = CompanyMatcher(test_session)
    assert m.match(company_name="同名測試新竹廠") is None


def test_longest_prefix_is_order_independent(test_session):
    """Longest prefix wins and the result does not depend on load order."""
    test_session.add(Company(code="7001", name="長前綴測試公司", market_type="Listed"))
    test_session.add(Company(code="7002", name="長前綴測試", market_type="Listed"))
    test_session.commit()
    m = CompanyMatcher(test_session)
    r1 = m.match(company_name="長前綴測試公司新竹廠")
    # reversing the internal candidate order must not change attribution
    m.branch_list = list(reversed(m.branch_list))
    r2 = m.match(company_name="長前綴測試公司新竹廠")
    assert r1 == r2 == "7001"
