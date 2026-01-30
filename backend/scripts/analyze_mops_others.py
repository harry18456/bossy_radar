import httpx
from bs4 import BeautifulSoup
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MOPS_BASE_URL = "https://mopsov.twse.com.tw/mops/web"
DATA_DIR = Path("data/raw/mops_analysis_others")
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENDPOINTS = {
    "t100sb14": "ajax_t100sb14",
    "t100sb13": "ajax_t100sb13",
    "t222sb01": "ajax_t222sb01"
}

# Config based on MopsScraper
CONFIGS = {
    "t100sb14": {"year_param": "RYEAR", "step": "1", "firstin": "1", "extra": {}}, 
    "t100sb13": {"year_param": "year", "step": "0", "firstin": "ture", "extra": {"off": "1"}}, # Note: 'ture' typo in original code
    "t222sb01": {"year_param": "RYEAR", "step": "1", "firstin": "1", "extra": {"CODE": ""}}
}

def fetch_and_analyze(source, year, market):
    cache_path = DATA_DIR / f"{source}_{market}_{year}.html"
    endpoint = ENDPOINTS[source]
    config = CONFIGS[source]
    
    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
    else:
        logger.info(f"Fetching {source} {year} {market}...")
        payload = {
            "encodeURIComponent": "1",
            "step": config["step"],
            "firstin": config["firstin"],
            "TYPEK": market,
            config["year_param"]: str(year)
        }
        payload.update(config["extra"])
        
        try:
            resp = httpx.post(
                f"{MOPS_BASE_URL}/{endpoint}", 
                data=payload,
                timeout=30
            )
            html = resp.text
            cache_path.write_text(html, encoding="utf-8")
            time.sleep(1) 
        except Exception as e:
            logger.error(f"Failed to fetch {source} {year} {market}: {e}")
            return

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    col_counts = {}
    
    for row in rows:
        cells = row.find_all("td")
        if not cells: continue
        
        # heuristic: checking if 1st or 2nd cell is a company code/name
        # structure varies, but usually data rows start with some text or number
        try:
            # Basic validation: row must have substantial content
            if len(cells) > 3: 
                count = len(cells)
                if count not in col_counts:
                    col_counts[count] = 0
                col_counts[count] += 1
        except:
            pass
            
    if not col_counts:
        logger.warning(f"{source} Year {year} {market}: No likely data rows found")
    else:
        # Filter out rare column counts (likely headers or footers)
        major_counts = {k: v for k, v in col_counts.items() if v > 5}
        if major_counts:
            logger.info(f"{source} Year {year} {market}: Major column counts: {major_counts}")
        else:
            logger.info(f"{source} Year {year} {market}: Raw counts: {col_counts}")

def main():
    years = range(105, 114) # Check wider range
    markets = ["sii", "otc"]
    sources = ["t100sb14", "t100sb13", "t222sb01"]
    
    for source in sources:
        print(f"--- analyzing {source} ---")
        for year in years:
            for market in markets:
                fetch_and_analyze(source, year, market)

if __name__ == "__main__":
    main()
