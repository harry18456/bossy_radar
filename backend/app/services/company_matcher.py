"""
Company Matcher - 共用的公司比對邏輯

提供統一的公司歸屬比對，供 ViolationService、EnvironmentalService 與
MopsScraper 共用（單一實作，避免各自內聯複製帶同樣 bug）。

比對優先序（高 → 低）：
1. 公司代號精確比對（MOPS 原始代號，最可靠）
2. 統一編號精確比對
3. 公司名稱精確比對（含簡稱）
4. 確定性最長前綴分公司比對（多候選並列時拒絕）

保守原則：任何層級無把握即回傳 None（歸 archive），絕不猜測。純人名／
負責人姓名不再自動連結到上市公司（無公司全名背書即無佐證）。
"""

from sqlmodel import Session, select

from app.models.company import Company


class CompanyMatcher:
    """公司比對器"""

    def __init__(self, session: Session):
        """
        初始化比對器，預載公司資料建立索引。

        Args:
            session: 資料庫 Session
        """
        companies = session.exec(select(Company)).all()

        # Code set (公司代號精確比對用，MOPS raw_company_code)
        self.code_set: set[str] = set()

        # Tax ID -> Code (統編精確比對用)
        self.tax_id_map: dict[str, str] = {}

        # Name -> Code (名稱/簡稱精確比對用)
        self.name_map: dict[str, str] = {}

        # (Name, Code) list (分公司最長前綴比對用)
        self.branch_list: list[tuple[str, str]] = []

        for c in companies:
            self.code_set.add(c.code)

            if c.tax_id:
                self.tax_id_map[c.tax_id] = c.code

            self.name_map[c.name] = c.code
            if c.abbreviation:
                self.name_map[c.abbreviation] = c.code

            self.branch_list.append((c.name, c.code))

    def match_by_code(self, company_code: str | None) -> str | None:
        """
        使用公司代號進行精確比對（MOPS 原始代號）。

        Args:
            company_code: 上市櫃公司代號

        Returns:
            公司代號，若無匹配則返回 None
        """
        if not company_code:
            return None
        code = company_code.strip()
        return code if code in self.code_set else None

    def match_by_tax_id(self, tax_id: str | None) -> str | None:
        """
        使用統一編號進行精確比對。

        Args:
            tax_id: 統一編號

        Returns:
            公司代號，若無匹配則返回 None
        """
        if not tax_id:
            return None
        return self.tax_id_map.get(tax_id.strip())

    def match_by_name(self, company_name: str | None) -> str | None:
        """
        使用公司名稱進行精確比對（含簡稱）。

        Args:
            company_name: 公司名稱

        Returns:
            公司代號，若無匹配則返回 None
        """
        if not company_name:
            return None
        return self.name_map.get(company_name.strip())

    def match_by_branch(self, company_name: str | None) -> str | None:
        """
        分公司／廠區最長前綴比對。

        當某公司全名為輸入的前綴時，將該筆歸屬到該公司；前綴之後的尾綴
        （括號負責人、廠區、主檔省略的法人後綴等）不改變歸屬。多個不同
        公司代號並列最長前綴時拒絕（回 None），使結果與資料庫列順序無關、
        跨 run 確定，並避免歧義猜測。

        例如：「某某科技股份有限公司新竹廠」-> 「某某科技股份有限公司」

        Args:
            company_name: 完整公司／分公司名稱

        Returns:
            總公司代號，若無匹配或有歧義則返回 None
        """
        if not company_name:
            return None

        name = company_name.strip()
        candidates = [
            (c_name, c_code)
            for c_name, c_code in self.branch_list
            if c_name and name.startswith(c_name) and len(name) > len(c_name)
        ]
        if not candidates:
            return None

        max_len = max(len(c_name) for c_name, _ in candidates)
        top_codes = {c_code for c_name, c_code in candidates if len(c_name) == max_len}
        if len(top_codes) > 1:
            # 多家公司並列最長前綴 -> 歧義，不猜
            return None
        return next(c_code for c_name, c_code in candidates if len(c_name) == max_len)

    def match(
        self,
        tax_id: str | None = None,
        company_name: str | None = None,
        company_code: str | None = None,
    ) -> str | None:
        """
        綜合比對：按優先順序嘗試比對策略。

        優先順序：
        1. 公司代號精確比對（最高優先，MOPS raw code）
        2. 統一編號精確比對
        3. 名稱精確比對（含簡稱）
        4. 分公司最長前綴比對（多候選拒絕）

        無任何層級命中即回 None（歸 archive）。已移除舊有的董事長姓名
        fallback：純人名無公司全名背書，自動連結會把個人違規誤掛上市公司。

        Args:
            tax_id: 統一編號
            company_name: 公司名稱
            company_code: 公司代號（MOPS 原始代號）

        Returns:
            公司代號，若無匹配則返回 None
        """
        # Level 1: Company code (MOPS golden path)
        if company_code:
            matched = self.match_by_code(company_code)
            if matched:
                return matched

        # Level 2: Tax ID
        if tax_id:
            matched = self.match_by_tax_id(tax_id)
            if matched:
                return matched

        if not company_name:
            return None

        # Level 3: Name exact match
        matched = self.match_by_name(company_name)
        if matched:
            return matched

        # Level 4: Deterministic longest-prefix branch match
        return self.match_by_branch(company_name)
