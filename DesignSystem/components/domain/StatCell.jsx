import React from 'react';
export function StatCell({ label, value, delta, deltaTone='neutral', unit, style }){
  const tones = { neutral:'var(--text-muted)', up:'var(--tp-600)', down:'var(--fp-600)' };
  return (
    <div style={{display:'flex', flexDirection:'column', gap:4, ...style}}>
      <div style={{fontSize:11, textTransform:'uppercase', letterSpacing:'var(--tracking-caps)', color:'var(--text-subtle)'}}>{label}</div>
      <div style={{display:'flex', alignItems:'baseline', gap:6}}>
        <span style={{fontSize:24, fontWeight:'var(--fw-semibold)', color:'var(--text-body)', fontFamily:'var(--font-mono)'}}>{value}</span>
        {unit && <span style={{fontSize:12, color:'var(--text-muted)'}}>{unit}</span>}
      </div>
      {delta && <div style={{fontSize:12, color:tones[deltaTone], fontFamily:'var(--font-mono)'}}>{delta}</div>}
    </div>
  );
}
