from __future__ import annotations

from pathlib import Path
from typing import Tuple


_HEADER_SENTINEL = "<!-- arcadia-ui-style:v1 -->"


def _ensure_dirs(app_dir: str) -> Tuple[Path, Path]:
    tdir = Path(app_dir) / "templates"
    sdir = Path(app_dir) / "static"
    tdir.mkdir(parents=True, exist_ok=True)
    sdir.mkdir(parents=True, exist_ok=True)
    return tdir, sdir


def _should_rewrite(path: Path, sentinel: str) -> bool:
    if not path.exists():
        return True
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return True
    return sentinel not in content


def _write_header(tdir: Path) -> None:
    header = tdir / "_header.html"
    if not _should_rewrite(header, _HEADER_SENTINEL):
        return
    header.write_text(
        f"""
{_HEADER_SENTINEL}
<link rel=\"stylesheet\" href=\"/ui-static/arcadia_theme.css\">\n
<!-- Shared application header -->
<style>
  /* Sticky footer layout: header + content + footer; footer stays at bottom on short pages */
  html, body {{ height: 100%; }}
  body {{ min-height: 100vh; display: flex; flex-direction: column; }}
  #arcadia-content {{ flex: 1 0 auto; }}
  :root {{ scrollbar-gutter: stable; }}
  .tm-header, .tm-header *, .tm-header *::before, .tm-header *::after {{ box-sizing: border-box; }}
  .tm-header {{ background:var(--header-bg, var(--bg)); color:var(--header-fg, var(--fg)); border-bottom:1px solid var(--header-border, var(--border)); font-family: system-ui, -apple-system, Segoe UI, Roboto, \"Helvetica Neue\", Arial, \"Noto Sans\", \"Liberation Sans\", sans-serif; font-size:14px; line-height:1.25; }}
  .tm-header .tm-container {{ max-width:1200px; margin:0 auto; padding:0.75rem 1rem; display:flex; align-items:center; justify-content:space-between; }}
  @media (min-width: 640px){{ .tm-header .tm-container {{ min-height:56px; }} }}
  .tm-header .tm-brand {{ color:var(--header-fg, var(--fg)); font-weight:600; text-decoration:none; letter-spacing:0.2px; font-size:18px; }}
  .tm-header .tm-nav a {{ color:var(--link-muted); text-decoration:none; margin-left:1rem; font-size:14px; }}
  .tm-header .tm-nav a:hover {{ color:var(--link); }}
  .tm-right {{ display:flex; align-items:center; gap:1rem; }}
  .tm-actions .tm-btn {{ padding:0.35rem 0.75rem; border:1px solid var(--header-border, var(--border)); border-radius:0.375rem; color:var(--header-fg, var(--fg)); text-decoration:none; font-size:14px; background:transparent; }}
  .tm-actions .tm-btn:hover {{ background:transparent; }}
  .tm-actions .tm-primary {{ border-color:var(--primary); background:var(--primary); color:var(--btn-fg, #fff); }}
  .tm-user {{ position:relative; }}
  .tm-user-btn {{ padding:0.35rem 0.75rem; border:1px solid var(--header-border, var(--border)); border-radius:0.375rem; color:var(--header-fg, var(--fg)); background:transparent; cursor:pointer; font-size:14px; }}
  .tm-user-menu {{ position:absolute; right:0; top:2.25rem; background:var(--panel); border:1px solid var(--border); border-radius:0.375rem; min-width:180px; display:none; z-index:50; }}
  .tm-user:focus-within .tm-user-menu {{ display:block; }}
  .tm-user-menu a {{ display:block; padding:0.5rem 0.75rem; color:var(--fg); text-decoration:none; font-size:14px; }}
  .tm-user-menu a:hover {{ background:var(--border); }}
  .tm-divider {{ width:1px; height:18px; background:var(--border); margin:0 0.5rem; }}
  .tm-nav a.active {{ color:var(--fg); }}
  .tm-brand small {{ color:var(--muted); font-weight:400; font-size:12px; margin-left:6px; }}
  .tm-flex {{ display:flex; align-items:center; gap:.75rem; }}
  .tm-nav {{ display:flex; align-items:center; }}
  @media (max-width: 640px){{ .tm-nav a {{ margin-left:.5rem; }} }}
  .tm-link {{ color:#9ca3af; }}
  .tm-link:hover {{ color:#f9fafb; }}
  .tm-hidden {{ display:none; }}
  .tm-show {{ display:block; }}
  .tm-menu-right {{ position:relative; }}
  .tm-user-menu hr {{ border:none; border-top:1px solid #1f2937; margin:4px 0; }}
</style>
<header class=\"tm-header t-header\">\n  <div class=\"tm-container\">\n    <a class=\"tm-brand\" href=\"{{ brand_home_url or '/' }}\">\n      {% if brand_logo_url %}<img src=\"{{ brand_logo_url }}\" alt=\"logo\" style=\"height:22px;vertical-align:middle;margin-right:8px;\"/>{% endif %}\n      {{ brand_name or 'Project Name' }}<small>{{ brand_tag or '' }}</small>\n    </a>\n    <div class=\"tm-right\"> \n      {% set _nav = nav_items if (nav_items is defined) else [] %}\n      {% if _nav and _nav|length > 0 %}\n        <nav class=\"tm-nav\" aria-label=\"Primary\"> \n          {% for it in _nav %}\n            <a href=\"{{ it.href }}\" class=\"tm-link{% if it.active %} active{% endif %}\">{{ it.label }}</a>\n          {% endfor %}\n        </nav>\n      {% endif %}\n      {% if request and request.state and request.state.user %} \n        <div class=\"tm-user\" id=\"tm-user\">\n          <button class=\"tm-user-btn\" id=\"tm-user-btn\">Account ▾</button>\n          <div class=\"tm-user-menu\" id=\"tm-user-menu\">\n            <button class=\"tm-menu-trigger\" id=\"theme-menu-trigger\">Theme</button>\n            <div id=\"theme-submenu\" style=\"display:none; position:absolute; right: 100%; top: 0; z-index: 3000;\"></div>\n            <a href=\"/profile\">Profile</a>\n            <a href=\"/settings\">Settings</a>\n            <hr />\n            <a href=\"/auth/logout\">Log out</a>\n          </div>\n        </div>\n      {% else %}\n        <div class=\"tm-actions\">\n          <a href=\"/login\" class=\"tm-btn\">Log in</a>\n          <a href=\"/signup\" class=\"tm-btn tm-primary\">Sign up</a>\n        </div>\n      {% endif %}\n    </div>\n  </div>\n</header>
<!-- Dropdown uses CSS :focus-within; no JS needed -->
<script src=\"/ui-static/theme-selector.js\"></script>
{% set __persist = persist_header if persist_header is defined else true %}
{% if __persist %}
<script src=\"https://unpkg.com/htmx.org@1.9.12\" integrity=\"sha384-+bVsx3b8QdE7cO1S4oFQ9hQ1TImfQxWqS4LzJd8j3jL5uFQw8L7f3NfL2hJdJg9w\" crossorigin=\"anonymous\"></script>
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
<!-- App-neutral UI re-init event; apps can hook `ui:reinit` to (re)initialize features -->
<script>
(function(){
  try{
    function fire(){
      try{ window.dispatchEvent(new CustomEvent('ui:reinit')); }catch(e){}
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fire, { once: true });
    } else {
      fire();
    }
    try{ document.body.addEventListener('htmx:afterSwap', fire); }catch(e){}
    document.addEventListener('visibilitychange', function(){ if(document.visibilityState==='visible') fire(); });
  }catch(e){}
})();
</script>
{% endif %}
        """,
        encoding="utf-8",
    )


def _ensure_theme_assets(sdir: Path) -> None:
    theme_css = sdir / "arcadia_theme.css"
    regen_theme = False
    if theme_css.exists():
        try:
            _tc = theme_css.read_text(encoding="utf-8", errors="ignore")
            if "--header-fg" not in _tc or ".theme-light" not in _tc:
                regen_theme = True
        except Exception:
            regen_theme = True
    else:
        regen_theme = True

    if regen_theme:
        from .theme import ThemeManager as NewThemeManager
        tm = NewThemeManager()
        theme_css.write_text(tm.generate_css(default="light"), encoding="utf-8")


def _write_footer(tdir: Path) -> None:
    footer = tdir / "_footer.html"
    if not footer.exists():
        footer.write_text(
            """<footer style=\"margin-top:auto;padding:12px;border-top:1px solid #eee;color:#888\">© Arcadia</footer>\n""",
            encoding="utf-8",
        )


def _write_legacy_base_css(sdir: Path) -> None:
    css = sdir / "arcadia.css"
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
             ".theme-item{display:flex;align-items:center;gap:8px;width:100%;background:var(--panel);color:var(--fg);border:1px solid var(--border);border-radius:8px;}\n")
            , encoding="utf-8",
        )


def _write_auth_dialog(tdir: Path) -> None:
    auth = tdir / "_auth.html"
    if not auth.exists():
        auth.write_text(
            """
<dialog id=\"authdlg\">\n  <form method=\"dialog\" style=\"min-width:340px\">\n    <h3 style=\"margin:0 0 8px\">Sign in</h3>\n    <div style=\"display:flex;flex-direction:column;gap:8px\">\n      <input id=\"email\" placeholder=\"you@example.com\" />\n      <input id=\"password\" type=\"password\" placeholder=\"password\" />\n      <div style=\"display:flex;gap:8px;justify-content:flex-end\">\n        <button id=\"register\" value=\"register\">Sign up</button>\n        <button id=\"login\" value=\"login\">Login</button>\n        <button value=\"cancel\">Cancel</button>\n      </div>\n    </div>\n  </form>\n</dialog>
            """,
            encoding="utf-8",
        )


def _write_login_signup(tdir: Path) -> None:
    login = tdir / "login.html"
    signup = tdir / "signup.html"
    if not login.exists():
        login.write_text(
            """<!DOCTYPE html>
<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Log in - Arcadia</title>\n    <script src=\"https://cdn.tailwindcss.com\"></script>\n</head>\n<body class=\"bg-gray-100 min-h-screen\" style=\"margin:0;\">\n    {% include \"_header.html\" ignore missing %}\n    <div id=\"arcadia-content\">\n    <div class=\"max-w-md mx-auto mt-12 bg-white shadow p-6 rounded\">\n        <h1 class=\"text-2xl font-semibold mb-4\">Log in</h1>\n        <form id=\"login-form\" class=\"space-y-4\" onsubmit=\"return false;\">\n            <div>\n                <label class=\"block text-sm mb-1\">Email</label>\n                <input id=\"email\" type=\"email\" class=\"w-full border rounded p-2\" required />\n            </div>\n            <div>\n                <label class=\"block text-sm mb-1\">Password</label>\n                <input id=\"password\" type=\"password\" class=\"w-full border rounded p-2\" required />\n            </div>\n            <button id=\"login-btn\" class=\"w-full bg-blue-600 text-white py-2 rounded\">Log in</button>\n            <p id=\"login-error\" class=\"text-sm text-red-600 mt-2\" style=\"display:none;\"></p>\n        </form>\n    </div>\n    <script>\n    function extractErrorMessage(data, fallback) {\n        if (!data) return fallback;\n        const d = data.detail;\n        if (typeof d === 'string') return d;\n        if (Array.isArray(d) && d.length) {\n            const first = d[0] || {};\n            const loc = first.loc || [];\n            if (loc.includes('password')) return 'Password must be at least 8 characters.';\n            if (loc.includes('email')) return 'Please enter a valid email address.';\n            return first.msg || fallback;\n        }\n        return fallback;\n    }\n    document.getElementById('login-btn').addEventListener('click', async () => {\n        const email = (document.getElementById('email').value || '').trim();\n        const password = document.getElementById('password').value || '';\n        const err = document.getElementById('login-error');\n        err.style.display = 'none';\n        try {\n            const res = await fetch('/auth/login', {\n                method: 'POST', headers: {'Content-Type': 'application/json'},\n                body: JSON.stringify({ email, password })\n            });\n            if (!res.ok) {\n                const d = await res.json().catch(()=>null);\n                throw new Error(extractErrorMessage(d, 'Login failed'));\n            }\n            const data = await res.json();\n            try {\n                document.cookie = `access_token=${data.access_token}; Path=/; SameSite=Lax`;\n            } catch {}\n            window.location.href = '/';\n        } catch (e) {\n            err.textContent = e.message || 'Login failed';\n            err.style.display = 'block';\n        }\n    });\n    </script>\n</div>\n</body>\n</html>\n""",
            encoding="utf-8",
        )
    if not signup.exists():
        signup.write_text(
            """<!DOCTYPE html>
<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Sign up - Arcadia</title>\n    <script src=\"https://cdn.tailwindcss.com\"></script>\n    <style>.hint{font-size:.85rem;color:#6b7280}</style>\n</head>\n<body class=\"bg-gray-100 min-h-screen\" style=\"margin:0;\">\n    {% include \"_header.html\" ignore missing %}\n    <div id=\"arcadia-content\">\n    <div class=\"max-w-md mx-auto mt-12 bg-white shadow p-6 rounded\">\n        <h1 class=\"text-2xl font-semibold mb-4\">Create your account</h1>\n        <form id=\"signup-form\" class=\"space-y-4\" onsubmit=\"return false;\">\n            <div>\n                <label class=\"block text-sm mb-1\">Email</label>\n                <input id=\"email\" type=\"email\" class=\"w-full border rounded p-2\" required />\n            </div>\n            <div>\n                <label class=\"block text-sm mb-1\">Password</label>\n                <input id=\"password\" type=\"password\" class=\"w-full border rounded p-2\" required />\n                <div class=\"hint\">At least 8 characters</div>\n            </div>\n            <button id=\"signup-btn\" class=\"w-full bg-blue-600 text-white py-2 rounded\">Sign up</button>\n            <p id=\"signup-error\" class=\"text-sm text-red-600 mt-2\" style=\"display:none;\"></p>\n        </form>\n    </div>\n    <script>\n    function extractErrorMessage(data, fallback) {\n        if (!data) return fallback;\n        const d = data.detail;\n        if (typeof d === 'string') return d;\n        if (Array.isArray(d) && d.length) {\n            const first = d[0] || {};\n            const loc = first.loc || [];\n            if (loc.includes('password')) return 'Password must be at least 8 characters.';\n            if (loc.includes('email')) return 'Please enter a valid email address.';\n            return first.msg || fallback;\n        }\n        return fallback;\n    }\n    document.getElementById('signup-btn').addEventListener('click', async () => {\n        const email = (document.getElementById('email').value || '').trim();\n        const password = document.getElementById('password').value || '';\n        const err = document.getElementById('signup-error');\n        err.style.display = 'none';\n        try {\n            const res = await fetch('/auth/register', {\n                method: 'POST', headers: {'Content-Type': 'application/json'},\n                body: JSON.stringify({ email, password })\n            });\n            if (!res.ok) {\n                const d = await res.json().catch(()=>null);\n                throw new Error(extractErrorMessage(d, 'Sign up failed'));\n            }\n            const res2 = await fetch('/auth/login', {\n                method: 'POST', headers: {'Content-Type': 'application/json'},\n                body: JSON.stringify({ email, password })\n            });\n            if (!res2.ok) {\n                const d2 = await res2.json().catch(()=>null);\n                throw new Error(extractErrorMessage(d2, 'Login failed'));\n            }\n            const data = await res2.json();\n            try {\n                document.cookie = `access_token=${data.access_token}; Path=/; SameSite=Lax`;\n            } catch {}\n            window.location.href = '/';\n        } catch (e) {\n            err.textContent = e.message || 'Sign up failed';\n            err.style.display = 'block';\n        }\n    });\n    </script>\n    \n</div>\n</body>\n</html>\n""",
            encoding="utf-8",
        )


def _write_settings_panel(tdir: Path) -> None:
    settings_panel = tdir / "_settings.html"
    if not settings_panel.exists():
        settings_panel.write_text(
            """
<div id=\"ui-settings\" data-mode=\"{{ settings_mode or (settings_schema.mode if settings_schema and settings_schema.mode else 'immediate') }}\">\n  {% set schema = (settings_schema or ui_settings_schema) or {} %}\n  {% set fields = schema.fields if schema and schema.fields else [] %}\n  {% set status_id = schema.status_id if schema and schema.status_id else 'ui-settings-status' %}\n  <div id=\"{{ status_id }}\" class=\"ui-settings-status\" style=\"margin:8px 0;color:#555\"></div>\n  <div class=\"ui-settings-body\">\n    {% for f in fields %}\n      <div class=\"ui-field\" data-field=\"{{ f.id }}\" data-save-path=\"{{ f.save_path or schema.save_path or '' }}\" data-save-method=\"{{ f.save_method or schema.save_method or 'POST' }}\" data-group=\"{{ f.group or '' }}\">\n        {% if f.type == 'select' %}\n          <label>{{ f.label }}\n            <select id=\"ui-f-{{ f.id }}\">\n              {% for opt in f.options or [] %}\n                <option value=\"{{ opt.value }}\" {% if opt.value == f.value %}selected{% endif %}>{{ opt.label or opt.value }}</option>\n              {% endfor %}\n            </select>\n          </label>\n        {% elif f.type == 'checkbox' %}\n          <label><input type=\"checkbox\" id=\"ui-f-{{ f.id }}\" {% if f.value %}checked{% endif %}/> {{ f.label }}</label>\n        {% else %}\n          <label>{{ f.label }} <input type=\"text\" id=\"ui-f-{{ f.id }}\" value=\"{{ f.value or '' }}\"/></label>\n        {% endif %}\n      </div>\n    {% endfor %}\n  </div>\n  {% if (settings_mode or (schema.mode if schema and schema.mode else None)) == 'manual' %}\n    <div style=\"margin-top:10px\"><button id=\"ui-settings-save\">Save</button></div>\n  {% endif %}\n</div>\n<script>\n(function(){\n  try{\n    const root=document.getElementById('ui-settings'); if(!root) return;\n    const mode=root.dataset.mode||'immediate';\n    const status=document.getElementById('{{ status_id }}');\n    function setStatus(ok,msg){ if(status){ status.textContent=msg||(ok?'Saved':'Error'); status.style.color=ok?'#055':'#700'; status.style.background=ok?'#e6ffed':'#ffeaea'; status.style.border='1px solid '+(ok?'#b7f5c7':'#ffb3b3'); status.style.padding='6px 8px'; status.style.borderRadius='4px'; }\n      try{ window.dispatchEvent(new CustomEvent('ui-settings-status',{detail:{ok:!!ok,message:msg||''}})); }catch(e){}\n    }\n    function collect(onlyId){ const data={}; const grouped={}; const fields=root.querySelectorAll('.ui-field'); fields.forEach(function(w){ const id=w.getAttribute('data-field'); if(!id|| (onlyId && onlyId!==id)) return; const group=(w.getAttribute('data-group')||'').trim(); const input=w.querySelector('select, input[type=text], input[type=checkbox]'); if(!input) return; let val; if(input.tagName==='SELECT') val=input.value; else if(input.type==='checkbox') val=input.checked; else val=input.value; if(group){ grouped[group]=grouped[group]||{}; grouped[group][id]=val; } else { data[id]=val; } }); for(const k in grouped){ data[k]=grouped[k]; } return data; }\n    async function saveOne(id){ const el=root.querySelector('.ui-field[data-field=\"'+id+'\"]'); if(!el) return; const path=el.getAttribute('data-save-path')||'{{ schema.save_path or '' }}'; const method=el.getAttribute('data-save-method')||'{{ schema.save_method or 'POST' }}'; if(!path){ setStatus(false,'No save_path configured'); return; } const payload=collect(id); try{ const res=await fetch(path,{method:method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}); const ok=res.ok; let msg= ok?'Saved':'Save failed'; try{ const t=await res.text(); const j=JSON.parse(t); msg=j.detail||(ok?'Saved':'Error'); }catch{} setStatus(ok,msg);}catch(e){ setStatus(false,'Network error'); } }\n    function bind(){ const fields=root.querySelectorAll('.ui-field'); fields.forEach(function(w){ const id=w.getAttribute('data-field'); const input=w.querySelector('select, input[type=text], input[type=checkbox]'); if(!input||!id) return; if(mode==='immediate'){ input.addEventListener('change', function(){ saveOne(id); }); } }); const btn=document.getElementById('ui-settings-save'); if(btn){ btn.addEventListener('click', async function(){ const path='{{ schema.save_path or '' }}'; const method='{{ schema.save_method or 'POST' }}'; if(!path){ setStatus(false,'No save_path configured'); return; } const payload=collect(null); try{ const res=await fetch(path,{method:method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}); const ok=res.ok; let msg= ok?'Saved':'Save failed'; try{ const t=await res.text(); const j=JSON.parse(t); msg=j.detail||(ok?'Saved':'Error'); }catch{} setStatus(ok,msg);}catch(e){ setStatus(false,'Network error'); } }); } }\n    bind();\n  }catch(e){}\n})();\n</script>
            """,
            encoding="utf-8",
        )


def _write_user_menu(tdir: Path) -> None:
    user_menu_tpl = tdir / "_user_menu.html"
    if not user_menu_tpl.exists():
        user_menu_tpl.write_text(
            """
<div class=\"tm-user\" id=\"tm-user\">\n  <button class=\"tm-user-btn t-btn\" id=\"tm-user-btn\">Account ▾</button>\n  <div class=\"tm-user-menu t-panel t-border\" id=\"tm-user-menu\">\n    {% set _items = (user_menu_items or []) %}\n    {% for it in _items %}\n      {% if it.divider %}<hr />{% else %}<a class=\"t-fg\" href=\"{{ it.href }}\">{{ it.label }}</a>{% endif %}\n    {% endfor %}\n  </div>\n</div>\n            """,
            encoding="utf-8",
        )


def ensure_templates(app_dir: str) -> str:
    """Ensure default templates/static assets and return templates dir path."""
    tdir, sdir = _ensure_dirs(app_dir)
    _write_header(tdir)
    _ensure_theme_assets(sdir)
    _write_footer(tdir)
    _write_legacy_base_css(sdir)
    _write_auth_dialog(tdir)
    _write_login_signup(tdir)
    _write_settings_panel(tdir)
    _write_user_menu(tdir)
    return str(tdir)
