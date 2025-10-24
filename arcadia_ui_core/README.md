# Arcadia UI Core

Server‑side UI building blocks for FastAPI + Jinja, with pluggable header/footer/settings partials and a lightweight, server‑driven context‑menu system.

Key APIs:
- UIState, attach_ui(app, templates, …), create_ui_router(state)
- Routes: GET /ui/header, /ui/footer, /ui/settings, /ui/user_menu, /ui/context-menu
- Context menus: ContextMenuRegistry, ContextMenuRequest, MenuItem; client targets use data-cm="<name>"
- Static assets: mount_ui_static(app) serves /ui-static/theme-selector.js and /ui-static/contextmenu.js

## Quick start

```python
from fastapi import FastAPI
from starlette.templating import Jinja2Templates
from arcadia_ui_core import attach_ui, router, mount_ui_static

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Attach UI state and expose server-side partials
attach_ui(
    app,
    templates,
    brand_name="Arcadia",
    nav_items=[{"label": "Home", "href": "/"}],
)

# Serve JS/CSS from arcadia_ui_style under /ui-static
mount_ui_static(app)

# Register endpoints like /ui/header, /ui/footer, etc.
app.include_router(router)
```

Base template (include UI assets once):

```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" href="/ui-static/arcadia_theme.css" />
    <script src="/ui-static/theme-selector.js" defer></script>
    <script src="/ui-static/contextmenu.js" defer></script>
    <title>{{ title or 'Arcadia' }}</title>
  </head>
  <body>
    {# You can render header/footer via Jinja includes or fetch as partials from the routes below #}
    {% include "_header.html" ignore missing %}
    <main id="arcadia-content">{% block content %}{% endblock %}</main>
    {% include "_footer.html" ignore missing %}
  </body>
  </html>
```

## Routes (server-side partials)

- GET `/ui/header?title=Arcadia` → renders `_header.html` (204 if missing)
- GET `/ui/footer` → renders `_footer.html` (204 if missing)
- GET `/ui/settings` → renders `_settings.html` (204 if missing); receives `ui_settings_schema` and `ui_settings_mode` from Jinja globals
- GET `/ui/user_menu` → renders `_user_menu.html` (204 if missing); items come from a provider or `user_menu_items` global
- GET `/ui/context-menu?name=<menu>&path=<path?>&element_id=<id?>` → returns HTML for a floating menu, or 204 if no items
  - Client sends base64-JSON dataset via `X-CM-Dataset` and optional `X-CM-Selection` header

## Context menus

1) Define a registry and provider(s):

```python
from typing import List, Dict
from arcadia_ui_core import ContextMenuRegistry, ContextMenuRequest

cm = ContextMenuRegistry()

def file_menu(req: ContextMenuRequest) -> List[Dict]:
    name = req.dataset.get("name", "")
    return [
        {"label": f"Open {name}", "href": f"/files/{name}"},
        {"divider": True},
        {"label": "Delete", "hx": {"delete": f"/api/files/{name}", "confirm": "Delete file?"}, "danger": True},
    ]

cm.add("file", file_menu)
```

2) Wire it during UI attach:

```python
attach_ui(app, templates, context_menus=cm)
```

3) Mark targets in HTML with `data-cm` and any `data-*` you want to forward:

```html
<ul>
  {% for f in files %}
    <li data-cm="file" data-name="{{ f.name }}">{{ f.name }}</li>
  {% endfor %}
  </ul>
```

Including `/ui-static/contextmenu.js` is required; it listens for right‑clicks on `[data-cm]` elements, collects `data-*` attributes, and fetches `/ui/context-menu` to display a menu.

## Advanced: create_ui_router

If you prefer explicit dependency injection or have multiple apps, bind a router to a concrete state:

```python
from arcadia_ui_core import mount_templates, create_ui_router

state = mount_templates(templates, brand_name="Arcadia")
state.context_menus = cm  # optional
app.include_router(create_ui_router(state))
```

## Notes

- `attach_ui` configures Jinja globals like `brand_*`, `persist_header`, `nav_items`, `ui_settings_schema`, `ui_settings_mode` and stores a UIState under `app.state.ui`.
- `mount_ui_static` mounts assets under `/ui-static` from `arcadia_ui_style` (make sure that package is installed/available).
