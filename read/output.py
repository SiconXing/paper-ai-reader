from collections import Counter
from pathlib import Path
from typing import Dict, List

from common.storage import iter_records


def write_report(
    output_path: Path,
    input_path: Path,
    interest: str,
    min_score: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_report(input_path, interest=interest, min_score=min_score),
        encoding="utf-8",
    )


def build_report(input_path: Path, interest: str, min_score: int) -> str:
    total = 0
    selected_total = 0
    conferences = Counter()
    top_items: List[Dict[str, object]] = []
    recommended: List[Dict[str, object]] = []

    for item in iter_records(input_path):
        total += 1
        conference = str(item.get("conference", ""))
        conferences[conference] += 1

        _append_top_scored(top_items, item, limit=10)

        if item.get("selected", True):
            selected_total += 1
            _append_top_scored(recommended, item, limit=20)

    lines = [
        "# Paper AI Reader Report",
        "",
        "## Summary",
        f"- Total papers: {total}",
        f"- Conferences covered: {len(conferences)}",
        f"- Selected papers: {selected_total}",
        f"- Min score threshold: {min_score}",
        "- AI filtering: enabled",
    ]

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

    if top_items:
        lines.extend(["", "## Top Papers"])
        for index, item in enumerate(top_items, start=1):
            score = item.get("interest_score")
            score_text = "N/A" if score is None else str(score)
            reason = str(item.get("reason", "")).strip()
            lines.append(
                f"{index}. [{item.get('conference')}] {item.get('title')} (score: {score_text})"
            )
            if reason:
                lines.append(f"   - Reason: {reason}")

    if recommended:
        lines.extend(["", "## Recommended Reading"])
        for index, item in enumerate(recommended, start=1):
            recommendation = item.get("recommendation") or "unknown"
            lines.append(
                f"{index}. [{item.get('conference')}] {item.get('title')} [{recommendation}]"
            )

    return "\n".join(lines) + "\n"


def _append_top_scored(rows: List[Dict[str, object]], item: Dict[str, object], limit: int) -> None:
    rows.append(item)
    rows.sort(key=lambda row: int(row.get("interest_score") or 0), reverse=True)
    del rows[limit:]
