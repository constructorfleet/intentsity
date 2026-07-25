import React from 'react';
export function Kbd({ children, style }){
  return (
    <kbd style={{
      fontFamily:'var(--font-mono)', fontSize:11,
      padding:'1px 6px', borderRadius:'var(--r-sm)',
      background:'var(--surface-panel)', color:'var(--text-muted)',
      border:'1px solid var(--border-default)',
      boxShadow:'inset 0 -1px 0 var(--border-subtle)',
      whiteSpace:'nowrap', ...style
    }}>{children}</kbd>
  );
}
