from __future__ import annotations
import os
import json
import httpx
from typing import AsyncIterator, Dict, List, Optional, Literal, TypedDict, NotRequired
import asyncio
import time
import random

_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def _headers() -> Dict[str, str]:
    """Build request headers using the current env value.

    Delays API key lookup to call-time so .env can be loaded earlier
    by the application before using this client.
    """
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Export it or put it in .env before calling OpenRouter."
        )
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    # Optional headers recommended by OpenRouter
    # Allow override via env vars, with a sensible default X-Title
    app_title = os.getenv("OPENROUTER_APP_TITLE", "Arcadia AI Chat")
    headers["X-Title"] = app_title
    if ref := os.getenv("OPENROUTER_REFERER"):
        headers["HTTP-Referer"] = ref
    return headers

_RETRIABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_RETRIES = int(os.getenv("OPENROUTER_MAX_RETRIES", "2"))

# Persistent clients to reuse connections and reduce handshake overhead
_sync_client: Optional[httpx.Client] = None
_async_client: Optional[httpx.AsyncClient] = None

def _get_sync_client() -> httpx.Client:
    global _sync_client
    if _sync_client is None:
        _sync_client = httpx.Client(
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _sync_client

def _get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=None, write=10.0, pool=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _async_client

def _backoff_delay(attempt: int, retry_after: Optional[str]) -> float:
    if retry_after and retry_after.isdigit():
        base = float(retry_after)
    else:
        base = float(2 ** attempt)
    jitter = random.uniform(0, base * 0.5)
    return base + jitter

class Chunk(TypedDict):
    kind: Literal["reasoning", "content", "usage"]
    text: str
    usage: NotRequired[dict]

class StreamController:
    """
    A controllable stream that allows stopping generation mid-stream.
    """
    def __init__(self, generator_factory):
        self.generator_factory = generator_factory
        self._cancelled = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    async def __aiter__(self):
        """Iterate over the stream, checking for cancellation."""
        self._task = asyncio.current_task()
        generator = self.generator_factory(cancellation_event=self._cancelled)
        async for chunk in generator:
            if self._cancelled.is_set():
                break
            yield chunk

    def stop(self):
        """Stop the stream immediately."""
        self._cancelled.set()
        if self._task and not self._task.done():
            self._task.cancel()

    @property
    def stopped(self) -> bool:
        """Check if the stream has been stopped."""
        return self._cancelled.is_set()

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

    last_err: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            resp = _get_sync_client().post(_BASE_URL, headers=_headers(), json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in _RETRIABLE_STATUS and attempt < _MAX_RETRIES:
                delay = _backoff_delay(attempt, e.response.headers.get("Retry-After"))
                time.sleep(delay)
                last_err = e
                continue
            raise
        except httpx.HTTPError as e:
            if attempt < _MAX_RETRIES:
                time.sleep(_backoff_delay(attempt, None))
                last_err = e
                continue
            raise
    # Should not reach here, but just in case
    if last_err:
        raise last_err
    raise RuntimeError("OpenRouter request failed without specific error")

# ---------- new single async generator ----------
async def _astream_generator(
    messages: List[dict],
    model: str,
    *,
    max_tokens: int = 32_768,
    thinking: bool = False,
    cancellation_event: Optional[asyncio.Event] = None,
) -> AsyncIterator[Chunk]:
    """
    Internal generator that yields (kind, text) tuples while the model streams.
    kind is one of: "reasoning", "content", "usage".
    """
    payload: Dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
        "include_reasoning": thinking,
    }

    # Retry only around establishing the stream; once streaming begins, we don't retry mid-stream.
    for attempt in range(_MAX_RETRIES + 1):
        try:
            client = _get_async_client()
            async with client.stream(
                "POST", _BASE_URL, headers=_headers(), json=payload
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    # Check for cancellation
                    if cancellation_event and cancellation_event.is_set():
                        break

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
            return
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in _RETRIABLE_STATUS and attempt < _MAX_RETRIES:
                delay = _backoff_delay(attempt, e.response.headers.get("Retry-After"))
                await asyncio.sleep(delay)
                continue
            raise
        except httpx.HTTPError:
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_backoff_delay(attempt, None))
                continue
            raise

def astream(
    messages: List[dict],
    model: str,
    *,
    max_tokens: int = 32_768,
    thinking: bool = False,
) -> StreamController:
    """
    Return a controllable stream that allows stopping generation mid-stream.

    Returns:
        StreamController: A stream object with stop() method to cancel generation.
    """
    return StreamController(lambda cancellation_event=None: _astream_generator(
        messages, model, max_tokens=max_tokens, thinking=thinking, cancellation_event=cancellation_event
    ))

async def consume_and_drop(generator: AsyncIterator[Chunk]) -> None:
    """Consume and drop the rest of a stream."""
    async for _ in generator:
        pass
