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

// ------------------------------------------------------------- block model
const blocks = [];
const elIndex = new Map();
function reindex(){ elIndex.clear(); document.querySelectorAll('[data-el]').forEach(e => elIndex.set(e.dataset.el, e)); }
function byId(id){
  if(!elIndex.has(id)) reindex();
  return elIndex.get(id) || null;
}
function sectionId(sec, i){ return sec.id || ('p57-sec-' + i); }
function collect(){
  blocks.length = 0;
  elIndex && elIndex.clear && elIndex.clear();
  const secs = [...document.querySelectorAll('.wrap section')];
  if(!secs.length){
    // single-chapter pages without <section> wrappers
    const wrap = document.querySelector('.wrap');
    if(wrap) secs.push(wrap);
  }
  secs.forEach((sec, si) => {
    sec.id = sectionId(sec, si);
    [...sec.children].forEach((el, i) => {
      if(el.classList.contains('p57-chapter-hero') || el.classList.contains('p57-block-deleted')) return;
      if(!el.dataset.el) el.dataset.el = sec.id + '~' + i;
      el.classList.add('p57-block');
      blocks.push(el);
    });
  });
}
collect();

// ------------------------------------------------------------- persistence
let edits = [];           // rows: {el_id, op, html, sort}
function persist(){
  if(online) return;      // server already stored it
  try{ localStorage.setItem(localKey, JSON.stringify(edits)); }catch{}
}
function loadInitial(){
  try{ edits = JSON.parse(localStorage.getItem(localKey) || '[]'); }catch{ edits = []; }
}
async function apiEdits(){
  if(!online) return loadInitial();
  try{
    const res = await fetch('/api/edits?run=' + encodeURIComponent(run));
    const data = await res.json();
    edits = data.edits || [];
  }catch{ loadInitial(); }
}
async function saveEdit(el_id, op, html='', sort=0){
  edits = edits.filter(e => !(e.el_id === el_id && e.op === op));
  if(op !== 'delete' || html !== null) edits.push({el_id, op, html, sort});
  persist();
  if(online){
    try{ await fetch('/api/edits', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({run, el_id, op, html, sort})}); }catch{}
  }
}
async function clearEdit(el_id, op){
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
  const dels = edits.filter(e => e.op === 'delete');
  const ins  = edits.filter(e => e.op === 'insert').sort((a,b) => (a.sort||0)-(b.sort||0));
  sets.forEach(e => { const el = byId(e.el_id); if(el){ el.innerHTML = e.html; el.classList.add('p57-block-edited'); } });
  dels.forEach(e => { const el = byId(e.el_id); if(el && !el.dataset.delHidden) hideDeleted(el); });
  ins.forEach(e => insertFromEdit(e));
}
function hideDeleted(el){
  el.dataset.delHidden = '1';
  const ph = make('div', null, 'p57-block-deleted');
  ph.dataset.for = el.dataset.el;
  ph.append(make('span', 'A block was removed here.'));
  const undo = make('button', 'Undo');
  undo.onclick = async () => { delete el.dataset.delHidden; ph.remove(); el.hidden = false; await clearEdit(el.dataset.el, 'delete'); };
  const really = make('button', 'Keep removed');
  really.onclick = () => { ph.style.opacity = '.55'; really.disabled = true; really.textContent = 'Removed'; };
  ph.append(undo, really);
  deletedOriginals.set(el.dataset.el, el);
  el.hidden = true;
  el.after(ph);
}
function insertFromEdit(e){
  const [anchorId, pos] = e.el_id.split('::');
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
  layoutOn = on;
  root.classList.toggle('p57-layout-on', on);
  layoutBtn.textContent = on ? 'Finish layout' : 'Layout';
  layoutBtn.setAttribute('aria-pressed', String(on));
  if(on){
    if(!banner){
      banner = make('div', null, 'p57-layout-banner');
      banner.append(make('span', 'Layout editing — hover any block for tools. Changes save automatically.'));
      const done = make('button', 'Done'); done.onclick = () => setLayout(false);
      banner.append(done);
      document.body.append(banner);
    }
    banner.hidden = false;
  }else if(banner){ banner.hidden = true; removeTools(); }
}
function removeTools(){ if(tools){ tools.remove(); tools = null; } hoverEl = null; }
function toolsFor(el){
  if(!layoutOn || el.classList.contains('p57-block-deleted')) return removeTools();
  if(tools && hoverEl === el) return;
  removeTools();
  hoverEl = el;
  tools = make('div', null, 'p57-block-tools');
  tools.setAttribute('role', 'toolbar');
  const mk = (label, title, fn, cls='') => { const b = make('button', label); b.title = title; b.className = cls; b.onclick = ev => { ev.stopPropagation(); fn(); }; tools.append(b); return b; };
  mk('✎', 'Edit this block', () => beginEdit(el));
  mk('＋↑', 'Add a block above', () => addBlock(el, 'before'));
  mk('＋↓', 'Add a block below', () => addBlock(el, 'after'));
  mk('🗑', 'Delete this block', () => { removeTools(); hideDeleted(el); saveEdit(el.dataset.el, 'delete'); }, 'danger');
  mk('✦', 'Rewrite with AI', () => window.P57AI && window.P57AI.openForElement(el, 'rewrite'));
  el.append(tools);
}
document.addEventListener('mouseover', e => {
  if(!layoutOn) return;
  const b = e.target.closest('.p57-block');
  if(b && !b.contains(tools)) toolsFor(b);
});

// ------------------------------------------------------------- inline edit
let editingEl = null;
function beginEdit(el, fresh=false){
  if(editingEl) commitEdit();
  removeTools();
  editingEl = el;
  el.classList.add('p57-block-editing');
  el.setAttribute('contenteditable', 'true');
  el.focus();
  const saveBar = make('div', null, 'p57-block-tools');
  saveBar.style.top = ''; saveBar.style.bottom = '-15px';
  const ok = make('button', 'Save'); ok.onclick = ev => { ev.stopPropagation(); commitEdit(); };
  const cancel = make('button', 'Cancel'); cancel.onclick = ev => { ev.stopPropagation(); cancelEdit(); };
  saveBar.append(ok, cancel);
  el.dataset.prevHtml = el.innerHTML;
  el.append(saveBar);
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
  if(el.dataset.el.includes('::ins:')) await saveEdit(el.dataset.el, 'set', html);
  else await saveEdit(el.dataset.el, 'set', html);
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

// ------------------------------------------------------------- add blocks
let addSeq = Date.now() % 100000;
async function addBlock(anchor, pos, html){
  removeTools();
  const node = make('div', null, 'p57-block p57-block-inserted');
  node.dataset.el = anchor.dataset.el + '::ins:' + (++addSeq);
  node.innerHTML = html || '<p>New text — click to edit, or use ✦ AI to write it.</p>';
  if(pos === 'before') anchor.before(node); else anchor.after(node);
  blocks.push(node);
  await saveEdit(anchor.dataset.el + '::' + pos, 'insert', node.innerHTML, addSeq);
  // keep the inserted node's id stable for future edits of the insert row
  node.dataset.el = anchor.dataset.el + '::ins:' + addSeq;
  beginEdit(node, true);
}

// ------------------------------------------------------------- toolbar hook
const layoutBtn = R.button('Layout', () => setLayout(!layoutOn));
layoutBtn.title = 'Add, delete and edit any block in the report';
layoutBtn.setAttribute('aria-pressed', 'false');

window.P57Edit = {
  collect, blocks,
  saveElement: (el, html) => saveEdit(el.dataset.el, 'set', html),
  insertAfter: (anchor, html) => addBlock(anchor, 'after', html),
  insertBefore: (anchor, html) => addBlock(anchor, 'before', html),
  refresh(){ collect(); applyAll(); },
  setLayout,
};
apiEdits().then(applyAll);
window.addEventListener('p57:layout', e => setLayout(!!e.detail));
})();
