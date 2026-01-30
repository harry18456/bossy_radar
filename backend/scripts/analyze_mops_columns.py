import httpx
from bs4 import BeautifulSoup
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOPS_BASE_URL = "https://mopsov.twse.com.tw/mops/web/ajax_t100sb15"
DATA_DIR = Path("data/raw/mops_analysis")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def fetch_and_analyze(year, market):
    cache_path = DATA_DIR / f"t100sb15_{market}_{year}.html"
    
    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
    else:
        logger.info(f"Fetching {year} {market}...")
        try:
            resp = httpx.post(
                MOPS_BASE_URL, 
                data={
                    'encodeURIComponent': '1', 
                    'step': '1', 
                    'firstin': '1', 
                    'TYPEK': market, 
                    'RYEAR': str(year)
                },
                timeout=30
            )
            html = resp.text
            cache_path.write_text(html, encoding="utf-8")
            time.sleep(1) # Be nice to the server
        except Exception as e:
            logger.error(f"Failed to fetch {year} {market}: {e}")
            return

    soup = BeautifulSoup(html, "html.parser")
    # Find data rows (usually have digits in 2nd column for company code)
    rows = soup.find_all("tr")
    col_counts = {}
    
    for row in rows:
        cells = row.find_all("td")
        if not cells: continue
        
        # heuristic: checking if 2nd cell is a company code
        try:
            if len(cells) > 1 and cells[1].get_text(strip=True).isdigit():
                count = len(cells)
                if count not in col_counts:
                    col_counts[count] = 0
                col_counts[count] += 1
        except:
            pass
            
    if not col_counts:
        logger.warning(f"Year {year} {market}: No invalid data rows found")
    else:
        logger.info(f"Year {year} {market}: Column counts found: {col_counts}")

def main():
    years = range(107, 115) # 107 to 114 to be safe
    markets = ["sii", "otc"]
    
    for year in years:
        for market in markets:
            fetch_and_analyze(year, market)

if __name__ == "__main__":
    main()
