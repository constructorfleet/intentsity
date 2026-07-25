import React from 'react';
const sz = { sm: 26, md: 32, lg: 40 };
export function IconButton({ size='md', variant='ghost', active, disabled, children, style, onClick, 'aria-label':al, ...rest }) {
  const [hover,setHover] = React.useState(false);
  const s = sz[size];
  const isBrand = variant === 'primary';
  const bg = disabled ? 'transparent'
    : active ? (isBrand ? 'var(--accent-active)' : 'var(--surface-active)')
    : hover ? (isBrand ? 'var(--accent-hover)' : 'var(--surface-hover)')
    : (isBrand ? 'var(--accent)' : 'transparent');
  return (
    <button type="button" aria-label={al} onClick={onClick} disabled={disabled}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        width:s, height:s, display:'inline-flex', alignItems:'center', justifyContent:'center',
        border: variant==='outline' ? '1px solid var(--border-default)' : 'none',
        background:bg, color: isBrand ? 'var(--text-on-brand)' : (disabled ? 'var(--text-subtle)' : 'var(--text-body)'),
        borderRadius:'var(--r-md)', cursor: disabled?'not-allowed':'pointer',
        transition:'background var(--dur-fast) var(--ease-out)', ...style
      }} {...rest}>{children}</button>
  );
}
