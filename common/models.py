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

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "Paper":
        return cls(
            conference=str(payload.get("conference", "")),
            year=int(payload.get("year", 0)),
            title=str(payload.get("title", "")),
            abstract=str(payload.get("abstract", "")),
            dblp_url=str(payload.get("dblp_url", "")),
            doi=str(payload.get("doi", "")),
            openalex_url=str(payload.get("openalex_url", "")),
            paper_url=str(payload.get("paper_url", "")),
            arxiv_id=str(payload.get("arxiv_id", "")),
            arxiv_url=str(payload.get("arxiv_url", "")),
            arxiv_pdf_url=str(payload.get("arxiv_pdf_url", "")),
            pdf_url=str(payload.get("pdf_url", "")),
            interest_score=_optional_int(payload.get("interest_score")),
            recommendation=str(payload.get("recommendation", "")),
            reason=str(payload.get("reason", "")),
            selected=bool(payload.get("selected", True)),
        )


def _optional_int(value: object) -> Optional[int]:
    if value in (None, ""):
        return None
    return int(value)
