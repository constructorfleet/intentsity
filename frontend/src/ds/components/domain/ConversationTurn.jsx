import React from 'react';
const roleStyles = {
  user:      { align:'flex-end',   bg:'var(--tn-050)',       ink:'var(--tn-600)', label:'USER' },
  assistant: { align:'flex-start', bg:'var(--surface-panel)', ink:'var(--text-body)', label:'ASSISTANT' },
  tool:      { align:'flex-start', bg:'var(--surface-sunken)', ink:'var(--text-muted)', label:'TOOL', mono:true },
  system:    { align:'center',     bg:'transparent', ink:'var(--text-subtle)', label:'SYSTEM', mono:true },
};
export function ConversationTurn({ role='user', name, timestamp, children, editable, onEdit, actions, style }){
  const r = roleStyles[role] || roleStyles.user;
  return (
    <div style={{display:'flex', flexDirection:'column', alignItems:r.align, gap:4, ...style}}>
      <div style={{
        display:'flex', alignItems:'center', gap:8, fontSize:11,
        letterSpacing:'var(--tracking-caps)', textTransform:'uppercase',
        color:r.ink, fontFamily:'var(--font-mono)', fontWeight:'var(--fw-medium)'
      }}>
        <span>{name || r.label}</span>
        {timestamp && <span style={{color:'var(--text-subtle)'}}>{timestamp}</span>}
      </div>
      <div style={{
        maxWidth:'75%', minWidth:60, padding:'8px 12px',
        background:r.bg, border: role==='system'?'none':'1px solid var(--border-subtle)',
        borderRadius:'var(--r-md)', fontSize:14, lineHeight:'var(--lh-normal)',
        color:'var(--text-body)', fontFamily: r.mono ? 'var(--font-mono)' : 'var(--font-sans)',
        whiteSpace:'pre-wrap', position:'relative'
      }}>
        {children}
      </div>
      {actions && <div style={{display:'flex', gap:6, marginTop:2}}>{actions}</div>}
    </div>
  );
}
