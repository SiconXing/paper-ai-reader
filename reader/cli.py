import argparse
from pathlib import Path

from .output import write_csv, write_json, write_report
from .pipeline import run_pipeline
from .sources import CONFERENCES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Grab public papers from major CS conferences and rank them with AI."
    )
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
        default=50,
        help="Maximum number of papers to fetch for each conference.",
    )
    parser.add_argument(
        "--interest",
        type=str,
        default="",
        help="Your research interests, used for AI filtering.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=70,
        help="Minimum AI interest score to keep a paper.",
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Fetch papers only, do not call the AI ranking step.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/papers.json",
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Also export the results to CSV. Disabled by default.",
    )
    parser.add_argument(
        "--csv-output",
        type=str,
        default="",
        help="Optional CSV output path. Defaults to the JSON output path with .csv suffix.",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Also generate a Markdown summary report. Disabled by default.",
    )
    parser.add_argument(
        "--report-output",
        type=str,
        default="",
        help="Optional report path. Defaults to the JSON output path with .md suffix.",
    )
    parser.add_argument(
        "--list-conferences",
        action="store_true",
        help="Print the supported conference aliases and exit.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_conferences:
        for alias, config in sorted(CONFERENCES.items()):
            print(f"{alias}\t{config.name}\t{config.stream_id}")
        return 0

    if not args.year:
        parser.error("--year is required unless --list-conferences is used.")

    if not args.skip_ai and not args.interest.strip():
        parser.error("--interest is required unless --skip-ai is used.")

    results = run_pipeline(
        conference_aliases=args.conferences,
        year=args.year,
        limit_per_conf=args.limit_per_conf,
        interest=args.interest,
        min_score=args.min_score,
        skip_ai=args.skip_ai,
    )

    output_path = Path(args.output)
    write_json(output_path, results)

    csv_path = None
    if args.export_csv:
        csv_path = Path(args.csv_output) if args.csv_output else output_path.with_suffix(".csv")
        write_csv(csv_path, results)

    report_path = None
    if args.generate_report:
        report_path = (
            Path(args.report_output) if args.report_output else output_path.with_suffix(".md")
        )
        write_report(
            report_path,
            results,
            interest=args.interest,
            skip_ai=args.skip_ai,
            min_score=args.min_score,
        )

    total = len(results)
    kept = sum(1 for item in results if item.get("selected", True))
    print(f"Wrote {total} papers to {output_path}")
    if csv_path:
        print(f"Wrote CSV to {csv_path}")
    if report_path:
        print(f"Wrote report to {report_path}")
    if not args.skip_ai:
        print(f"Selected {kept} papers with score >= {args.min_score}")
    return 0
