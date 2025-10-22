from __future__ import annotations

from pathlib import Path
import sys

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import libs locally (monorepo path fallback)
base = Path(__file__).resolve().parents[1]
core_pkg = base / "arcadia_ui_core"
style_pkg = base / "arcadia_ui_style"
auth_pkg = base / "auth"
for p in (core_pkg, style_pkg, auth_pkg):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from arcadia_ui_core import router as ui_router, mount_templates, mount_ui_static  # type: ignore
from arcadia_ui_style import ensure_templates  # type: ignore
from arcadia_auth import create_auth_router, AuthSettings, mount_cookie_agent_middleware  # type: ignore
from arcadia_auth.repo import InMemoryRepo  # type: ignore


app = FastAPI(title="Arcadia Libs Test App")

app_dir = Path(__file__).resolve().parent
static_dir = app_dir / "static"
templates_dir = app_dir / "templates"
static_dir.mkdir(parents=True, exist_ok=True)
templates_dir.mkdir(parents=True, exist_ok=True)

# Static and templates
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Serve UI static from the lib (no copying to app)
mount_ui_static(app)
# Optional: still scaffold defaults if you want local files
# ensure_templates(str(app_dir))
mount_templates(templates, persist_header=True)
app.include_router(ui_router)

# Minimal in-memory auth with defaults
_settings = AuthSettings(secret_key="dev-secret")
_repo = InMemoryRepo()
app.include_router(create_auth_router(_repo, _settings))
mount_cookie_agent_middleware(app, secret_key=_settings.secret_key, algorithm=_settings.algorithm)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Test App"})

@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    agent = getattr(request.state, "agent", None) or getattr(request.state, "user", None)
    return templates.TemplateResponse("profile.html", {"request": request, "agent": agent})

@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
