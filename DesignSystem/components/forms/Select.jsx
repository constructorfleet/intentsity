import React from 'react';
const sz = { sm:{h:28,fs:13}, md:{h:34,fs:14}, lg:{h:42,fs:15} };
export function Select({ size='md', invalid, options=[], value, onChange, style, disabled, ...rest }){
  const [focus,setFocus]=React.useState(false);
  const s = sz[size];
  const border = invalid?'var(--fp-500)':focus?'var(--border-focus)':'var(--border-default)';
  return (
    <div style={{position:'relative', display:'inline-flex', width: style?.width || 'auto'}}>
      <select value={value} onChange={onChange} disabled={disabled} {...rest}
        onFocus={()=>setFocus(true)} onBlur={()=>setFocus(false)}
        style={{
          height:s.h, fontSize:s.fs, fontFamily:'var(--font-sans)',
          padding:'0 28px 0 10px', appearance:'none', WebkitAppearance:'none',
          background: disabled?'var(--surface-sunken)':'var(--surface-panel)',
          border:`1px solid ${border}`, borderRadius:'var(--r-md)',
          color:'var(--text-body)', outline:'none', width:'100%',
          boxShadow: focus?'var(--shadow-focus)':'none',
          transition:'border-color var(--dur-fast)', ...style
        }}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <span aria-hidden style={{
        position:'absolute', right:8, top:'50%', transform:'translateY(-50%)',
        color:'var(--text-muted)', pointerEvents:'none', fontSize:10
      }}>▾</span>
    </div>
  );
}
