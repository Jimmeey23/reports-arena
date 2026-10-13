/* Layout editor: manually add, delete and edit any block in a generated
report. Structural changes persist server-side (Supabase-backed) per run, so
everyone opening the same review sees the same document. Works offline via
localStorage for standalone exported files. */
(() => {
'use strict';
const R = window.P57Reader; if(!R) return;
const {make} = R;
const root = document.documentElement;
const route = location.pathname.match(/^\/api\/report\/([^/]+)/);
const run = route ? route[1] : null;
const online = /^https?:$/.test(location.protocol) && !!run;
const localKey = 'p57-layout-edits:' + (run || document.title);
const model = window.P57EditModel;
const cleanup = () => model?.cleanup();
const undoStack = [], redoStack = [];
const originalMarkup = new Map();
let toast = null;
function remember(change){undoStack.push(change);redoStack.length=0;updateHistory();return change;}
function updateHistory(){undoBtn.disabled=!undoStack.length;redoBtn.disabled=!redoStack.length;}
function notice(text){toast?.remove();toast=make('div',null,'p57-edit-toast');toast.setAttribute('role','status');toast.append(make('span',text));const undo=make('button','Undo');undo.onclick=()=>undoChange();const close=make('button','✕');close.setAttribute('aria-label','Dismiss editing notice');close.onclick=()=>toast?.remove();toast.append(undo,close);document.body.append(toast);}

// ------------------------------------------------------------- block model
const blocks = [];
const elIndex = new Map();
function reindex(){ elIndex.clear(); document.querySelectorAll('[data-el]').forEach(e => elIndex.set(e.dataset.el, e)); }
function byId(id){
  if(!elIndex.has(id) || !elIndex.get(id).isConnected) reindex();
  return elIndex.get(id) || null;
}
function sectionId(sec, i){ return sec.id || ('p57-sec-' + i); }
function collect(){
  blocks.length = 0;
  elIndex && elIndex.clear && elIndex.clear();
  const secs = [...document.querySelectorAll('.wrap section')];
  const wrap = document.querySelector('.wrap');
  if(wrap) secs.push(wrap);
  const cover = document.querySelector('body > header');
  if(cover){
    let savedCover;
    try{savedCover=JSON.parse(document.getElementById('p57-structural-edits')?.textContent||'[]').find(row=>row.el_id?.startsWith('p57-cover-'))?.el_id.split('~')[0];}catch{}
    cover.id ||= savedCover || 'p57-cover-' + (location.pathname.split('/').pop() || 'report');secs.push(cover);
  }
  secs.forEach((sec, si) => {
    sec.id = sectionId(sec, si);
    if(sec.matches('.wrap>section')){sec.dataset.el ||= sec.id+'~container';sec.classList.add('p57-block');blocks.push(sec);if(!originalMarkup.has(sec.dataset.el))originalMarkup.set(sec.dataset.el,sec.innerHTML);}
    [...sec.children].forEach((el, i) => {
      if(el.tagName === 'SECTION' || el.classList.contains('p57-block-deleted') || el.matches('script,style,.toc,footer')) return;
      if(!el.dataset.el) el.dataset.el = sec.id + '~' + i;
      el.classList.add('p57-block');
      blocks.push(el);
      if(!originalMarkup.has(el.dataset.el))originalMarkup.set(el.dataset.el,el.innerHTML);
      if(el.matches('.p57-monthly')) return; // Edit the complete generated register, not React's transient cells.
      el.querySelectorAll('h1,h2,h3,h4,p,li,.kpi,.stat,.v,.l,.d,th,td,figcaption,summary,.chart,svg').forEach((part, j) => {
        if(part.closest('.rt-table-tools,.p57-block-tools,.p57-monthly,.p57-art,.p57-marquee')) return;
        if(!part.dataset.el) part.dataset.el = el.dataset.el + '~part-' + j;
        part.classList.add('p57-component');
        if(!originalMarkup.has(part.dataset.el))originalMarkup.set(part.dataset.el,part.innerHTML);
      });
      // Add structural row targets without changing legacy part IDs.
      el.querySelectorAll('tr').forEach((row,j)=>{if(row.closest('.p57-monthly'))return;row.dataset.el ||= el.dataset.el+'~row-'+j;row.classList.add('p57-component');if(!originalMarkup.has(row.dataset.el))originalMarkup.set(row.dataset.el,row.innerHTML);});
    });
  });
}
collect();

// ------------------------------------------------------------- persistence
let edits = [];           // rows: {el_id, op, html, sort}
function persist(){
  try{ localStorage.setItem(localKey, JSON.stringify(edits)); localStorage.setItem(localKey+':pending',JSON.stringify([...pendingSaves.values()])); }catch{}
}
function loadInitial(){
  try{ edits = JSON.parse(document.getElementById('p57-structural-edits')?.textContent || localStorage.getItem(localKey) || '[]'); }catch{ edits = []; }
}
async function apiEdits(){
  if(!online) return loadInitial();
  try{
    const res = await fetch('/api/edits?run=' + encodeURIComponent(run));
    const data = await res.json();
    if(!res.ok) throw Error(data.error || 'Could not load edits');
    const queued = [...pendingSaves.values()];
    edits = (data.edits || []).filter(e=>!queued.some(q=>q.el_id===e.el_id&&(q.op===e.op||(q.op==='restore'&&e.op==='delete')))).concat(queued.filter(q=>q.op!=='restore'));
    persist();
  }catch{ loadInitial(); }
}
async function saveEdit(el_id, op, html='', sort=0){
  edits = edits.filter(e => !(e.el_id === el_id && (e.op === op || (op==='restore'&&e.op==='delete'))));
  if(op !== 'restore') edits.push({el_id, op, html, sort});
  pendingSaves.set(el_id+'|'+op,{el_id,op,html,sort});
  persist();
  if(online){
    try{ const response = await fetch('/api/edits', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({run, el_id, op, html, sort})});
      if(!response.ok) throw Error('Server rejected the save');
      pendingSaves.delete(el_id+'|'+op);
      saveStatus.textContent = 'Saved to report';
    }catch(e){ saveStatus.textContent = 'Saved locally · server save failed. Use Save all to retry.'; pendingSaves.set(el_id+'|'+op, {el_id,op,html,sort}); }
  }else{ pendingSaves.delete(el_id+'|'+op); saveStatus.textContent = 'Saved locally';
  }
  persist();
}
async function clearEdit(el_id, op){
  pendingSaves.delete(el_id+'|'+op);
  if(op==='delete') return saveEdit(el_id,'restore');
  edits = edits.filter(e => !(e.el_id === el_id && e.op === op));
  persist();
  if(online){
    try{ await fetch('/api/edits', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({run, el_id, op: op === 'delete' ? 'restore' : op, html:'', sort:0})}); }catch{}
  }
}

// ------------------------------------------------------------- apply edits
const deletedOriginals = new Map();
function applyAll(){
  const sets = edits.filter(e => e.op === 'set');
  const styles = edits.filter(e => e.op === 'style');
  const dels = edits.filter(e => e.op === 'delete');
  const ins  = edits.filter(e => e.op === 'insert').sort((a,b) => (a.sort||0)-(b.sort||0));
  ins.forEach(e => insertFromEdit(e));
  collect();
  reindex();
  sets.sort((a,b)=>a.el_id.split('~').length-b.el_id.split('~').length).forEach(e => { const el = byId(e.el_id); if(el){ el.innerHTML = e.html; el.classList.add('p57-block-edited'); } });
  styles.forEach(e => {const el=byId(e.el_id);if(el)try{Object.entries(JSON.parse(e.html)).forEach(([key,value])=>el.style.setProperty(key,value));}catch{}});
  dels.forEach(e => { const el = byId(e.el_id); if(el && !el.dataset.delHidden) hideDeleted(el); });
  collect();reindex();cleanup();
}
function hideDeleted(el){
  el.dataset.delHidden = '1';
  deletedOriginals.set(el.dataset.el, el);
  el.hidden = true;
  cleanup();
}
async function removeElement(el){
  removeTools();remember({op:'delete',el,id:el.dataset.el});hideDeleted(el);
  await saveEdit(el.dataset.el,'delete');notice('Component removed. Layout space released.');
}
async function saveElement(el,html,before=el.innerHTML){
  if(html===before)return;
  const change=remember({op:'set',el,id:el.dataset.el,before,after:html,beforeStyle:el.style.cssText,afterStyle:el.style.cssText});
  el.innerHTML=html;el.classList.add('p57-block-edited');
  await saveEdit(el.dataset.el,'set',html);collect();reindex();cleanup();
  return change;
}
async function historyChange(from,to,reverse){
  if(editingEl)await commitEdit();
  const change=from.pop();if(!change)return;const el=byId(change.id)||change.el;
  removeTools();toast?.remove();
  if(change.op==='delete'||change.op==='insert'||change.op==='restore'){
    const restore=change.op==='delete'?reverse:!reverse;
    if(restore){delete el.dataset.delHidden;el.hidden=false;await clearEdit(change.id,'delete');}
    else{hideDeleted(el);await saveEdit(change.id,'delete');}
  }else if(change.op==='style'){
    el.style.cssText=reverse?change.beforeStyle:change.afterStyle;
    await saveEdit(change.id,'style',JSON.stringify(Object.fromEntries(Array.from(el.style).map(key=>[key,el.style.getPropertyValue(key)]))));
  }else{
    el.innerHTML=reverse?change.before:change.after;await saveEdit(change.id,'set',el.innerHTML);
    if(change.beforeStyle!==change.afterStyle){el.style.cssText=reverse?change.beforeStyle:change.afterStyle;await saveEdit(change.id,'style',JSON.stringify(Object.fromEntries(Array.from(el.style).map(key=>[key,el.style.getPropertyValue(key)]))));}
  }
  to.push(change);collect();reindex();cleanup();updateHistory();
}
const undoChange=()=>historyChange(undoStack,redoStack,true);
const redoChange=()=>historyChange(redoStack,undoStack,false);
function insertFromEdit(e){
  const split = e.el_id.lastIndexOf('::');
  const anchorId = e.el_id.slice(0, split), pos = e.el_id.slice(split+2).split(':')[0];
  if(byId(anchorId + '::ins:' + e.sort)) return;
  const anchor = byId(anchorId); if(!anchor) return;
  const holder = make('div');
  holder.innerHTML = e.html;
  const node = make('div', null, 'p57-block p57-block-inserted');
  node.dataset.el = anchorId + '::ins:' + e.sort;
  node.append(...holder.childNodes);
  if(pos === 'before') anchor.before(node); else anchor.after(node);
  blocks.push(node);
}

// ------------------------------------------------------------- layout mode
let layoutOn = false, banner = null, tools = null, hoverEl = null;
function setLayout(on){
  if(on){collect();cleanup();}
  layoutOn = on;
  root.classList.toggle('p57-layout-on', on);
  layoutBtn.textContent = on ? 'Finish editing' : 'Edit components';
  layoutBtn.setAttribute('aria-pressed', String(on));
  if(on){
    R.bar.hidden = true;
    document.querySelector('.p57-tool-trigger')?.setAttribute('aria-expanded','false');
    if(!banner){
      banner = make('div', null, 'p57-layout-banner');
      banner.append(make('span', 'Select a part or its container · edit, remove, or Undo. Ctrl/Cmd+Enter saves; Escape cancels.'));
      const done = make('button', 'Done'); done.onclick = () => setLayout(false);
      banner.append(done);
      document.body.append(banner);
    }
    banner.insertBefore(undoBtn,banner.lastElementChild);
    banner.insertBefore(redoBtn,banner.lastElementChild);
    banner.insertBefore(restoreBtn,banner.lastElementChild);
    banner.insertBefore(saveStatus,banner.lastElementChild);
    banner.hidden = false;
  }else if(banner){ commitEdit(); R.bar.append(undoBtn,redoBtn,restoreBtn,saveStatus); banner.hidden = true; removeTools(); }
}
function removeTools(){ if(tools){ tools.remove(); tools = null; } hoverEl?.classList.remove('p57-edit-selected');hoverEl = null; }
function toolsFor(el){
  if(!layoutOn || el.classList.contains('p57-block-deleted')) return removeTools();
  if(tools && hoverEl === el) return;
  removeTools();
  hoverEl = el;
  el.classList.add('p57-edit-selected');
  tools = make('div', null, 'p57-block-tools');
  tools.setAttribute('role', 'toolbar');
  tools.setAttribute('aria-label','Report component editing');
  const scope=make('select');scope.setAttribute('aria-label','Editing target');
  const targets=[['Selected part',el],['Table row',el.closest('tr')],['Containing component',model?.component(el)],['Whole block',el.closest('.p57-block')],['Whole chapter',el.closest('.wrap>section')]].filter((item,i,all)=>item[1]&&!all.slice(0,i).some(x=>x[1]===item[1]));
  targets.forEach(([label],i)=>{const option=make('option',label);option.value=i;scope.append(option);});
  scope.onchange=()=>{const target=targets[Number(scope.value)][1];if(!target.dataset.el){target.dataset.el=target.id+'~container';target.classList.add('p57-block');reindex();}toolsFor(target);};tools.append(scope);
  const mk = (label, title, fn, cls='') => { const b = make('button', label); b.title = title; b.className = cls; b.onclick = ev => { ev.stopPropagation(); fn(); }; tools.append(b); return b; };
  mk('Edit text', 'Edit this selection inline', () => beginEdit(el));
  mk('Design', 'Edit component markup and appearance', () => designComponent(el));
  mk('＋↑', 'Add a block above', () => addBlock(el, 'before'));
  mk('＋↓', 'Add a block below', () => addBlock(el, 'after'));
  mk('Remove', 'Remove the selected part or container; Undo remains available', () => removeElement(el), 'danger');
  mk('AI replace', 'Replace this component with AI', () => window.P57AI && window.P57AI.openForElement(el, 'rewrite'));
  mk('AI add', 'Add a component with AI', () => window.P57AI && window.P57AI.openForElement(el.closest('.p57-block') || el, 'create'));
  tools.contentEditable = 'false';
  document.body.append(tools);
  const rect = el.getBoundingClientRect();
  tools.style.top = Math.max(72, Math.min(innerHeight-65,rect.top-42))+'px';
  tools.style.left = Math.max(12, Math.min(innerWidth-480,rect.left))+'px';
}
document.addEventListener('mouseover', e => {
  if(!layoutOn) return;
  if(editingEl || e.target.closest('.p57-block-tools')) return;
  const b = e.target.closest('.p57-component,.p57-block');
  if(b && !b.closest('[data-del-hidden],[data-p57-empty]')) toolsFor(b);
});

// ------------------------------------------------------------- inline edit
let editingEl = null;
const pendingSaves = new Map();
try{JSON.parse(localStorage.getItem(localKey+':pending')||'[]').forEach(row=>pendingSaves.set(row.el_id+'|'+row.op,row));}catch{}
const saveStatus = make('span', '', 'p57-edit-status'); saveStatus.setAttribute('role','status'); R.bar.append(saveStatus);
const undoBtn=R.button('Undo change',undoChange),redoBtn=R.button('Redo change',redoChange);updateHistory();
const restoreBtn=R.button('Restore removed components',()=>{
  const form=make('div',null,'p57-component-inspector');
  const removed=edits.filter(row=>row.op==='delete'||(row.op==='set'&&byId(row.el_id)&&!model?.hasContent(byId(row.el_id))));
  if(!removed.length)form.append(make('p','No removed or cleared components in this report.'));
  removed.forEach(row=>{const el=byId(row.el_id)||deletedOriginals.get(row.el_id);if(!el)return;
    const item=make('div');item.append(make('p',el.tagName.toLowerCase()+' · '+(el.textContent.trim().slice(0,90)||row.el_id)));
    R.button(row.op==='delete'?'Restore':'Restore original content',async()=>{
      if(row.op==='delete'){delete el.dataset.delHidden;el.hidden=false;await clearEdit(row.el_id,'delete');remember({op:'restore',el,id:row.el_id});}
      else await saveElement(el,originalMarkup.get(row.el_id)||'');
      applyAll();R.dialog.close();
    },item);form.append(item);
  });R.openDialog('Restore removed components',form);
});
document.addEventListener('keydown',e=>{
  if(!layoutOn||editingEl||e.target.closest?.('input,textarea,select,[contenteditable="true"]')||!(e.ctrlKey||e.metaKey))return;
  const key=e.key.toLowerCase();
  if(key==='z'){e.preventDefault();e.shiftKey?redoChange():undoChange();}
  else if(key==='y'){e.preventDefault();redoChange();}
});
R.button('Save all changes', async () => { await commitEdit(); for(const [key,row] of [...pendingSaves]){ pendingSaves.delete(key); await saveEdit(row.el_id,row.op,row.html,row.sort); } });
document.addEventListener('click', e => {
  if(!layoutOn || e.target.closest('.p57-block-tools,.p57-layout-banner')) return;
  const target = e.target.closest('.p57-component,.p57-block');
  if(target && !editingEl){ e.preventDefault(); e.stopPropagation(); toolsFor(target); }
}, true);
document.addEventListener('dblclick', e => { if(layoutOn){ const target=e.target.closest('.p57-component,.p57-block'); if(target){e.preventDefault();beginEdit(target);} } });
function beginEdit(el, fresh=false){
  if(editingEl) commitEdit();
  removeTools();
  editingEl = el;
  el.classList.add('p57-block-editing');
  el.setAttribute('contenteditable', 'true');
  el.focus();
  const saveBar = make('div', null, 'p57-block-tools');
  saveBar.contentEditable = 'false';
  saveBar.style.top = '76px'; saveBar.style.left = '50%'; saveBar.style.transform = 'translateX(-50%)';
  const ok = make('button', 'Save'); ok.onclick = ev => { ev.stopPropagation(); commitEdit(); };
  const cancel = make('button', 'Cancel'); cancel.onclick = ev => { ev.stopPropagation(); cancelEdit(); };
  saveBar.append(ok, cancel);
  el.dataset.prevHtml = el.innerHTML;
  document.body.append(saveBar);
  el._saveBar = saveBar;
  el.addEventListener('keydown', editKeys);
}
function editKeys(e){
  if(e.key === 'Escape'){ e.preventDefault(); cancelEdit(); }
  if((e.metaKey || e.ctrlKey) && e.key === 'Enter'){ e.preventDefault(); commitEdit(); }
}
async function commitEdit(){
  const el = editingEl; if(!el) return;
  editingEl = null;
  el._saveBar?.remove();
  el.removeEventListener('keydown', editKeys);
  el.removeAttribute('contenteditable');
  el.classList.remove('p57-block-editing');
  const html = el.innerHTML;
  if(html === el.dataset.prevHtml) return;
  await saveElement(el,html,el.dataset.prevHtml);
}
function cancelEdit(){
  const el = editingEl; if(!el) return;
  editingEl = null;
  if(el.dataset.prevHtml !== undefined) el.innerHTML = el.dataset.prevHtml;
  el._saveBar?.remove();
  el.removeEventListener('keydown', editKeys);
  el.removeAttribute('contenteditable');
  el.classList.remove('p57-block-editing');
}

// Component inspector works for charts, metrics, tables and complete sections.
function designComponent(el){
  removeTools();
  const form=make('div',null,'p57-component-inspector');
  form.append(make('p','Change this component’s content and appearance. Edited figures are presentation overrides; source evidence remains unchanged.'));
  const label=make('label','Component HTML'), source=make('textarea');source.value=el.innerHTML;source.setAttribute('aria-label','Component HTML');label.append(source);form.append(label);
  const grid=make('div',null,'p57-design-grid');form.append(grid);
  const controls={};
  const fields=[['text-align','Alignment',['','left','center','right']],['font-size','Text size',['','14px','16px','20px','28px','36px']],['padding','Spacing',['','0px','12px','24px','36px']],['border-radius','Corners',['','0px','8px','16px','24px']],['background','Surface',['','var(--paper)','var(--soft)','var(--a1)']],['color','Text colour',['','var(--ink)','var(--mut)','var(--a1)','var(--paper)']]];
  fields.forEach(([key,title,values])=>{const label=make('label',title),select=make('select');select.setAttribute('aria-label',title);values.forEach(value=>{const o=make('option',value||'Inherit');o.value=value;select.append(o);});select.value=el.style.getPropertyValue(key);label.append(select);grid.append(label);controls[key]=select;});
  const status=make('p');status.setAttribute('role','status');form.append(status);
  R.button('Save component',async()=>{
    const holder=make('div');holder.innerHTML=source.value;
    holder.querySelectorAll('script,iframe,object,embed,style,link').forEach(node=>node.remove());
    holder.querySelectorAll('*').forEach(node=>[...node.attributes].forEach(attr=>{if(/^on/i.test(attr.name)||/javascript:/i.test(attr.value))node.removeAttribute(attr.name);}));
    const beforeStyle=el.style.cssText,change=await saveElement(el,holder.innerHTML);const style={};Object.entries(controls).forEach(([key,input])=>{style[key]=input.value;el.style.setProperty(key,input.value);});
    if(change)change.afterStyle=el.style.cssText;
    else if(beforeStyle!==el.style.cssText)remember({op:'style',el,id:el.dataset.el,beforeStyle,afterStyle:el.style.cssText});
    await saveEdit(el.dataset.el,'style',JSON.stringify(style));collect();cleanup();R.dialog.close();
  },form);
  R.openDialog('Component editor',form);
}

// ------------------------------------------------------------- add blocks
let addSeq = Date.now() % 100000;
async function addBlock(anchor, pos, html){
  removeTools();
  const node = make('div', null, 'p57-block p57-block-inserted');
  if(!html){
    const form=make('div',null,'p57-component-inspector'),select=make('select');select.setAttribute('aria-label','New component type');
    const templates={Paragraph:'<p>New report narrative</p>',Callout:'<div class="call"><h4>Key insight</h4><p>Add your insight here.</p></div>',Metrics:'<div class="kpis"><div class="kpi"><div class="l">Metric label</div><div class="v">n/a</div><div class="d">Selected reporting period</div></div></div>',List:'<ul><li>First action</li><li>Second action</li></ul>',Table:'<table><thead><tr><th>Measure</th><th>Value</th></tr></thead><tbody><tr><td>Metric</td><td>n/a</td></tr></tbody></table>',Chart:'<figure class="chart"><svg viewBox="0 0 400 160" role="img" aria-label="Chart placeholder"><rect x="40" y="40" width="320" height="80" fill="var(--soft)"></rect><text x="70" y="85" fill="var(--ink)">Add chart data in Design</text></svg><figcaption>Chart · selected reporting period</figcaption></figure>'};
    Object.keys(templates).forEach(value=>{const option=make('option',value);option.value=value;select.append(option);});form.append(make('p','Choose a component, then edit it inline or open Design for its HTML and appearance.'),select);
    R.button('Add component',()=>{R.dialog.close();addBlock(anchor,pos,templates[select.value]);},form);R.openDialog('Add report component',form);return;
  }
  anchor = anchor.closest('.p57-block') || anchor;
  node.dataset.el = anchor.dataset.el + '::ins:' + (++addSeq);
  node.innerHTML = html || '<p>New text — click to edit, or use ✦ AI to write it.</p>';
  if(pos === 'before') anchor.before(node); else anchor.after(node);
  blocks.push(node);
  await saveEdit(anchor.dataset.el + '::' + pos + ':' + addSeq, 'insert', node.innerHTML, addSeq);
  // keep the inserted node's id stable for future edits of the insert row
  node.dataset.el = anchor.dataset.el + '::ins:' + addSeq;
  remember({op:'insert',el:node,id:node.dataset.el});
  collect();
  beginEdit(node, true);
}

// ------------------------------------------------------------- toolbar hook
const layoutBtn = R.button('Edit components', () => setLayout(!layoutOn));
layoutBtn.title = 'Add, delete and edit any block in the report';
layoutBtn.setAttribute('aria-pressed', 'false');

window.P57Edit = {
  collect, blocks,
  get edits(){return edits;},
  commitEdit,
  saveElement, removeElement, undo:undoChange, redo:redoChange, cleanup,
  addBlock,
  insertAfter: (anchor, html) => addBlock(anchor, 'after', html),
  insertBefore: (anchor, html) => addBlock(anchor, 'before', html),
  refresh(){ collect(); applyAll(); },
  setLayout,
};
loadInitial();
apiEdits().then(applyAll);
window.addEventListener('p57:layout', e => setLayout(!!e.detail));
})();
