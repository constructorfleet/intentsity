import React from 'react';
export function Tabs({ tabs=[], value, onChange, style }){
  return (
    <div style={{display:'flex', gap:2, borderBottom:'1px solid var(--border-subtle)', ...style}}>
      {tabs.map(t => {
        const active = t.value === value;
        return (
          <button key={t.value} type="button" onClick={()=>onChange?.(t.value)}
            style={{
              background:'none', border:'none', padding:'10px 12px',
              fontSize:13, fontWeight:active?'var(--fw-semibold)':'var(--fw-medium)',
              color: active ? 'var(--text-body)' : 'var(--text-muted)',
              borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
              cursor:'pointer', marginBottom:-1,
              display:'inline-flex', alignItems:'center', gap:6,
              transition:'color var(--dur-fast)'
            }}>
            {t.label}
            {t.count != null && <span style={{
              fontFamily:'var(--font-mono)', fontSize:11, color:'var(--text-subtle)',
              padding:'0 5px', background:'var(--surface-hover)', borderRadius:'var(--r-sm)'
            }}>{t.count}</span>}
          </button>
        );
      })}
    </div>
  );
}
