/* Arcadia Toasts: lightweight notifications + htmx error bridge (JS-only) */
(function(){
  if (window.__arcadiaToastLoaded) return; window.__arcadiaToastLoaded = true;

  const ROOT_ID = 'ui-toast-root';
  let root = null;

  function ensureRoot(){
    root = document.getElementById(ROOT_ID);
    if (!root){
      root = document.createElement('div');
      root.id = ROOT_ID;
      root.style.position = 'fixed';
      root.style.right = '12px';
      root.style.bottom = '12px';
      root.style.display = 'flex';
      root.style.flexDirection = 'column';
      root.style.alignItems = 'flex-end';
      root.style.gap = '8px';
      root.style.zIndex = '3500';
      root.style.pointerEvents = 'none';
      document.body.appendChild(root);
    }
    return root;
  }

  function removeToast(el){
    try{ el.remove(); }catch{}
  }

  function show(kind, message, opts){
    ensureRoot();
    const options = opts || {};
    const duration = Number.isFinite(options.duration) ? Math.max(0, options.duration) : 5000;

    const el = document.createElement('div');
    el.className = 't-toast' + (kind ? (' is-' + kind) : '');
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', kind === 'error' ? 'assertive' : 'polite');
    el.tabIndex = 0;
    // Minimal inline styles; appearance driven by CSS vars
    el.style.background = 'var(--panel)';
    el.style.color = 'var(--fg)';
    el.style.border = '1px solid var(--border)';
    el.style.borderRadius = '6px';
    el.style.padding = '10px 12px';
    el.style.maxWidth = '360px';
    el.style.fontSize = '14px';
    el.style.lineHeight = '1.35';
    el.style.pointerEvents = 'auto';

    const text = document.createElement('div');
    text.textContent = String(message || ''); // sanitize
    el.appendChild(text);

    root.appendChild(el);
    if (root.childElementCount === 1){
      try{ el.focus({ preventScroll: true }); }catch{ try{ el.focus(); }catch{} }
    }

    let timerId = null;
    let remaining = duration;
    let startedAt = Date.now();

    function clear(){ if (timerId){ clearTimeout(timerId); timerId = null; } }
    function schedule(){ if (remaining > 0){ timerId = setTimeout(close, remaining); } }
    function onEnter(){ if (duration > 0){ clear(); remaining -= (Date.now() - startedAt); if (remaining < 0) remaining = 0; } }
    function onLeave(){ if (duration > 0){ startedAt = Date.now(); schedule(); } }
    function onClick(e){ e.preventDefault(); close(); }

    function close(){
      clear();
      el.removeEventListener('mouseenter', onEnter);
      el.removeEventListener('mouseleave', onLeave);
      el.removeEventListener('click', onClick);
      removeToast(el);
    }

    el.addEventListener('mouseenter', onEnter);
    el.addEventListener('mouseleave', onLeave);
    el.addEventListener('click', onClick);
    if (duration > 0) schedule();

    return { el, close };
  }

  const api = {
    show: (kind, message, opts) => show(kind, message, opts),
    info: (m, o) => show('info', m, o),
    success: (m, o) => show('success', m, o),
    warn: (m, o) => show('warn', m, o),
    error: (m, o) => show('error', m, o),
  };

  window.ArcadiaToast = api;

  // htmx error bridge (guarded)
  function onHtmxResponseError(ev){
    try{
      const d = ev.detail || {};
      const xhr = d.xhr || null;
      const status = xhr ? xhr.status : 0;
      const text = (xhr && (xhr.statusText || '')) || 'Request Error';
      const url = (d.requestConfig && d.requestConfig.path) || (xhr && xhr.responseURL) || '';
      let msg = (status ? (status + ' ') : '') + text;
      if (url) msg += ' - ' + url;
      api.error(msg);
    }catch{}
  }
  function onHtmxSendError(ev){
    let url = '';
    try{ const d = ev.detail || {}; url = (d.requestConfig && d.requestConfig.path) || ''; }catch{}
    api.error('Network error' + (url ? (' - ' + url) : ''));
  }
  function onHtmxTimeout(ev){
    let url = '';
    try{ const d = ev.detail || {}; url = (d.requestConfig && d.requestConfig.path) || ''; }catch{}
    api.error('Request timeout' + (url ? (' - ' + url) : ''));
  }

  try{
    document.addEventListener('htmx:responseError', onHtmxResponseError, true);
    document.addEventListener('htmx:sendError', onHtmxSendError, true);
    document.addEventListener('htmx:timeout', onHtmxTimeout, true);
  }catch{}
})();
