import csv
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, TextIO


CSV_FIELDS = [
    "conference",
    "year",
    "title",
    "abstract",
    "dblp_url",
    "doi",
    "openalex_url",
    "paper_url",
    "arxiv_id",
    "arxiv_url",
    "arxiv_pdf_url",
    "pdf_url",
    "interest_score",
    "recommendation",
    "reason",
    "selected",
]


class JsonlWriter:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self._file: TextIO

    def __enter__(self) -> "JsonlWriter":
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.output_path.open("w", encoding="utf-8")
        return self

    def write(self, row: Dict[str, object]) -> None:
        self._file.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._file.flush()

    def __exit__(self, exc_type, exc, tb) -> None:
        self._file.close()


class CsvWriter:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self._file: TextIO
        self._writer: csv.DictWriter

    def __enter__(self) -> "CsvWriter":
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.output_path.open("w", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_FIELDS, extrasaction="ignore")
        self._writer.writeheader()
        return self

    def write(self, row: Dict[str, object]) -> None:
        self._writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
        self._file.flush()

    def __exit__(self, exc_type, exc, tb) -> None:
        self._file.close()


def iter_records(input_path: Path) -> Iterator[Dict[str, object]]:
    if input_path.suffix.lower() == ".jsonl":
        with input_path.open("r", encoding="utf-8") as file:
            for line in file:
                text = line.strip()
                if text:
                    yield json.loads(text)
        return

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Unsupported JSON payload in {input_path}: expected a list.")
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError(f"Unsupported JSON row in {input_path}: expected an object.")
        yield row


def read_records(input_path: Path) -> List[Dict[str, object]]:
    return list(iter_records(input_path))


def write_json(output_path: Path, results: List[Dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(output_path: Path, results: Iterable[Dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
