import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from tqdm import tqdm

from reader.fetchers import find_arxiv_match_by_title
from reader.http import download_file


def load_papers_from_json(input_path: Path) -> List[Dict[str, object]]:
    return json.loads(input_path.read_text(encoding="utf-8"))


def download_papers(
    papers: Iterable[Dict[str, object]],
    output_dir: Path,
    selected_only: bool = True,
    max_papers: int = 0,
    overwrite: bool = False,
) -> List[Dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 转换为列表以便计算总数
    papers_list = list(papers)
    # 过滤出需要处理的论文
    filtered_papers = [p for p in papers_list if not selected_only or bool(p.get("selected", False))]
    if max_papers > 0:
        filtered_papers = filtered_papers[:max_papers]

    results: List[Dict[str, object]] = []
    downloaded = 0
    
    # 显示下载进度
    for paper in tqdm(filtered_papers, desc="Downloading papers"):
        _hydrate_missing_download_sources(paper)
        sources = _build_download_sources(paper)
        filename = _build_filename(paper)
        target_path = output_dir / filename

        if not sources:
            results.append(_result_row(paper, target_path, "missing_pdf", "no downloadable source"))
            continue
        if target_path.exists() and not overwrite:
            results.append(_result_row(paper, target_path, "skipped", "already exists"))
            downloaded += 1
            continue

        last_error = ""
        source_name = ""
        source_url = ""
        for source_name, source_url in sources:
            try:
                download_file(source_url, target_path)
                results.append(_result_row(paper, target_path, "downloaded", f"{source_name}: ok", source_url))
                downloaded += 1
                break
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                last_error = f"{source_name}: {exc}"
        else:
            results.append(_result_row(paper, target_path, "failed", last_error or "download failed", source_url))
    return results


def _build_filename(paper: Dict[str, object]) -> str:
    conference = _slug(str(paper.get("conference", "paper")))
    year = str(paper.get("year", "unknown"))
    title = _slug(str(paper.get("title", "untitled")))
    return f"{conference}_{year}_{title[:120]}.pdf"


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned or "paper"


def _result_row(
    paper: Dict[str, object],
    target_path: Path,
    status: str,
    message: str,
    source_url: str = "",
) -> Dict[str, object]:
    return {
        "conference": paper.get("conference", ""),
        "year": paper.get("year", ""),
        "title": paper.get("title", ""),
        "arxiv_pdf_url": paper.get("arxiv_pdf_url", ""),
        "pdf_url": paper.get("pdf_url", ""),
        "source_url": source_url,
        "status": status,
        "message": message,
        "path": str(target_path),
    }


def _build_download_sources(paper: Dict[str, object]) -> List[Tuple[str, str]]:
    candidates = [
        ("arxiv", str(paper.get("arxiv_pdf_url", "")).strip()),
        ("pdf_url", str(paper.get("pdf_url", "")).strip()),
        ("paper_url_as_pdf", _paper_url_to_pdf(str(paper.get("paper_url", "")).strip())),
    ]
    sources: List[Tuple[str, str]] = []
    seen = set()
    for source_name, source_url in candidates:
        if not source_url or source_url in seen:
            continue
        seen.add(source_url)
        sources.append((source_name, source_url))
    return sources


def _hydrate_missing_download_sources(paper: Dict[str, object]) -> None:
    if _build_download_sources(paper):
        return

    title = str(paper.get("title", "")).strip()
    raw_year = paper.get("year")
    try:
        year_value = int(raw_year)
    except (TypeError, ValueError):
        year_value = 0
    if not title or not year_value:
        return

    arxiv_match = find_arxiv_match_by_title(title, year_value)
    if not arxiv_match:
        return

    paper["arxiv_id"] = arxiv_match["arxiv_id"]
    paper["arxiv_url"] = arxiv_match["arxiv_url"]
    paper["arxiv_pdf_url"] = arxiv_match["arxiv_pdf_url"]
    if not str(paper.get("pdf_url", "")).strip():
        paper["pdf_url"] = arxiv_match["arxiv_pdf_url"]


def _paper_url_to_pdf(url: str) -> str:
    if not url:
        return ""
    lowered = url.lower()
    if "arxiv.org/abs/" in lowered:
        return url.replace("/abs/", "/pdf/") + ".pdf"
    if lowered.endswith(".pdf"):
        return url
    return ""