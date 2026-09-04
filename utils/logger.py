from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.text import Text

console = Console()


def print_banner():
    banner = Text()
    banner.append("⚡ YouTube Terminal Downloader", style="bold cyan")
    banner.append(
        "\nFast, resilient CLI downloader for videos, playlists & clips",
        style="dim white",
    )
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))


def print_detection(message: str):
    console.print(
        f"  [bold green]✓[/bold green] [dim]Detected:[/dim] [bold white]{message}[/bold white]"
    )


def print_error(message: str):
    console.print(f"  [bold red]✗[/bold red] [red]{message}[/red]")


def print_success(message: str):
    console.print(f"  [bold green]✓[/bold green] [green]{message}[/green]")


def print_warning(message: str):
    console.print(f"  [bold yellow]⚠[/bold yellow] [yellow]{message}[/yellow]")


def print_info(message: str):
    console.print(f"  [bold cyan]ℹ[/bold cyan] [cyan]{message}[/cyan]")


def print_summary(done: int, failed: int, total: int):
    table = Table(
        title="📊 Download Summary",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    table.add_column("Status", style="bold", width=16)
    table.add_column("Count", justify="right", width=10)
    table.add_row("[green]✓ Completed[/green]", f"[bold green]{done}[/bold green]")
    if failed > 0:
        table.add_row("[red]✗ Failed[/red]", f"[bold red]{failed}[/bold red]")
    else:
        table.add_row("[dim]✗ Failed[/dim]", "[dim]0[/dim]")
    table.add_row("[bold blue]Total[/bold blue]", f"[bold blue]{total}[/bold blue]")
    console.print()
    console.print(table)
    console.print()


def get_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(bar_width=30, style="dim cyan", complete_style="bold cyan"),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )
