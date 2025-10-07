from __future__ import annotations
import json
from typing import AsyncIterator, Dict


async def sse_from_openrouter(stream: AsyncIterator[Dict]) -> AsyncIterator[str]:
    """Yield JSON strings suitable for SSE 'data: ...' lines from OpenRouter stream chunks.

    Emits {"delta": text} per content chunk, and a final {"end": true}.
    Errors are wrapped into {"error": msg} followed by {"end": true}.
    """
    try:
        async for ch in stream:
            kind = ch.get("kind")
            if kind == "content":
                txt = ch.get("text") or ""
                if txt:
                    yield json.dumps({"delta": txt})
            elif kind == "usage":
                # pass through as-is for clients that care
                yield json.dumps({"usage": ch.get("usage")})
        yield json.dumps({"end": True})
    except Exception as e:
        yield json.dumps({"error": str(e)})
        yield json.dumps({"end": True})
