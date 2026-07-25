import React from 'react';
const tones = {
  neutral: { bg:'var(--surface-hover)', fg:'var(--text-body)' },
  brand:   { bg:'var(--accent-quiet)', fg:'var(--accent-active)' },
  tp:      { bg:'var(--tp-050)', fg:'var(--tp-600)' },
  tn:      { bg:'var(--tn-050)', fg:'var(--tn-600)' },
  fp:      { bg:'var(--fp-050)', fg:'var(--fp-600)' },
  fn:      { bg:'var(--fn-050)', fg:'var(--fn-600)' },
  bgnoise: { bg:'var(--bg-050)', fg:'var(--bg-600)' },
};
export function Badge({ tone='neutral', children, style, mono, dot }){
  const t = tones[tone] || tones.neutral;
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap:6,
      padding:'2px 8px', height:20, borderRadius:'var(--r-pill)',
      background:t.bg, color:t.fg,
      fontSize:11, fontWeight:'var(--fw-semibold)',
      letterSpacing:'var(--tracking-wide)',
      fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)',
      textTransform: mono ? 'none' : 'uppercase',
      ...style
    }}>
      {dot && <span style={{width:6, height:6, borderRadius:'50%', background:'currentColor'}}/>}
      {children}
    </span>
  );
}
