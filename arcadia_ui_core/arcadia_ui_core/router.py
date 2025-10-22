from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any, List, Callable

_templates = None
_user_menu_provider: Optional[Callable[[Any], List[Dict[str, Any]]]] = None  # type: ignore[name-defined]


def mount_templates(
    templates,
    *,
    persist_header: bool | None = None,
    brand_logo_url: str | None = None,
    brand_home_url: str | None = None,
    brand_name: str | None = None,
    brand_tag: str | None = None,
    settings_schema: Optional[Dict[str, Any]] | None = None,
    settings_mode: Optional[str] = None,
    nav_items: Optional[List[Dict[str, Any]]] = None,
    user_menu_items: Optional[List[Dict[str, Any]]] = None,
    user_menu_provider: Optional[Callable[[Any], List[Dict[str, Any]]]] = None,
):
    global _templates, _user_menu_provider
    _templates = templates
    try:
        if persist_header is not None:
            # Make available to Jinja templates as a global
            templates.env.globals["persist_header"] = bool(persist_header)
        if brand_logo_url is not None:
            templates.env.globals["brand_logo_url"] = brand_logo_url
        if brand_home_url is not None:
            templates.env.globals["brand_home_url"] = brand_home_url
        if brand_name is not None:
            templates.env.globals["brand_name"] = brand_name
        if brand_tag is not None:
            templates.env.globals["brand_tag"] = brand_tag
        if settings_schema is not None:
            templates.env.globals["ui_settings_schema"] = settings_schema
        if settings_mode is not None:
            templates.env.globals["ui_settings_mode"] = settings_mode
        if nav_items is not None:
            templates.env.globals["nav_items"] = nav_items
        if user_menu_items is not None:
            templates.env.globals["user_menu_items"] = user_menu_items
        if user_menu_provider is not None:
            _user_menu_provider = user_menu_provider
    except Exception:
        pass


router = APIRouter()


def mount_templates_personal(templates):
    """Personalized defaults: header persistence always on and default brand icon/home.

    Projects can call this to apply opinionated settings without passing options.
    """
    mount_templates(
        templates,
        persist_header=True,
        brand_logo_url="/static/logo.svg",
        brand_home_url="/",
    )


@router.get("/ui/header", response_class=HTMLResponse)
def ui_header(request: Request, *, title: str = "Arcadia"):
    if _templates is None:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request, "title": title}
    return _templates.TemplateResponse("_header.html", ctx)


@router.get("/ui/footer", response_class=HTMLResponse)
def ui_footer(request: Request):
    if _templates is None:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    return _templates.TemplateResponse("_footer.html", ctx)


@router.get("/ui/auth_modal", response_class=HTMLResponse)
def ui_auth_modal(request: Request):
    if _templates is None:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    # Optional template; return 204 if missing
    try:
        return _templates.TemplateResponse("_auth.html", ctx)
    except Exception:
        return HTMLResponse("", status_code=204)


@router.get("/ui/settings", response_class=HTMLResponse)
def ui_settings(request: Request):
    if _templates is None:
        return HTMLResponse("", status_code=204)
    ctx = {
        "request": request,
        "settings_schema": getattr(_templates.env, "globals", {}).get("ui_settings_schema"),
        "settings_mode": getattr(_templates.env, "globals", {}).get("ui_settings_mode"),
    }
    try:
        return _templates.TemplateResponse("_settings.html", ctx)
    except Exception:
        return HTMLResponse("", status_code=204)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if _templates is None:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    try:
        return _templates.TemplateResponse("login.html", ctx)
    except Exception:
        return HTMLResponse("Login page not available", status_code=404)


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    if _templates is None:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    try:
        return _templates.TemplateResponse("signup.html", ctx)
    except Exception:
        return HTMLResponse("Signup page not available", status_code=404)


def mount_ui_static(app):
    """Mount UI static assets (served from the ui_style package) under /ui-static.

    Apps should call this once during setup.
    """
    try:
        import arcadia_ui_style as _style  # type: ignore
        from pathlib import Path as _Path
        _root = _Path(_style.__file__).resolve().parent
        _static = _root / "static"
        if _static.exists():
            app.mount("/ui-static", StaticFiles(directory=str(_static)), name="ui-static")
    except Exception:
        pass


def _resolve_user_menu_items(user: Any) -> List[Dict[str, Any]]:
    # Provider wins
    try:
        if _user_menu_provider is not None:
            items = _user_menu_provider(user)
            if items:
                return list(items)
    except Exception:
        pass
    # Then globals
    try:
        gi = getattr(_templates.env, "globals", {})  # type: ignore[attr-defined]
        items = gi.get("user_menu_items")
        if items:
            return list(items)
    except Exception:
        pass
    # Defaults
    if user:
        return [
            {"label": "Profile", "href": "/profile"},
            {"label": "Settings", "href": "/settings"},
            {"divider": True},
            {"label": "Log out", "href": "/auth/logout"},
        ]
    else:
        return [
            {"label": "Log in", "href": "/login"},
            {"label": "Sign up", "href": "/signup", "primary": True},
        ]


@router.get("/ui/user_menu", response_class=HTMLResponse)
def ui_user_menu(request: Request):
    if _templates is None:
        return HTMLResponse("", status_code=204)
    user = getattr(request.state, "user", None)
    ctx = {"request": request, "user_menu_items": _resolve_user_menu_items(user)}
    try:
        return _templates.TemplateResponse("_user_menu.html", ctx)
    except Exception:
        return HTMLResponse("", status_code=204)
