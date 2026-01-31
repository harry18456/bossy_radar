import logging
import re
import time
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.db.session import engine
from app.models.company import Company

logger = logging.getLogger(__name__)

# MOPS Base URL (mopsov supports direct GET with parameters)
MOPSOV_BASE_URL = "https://mopsov.twse.com.tw/mops/web"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://mopsov.twse.com.tw/mops/web/index",
}

class CompanyDetailScraper:
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data/raw/company_details")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def sync_all_details(self, limit: Optional[int] = None, force: bool = False, company_code: Optional[str] = None, retries: int = 3, delay: float = 2.0):
        """Sync detailed info (Stakeholder/Governance URLs) for all companies."""
        with Session(engine) as session:
            if company_code:
                query = select(Company).where(Company.code == company_code)
            else:
                query = select(Company)
                if not force:
                    # Only sync companies missing these URLs
                    query = query.where(
                        (Company.stakeholder_url == None) | (Company.governance_url == None)
                    )
            
            companies = session.exec(query).all()
            if limit:
                companies = companies[:limit]

            logger.info(f"Starting detail sync for {len(companies)} companies... (Retries: {retries if retries >= 0 else 'infinite'}, Delay: {delay}s)")

            for i, company in enumerate(companies):
                try:
                    self._fetch_and_update_company(session, company, retries=retries, retry_delay=delay)
                    # MOPS has strict rate limiting, stay safe
                    time.sleep(1.5) 
                    
                    if (i + 1) % 10 == 0:
                        session.commit()
                        logger.info(f"Progress: {i + 1}/{len(companies)} companies processed.")
                except Exception as e:
                    logger.error(f"Error processing company {company.code}: {e}")
                    continue

            session.commit()
            logger.info("Company detail sync completed.")

    def _fetch_and_update_company(self, session: Session, company: Company, retries: int = 3, retry_delay: float = 2.0):
        """Fetch t05st03 for a company and update its URLs."""
        # Pattern verified: mopsov supports direct GET
        url = f"{MOPSOV_BASE_URL}/t05st03"
        params = {
            "step": "1",
            "firstin": "1",
            "off": "1",
            "queryName": "co_id",
            "t05st03_ck": "1",
            "co_id": company.code
        }

        # Cache path
        cache_path = self.data_dir / f"{company.code}.html"
        
        # 1. Check Cache (Skip if exists and not empty)
        if cache_path.exists() and cache_path.stat().st_size > 1000:
            logger.debug(f"Using cache for {company.code}")
            html = cache_path.read_text(encoding="utf-8")
        else:
            # 2. Fetch from Network with Retry
            html = self._fetch_with_retry(url, params, retries=retries, delay=retry_delay)
            if html:
                cache_path.write_text(html, encoding="utf-8")
            else:
                logger.warning(f"Failed to fetch data for {company.code}")
                return

        # 3. Parse
        soup = BeautifulSoup(html, "html.parser")
        
        # The page uses a structure with labels in spans/tds
        stakeholder_url = self._extract_url_by_label(soup, "公司網站內利害關係人專區網址")
        governance_url = self._extract_url_by_label(soup, "公司網站內公司治理資訊專區網址")

        if stakeholder_url:
            company.stakeholder_url = stakeholder_url
        if governance_url:
            company.governance_url = governance_url

        session.add(company)

    def _fetch_with_retry(self, url: str, params: dict, retries: int = 3, delay: float = 2.0, max_delay: float = 60.0) -> Optional[str]:
        """Fetch URL with exponential backoff retry. Support infinite if retries < 0."""
        attempt = 0
        while True:
            try:
                with httpx.Client(timeout=30, follow_redirects=True) as client:
                    response = client.get(url, headers=HEADERS, params=params)
                    response.raise_for_status()
                    
                    # Check if MOPS returned a valid page (not an error or maintenance page)
                    if "服務暫時無法提供" in response.text or "請稍後再試" in response.text:
                        raise httpx.HTTPStatusError("MOPS rate limit/maintenance detected", request=response.request, response=response)
                        
                    return response.text
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                attempt += 1
                # Check if we should stop
                if retries >= 0 and attempt > retries:
                    logger.error(f"Failed after {retries} retries: {e}")
                    break
                
                # Calculate exponential backoff
                wait_time = min(delay * (2 ** (attempt - 1)), max_delay)
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {wait_time}s... (Target: {params.get('co_id')})")
                time.sleep(wait_time)
        
        return None

    def _extract_url_by_label(self, soup: BeautifulSoup, label_text: str) -> Optional[str]:
        """Find the link corresponding to a label in the MOPS layout."""
        # Some labels have <br> in them, so we strip them when comparing
        # OR we search for partial matches.
        
        target_cells = soup.find_all(['th', 'td'])
        value = None
        
        for cell in target_cells:
            # Get text and clean it (including internal whitespace/newlines)
            cell_text = "".join(cell.get_text().split())
            if label_text in cell_text:
                # Value is usually in the next sibling td
                next_td = cell.find_next_sibling('td')
                if next_td:
                    link = next_td.find('a')
                    if link and 'href' in link.attrs:
                        value = link['href']
                    else:
                        value = next_td.get_text(strip=True).replace('\xa0', '') # Remove &nbsp;
                    break
        
        if value in ["不適用", "", None]:
            return None
            
        return value.strip()
