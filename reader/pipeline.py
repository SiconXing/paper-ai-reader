from typing import List

from .ai_filter import score_papers_with_ai
from .fetchers import enrich_with_openalex, fetch_dblp_papers
from .models import Paper
from .sources import CONFERENCES


def run_pipeline(
    conference_aliases: List[str],
    year: int,
    limit_per_conf: int,
    interest: str,
    min_score: int,
    skip_ai: bool,
) -> List[dict]:
    papers: List[Paper] = []
    for alias in conference_aliases:
        key = alias.lower()
        if key not in CONFERENCES:
            raise ValueError(f"Unsupported conference alias: {alias}")
        conference = CONFERENCES[key]
        papers.extend(fetch_dblp_papers(conference, year, limit_per_conf))

    papers = enrich_with_openalex(papers)

    if skip_ai:
        return [paper.to_dict() for paper in papers]

    papers = score_papers_with_ai(papers, interest=interest, min_score=min_score)
    papers.sort(key=lambda item: item.interest_score or 0, reverse=True)
    return [paper.to_dict() for paper in papers]
