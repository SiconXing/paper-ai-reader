import argparse
import json
from pathlib import Path

from load.downloader import download_papers

from common.storage import iter_records

from .output import write_report
from .pipeline import run_read_pipeline


def add_read_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--input",
        type=str,
        default="data/fetched_papers.jsonl",
        help="Path to the fetched JSON or JSONL file.",
    )
    parser.add_argument(
        "--interest",
        type=str,
        required=True,
        help="Your research interests, used for AI filtering.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=70,
        help="Minimum AI interest score to keep a paper.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/selected_papers.jsonl",
        help="Path to the output JSONL file.",
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
        help="Optional CSV output path. Defaults to the JSONL output path with .csv suffix.",
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
        help="Optional report path. Defaults to the JSONL output path with .md suffix.",
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
    return parser


def execute_read(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)

    csv_path = None
    if args.export_csv:
        csv_path = Path(args.csv_output) if args.csv_output else output_path.with_suffix(".csv")

    stats = run_read_pipeline(
        input_path=input_path,
        output_path=output_path,
        interest=args.interest,
        min_score=args.min_score,
        export_csv=args.export_csv,
        csv_output_path=csv_path,
    )

    report_path = None
    if args.generate_report:
        report_path = (
            Path(args.report_output) if args.report_output else output_path.with_suffix(".md")
        )
        write_report(
            report_path,
            output_path,
            interest=args.interest,
            min_score=args.min_score,
        )

    download_results = []
    if args.download_pdfs:
        download_results = download_papers(
            iter_records(output_path),
            output_dir=Path(args.pdf_dir),
            selected_only=not args.download_all,
            max_papers=args.max_downloads,
        )
        if args.pdf_log_output:
            log_path = Path(args.pdf_log_output)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(
                json.dumps(download_results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Wrote PDF download log to {log_path}")

    print(f"Wrote {stats['total']} papers to {output_path}")
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
    print(f"Selected {stats['kept']} papers with score >= {args.min_score}")
    return 0
