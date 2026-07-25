import React from 'react';
// A collapsed sidebar becomes an icon rail: section headings and item labels
// drop out, so surrounding chrome does not have to be rewritten per screen.
const CollapsedContext = React.createContext(false);
export function Sidebar({ children, width=232, collapsedWidth=52, collapsed=false, style }){
  const w = collapsed ? collapsedWidth : width;
  return (
    <CollapsedContext.Provider value={collapsed}>
      <aside style={{
        width:w, minWidth:w, height:'100%',
        background:'var(--surface-panel)',
        borderRight:'1px solid var(--border-subtle)',
        display:'flex', flexDirection:'column',
        transition:'width var(--dur-fast)',
        fontSize:13, color:'var(--text-body)', ...style
      }}>{children}</aside>
    </CollapsedContext.Provider>
  );
}
export function useSidebarCollapsed(){ return React.useContext(CollapsedContext); }
export function SidebarSection({ title, children, style }){
  const collapsed = useSidebarCollapsed();
  return (
    <div style={{padding: collapsed ? '8px 6px 4px' : '12px 8px 4px', ...style}}>
      {title && !collapsed && <div style={{padding:'0 8px 6px', fontSize:10, textTransform:'uppercase', letterSpacing:'var(--tracking-caps)', color:'var(--text-subtle)', fontWeight:'var(--fw-semibold)'}}>{title}</div>}
      <div style={{display:'flex', flexDirection:'column', gap:1}}>{children}</div>
    </div>
  );
}
export function SidebarItem({ icon, active, badge, children, onClick, title, style }){
  const collapsed = useSidebarCollapsed();
  const [hover,setHover]=React.useState(false);
  return (
    <button type="button" onClick={onClick}
      title={title ?? (collapsed && typeof children === 'string' ? children : undefined)}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        display:'flex', alignItems:'center', gap:8, width:'100%', position:'relative',
        padding: collapsed ? '8px 0' : '6px 8px', border:'none', textAlign:'left',
        justifyContent: collapsed ? 'center' : 'flex-start',
        background: active ? 'var(--accent-quiet)' : hover ? 'var(--surface-hover)' : 'transparent',
        color: active ? 'var(--accent-active)' : 'var(--text-body)',
        borderRadius:'var(--r-md)', cursor:'pointer', fontSize:13, fontFamily:'var(--font-sans)',
        fontWeight: active?'var(--fw-semibold)':'var(--fw-regular)',
        transition:'background var(--dur-fast)', ...style
      }}>
      {icon && <span style={{width:16, height:16, display:'inline-flex', alignItems:'center', justifyContent:'center', color: active?'var(--accent-active)':'var(--text-muted)'}}>{icon}</span>}
      {!collapsed && <span style={{flex:1, minWidth:0, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{children}</span>}
      {badge != null && (collapsed
        // No room for a count on the rail — a dot just says "there is work here",
        // so an empty queue gets no marker at all.
        ? Number(badge) !== 0 && <span style={{
            position:'absolute', top:4, right:6, width:6, height:6,
            background:'var(--accent)', borderRadius:'var(--r-pill)'
          }} />
        : <span style={{
            fontSize:11, fontFamily:'var(--font-mono)', color:'var(--text-muted)',
            padding:'0 5px', background:'var(--surface-hover)', borderRadius:'var(--r-sm)'
          }}>{badge}</span>)}
    </button>
  );
}
