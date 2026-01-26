import requests
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CrawlerService:
    def __init__(self):
        pass

    def download_file(self, url: str, save_path: Path, max_retries: int = 3) -> bool:
        """
        Download a file from a URL to a local path with retries.
        """
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {url} (Attempt {attempt + 1}/{max_retries})")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                with open(save_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Saved to {save_path}")
                return True
            except Exception as e:
                logger.error(f"Error downloading {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return False
        return False
