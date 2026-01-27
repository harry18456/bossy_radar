"""
Test different payload combinations for MOPS endpoints to find working parameters.
Run with: uv run python scripts/test_mops_params.py
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

# Test different parameter combinations
TEST_CASES = [
    # t100sb15 - Non-manager salary
    {
        "name": "t100sb15_v1",
        "endpoint": "ajax_t100sb15",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",  # Try different year param name
        }
    },
    {
        "name": "t100sb15_v2",
        "endpoint": "ajax_t100sb15",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1", 
            "off": "1",
            "TYPEK": "sii",
            "RYEAR": "113",  # Try RYEAR instead
        }
    },
    {
        "name": "t100sb15_v3",
        "endpoint": "ajax_t100sb15",
        "payload": {
            "encodeURIComponent": "1",
            "step": "2",  # Try step 2
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",
        }
    },
    # t100sb13 - Welfare policy summary
    {
        "name": "t100sb13_v1",
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
    {
        "name": "t100sb13_v2",
        "endpoint": "ajax_t100sb13",
        "payload": {
            "encodeURIComponent": "1",
            "step": "2",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",
        }
    },
    {
        "name": "t100sb13_v3",
        "endpoint": "ajax_t100sb13",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "true",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",
        }
    },
    # t222sb01 - Salary adjustment
    {
        "name": "t222sb01_v1",
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
    {
        "name": "t222sb01_v2",
        "endpoint": "ajax_t222sb01",
        "payload": {
            "encodeURIComponent": "1",
            "step": "2",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": "113",
        }
    },
    {
        "name": "t222sb01_v3",
        "endpoint": "ajax_t222sb01",
        "payload": {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "true",
            "off": "1",
            "TYPEK": "sii",
            "YEAR": "113",  # Try uppercase YEAR
        }
    },
]


def test_params():
    today = datetime.now().strftime("%Y%m%d")
    output_dir = Path(f"data/raw/mops/{today}/tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        for test in TEST_CASES:
            name = test["name"]
            url = f"{BASE_URL}/{test['endpoint']}"
            payload = test["payload"]
            
            print(f"Testing {name}...")
            try:
                response = client.post(url, data=payload)
                response.raise_for_status()
                
                # Check if it's an error page
                text = response.text
                has_error = any(err in text for err in ["參數傳入錯誤", "年度不可空白", "請輸入年度", "查無資料"])
                has_table = "<table" in text.lower() and len(text) > 5000
                
                status = "✓ HAS DATA" if has_table else ("✗ ERROR" if has_error else "? UNCLEAR")
                print(f"  {status} ({len(text)} bytes)")
                
                # Save response
                filepath = output_dir / f"{name}.html"
                filepath.write_text(text, encoding="utf-8")
                
            except Exception as e:
                print(f"  Error: {e}")


if __name__ == "__main__":
    test_params()
    print("\nDone! Check data/raw/mops/{date}/tests/ for results.")
