/* Arcadia Command Palette: depends on ArcadiaShortcuts. */
(function(){
  if (window.__arcadiaCmdPaletteLoaded) return; window.__arcadiaCmdPaletteLoaded = true;

  const SCROLL_ITEM_CLASS = 't-cmd-item';
  const ROOT_ID = 'ui-cmd-root';
  let root = null, wrap = null, inputEl = null, listEl = null, visible = false, items = [], idx = 0;

  function ensureRoot(){
    root = document.getElementById(ROOT_ID);
    if (!root){
      root = document.createElement('div');
      root.id = ROOT_ID;
      root.style.position = 'fixed';
      root.style.inset = '0';
      root.style.zIndex = '4000';
      root.style.display = 'none';
      root.style.background = 'rgba(0,0,0,0.35)';
      root.setAttribute('aria-hidden','true');
      document.body.appendChild(root);

      wrap = document.createElement('div');
      wrap.style.position = 'absolute';
      wrap.style.left = '50%';
      wrap.style.top = '15%';
      wrap.style.transform = 'translateX(-50%)';
      wrap.style.background = 'var(--panel)';
      wrap.style.color = 'var(--fg)';
      wrap.style.border = '1px solid var(--border)';
      wrap.style.borderRadius = '8px';
      wrap.style.minWidth = '520px';
      wrap.style.maxWidth = '80vw';
      wrap.style.boxShadow = '0 10px 30px rgba(0,0,0,0.2)';
      root.appendChild(wrap);

      const header = document.createElement('div');
      header.style.padding = '10px';
      wrap.appendChild(header);

      inputEl = document.createElement('input');
      inputEl.type = 'text';
      inputEl.placeholder = 'Type a command…';
      inputEl.style.width = '100%';
      inputEl.style.padding = '10px';
      inputEl.style.border = '1px solid var(--border)';
      inputEl.style.borderRadius = '6px';
      inputEl.style.background = 'var(--panel)';
      inputEl.style.color = 'var(--fg)';
      header.appendChild(inputEl);

      listEl = document.createElement('div');
      listEl.style.maxHeight = '50vh';
      listEl.style.overflow = 'auto';
      listEl.style.padding = '8px';
      wrap.appendChild(listEl);
    }
  }

  function close(){
    visible = false;
    if (root){ root.style.display='none'; root.setAttribute('aria-hidden','true'); }
    items = []; listEl && (listEl.innerHTML = '');
    document.removeEventListener('keydown', onKeyDown, true);
  }

  function onKeyDown(e){
    if (!visible) return;
    if (e.key === 'Escape'){ e.preventDefault(); close(); return; }
    if (e.key === 'ArrowDown'){ e.preventDefault(); setIdx(idx+1); return; }
    if (e.key === 'ArrowUp'){ e.preventDefault(); setIdx(idx-1); return; }
    if (e.key === 'Enter'){ e.preventDefault(); activateIdx(idx); return; }
  }

  function setIdx(i){
    if (!items.length) { idx = 0; return; }
    idx = (i + items.length) % items.length;
    const nodes = listEl.querySelectorAll('.'+SCROLL_ITEM_CLASS);
    nodes.forEach((n, j)=>{ n.style.background = (j===idx? 'var(--border)' : 'transparent'); });
    const current = nodes[idx]; if (current){ current.scrollIntoView({ block: 'nearest' }); }
  }

  function activateIdx(i){
    if (!items.length) return;
    const it = items[(i + items.length) % items.length];
    close();
    try { it.handler({ from: 'palette' }); } catch {}
  }

  function render(){
    listEl.innerHTML = '';
    items.forEach((it, i)=>{
      const row = document.createElement('div');
      row.className = SCROLL_ITEM_CLASS;
      row.style.display = 'flex';
      row.style.alignItems = 'center';
      row.style.justifyContent = 'space-between';
      row.style.padding = '8px 10px';
      row.style.cursor = 'pointer';
      row.addEventListener('click', ()=>{ activateIdx(i); });

      const title = document.createElement('div');
      title.textContent = it.title || it.id;
      row.appendChild(title);

      const kbd = document.createElement('div');
      kbd.style.opacity = '0.7';
      kbd.style.fontSize = '12px';
      kbd.textContent = it.shortcut || '';
      row.appendChild(kbd);

      listEl.appendChild(row);
    });
    setIdx(0);
  }

  function fuzzy(q, hay){
    if (!q) return true; // show all
    q = q.toLowerCase(); hay = (hay||'').toLowerCase();
    // simple subsequence match
    let i=0; for (let c of q){ i = hay.indexOf(c, i); if (i<0) return false; i++; }
    return true;
  }

  function open(){
    ensureRoot();
    const acts = (window.ArcadiaShortcuts && window.ArcadiaShortcuts.getActions) ? window.ArcadiaShortcuts.getActions() : [];
    items = acts.slice();
    visible = true;
    root.style.display = 'block';
    root.setAttribute('aria-hidden','false');
    inputEl.value = '';
    render();
    inputEl.focus();
    document.addEventListener('keydown', onKeyDown, true);
  }

  function filter(){
    const q = inputEl.value||'';
    const acts = (window.ArcadiaShortcuts && window.ArcadiaShortcuts.getActions) ? window.ArcadiaShortcuts.getActions() : [];
    const scope = (window.ArcadiaShortcuts && window.ArcadiaShortcuts._scope) || null;
    items = acts.filter(a=> fuzzy(q, a.title||a.id) || fuzzy(q, a.id));
    render();
  }

  document.addEventListener('click', function(e){ if (visible && root && !wrap.contains(e.target)) close(); }, true);
  document.addEventListener('input', function(e){ if (e.target === inputEl) filter(); }, true);

  // Bind Ctrl/Cmd+K to open
  document.addEventListener('keydown', function(e){
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && (e.key||'').toLowerCase()==='k'){
      // Ignore when typing in text inputs
      const el = document.activeElement; const isEditable = el && ((el.tagName||'').toLowerCase()==='input' || (el.tagName||'').toLowerCase()==='textarea' || el.isContentEditable);
      if (isEditable) return;
      e.preventDefault(); open();
    }
  }, true);

  window.ArcadiaShortcuts = window.ArcadiaShortcuts || {};
  window.ArcadiaShortcuts.openPalette = open;
})();
