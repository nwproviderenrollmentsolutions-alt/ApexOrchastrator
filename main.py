"""Run one scan/publish/learn cycle of the ApexOrchastrator pipeline and print a summary."""

from __future__ import annotations

import argparse

from apex.pipeline import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ApexOrchastrator viral-content pipeline.")
    parser.add_argument("--cycles", type=int, default=1, help="number of scan/publish/learn cycles to run")
    parser.add_argument("--signals-per-scan", type=int, default=5, help="candidates pulled per radar scan")
    parser.add_argument("--product", type=str, default="our product", help="what the UGC content is promoting")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible mock runs")
    args = parser.parse_args()

    orchestrator = Orchestrator(product_context=args.product, seed=args.seed)

    for cycle_num in range(1, args.cycles + 1):
        print(f"\n=== Cycle {cycle_num} ===")
        for result in orchestrator.run_cycle(signals_per_scan=args.signals_per_scan):
            title = result.qc_result.package.strategy.working_title
            if not result.published:
                print(f"[REJECTED] {title!r} -- {result.reject_reason}")
                continue
            print(f"[PUBLISHED] {title!r}")
            for record in result.learning_records:
                platform = record.metrics.publish_result.platform.value
                print(f"  - {platform}: {record.notes}")

    print(f"\nWinning topics so far: {orchestrator.learning_db.winning_topics()}")


if __name__ == "__main__":
    main()
