import React from 'react';
export function Dialog({ open, onClose, title, children, footer, width=480 }){
  React.useEffect(()=>{
    if (!open) return;
    const h = (e) => { if(e.key==='Escape') onClose?.(); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  },[open,onClose]);
  if (!open) return null;
  return (
    <div role="dialog" aria-modal="true" style={{
      position:'fixed', inset:0, zIndex:200, display:'flex', alignItems:'center', justifyContent:'center',
      background:'var(--surface-overlay)', backdropFilter:'blur(4px)'
    }} onClick={onClose}>
      <div onClick={e=>e.stopPropagation()} style={{
        width, maxWidth:'calc(100vw - 32px)',
        background:'var(--surface-raised)', border:'1px solid var(--border-subtle)',
        borderRadius:'var(--r-lg)', boxShadow:'var(--shadow-xl)', overflow:'hidden'
      }}>
        {title && <div style={{padding:'14px 16px', borderBottom:'1px solid var(--border-subtle)', fontWeight:'var(--fw-semibold)', fontSize:15}}>{title}</div>}
        <div style={{padding:16, fontSize:14, color:'var(--text-body)', lineHeight:'var(--lh-normal)'}}>{children}</div>
        {footer && <div style={{padding:'10px 16px', borderTop:'1px solid var(--border-subtle)', background:'var(--surface-sunken)', display:'flex', justifyContent:'flex-end', gap:8}}>{footer}</div>}
      </div>
    </div>
  );
}
