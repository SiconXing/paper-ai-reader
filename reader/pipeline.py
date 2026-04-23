from typing import List
from tqdm import tqdm

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
    
    # 显示会议论文获取进度
    for alias in tqdm(conference_aliases, desc="Fetching papers from conferences"):
        key = alias.lower()
        if key not in CONFERENCES:
            raise ValueError(f"Unsupported conference alias: {alias}")
        conference = CONFERENCES[key]
        papers.extend(fetch_dblp_papers(conference, year, limit_per_conf))

    # 显示 OpenAlex 富集进度
    papers = list(tqdm(
        enrich_with_openalex(papers),
        total=len(papers),
        desc="Enriching papers with OpenAlex"
    ))

    if skip_ai:
        return [paper.to_dict() for paper in papers]

    # 显示 AI 评分进度
    papers = list(tqdm(
        score_papers_with_ai(papers, interest=interest, min_score=min_score),
        total=len(papers),
        desc="Scoring papers with AI"
    ))
    papers.sort(key=lambda item: item.interest_score or 0, reverse=True)
    return [paper.to_dict() for paper in papers]