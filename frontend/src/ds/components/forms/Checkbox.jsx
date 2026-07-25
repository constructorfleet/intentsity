import React from 'react';
export function Checkbox({ checked, indeterminate, onChange, label, disabled, id, style }){
  const ref = React.useRef(null);
  React.useEffect(()=>{ if(ref.current) ref.current.indeterminate = !!indeterminate; },[indeterminate]);
  const box = (
    <span style={{position:'relative', display:'inline-block', width:16, height:16}}>
      <input ref={ref} id={id} type="checkbox" checked={!!checked} disabled={disabled}
        onChange={e=>onChange?.(e.target.checked, e)}
        style={{
          appearance:'none', WebkitAppearance:'none', width:16, height:16, margin:0,
          border:`1.5px solid ${checked||indeterminate?'var(--accent)':'var(--border-strong)'}`,
          borderRadius:'var(--r-sm)',
          background: checked||indeterminate ? 'var(--accent)' : 'var(--surface-panel)',
          cursor: disabled?'not-allowed':'pointer', display:'block',
          transition:'background var(--dur-fast), border-color var(--dur-fast)'
        }} />
      {(checked || indeterminate) && (
        <span aria-hidden style={{
          position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center',
          color:'var(--text-on-brand)', fontSize:11, fontWeight:700, pointerEvents:'none'
        }}>{indeterminate ? '–' : '✓'}</span>
      )}
    </span>
  );
  if (!label) return box;
  return (
    <label htmlFor={id} style={{display:'inline-flex', alignItems:'center', gap:8, cursor: disabled?'not-allowed':'pointer', color:'var(--text-body)', fontSize:14, ...style}}>
      {box}<span>{label}</span>
    </label>
  );
}
