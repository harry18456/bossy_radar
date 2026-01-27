"""
Final test with correct MOPS parameters.
Run with: uv run python scripts/test_mops_final.py
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

# Confirmed working parameters from browser analysis
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
            "RYEAR": "113",  # Uses RYEAR not year!
        }
    },
    "t100sb13": {
        "endpoint": "ajax_t100sb13",
        "payload": {
            "encodeURIComponent": "1",
            "step": "0",  # Must be 0
            "firstin": "ture",  # Typo in original system!
            "off": "1",
            "TYPEK": "sii",
            "year": "113",  # Uses lowercase 'year' not RYEAR!
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
            "RYEAR": "113",
            "CODE": "",  # Uppercase CODE
        }
    },
}


def fetch_and_test():
    today = datetime.now().strftime("%Y%m%d")
    output_dir = Path(f"data/raw/mops/{today}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        for name, config in ENDPOINTS.items():
            url = f"{BASE_URL}/{config['endpoint']}"
            payload = config["payload"]
            
            print(f"Fetching {name}...")
            try:
                response = client.post(url, data=payload)
                response.raise_for_status()
                
                text = response.text
                has_error = any(err in text for err in ["參數傳入錯誤", "年度不可空白", "請輸入年度", "查無資料", "傳入參數錯誤"])
                has_table = "<table" in text.lower() and len(text) > 10000
                
                status = "✓ SUCCESS" if has_table else ("✗ ERROR" if has_error else "? UNCLEAR")
                print(f"  {status} ({len(text):,} bytes)")
                
                results.append({
                    "name": name,
                    "status": status,
                    "size": len(text)
                })
                
                # Save HTML
                filepath = output_dir / f"{name}_sii_113_final.html"
                filepath.write_text(text, encoding="utf-8")
                
            except Exception as e:
                print(f"  Error: {e}")
                results.append({"name": name, "status": "ERROR", "error": str(e)})
    
    print("\n=== Summary ===")
    for r in results:
        print(f"  {r['name']}: {r['status']} ({r.get('size', 0):,} bytes)")


if __name__ == "__main__":
    fetch_and_test()
