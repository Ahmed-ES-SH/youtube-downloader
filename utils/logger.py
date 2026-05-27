from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_banner():
    banner = Text()
    banner.append("YouTube Terminal Downloader", style="bold cyan")
    console.print(Panel(banner, border_style="cyan"))


def print_detection(message: str):
    console.print(f"  [green]\u2713[/green] Detected: {message}")


def print_error(message: str):
    console.print(f"  [red]\u2717[/red] {message}")


def print_success(message: str):
    console.print(f"  [green]\u2713[/green] {message}")


def print_warning(message: str):
    console.print(f"  [yellow]\u26a0[/yellow] {message}")


def print_info(message: str):
    console.print(f"  [cyan]i[/cyan] {message}")


def print_summary(done: int, failed: int, total: int):
    table = Table(show_header=False, border_style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Count")
    table.add_row("[green]\u2713 Done[/green]", str(done))
    table.add_row("[red]\u2717 Failed[/red]", str(failed))
    table.add_row("[blue]Total[/blue]", str(total))
    console.print(table)


def get_progress() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )
