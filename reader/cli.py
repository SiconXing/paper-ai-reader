import argparse
import json
from pathlib import Path

from loader.downloader import download_papers
from .output import write_csv, write_json, write_report
from .pipeline import run_pipeline
from .sources import CONFERENCES


def add_reader_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
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
        "--download-pdfs",
        action="store_true",
        help="Download PDFs for selected papers after the pipeline finishes.",
    )
    parser.add_argument(
        "--pdf-dir",
        type=str,
        default="downloads/papers",
        help="Directory used when --download-pdfs is enabled.",
    )
    parser.add_argument(
        "--pdf-log-output",
        type=str,
        default="",
        help="Optional JSON log path for PDF download results.",
    )
    parser.add_argument(
        "--download-all",
        action="store_true",
        help="When downloading PDFs, include unselected papers too.",
    )
    parser.add_argument(
        "--max-downloads",
        type=int,
        default=0,
        help="Maximum number of PDFs to download. 0 means no limit.",
    )
    parser.add_argument(
        "--list-conferences",
        action="store_true",
        help="Print the supported conference aliases and exit.",
    )
    return parser


def execute_reader(args: argparse.Namespace) -> int:
    if args.list_conferences:
        for alias, config in sorted(CONFERENCES.items()):
            print(f"{alias}\t{config.name}\t{config.stream_id}")
        return 0

    if not args.year:
        raise ValueError("--year is required unless --list-conferences is used.")

    if not args.skip_ai and not args.interest.strip():
        raise ValueError("--interest is required unless --skip-ai is used.")

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

    download_results = []
    if args.download_pdfs:
        download_results = download_papers(
            results,
            output_dir=Path(args.pdf_dir),
            selected_only=not args.download_all,
            max_papers=args.max_downloads,
        )
        write_json(output_path, results)
        if args.pdf_log_output:
            log_path = Path(args.pdf_log_output)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(json.dumps(download_results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Wrote PDF download log to {log_path}")

    total = len(results)
    kept = sum(1 for item in results if item.get("selected", True))
    print(f"Wrote {total} papers to {output_path}")
    if csv_path:
        print(f"Wrote CSV to {csv_path}")
    if report_path:
        print(f"Wrote report to {report_path}")
    if args.download_pdfs:
        downloaded = sum(1 for row in download_results if row["status"] == "downloaded")
        skipped = sum(1 for row in download_results if row["status"] == "skipped")
        missing_pdf = sum(1 for row in download_results if row["status"] == "missing_pdf")
        failed = sum(1 for row in download_results if row["status"] == "failed")
        print(
            f"PDF download summary: downloaded={downloaded}, skipped={skipped}, missing_pdf={missing_pdf}, failed={failed}"
        )
    if not args.skip_ai:
        print(f"Selected {kept} papers with score >= {args.min_score}")
    return 0
