import React from 'react';
export function Textarea({ invalid, style, disabled, minRows=3, ...rest }){
  const [focus,setFocus]=React.useState(false);
  const border = invalid ? 'var(--fp-500)' : focus ? 'var(--border-focus)' : 'var(--border-default)';
  return (
    <textarea {...rest} disabled={disabled} rows={minRows}
      onFocus={e=>{setFocus(true); rest.onFocus?.(e)}} onBlur={e=>{setFocus(false); rest.onBlur?.(e)}}
      style={{
        width:'100%', padding:'8px 10px', fontFamily:'var(--font-sans)', fontSize:14,
        lineHeight:'var(--lh-normal)', color:'var(--text-body)',
        background: disabled ? 'var(--surface-sunken)' : 'var(--surface-panel)',
        border:`1px solid ${border}`, borderRadius:'var(--r-md)',
        boxShadow: focus ? 'var(--shadow-focus)' : 'none', outline:'none',
        resize:'vertical', transition:'border-color var(--dur-fast), box-shadow var(--dur-fast)', ...style
      }} />
  );
}
