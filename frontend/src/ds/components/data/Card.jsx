import React from 'react';
export function Card({ title, actions, footer, children, style, padded=true, elevation='flat' }){
  const shadow = elevation==='raised' ? 'var(--shadow-sm)' : elevation==='floating' ? 'var(--shadow-md)' : 'none';
  return (
    <div style={{
      background:'var(--surface-panel)', border:'1px solid var(--border-subtle)',
      borderRadius:'var(--r-lg)', boxShadow:shadow, overflow:'hidden', ...style
    }}>
      {(title || actions) && (
        <div style={{display:'flex', alignItems:'center', padding:'10px 14px', borderBottom:'1px solid var(--border-subtle)', gap:12}}>
          <div style={{fontWeight:'var(--fw-semibold)', fontSize:14, color:'var(--text-body)', flex:1}}>{title}</div>
          {actions}
        </div>
      )}
      <div style={{padding: padded ? 14 : 0}}>{children}</div>
      {footer && <div style={{padding:'10px 14px', borderTop:'1px solid var(--border-subtle)', background:'var(--surface-sunken)'}}>{footer}</div>}
    </div>
  );
}
