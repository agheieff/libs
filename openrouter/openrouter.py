import os
import json
import requests
from typing import List, Dict, Iterator, Tuple

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY env var not set")

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

def get_response(history: List[Dict], model: str, max_tokens: int = 4096) -> Tuple[str, Dict]:
    """Blocking call. Returns (assistant_text, usage_dict)."""
    body = {"model": model, "messages": history, "max_tokens": max_tokens}
    resp = requests.post(BASE_URL, headers=_headers(), json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    usage = data.get("usage", {})
    cost = usage.get("total_cost_usd", 0.0)
    text = data["choices"][0]["message"]["content"]
    return text, {
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_cost_usd": cost,
    }

def get_streaming_response(history: List[Dict], model: str, max_tokens: int = 4096) -> Iterator[str]:
    """SSE streaming. Yields delta content; last chunk is JSON with usage."""
    body = {"model": model, "messages": history, "max_tokens": max_tokens, "stream": True}
    with requests.post(BASE_URL, headers=_headers(), json=body, stream=True, timeout=(10, 60)) as r:
        r.raise_for_status()
        for raw in r.iter_lines():
            if raw and raw.startswith(b"data: "):
                chunk = raw[6:].decode()
                if chunk == "[DONE]": break
                data = json.loads(chunk)
                delta = data.get("choices", [{}])[0].get("delta", {})
                if delta.get("content"):
                    yield delta["content"]
                if "usage" in data:  # final chunk
                    yield json.dumps(data["usage"])
