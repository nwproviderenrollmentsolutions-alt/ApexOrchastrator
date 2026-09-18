"""Local web dashboard: a browser view of pipeline runs, polling the same
JSONL event log the terminal `rich` view reads from. Run with:

    python -m apex_orchestrator.dashboard

then open http://127.0.0.1:8765 (or DASHBOARD_HOST/DASHBOARD_PORT).
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apex_orchestrator.config import CONFIG

app = FastAPI(title="ApexOrchastrator Dashboard")

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/runs")
def list_runs() -> list[str]:
    runs_dir = Path(CONFIG.runs_dir)
    if not runs_dir.exists():
        return []
    return sorted((p.name for p in runs_dir.iterdir() if p.is_dir()), reverse=True)


@app.get("/api/runs/{run_id}/events")
def get_events(run_id: str) -> list[dict]:
    log_path = Path(CONFIG.runs_dir) / run_id / "events.jsonl"
    if not log_path.exists():
        raise HTTPException(404, f"no events for run {run_id}")
    events = []
    for line in log_path.read_text().splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=CONFIG.dashboard_host, port=CONFIG.dashboard_port)


if __name__ == "__main__":
    main()
