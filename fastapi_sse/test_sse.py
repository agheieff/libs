from __future__ import annotations
import asyncio
from fastapi_sse import sse_from_openrouter


async def _fake_stream():
    yield {"kind": "content", "text": "Hello"}
    yield {"kind": "content", "text": " World"}


async def test_sse_basic():
    chunks = []
    async for line in sse_from_openrouter(_fake_stream()):
        chunks.append(line)
    assert any("\"delta\": \"Hello\"" in x for x in chunks)
    assert any('"end": true' in x for x in chunks)


if __name__ == "__main__":
    asyncio.run(test_sse_basic())
    print("fastapi_sse tests passed")
