import React from 'react';
const sizes = {
  md:{ pad:'10px 12px', font:13, gap:6, count:11 },
  sm:{ pad:'7px 8px',   font:12, gap:4, count:10 },
};
export function Tabs({ tabs=[], value, onChange, size='md', style }){
  const s = sizes[size] || sizes.md;
  return (
    // minWidth:0 + overflowX keeps a long tab strip inside its column instead of
    // pushing past the panel edge into whatever sits beside it.
    <div style={{
      display:'flex', gap:2, minWidth:0, maxWidth:'100%',
      overflowX:'auto', scrollbarWidth:'none',
      borderBottom:'1px solid var(--border-subtle)', ...style
    }}>
      {tabs.map(t => {
        const active = t.value === value;
        return (
          <button key={t.value} type="button" onClick={()=>onChange?.(t.value)}
            style={{
              background:'none', border:'none', padding:s.pad, flex:'0 0 auto',
              fontSize:s.font, fontWeight:active?'var(--fw-semibold)':'var(--fw-medium)',
              fontFamily:'var(--font-sans)',
              color: active ? 'var(--text-body)' : 'var(--text-muted)',
              borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
              cursor:'pointer', marginBottom:-1, whiteSpace:'nowrap',
              display:'inline-flex', alignItems:'center', gap:s.gap,
              transition:'color var(--dur-fast)'
            }}>
            {t.label}
            {t.count != null && <span style={{
              fontFamily:'var(--font-mono)', fontSize:s.count, color:'var(--text-subtle)',
              padding:'0 4px', background:'var(--surface-hover)', borderRadius:'var(--r-sm)'
            }}>{t.count}</span>}
          </button>
        );
      })}
    </div>
  );
}
