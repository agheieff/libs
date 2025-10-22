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
  background: var(--panel);
}

.theme-item:hover {
  background: var(--panel) !important;
}
""")
        
        return "\n\n".join(out) + "\n"
    
    def generate_theme_selector_js(self) -> str:
        """Generate JavaScript for AI Chat style theme selector."""
        import json
        return '''
// Arcadia Theme Selector (AI Chat Style)
(function(){
  const PRESETS = ''' + json.dumps({theme.name: theme.tokens for theme in self._themes.values()}) + ''';
  
  const DISPLAY_NAMES = ''' + json.dumps({theme.name: theme.display_name for theme in self._themes.values()}) + ''';
  
  function applyTheme(name) {
    console.log('=== APPLYING THEME:', name);
    console.log('Available themes:', Object.keys(PRESETS));
    
    const root = document.documentElement;
    console.log('Before - root classes:', root.className);
    
    // Remove all theme classes
    Object.keys(PRESETS).forEach(themeName => {
      console.log('Removing class: theme-' + themeName);
      root.classList.remove('theme-' + themeName);
    });
    
    // Apply new theme
    if (name !== 'light') {
      console.log('Adding class: theme-' + name);
      root.classList.add('theme-' + name);
    }
    
    // Verify CSS is working by checking computed styles
    setTimeout(() => {
      const computedBg = getComputedStyle(root).getPropertyValue('--bg');
      const computedFg = getComputedStyle(root).getPropertyValue('--fg'); 
      console.log('Applied CSS variables --bg:', computedBg.trim());
      console.log('Applied CSS variables --fg:', computedFg.trim());
      console.log('HTML classes after apply:', root.className);
    }, 100);
    
    // Store preference
    localStorage.setItem('arcadia.theme', name);
    console.log('Theme applied:', name);
    
    // Trigger theme change event
    window.dispatchEvent(new CustomEvent('arcadia:themeChanged', { detail: { theme: name } }));
  }
  
  // Add manual test function
  window.testTheme = function(name) {
    console.log('=== MANUAL THEME TEST ===');
    applyTheme(name);
  };
  
  function loadTheme() {
    const saved = localStorage.getItem('arcadia.theme') || 'light';
    applyTheme(saved);
  }
  
  function initThemeSubmenu() {
    const trigger = document.getElementById('theme-menu-trigger');
    const submenu = document.getElementById('theme-submenu');
    
    if (!trigger || !submenu) {
      console.log('Theme selector elements not found');
      return;
    }
    
    console.log('Building submenu for themes:', Object.keys(PRESETS));
    // Build theme items
    submenu.innerHTML = '';
    
    Object.keys(PRESETS).forEach((themeName, index) => {
      console.log('Creating theme item:', themeName);
      const theme = PRESETS[themeName];
      const displayName = DISPLAY_NAMES[themeName] || themeName;
      
      const button = document.createElement('button');
      button.className = 'theme-item';
      button.setAttribute('data-theme', themeName);
      button.style.cssText = 'width:100%;padding:8px 12px;border:none;background:none;text-align:left;cursor:pointer;font-size:14px;display:flex;align-items:center;gap:8px;';
      
      // Add margin for items after the first
      if (index > 0) {
        button.style.marginTop = '6px';
      }
      
      // Theme label
      const label = document.createElement('span');
      label.textContent = displayName;
      button.appendChild(label);
      
      // Theme swatches (3 colors: bg, panel, primary)
      const swatches = document.createElement('span');
      swatches.className = 'theme-swatches';
      swatches.style.cssText = 'display:flex;gap:3px;margin-left:auto;';
      
      // Create 3 swatches
      const colors = [
        theme['--bg'] || '#ffffff',
        theme['--panel'] || '#f9f9fb', 
        theme['--primary'] || '#1f6feb'
      ];
      
      colors.forEach(color => {
        const swatch = document.createElement('span');
        swatch.className = 'theme-swatch';
        swatch.style.cssText = `width:12px;height:12px;border-radius:50%;background:${color};border:1px solid var(--border);`;
        swatches.appendChild(swatch);
      });
      
      button.appendChild(swatches);
      submenu.appendChild(button);
      
      // Add click handler
      button.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Theme item clicked:', themeName);
        const selectedThemeName = button.getAttribute('data-theme');
        applyTheme(selectedThemeName);
        
        try {
          // Save to server if available
          const csrf = document.body.dataset && document.body.dataset.csrf || '';
          if (csrf) {
            fetch('/theme', { 
              method:'POST', 
              headers:{
                'Content-Type':'application/json',
                'X-CSRF-Token': csrf
              }, 
              body: JSON.stringify({ name: selectedThemeName, vars: {} }) 
            }).catch(()=>{});
          }
        } catch {}
        
        // Close submenu
        submenu.style.display = 'none';
      });
    });
    
    console.log('Submenu built with', submenu.children.length, 'items');
  }
  
  function buildThemeMenu() {
    const submenu = document.getElementById('theme-submenu');
    if (!submenu) {
      console.log('Theme submenu not found');
      return;
    }
    
    console.log('Building theme menu for themes:', Object.keys(PRESETS));
    submenu.innerHTML = '';  // Clear first (AI Chat approach)
    
    Object.keys(PRESETS).forEach((themeName, index) => {
      console.log('Creating theme item:', themeName);
      const theme = PRESETS[themeName];
      const displayName = DISPLAY_NAMES[themeName] || themeName;
      
      const button = document.createElement('button');
      button.className = 'theme-item';
      button.setAttribute('data-theme', themeName);
      
      // Copy main dropdown styling exactly
      button.style.cssText = 'display:block;padding:0.5rem 0.75rem;color:var(--fg);text-decoration:none;font-size:14px;background:none;border:none;width:100%;text-align:left;cursor:pointer;';
      
      // Theme label
      const label = document.createElement('span');
      label.textContent = displayName;
      button.appendChild(label);
      
      // Theme swatches (3 colors) - add after label
      const swatches = document.createElement('span');
      swatches.className = 'theme-swatches';
      swatches.style.cssText = 'display:flex;gap:4px;margin-left:8px;';
      
      const colors = [
        theme['--bg'] || '#ffffff',
        theme['--panel'] || '#f9f9fb', 
        theme['--primary'] || '#1f6feb'
      ];
      
      colors.forEach(color => {
        const swatch = document.createElement('span');
        swatch.className = 'theme-swatch';
        swatch.style.cssText = `width:12px;height:12px;border-radius:50%;background:${color};border:1px solid var(--border);`;
        swatches.appendChild(swatch);
      });
      
      button.appendChild(swatches);
      submenu.appendChild(button);
      
      // Add click handler
      button.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Theme item clicked:', themeName);
        const selectedThemeName = button.getAttribute('data-theme');
        applyTheme(selectedThemeName);
        
        // Close submenu immediately
        submenu.style.display = 'none';
      });
    });
    
    console.log('Theme menu built with', submenu.children.length, 'items');
  }

  function initThemeMenu() {
    const trigger = document.getElementById('theme-menu-trigger');
    const submenu = document.getElementById('theme-submenu');
    
    if (!trigger || !submenu) return;
    
    let hideTimer = null;
    
    function openMenu() {
      clearTimeout(hideTimer);
      submenu.style.display = 'block';
      buildThemeMenu(); // Build BEFORE showing (AI Chat approach)
    }
    
    function closeSoon() {
      hideTimer = setTimeout(() => {
        submenu.style.display = 'none';
      }, 150);
    }
    
    trigger.addEventListener('mouseenter', openMenu);
    trigger.addEventListener('mouseleave', closeSoon);
    
    submenu.addEventListener('mouseenter', () => {
      clearTimeout(hideTimer);
    });
    
    submenu.addEventListener('mouseleave', closeSoon);
    
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      console.log('Theme trigger clicked');
      if (submenu.style.display === 'none') {
        openMenu();
      } else {
        submenu.style.display = 'none';
      }
    });
  }
  
  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      console.log('DOM ready, initializing theme system');
      loadTheme();
      setTimeout(initThemeMenu, 100); // Small delay to ensure elements are ready
    });
  } else {
    console.log('DOM already loaded, initializing theme system');
    loadTheme();
    setTimeout(initThemeMenu, 100);
  }
  
  // Expose functions globally
  window.ArcadiaTheme = {
    applyTheme,
    loadTheme,
    themes: PRESETS,
    displayNames: DISPLAY_NAMES
  };
})();
'''
