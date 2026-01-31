"""
Environmental Service - 環境部裁罰資料 ETL

處理 EMS_P_46 資料的下載、解析、比對與儲存。
"""

import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

import requests
from sqlmodel import Session, select, SQLModel

from app.core.config import settings
from app.db.session import engine, archive_engine
from app.models.environmental_violation import EnvironmentalViolation
from app.services.company_matcher import CompanyMatcher

logger = logging.getLogger(__name__)

# API 設定
MOENV_API_URL = "https://data.moenv.gov.tw/api/v2/EMS_P_46"


class EnvironmentalService:
    """環境部裁罰資料 ETL 服務"""
    
    def __init__(self):
        self.api_key = settings.MOENV_API_KEY
    
    def download_data(self, save_path: Path) -> bool:
        """
        從環境部 Open Data 下載 EMS_P_46 資料。
        
        Args:
            save_path: 儲存路徑
            
        Returns:
            是否成功
        """
        if not self.api_key:
            logger.error("MOENV_API_KEY is not set")
            return False
        
        try:
            # 使用分頁下載所有資料
            all_records = []
            offset = 0
            limit = 1000
            
            while True:
                params = {
                    "format": "json",
                    "api_key": self.api_key,
                    "offset": offset,
                    "limit": limit
                }
                
                logger.info(f"Fetching records offset={offset}, limit={limit}")
                response = requests.get(MOENV_API_URL, params=params, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                
                # API 可能回傳 list 或 dict with "records" key
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    records = data.get("records", [])
                else:
                    logger.warning(f"Unexpected response type: {type(data)}")
                    break
                
                if not records:
                    break
                
                all_records.extend(records)
                logger.info(f"Fetched {len(records)} records, total: {len(all_records)}")
                
                # 如果回傳的資料少於 limit，表示已經沒有更多資料
                if len(records) < limit:
                    break
                
                offset += limit
            
            logger.info(f"Downloaded {len(all_records)} records total")
            
            # 儲存到檔案
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download environmental data: {e}")
            return False
    
    def sync_data(self, data_dir: Path):
        """
        同步環境違規資料到資料庫。
        
        Args:
            data_dir: 資料目錄 (包含 EMS_P_46.json)
        """
        file_path = data_dir / "EMS_P_46.json"
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return
        
        # 確保資料表存在
        SQLModel.metadata.create_all(engine)
        SQLModel.metadata.create_all(archive_engine)
        
        with Session(engine) as session, Session(archive_engine) as archive_session:
            # 初始化比對器
            matcher = CompanyMatcher(session)
            
            # 解析資料
            logger.info(f"Processing environmental violations from {file_path}")
            violations = self._parse_json(file_path)
            logger.info(f"Parsed {len(violations)} records. Starting linking and upsert...")
            
            # 比對與儲存
            self._upsert_violations(session, archive_session, violations, matcher)
            
            session.commit()
            archive_session.commit()
    
    def _parse_json(self, file_path: Path) -> List[EnvironmentalViolation]:
        """解析 JSON 檔案"""
        records = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.warning("Data is not a list")
                return []
            
            for row in data:
                try:
                    # 使用 API 回傳的英文欄位名稱
                    violation = EnvironmentalViolation(
                        # 識別資料
                        tax_id=self._clean_str(row.get("ban")),  # 統一編號
                        control_no=self._clean_str(row.get("ems_no")),  # 管制事業編號
                        disposition_no=self._clean_str(row.get("document_no")),  # 裁處書字號
                        
                        # 事業資料
                        company_name=self._clean_str(row.get("fac_name")) or "",  # 事業名稱
                        company_address=self._clean_str(row.get("fac_address")),  # 公司（工廠）地址
                        violation_address=self._clean_str(row.get("transgress_address")),  # 違反地址
                        
                        # 違規資訊
                        violation_type=self._clean_str(row.get("transgress_type")),  # 污染類別
                        violation_date=self._parse_date(row.get("transgress_date")),  # 違反時間
                        violation_reason=self._clean_str(row.get("openinfor")),  # 違反事實
                        law_article=self._clean_str(row.get("transgress_law")),  # 違反法令
                        
                        # 裁處資訊
                        authority=self._clean_str(row.get("county_name")),  # 裁處機關
                        penalty_date=self._parse_date(row.get("penalty_date")),  # 裁處時間
                        fine_amount=self._parse_amount(row.get("penalty_money")),  # 裁處金額
                        penalty_reason=self._clean_str(row.get("gist_define")),  # 裁處理由及法令
                        
                        # 後續處理
                        limit_date=self._parse_date(row.get("improve_deadline")),  # 限改日期
                        is_improved=self._parse_bool(row.get("is_improve")),  # 改善完妥與否
                        is_appeal=self._parse_bool(row.get("ispetition")),  # 是否訴願訴訟
                        appeal_result=self._clean_str(row.get("petition_results")),  # 訴願訴訟結果
                        is_paid=self._parse_bool(row.get("paymentstate")),  # 罰鍰是否繳清
                        
                        # 其他
                        illegal_profit=self._parse_amount(row.get("illegal_money")),  # 不法利得
                        other_penalty=self._clean_str(row.get("penaltykind")),  # 其他處罰方式
                        is_serious=self._parse_bool(row.get("isimportant")),  # 情節重大
                    )
                    
                    if violation.company_name:
                        records.append(violation)
                        
                except Exception as e:
                    logger.debug(f"Error parsing record: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error reading file: {e}")
        
        return records
    
    def _upsert_violations(
        self,
        session: Session,
        archive_session: Session,
        violations: List[EnvironmentalViolation],
        matcher: CompanyMatcher
    ):
        """比對並儲存違規資料"""
        count = 0
        linked_count = 0
        
        for v in violations:
            # 使用 CompanyMatcher 進行比對
            matched_code = matcher.match(tax_id=v.tax_id, company_name=v.company_name)
            
            if matched_code:
                v.company_code = matched_code
                linked_count += 1
                target_session = session
            else:
                target_session = archive_session
            
            # Upsert 邏輯
            if not v.disposition_no:
                target_session.add(v)
                count += 1
                continue
            
            existing = target_session.exec(
                select(EnvironmentalViolation).where(
                    EnvironmentalViolation.disposition_no == v.disposition_no
                )
            ).first()
            
            if existing:
                # 更新現有記錄
                for field in [
                    "company_code", "company_name", "tax_id", "control_no",
                    "company_address", "violation_address", "violation_type",
                    "violation_date", "violation_reason", "law_article",
                    "authority", "penalty_date", "fine_amount", "penalty_reason",
                    "limit_date", "is_improved", "is_appeal", "appeal_result",
                    "is_paid", "illegal_profit", "other_penalty", "is_serious"
                ]:
                    setattr(existing, field, getattr(v, field))
                existing.last_updated = datetime.now()
                target_session.add(existing)
            else:
                target_session.add(v)
            
            count += 1
            
            if count % 1000 == 0:
                session.commit()
                archive_session.commit()
                logger.info(f"Processed {count} records...")
        
        session.commit()
        archive_session.commit()
        logger.info(f"Processed {count} violations. Linked {linked_count} to companies.")
    
    # ========== Helper Methods ==========
    
    def _clean_str(self, value) -> Optional[str]:
        """清理字串"""
        if value is None:
            return None
        s = str(value).strip()
        if not s or s.lower() in ("null", "none", "n/a", "-"):
            return None
        return s
    
    def _parse_date(self, value) -> Optional[date]:
        """解析日期 (支援多種格式)"""
        if not value:
            return None
        
        try:
            s = str(value).strip()
            if not s or s.lower() in ("null", "none"):
                return None
            
            # 嘗試 YYYY-MM-DD 格式
            if "-" in s:
                parts = s.split("-")
                if len(parts) == 3:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
            
            # 嘗試 YYYYMMDD 格式
            if len(s) == 8 and s.isdigit():
                return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
            
            # 嘗試民國年格式 (YYYMMDD)
            if len(s) == 7 and s.isdigit():
                year = int(s[:3]) + 1911
                return date(year, int(s[3:5]), int(s[5:7]))
                
        except Exception:
            pass
        
        return None
    
    def _parse_amount(self, value) -> int:
        """解析金額"""
        if not value:
            return 0
        try:
            digits = re.sub(r"[^\d]", "", str(value))
            return int(digits) if digits else 0
        except Exception:
            return 0
    
    def _parse_bool(self, value) -> Optional[bool]:
        """解析布林值"""
        if not value:
            return None
        s = str(value).strip().lower()
        if s in ("是", "y", "yes", "true", "1"):
            return True
        if s in ("否", "n", "no", "false", "0"):
            return False
        return None
