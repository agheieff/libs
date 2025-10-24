Arcadia UI Style — Audit Implementation Journal

- 2025-10-24 — Step A: De-duplicate theme selector JS. Stopped generating theme-selector.js in ensure_templates and made ThemeManager.generate_theme_selector_js return the packaged static asset to keep a single source of truth. Files: arcadia_ui_style/arcadia_ui_style/templates.py, arcadia_ui_style/arcadia_ui_style/theme.py. Commit: 4ea6cb8.
