/* Lightweight context-menu client for Arcadia UI Core.
 * Activates on elements with data-cm="<name>".
 * Requests menu HTML from /ui/context-menu and renders a floating menu.
 */
(function(){
  if (window.__arcadiaContextMenuLoaded) return; window.__arcadiaContextMenuLoaded = true;

  const ROOT_ID = 'ui-cm-root';
  let root = null; let openMenu = null;

  function ensureRoot(){
    root = document.getElementById(ROOT_ID);
    if (!root){
      root = document.createElement('div');
      root.id = ROOT_ID;
      root.style.position = 'fixed';
      root.style.zIndex = '3000';
      root.style.inset = '0 auto auto 0';
      root.style.pointerEvents = 'none';
      document.body.appendChild(root);
    }
  }

  function hide(){
    if (openMenu){
      try{ window.dispatchEvent(new CustomEvent('ui:cm:hide')); }catch{}
      openMenu.remove();
      openMenu = null;
    }
    if (root) root.style.pointerEvents = 'none';
    removeDocListeners();
  }

  function onDocKey(e){
    if (!openMenu) return;
    const items = Array.from(openMenu.querySelectorAll('.t-cm-item:not(.is-disabled)'));
    const idx = items.indexOf(document.activeElement);
    if (e.key === 'Escape'){ hide(); return; }
    if (e.key === 'ArrowDown'){
      e.preventDefault();
      const n = items[(idx + 1 + items.length) % items.length]; if (n) n.focus();
    }
    if (e.key === 'ArrowUp'){
      e.preventDefault();
      const n = items[(idx - 1 + items.length) % items.length]; if (n) n.focus();
    }
  }

  function onDocClick(e){
    if (!openMenu) return;
    if (!openMenu.contains(e.target)) hide();
  }

  function onDocScrollOrResize(){ hide(); }

  function addDocListeners(){
    document.addEventListener('keydown', onDocKey, true);
    document.addEventListener('click', onDocClick, true);
    window.addEventListener('scroll', onDocScrollOrResize, true);
    window.addEventListener('resize', onDocScrollOrResize, true);
    try{ document.body.addEventListener('htmx:afterSwap', hide, true); }catch{}
  }

  function removeDocListeners(){
    document.removeEventListener('keydown', onDocKey, true);
    document.removeEventListener('click', onDocClick, true);
    window.removeEventListener('scroll', onDocScrollOrResize, true);
    window.removeEventListener('resize', onDocScrollOrResize, true);
    try{ document.body.removeEventListener('htmx:afterSwap', hide, true); }catch{}
  }

  async function fetchMenu(name, payload){
    try{ window.dispatchEvent(new CustomEvent('ui:cm:beforefetch', { detail: { name, payload } })); }catch{}
    const headers = { 'X-CM-Dataset': btoa(JSON.stringify(payload.dataset || {})) };
    if (payload.selection) headers['X-CM-Selection'] = payload.selection;
    const qp = new URLSearchParams(); qp.set('name', name);
    if (payload.path) qp.set('path', payload.path);
    if (payload.element_id) qp.set('element_id', payload.element_id);
    const res = await fetch('/ui/context-menu?' + qp.toString(), { headers });
    if (!res.ok) return null;
    const html = await res.text();
    return (html && html.trim().length) ? html : null;
  }

  function showAt(html, x, y){
    ensureRoot(); hide();
    root.style.pointerEvents = 'auto';
    const wrap = document.createElement('div');
    wrap.style.position = 'fixed';
    wrap.style.left = x + 'px';
    wrap.style.top = y + 'px';
    wrap.style.maxWidth = '50vw';
    wrap.style.pointerEvents = 'auto';
    wrap.innerHTML = html;
    root.appendChild(wrap);
    openMenu = wrap.querySelector('.t-cm') || wrap.firstElementChild;
    try{ window.dispatchEvent(new CustomEvent('ui:cm:show', { detail: { menu: openMenu } })); }catch{}
    // Focus first item
    const first = openMenu && openMenu.querySelector('.t-cm-item:not(.is-disabled)');
    if (first) first.focus();
    addDocListeners();
  }

  function collectDataset(el){
    const ds = {};
    for (const k in el.dataset){ if (k !== 'cm') ds[k] = String(el.dataset[k]); }
    return ds;
  }

  document.addEventListener('contextmenu', async function(e){
    const t = e.target && (e.target.closest ? e.target.closest('[data-cm]') : null);
    if (!t) return; // Let browser default
    const name = t.getAttribute('data-cm');
    if (!name) return;
    const selection = (window.getSelection && window.getSelection().toString()) || '';
    const payload = {
      dataset: collectDataset(t),
      selection: selection || undefined,
      path: location.pathname,
      element_id: t.id || undefined,
    };
    const html = await fetchMenu(name, payload);
    if (html){
      e.preventDefault();
      showAt(html, e.clientX, e.clientY);
    }
  }, true);
})();
