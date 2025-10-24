
// Arcadia Theme Selector (AI Chat Style)
(function(){
  const PRESETS = {"light": {"--bg": "#ffffff", "--fg": "#111111", "--muted": "#666666", "--border": "#e6e6e6", "--panel": "#f9f9fb", "--primary": "#1f6feb", "--primary-hover": "#1a64d6", "--btn-fg": "#ffffff", "--header-bg": "linear-gradient(180deg, #101317 0%, #0f1115 100%)", "--header-fg": "#ffffff", "--header-border": "#1c2128", "--font-body": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", "--font-mono": "ui-monospace, SFMono-Regular, Menlo, monospace"}, "dark": {"--bg": "#0d1117", "--fg": "#e6edf3", "--muted": "#9ca3af", "--border": "#21262d", "--panel": "#161b22", "--primary": "#7aa2f7", "--primary-hover": "#6b93e6", "--btn-fg": "#ffffff", "--header-bg": "#0d1117", "--header-fg": "#e6edf3", "--header-border": "#21262d", "--font-body": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", "--font-mono": "ui-monospace, SFMono-Regular, Menlo, monospace"}};
  
  const DISPLAY_NAMES = {"light": "Light", "dark": "Dark"};
  
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
      button.className = 'theme-item theme-' + themeName;
      button.setAttribute('data-theme', themeName);
      button.style.cssText = 'width:100%;padding:0.5rem 0.75rem;border:none;background:var(--panel);text-align:left;cursor:pointer;font-size:14px;font-family:inherit;display:flex;align-items:center;gap:8px;color:var(--fg);';
      
      // Add margin for items after the first
      if (index > 0) {
        button.style.marginTop = '6px';
      }
      
      // Theme label
      const label = document.createElement('span');
      label.textContent = displayName;
      button.appendChild(label);
      
      // No color swatches; keep item minimal with label only
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
      button.className = 'theme-item theme-' + themeName;
      button.setAttribute('data-theme', themeName);
      // Match dropdown feel while previewing the theme variables on the item
      button.style.cssText = 'display:flex;align-items:center;gap:8px;padding:0.5rem 0.75rem;color:var(--fg);text-decoration:none;font-size:14px;font-family:inherit;background:var(--panel);border:none;width:100%;text-align:left;cursor:pointer;';
      
      // Theme label
      const label = document.createElement('span');
      label.textContent = displayName;
      button.appendChild(label);
      
      // No color swatches; minimal label-only item
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
