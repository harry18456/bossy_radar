import csv
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from sqlmodel import Session, select, col, asc, desc, func

from app.models.company import Company
from app.db.session import engine
import logging

logger = logging.getLogger(__name__)

class CompanyService:
    def __init__(self):
        pass

    def get_companies(
        self,
        session: Session,
        page: int = 1,
        size: int = 20,
        filters: Optional[dict] = None,
        sorts: Optional[List[str]] = None
    ):
        """
        Get companies with pagination, filtering, and sorting.
        """
        query = select(Company)
        
        # Apply Filters
        if filters:
            if filters.get("market_type"):
                # Multi-value filter (IN)
                query = query.where(col(Company.market_type).in_(filters["market_type"]))
            
            if filters.get("industry"):
                # Multi-value filter (IN)
                query = query.where(col(Company.industry).in_(filters["industry"]))
                
            if filters.get("code"):
                # Multi-value filter (IN)
                query = query.where(col(Company.code).in_(filters["code"]))
            
            if filters.get("name"):
                # Partial match
                query = query.where(col(Company.name).ilike(f"%{filters['name']}%"))

        # Calculate Total (before pagination)
        # Efficient count query
        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()

        # Apply Sorts
        if sorts:
            for sort_field in sorts:
                direction = desc
                if not sort_field.startswith("-"):
                    direction = asc
                
                field_name = sort_field.lstrip("-")
                if hasattr(Company, field_name):
                    query = query.order_by(direction(getattr(Company, field_name)))
        else:
            # Default sort
            query = query.order_by(Company.code)
            
        # Apply Pagination
        query = query.offset((page - 1) * size).limit(size)
        
        results = session.exec(query).all()
        
        return results, total

    def get_catalog(self, session: Session) -> List[Company]:
        """
        Get all companies with minimal fields for search catalog.
        """
        # Select only required columns for efficiency
        query = select(
            Company.code,
            Company.name,
            Company.abbreviation,
            Company.market_type,
            Company.industry,
            Company.capital,
            Company.establishment_date,
            Company.listing_date
        ).order_by(Company.code)
        
        # When selecting specific columns, SQLModel returns rows (tuples)
        results = session.exec(query).all()
        
        # Map to dictionaries for Pydantic compatibility
        catalog = []
        for row in results:
            catalog.append({
                "code": row.code,
                "name": row.name,
                "abbreviation": row.abbreviation,
                "market_type": row.market_type,
                "industry": row.industry,
                "capital": float(row.capital) if row.capital is not None else None,
                "establishment_date": row.establishment_date.isoformat() if row.establishment_date else None,
                "listing_date": row.listing_date.isoformat() if row.listing_date else None
            })
        return catalog

    def sync_companies(self, data_dir: Path, target_types: List[str]):
        """
        Sync companies from downloaded CSVs to DB.
        """
        # Ensure tables exist
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
        
        with Session(engine) as session:
            for market_type in target_types:
                file_path = data_dir / f"{market_type}.csv"
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                logger.info(f"Processing {market_type} companies from {file_path}")
                companies = self._parse_csv(file_path, market_type)
                self._upsert_companies(session, companies)
            
            session.commit()

    def _parse_csv(self, file_path: Path, market_type: str) -> List[Company]:
        companies = []
        with open(file_path, "r", encoding="utf-8") as f:
            # Skip potential BOM or weird first characters if simple
            # But csv.DictReader usually handles it if we strip
            lines = f.readlines()
            
        if not lines:
            return []

        # The first line is often "出表日期:...", second line is headers
        # We need to find the header line. Based on analysis, headers start with "出表日期" or "公司代號"
        # The sample showed:
        # Header: ﻿出表日期,公司代號,...
        
        # We can try to parse from the first line that looks like a header
        header_index = 0
        for i, line in enumerate(lines):
            if "公司代號" in line:
                header_index = i
                break
        
        # Parse CSV from header_index
        # We treat lines[header_index] as header
        reader = csv.DictReader(lines[header_index:])
        
        for row in reader:
            try:
                code = row.get("公司代號", "").strip()
                if not code:
                    continue
                
                # Validate company code format (must be alphanumeric, no dots or URL-like strings)
                if not re.match(r'^[A-Za-z0-9]+$', code):
                    logger.warning(f"Skipping invalid company code: {code}")
                    continue
                
                # Sanitize string fields (strip whitespace and hidden characters)
                def clean_str(val: str) -> str:
                    return val.strip() if val else ""
                
                # Validate website field - must look like a URL or be empty
                website = clean_str(row.get("網址", ""))
                address = clean_str(row.get("住址", ""))
                
                # Check for data corruption: if address looks like a URL, log and skip
                if address and re.match(r'^(https?://|www\.)', address, re.IGNORECASE):
                    logger.warning(f"Possible data corruption for {code}: address contains URL-like content, skipping: {address}")
                    continue
                
                # Basic Mapping
                company = Company(
                    code=code,
                    name=clean_str(row.get("公司名稱", "")),
                    abbreviation=clean_str(row.get("公司簡稱", "")),
                    market_type=market_type,  # Always use the parameter, never from CSV
                    industry=clean_str(row.get("產業別", "")),
                    tax_id=clean_str(row.get("營利事業統一編號", "")),
                    chairman=clean_str(row.get("董事長", "")),
                    manager=clean_str(row.get("總經理", "")),
                    establishment_date=self._parse_roc_date(row.get("成立日期", "")),
                    listing_date=self._parse_roc_date(row.get("上市日期") or row.get("上櫃日期", "")),
                    capital=self._parse_money(row.get("實收資本額", "")),
                    address=address,
                    website=website,
                    email=clean_str(row.get("電子郵件信箱", ""))
                )
                companies.append(company)
            except Exception as e:
                logger.error(f"Error parsing row {row.get('公司代號')}: {e}")
                
        return companies

    def _upsert_companies(self, session: Session, companies: List[Company]):
        count = 0
        for new_data in companies:
            # Check if exists
            statement = select(Company).where(Company.code == new_data.code)
            existing = session.exec(statement).first()
            
            if existing:
                # Update fields
                existing.name = new_data.name
                existing.abbreviation = new_data.abbreviation
                existing.market_type = new_data.market_type # Identify sync source preference
                existing.industry = new_data.industry
                existing.tax_id = new_data.tax_id
                existing.chairman = new_data.chairman
                existing.manager = new_data.manager
                existing.establishment_date = new_data.establishment_date
                existing.listing_date = new_data.listing_date
                existing.capital = new_data.capital
                existing.address = new_data.address
                existing.website = new_data.website
                existing.email = new_data.email
                existing.last_updated = datetime.now()
                session.add(existing)
            else:
                session.add(new_data)
            count += 1
        logger.info(f"Upserted {count} companies")

    def _parse_roc_date(self, date_str: str) -> Optional[date]:
        """
        Convert ROC date string (e.g. '1150126') to date object.
        """
        if not date_str:
            return None
        
        try:
            # Clean string
            date_str = date_str.strip()
            if len(date_str) < 6: # e.g. 990101
                return None
                
            year_len = len(date_str) - 4
            year_val = int(date_str[:year_len])
            month = int(date_str[year_len:year_len+2])
            day = int(date_str[year_len+2:])
            
            # If year is already in AD format (e.g. 1950), don't add 1911
            actual_year = year_val + 1911 if year_val < 1000 else year_val
            return date(actual_year, month, day)
        except ValueError:
            return None

    def _parse_money(self, money_str: str) -> Optional[int]:
        """
        Parse money string like '新台幣 10000元' or '10000'
        """
        if not money_str:
            return None
        try:
            # Remove non-digits
            digits = re.sub(r"[^\d]", "", money_str)
            if digits:
                return int(digits)
            return None
        except:
            return None
