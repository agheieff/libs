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

from arcadia_ui_core import router as ui_router, attach_ui, mount_ui_static, render_page, ActiveProfileMiddleware  # type: ignore
from arcadia_ui_core.contextmenu import ContextMenuRegistry, ContextMenuRequest  # type: ignore
import json
from arcadia_ui_style import ensure_templates  # type: ignore
from arcadia_auth import create_auth_router, AuthSettings, mount_cookie_agent_middleware, create_sqlite_repo  # type: ignore


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
# Attach UI state so /ui/* endpoints work with the default router
# Provide profile provider/validator so active profile can be resolved and validated
def _get_account_id(obj):
    try:
        return getattr(obj, "id")
    except Exception:
        try:
            return obj.get("id")  # type: ignore[attr-defined]
        except Exception:
            return None

def _profile_provider(request: Request, user):
    acc_id = _get_account_id(user)
    if acc_id is None:
        return []
    try:
        return _repo.list_profiles(acc_id)
    except Exception:
        return []

def _profile_validator(request: Request, user, profile_id: str) -> bool:
    acc_id = _get_account_id(user)
    if acc_id is None:
        return False
    try:
        profs = _repo.list_profiles(acc_id)
        return any(str(p.get("id")) == str(profile_id) for p in profs)
    except Exception:
        return False

# Context menu: provide a profile menu with Edit/Delete actions
cm_registry = ContextMenuRegistry()

def _cm_profile(req: ContextMenuRequest):
    ds = req.dataset or {}
    pid = str(ds.get("id", "")).strip()
    items = []
    # Edit name via client event
    if pid:
        items.append({
            "id": "cm-edit",
            "label": "Edit name",
            "hx": {"get": f"/ui/cm/profile/edit?id={pid}", "target": "#arcadia-content", "swap": "none"},
        })
        items.append({"divider": True})
    # Delete profile via client event; disable when single-profile
    disable_delete = True
    try:
        user = getattr(req, "user", None)
        acc_id = getattr(user, "id", None)
        if acc_id is None and isinstance(user, dict):
            acc_id = user.get("id")
        profs = _repo.list_profiles(acc_id) if acc_id is not None else []
        disable_delete = (len(profs) <= 1)
    except Exception:
        disable_delete = True
    items.append({
        "id": "cm-delete",
        "label": "Delete profile",
        "hx": {"get": f"/ui/cm/profile/delete?id={pid}", "target": "#arcadia-content", "swap": "none"},
        "danger": True,
        "disabled": (not pid) or disable_delete,
    })
    return items

cm_registry.add("profile", _cm_profile)

attach_ui(
    app,
    templates,
    persist_header=True,
    context_menus=cm_registry,
    profile_provider=_profile_provider,
    profile_validator=_profile_validator,
)
app.include_router(ui_router)

# Enable ActiveProfileMiddleware to default the active profile and keep cookie/state in sync
app.add_middleware(ActiveProfileMiddleware, state=app.state.ui)

# SQLite auth with extended schema support
_settings = AuthSettings(secret_key="dev-secret")
_repo = create_sqlite_repo("sqlite:///./test_app.db", echo=False)  # Set to True for SQL debugging
app.include_router(create_auth_router(_repo, _settings))
mount_cookie_agent_middleware(app, secret_key=_settings.secret_key, algorithm=_settings.algorithm)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return render_page(request, templates, content_template="index_main.html", title="Test App", context={})

@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    agent = getattr(request.state, "agent", None) or getattr(request.state, "user", None)
    # Reflect app's multi_profile setting to the template
    return render_page(request, templates, content_template="profile_main.html", title="Profile", context={"agent": agent, "multi_profile": getattr(_settings, "multi_profile", True)})

@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request):
    return render_page(request, templates, content_template="settings_main.html", title="Settings", context={})

@app.get("/account", response_class=HTMLResponse)
def account(request: Request):
    return render_page(request, templates, content_template="account_main.html", title="Account", context={})

@app.get("/shortcuts", response_class=HTMLResponse)
def shortcuts(request: Request):
    return render_page(request, templates, content_template="shortcuts_main.html", title="Keyboard Shortcuts", context={})

# Context-menu endpoints that trigger client-side actions via htmx events
@app.get("/ui/cm/profile/edit")
def cm_profile_edit(request: Request, id: str):
    # Trigger a client event to toggle edit mode for this row (hx-swap none)
    payload = json.dumps({"profile:edit": {"id": id}})
    return HTMLResponse(content="", status_code=204, headers={"HX-Trigger": payload})


@app.get("/ui/cm/profile/delete")
def cm_profile_delete(request: Request, id: str):
    # Trigger a client event to initiate delete flow for this row
    payload = json.dumps({"profile:delete": {"id": id}})
    return HTMLResponse(content="", status_code=204, headers={"HX-Trigger": payload})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
