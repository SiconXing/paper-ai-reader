import json
import ssl
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


DEFAULT_HEADERS = {
    "User-Agent": "paper-ai-reader/0.1 (+https://example.local)",
    "Accept": "application/json",
}


def get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Any:
    final_headers = dict(DEFAULT_HEADERS)
    final_headers["Content-Type"] = "application/json"
    if headers:
        final_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=final_headers,
        method="POST",
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))
