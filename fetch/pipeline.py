from tqdm import tqdm

from common.storage import JsonlWriter

from .fetchers import enrich_with_openalex, fetch_dblp_papers
from .sources import CONFERENCES


def run_fetch_pipeline(
    conference_aliases,
    year: int,
    limit_per_conf: int,
    output_path,
) -> int:
    written = 0
    with JsonlWriter(output_path) as writer:
        for alias in tqdm(conference_aliases, desc="Fetching papers from conferences"):
            key = alias.lower()
            if key not in CONFERENCES:
                raise ValueError(f"Unsupported conference alias: {alias}")
            conference = CONFERENCES[key]
            papers = fetch_dblp_papers(conference, year, limit_per_conf)
            for paper in tqdm(
                enrich_with_openalex(papers),
                total=len(papers),
                desc=f"Enriching papers with OpenAlex ({conference.name})",
                leave=False,
            ):
                writer.write(paper.to_dict())
                written += 1
    return written
