/* ArcadiaShortcuts: lightweight keyboard shortcut registry.
 * API:
 *   ArcadiaShortcuts.register({ id, title, shortcut, handler, scope? })
 *   ArcadiaShortcuts.unregister(id)
 *   ArcadiaShortcuts.setScope(scope) // current active scope string or null
 *   ArcadiaShortcuts.getActions() // list
 *   ArcadiaShortcuts.openPalette?.() // set by command-palette.js
 */
(function(){
  if (window.ArcadiaShortcuts) return;

  function isTextLike(el){
    if (!el) return false;
    const tag = (el.tagName||'').toLowerCase();
    if (tag === 'input'){
      const t = (el.type||'').toLowerCase();
      return ['text','search','email','password','url','number','tel','date','datetime-local','month','time','week'].includes(t);
    }
    return tag === 'textarea' || el.isContentEditable;
  }

  function normalizeShortcut(str){
    // Example: "Ctrl+Shift+K", "Meta+K", "?" (Shift+/)
    const s = String(str||'').trim();
    const parts = s.split('+').map(p=>p.trim()).filter(Boolean);
    let ctrl=false, meta=false, alt=false, shift=false, key='';
    parts.forEach(p=>{
      const u = p.toLowerCase();
      if (u==='ctrl' || u==='control') ctrl=true;
      else if (u==='cmd' || u==='meta' || u==='command') meta=true;
      else if (u==='alt' || u==='option') alt=true;
      else if (u==='shift') shift=true;
      else key = p;
    });
    if (!key && s === '?'){ shift = true; key = '/'; }
    return { ctrl, meta, alt, shift, key: key.toLowerCase() };
  }

  function eventSig(e){
    const k = (e.key||'').toLowerCase();
    return { ctrl: !!e.ctrlKey, meta: !!e.metaKey, alt: !!e.altKey, shift: !!e.shiftKey, key: k };
  }

  function sigEq(a,b){
    return a.ctrl===b.ctrl && a.meta===b.meta && a.alt===b.alt && a.shift===b.shift && a.key===b.key;
  }

  const actions = new Map(); // id -> {id,title,shortcut,handler,scope,sig}
  let currentScope = null; // string or null

  function register(def){
    if (!def || !def.id || !def.handler) return;
    const sig = normalizeShortcut(def.shortcut||'');
    const act = { id: String(def.id), title: String(def.title||def.id), shortcut: def.shortcut||'', handler: def.handler, scope: def.scope||null, sig };
    actions.set(act.id, act);
    return act.id;
  }

  function unregister(id){ actions.delete(String(id)); }
  function setScope(scope){ currentScope = scope ? String(scope) : null; }

  function getActions(){ return Array.from(actions.values()); }

  function matchActions(eSig){
    const list = [];
    actions.forEach(a=>{ if (a.shortcut && sigEq(a.sig, eSig)) list.push(a); });
    return list;
  }

  document.addEventListener('keydown', function(e){
    // Skip when typing in inputs unless explicit alt/meta/ctrl used
    const active = document.activeElement;
    const inText = isTextLike(active);
    const usesMod = e.ctrlKey || e.metaKey || e.altKey;
    if (inText && !usesMod) return;

    const sig = eventSig(e);
    const matched = matchActions(sig);
    if (!matched.length) return;

    // Prefer actions in current scope
    let chosen = matched.find(a=>a.scope && currentScope && a.scope===currentScope) || matched[0];
    try{
      const res = chosen.handler(e) ;
      if (res !== false) e.preventDefault();
    }catch{}
  }, true);

  window.ArcadiaShortcuts = {
    register, unregister, setScope, getActions,
    openPalette: null
  };
})();
