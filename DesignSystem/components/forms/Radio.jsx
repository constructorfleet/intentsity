import React from 'react';
export function Radio({ checked, onChange, label, name, value, disabled, id, style }){
  const dot = (
    <span style={{position:'relative', display:'inline-block', width:16, height:16}}>
      <input id={id} type="radio" name={name} value={value} checked={!!checked} disabled={disabled}
        onChange={e=>onChange?.(e)}
        style={{
          appearance:'none', WebkitAppearance:'none', width:16, height:16, margin:0,
          border:`1.5px solid ${checked?'var(--accent)':'var(--border-strong)'}`,
          borderRadius:'var(--r-pill)', background:'var(--surface-panel)',
          cursor: disabled?'not-allowed':'pointer', display:'block'
        }} />
      {checked && <span aria-hidden style={{position:'absolute', inset:4, background:'var(--accent)', borderRadius:'var(--r-pill)'}}/>}
    </span>
  );
  if (!label) return dot;
  return <label htmlFor={id} style={{display:'inline-flex', alignItems:'center', gap:8, cursor: disabled?'not-allowed':'pointer', color:'var(--text-body)', fontSize:14, ...style}}>{dot}<span>{label}</span></label>;
}

export function RadioGroup({ children, style }){
  return <div style={{display:'flex', flexDirection:'column', gap:6, ...style}}>{children}</div>;
}
