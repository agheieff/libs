from __future__ import annotations
import os
import json
import requests
from typing import Any, Dict, Iterator, List, Optional

_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not _API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY env var not set")

_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
_HEADERS = {
    "Authorization": f"Bearer {_API_KEY}",
    "Content-Type": "application/json",
}


def complete(
    messages: List[dict],
    model: str,
    *,
    max_tokens: int = 4096,
    reasoning: Optional[Dict[str, Any]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
) -> dict:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if reasoning is not None:
        payload["reasoning"] = reasoning
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p

    resp = requests.post(_BASE_URL, headers=_HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def stream(
    messages: List[dict],
    model: str,
    *,
    max_tokens: int = 4096,
    reasoning: Optional[Dict[str, Any]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
) -> Iterator[dict]:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if reasoning is not None:
        payload["reasoning"] = reasoning
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p

    with requests.post(
        _BASE_URL, headers=_HEADERS, json=payload, stream=True, timeout=(10, 60)
    ) as r:
        r.raise_for_status()
        for raw in r.iter_lines():
            if not raw or not raw.startswith(b"data: "):
                continue
            chunk = raw[6:].decode()
            if chunk == "[DONE]":
                break
            yield json.loads(chunk)
