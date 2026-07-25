import React from 'react';
// Deterministic pseudo-random for stable rendering
function seedBars(seed, n, minH=0.15, maxH=1){
  const arr = []; let s = seed;
  for (let i=0;i<n;i++){ s = (s*9301 + 49297) % 233280; const r = s/233280; arr.push(minH + r*(maxH-minH)); }
  return arr;
}
export function Waveform({
  bars, samples=64, seed=42, playhead, // 0..1
  color, height=56, barWidth=3, barGap=2,
  region, // { start, end } in 0..1 — highlight
  onScrub, style
}){
  const data = bars || seedBars(seed, samples);
  const ref = React.useRef(null);
  const scrub = (e) => {
    if (!onScrub || !ref.current) return;
    const r = ref.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - r.left)/r.width));
    onScrub(x);
  };
  const fill = color || 'var(--waveform-fill)';
  return (
    <div ref={ref} onClick={scrub}
      style={{
        position:'relative', height, width:'100%', display:'flex', alignItems:'center',
        gap:barGap, cursor: onScrub ? 'pointer' : 'default',
        userSelect:'none', ...style
      }}>
      {region && (
        <div style={{
          position:'absolute', top:0, bottom:0,
          left: `${region.start*100}%`, width: `${(region.end-region.start)*100}%`,
          background:'var(--accent-quiet)', borderLeft:'1px solid var(--accent)', borderRight:'1px solid var(--accent)',
          pointerEvents:'none'
        }}/>
      )}
      {data.map((h,i) => (
        <div key={i} style={{
          flex:'1 1 0', minWidth:barWidth, height: `${h*100}%`, minHeight:2,
          background: playhead != null && i/data.length < playhead ? fill : 'var(--waveform-track)',
          borderRadius:1,
          transition:'background var(--dur-fast)'
        }}/>
      ))}
      {playhead != null && (
        <div style={{
          position:'absolute', top:-2, bottom:-2, left:`${playhead*100}%`,
          width:2, background:'var(--waveform-playhead)', pointerEvents:'none'
        }}/>
      )}
    </div>
  );
}
