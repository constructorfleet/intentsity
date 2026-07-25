import React from 'react';
export function Tag({ children, onRemove, style }){
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap:6,
      padding:'2px 4px 2px 8px', height:22,
      background:'var(--surface-hover)', border:'1px solid var(--border-subtle)',
      borderRadius:'var(--r-sm)', fontSize:12, color:'var(--text-body)',
      fontFamily:'var(--font-mono)', ...style
    }}>
      {children}
      {onRemove && <button onClick={onRemove} style={{
        background:'none', border:'none', color:'var(--text-muted)', cursor:'pointer',
        fontSize:14, lineHeight:1, padding:'0 2px'
      }} aria-label="Remove">×</button>}
    </span>
  );
}
