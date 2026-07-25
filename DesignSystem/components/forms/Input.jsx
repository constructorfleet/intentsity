import React from 'react';
const sz = { sm:{h:28,fs:13,px:8}, md:{h:34,fs:14,px:10}, lg:{h:42,fs:15,px:12} };
export function Input({ size='md', invalid, prefix, suffix, style, disabled, ...rest }) {
  const [focus,setFocus] = React.useState(false);
  const s = sz[size];
  const border = invalid ? 'var(--fp-500)' : focus ? 'var(--border-focus)' : 'var(--border-default)';
  return (
    <div style={{
      display:'flex', alignItems:'center', height:s.h,
      background: disabled?'var(--surface-sunken)':'var(--surface-panel)',
      border:`1px solid ${border}`,
      borderRadius:'var(--r-md)',
      boxShadow: focus ? 'var(--shadow-focus)' : 'none',
      transition:'border-color var(--dur-fast), box-shadow var(--dur-fast)',
      padding:`0 ${s.px}px`, ...style
    }}>
      {prefix && <span style={{color:'var(--text-muted)', display:'inline-flex', marginRight:6}}>{prefix}</span>}
      <input {...rest} disabled={disabled} onFocus={e=>{setFocus(true); rest.onFocus?.(e)}} onBlur={e=>{setFocus(false); rest.onBlur?.(e)}}
        style={{
          flex:1, height:'100%', border:'none', outline:'none', background:'transparent',
          fontSize:s.fs, color:'var(--text-body)', fontFamily:'var(--font-sans)', minWidth:0
        }} />
      {suffix && <span style={{color:'var(--text-muted)', display:'inline-flex', marginLeft:6}}>{suffix}</span>}
    </div>
  );
}
