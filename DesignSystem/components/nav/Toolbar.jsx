import React from 'react';
export function Toolbar({ children, style }){
  return (
    <div style={{
      display:'flex', alignItems:'center', gap:8,
      padding:'8px 12px', minHeight:48,
      background:'var(--surface-panel)',
      borderBottom:'1px solid var(--border-subtle)',
      ...style
    }}>{children}</div>
  );
}
export function ToolbarSeparator(){
  return <div style={{width:1, height:20, background:'var(--border-default)', margin:'0 4px'}}/>;
}
export function ToolbarSpacer(){
  return <div style={{flex:1}}/>;
}
