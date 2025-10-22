# Arcadia UI Core

Core UI building blocks for FastAPI.

- FastAPI router with endpoints for header, footer, auth modal, settings, and user menu; `mount_templates` injects Jinja globals, `mount_ui_static` serves theme assets from arcadia_ui_style. Includes a simple `ThemeManager` to register themes and generate CSS variables/classes.

Install (editable):
uv add -e ../libs/arcadia_ui_core

Minimal usage:
```python
from arcadia_ui_core import router, mount_templates, mount_ui_static

app.include_router(router)
mount_ui_static(app)
mount_templates(jinja_templates, persist_header=True)
```

## Terminology
- Account: Authentication identity and credentials managed by the auth layer; one Account may be used by multiple agents.
- Profile: In‑app workspace/dataset that belongs to an Account; apps may enable multiple profiles per account.
- Agent: An actor operating the app (human or automated). Use “agent” instead of “user” in app‑level docs/UI.
