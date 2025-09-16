from __future__ import annotations
import os
import json
import httpx
from typing import AsyncIterator, Dict, List, Optional, Literal, TypedDict, NotRequired

_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not _API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY env var not set")

_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
_HEADERS = {
    "Authorization": f"Bearer {_API_KEY}",
    "Content-Type": "application/json",
}

class Chunk(TypedDict):
    kind: Literal["reasoning", "content", "usage"]
    text: str
    usage: NotRequired[dict]

# ---------- sync helpers (keep old surface if you want) ----------
def complete(
    messages: List[dict],
    model: str,
    *,
    max_tokens: int = 4096,
    reasoning: Optional[Dict] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
) -> dict:
    payload: Dict = {
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

    resp = httpx.post(_BASE_URL, headers=_HEADERS, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

# ---------- new single async generator ----------
async def astream(
    messages: List[dict],
    model: str,
    *,
    max_tokens: int = 32_768,
    thinking: bool = False,
) -> AsyncIterator[Chunk]:
    """
    Yield (kind, text) tuples while the model streams.
    kind is one of: "reasoning", "content", "usage".
    """
    payload: Dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
        "include_reasoning": thinking,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST", _BASE_URL, headers=_HEADERS, json=payload
        ) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                chunk = line[6:]
                if chunk == "[DONE]":
                    break
                data = json.loads(chunk)

                # usage block (sent once at the end)
                if "usage" in data:
                    yield {"kind": "usage", "text": "", "usage": data["usage"]}
                    continue

                delta = data["choices"][0].get("delta", {})

                # reasoning text
                reason = (delta.get("reasoning") or "") + "".join(
                    rd["text"]
                    for rd in delta.get("reasoning_details", [])
                    if rd.get("type") == "reasoning.text"
                )
                if reason:
                    yield {"kind": "reasoning", "text": reason}

                # response text
                if content := delta.get("content"):
                    yield {"kind": "content", "text": content}

async def consume_and_drop(generator: AsyncIterator[Chunk]) -> None:
    """Consume and drop the rest of a stream."""
    async for _ in generator:
        pass
