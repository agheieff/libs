/* ArcadiaModal: alert/confirm/prompt/open with minimal a11y and focus trap. */
(function(){
  if (window.ArcadiaModal) return;
  const ROOT_ID='ui-modal-root';
  let root=null, active=null, lastFocus=null;

  function ensureRoot(){
    root = document.getElementById(ROOT_ID);
    if (!root){
      root = document.createElement('div');
      root.id = ROOT_ID;
      root.style.position='fixed';
      root.style.inset='0';
      root.style.zIndex='5000';
      root.style.display='none';
      document.body.appendChild(root);
    }
  }

  function overlay(){
    const ov=document.createElement('div');
    ov.className='t-modal-overlay';
    ov.style.position='absolute';
    ov.style.inset='0';
    ov.style.background='rgba(0,0,0,0.35)';
    return ov;
  }

  function dialog(){
    const d=document.createElement('div');
    d.className='t-modal t-panel t-border';
    d.setAttribute('role','dialog');
    d.setAttribute('aria-modal','true');
    d.style.position='absolute';
    d.style.left='50%';
    d.style.top='20%';
    d.style.transform='translateX(-50%)';
    d.style.background='var(--panel)';
    d.style.color='var(--fg)';
    d.style.border='1px solid var(--border)';
    d.style.borderRadius='8px';
    d.style.minWidth='360px';
    d.style.maxWidth='80vw';
    d.style.boxShadow='0 10px 30px rgba(0,0,0,0.2)';
    return d;
  }

  function close(){
    if (!active) return;
    active.remove(); active=null;
    root.style.display='none';
    if (lastFocus && lastFocus.focus) try{ lastFocus.focus(); }catch{}
  }

  function trap(e){
    if (!active) return;
    if (e.key==='Escape'){ e.preventDefault(); close(); return; }
    if (e.key!=='Tab') return;
    const f = active.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (!f.length) return;
    const first=f[0], last=f[f.length-1];
    if (e.shiftKey){ if (document.activeElement===first){ e.preventDefault(); last.focus(); } }
    else { if (document.activeElement===last){ e.preventDefault(); first.focus(); } }
  }

  function open(build){
    ensureRoot();
    lastFocus=document.activeElement;
    root.style.display='block';
    active=document.createElement('div');
    active.style.position='absolute';
    active.style.inset='0';
    root.appendChild(active);
    const ov=overlay();
    const dlg=dialog();
    active.appendChild(ov); active.appendChild(dlg);
    ov.addEventListener('click', close, true);
    document.addEventListener('keydown', trap, true);
    build(dlg, close);
    // focus first focusable
    setTimeout(()=>{
      const f = dlg.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (f && f.focus) try{ f.focus(); }catch{}
    }, 0);
    return { close };
  }

  function alert(msg, opts){
    return new Promise(resolve=>{
      open((dlg,close)=>{
        const body=document.createElement('div'); body.style.padding='16px'; body.textContent=String(msg||''); dlg.appendChild(body);
        const actions=document.createElement('div'); actions.style.display='flex'; actions.style.justifyContent='flex-end'; actions.style.gap='8px'; actions.style.padding='0 16px 16px'; dlg.appendChild(actions);
        const ok=document.createElement('button');
        ok.type='button';
        ok.className='t-btn t-btn-primary';
        ok.textContent=(opts&&opts.okLabel)||'OK';
        ok.addEventListener('click', ()=>{ close(); resolve(true); });
        actions.appendChild(ok);
      });
    });
  }

  function confirm(msg, opts){
    return new Promise(resolve=>{
      open((dlg,close)=>{
        const body=document.createElement('div'); body.style.padding='16px'; body.textContent=String(msg||''); dlg.appendChild(body);
        const actions=document.createElement('div'); actions.style.display='flex'; actions.style.justifyContent='flex-end'; actions.style.gap='8px'; actions.style.padding='0 16px 16px'; dlg.appendChild(actions);
        const cancel=document.createElement('button');
        cancel.type='button';
        cancel.className='t-btn';
        cancel.textContent=(opts&&opts.cancelLabel)||'Cancel';
        cancel.addEventListener('click', ()=>{ close(); resolve(false); });
        actions.appendChild(cancel);
        const ok=document.createElement('button');
        ok.type='button';
        ok.className='t-btn t-btn-primary';
        ok.textContent=(opts&&opts.okLabel)||'OK';
        ok.addEventListener('click', ()=>{ close(); resolve(true); });
        actions.appendChild(ok);
      });
    });
  }

  function prompt(msg, opts){
    return new Promise(resolve=>{
      open((dlg,close)=>{
        const body=document.createElement('div'); body.style.padding='16px'; dlg.appendChild(body);
        const label=document.createElement('div'); label.textContent=String(msg||''); label.style.marginBottom='8px'; body.appendChild(label);
        const input=document.createElement('input'); input.type='text'; input.value=(opts&&opts.defaultValue)||''; input.style.width='100%'; input.style.padding='8px'; input.style.border='1px solid var(--border)'; input.style.borderRadius='6px'; input.style.background='var(--panel)'; input.style.color='var(--fg)'; body.appendChild(input);
        input.addEventListener('keydown', (e)=>{ if (e.key==='Enter'){ e.preventDefault(); ok.click(); } });
        const actions=document.createElement('div'); actions.style.display='flex'; actions.style.justifyContent='flex-end'; actions.style.gap='8px'; actions.style.padding='0 16px 16px'; dlg.appendChild(actions);
        const cancel=document.createElement('button');
        cancel.type='button';
        cancel.className='t-btn';
        cancel.textContent=(opts&&opts.cancelLabel)||'Cancel';
        cancel.addEventListener('click', ()=>{ close(); resolve(null); });
        actions.appendChild(cancel);
        const ok=document.createElement('button');
        ok.type='button';
        ok.className='t-btn t-btn-primary';
        ok.textContent=(opts&&opts.okLabel)||'OK';
        ok.addEventListener('click', ()=>{ close(); resolve(String(input.value)); });
        actions.appendChild(ok);
        setTimeout(()=>{ try{ input.focus(); input.select(); }catch{} }, 0);
      });
    });
  }

  window.ArcadiaModal = { alert, confirm, prompt, open };
})();
