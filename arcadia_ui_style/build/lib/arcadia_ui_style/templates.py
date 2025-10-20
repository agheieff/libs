from __future__ import annotations

import os
from pathlib import Path
from typing import Any

def ensure_templates(app_dir: str) -> str:
    """Ensure default header/footer templates and base CSS exist under app's templates/static.

    Returns path to templates directory that contains _header.html and _footer.html.
    """
    tdir = Path(app_dir) / "templates"
    sdir = Path(app_dir) / "static"
    tdir.mkdir(parents=True, exist_ok=True)
    sdir.mkdir(parents=True, exist_ok=True)
    header = tdir / "_header.html"
    footer = tdir / "_footer.html"
    css = sdir / "arcadia.css"
    auth = tdir / "_auth.html"
    if not header.exists():
        header.write_text("""<header style=\"display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 12px;border-bottom:1px solid #eee\">\n  <div style=\"display:flex;align-items:center;gap:10px\"><a href=\"/\" style=\"text-decoration:none;font-weight:600;color:inherit\">{{ title or 'Arcadia' }}</a></div>\n  <div style=\"display:flex;align-items:center;gap:8px\">\n    <button id=\"theme-toggle\" title=\"Toggle theme\">Theme</button>\n    <div id=\"userbar\"></div>\n  </div>\n</header>\n""", encoding="utf-8")
    if not footer.exists():
        footer.write_text("""<footer style=\"margin-top:32px;padding:12px;border-top:1px solid #eee;color:#888\">© Arcadia</footer>\n""", encoding="utf-8")
    if not css.exists():
        css.write_text(
            ":root{--bg:#fff;--fg:#111;--muted:#666;--link:#06c;}"
            ":root[data-theme=dark]{--bg:#111;--fg:#eee;--muted:#aaa;--link:#4af}"
            "@media(prefers-color-scheme:dark){:root:not([data-theme]){--bg:#111;--fg:#eee;--muted:#aaa;--link:#4af}}"
            "body{background:var(--bg);color:var(--fg)}a{color:var(--link)}",
            encoding="utf-8",
        )
    if not auth.exists():
        auth.write_text(
            """
<dialog id=\"authdlg\">
  <form method=\"dialog\" style=\"min-width:340px\">
    <h3 style=\"margin:0 0 8px\">Sign in</h3>
    <div style=\"display:flex;flex-direction:column;gap:8px\">
      <input id=\"email\" placeholder=\"you@example.com\" />
      <input id=\"password\" type=\"password\" placeholder=\"password\" />
      <div style=\"display:flex;gap:8px;justify-content:flex-end\">
        <button id=\"register\" value=\"register\">Sign up</button>
        <button id=\"login\" value=\"login\">Login</button>
        <button value=\"cancel\">Cancel</button>
      </div>
    </div>
  </form>
</dialog>
            """,
            encoding="utf-8",
        )
    return str(tdir)
