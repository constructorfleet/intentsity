import React from 'react';
export function ToolInvocation({ name, args, result, status='ok', editable, onEditArgs, style }){
  const [open,setOpen] = React.useState(true);
  const statusTone = { ok:'var(--tp-500)', pending:'var(--fn-500)', error:'var(--fp-500)' }[status];
  return (
    <div style={{
      border:'1px solid var(--border-subtle)', borderRadius:'var(--r-md)',
      background:'var(--surface-sunken)', overflow:'hidden',
      fontFamily:'var(--font-mono)', fontSize:12, ...style
    }}>
      <button type="button" onClick={()=>setOpen(o=>!o)} style={{
        width:'100%', display:'flex', alignItems:'center', gap:8, padding:'8px 10px',
        background:'transparent', border:'none', cursor:'pointer', color:'var(--text-body)',
        borderBottom: open ? '1px solid var(--border-subtle)' : 'none',
        fontFamily:'inherit', fontSize:12, textAlign:'left'
      }}>
        <span style={{width:6, height:6, borderRadius:'50%', background:statusTone}}/>
        <span style={{fontWeight:'var(--fw-semibold)'}}>{name}</span>
        <span style={{color:'var(--text-subtle)', marginLeft:'auto'}}>{open?'▾':'▸'}</span>
      </button>
      {open && (
        <div style={{padding:'8px 10px', display:'flex', flexDirection:'column', gap:8}}>
          <div>
            <div style={{color:'var(--text-subtle)', marginBottom:2, fontSize:10, textTransform:'uppercase', letterSpacing:'var(--tracking-caps)'}}>Arguments</div>
            <pre style={{margin:0, whiteSpace:'pre-wrap', color:'var(--text-body)'}}>{typeof args==='string'?args:JSON.stringify(args,null,2)}</pre>
          </div>
          {result != null && (
            <div>
              <div style={{color:'var(--text-subtle)', marginBottom:2, fontSize:10, textTransform:'uppercase', letterSpacing:'var(--tracking-caps)'}}>Result</div>
              <pre style={{margin:0, whiteSpace:'pre-wrap', color:'var(--text-muted)'}}>{typeof result==='string'?result:JSON.stringify(result,null,2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
