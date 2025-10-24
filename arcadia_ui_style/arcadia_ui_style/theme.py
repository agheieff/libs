"""Theme system with presets and dynamic switching inspired by AI Chat."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


TokenMap = Dict[str, str]


@dataclass
class Theme:
    name: str
    display_name: str
    tokens: TokenMap = field(default_factory=dict)


class ThemeManager:
    """Enhanced theme manager with preset themes and dynamic switching."""
    
    def __init__(self) -> None:
        self._themes: Dict[str, Theme] = {}
        self._register_builtin_presets()
    
    def _register_builtin_presets(self) -> None:
        """Register built-in theme presets."""
        
        # Light theme - clean, modern
        self.register_theme(
            "light",
            "Light",
            {
                "--bg": "#ffffff",
                "--fg": "#111111", 
                "--muted": "#666666",
                "--border": "#e6e6e6",
                "--panel": "#f9f9fb",
                "--primary": "#1f6feb",
                "--primary-hover": "#1a64d6",
                "--btn-fg": "#ffffff",
                "--header-bg": "linear-gradient(180deg, #101317 0%, #0f1115 100%)",
                "--header-fg": "#ffffff",
                "--header-border": "#1c2128",
                "--font-body": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
                "--font-mono": "ui-monospace, SFMono-Regular, Menlo, monospace"
            }
        )
        
        # Dark theme - GitHub/VSCode inspired
        self.register_theme(
            "dark",
            "Dark", 
            {
                "--bg": "#0d1117",
                "--fg": "#e6edf3",
                "--muted": "#9ca3af", 
                "--border": "#21262d",
                "--panel": "#161b22",
                "--primary": "#7aa2f7",
                "--primary-hover": "#6b93e6",
                "--btn-fg": "#ffffff",
                "--header-bg": "#0d1117",
                "--header-fg": "#e6edf3", 
                "--header-border": "#21262d",
                "--font-body": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
                "--font-mono": "ui-monospace, SFMono-Regular, Menlo, monospace"
            }
        )

    def register_theme(self, name: str, display_name: str, tokens: TokenMap) -> None:
        """Register a theme with name and tokens."""
        self._themes[name] = Theme(name=name, display_name=display_name, tokens=dict(tokens))

    def get(self, name: str) -> Optional[Theme]:
        """Get theme by name."""
        return self._themes.get(name)

    def names(self) -> List[str]:
        """Get all theme names."""
        return list(self._themes.keys())
    
    def get_display_name(self, name: str) -> str:
        """Get display name for a theme."""
        theme = self.get(name)
        return theme.display_name if theme else name

    def generate_css(self, default: Optional[str] = None) -> str:
        """Generate CSS with theme variables and role classes."""
        if not self._themes:
            return ""
        if default is None:
            default = next(iter(self._themes))
        base = self._themes.get(default) or next(iter(self._themes.values()))

        def _vars(tokens: TokenMap) -> str:
            return "\n".join([f"  {k}: {v};" for k, v in tokens.items()])

        out: List[str] = []
        
        # Defaults via :root
        out.append(":root{\n" + _vars(base.tokens) + "\n}")
        
        # Theme-specific overrides
        for t in self._themes.values():
            out.append(f".theme-{t.name}{{\n" + _vars(t.tokens) + "\n}")
            
        # Role classes for semantic styling
        out.extend([
            ".t-bg{background:var(--bg);}",
            ".t-fg{color:var(--fg);}",
            ".t-muted{color:var(--muted);}",
            ".t-panel{background:var(--panel);}",
            ".t-border{border-color:var(--border);}",
            ".t-border-b{border-bottom:1px solid var(--border);}",
            ".t-link{color:var(--link, var(--primary));}",
            ".t-header{background:var(--header-bg, var(--bg));color:var(--header-fg, var(--fg));border-bottom:1px solid var(--header-border, var(--border));}",
            ".t-btn{color:var(--fg);background:transparent;border:1px solid var(--border);}",
            ".t-btn-primary{background:var(--primary);border:1px solid var(--primary);color:var(--btn-fg, #fff);}",
        ])
        
        # Theme transition for smooth switching
        out.append("""
/* Theme transition */
:root {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}

/* Theme selector styles */
.tm-menu-trigger {
  width: 100%;
  background: none;
  border: none;
  text-align: left;
  padding: 8px 12px;
  font-size: 14px;
  color: var(--fg);
  cursor: pointer;
}

.tm-menu-trigger:hover {
  background: var(--border);
}

#theme-submenu {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 0.375rem;
  min-width: 180px;
  overflow: hidden;
}

.theme-item:hover {
  background: var(--border) !important;
}
""")
        
        return "\n\n".join(out) + "\n"
    
    def generate_theme_selector_js(self) -> str:
        """Return the packaged theme selector JS to keep a single source of truth.

        Note: The shipped static asset is the canonical implementation.
        This method is retained for backward compatibility and simply
        returns the contents of the packaged file. Apps should reference
        "/ui-static/theme-selector.js" directly in templates.
        """
        from importlib import resources as importlib_resources
        try:
            pkg_root = importlib_resources.files(__package__)  # type: ignore[attr-defined]
            js_path = pkg_root.joinpath("static", "theme-selector.js")
            return js_path.read_text(encoding="utf-8")
        except Exception:
            # Fallback minimal stub pointing to the static asset
            return (
                "// Theme selector is provided via static asset; include /ui-static/theme-selector.js\n"
            )
