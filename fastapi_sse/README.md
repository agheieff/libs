# fastapi-sse-mini

Tiny helpers to turn OpenRouter streaming chunks into Server-Sent Events (SSE) lines.

- `sse_from_openrouter(stream)` yields JSON strings suitable for `data: ...` lines and emits a final `{ "end": true }`.

Example (conceptual):
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from fastapi_sse import sse_from_openrouter

@router.get('/stream')
def stream():
    async def gen():
        async for line in sse_from_openrouter(openrouter_stream()):
            yield f"data: {line}\n\n"
    return StreamingResponse(gen(), media_type='text/event-stream')
```

Install (editable):
uv add -e ../libs/fastapi_sse
