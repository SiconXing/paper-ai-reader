import argparse
from pathlib import Path

from .pipeline import run_fetch_pipeline
from .sources import CONFERENCES


def add_fetch_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--conferences",
        nargs="*",
        default=["cvpr", "iccv", "eccv", "nips", "icml", "iclr"],
        help="Conference aliases, e.g. cvpr iclr acl.",
    )
    parser.add_argument("--year", type=int, required=False, help="Target publication year.")
    parser.add_argument(
        "--limit-per-conf",
        type=int,
        default=10,
        help="Maximum number of papers to fetch for each conference.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/fetched_papers.jsonl",
        help="Path to the output JSONL file.",
    )
    parser.add_argument(
        "--list-conferences",
        action="store_true",
        help="Print the supported conference aliases and exit.",
    )
    return parser


def execute_fetch(args: argparse.Namespace) -> int:
    if args.list_conferences:
        for alias, config in sorted(CONFERENCES.items()):
            print(f"{alias}\t{config.name}\t{config.stream_id}")
        return 0

    if not args.year:
        raise ValueError("--year is required unless --list-conferences is used.")

    output_path = Path(args.output)
    total = run_fetch_pipeline(
        conference_aliases=args.conferences,
        year=args.year,
        limit_per_conf=args.limit_per_conf,
        output_path=output_path,
    )
    print(f"Wrote {total} papers to {output_path}")
    return 0
