import csv
from collections import Counter
from pathlib import Path
from typing import Dict, List


CSV_FIELDS = [
    "conference",
    "year",
    "title",
    "abstract",
    "dblp_url",
    "doi",
    "openalex_url",
    "interest_score",
    "recommendation",
    "reason",
    "selected",
]


def write_json(output_path: Path, results: List[Dict[str, object]]) -> None:
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(output_path: Path, results: List[Dict[str, object]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_report(
    output_path: Path,
    results: List[Dict[str, object]],
    interest: str,
    skip_ai: bool,
    min_score: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_report(results, interest=interest, skip_ai=skip_ai, min_score=min_score),
        encoding="utf-8",
    )


def build_report(
    results: List[Dict[str, object]],
    interest: str,
    skip_ai: bool,
    min_score: int,
) -> str:
    total = len(results)
    selected = [item for item in results if item.get("selected", True)]
    conferences = Counter(str(item.get("conference", "")) for item in results)

    lines = [
        "# Paper AI Reader Report",
        "",
        "## Summary",
        f"- Total papers: {total}",
        f"- Conferences covered: {len(conferences)}",
    ]

    if skip_ai:
        lines.append("- AI filtering: disabled")
    else:
        lines.extend(
            [
                f"- Selected papers: {len(selected)}",
                f"- Min score threshold: {min_score}",
                "- AI filtering: enabled",
            ]
        )

    if interest.strip():
        lines.extend(
            [
                "",
                "## Interest Profile",
                interest.strip(),
            ]
        )

    lines.extend(["", "## Conference Breakdown"])
    for conference, count in sorted(conferences.items()):
        lines.append(f"- {conference}: {count}")

    if results:
        lines.extend(["", "## Top Papers"])
        top_items = results[: min(10, len(results))]
        for index, item in enumerate(top_items, start=1):
            score = item.get("interest_score")
            score_text = "N/A" if score is None else str(score)
            reason = str(item.get("reason", "")).strip()
            lines.append(
                f"{index}. [{item.get('conference')}] {item.get('title')} (score: {score_text})"
            )
            if reason:
                lines.append(f"   - Reason: {reason}")

    if not skip_ai and selected:
        lines.extend(["", "## Recommended Reading"])
        for index, item in enumerate(selected[: min(20, len(selected))], start=1):
            recommendation = item.get("recommendation") or "unknown"
            lines.append(
                f"{index}. [{item.get('conference')}] {item.get('title')} [{recommendation}]"
            )

    return "\n".join(lines) + "\n"
