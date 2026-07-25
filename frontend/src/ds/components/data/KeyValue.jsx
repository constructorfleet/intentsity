import React from 'react';
export function KeyValue({ items=[], layout='rows', style }){
  if (layout==='columns'){
    return (
      <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(140px, 1fr))', gap:16, ...style}}>
        {items.map((it,i)=>(
          <div key={i}>
            <div style={{fontSize:11, textTransform:'uppercase', letterSpacing:'var(--tracking-caps)', color:'var(--text-subtle)', marginBottom:4}}>{it.k}</div>
            <div style={{fontSize:14, color:'var(--text-body)', fontFamily: it.mono?'var(--font-mono)':'var(--font-sans)'}}>{it.v}</div>
          </div>
        ))}
      </div>
    );
  }
  return (
    <dl style={{display:'grid', gridTemplateColumns:'auto 1fr', gap:'8px 16px', margin:0, ...style}}>
      {items.map((it,i)=>(
        <React.Fragment key={i}>
          <dt style={{fontSize:13, color:'var(--text-muted)'}}>{it.k}</dt>
          <dd style={{margin:0, fontSize:13, color:'var(--text-body)', fontFamily: it.mono?'var(--font-mono)':'var(--font-sans)'}}>{it.v}</dd>
        </React.Fragment>
      ))}
    </dl>
  );
}
