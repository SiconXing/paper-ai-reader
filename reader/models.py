from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass
class Paper:
    conference: str
    year: int
    title: str
    abstract: str = ""
    dblp_url: str = ""
    doi: str = ""
    openalex_url: str = ""
    paper_url: str = ""
    arxiv_id: str = ""
    arxiv_url: str = ""
    arxiv_pdf_url: str = ""
    pdf_url: str = ""
    interest_score: Optional[int] = None
    recommendation: str = ""
    reason: str = ""
    selected: bool = True

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)
