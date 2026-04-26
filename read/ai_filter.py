import json
import os

from common.http import post_json
from common.models import Paper


def score_paper_with_ai(paper: Paper, interest: str, min_score: int) -> Paper:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for AI filtering.")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    result = _score_single_paper(
        base_url=base_url,
        api_key=api_key,
        model=model,
        interest=interest,
        paper=paper,
    )
    paper.interest_score = int(result.get("score", 0))
    paper.recommendation = str(result.get("recommendation", "skip"))
    paper.reason = str(result.get("reason", ""))
    paper.selected = paper.interest_score >= min_score
    return paper


def _score_single_paper(
    base_url: str,
    api_key: str,
    model: str,
    interest: str,
    paper: Paper,
) -> dict:
    system_prompt = (
        "You are a research assistant. "
        "Given the user's interests and one paper's metadata, "
        "return strict JSON with keys: score, recommendation, reason. "
        "score must be an integer from 0 to 100. "
        "recommendation must be one of: strong_yes, yes, maybe, skip. "
        "reason must be under 80 Chinese characters."
    )
    user_prompt = (
        f"用户兴趣:\n{interest}\n\n"
        f"论文标题:\n{paper.title}\n\n"
        f"论文摘要:\n{paper.abstract or '摘要缺失'}\n\n"
        "请只输出 JSON。"
    )
    response = post_json(
        f"{base_url}/chat/completions",
        payload={
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )
    content = response["choices"][0]["message"]["content"]
    return json.loads(content)
