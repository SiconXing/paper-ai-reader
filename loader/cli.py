import argparse
import json
from pathlib import Path

from .downloader import download_papers, load_papers_from_json


def add_loader_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--input", required=True, help="Path to the JSON file produced by the main pipeline.")
    parser.add_argument(
        "--output-dir",
        default="downloads",
        help="Directory where PDFs will be stored.",
    )
    parser.add_argument(
        "--all-papers",
        action="store_true",
        help="Download all papers in the JSON file, not only selected ones.",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=0,
        help="Maximum number of papers to download. 0 means no limit.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PDFs.",
    )
    parser.add_argument(
        "--log-output",
        default="",
        help="Optional JSON log path for download results.",
    )
    return parser


def execute_loader(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    papers = load_papers_from_json(input_path)
    results = download_papers(
        papers,
        output_dir=output_dir,
        selected_only=not args.all_papers,
        max_papers=args.max_papers,
        overwrite=args.overwrite,
    )

    downloaded = sum(1 for row in results if row["status"] == "downloaded")
    skipped = sum(1 for row in results if row["status"] == "skipped")
    missing_pdf = sum(1 for row in results if row["status"] == "missing_pdf")
    failed = sum(1 for row in results if row["status"] == "failed")

    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Missing PDF: {missing_pdf}")
    print(f"Failed: {failed}")

    if args.log_output:
        log_path = Path(args.log_output)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote log to {log_path}")
    return 0
