from datetime import datetime
from pathlib import Path
from typing import Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from app.config import settings
from app.database import get_db
from app.models import AccountVerificationDB, ProblemDB, ProblemStatus, SubmissionDB

console = Console()

class ReportingService:
    """Generates visual status tables and exportable markdown reports."""

    @staticmethod
    def print_status() -> None:
        """Prints a comprehensive progress summary to the terminal."""
        with get_db() as db:
            problems = db.query(ProblemDB).all()
            total = len(problems)

            status_counts: Dict[str, int] = {}
            for p in problems:
                status_counts[p.status] = status_counts.get(p.status, 0) + 1

            accepted = status_counts.get(ProblemStatus.ACCEPTED.value, 0)
            passed = status_counts.get(ProblemStatus.LOCAL_TEST_PASSED.value, 0)
            pending = status_counts.get(ProblemStatus.PENDING.value, 0)
            failed = status_counts.get(ProblemStatus.LOCAL_TEST_FAILED.value, 0)
            rejected = status_counts.get(ProblemStatus.REJECTED.value, 0)

            # Verification Info
            latest_verif = (
                db.query(AccountVerificationDB)
                .order_by(AccountVerificationDB.verified_at.desc())
                .first()
            )

            # Recent Submissions
            recent_subs = (
                db.query(SubmissionDB)
                .order_by(SubmissionDB.created_at.desc())
                .limit(5)
                .all()
            )

        # Overview Table
        table = Table(title="NeetCode 150 Automation Status", show_header=True, header_style="bold cyan")
        table.add_column("Category", style="dim")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        pct = lambda c: f"{(c / total * 100):.1f}%" if total > 0 else "0.0%"
        table.add_row("Total Problems", str(total), "100.0%")
        table.add_row("[green]Accepted (LeetCode)[/green]", str(accepted), pct(accepted))
        table.add_row("[blue]Local Tests Passed[/blue]", str(passed), pct(passed))
        table.add_row("[yellow]Pending / Untested[/yellow]", str(pending), pct(pending))
        table.add_row("[red]Local Tests Failed[/red]", str(failed), pct(failed))
        table.add_row("[magenta]Rejected (LeetCode)[/magenta]", str(rejected), pct(rejected))

        console.print(table)

        # Account Verification Panel
        if latest_verif:
            verif_color = "green" if latest_verif.status == "VERIFIED" else "red"
            verif_text = (
                f"[{verif_color}]Status: {latest_verif.status}[/{verif_color}]\n"
                f"Username: {latest_verif.username or 'N/A'}\n"
                f"Expected: {latest_verif.expected_username}\n"
                f"Verified At: {latest_verif.verified_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            verif_text = "[yellow]No account verification recorded yet. Run: python main.py verify-account[/yellow]"

        console.print(Panel(verif_text, title="LeetCode Account Identity", expand=False))

        # Recent Submissions Table
        if recent_subs:
            sub_table = Table(title="Recent Submissions", show_header=True, header_style="bold magenta")
            sub_table.add_column("Problem", style="cyan")
            sub_table.add_column("Verdict", style="bold")
            sub_table.add_column("Runtime", justify="right")
            sub_table.add_column("Memory", justify="right")
            sub_table.add_column("Time", style="dim")

            for s in recent_subs:
                color = "green" if s.verdict == "Accepted" else "red"
                sub_table.add_row(
                    s.problem_slug,
                    f"[{color}]{s.verdict}[/{color}]",
                    f"{s.runtime_ms} ms" if s.runtime_ms else "N/A",
                    f"{s.memory_mb:.1f} MB" if s.memory_mb else "N/A",
                    s.created_at.strftime("%H:%M:%S"),
                )
            console.print(sub_table)

    @staticmethod
    def generate_report() -> Path:
        """Generates an exportable markdown report file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = settings.REPORTS_DIR / f"report_{timestamp}.md"

        with get_db() as db:
            problems = db.query(ProblemDB).order_by(ProblemDB.order_index.asc()).all()
            total = len(problems)
            accepted = sum(1 for p in problems if p.status == ProblemStatus.ACCEPTED.value)
            passed = sum(1 for p in problems if p.status == ProblemStatus.LOCAL_TEST_PASSED.value)

            content = [
                f"# NeetCode 150 Automation Report",
                f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                f"",
                f"## Executive Summary",
                f"- **Total Problems:** {total}",
                f"- **Accepted on LeetCode:** {accepted} ({(accepted/total*100):.1f}%)" if total else "",
                f"- **Locally Verified:** {passed} ({(passed/total*100):.1f}%)" if total else "",
                f"",
                f"## Problem Progress Breakdown",
                f"| # | Slug | Difficulty | Category | Status | Retries |",
                f"|---|---|---|---|---|---|",
            ]

            for p in problems:
                content.append(
                    f"| {p.order_index} | [{p.slug}]({p.url}) | {p.difficulty} | {p.category} | {p.status} | {p.retry_count} |"
                )

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        console.print(f"[green]Report saved to {report_file}[/green]")
        return report_file
