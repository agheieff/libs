Arcadia UI Style — Audit Implementation Journal

- 2025-10-24 — Step A: De-duplicate theme selector JS. Stopped generating theme-selector.js in ensure_templates and made ThemeManager.generate_theme_selector_js return the packaged static asset to keep a single source of truth. Files: arcadia_ui_style/arcadia_ui_style/templates.py, arcadia_ui_style/arcadia_ui_style/theme.py. Commit: 4ea6cb8.

- 2025-10-24 — Step B: Split ensure_templates into cohesive helpers with a versioned sentinel. Introduced templates_v2 with helper functions and a header sentinel comment for rewrite gating; templates.py now delegates to the refactored implementation to preserve the public interface. Files: arcadia_ui_style/arcadia_ui_style/templates_v2.py, arcadia_ui_style/arcadia_ui_style/templates.py. Commit: e24d6ad.

- 2025-10-24 — Step C: Decouple theme asset generation from arcadia_ui_core. ensure_theme_assets now always uses the local ThemeManager to generate arcadia_theme.css when needed, removing the hidden dependency gate. Files: arcadia_ui_style/arcadia_ui_style/templates_v2.py. Commit: e4178e8.
