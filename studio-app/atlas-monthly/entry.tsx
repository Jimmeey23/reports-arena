import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ReportMoMTable } from './ReportMoMTable';
import { register } from './adapter';

function Monthly({payload}:{payload:any}) {
  const [selected,setSelected]=useState('');
  return <ReportMoMTable history={payload.history} ids={payload.ids} selected={selected} onSelect={setSelected} title={payload.title}/>;
}
document.querySelectorAll<HTMLDetailsElement>('details.p57-monthly').forEach(details=>{
  const script=details.querySelector('script.p57-atlas-monthly-data');
  const mount=details.querySelector('.p57-atlas-monthly');
  if(!script||!mount)return;
  mount.removeAttribute('data-mounted'); // Reconnect controls in edited standalone downloads.
  const payload=JSON.parse(script.textContent||'{}');
  register(payload.definitions);
  // Mount only on expansion. Until then the complete server-rendered table
  // remains available, including in downloaded HTML without JavaScript.
  const open=()=>{if(!details.open||mount.getAttribute('data-mounted'))return;
    mount.setAttribute('data-mounted','true');details.querySelector('.p57-mom-scroll')?.remove();
    createRoot(mount).render(<Monthly payload={payload}/>);
  };
  details.addEventListener('toggle',open);open();
});
