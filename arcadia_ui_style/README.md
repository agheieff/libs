# Arcadia UI Style

Opinionated theme and default templates for Arcadia apps.

## What’s included
- Static assets (served under `/ui-static` when mounted):
  - `arcadia_theme.css` — theme tokens, layout, header, panels, buttons
  - `theme-selector.js` — lightweight theme switcher that renders a submenu in the header
  - `contextmenu.js` — client for server-provided context menus (targets `.t-cm` markup)
- Template scaffolds via `ensure_templates(app_dir)`:
  - `_header.html`, `_footer.html`, `_auth.html`, `_settings.html`, `login.html`, `signup.html`, `_user_menu.html`
  - Uses a versioned sentinel (`<!-- arcadia-ui-style:v2 -->`) to safely rewrite the header when formats change

### Header defaults
When a user is present: Theme submenu, Profile, Account, Settings, and Log out entries are provided.
When anonymous: Log in and Sign up buttons are shown.

## Using assets in your app
Serve this package’s static files at `/ui-static` using arcadia_ui_core:

```python
from arcadia_ui_core import mount_ui_static

mount_ui_static(app)  # exposes /ui-static/{arcadia_theme.css,theme-selector.js,contextmenu.js}
```

Reference assets from templates (the scaffolded header already includes these):

```html
<link rel="stylesheet" href="/ui-static/arcadia_theme.css" />
<script src="/ui-static/theme-selector.js"></script>
<script src="/ui-static/contextmenu.js"></script>
```

Note: You can customize the context menu look in your CSS by styling `.t-cm`, `.t-cm-item`, and `.t-cm-divider` classes.

## Minimal setup example

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from arcadia_ui_core import router as ui_router, attach_ui, mount_ui_static
from arcadia_ui_style import ensure_templates

app = FastAPI()

# App dirs
templates = Jinja2Templates(directory="./templates")
app.mount("/static", StaticFiles(directory="./static"), name="static")

# Serve packaged UI assets and (optionally) scaffold local templates/assets
mount_ui_static(app)
ensure_templates(".")  # creates/updates header/footer, auth, settings, login/signup, and theme CSS

# Attach UI state and include default /ui/* endpoints
attach_ui(app, templates, persist_header=True)
app.include_router(ui_router)
```

Install (editable):

```bash
uv add -e ../libs/arcadia_ui_style
```

See also: `arcadia_ui_core` for the router, static mounting, and rendering helpers.
