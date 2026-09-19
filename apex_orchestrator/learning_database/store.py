"""SQLite-backed record of every run and the performance it earned.

One shared database across all runs (not per-run, unlike the JSONL event
logs), since the whole point is to compare frameworks against each other
over time. SQLite is the free/no-setup choice here -- it's a single file,
part of the Python standard library, and this workload (one write per run,
occasional aggregate reads) is well within what it's good at.

Every function takes an explicit `db_path` (defaulting to the configured
one) so tests can point at a throwaway file instead of the real database.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import PerformanceSnapshot

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    niche TEXT NOT NULL,
    framework TEXT NOT NULL,
    brief_id TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS performance (
    run_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    remote_id TEXT NOT NULL,
    views INTEGER NOT NULL,
    watch_time_sec REAL NOT NULL,
    retention_pct REAL NOT NULL,
    shares INTEGER NOT NULL,
    saves INTEGER NOT NULL,
    comments INTEGER NOT NULL,
    clicks INTEGER NOT NULL,
    recorded_at REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs (run_id)
);
"""


def default_db_path() -> Path:
    return Path(CONFIG.runs_dir) / "learning.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def record_run(run_id: str, niche: str, framework: str, brief_id: str, db_path: Path | None = None) -> None:
    with _connect(db_path or default_db_path()) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO runs (run_id, niche, framework, brief_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, niche, framework, brief_id, time.time()),
        )


def record_performance(run_id: str, snapshots: list[PerformanceSnapshot], db_path: Path | None = None) -> None:
    if not snapshots:
        return
    with _connect(db_path or default_db_path()) as conn:
        conn.executemany(
            """INSERT INTO performance
               (run_id, platform, remote_id, views, watch_time_sec, retention_pct, shares, saves, comments, clicks, recorded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    run_id,
                    s.platform,
                    s.remote_id,
                    s.views,
                    s.watch_time_sec,
                    s.retention_pct,
                    s.shares,
                    s.saves,
                    s.comments,
                    s.clicks,
                    time.time(),
                )
                for s in snapshots
            ],
        )


def framework_leaderboard(niche: str | None = None, db_path: Path | None = None) -> list[tuple[str, float, int]]:
    """(framework, avg_views, sample_count), best (highest avg views) first.

    Only frameworks with at least one recorded performance snapshot appear.
    """
    where = "WHERE r.niche = ?" if niche else ""
    params = (niche,) if niche else ()
    with _connect(db_path or default_db_path()) as conn:
        rows = conn.execute(
            f"""
            SELECT r.framework, AVG(p.views), COUNT(*)
            FROM runs r JOIN performance p ON r.run_id = p.run_id
            {where}
            GROUP BY r.framework
            ORDER BY AVG(p.views) DESC
            """,
            params,
        ).fetchall()
    return [(framework, avg_views, count) for framework, avg_views, count in rows]


def best_framework_for_niche(niche: str, min_samples: int = 2, db_path: Path | None = None) -> str | None:
    """Only trust the leaderboard once a framework has a couple of data
    points for this niche -- a single lucky post shouldn't lock in a
    framework choice.
    """
    board = framework_leaderboard(niche, db_path)
    for framework, _avg_views, count in board:
        if count >= min_samples:
            return framework
    return None
