import React from 'react';
export function Switch({ checked, onChange, label, disabled, style }){
  const track = (
    <span onClick={()=>!disabled && onChange?.(!checked)}
      style={{
        width:32, height:18, borderRadius:'var(--r-pill)',
        background: checked ? 'var(--accent)' : 'var(--gray-300)',
        position:'relative', cursor: disabled?'not-allowed':'pointer',
        transition:'background var(--dur-fast)', flexShrink:0, opacity: disabled?.5:1
      }}>
      <span style={{
        position:'absolute', top:2, left: checked?16:2, width:14, height:14,
        borderRadius:'var(--r-pill)', background:'#fff',
        boxShadow:'var(--shadow-sm)', transition:'left var(--dur-fast) var(--ease-out)'
      }}/>
    </span>
  );
  if (!label) return track;
  return <label style={{display:'inline-flex', alignItems:'center', gap:10, cursor: disabled?'not-allowed':'pointer', color:'var(--text-body)', fontSize:14, ...style}}>{track}<span>{label}</span></label>;
}
