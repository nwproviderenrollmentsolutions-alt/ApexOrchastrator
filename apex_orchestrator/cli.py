"""CLI entrypoint.

Full loop, starting from Viral Radar:
    python -m apex_orchestrator.cli --niche "budget travel" --product "..." \\
        --cta "..." --platforms youtube_shorts,tiktok

Skip straight to UGC Creator with a hand-built brief:
    python -m apex_orchestrator.cli --topic "..." --angle "..." --cta "..." \\
        --platforms youtube_shorts,tiktok

    python -m apex_orchestrator.cli --brief path/to/brief.json

--niche is mutually exclusive with --brief/--topic: it runs Viral Radar ->
Viral Analyst AI -> Content Strategist to build the brief for you, instead
of you supplying one directly.

Once a run has actually published and had time to accumulate real
analytics (hours/days later, not immediately), close the loop:
    python -m apex_orchestrator.cli --collect-performance <run_id>
This runs Performance Engine -> Learning Database, so future --niche runs
in the same niche can learn which framework performed best.
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
from apex_orchestrator.pipeline import collect_performance_for_run, run_full_pipeline, run_pipeline

console = Console()


def _load_brief(args: argparse.Namespace) -> ContentBrief:
    if args.brief:
        data = json.loads(open(args.brief).read())
        data.setdefault("brief_id", uuid.uuid4().hex[:8])
        return ContentBrief(**data)

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
    parser = argparse.ArgumentParser(description="ApexOrchastrator: Viral Radar -> ... -> Publish")
    parser.add_argument("--niche", help="run the full loop starting at Viral Radar, e.g. 'budget travel'")
    parser.add_argument("--brief", help="path to a ContentBrief JSON file (skips Radar/Analyst/Strategist)")
    parser.add_argument("--topic", help="build a brief directly (skips Radar/Analyst/Strategist)")
    parser.add_argument("--angle", help="only used with --topic")
    parser.add_argument("--cta")
    parser.add_argument("--claims", help="pipe-separated key claims, e.g. 'fact one|fact two'")
    parser.add_argument("--product")
    parser.add_argument("--platforms", help="comma-separated: youtube_shorts,tiktok,instagram_reels")
    parser.add_argument("--disclosure", action="store_true", help="mark this content as sponsored/ad")
    parser.add_argument("--max-duration", type=int, default=45, dest="max_duration")
    parser.add_argument("--skip-qc-gate", action="store_true", help="publish even if QC fails (debugging only)")
    parser.add_argument(
        "--collect-performance",
        metavar="RUN_ID",
        help="Performance Engine -> Learning Database for a run that already published",
    )
    args = parser.parse_args()

    if args.collect_performance:
        snapshots = collect_performance_for_run(args.collect_performance)
        console.print(f"[bold]Collected {len(snapshots)} performance snapshot(s)[/bold] for run {args.collect_performance}")
        for s in snapshots:
            console.print(f"  {s.platform}: views={s.views} shares={s.shares} saves={s.saves} comments={s.comments}")
        return

    if not (args.niche or args.brief or args.topic):
        console.print("[red]One of --niche, --brief, --topic, or --collect-performance is required.[/red]")
        sys.exit(1)

    console.print("[bold]Active integrations:[/bold]")
    for name, active in CONFIG.integration_summary().items():
        console.print(f"  {'[green]on[/green] ' if active else '[dim]off[/dim]'} {name}")
    console.print()

    if args.niche:
        result = run_full_pipeline(
            args.niche,
            product_name=args.product,
            cta=args.cta,
            platforms=args.platforms.split(",") if args.platforms else None,
            key_claims=args.claims.split("|") if args.claims else None,
            disclosure_required=args.disclosure,
            max_duration_sec=args.max_duration,
            skip_qc_gate=args.skip_qc_gate,
        )
    else:
        brief = _load_brief(args)
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
                "niche": result.niche,
                "framework": result.framework,
                "brief": asdict(result.brief),
                "qc_report": asdict(result.qc_report),
                "publish_results": [asdict(p) for p in result.publish_results],
                "video_path": result.asset.video_path,
            },
            f,
            indent=2,
        )
    console.print(f"Summary written to {summary_path}")
    if any(p.status == "published" for p in result.publish_results):
        console.print(
            f"Once analytics have had time to accumulate, run: "
            f"python -m apex_orchestrator.cli --collect-performance {result.run_id}"
        )


if __name__ == "__main__":
    main()
