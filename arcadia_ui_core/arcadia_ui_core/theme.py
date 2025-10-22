from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


TokenMap = Dict[str, str]


@dataclass
class Theme:
    name: str
    tokens: TokenMap = field(default_factory=dict)


class ThemeManager:
    """Simple theme registry and CSS generator.

    - register_theme(name, tokens): tokens is a mapping of semantic keys to CSS color/font values.
    - generate_css(default): returns CSS with :root variables and .theme-<name> variable overrides
      plus a small set of role classes that use those variables.
    """

    def __init__(self) -> None:
        self._themes: Dict[str, Theme] = {}

    def register_theme(self, name: str, tokens: TokenMap) -> None:
        self._themes[name] = Theme(name=name, tokens=dict(tokens))

    def get(self, name: str) -> Optional[Theme]:
        return self._themes.get(name)

    def names(self) -> list[str]:
        return list(self._themes.keys())

    def generate_css(self, default: Optional[str] = None) -> str:
        if not self._themes:
            return ""
        if default is None:
            default = next(iter(self._themes))
        base = self._themes.get(default) or next(iter(self._themes.values()))

        def _vars(tokens: TokenMap) -> str:
            return "\n".join([f"  --{k}: {v};" for k, v in tokens.items()])

        out: list[str] = []
        # Defaults via :root
        out.append(":root{\n" + _vars(base.tokens) + "\n}")
        # Theme-specific overrides
        for t in self._themes.values():
            out.append(f".theme-{t.name}{{\n" + _vars(t.tokens) + "\n}")
        # Role classes (elements declare semantic role, theme provides variables)
        out.append(
            "\n".join(
                [
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
                ]
            )
        )
        return "\n\n".join(out) + "\n"
