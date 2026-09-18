"""Observability: every stage reports through this event bus.

Two outputs, both driven by the same events:
1. A live `rich` table in the terminal (zero setup, always on).
2. A JSONL file per run that the local web dashboard polls, so you can
   also watch a run from a browser (`python -m apex_orchestrator.dashboard`).
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table

from apex_orchestrator.config import CONFIG

STATUS_STYLE = {
    "pending": "dim",
    "running": "yellow",
    "ok": "green",
    "failed": "red",
    "mocked": "cyan",
    "skipped": "dim",
}

# Declared up front so the live table shows the whole pipeline immediately,
# not just the stages that have emitted an event yet.
STAGE_ORDER = [
    "ugc.script",
    "ugc.voiceover",
    "ugc.broll",
    "ugc.captions",
    "ugc.assemble",
    "qc.hook_score",
    "qc.brand_safety",
    "qc.disclosure",
    "qc.copyright",
    "publish.youtube_shorts",
    "publish.tiktok",
    "publish.instagram",
]


@dataclass
class Event:
    ts: float
    run_id: str
    stage: str
    status: str
    message: str
    data: Optional[dict] = None


def _json_default(obj: Any):
    if is_dataclass(obj):
        return asdict(obj)
    return str(obj)


class EventBus:
    def __init__(self, run_id: Optional[str] = None, live_console: bool = True):
        self.run_id = run_id or time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.run_dir = Path(CONFIG.runs_dir) / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.run_dir / "events.jsonl"
        self._stage_status: dict[str, tuple[str, str]] = {s: ("pending", "") for s in STAGE_ORDER}
        self._console = Console()
        self._live: Optional[Live] = Live(self._render(), console=self._console, refresh_per_second=6) if live_console else None
        if self._live:
            self._live.start()

    def _render(self) -> Table:
        table = Table(title=f"ApexOrchastrator run {self.run_id}")
        table.add_column("Stage")
        table.add_column("Status")
        table.add_column("Detail")
        for stage in STAGE_ORDER:
            status, detail = self._stage_status.get(stage, ("pending", ""))
            style = STATUS_STYLE.get(status, "white")
            table.add_row(stage, f"[{style}]{status}[/{style}]", detail)
        return table

    def emit(self, stage: str, status: str, message: str, data: Optional[dict] = None) -> None:
        event = Event(ts=time.time(), run_id=self.run_id, stage=stage, status=status, message=message, data=data)
        with self.log_path.open("a") as f:
            f.write(json.dumps(asdict(event), default=_json_default) + "\n")

        self._stage_status[stage] = (status, message)
        if self._live:
            self._live.update(self._render())
        else:
            self._console.log(f"[{stage}] {status}: {message}")

    def stop(self) -> None:
        if self._live:
            self._live.stop()

    def __enter__(self) -> "EventBus":
        return self

    def __exit__(self, *exc) -> None:
        self.stop()
