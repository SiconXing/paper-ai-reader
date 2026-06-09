from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

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
    workers: int = 1,
) -> Dict[str, int]:
    total = 0
    kept = 0

    csv_writer = CsvWriter(csv_output_path) if export_csv and csv_output_path else None
    with JsonlWriter(output_path) as writer:
        if csv_writer:
            with csv_writer as stream_csv:
                for result in _score_rows(
                    rows=iter_records(input_path),
                    interest=interest,
                    min_score=min_score,
                    workers=workers,
                ):
                    total, kept = _write_result(
                        result=result,
                        writer=writer,
                        csv_writer=stream_csv,
                        total=total,
                        kept=kept,
                    )
        else:
            for result in _score_rows(
                rows=iter_records(input_path),
                interest=interest,
                min_score=min_score,
                workers=workers,
            ):
                total, kept = _write_result(
                    result=result,
                    writer=writer,
                    csv_writer=None,
                    total=total,
                    kept=kept,
                )

    return {"total": total, "kept": kept}


def _score_rows(
    rows: Iterable[Dict[str, object]],
    interest: str,
    min_score: int,
    workers: int,
) -> Iterable[Dict[str, object]]:
    if workers <= 1:
        for row in tqdm(rows, desc="Scoring papers with AI"):
            yield _score_row(row, interest=interest, min_score=min_score)
        return

    with ThreadPoolExecutor(max_workers=workers) as executor:
        yield from tqdm(
            executor.map(
                lambda row: _score_row(row, interest=interest, min_score=min_score),
                rows,
            ),
            desc="Scoring papers with AI",
        )


def _score_row(
    row: Dict[str, object],
    interest: str,
    min_score: int,
) -> Dict[str, object]:
    paper = Paper.from_dict(row)
    scored = score_paper_with_ai(paper, interest=interest, min_score=min_score)
    return scored.to_dict()


def _write_result(
    result: Dict[str, object],
    writer: JsonlWriter,
    csv_writer: Optional[CsvWriter],
    total: int,
    kept: int,
) -> Tuple[int, int]:
    writer.write(result)
    if csv_writer:
        csv_writer.write(result)
    total += 1
    if bool(result.get("selected", False)):
        kept += 1
    return total, kept
