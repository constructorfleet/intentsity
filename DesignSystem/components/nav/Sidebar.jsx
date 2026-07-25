import React from 'react';
export function Sidebar({ children, width=232, style }){
  return (
    <aside style={{
      width, minWidth:width, height:'100%',
      background:'var(--surface-panel)',
      borderRight:'1px solid var(--border-subtle)',
      display:'flex', flexDirection:'column',
      fontSize:13, color:'var(--text-body)', ...style
    }}>{children}</aside>
  );
}
export function SidebarSection({ title, children, style }){
  return (
    <div style={{padding:'12px 8px 4px', ...style}}>
      {title && <div style={{padding:'0 8px 6px', fontSize:10, textTransform:'uppercase', letterSpacing:'var(--tracking-caps)', color:'var(--text-subtle)', fontWeight:'var(--fw-semibold)'}}>{title}</div>}
      <div style={{display:'flex', flexDirection:'column', gap:1}}>{children}</div>
    </div>
  );
}
export function SidebarItem({ icon, active, badge, children, onClick, style }){
  const [hover,setHover]=React.useState(false);
  return (
    <button type="button" onClick={onClick}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        display:'flex', alignItems:'center', gap:8, width:'100%',
        padding:'6px 8px', border:'none', textAlign:'left',
        background: active ? 'var(--accent-quiet)' : hover ? 'var(--surface-hover)' : 'transparent',
        color: active ? 'var(--accent-active)' : 'var(--text-body)',
        borderRadius:'var(--r-md)', cursor:'pointer', fontSize:13, fontFamily:'var(--font-sans)',
        fontWeight: active?'var(--fw-semibold)':'var(--fw-regular)',
        transition:'background var(--dur-fast)', ...style
      }}>
      {icon && <span style={{width:16, height:16, display:'inline-flex', alignItems:'center', justifyContent:'center', color: active?'var(--accent-active)':'var(--text-muted)'}}>{icon}</span>}
      <span style={{flex:1, minWidth:0, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{children}</span>
      {badge != null && <span style={{
        fontSize:11, fontFamily:'var(--font-mono)', color:'var(--text-muted)',
        padding:'0 5px', background:'var(--surface-hover)', borderRadius:'var(--r-sm)'
      }}>{badge}</span>}
    </button>
  );
}
