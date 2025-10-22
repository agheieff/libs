OpenRouter Python Client (local)

This is a minimal OpenRouter client with:
- `openrouter/` streaming and complete helpers
- `openrouter/whisper.py` for OpenAI Whisper transcription (optional)

It expects the following env vars at call-time:
- `OPENROUTER_API_KEY` for OpenRouter
- `OPENAI_API_KEY` for Whisper

Install locally (editable) from the project using:

```
uv add -e ../libs/openrouter
```

Note: This package is intended for local development and is not published.
