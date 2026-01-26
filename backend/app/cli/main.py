import typer
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.services.crawler_service import CrawlerService
from app.services.company_service import CompanyService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)

URLS = {
    "Listed": "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv",
    "OTC": "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv",
    "Emerging": "https://mopsfin.twse.com.tw/opendata/t187ap03_R.csv"
}

@app.command()
def hello(name: str):
    print(f"Hello {name}")

@app.command()
def goodbye():
    print("Goodbye")

@app.command()
def sync_companies(
    market_type: str = typer.Option("all", "--type", help="Type of market to sync (all, listed, otc, emerging)"),
):
    """
    Sync company data from TWSE/TPEX to database.
    Order: Emerging -> OTC -> Listed (to ensure proper precedence if overlap, though keys are unique)
    """
    crawler_service = CrawlerService()
    company_service = CompanyService()
    
    # Define execution order
    target_types = []
    if market_type.lower() == "all":
        target_types = ["Emerging", "OTC", "Listed"]
    elif market_type.capitalize() in URLS:
        target_types = [market_type.capitalize()]
    else:
        typer.echo(f"Invalid type: {market_type}. options: all, listed, otc, emerging")
        raise typer.Exit(code=1)
    
    # Prepare Data Directory
    today_str = datetime.now().strftime("%Y%m%d")
    data_dir = Path(f"data/raw/companies/{today_str}")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download Step
    typer.echo("--- Starting Download ---")
    for m_type in target_types:
        url = URLS[m_type]
        save_path = data_dir / f"{m_type}.csv"
        if not save_path.exists():
            success = crawler_service.download_file(url, save_path)
            if not success:
               logger.error(f"Failed to download {m_type}")
        else:
            logger.info(f"File already exists: {save_path}")

    # 2. Sync Step
    typer.echo("--- Starting Sync ---")
    company_service.sync_companies(data_dir, target_types)
    typer.echo("Sync completed successfully.")

if __name__ == "__main__":
    app()
