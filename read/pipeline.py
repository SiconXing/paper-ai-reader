from pathlib import Path
from typing import Dict, Optional, Tuple

from tqdm import tqdm

from common.models import Paper
from common.storage import CsvWriter, JsonlWriter, iter_records

from .ai_filter import score_paper_with_ai


def run_read_pipeline(
    input_path: Path,
    output_path: Path,
    interest: str,
    min_score: int,
    export_csv: bool = False,
    csv_output_path: Optional[Path] = None,
) -> Dict[str, int]:
    total = 0
    kept = 0

    csv_writer = CsvWriter(csv_output_path) if export_csv and csv_output_path else None
    with JsonlWriter(output_path) as writer:
        if csv_writer:
            with csv_writer as stream_csv:
                for row in tqdm(iter_records(input_path), desc="Scoring papers with AI"):
                    total, kept = _process_row(
                        row=row,
                        writer=writer,
                        csv_writer=stream_csv,
                        interest=interest,
                        min_score=min_score,
                        total=total,
                        kept=kept,
                    )
        else:
            for row in tqdm(iter_records(input_path), desc="Scoring papers with AI"):
                total, kept = _process_row(
                    row=row,
                    writer=writer,
                    csv_writer=None,
                    interest=interest,
                    min_score=min_score,
                    total=total,
                    kept=kept,
                )

    return {"total": total, "kept": kept}


def _process_row(
    row: Dict[str, object],
    writer: JsonlWriter,
    csv_writer: Optional[CsvWriter],
    interest: str,
    min_score: int,
    total: int,
    kept: int,
) -> Tuple[int, int]:
    paper = Paper.from_dict(row)
    scored = score_paper_with_ai(paper, interest=interest, min_score=min_score)
    result = scored.to_dict()
    writer.write(result)
    if csv_writer:
        csv_writer.write(result)
    total += 1
    if scored.selected:
        kept += 1
    return total, kept
