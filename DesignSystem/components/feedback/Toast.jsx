import React from 'react';
const toneMap = {
  info:{bar:'var(--tn-500)', bg:'var(--tn-050)'},
  success:{bar:'var(--tp-500)', bg:'var(--tp-050)'},
  warn:{bar:'var(--fn-500)', bg:'var(--fn-050)'},
  error:{bar:'var(--fp-500)', bg:'var(--fp-050)'},
};
export function Toast({ tone='info', title, description, onDismiss, style }){
  const t = toneMap[tone];
  return (
    <div style={{
      display:'flex', gap:12, alignItems:'flex-start',
      padding:'10px 12px', minWidth:280, maxWidth:420,
      background:'var(--surface-raised)', border:'1px solid var(--border-subtle)',
      borderLeft:`3px solid ${t.bar}`, borderRadius:'var(--r-md)',
      boxShadow:'var(--shadow-lg)', ...style
    }}>
      <div style={{flex:1, minWidth:0}}>
        {title && <div style={{fontWeight:'var(--fw-semibold)', fontSize:13, color:'var(--text-body)', marginBottom:2}}>{title}</div>}
        {description && <div style={{fontSize:12, color:'var(--text-muted)', lineHeight:'var(--lh-snug)'}}>{description}</div>}
      </div>
      {onDismiss && <button onClick={onDismiss} aria-label="Dismiss" style={{background:'none', border:'none', color:'var(--text-muted)', cursor:'pointer', fontSize:16, lineHeight:1}}>×</button>}
    </div>
  );
}
