"""CLI entrypoint.

    python -m apex_orchestrator.cli --topic "..." --angle "..." --cta "..." \\
        --platforms youtube_shorts,tiktok

    python -m apex_orchestrator.cli --brief path/to/brief.json

Until the Viral Radar / Analyst / Strategist stages exist, a ContentBrief
is either built from flags or loaded from a JSON file shaped like
ContentBrief's fields (see contracts.py).
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict

from rich.console import Console

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import ContentBrief
from apex_orchestrator.pipeline import run_pipeline

console = Console()


def _load_brief(args: argparse.Namespace) -> ContentBrief:
    if args.brief:
        data = json.loads(open(args.brief).read())
        data.setdefault("brief_id", uuid.uuid4().hex[:8])
        return ContentBrief(**data)

    if not args.topic:
        console.print("[red]Either --brief or --topic is required.[/red]")
        sys.exit(1)

    return ContentBrief(
        brief_id=uuid.uuid4().hex[:8],
        topic=args.topic,
        angle=args.angle or args.topic,
        cta=args.cta or "Follow for more",
        key_claims=args.claims.split("|") if args.claims else [],
        target_platforms=args.platforms.split(",") if args.platforms else ["youtube_shorts"],
        product_name=args.product,
        disclosure_required=args.disclosure,
        max_duration_sec=args.max_duration,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ApexOrchastrator: UGC Creator -> QC -> Publish")
    parser.add_argument("--brief", help="path to a ContentBrief JSON file")
    parser.add_argument("--topic")
    parser.add_argument("--angle")
    parser.add_argument("--cta")
    parser.add_argument("--claims", help="pipe-separated key claims, e.g. 'fact one|fact two'")
    parser.add_argument("--product")
    parser.add_argument("--platforms", help="comma-separated: youtube_shorts,tiktok,instagram_reels")
    parser.add_argument("--disclosure", action="store_true", help="mark this content as sponsored/ad")
    parser.add_argument("--max-duration", type=int, default=45, dest="max_duration")
    parser.add_argument("--skip-qc-gate", action="store_true", help="publish even if QC fails (debugging only)")
    args = parser.parse_args()

    brief = _load_brief(args)

    console.print("[bold]Active integrations:[/bold]")
    for name, active in CONFIG.integration_summary().items():
        console.print(f"  {'[green]on[/green] ' if active else '[dim]off[/dim]'} {name}")
    console.print()

    result = run_pipeline(brief, skip_qc_gate=args.skip_qc_gate)

    console.print()
    console.print(f"[bold]Run {result.run_id}[/bold] -- events at runs/{result.run_id}/events.jsonl")
    console.print(f"QC passed: {'[green]yes[/green]' if result.qc_report.passed else '[red]no[/red]'}")
    for pr in result.publish_results:
        console.print(f"  {pr.platform}: {pr.status}" + (f" -> {pr.url}" if pr.url else "") + (f" ({pr.error})" if pr.error else ""))

    summary_path = f"runs/{result.run_id}/summary.json"
    with open(summary_path, "w") as f:
        json.dump(
            {
                "brief": asdict(result.brief),
                "qc_report": asdict(result.qc_report),
                "publish_results": [asdict(p) for p in result.publish_results],
                "video_path": result.asset.video_path,
            },
            f,
            indent=2,
        )
    console.print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
