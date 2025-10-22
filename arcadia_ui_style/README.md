# Arcadia UI Style

Opinionated theme and template scaffolding for Arcadia UI.

- `ensure_templates(app_dir)` writes default Jinja templates (header/footer, login/signup, settings panel, user menu) and generates `arcadia_theme.css` using `ThemeManager`.
- Static assets are shipped within the package and can be served via `mount_ui_static(app)` from arcadia_ui_core.

Install (editable):
uv add -e ../libs/arcadia_ui_style

See also: arcadia_ui_core for the router and template mounting helpers.
