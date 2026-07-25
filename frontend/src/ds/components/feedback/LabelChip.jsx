import React from 'react';
export const WAKE_LABELS = [
  { id:'tp', label:'True positive', short:'TP', tone:'tp', key:'1' },
  { id:'tn', label:'True negative', short:'TN', tone:'tn', key:'2' },
  { id:'fp', label:'False positive', short:'FP', tone:'fp', key:'3' },
  { id:'fn', label:'False negative', short:'FN', tone:'fn', key:'4' },
  { id:'bgnoise', label:'Background noise', short:'BG', tone:'bgnoise', key:'5' },
];
const toneMap = {
  tp:{bg:'var(--tp-500)', quiet:'var(--tp-050)', ink:'var(--tp-600)'},
  tn:{bg:'var(--tn-500)', quiet:'var(--tn-050)', ink:'var(--tn-600)'},
  fp:{bg:'var(--fp-500)', quiet:'var(--fp-050)', ink:'var(--fp-600)'},
  fn:{bg:'var(--fn-500)', quiet:'var(--fn-050)', ink:'var(--fn-600)'},
  bgnoise:{bg:'var(--bg-500)', quiet:'var(--bg-050)', ink:'var(--bg-600)'},
};
export function LabelChip({ tone='tp', selected, onClick, shortcut, children, style }){
  const t = toneMap[tone];
  const [hover,setHover] = React.useState(false);
  return (
    <button type="button" onClick={onClick}
      onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}
      style={{
        display:'inline-flex', alignItems:'center', gap:8, height:30,
        padding:'0 10px 0 8px',
        border: selected ? `1.5px solid ${t.bg}` : '1.5px solid var(--border-default)',
        borderRadius:'var(--r-md)',
        background: selected ? t.quiet : (hover ? 'var(--surface-hover)' : 'var(--surface-panel)'),
        color: selected ? t.ink : 'var(--text-body)',
        cursor:'pointer', fontSize:13, fontWeight:'var(--fw-medium)',
        transition:'all var(--dur-fast) var(--ease-out)', ...style
      }}>
      <span style={{width:10, height:10, borderRadius:2, background:t.bg, display:'inline-block'}}/>
      <span>{children}</span>
      {shortcut && <kbd style={{
        marginLeft:4, fontFamily:'var(--font-mono)', fontSize:10,
        padding:'1px 5px', borderRadius:'var(--r-sm)',
        background:'var(--surface-sunken)', color:'var(--text-muted)',
        border:'1px solid var(--border-subtle)'
      }}>{shortcut}</kbd>}
    </button>
  );
}
