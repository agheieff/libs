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
    # Write/refresh header to ensure htmx persistence block exists
    _cur = header.read_text(encoding="utf-8", errors="ignore") if header.exists() else ""
    needs_write = (
        (not header.exists()) or
        ("ai-header" in _cur) or
        (("hx-boost" not in _cur) and ("htmx.org" not in _cur)) or
        ("brand_logo_url" not in _cur)
    )
    if needs_write:
        header.write_text(
            """
<!-- Shared header styled like Trading MMO -->
<style>
  :root { scrollbar-gutter: stable; }
  .tm-header, .tm-header *, .tm-header *::before, .tm-header *::after { box-sizing: border-box; }
  .tm-header { background:#111827; color:#e5e7eb; border-bottom:1px solid #1f2937; font-family: system-ui, -apple-system, Segoe UI, Roboto, \"Helvetica Neue\", Arial, \"Noto Sans\", \"Liberation Sans\", sans-serif; font-size:14px; line-height:1.25; }
  .tm-header .tm-container { max-width:1200px; margin:0 auto; padding:0.75rem 1rem; display:flex; align-items:center; justify-content:space-between; }
  @media (min-width: 640px){ .tm-header .tm-container { min-height:56px; } }
  .tm-header .tm-brand { color:#f9fafb; font-weight:600; text-decoration:none; letter-spacing:0.2px; font-size:18px; }
  .tm-header .tm-nav a { color:#9ca3af; text-decoration:none; margin-left:1rem; font-size:14px; }
  .tm-header .tm-nav a:hover { color:#f9fafb; }
  .tm-right { display:flex; align-items:center; gap:1rem; }
  .tm-actions .tm-btn { padding:0.35rem 0.75rem; border:1px solid #374151; border-radius:0.375rem; color:#e5e7eb; text-decoration:none; font-size:14px; }
  .tm-actions .tm-btn:hover { background:#1f2937; }
  .tm-actions .tm-primary { border-color:#2563eb; background:#2563eb; }
  .tm-actions .tm-primary:hover { background:#1d4ed8; }
  .tm-user { position:relative; }
  .tm-user-btn { padding:0.35rem 0.75rem; border:1px solid #374151; border-radius:0.375rem; color:#e5e7eb; background:#111827; cursor:pointer; font-size:14px; }
  .tm-user-menu { position:absolute; right:0; top:2.25rem; background:#111827; border:1px solid #1f2937; border-radius:0.375rem; min-width:180px; display:none; z-index:50; }
  .tm-user-menu a { display:block; padding:0.5rem 0.75rem; color:#e5e7eb; text-decoration:none; font-size:14px; }
  .tm-user-menu a:hover { background:#1f2937; }
  .tm-divider { width:1px; height:18px; background:#374151; margin:0 0.5rem; }
  .tm-nav a.active { color:#f9fafb; }
  .tm-brand small { color:#9ca3af; font-weight:400; font-size:12px; margin-left:6px; }
  .tm-flex { display:flex; align-items:center; gap:.75rem; }
  .tm-nav { display:flex; align-items:center; }
  @media (max-width: 640px){ .tm-nav a { margin-left:.5rem; } }
  .tm-link { color:#9ca3af; }
  .tm-link:hover { color:#f9fafb; }
  .tm-hidden { display:none; }
  .tm-show { display:block; }
  .tm-menu-right { position:relative; }
  .tm-user-menu hr { border:none; border-top:1px solid #1f2937; margin:4px 0; }
</style>
<header class=\"tm-header\">
  <div class=\"tm-container\">
    <a class=\"tm-brand\" href=\"{{ brand_home_url or '/' }}\">
      {% if brand_logo_url %}<img src=\"{{ brand_logo_url }}\" alt=\"logo\" style=\"height:22px;vertical-align:middle;margin-right:8px;\"/>{% endif %}
      {{ brand_name or 'Trading MMO' }}<small>{{ brand_tag or '' }}</small>
    </a>
    <div class=\"tm-right\">
      <nav class=\"tm-nav\" aria-label=\"Primary\">
        <a href=\"/\" class=\"tm-link\">Home</a>
        <a href=\"/chart\" class=\"tm-link\">Chart</a>
        <a href=\"/docs\" class=\"tm-link\">API</a>
      </nav>
      {% if request and request.state and request.state.user %}
        <div class=\"tm-user\" id=\"tm-user\">
          <button class=\"tm-user-btn\" id=\"tm-user-btn\">Account ▾</button>
          <div class=\"tm-user-menu\" id=\"tm-user-menu\">
            <a href=\"/profile\">Profile</a>
            <a href=\"/settings\">Settings</a>
            <a href=\"/words\">My Words</a>
            <a href=\"/stats\">Statistics</a>
            <hr />
            <a href=\"/logout\">Log out</a>
          </div>
        </div>
      {% else %}
        <div class=\"tm-actions\">
          <a href=\"/login\" class=\"tm-btn\">Log in</a>
          <a href=\"/signup\" class=\"tm-btn tm-primary\">Sign up</a>
        </div>
      {% endif %}
    </div>
  </div>
</header>
<script>
(function(){
  var btn = document.getElementById('tm-user-btn');
  var menu = document.getElementById('tm-user-menu');
  if (!btn || !menu) return;
  btn.addEventListener('click', function(e){ e.stopPropagation(); menu.style.display = (menu.style.display === 'block' ? 'none' : 'block'); });
  document.addEventListener('click', function(){ if (menu.style.display === 'block') menu.style.display = 'none'; });
})();
</script>
{% set __persist = persist_header if persist_header is defined else true %}
{% if __persist %}
<script src="https://unpkg.com/htmx.org@1.9.12" integrity="sha384-+bVsx3b8QdE7cO1S4oFQ9hQ1TImfQxWqS4LzJd8j3jL5uFQw8L7f3NfL2hJdJg9w" crossorigin="anonymous"></script>
<script>
// Enable header persistence via htmx: boost links/forms and swap only #arcadia-content
(function(){
  try{
    var b=document.body; if(!b) return;
    b.setAttribute('hx-boost','true');
    b.setAttribute('hx-target','#arcadia-content');
    b.setAttribute('hx-select','#arcadia-content');
    b.setAttribute('hx-swap','innerHTML');
    b.setAttribute('hx-push-url','true');
  }catch(e){}
})();
</script>
<!-- Persistent module hook: re-initialize pages after HTMX swaps (e.g., chart bootstrap) -->
<script type="module">
  const initPage = async () => {
    const chartCanvas = document.getElementById('price-chart');
    if (chartCanvas) {
      try {
        const mod = await import('/static/js/modules/app.js');
        if (!window._arcadia_chart) {
          window._arcadia_chart = mod.bootstrapApp?.();
        }
      } catch (e) { /* ignore */ }
    }
  };
  window.addEventListener('DOMContentLoaded', initPage);
  document.body.addEventListener('htmx:afterSwap', initPage);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') initPage();
  });
}</script>
{% endif %}
            """,
            encoding="utf-8",
        )
    if not footer.exists():
        footer.write_text("""<footer style=\"margin-top:32px;padding:12px;border-top:1px solid #eee;color:#888\">© Arcadia</footer>\n""", encoding="utf-8")
    if not css.exists():
        css.write_text(
            ("/* AI Chat-inspired theme */\n" 
             ":root{--bg:#ffffff;--fg:#111;--muted:#666;--border:#e6e6e6;--panel:#f9f9fb;--primary:#1f6feb;--primary-600:#1a64d6;--header-bg:linear-gradient(180deg,#101317 0%,#0f1115 100%);}\n"
             "body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif;}\n"
             "header.ai-header{background:var(--header-bg);color:#fff;box-shadow:0 2px 12px rgba(0,0,0,0.15);position:sticky;top:0;z-index:2000;display:flex;align-items:center;justify-content:space-between;padding:10px 14px;}\n"
             "a{color:var(--primary);text-decoration:none;}a:hover{text-decoration:underline;}\n"
             "details.menu{position:relative;display:inline-block;}details.menu[open] summary::after{content:\"\";position:fixed;inset:0;}details.menu>summary::-webkit-details-marker{display:none;}\n"
             ".menu-button{display:flex;align-items:center;gap:10px;padding:6px 10px;border:1px solid rgba(255,255,255,0.15);border-radius:999px;background:rgba(255,255,255,0.06);backdrop-filter:blur(6px);}\n"
             ".menu-button .avatar{width:24px;height:24px;border-radius:50%;background:var(--panel);color:var(--fg);display:inline-flex;align-items:center;justify-content:center;font-weight:600;}\n"
             ".menu-button .label{font-size:13px;color:#fff;opacity:.95;}\n"
             ".menu-panel{position:absolute;right:0;top:120%;background:var(--panel);border:1px solid var(--border);border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,0.10);min-width:160px;overflow:visible;color:var(--fg);}\n"
             ".menu-panel a,.menu-panel form{display:block;padding:8px 10px;margin:0;}\n"
             ".theme-item{display:flex;align-items:center;gap:8px;width:100%;background:var(--panel);color:var(--fg);border:1px solid var(--border);border-radius:8px;padding:6px 8px;}\n")
            , encoding="utf-8",
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
