import React from 'react';
export function Tooltip({ content, placement='top', children, delay=200 }){
  const [open,setOpen] = React.useState(false);
  const t = React.useRef(null);
  const show = () => { clearTimeout(t.current); t.current = setTimeout(()=>setOpen(true), delay); };
  const hide = () => { clearTimeout(t.current); setOpen(false); };
  const pos = { top:{bottom:'100%',left:'50%',transform:'translate(-50%,-6px)'},
    bottom:{top:'100%',left:'50%',transform:'translate(-50%,6px)'},
    left:{right:'100%',top:'50%',transform:'translate(-6px,-50%)'},
    right:{left:'100%',top:'50%',transform:'translate(6px,-50%)'} }[placement];
  return (
    <span style={{position:'relative', display:'inline-flex'}} onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      {children}
      {open && (
        <span role="tooltip" style={{
          position:'absolute', ...pos, zIndex:100,
          background:'var(--surface-inverse)', color:'var(--text-inverse)',
          padding:'5px 8px', borderRadius:'var(--r-sm)', fontSize:12,
          whiteSpace:'nowrap', pointerEvents:'none',
          boxShadow:'var(--shadow-md)', fontFamily:'var(--font-sans)'
        }}>{content}</span>
      )}
    </span>
  );
}
