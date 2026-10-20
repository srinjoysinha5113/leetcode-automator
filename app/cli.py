import asyncio
import os
import sys
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from app.account_verifier import AccountVerifier
from app.config import logger, settings
from app.database import DatabaseManager, init_db
from app.llm_client import OllamaClient
from app.orchestrator import PipelineOrchestrator
from app.problem_source import ProblemSource
from app.reporting import ReportingService

console = Console()

@click.group()
def cli():
    """NeetCode 150 Automated LeetCode Solver CLI."""
    pass

@cli.command()
def setup():
    """Initializes database tables, creates directories, and imports NeetCode 150 problems."""
    console.print("[bold cyan]Running leetcode-automator setup...[/bold cyan]")
    init_db()
    source = ProblemSource()
    count = source.import_all_manifest_problems()
    console.print(f"[bold green]Setup complete! Initialized database with {count} NeetCode 150 problems.[/bold green]")

@cli.command()
def doctor():
    """Checks Python dependencies, Ollama, model availability, database, browser, and configuration."""
    console.print("\n[bold cyan]Running System Diagnostic (Doctor)...[/bold cyan]\n")
    table = Table(title="System & Dependency Health Check", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    all_ok = True

    # 1. Python Version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 11):
        table.add_row("Python Version", "[green]PASS[/green]", f"Python {py_ver} (>= 3.11 requirement met)")
    else:
        table.add_row("Python Version", "[red]FAIL[/red]", f"Python {py_ver} (< 3.11)")
        all_ok = False

    # 2. Database
    try:
        init_db()
        table.add_row("Database Connection", "[green]PASS[/green]", f"Connected to {settings.DATABASE_URL.split('///')[-1]}")
    except Exception as e:
        table.add_row("Database Connection", "[red]FAIL[/red]", str(e))
        all_ok = False

    # 3. Ollama Connectivity & Model
    llm = OllamaClient()
    healthy, msg = llm.check_health()
    if healthy:
        table.add_row("Ollama Service", "[green]PASS[/green]", f"Reachable at {settings.OLLAMA_HOST}")
        table.add_row("Ollama Model", "[green]PASS[/green]", f"Model '{settings.OLLAMA_MODEL}' ready")
    else:
        table.add_row("Ollama Service / Model", "[red]FAIL[/red]", msg)
        all_ok = False

    # 4. Playwright & Browser
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        table.add_row("Playwright Chromium", "[green]PASS[/green]", "Chromium launched successfully")
    except Exception as e:
        table.add_row("Playwright Chromium", "[red]FAIL[/red]", f"Browser error: {e}. Run: playwright install chromium")
        all_ok = False

    # 5. Configuration & Expected Username
    username = settings.EXPECTED_LEETCODE_USERNAME
    if username:
        table.add_row("Expected Username", "[green]CONFIGURED[/green]", f"User: '{username}'")
    else:
        table.add_row("Expected Username", "[yellow]NOT SET[/yellow]", "EXPECTED_LEETCODE_USERNAME in .env is empty")

    auto_sub = settings.AUTO_SUBMIT
    sub_color = "yellow" if not auto_sub else "green"
    table.add_row("AUTO_SUBMIT", f"[{sub_color}]{auto_sub}[/{sub_color}]", "Set to true only when ready for real submissions")

    console.print(table)
    if all_ok:
        console.print("\n[bold green]All core system checks passed![/bold green]\n")
    else:
        console.print("\n[bold red]Some checks failed. Please address the issues listed above.[/bold red]\n")

@cli.command("import-problems")
def import_problems():
    """Imports or refreshes the NeetCode 150 problem list in the database."""
    source = ProblemSource()
    count = source.import_all_manifest_problems()
    console.print(f"[green]Successfully loaded {count} problems into the database.[/green]")

@cli.command("verify-account")
@click.option("--timeout", default=300, help="Timeout in seconds for manual login.")
def verify_account(timeout: int):
    """Opens a visible browser to manually log into LeetCode and verify account username."""
    verifier = AccountVerifier()
    console.print("[cyan]Starting interactive LeetCode account verification...[/cyan]")
    success, username, msg = asyncio.run(verifier.interactive_login(timeout_seconds=timeout))
    if success:
        console.print(f"[bold green]{msg}[/bold green]")
    else:
        console.print(f"[bold red]Verification failed: {msg}[/bold red]")

@cli.command()
@click.option("--limit", default=1, type=int, help="Number of problems to process.")
@click.option("--all", "all_problems", is_flag=True, default=False, help="Process all remaining queued problems.")
@click.option("--slug", default=None, type=str, help="Process a specific problem slug.")
def run(limit: int, all_problems: bool, slug: Optional[str]):
    """Runs the solver pipeline in standard mode."""
    orchestrator = PipelineOrchestrator()
    asyncio.run(orchestrator.run(limit=limit, slug=slug, dry_run=False, all_problems=all_problems))

@cli.command("dry-run")
@click.option("--limit", default=1, type=int, help="Number of problems to test.")
@click.option("--slug", default=None, type=str, help="Test a specific problem slug.")
def dry_run(limit: int, slug: Optional[str]):
    """Runs generation and local testing without submitting to LeetCode."""
    console.print("[bold yellow]Running in DRY-RUN mode. Submissions are strictly disabled.[/bold yellow]")
    orchestrator = PipelineOrchestrator()
    asyncio.run(orchestrator.run(limit=limit, slug=slug, dry_run=True, all_problems=False))

@cli.command()
@click.argument("slug")
def retry(slug: str):
    """Resets a problem's state to PENDING so it can be re-run."""
    success = DatabaseManager.reset_problem(slug)
    if success:
        console.print(f"[green]Problem '{slug}' has been reset to PENDING.[/green]")
    else:
        console.print(f"[red]Problem '{slug}' not found in database.[/red]")

@cli.command()
def status():
    """Displays progress summary and recent submissions."""
    ReportingService.print_status()

@cli.command()
def report():
    """Generates an exportable markdown summary report."""
    ReportingService.generate_report()
