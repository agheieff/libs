# Arcadia Libraries

Lightweight Python libraries for FastAPI apps (UI, auth, integrations) plus utilities. Each subfolder is an installable package intended for local development.

## Packages
- arcadia_ui_core — Core UI building blocks for FastAPI: Jinja2 template mounting, UI endpoints (header/footer/auth/settings/user_menu), ThemeManager, and static mounting helper.
- arcadia_ui_style — Opinionated theme and default templates; ensure_templates scaffolds header/footer, login/signup, settings, and generates arcadia_theme.css; depends on arcadia_ui_core.
- auth — Minimal shared auth (JWT bearer, Account/Profile). FastAPI router (/auth), cookie-based middleware, and a repository abstraction with an in-memory implementation for tests.
- cli_loop — Zero-dep micro CLI loop engine.
- fastapi_sse — Tiny helpers to stream OpenRouter chunks as Server-Sent Events (SSE) lines.
- openrouter — Minimal OpenRouter client with streaming helpers and optional Whisper transcription (uses OPENROUTER_API_KEY / OPENAI_API_KEY).
- telegram_mini — Minimal Telegram bot client with polling, send/edit/delete, inline keyboards, typing indicators, and buffered streaming.
- web_upload — Utilities to save uploads with size caps, unique filenames, and sanitization.
- workspace_fs — Filesystem helpers: safe_join, sanitize_filename, guess_mime, human_size.
- test_app — Minimal FastAPI app exercising ui_core, ui_style, and auth together.

## Local development
- Install any package editable from a parent project:
  uv add -e ../libs/<package_dir>

## Terminology (shared across libs)
- Account: Authentication identity and credentials managed by the auth layer; one Account may be used by multiple agents.
- Profile: In‑app workspace/dataset that belongs to an Account; apps may enable multiple profiles per account.
- Agent: An actor operating the app (human or automated). Use “agent” instead of “user” in app‑level docs/UI.
