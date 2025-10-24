/* ActiveProfile: maintain active profile id per device and attach to requests. */
(function(){
  if (window.ActiveProfile) return;
  const KEY = 'active_profile';
  let current = null;
  const subs = new Set();

  function readCookie(name){
    try{
      const m = document.cookie.match(new RegExp('(?:^|; )'+name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')+'=([^;]*)'));
      return m ? decodeURIComponent(m[1]) : null;
    }catch{ return null; }
  }

  function notify(){ subs.forEach(cb=>{ try{ cb(current); }catch{} }); }

  async function refresh(){
    try{
      const res = await fetch('/ui/active-profile');
      if (!res.ok) return;
      const data = await res.json().catch(()=>null);
      if (data && data.id){ current = String(data.id); try{ localStorage.setItem(KEY, current); }catch{} notify(); }
    }catch{}
  }

  async function set(id){
    if (!id) return false;
    try{
      const res = await fetch('/ui/active-profile', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: String(id) }) });
      if (!res.ok) return false;
      current = String(id);
      try{ localStorage.setItem(KEY, current); }catch{}
      notify();
      return true;
    }catch{ return false; }
  }

  function get(){
    if (current) return current;
    try{ current = localStorage.getItem(KEY) || null; }catch{}
    if (!current) current = readCookie('active_profile');
    return current;
  }

  function onChange(cb){ if (typeof cb==='function') subs.add(cb); return ()=>subs.delete(cb); }

  // Inject header for fetch
  if (window.fetch){
    const orig = window.fetch;
    window.fetch = function(input, init){
      try{
        const url = (typeof input==='string') ? input : (input && input.url) || '';
        const sameOrigin = !/^https?:\/\//i.test(url) || url.startsWith(location.origin);
        if (sameOrigin){
          init = init || {};
          init.headers = new Headers(init.headers||{});
          const ap = get(); if (ap) init.headers.set('X-Active-Profile', ap);
        }
      }catch{}
      return orig(input, init);
    };
  }

  // Inject header for htmx
  try{
    document.body.addEventListener('htmx:configRequest', function(ev){
      const ap = get(); if (ap) ev.detail.headers['X-Active-Profile'] = ap;
    });
  }catch{}

  // Initial pull from server
  refresh();

  window.ActiveProfile = { get, set, refresh, onChange };
})();
