import typer
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.services.crawler_service import CrawlerService
from app.services.company_service import CompanyService
from app.services.violation_service import ViolationService
from app.services.mops_scraper import MopsScraper
from app.services.export_service import ExportService
from app.services.environmental_service import EnvironmentalService
from app.services.company_detail_scraper import CompanyDetailScraper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)

URLS = {
    "Listed": "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv",
    "OTC": "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv",
    "Emerging": "https://mopsfin.twse.com.tw/opendata/t187ap03_R.csv",
    "Public": "https://mopsfin.twse.com.tw/opendata/t187ap03_P.csv"
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
    market_type: str = typer.Option("all", "--type", help="Type of market to sync (all, listed, otc, emerging, public)"),
):
    """
    Sync company data from TWSE/TPEX to database.
    Order: Public -> Emerging -> OTC -> Listed (to ensure proper precedence if overlap)
    """
    crawler_service = CrawlerService()
    company_service = CompanyService()
    
    # Define execution order
    target_types = []
    if market_type.lower() == "all":
        # 排序：從初階到進階，確保最新狀態蓋掉舊狀態
        target_types = ["Public", "Emerging", "OTC", "Listed"]
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

@app.command()
def sync_mops(
    start_year: Optional[int] = typer.Option(None, "--start-year", help="Start ROC year (default: current - 4)"),
    end_year: Optional[int] = typer.Option(None, "--end-year", help="End ROC year (default: current)"),
    data_type: Optional[str] = typer.Option(None, "--data-type", help="Specific data type to sync (employee_benefit, non_manager_salary, welfare_policy, salary_adjustment)"),
):
    """
    Sync MOPS employee salary/benefit data.
    
    Data types:
    - employee_benefit: t100sb14 財務報告附註揭露之員工福利(薪資)資訊
    - non_manager_salary: t100sb15 非擔任主管職務之全時員工薪資資訊
    - welfare_policy: t100sb13 員工福利政策及權益維護措施揭露
    - salary_adjustment: t222sb01 基層員工調整薪資或分派酬勞
    """
    scraper = MopsScraper()
    
    # Calculate year range
    current_roc = scraper.get_current_roc_year()
    start_year = start_year or (current_roc - 4)
    end_year = end_year or current_roc
    years = list(range(start_year, end_year + 1))
    markets = ["sii", "otc"]
    
    typer.echo(f"--- Starting MOPS Sync ---")
    typer.echo(f"Years: {years}")
    typer.echo(f"Markets: {markets}")
    
    if data_type:
        # Sync specific data type
        data_type_map = {
            "employee_benefit": scraper.sync_employee_benefit,
            "non_manager_salary": scraper.sync_non_manager_salary,
            "welfare_policy": scraper.sync_welfare_policy,
            "salary_adjustment": scraper.sync_salary_adjustment,
        }
        
        if data_type not in data_type_map:
            typer.echo(f"Invalid data type: {data_type}. Available: {list(data_type_map.keys())}")
            raise typer.Exit(code=1)
        
        typer.echo(f"Syncing data type: {data_type}")
        data_type_map[data_type](years, markets)
    else:
        # Sync all
        typer.echo("Syncing all MOPS data types...")
        scraper.sync_all(start_year=start_year, end_year=end_year)
    
    typer.echo("MOPS Sync completed.")

@app.command()
def export(
    output_dir: Path = typer.Option("frontend/public/data", "--output-dir", help="Output directory for generated JSON files"),
):
    """
    Export all data to static JSON files for SSG.
    """
    service = ExportService(output_dir)
    service.export_all()

@app.command()
def sync_env():
    """
    Sync environmental violation data from MOENV Open Data.
    """
    service = EnvironmentalService()
    
    # Data Dir
    today_str = datetime.now().strftime("%Y%m%d")
    data_dir = Path(f"data/raw/environmental/{today_str}")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = data_dir / "EMS_P_46.json"
    
    # 1. Download
    typer.echo("--- Starting Environmental Data Download ---")
    if not file_path.exists():
        success = service.download_data(file_path)
        if not success:
            typer.echo("Failed to download environmental data")
            raise typer.Exit(code=1)
    else:
        typer.echo(f"File already exists: {file_path}")
    
    # 2. Sync
    typer.echo("--- Starting Environmental Data Sync ---")
    service.sync_data(data_dir)
    typer.echo("Environmental Sync completed.")

@app.command()
def sync_company_details(
    company_code: Optional[str] = typer.Option(None, "--code", help="Sync specific company code"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit number of companies to sync"),
    force: bool = typer.Option(False, "--force", help="Force sync even if URLs already exist"),
    retries: int = typer.Option(3, "--retries", help="Number of retries per request (-1 for infinite)"),
    retry_delay: float = typer.Option(2.0, "--retry-delay", help="Initial delay between retries in seconds"),
):
    """
    Sync additional company details (Stakeholder/Governance URLs) from MOPS t05st03.
    """
    scraper = CompanyDetailScraper()
    typer.echo("--- Starting Company Detail Sync (t05st03) ---")
    scraper.sync_all_details(limit=limit, force=force, company_code=company_code, retries=retries, delay=retry_delay)
    typer.echo("Company Detail Sync completed.")

@app.command()
def sync_all(
    skip_download: bool = typer.Option(False, "--skip-download", help="Skip download step if files exist"),
):
    """
    Run all sync commands in sequence:
    Companies -> Violations -> Environmental -> MOPS -> Export
    """
    import subprocess
    import sys
    
    commands = [
        ["sync_companies"],
        ["sync_violations"],
        ["sync_env"],
        ["sync_company_details"],
        ["sync_mops"],
        ["export"],
    ]
    
    for cmd in commands:
        typer.echo(f"\n{'='*50}")
        typer.echo(f"Running: {' '.join(cmd)}")
        typer.echo(f"{'='*50}")
        
        # Call the command directly via typer context
        try:
            ctx = typer.Context(app)
            app.invoke(ctx)
        except Exception:
            pass
        
        # Use subprocess for proper isolation
        result = subprocess.run(
            [sys.executable, "-m", "app.cli.main"] + cmd,
            cwd=Path.cwd()
        )
        
        if result.returncode != 0:
            typer.echo(f"Command {cmd} failed with code {result.returncode}")
            raise typer.Exit(code=result.returncode)
    
    typer.echo("\n" + "="*50)
    typer.echo("All sync commands completed successfully!")
    typer.echo("="*50)

if __name__ == "__main__":
    app()
