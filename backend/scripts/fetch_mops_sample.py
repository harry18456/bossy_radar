"""
Fetch sample HTML from MOPS endpoints to analyze table structure.
Run with: uv run python scripts/fetch_mops_sample.py
"""
import httpx
from pathlib import Path
from datetime import datetime

BASE_URL = "https://mopsov.twse.com.tw/mops/web"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://mopsov.twse.com.tw/mops/web/index",
    "Origin": "https://mopsov.twse.com.tw",
    "Content-Type": "application/x-www-form-urlencoded",
}

ENDPOINTS = {
    "t100sb14": {
        "endpoint": "ajax_t100sb14",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "RYEAR": "113",
        }
    },
    "t100sb15": {
        "endpoint": "ajax_t100sb15",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",
        }
    },
    "t100sb13": {
        "endpoint": "ajax_t100sb13",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",
        }
    },
    "t222sb01": {
        "endpoint": "ajax_t222sb01",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",
        }
    },
}


def fetch_and_save():
    today = datetime.now().strftime("%Y%m%d")
    output_dir = Path(f"data/raw/mops/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        for name, config in ENDPOINTS.items():
            url = f"{BASE_URL}/{config['endpoint']}"
            payload = config["payload"]
            
            print(f"Fetching {name} from {url}...")
            try:
                response = client.post(url, data=payload)
                response.raise_for_status()
                
                # Save HTML
                filename = f"{name}_sii_113.html"
                filepath = output_dir / filename
                filepath.write_text(response.text, encoding="utf-8")
                print(f"  Saved to {filepath} ({len(response.text)} bytes)")
                
            except Exception as e:
                print(f"  Error: {e}")


if __name__ == "__main__":
    fetch_and_save()
    print("\nDone! Check data/raw/mops/ for HTML files.")
