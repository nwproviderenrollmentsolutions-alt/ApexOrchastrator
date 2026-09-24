"""Local environment validation -- zero network calls, zero API spend.

Run via `python -m apex_orchestrator.cli --doctor`. Checks the things that
fail loudly and confusingly if missing (a package that isn't installed, no
ffmpeg on PATH, an unwritable runs/ directory) and reports which free-tier
integrations are configured, without touching a single external service.
"""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table

from apex_orchestrator.config import CONFIG

REQUIRED_PACKAGES = [
    ("requests", "HTTP client used by every network-touching stage"),
    ("dotenv", ".env loading (python-dotenv)"),
    ("rich", "terminal live view"),
    ("edge_tts", "voiceover synthesis"),
    ("pytrends", "Google Trends signal in Viral Radar"),
    ("fastapi", "local dashboard"),
    ("uvicorn", "local dashboard server"),
    ("googleapiclient", "YouTube publish + trending lookup"),
    ("google_auth_oauthlib", "YouTube OAuth flow"),
    ("cryptography", "transitive dependency of google-auth"),
]


def _check_packages(console: Console) -> bool:
    table = Table(title="Python packages")
    table.add_column("Package")
    table.add_column("Status")
    table.add_column("Used for")
    all_ok = True
    for module_name, purpose in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
            table.add_row(module_name, "[green]ok[/green]", purpose)
        except ImportError as e:
            all_ok = False
            table.add_row(module_name, f"[red]missing[/red] ({e})", purpose)
    console.print(table)
    return all_ok


def _check_ffmpeg(console: Console) -> bool:
    path = shutil.which("ffmpeg")
    if path:
        console.print(f"[green]ok[/green] ffmpeg found at {path}")
        return True
    console.print(
        "[red]missing[/red] ffmpeg not found on PATH -- video rendering (UGC Creator's "
        "assemble step) will fail. Install it, e.g. `apt-get install ffmpeg`."
    )
    return False


def _check_runs_dir(console: Console) -> bool:
    runs_dir = Path(CONFIG.runs_dir)
    try:
        runs_dir.mkdir(parents=True, exist_ok=True)
        probe = runs_dir / ".doctor_write_test"
        probe.write_text("ok")
        probe.unlink()
        console.print(f"[green]ok[/green] runs directory is writable: {runs_dir.resolve()}")
        return True
    except OSError as e:
        console.print(f"[red]failed[/red] runs directory {runs_dir} is not writable: {e}")
        return False


def _check_integrations(console: Console) -> None:
    table = Table(title="Configured integrations (all free tier -- see README for setup links)")
    table.add_column("Integration")
    table.add_column("Status")
    for name, active in CONFIG.integration_summary().items():
        status = "[green]on[/green]" if active else "[dim]off (runs in offline/mock mode)[/dim]"
        table.add_row(name, status)
    console.print(table)


def run_doctor() -> bool:
    """Returns True iff every *required* check passed. Integrations left
    'off' are not failures -- they're a valid, supported configuration.
    """
    console = Console()
    console.print(
        "[bold]ApexOrchastrator doctor[/bold] -- checking your local setup "
        "(no network calls, no API spend)\n"
    )

    packages_ok = _check_packages(console)
    console.print()
    ffmpeg_ok = _check_ffmpeg(console)
    console.print()
    runs_dir_ok = _check_runs_dir(console)
    console.print()
    _check_integrations(console)
    console.print()

    if packages_ok and ffmpeg_ok and runs_dir_ok:
        console.print(
            "[bold green]All required checks passed.[/bold green] Integrations left "
            "'off' above will run in offline/mock mode -- see README for free setup steps."
        )
        return True

    console.print("[bold red]Some required checks failed.[/bold red] Fix the items marked above before running the pipeline.")
    return False
