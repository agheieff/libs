from __future__ import annotations

from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from starlette.templating import Jinja2Templates
from jinja2 import TemplateNotFound
from starlette.middleware.base import BaseHTTPMiddleware
import base64
import json
import html

from .contextmenu import ContextMenuRegistry, ContextMenuRequest


@dataclass
class UIState:
    """Container for UI runtime state.

    Replaces previous module-level globals; can be attached to app.state
    or captured by a router factory for explicit dependency injection.
    """

    templates: Jinja2Templates
    user_menu_provider: Optional[Callable[[Any], List[Dict[str, Any]]]] = None
    context_menus: Optional[ContextMenuRegistry] = None
    # i18n
    translations: Optional[Dict[str, Dict[str, str]]] = None
    locale: Optional[str] = "en"
    # active profile support
    active_profile_cookie: str = "active_profile"
    # Provider returns list of profiles (dicts with at least id, display_name) for current user
    profile_provider: Optional[Callable[[Request, Any], List[Dict[str, Any]]]] = None
    # Validator checks if a profile id belongs to current user
    profile_validator: Optional[Callable[[Request, Any, str], bool]] = None


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
    context_menus: Optional[ContextMenuRegistry] = None,
    translations: Optional[Dict[str, Dict[str, str]]] = None,
    locale: Optional[str] = "en",
    # active profile
    active_profile_cookie: str = "active_profile",
    profile_provider: Optional[Callable[[Request, Any], List[Dict[str, Any]]]] = None,
    profile_validator: Optional[Callable[[Request, Any, str], bool]] = None,
):
    """Configure provided Jinja templates with globals.

    Returns a UIState that can be attached to app.state or passed to a router factory.
    """
    # Configure Jinja globals (kept for backward compatibility in templates)
    gi = templates.env.globals
    if persist_header is not None:
        gi["persist_header"] = bool(persist_header)
    if brand_logo_url is not None:
        gi["brand_logo_url"] = brand_logo_url
    if brand_home_url is not None:
        gi["brand_home_url"] = brand_home_url
    if brand_name is not None:
        gi["brand_name"] = brand_name
    if brand_tag is not None:
        gi["brand_tag"] = brand_tag
    if settings_schema is not None:
        gi["ui_settings_schema"] = settings_schema
    if settings_mode is not None:
        gi["ui_settings_mode"] = settings_mode
    if nav_items is not None:
        gi["nav_items"] = nav_items
    if user_menu_items is not None:
        gi["user_menu_items"] = user_menu_items

    state = UIState(
        templates=templates,
        user_menu_provider=user_menu_provider,
        context_menus=context_menus,
        translations=translations,
        locale=locale,
        active_profile_cookie=active_profile_cookie,
        profile_provider=profile_provider,
        profile_validator=profile_validator,
    )

    # Inject a minimal button helper returning class strings
    def btn(variant: Optional[str] = None, *, primary: Optional[bool] = None) -> str:
        classes = ["t-btn"]
        v = (variant or "").strip()
        if v:
            classes.append(f"t-btn-{v}")
        if primary:
            # Avoid duplicate when variant already equals "primary"
            if v != "primary":
                classes.append("t-btn-primary")
        return " ".join(classes)

    templates.env.globals["btn"] = btn

    # Inject minimal i18n lookup as a Jinja global
    def t(key: str, default: Optional[str] = None) -> str:
        try:
            loc = state.locale or "en"
            table = (state.translations or {}).get(loc)
            if isinstance(table, dict):
                val = table.get(key)
                if val is not None:
                    return str(val)
        except Exception:
            pass
        return default if default is not None else key

    templates.env.globals["t"] = t

    # Expose active_profile_id(request) helper
    def _active_profile_id(request: Request) -> Optional[str]:
        try:
            return getattr(request.state, "active_profile_id", None)
        except Exception:
            return None
    templates.env.globals["active_profile_id"] = _active_profile_id

    # Expose active_profile_name(request) helper using profile_provider if available
    def _active_profile_name(request: Request) -> Optional[str]:
        try:
            apid = getattr(request.state, "active_profile_id", None)
            if not apid:
                return None
            if state.profile_provider and getattr(request.state, "user", None) is not None:
                profs = state.profile_provider(request, getattr(request.state, "user", None)) or []
                for p in profs:
                    if str(p.get("id")) == str(apid):
                        return p.get("display_name")
        except Exception:
            pass
        return None
    templates.env.globals["active_profile_name"] = _active_profile_name

    return state


def attach_ui(
    app,
    templates: Jinja2Templates,
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
    context_menus: Optional[ContextMenuRegistry] = None,
    translations: Optional[Dict[str, Dict[str, str]]] = None,
    locale: Optional[str] = "en",
    active_profile_cookie: str = "active_profile",
    profile_provider: Optional[Callable[[Request, Any], List[Dict[str, Any]]]] = None,
    profile_validator: Optional[Callable[[Request, Any, str], bool]] = None,
) -> UIState:
    """Attach UI state to app.state.ui and configure template globals.

    This is the preferred bootstrap path for the default exported router.
    """
    state = mount_templates(
        templates,
        persist_header=persist_header,
        brand_logo_url=brand_logo_url,
        brand_home_url=brand_home_url,
        brand_name=brand_name,
        brand_tag=brand_tag,
        settings_schema=settings_schema,
        settings_mode=settings_mode,
        nav_items=nav_items,
        user_menu_items=user_menu_items,
        user_menu_provider=user_menu_provider,
        context_menus=context_menus,
        translations=translations,
        locale=locale,
        active_profile_cookie=active_profile_cookie,
        profile_provider=profile_provider,
        profile_validator=profile_validator,
    )
    # Attach to app.state for request-time access
    setattr(app.state, "ui", state)
    return state


router = APIRouter()


# Minimal helpers to escape text and attribute values
def safe_attr(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def safe_label(text: Any) -> str:
    if text is None:
        return ""
    # Text node content; escape HTML metacharacters
    return html.escape(str(text), quote=False)


class ActiveProfileMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, state: Optional[UIState] = None):
        super().__init__(app)
        self.state = state

    async def dispatch(self, request: Request, call_next):
        state = self.state
        user = getattr(request.state, "user", None)
        current_id: Optional[str] = None
        changed = False
        if user is not None and state is not None:
            cookie_name = state.active_profile_cookie or "active_profile"
            # Read cookie
            try:
                current_id = request.cookies.get(cookie_name)
            except Exception:
                current_id = None
            # Validate
            valid = False
            if current_id:
                try:
                    if state.profile_validator:
                        valid = bool(state.profile_validator(request, user, str(current_id)))
                    elif state.profile_provider:
                        profs = state.profile_provider(request, user) or []
                        valid = any(str(p.get("id")) == str(current_id) for p in profs)
                    else:
                        valid = True
                except Exception:
                    valid = False
            if not current_id or not valid:
                # Pick default
                try:
                    if state.profile_provider:
                        profs = state.profile_provider(request, user) or []
                        if profs:
                            current_id = str(profs[0].get("id"))
                            changed = True
                except Exception:
                    pass
            try:
                setattr(request.state, "active_profile_id", current_id)
            except Exception:
                pass

        response = await call_next(request)
        # Write cookie if changed
        if (user is not None) and (self.state is not None):
            cookie_name = self.state.active_profile_cookie or "active_profile"
            if changed and current_id:
                try:
                    response.set_cookie(cookie_name, current_id, path="/", samesite="lax")
                except Exception:
                    pass
        return response


def mount_templates_personal(templates):
    """Personalized defaults: header persistence always on and default brand icon/home.

    Projects can call this to apply opinionated settings without passing options.
    """
    return mount_templates(
        templates,
        persist_header=True,
        brand_logo_url="/static/logo.svg",
        brand_home_url="/",
    )


@router.get("/ui/header", response_class=HTMLResponse)
def ui_header(request: Request, *, title: str = "Arcadia"):
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request, "title": title}
    return state.templates.TemplateResponse("_header.html", ctx)


@router.get("/ui/footer", response_class=HTMLResponse)
def ui_footer(request: Request):
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    return state.templates.TemplateResponse("_footer.html", ctx)


@router.get("/ui/auth_modal", response_class=HTMLResponse)
def ui_auth_modal(request: Request):
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    # Optional template; return 204 if missing
    try:
        return state.templates.TemplateResponse("_auth.html", ctx)
    except TemplateNotFound:
        return HTMLResponse("", status_code=204)


@router.get("/ui/settings", response_class=HTMLResponse)
def ui_settings(request: Request):
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state:
        return HTMLResponse("", status_code=204)
    ctx = {
        "request": request,
        "settings_schema": getattr(state.templates.env, "globals", {}).get("ui_settings_schema"),
        "settings_mode": getattr(state.templates.env, "globals", {}).get("ui_settings_mode"),
    }
    try:
        return state.templates.TemplateResponse("_settings.html", ctx)
    except TemplateNotFound:
        return HTMLResponse("", status_code=204)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    try:
        return state.templates.TemplateResponse("login.html", ctx)
    except TemplateNotFound:
        return HTMLResponse("Login page not available", status_code=404)


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state:
        return HTMLResponse("", status_code=204)
    ctx = {"request": request}
    try:
        return state.templates.TemplateResponse("signup.html", ctx)
    except TemplateNotFound:
        return HTMLResponse("Signup page not available", status_code=404)


def mount_ui_static(app):
    """Mount UI static assets (served from the ui_style package) under /ui-static.

    Apps should call this once during setup.
    """
    try:
        import arcadia_ui_style as _style  # type: ignore
    except ImportError:
        return
    from pathlib import Path as _Path
    _root = _Path(_style.__file__).resolve().parent
    _static = _root / "static"
    if _static.exists():
        app.mount("/ui-static", StaticFiles(directory=str(_static)), name="ui-static")


def _template_exists(templates, name: str) -> bool:
    if not name:
        return False
    try:
        templates.env.get_template(name)
        return True
    except TemplateNotFound:
        return False


def _render_subtemplate(templates, name: str, ctx: Dict[str, Any]) -> str:
    try:
        return templates.env.get_template(name).render(ctx)
    except TemplateNotFound:
        return ""


def render_page(
    request: Request,
    templates,
    *,
    content_template: str,
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    layout_template: str = "_layout.html",
    wrapper_template: str = "_content_wrapper.html",
    status_code: int = 200,
):
    """Render a page with DRY composition.

    - Full page (first load): use layout_template which includes header/footer and wraps content under #arcadia-content.
    - htmx boosted nav (HX-Request=true): return only wrapper_template with #arcadia-content and an out-of-band <title>.

    Falls back to minimal HTML/fragment when templates are missing.
    """
    base: Dict[str, Any] = {"request": request, "title": title, "content_template": content_template}
    if context:
        base.update(context)

    hx = (request.headers.get("HX-Request") == "true") or (request.headers.get("hx-request") == "true")

    if hx:
        if _template_exists(templates, wrapper_template):
            try:
                return templates.TemplateResponse(wrapper_template, base, status_code=status_code)
            except TemplateNotFound:
                pass
        # Fallback: render content and wrap with #arcadia-content; include OOB title
        body = _render_subtemplate(templates, content_template, base)
        html = f"<title hx-swap-oob=\"true\">{(title or 'Arcadia')}</title>\n<div id=\"arcadia-content\">{body}</div>"
        return HTMLResponse(content=html, status_code=status_code)

    # Full page
    if _template_exists(templates, layout_template):
        try:
            return templates.TemplateResponse(layout_template, base, status_code=status_code)
        except TemplateNotFound:
            pass
    # Minimal fallback full page
    body = _render_subtemplate(templates, content_template, base)
    html = "".join([
        "<!DOCTYPE html><html lang=\"en\"><head>",
        f"<meta charset=\"utf-8\"/><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>",
        f"<title>{(title or 'Arcadia')}</title>",
        "</head><body>",
        f"<div id=\"arcadia-content\">{body}</div>",
        "</body></html>",
    ])
    return HTMLResponse(content=html, status_code=status_code)


def render_composed_page(
    request: Request,
    templates,
    *,
    glue_template: str,
    components: Dict[str, str],
    title: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    layout_template: str = "_layout.html",
    wrapper_template: str = "_content_wrapper.html",
    status_code: int = 200,
):
    """Render a page whose <main> is composed by a glue template that includes component templates.

    The glue template should reference components via the provided mapping, e.g.:
      {% include components.hero ignore missing %}
      {% include components.sidebar ignore missing %}
    """
    ctx = dict(context or {})
    ctx["components"] = dict(components or {})
    return render_page(
        request,
        templates,
        content_template=glue_template,
        title=title,
        context=ctx,
        layout_template=layout_template,
        wrapper_template=wrapper_template,
        status_code=status_code,
    )


def _resolve_user_menu_items(user: Any, state: Optional[UIState]) -> List[Dict[str, Any]]:
    # Provider wins
    try:
        if state and state.user_menu_provider is not None:
            items = state.user_menu_provider(user)
            if items:
                return list(items)
    except Exception:
        pass
    # Then globals
    if state:
        gi = getattr(state.templates.env, "globals", {})  # type: ignore[attr-defined]
        items = gi.get("user_menu_items")
        if items:
            return list(items)
    # Defaults
    if user:
        return [
            {"label": "Profile", "href": "/profile"},
            {"label": "Account", "href": "/account"},
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
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state:
        return HTMLResponse("", status_code=204)
    user = getattr(request.state, "user", None)
    ctx = {"request": request, "user_menu_items": _resolve_user_menu_items(user, state)}
    try:
        return state.templates.TemplateResponse("_user_menu.html", ctx)
    except TemplateNotFound:
        return HTMLResponse("", status_code=204)


def _build_context_menu_html(items: List[Dict[str, Any]], name: str) -> str:
    if not items:
        return ""
    out: List[str] = [f'<div class="t-cm" role="menu" data-name="{name}">']
    for it in items:
        if it.get("divider"):
            out.append('<hr class="t-cm-divider" />')
            continue
        label = safe_label(it.get("label", ""))
        classes = ["t-cm-item"]
        if it.get("disabled"):
            classes.append("is-disabled")
        if it.get("danger"):
            classes.append("is-danger")
        cls = " ".join(classes)

        attrs: List[str] = [f'class="{cls}"', 'role="menuitem"']
        if it.get("id"):
            attrs.append(f'id="{safe_attr(it["id"])}"')
        target = it.get("target")
        if target:
            attrs.append(f'target="{safe_attr(target)}"')

        hx = it.get("hx") or {}
        href_raw = it.get("href")
        # Only allow href starting with /, http:// or https:// (case-insensitive)
        href: Optional[str] = None
        if isinstance(href_raw, str):
            _href_trim = href_raw.strip()
            _href_low = _href_trim.lower()
            if _href_trim.startswith("/") or _href_low.startswith("http://") or _href_low.startswith("https://"):
                href = _href_trim
        disabled = bool(it.get("disabled"))

        if disabled:
            # Render as a non-interactive button (disabled)
            out.append(f'<button type="button" {" ".join(attrs)} disabled>{label}</button>')
        elif href:
            # Simple navigation
            attrs.append(f'href="{safe_attr(href)}"')
            # If opening in a new tab, ensure no opener leakage
            if target == "_blank":
                attrs.append('rel="noopener noreferrer"')
            out.append(f'<a {" ".join(attrs)}>{label}</a>')
        elif hx:
            # htmx action
            _allowed = {"get", "post", "delete", "put", "patch", "confirm", "target", "swap"}
            for k, v in hx.items():
                ks = str(k).strip().lower()
                if ks.startswith("hx-"):
                    ks = ks[3:]
                if ks.startswith("hx_"):
                    ks = ks[3:]
                ks = ks.replace("_", "-")
                if ks not in _allowed:
                    continue
                attrs.append(f'hx-{ks}="{safe_attr(v)}"')
            out.append(f'<button type="button" {" ".join(attrs)}>{label}</button>')
        else:
            # Fallback inert button
            out.append(f'<button type="button" {" ".join(attrs)}>{label}</button>')
    out.append("</div>")
    return "".join(out)


@router.get("/ui/context-menu", response_class=HTMLResponse)
def ui_context_menu(request: Request, name: str, path: Optional[str] = None, element_id: Optional[str] = None):
    state: Optional[UIState] = getattr(request.app.state, "ui", None)
    if not state or not state.context_menus:
        return HTMLResponse("", status_code=204)
    provider = state.context_menus.get(name)
    if not provider:
        return HTMLResponse("", status_code=204)

    dataset: Dict[str, str] = {}
    sel: Optional[str] = None
    # Headers carry dataset/selection (base64 JSON)
    ds_hdr = request.headers.get("X-CM-Dataset")
    if ds_hdr:
        try:
            payload = base64.b64decode(ds_hdr.encode("utf-8"))
            dataset = json.loads(payload.decode("utf-8"))
            if not isinstance(dataset, dict):
                dataset = {}
        except Exception:
            dataset = {}
    sel = request.headers.get("X-CM-Selection")

    cm_req = ContextMenuRequest(
        dataset=dataset,
        selection=sel,
        path=path,
        element_id=element_id,
        user=getattr(request.state, "user", None),
    )
    try:
        items = provider(cm_req) or []
    except Exception:
        items = []
    if not items:
        return HTMLResponse("", status_code=204)
    html = _build_context_menu_html(items, name)
    return HTMLResponse(html)
    user = getattr(request.state, "user", None)
    ctx = {"request": request, "user_menu_items": _resolve_user_menu_items(user, state)}
    try:
        return state.templates.TemplateResponse("_user_menu.html", ctx)
    except TemplateNotFound:
        return HTMLResponse("", status_code=204)


def create_ui_router(state: UIState) -> APIRouter:
    """Return a router bound to the provided UI state via closures.

    Useful for multi-app setups or explicit dependency injection without app.state.
    """
    r = APIRouter()

    @r.get("/ui/header", response_class=HTMLResponse)
    def _header(request: Request, *, title: str = "Arcadia"):
        ctx = {"request": request, "title": title}
        return state.templates.TemplateResponse("_header.html", ctx)

    @r.get("/ui/footer", response_class=HTMLResponse)
    def _footer(request: Request):
        ctx = {"request": request}
        return state.templates.TemplateResponse("_footer.html", ctx)

    @r.get("/ui/auth_modal", response_class=HTMLResponse)
    def _auth_modal(request: Request):
        ctx = {"request": request}
        try:
            return state.templates.TemplateResponse("_auth.html", ctx)
        except TemplateNotFound:
            return HTMLResponse("", status_code=204)

    @r.get("/ui/settings", response_class=HTMLResponse)
    def _settings(request: Request):
        ctx = {
            "request": request,
            "settings_schema": getattr(state.templates.env, "globals", {}).get("ui_settings_schema"),
            "settings_mode": getattr(state.templates.env, "globals", {}).get("ui_settings_mode"),
        }
        try:
            return state.templates.TemplateResponse("_settings.html", ctx)
        except TemplateNotFound:
            return HTMLResponse("", status_code=204)

    @r.get("/login", response_class=HTMLResponse)
    def _login(request: Request):
        ctx = {"request": request}
        try:
            return state.templates.TemplateResponse("login.html", ctx)
        except TemplateNotFound:
            return HTMLResponse("Login page not available", status_code=404)

    @r.get("/signup", response_class=HTMLResponse)
    def _signup(request: Request):
        ctx = {"request": request}
        try:
            return state.templates.TemplateResponse("signup.html", ctx)
        except TemplateNotFound:
            return HTMLResponse("Signup page not available", status_code=404)

    @r.get("/ui/user_menu", response_class=HTMLResponse)
    def _user_menu(request: Request):
        user = getattr(request.state, "user", None)
        ctx = {"request": request, "user_menu_items": _resolve_user_menu_items(user, state)}
        try:
            return state.templates.TemplateResponse("_user_menu.html", ctx)
        except TemplateNotFound:
            return HTMLResponse("", status_code=204)

    @r.get("/ui/active-profile")
    def _active_profile_get(request: Request):
        apid = getattr(request.state, "active_profile_id", None)
        if not apid:
            return Response(status_code=204)
        name: Optional[str] = None
        try:
            if state.profile_provider and getattr(request.state, "user", None) is not None:
                profs = state.profile_provider(request, getattr(request.state, "user", None)) or []
                for p in profs:
                    if str(p.get("id")) == str(apid):
                        name = p.get("display_name")
                        break
        except Exception:
            pass
        return JSONResponse({"id": apid, "name": name})

    @r.post("/ui/active-profile")
    def _active_profile_set(request: Request, payload: Dict[str, Any] = Body(...)):
        user = getattr(request.state, "user", None)
        if not user:
            return Response(status_code=401)
        apid = str(payload.get("id", "")).strip()
        if not apid:
            return Response(status_code=400)
        valid = False
        try:
            if state.profile_validator:
                valid = bool(state.profile_validator(request, user, apid))
            elif state.profile_provider:
                profs = state.profile_provider(request, user) or []
                valid = any(str(p.get("id")) == str(apid) for p in profs)
        except Exception:
            valid = False
        if not valid:
            return Response(status_code=403)
        try:
            setattr(request.state, "active_profile_id", apid)
        except Exception:
            pass
        resp = Response(status_code=204)
        try:
            resp.set_cookie(state.active_profile_cookie, apid, path="/", samesite="lax")
        except Exception:
            pass
        return resp

    @r.get("/ui/active-profile")
    def _active_profile_get(request: Request):
        apid = getattr(request.state, "active_profile_id", None)
        if not apid:
            return Response(status_code=204)
        name: Optional[str] = None
        try:
            if state.profile_provider and getattr(request.state, "user", None) is not None:
                profs = state.profile_provider(request, getattr(request.state, "user", None)) or []
                for p in profs:
                    if str(p.get("id")) == str(apid):
                        name = p.get("display_name")
                        break
        except Exception:
            pass
        return JSONResponse({"id": apid, "name": name})

    @r.post("/ui/active-profile")
    def _active_profile_set(request: Request, payload: Dict[str, Any] = Body(...)):
        user = getattr(request.state, "user", None)
        if not user:
            return Response(status_code=401)
        apid = str(payload.get("id", "")).strip()
        if not apid:
            return Response(status_code=400)
        valid = False
        try:
            if state.profile_validator:
                valid = bool(state.profile_validator(request, user, apid))
            elif state.profile_provider:
                profs = state.profile_provider(request, user) or []
                valid = any(str(p.get("id")) == str(apid) for p in profs)
        except Exception:
            valid = False
        if not valid:
            return Response(status_code=403)
        try:
            setattr(request.state, "active_profile_id", apid)
        except Exception:
            pass
        resp = Response(status_code=204)
        try:
            resp.set_cookie(state.active_profile_cookie, apid, path="/", samesite="lax")
        except Exception:
            pass
        return resp

    @r.get("/ui/context-menu", response_class=HTMLResponse)
    def _context_menu(request: Request, name: str, path: Optional[str] = None, element_id: Optional[str] = None):
        if not state.context_menus:
            return HTMLResponse("", status_code=204)
        provider = state.context_menus.get(name)
        if not provider:
            return HTMLResponse("", status_code=204)

        dataset: Dict[str, str] = {}
        ds_hdr = request.headers.get("X-CM-Dataset")
        if ds_hdr:
            try:
                payload = base64.b64decode(ds_hdr.encode("utf-8"))
                dataset = json.loads(payload.decode("utf-8"))
                if not isinstance(dataset, dict):
                    dataset = {}
            except Exception:
                dataset = {}
        sel = request.headers.get("X-CM-Selection")
        cm_req = ContextMenuRequest(
            dataset=dataset,
            selection=sel,
            path=path,
            element_id=element_id,
            user=getattr(request.state, "user", None),
        )
        try:
            items = provider(cm_req) or []
        except Exception:
            items = []
        if not items:
            return HTMLResponse("", status_code=204)
        html = _build_context_menu_html(items, name)
        return HTMLResponse(html)

    return r
