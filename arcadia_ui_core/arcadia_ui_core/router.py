from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, Any

_templates = None


def mount_templates(templates, *, persist_header: bool | None = None, brand_logo_url: str | None = None, brand_home_url: str | None = None, brand_name: str | None = None, brand_tag: str | None = None):
    global _templates
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
