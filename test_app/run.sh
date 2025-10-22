#!/usr/bin/env bash
PORT=9000; [[ "$1" =~ ^--port=([0-9]+)$ ]] && PORT="${BASH_REMATCH[1]}"
uv sync && uv run uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
