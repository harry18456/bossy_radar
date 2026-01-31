"""
Company Matcher - 共用的公司比對邏輯

提供 Tax ID 精確比對與名稱模糊比對功能，供 ViolationService 與 EnvironmentalService 共用。
"""

from typing import Dict, List, Optional, Tuple
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
        
        # Tax ID -> Code (精確比對用)
        self.tax_id_map: Dict[str, str] = {}
        
        # Name -> Code (名稱精確比對用)
        self.name_map: Dict[str, str] = {}
        
        # (Name, Code) list (分公司比對用)
        self.branch_list: List[Tuple[str, str]] = []
        
        # Chairman -> [(Name, Code)] (負責人比對用)
        self.chairman_map: Dict[str, List[Tuple[str, str]]] = {}
        
        for c in companies:
            # Tax ID Index
            if c.tax_id:
                self.tax_id_map[c.tax_id] = c.code
            
            # Name Exact Match
            self.name_map[c.name] = c.code
            if c.abbreviation:
                self.name_map[c.abbreviation] = c.code
            
            # Branch Match Prep
            self.branch_list.append((c.name, c.code))
            
            # Chairman Match Prep
            if c.chairman:
                if c.chairman not in self.chairman_map:
                    self.chairman_map[c.chairman] = []
                self.chairman_map[c.chairman].append((c.name, c.code))
    
    def match_by_tax_id(self, tax_id: Optional[str]) -> Optional[str]:
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
    
    def match_by_name(self, company_name: str) -> Optional[str]:
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
    
    def match_by_branch(self, company_name: str) -> Optional[str]:
        """
        使用分公司/廠區名稱進行前綴比對。
        例如：「某某科技股份有限公司新竹廠」-> 匹配「某某科技股份有限公司」
        
        Args:
            company_name: 完整公司/分公司名稱
            
        Returns:
            總公司代號，若無匹配則返回 None
        """
        if not company_name:
            return None
        
        name = company_name.strip()
        for c_name, c_code in self.branch_list:
            if name.startswith(c_name) and len(name) > len(c_name):
                return c_code
        return None
    
    def match_by_chairman(self, name: str) -> Optional[str]:
        """
        使用負責人姓名進行比對（僅當唯一時匹配）。
        
        Args:
            name: 姓名
            
        Returns:
            公司代號，若無匹配或有多個候選則返回 None
        """
        if not name:
            return None
        
        candidates = self.chairman_map.get(name.strip())
        if candidates and len(candidates) == 1:
            return candidates[0][1]
        return None
    
    def match(self, tax_id: Optional[str] = None, company_name: Optional[str] = None) -> Optional[str]:
        """
        綜合比對：按優先順序嘗試所有比對策略。
        
        優先順序：
        1. Tax ID 精確比對 (最高優先)
        2. 名稱精確比對
        3. 分公司前綴比對
        4. 負責人比對 (最低優先)
        
        Args:
            tax_id: 統一編號
            company_name: 公司名稱
            
        Returns:
            公司代號，若無匹配則返回 None
        """
        # Level 1: Tax ID (Golden Path)
        if tax_id:
            matched = self.match_by_tax_id(tax_id)
            if matched:
                return matched
        
        if not company_name:
            return None
        
        # Level 2: Name Exact Match
        matched = self.match_by_name(company_name)
        if matched:
            return matched
        
        # Level 3: Branch Match
        matched = self.match_by_branch(company_name)
        if matched:
            return matched
        
        # Level 4: Chairman Match (fallback)
        matched = self.match_by_chairman(company_name)
        if matched:
            return matched
        
        return None
