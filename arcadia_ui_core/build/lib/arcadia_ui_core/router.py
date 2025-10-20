from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, Any

_templates = None


def mount_templates(templates):
    global _templates
    _templates = templates


router = APIRouter()


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
