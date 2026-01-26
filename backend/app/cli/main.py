import typer
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.services.crawler_service import CrawlerService
from app.services.crawler_service import CrawlerService
from app.services.company_service import CompanyService
from app.services.violation_service import ViolationService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)

URLS = {
    "Listed": "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv",
    "OTC": "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv",
    "Emerging": "https://mopsfin.twse.com.tw/opendata/t187ap03_R.csv"
}

VIOLATION_URLS = {
    "LaborStandards": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030225-QDf",
    "GenderEquality": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030226-rtp",
    "Pension": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030227-9UN",
    "EmploymentService": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030228-K1J",
    "OccupationalSafety": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030466-zyC",
    "Insurance": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030471-uro",
    "MiddleAged": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030472-IXx",
    "Union": "https://apiservice.mol.gov.tw/OdService/download/A17000000J-030542-2ZK"
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

@app.command()
def sync_violations(
    source: str = typer.Option("all", "--source", help="Source to sync (all, or specific key like LaborStandards)"),
):
    """
    Sync violation data from MOL Open Data.
    """
    crawler_service = CrawlerService()
    violation_service = ViolationService()
    
    target_sources = []
    if source.lower() == "all":
        target_sources = list(VIOLATION_URLS.keys())
    elif source in VIOLATION_URLS:
        target_sources = [source]
    else:
        typer.echo(f"Invalid source: {source}. Available: {list(VIOLATION_URLS.keys())}")
        raise typer.Exit(code=1)

    # Data Dir
    today_str = datetime.now().strftime("%Y%m%d")
    data_dir = Path(f"data/raw/violations/{today_str}")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download
    typer.echo("--- Starting Violation Download ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    
    # Need to override Crawler to support headers? 
    # Actually CrawlerService default implementation uses requests.get without custom headers argument exposed.
    # Let's check CrawlerService implementation.
    # It just takes url. We might need to update CrawlerService if websites block empty UA.
    # For now let's hope it works or we update CrawlerService. The previous analysis required UA.
    
    # Let's quickly patch/use direct request here if CrawlerService is too simple, 
    # OR better: Update CrawlerService to accept headers.
    # But for now, let's try using the existing one. If it fails we'll know.
    # Wait, the analysis script failed without UA. So we MUST update CrawlerService or pass headers.
    # Let's assume we update CrawlerService in the next step or right before this.
    # Actually, I'll update CrawlerService to accept kwargs.
    
    for src in target_sources:
        url = VIOLATION_URLS[src]
        save_path = data_dir / f"{src}.json"
        
        if not save_path.exists():
            # Pass headers via kwargs if we update CrawlerService, 
            # Or currently just rely on it. 
            # Given the previous experience, I should probably update CrawlerService first.
            # But let's write this code assuming I will update CrawlerService to take **kwargs.
            success = crawler_service.download_file(url, save_path, headers=headers)
            if not success:
                logger.error(f"Failed to download {src}")
        else:
            logger.info(f"File already exists: {save_path}")

    # 2. Sync
    typer.echo("--- Starting Violation Sync ---")
    violation_service.sync_violations(data_dir, target_sources)
    typer.echo("Violation Sync completed.")

if __name__ == "__main__":
    app()
