import arxiv
from difflib import SequenceMatcher
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
        try:
            enriched.append(_enrich_single_paper(paper))
        except Exception as exc:
            print(f"Warning: OpenAlex enrichment failed for '{paper.title[:80]}': {exc}")
            enriched.append(paper)
        time.sleep(0.5)
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
    if best:
        abstract_index = best.get("abstract_inverted_index") or {}
        paper.abstract = _reconstruct_abstract(abstract_index)
        paper.openalex_url = best.get("id", "")
        paper.paper_url = _extract_paper_url(best)
        paper.arxiv_id = _extract_arxiv_id(best)
        paper.arxiv_url = _build_arxiv_abs_url(paper.arxiv_id)
        paper.arxiv_pdf_url = _build_arxiv_pdf_url(paper.arxiv_id)
        paper.pdf_url = _extract_pdf_url(best)
        if not paper.doi:
            paper.doi = best.get("doi", "") or ""

    if not paper.arxiv_pdf_url and not paper.pdf_url:
        arxiv_match = find_arxiv_match_by_title(paper.title, paper.year)
        if arxiv_match:
            paper.arxiv_id = arxiv_match["arxiv_id"]
            paper.arxiv_url = arxiv_match["arxiv_url"]
            paper.arxiv_pdf_url = arxiv_match["arxiv_pdf_url"]
            paper.pdf_url = arxiv_match["arxiv_pdf_url"]
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


def _extract_paper_url(candidate: Dict[str, object]) -> str:
    primary_location = candidate.get("primary_location") or {}
    if isinstance(primary_location, dict):
        landing_page_url = primary_location.get("landing_page_url", "")
        if landing_page_url:
            return str(landing_page_url)

    best_oa_location = candidate.get("best_oa_location") or {}
    if isinstance(best_oa_location, dict):
        landing_page_url = best_oa_location.get("landing_page_url", "")
        if landing_page_url:
            return str(landing_page_url)
    return ""


def _extract_pdf_url(candidate: Dict[str, object]) -> str:
    primary_location = candidate.get("primary_location") or {}
    if isinstance(primary_location, dict):
        pdf_url = primary_location.get("pdf_url", "")
        if pdf_url:
            pdf_url_str = str(pdf_url)
            if _is_arxiv_url(pdf_url_str):
                arxiv_id = _normalize_arxiv_id(pdf_url_str)
                if arxiv_id:
                    return _build_arxiv_pdf_url(arxiv_id)
            else:
                return pdf_url_str

    best_oa_location = candidate.get("best_oa_location") or {}
    if isinstance(best_oa_location, dict):
        pdf_url = best_oa_location.get("pdf_url", "")
        if pdf_url:
            pdf_url_str = str(pdf_url)
            if _is_arxiv_url(pdf_url_str):
                arxiv_id = _normalize_arxiv_id(pdf_url_str)
                if arxiv_id:
                    return _build_arxiv_pdf_url(arxiv_id)
            else:
                return pdf_url_str

    locations = candidate.get("locations") or []
    for location in locations:
        if not isinstance(location, dict):
            continue
        pdf_url = location.get("pdf_url", "")
        if pdf_url:
            pdf_url_str = str(pdf_url)
            if _is_arxiv_url(pdf_url_str):
                arxiv_id = _normalize_arxiv_id(pdf_url_str)
                if arxiv_id:
                    return _build_arxiv_pdf_url(arxiv_id)
            else:
                return pdf_url_str
    return ""


def _extract_arxiv_id(candidate: Dict[str, object]) -> str:
    ids = candidate.get("ids") or {}
    if isinstance(ids, dict):
        arxiv_value = str(ids.get("arxiv", "")).strip()
        arxiv_id = _normalize_arxiv_id(arxiv_value)
        if arxiv_id:
            return arxiv_id

    locations = candidate.get("locations") or []
    for location in locations:
        if not isinstance(location, dict):
            continue
        for key in ("landing_page_url", "pdf_url"):
            url = str(location.get(key, "")).strip()
            arxiv_id = _normalize_arxiv_id(url)
            if arxiv_id:
                return arxiv_id

    for key in ("paper_url", "openalex_url", "doi"):
        value = str(candidate.get(key, "")).strip()
        arxiv_id = _normalize_arxiv_id(value)
        if arxiv_id:
            return arxiv_id
    return ""


def _normalize_arxiv_id(value: str) -> str:
    if not value:
        return ""
    normalized = value.strip()
    normalized = normalized.replace("http://", "https://")
    prefixes = (
        "https://arxiv.org/abs/",
        "https://arxiv.org/pdf/",
        "https://www.arxiv.org/abs/",
        "https://www.arxiv.org/pdf/",
        "arxiv:",
        "ArXiv:",
    )
    matched = False
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            matched = True
            break
    if not matched:
        return ""
    normalized = normalized.removesuffix(".pdf")
    normalized = normalized.strip("/")
    return normalized if normalized else ""


def _build_arxiv_abs_url(arxiv_id: str) -> str:
    if not arxiv_id:
        return ""
    return f"https://arxiv.org/abs/{arxiv_id}"


def _build_arxiv_pdf_url(arxiv_id: str) -> str:
    if not arxiv_id:
        return ""
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def _is_arxiv_url(url: str) -> bool:
    lowered = url.lower()
    return "arxiv.org/abs/" in lowered or "arxiv.org/pdf/" in lowered


def _search_arxiv_for_pdf(title: str, year: int) -> str:
    match = find_arxiv_match_by_title(title, year)
    if not match:
        return ""
    return str(match["arxiv_pdf_url"])


def find_arxiv_match_by_title(title: str, year: int) -> Dict[str, str]:
    client = arxiv.Client()
    queries = [
        f'ti:"{title}"',
        title,
    ]
    best_match: Dict[str, str] = {}
    best_score = 0.0
    seen_ids = set()

    try:
        for query in queries:
            search = arxiv.Search(
                query=query,
                max_results=10,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            for result in client.results(search):
                arxiv_id = str(getattr(result, "get_short_id", lambda: "")()).strip()
                if not arxiv_id:
                    arxiv_id = _normalize_arxiv_id(getattr(result, "entry_id", ""))
                if arxiv_id in seen_ids:
                    continue
                seen_ids.add(arxiv_id)

                score = _score_arxiv_candidate(title, year, result.title, result.published.year)
                if score > best_score:
                    best_score = score
                    best_match = {
                        "arxiv_id": arxiv_id,
                        "arxiv_url": _build_arxiv_abs_url(arxiv_id),
                        "arxiv_pdf_url": _build_arxiv_pdf_url(arxiv_id),
                    }
    except Exception as exc:
        print(f"Warning: arXiv search failed for '{title[:50]}': {exc}")
        return {}

    if best_score < 0.88:
        return {}
    return best_match


def _score_arxiv_candidate(query_title: str, query_year: int, candidate_title: str, candidate_year: int) -> float:
    normalized_query = _normalize_for_match(query_title)
    normalized_candidate = _normalize_for_match(candidate_title)
    similarity = SequenceMatcher(None, normalized_query, normalized_candidate).ratio()

    if normalized_query == normalized_candidate:
        similarity += 0.2
    elif normalized_query in normalized_candidate or normalized_candidate in normalized_query:
        similarity += 0.1

    year_gap = abs(query_year - candidate_year)
    if year_gap == 0:
        similarity += 0.03
    elif year_gap == 1:
        similarity += 0.02
    elif year_gap == 2:
        similarity += 0.01

    return similarity


def _normalize_for_match(text: str) -> str:
    lowered = _cleanup_title(text).lower()
    alnum_only = "".join(ch if ch.isalnum() else " " for ch in lowered)
    return " ".join(alnum_only.split())
