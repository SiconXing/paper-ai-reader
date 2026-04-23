import time
import urllib.parse
from typing import Dict, List

from .http import get_json
from .models import Paper
from .sources import ConferenceConfig


DBLP_API = "https://dblp.org/search/publ/api"
OPENALEX_API = "https://api.openalex.org/works"


def fetch_dblp_papers(conference: ConferenceConfig, year: int, limit: int) -> List[Paper]:
    query = f"streamid:{conference.stream_id}: {year}"
    raw_limit = max(limit * 8, 100)
    payload = get_json(
        DBLP_API,
        params={
            "q": query,
            "h": raw_limit,
            "format": "json",
        },
    )
    hits = (
        payload.get("result", {})
        .get("hits", {})
        .get("hit", [])
    )

    papers: List[Paper] = []
    for hit in hits:
        info = hit.get("info", {})
        title = _cleanup_title(info.get("title", ""))
        venue = str(info.get("venue", ""))
        entry_type = str(info.get("type", ""))
        hit_year = int(info.get("year", year))
        if not title or hit_year != year:
            continue
        if venue not in conference.allowed_venues:
            continue
        if entry_type != "Conference and Workshop Papers" and entry_type != "Journal Articles":
            continue
        if _looks_like_proceedings(title):
            continue
        papers.append(
            Paper(
                conference=conference.name,
                year=hit_year,
                title=title,
                dblp_url=info.get("url", ""),
                doi=info.get("doi", ""),
            )
        )
    return _deduplicate(papers)[:limit]


def enrich_with_openalex(papers: List[Paper]) -> List[Paper]:
    enriched: List[Paper] = []
    for paper in papers:
        enriched.append(_enrich_single_paper(paper))
        time.sleep(0.1)
    return enriched


def _enrich_single_paper(paper: Paper) -> Paper:
    params = {
        "search": paper.title,
        "filter": f"publication_year:{paper.year}",
        "per-page": 5,
    }
    payload = get_json(OPENALEX_API, params=params)
    candidates = payload.get("results", [])
    best = _select_best_match(candidates, paper.title)
    if not best:
        return paper

    abstract_index = best.get("abstract_inverted_index") or {}
    paper.abstract = _reconstruct_abstract(abstract_index)
    paper.openalex_url = best.get("id", "")
    if not paper.doi:
        paper.doi = best.get("doi", "") or ""
    return paper


def _select_best_match(candidates: List[Dict[str, object]], title: str) -> Dict[str, object]:
    normalized_title = _normalize(title)
    for candidate in candidates:
        candidate_title = _normalize(candidate.get("title", ""))
        if candidate_title == normalized_title:
            return candidate
    for candidate in candidates:
        candidate_title = _normalize(candidate.get("title", ""))
        if normalized_title and normalized_title in candidate_title:
            return candidate
    return {}


def _reconstruct_abstract(abstract_index: Dict[str, List[int]]) -> str:
    if not abstract_index:
        return ""
    positions: Dict[int, str] = {}
    for token, indexes in abstract_index.items():
        for index in indexes:
            positions[index] = token
    return " ".join(token for _, token in sorted(positions.items()))


def _cleanup_title(title: str) -> str:
    return " ".join(str(title).replace("\n", " ").split()).strip(". ")


def _looks_like_proceedings(title: str) -> bool:
    lowered = title.lower()
    markers = (
        "conference on",
        "proceedings of",
        "workshops",
        "doctorial consortium",
        "tutorial",
    )
    return any(marker in lowered for marker in markers)


def _normalize(text: str) -> str:
    cleaned = _cleanup_title(text).lower()
    safe = urllib.parse.quote(cleaned, safe="")
    return urllib.parse.unquote(safe)


def _deduplicate(papers: List[Paper]) -> List[Paper]:
    seen = set()
    unique: List[Paper] = []
    for paper in papers:
        key = (paper.conference, paper.year, paper.title.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(paper)
    return unique
