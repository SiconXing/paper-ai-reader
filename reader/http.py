import json
import ssl
import socket
import time
import urllib.parse
import urllib.request
from http.client import IncompleteRead
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError


DEFAULT_HEADERS = {
    "User-Agent": "paper-ai-reader/0.1 (+https://example.local)",
    "Accept": "application/json",
}


def _urlopen_with_retries(request: urllib.request.Request, context: ssl.SSLContext, timeout: int) -> urllib.request.addinfourl:
    max_attempts = 4
    delay = 2.0

    for attempt in range(1, max_attempts + 1):
        try:
            return urllib.request.urlopen(request, context=context, timeout=timeout)
        except HTTPError as exc:
            if exc.code in {429, 500, 502, 503, 504} and attempt < max_attempts:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (URLError, socket.timeout, ssl.SSLError, IncompleteRead) as exc:
            if attempt < max_attempts:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    context = ssl.create_default_context()
    with _urlopen_with_retries(request, context=context, timeout=120) as response:
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
    with _urlopen_with_retries(request, context=context, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, output_path: Path, headers: Optional[Dict[str, str]] = None) -> None:
    final_headers = dict(DEFAULT_HEADERS)
    if headers:
        final_headers.update(headers)
    request = urllib.request.Request(url, headers=final_headers)
    context = ssl.create_default_context()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with _urlopen_with_retries(request, context=context, timeout=180) as response:
        with output_path.open("wb") as file:
            file.write(response.read())
