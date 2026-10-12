/* Sticky notes, anywhere in the app or a report.
   Notes attach to the content under them, so they follow it when the layout
   reflows; a note can instead be pinned to the screen. Saved per page in this
   browser and kept in sync across open tabs. */
(() => {
'use strict';
if(window.P57Sticky)return;
const root=document.documentElement;
const KEY='p57-sticky:'+location.pathname;
const COLORS=[['lemon','Lemon'],['peach','Peach'],['mint','Mint'],['sky','Sky'],['lilac','Lilac'],['rose','Rose'],['graphite','Graphite']];
const ICON={
 note:'<path d="M5 4h14v10l-6 6H5z"/><path d="M13 20v-6h6"/>',
 pin:'<path d="M9 4h6l-1 6 4 3H6l4-3z"/><path d="M12 13v7"/>',
 min:'<path d="M6 12h12"/>',
 more:'<circle cx="6" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="18" cy="12" r="1.2"/>',
 close:'<path d="M6 6l12 12M18 6L6 18"/>',
 bold:'<path d="M7 5h6a3.5 3.5 0 0 1 0 7H7zM7 12h7a3.5 3.5 0 0 1 0 7H7z"/>',
 italic:'<path d="M14 5h-4M14 19h-4M13 5l-2 14"/>',
 under:'<path d="M7 4v7a5 5 0 0 0 10 0V4M6 20h12"/>',
 strike:'<path d="M5 12h14M16 7a4 3 0 0 0-8 0c0 4 8 2 8 7a4 3 0 0 1-8 0"/>',
 list:'<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
 check:'<rect x="3" y="4" width="6" height="6" rx="1.5"/><path d="M4.5 7l1.2 1.2L8 5.8M12 7h9M3 15h6v6H3zM12 18h9"/>',
 color:'<circle cx="12" cy="12" r="7"/>'
};
const svg=(n,cls='')=>`<svg class="p57-sn-i ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[n]}</svg>`;
const uid=()=>Math.random().toString(36).slice(2,10);
const now=()=>Date.now();
const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
// Notes are plain user text with a few formatting tags; keep it that way.
function sanitize(html){const t=document.createElement('template');t.innerHTML=html;const ok=new Set(['B','STRONG','I','EM','U','S','STRIKE','BR','DIV','P','UL','OL','LI','SPAN']);
 (function walk(n){for(const c of [...n.childNodes]){if(c.nodeType===1){if(!ok.has(c.tagName)){c.replaceWith(...c.childNodes);continue;}const keep=c.classList.contains('p57-sn-check')?['class','data-done']:[];for(const a of [...c.attributes])if(!keep.includes(a.name))c.removeAttribute(a.name);walk(c);}else if(c.nodeType!==3)c.remove();}})(t.content);
 return t.innerHTML;}
const ago=ts=>{const s=Math.round((now()-ts)/1000);if(s<45)return'just now';const m=Math.round(s/60);if(m<60)return m+'m ago';const h=Math.round(m/60);if(h<24)return h+'h ago';return new Date(ts).toLocaleDateString(undefined,{day:'numeric',month:'short'});};
const view=()=>document.querySelector('.view.on')?.id||'';

let notes=load(),hiddenAll=false,topZ=Math.max(10,...notes.map(n=>n.z||0));
function load(){try{const v=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(v)?v:[];}catch{return[];}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(notes));}catch{}updateCount();}

// Layers: one scrolls with the page, one stays on screen.
const layer=document.createElement('div');layer.className='p57-sn-layer';layer.setAttribute('aria-label','Sticky notes');
const fixed=document.createElement('div');fixed.className='p57-sn-layer p57-sn-fixed';
// On the root element so body margins (the contents sidebar) never offset them.
root.append(layer,fixed);
const els=new Map();

function anchorAt(x,y){
 const hit=document.elementsFromPoint(x,y).find(e=>!e.closest('.p57-sn,.p57-sn-layer,.p57-sn-menu,.p57-reader-header,.top,.p57-navigation,.p57-sn-placer')&&e!==document.body&&e!==root);
 const a=hit?.closest('[data-el],[id]');if(!a||a===document.body)return null;
 const sel=a.dataset.el?`[data-el="${CSS.escape(a.dataset.el)}"]`:'#'+CSS.escape(a.id);const idx=Math.max(0,[...document.querySelectorAll(sel)].indexOf(a));const r=a.getBoundingClientRect();return{sel,idx,dx:x-r.left,dy:y-r.top};
}
function pagePos(n){
 if(n.pinned)return{x:n.vx,y:n.vy};
 const a=n.anchor&&(document.querySelectorAll(n.anchor.sel)[n.anchor.idx||0]||document.querySelector(n.anchor.sel));
 if(a&&a.getClientRects().length){const r=a.getBoundingClientRect();return{x:r.left+scrollX+n.anchor.dx,y:r.top+scrollY+n.anchor.dy};}
 return{x:n.px,y:n.py};
}
function place(n){const el=els.get(n.id);if(!el)return;const p=pagePos(n);
 const maxX=(n.pinned?innerWidth:document.documentElement.scrollWidth)-60;el.style.left=Math.max(4,Math.min(p.x,maxX))+'px';el.style.top=Math.max(n.pinned?64:4,p.y)+'px';
 el.hidden=hiddenAll||(n.view&&n.view!==view());}
function placeAll(){notes.forEach(place);}

function build(n){
 const el=document.createElement('article');el.className='p57-sn';el.dataset.id=n.id;el.tabIndex=-1;el.setAttribute('aria-label','Sticky note');
 el.innerHTML=`<header class="p57-sn-bar"><span class="p57-sn-grip" aria-hidden="true"></span><button type="button" class="p57-sn-b p57-sn-color" title="Colour" aria-label="Change colour">${svg('color')}</button><span class="p57-sn-title"></span><button type="button" class="p57-sn-b p57-sn-pin" title="Pin to screen" aria-label="Pin to screen">${svg('pin')}</button><button type="button" class="p57-sn-b p57-sn-min" title="Collapse" aria-label="Collapse note">${svg('min')}</button><button type="button" class="p57-sn-b p57-sn-more" title="More" aria-label="More actions">${svg('more')}</button><button type="button" class="p57-sn-b p57-sn-del" title="Delete" aria-label="Delete note">${svg('close')}</button></header>
 <div class="p57-sn-body" contenteditable="true" spellcheck="true" role="textbox" aria-multiline="true" data-placeholder="Write a note… (- for bullets, [] for a checklist)"></div>
 <div class="p57-sn-tools" role="toolbar" aria-label="Formatting"><button type="button" data-cmd="bold" title="Bold (⌘B)">${svg('bold')}</button><button type="button" data-cmd="italic" title="Italic (⌘I)">${svg('italic')}</button><button type="button" data-cmd="underline" title="Underline (⌘U)">${svg('under')}</button><button type="button" data-cmd="strikeThrough" title="Strikethrough">${svg('strike')}</button><button type="button" data-cmd="insertUnorderedList" title="Bullets">${svg('list')}</button><button type="button" data-cmd="check" title="Checklist item">${svg('check')}</button></div>
 <footer class="p57-sn-foot"><span class="p57-sn-meta"></span><span class="p57-sn-progress" hidden></span></footer>
 <button type="button" class="p57-sn-chip" aria-label="Expand note"></button>`;
 const body=el.querySelector('.p57-sn-body');body.innerHTML=sanitize(n.html||'');
 const target=n.pinned?fixed:layer;target.append(el);els.set(n.id,el);
 refresh(n);place(n);
 // Keep report and editor handlers from reacting to clicks inside a note.
 for(const ev of ['pointerdown','click','dblclick','keydown','keyup','input'])el.addEventListener(ev,e=>e.stopPropagation());
 el.addEventListener('pointerdown',()=>front(n));
 el.addEventListener('focusin',()=>{el.classList.add('p57-sn-focus');front(n);});
 el.addEventListener('focusout',e=>{if(!el.contains(e.relatedTarget))el.classList.remove('p57-sn-focus');});
 // Dragging from the header bar.
 const bar=el.querySelector('.p57-sn-bar');
 bar.addEventListener('pointerdown',e=>{if(e.target.closest('button')||n.locked)return;e.preventDefault();bar.setPointerCapture(e.pointerId);el.classList.add('p57-sn-drag');
  const sx=e.clientX,sy=e.clientY,ox=parseFloat(el.style.left),oy=parseFloat(el.style.top);
  const move=ev=>{el.style.left=ox+ev.clientX-sx+'px';el.style.top=oy+ev.clientY-sy+'px';};
  const up=ev=>{bar.removeEventListener('pointermove',move);bar.removeEventListener('pointerup',up);el.classList.remove('p57-sn-drag');
   const r=el.getBoundingClientRect();
   if(n.pinned){n.vx=r.left;n.vy=r.top;}else{n.px=r.left+scrollX;n.py=r.top+scrollY;el.style.pointerEvents='none';n.anchor=anchorAt(r.left+4,r.top+4)||n.anchor;el.style.pointerEvents='';if(n.anchor){const a=document.querySelectorAll(n.anchor.sel)[n.anchor.idx||0];if(a){const ar=a.getBoundingClientRect();n.anchor.dx=r.left-ar.left;n.anchor.dy=r.top-ar.top;}}}
   touch(n,false);};
  bar.addEventListener('pointermove',move);bar.addEventListener('pointerup',up);});
 bar.addEventListener('keydown',e=>{if(n.locked||!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)||e.target.closest('.p57-sn-body'))return;e.preventDefault();const d=e.shiftKey?40:10;const k={ArrowUp:[0,-d],ArrowDown:[0,d],ArrowLeft:[-d,0],ArrowRight:[d,0]}[e.key];
  if(n.pinned){n.vx+=k[0];n.vy+=k[1];}else if(n.anchor){n.anchor.dx+=k[0];n.anchor.dy+=k[1];}else{n.px+=k[0];n.py+=k[1];}place(n);touch(n,false);});
 // Editing.
 let timer;body.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>{n.html=sanitize(body.innerHTML);touch(n);},250);});
 body.addEventListener('keydown',e=>{
  if(e.key==='Escape'){body.blur();return;}
  if(e.key===' '){const sel=getSelection();const node=sel.anchorNode;const line=(node?.nodeType===3?node.textContent:'').slice(0,sel.anchorOffset);
   if(line==='-'||line==='*'){e.preventDefault();node.textContent=node.textContent.slice(1);document.execCommand('insertUnorderedList');}
   else if(line==='[]'||line==='[ ]'){e.preventDefault();node.textContent=node.textContent.slice(line.length);makeCheck(body);}}
  if(e.key==='Enter'&&!e.shiftKey){const c=getSelection().anchorNode?.parentElement?.closest('.p57-sn-check');if(c){if(!c.textContent.trim()){e.preventDefault();c.replaceWith(Object.assign(document.createElement('div'),{innerHTML:'<br>'}));return;}setTimeout(()=>{const nc=getSelection().anchorNode?.parentElement?.closest('.p57-sn-check')||getSelection().anchorNode?.closest?.('.p57-sn-check');if(nc&&nc!==c)nc.dataset.done='false';},0);}}
 });
 body.addEventListener('click',e=>{const c=e.target.closest('.p57-sn-check');if(c&&e.offsetX<22){c.dataset.done=c.dataset.done==='true'?'false':'true';n.html=sanitize(body.innerHTML);touch(n);}});
 body.addEventListener('paste',e=>{e.preventDefault();const t=e.clipboardData.getData('text/plain');document.execCommand('insertText',false,t);});
 el.querySelector('.p57-sn-tools').addEventListener('mousedown',e=>e.preventDefault());
 el.querySelector('.p57-sn-tools').addEventListener('click',e=>{const b=e.target.closest('button');if(!b||n.locked)return;body.focus();if(b.dataset.cmd==='check')makeCheck(body);else document.execCommand(b.dataset.cmd);n.html=sanitize(body.innerHTML);touch(n);});
 // Header actions.
 el.querySelector('.p57-sn-del').onclick=()=>remove(n);
 el.querySelector('.p57-sn-min').onclick=()=>{n.collapsed=true;touch(n,false);refresh(n);};
 el.querySelector('.p57-sn-chip').onclick=()=>{n.collapsed=false;touch(n,false);refresh(n);el.querySelector('.p57-sn-body').focus();};
 el.querySelector('.p57-sn-pin').onclick=()=>togglePin(n);
 el.querySelector('.p57-sn-color').onclick=e=>menu(e.currentTarget,COLORS.map(([c,l])=>({label:l,swatch:c,on:n.color===c,run:()=>{n.color=c;touch(n,false);refresh(n);}})));
 el.querySelector('.p57-sn-more').onclick=e=>menu(e.currentTarget,[
  {label:n.locked?'Unlock':'Lock',run:()=>{n.locked=!n.locked;touch(n,false);refresh(n);}},
  {label:'Duplicate',run:()=>{const c=structuredClone(n);c.id=uid();c.created=c.updated=now();if(c.pinned){c.vx+=24;c.vy+=24;}else if(c.anchor){c.anchor.dx+=24;c.anchor.dy+=24;}else{c.px+=24;c.py+=24;}notes.push(c);save();build(c);}},
  {label:'Copy text',run:()=>navigator.clipboard?.writeText(body.innerText).catch(()=>{})},
  {label:'Bring to front',run:()=>front(n,true)},
  {label:'Delete',danger:true,run:()=>remove(n)}]);
 new ResizeObserver(()=>{if(n.collapsed)return;const w=el.offsetWidth,h=el.offsetHeight;if(Math.abs(w-(n.w||0))>2||Math.abs(h-(n.h||0))>2){n.w=w;n.h=h;clearTimeout(el._rs);el._rs=setTimeout(()=>save(),300);}}).observe(el);
 return el;
}
function makeCheck(body){const sel=getSelection();let block=sel.anchorNode;while(block&&block.parentElement!==body&&block!==body)block=block.parentElement;
 const item=document.createElement('div');item.className='p57-sn-check';item.dataset.done='false';
 if(block&&block!==body&&block.nodeType===1&&!block.matches('ul,ol')){item.innerHTML=block.innerHTML||'<br>';block.replaceWith(item);}
 else if(block&&block.nodeType===3){item.textContent=block.textContent;block.replaceWith(item);if(!item.textContent)item.innerHTML='<br>';}
 else{item.innerHTML='<br>';body.append(item);}
 const r=document.createRange();r.selectNodeContents(item);r.collapse(false);sel.removeAllRanges();sel.addRange(r);}
function refresh(n){const el=els.get(n.id);if(!el)return;
 el.dataset.color=n.color||'lemon';el.classList.toggle('p57-sn-collapsed',!!n.collapsed);el.classList.toggle('p57-sn-locked',!!n.locked);el.classList.toggle('p57-sn-pinned',!!n.pinned);
 el.style.zIndex=n.z||10;if(!n.collapsed){if(n.w)el.style.width=n.w+'px';if(n.h)el.style.height=n.h+'px';}else{el.style.width='';el.style.height='';}
 const body=el.querySelector('.p57-sn-body');body.contentEditable=String(!n.locked);
 const text=body.innerText.trim();el.querySelector('.p57-sn-title').textContent=n.locked?'Locked':'';
 el.querySelector('.p57-sn-chip').textContent=text.split('\n')[0].slice(0,28)||'Note';
 const pin=el.querySelector('.p57-sn-pin');pin.setAttribute('aria-pressed',String(!!n.pinned));pin.title=n.pinned?'Attach to page':'Pin to screen';
 const checks=[...body.querySelectorAll('.p57-sn-check')];const prog=el.querySelector('.p57-sn-progress');prog.hidden=!checks.length;
 if(checks.length){const done=checks.filter(c=>c.dataset.done==='true').length;prog.textContent=`${done}/${checks.length} done`;prog.style.setProperty('--p',done/checks.length);}
 const words=text?text.split(/\s+/).length:0;el.querySelector('.p57-sn-meta').textContent=`${ago(n.updated||n.created)}${words?' · '+words+' word'+(words===1?'':'s'):''}`;}
function touch(n,content=true){if(content)n.updated=now();save();refresh(n);}
function front(n,force){if(!force&&(n.z||0)>=topZ)return;n.z=++topZ;const el=els.get(n.id);if(el)el.style.zIndex=n.z;save();}
function togglePin(n){const el=els.get(n.id);const r=el.getBoundingClientRect();n.pinned=!n.pinned;
 if(n.pinned){n.vx=r.left;n.vy=r.top;}else{n.px=r.left+scrollX;n.py=r.top+scrollY;el.style.pointerEvents='none';n.anchor=anchorAt(r.left+4,r.top+4);el.style.pointerEvents='';}
 el.remove();els.delete(n.id);build(n);touch(n,false);}

function create(at,opts={}){
 const vx=at?.x??innerWidth/2-130+(notes.length%5)*18,vy=at?.y??innerHeight/2-90+(notes.length%5)*18;
 const n={id:uid(),html:'',color:opts.color||COLORS[notes.length%COLORS.length][0],created:now(),updated:now(),z:++topZ,view:view(),pinned:false,px:vx+scrollX,py:vy+scrollY,anchor:null};
 n.anchor=anchorAt(vx+4,vy+4);
 if(hiddenAll)setHidden(false);
 notes.push(n);save();const el=build(n);el.classList.add('p57-sn-new');setTimeout(()=>el.classList.remove('p57-sn-new'),400);
 el.querySelector('.p57-sn-body').focus();return n;}
let undo=null;
function remove(n){const el=els.get(n.id);const i=notes.indexOf(n);if(i<0)return;notes.splice(i,1);save();
 el.classList.add('p57-sn-out');setTimeout(()=>{el.remove();els.delete(n.id);},180);
 toast('Note deleted',()=>{notes.splice(Math.min(i,notes.length),0,n);save();build(n);});}
function toast(text,action){document.querySelector('.p57-sn-toast')?.remove();clearTimeout(undo);
 const t=document.createElement('div');t.className='p57-sn-toast';t.setAttribute('role','status');t.textContent=text;
 if(action){const b=document.createElement('button');b.type='button';b.textContent='Undo';b.onclick=()=>{action();t.remove();};t.append(b);}
 document.body.append(t);undo=setTimeout(()=>t.remove(),5000);}

// Small popover used by the colour picker, the note menu and the board.
function menu(anchor,items,extra){document.querySelector('.p57-sn-menu')?.remove();
 const m=document.createElement('div');m.className='p57-sn-menu';m.setAttribute('role','menu');
 if(extra)m.append(extra);
 for(const it of items){if(it.sep){m.append(Object.assign(document.createElement('hr')));continue;}const b=document.createElement('button');b.type='button';b.setAttribute('role','menuitem');
  if(it.swatch){b.className='p57-sn-swatch';b.dataset.color=it.swatch;b.setAttribute('aria-pressed',String(!!it.on));}
  if(it.danger)b.classList.add('p57-sn-danger');b.innerHTML=(it.swatch?'<i></i>':'')+'<span></span>'+(it.hint?'<kbd></kbd>':'');b.querySelector('span').textContent=it.label;if(it.hint)b.querySelector('kbd').textContent=it.hint;
  b.onclick=()=>{m.remove();it.run();};m.append(b);}
 document.body.append(m);const r=anchor.getBoundingClientRect();const w=m.offsetWidth,h=m.offsetHeight;
 m.style.left=Math.max(8,Math.min(r.left,innerWidth-w-8))+'px';m.style.top=(r.bottom+6+h>innerHeight?Math.max(8,r.top-h-6):r.bottom+6)+'px';
 for(const ev of ['pointerdown','click','keydown'])m.addEventListener(ev,e=>e.stopPropagation());
 setTimeout(()=>{const off=e=>{if(!m.contains(e.target)){m.remove();removeEventListener('pointerdown',off,true);}};addEventListener('pointerdown',off,true);},0);
 m.addEventListener('keydown',e=>{if(e.key==='Escape'){m.remove();anchor.focus();}});
 (m.querySelector('input')||m.querySelector('button'))?.focus();return m;}

// Click-to-place mode.
function startPlacing(){const p=document.createElement('div');p.className='p57-sn-placer';p.innerHTML='<span>Click anywhere to drop a note · Esc to cancel</span>';document.body.append(p);
 const done=()=>{p.remove();removeEventListener('keydown',key,true);};const key=e=>{if(e.key==='Escape'){e.stopPropagation();done();}};addEventListener('keydown',key,true);
 p.addEventListener('click',e=>{done();create({x:e.clientX-12,y:e.clientY-12});});}
function setHidden(v){hiddenAll=v;root.classList.toggle('p57-sn-hidden',v);placeAll();}

// Board: every note on this page, searchable.
function board(anchor){
 const wrap=document.createElement('div');wrap.className='p57-sn-board';
 const head=document.createElement('div');head.className='p57-sn-board-head';head.innerHTML='<strong>Sticky notes</strong>';
 const search=document.createElement('input');search.type='search';search.placeholder='Search notes';search.setAttribute('aria-label','Search notes');
 const list=document.createElement('div');list.className='p57-sn-board-list';
 const fill=()=>{const q=search.value.toLowerCase();const items=notes.filter(n=>!n.view||n.view===view()).filter(n=>!q||sanitizeText(n.html).toLowerCase().includes(q));
  list.replaceChildren(...(items.length?items.map(n=>{const b=document.createElement('button');b.type='button';b.dataset.color=n.color;b.innerHTML='<i></i><span></span><small></small>';b.querySelector('span').textContent=sanitizeText(n.html).slice(0,60)||'Empty note';b.querySelector('small').textContent=ago(n.updated||n.created);
   b.onclick=()=>{document.querySelector('.p57-sn-menu')?.remove();jump(n);};return b;}):[Object.assign(document.createElement('p'),{textContent:notes.length?'No notes match.':'No notes on this page yet.'})]));};
 search.oninput=fill;fill();head.append(search);wrap.append(head,list);
 menu(anchor,[
  {label:'New note',hint:'⌥⇧N',run:()=>create()},
  {label:'Place a note…',run:startPlacing},
  {label:hiddenAll?'Show notes':'Hide notes',run:()=>setHidden(!hiddenAll)},
  {sep:true},
  {label:'Export as Markdown',run:exportMd},
  {label:'Delete all on this page',danger:true,run:()=>{const keep=notes.slice();const gone=notes.filter(n=>!n.view||n.view===view());if(!gone.length)return;notes=notes.filter(n=>!gone.includes(n));gone.forEach(n=>{els.get(n.id)?.remove();els.delete(n.id);});save();toast(`${gone.length} note${gone.length>1?'s':''} deleted`,()=>{notes=keep;save();keep.forEach(n=>{if(!els.has(n.id))build(n);});});}}
 ],wrap);
}
function sanitizeText(html){const d=document.createElement('div');d.innerHTML=sanitize(html||'');d.querySelectorAll('div,li,br').forEach(e=>e.append(' '));return d.textContent.replace(/\s+/g,' ').trim();}
function jump(n){setHidden(false);const el=els.get(n.id);if(!el)return;if(n.collapsed){n.collapsed=false;refresh(n);}if(!n.pinned){const top=parseFloat(el.style.top)-innerHeight/3;scrollTo({top,behavior:'smooth'});}front(n,true);el.classList.add('p57-sn-flash');setTimeout(()=>el.classList.remove('p57-sn-flash'),900);el.querySelector('.p57-sn-body').focus({preventScroll:true});}
function exportMd(){const md=`# Sticky notes — ${document.title}\n\n`+notes.map(n=>{const d=document.createElement('div');d.innerHTML=sanitize(n.html);d.querySelectorAll('.p57-sn-check').forEach(c=>c.prepend(c.dataset.done==='true'?'- [x] ':'- [ ] '));d.querySelectorAll('li').forEach(li=>li.prepend('- '));d.querySelectorAll('div,li,br').forEach(e=>e.append('\n'));return d.textContent.replace(/\n{3,}/g,'\n\n').trim();}).join('\n\n---\n\n')+'\n';
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([md],{type:'text/markdown'}));a.download='sticky-notes.md';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}

// Toolbar button: in a report's header, or the app's top bar.
const trigger=document.createElement('button');trigger.type='button';trigger.className='p57-sn-trigger';trigger.setAttribute('aria-label','Sticky notes');trigger.title='Sticky notes (⌥⇧N for a new note)';
trigger.innerHTML=svg('note','p57-hicon')+'<span class="p57-hl">Sticky</span><span class="p57-sn-count" hidden></span>';
trigger.onclick=()=>board(trigger);
const header=document.querySelector('.p57-reader-header');
if(header){const g=document.createElement('div');g.className='p57-hgroup';g.append(trigger);const present=[...header.children].find(c=>c.tagName==='BUTTON');present?header.insertBefore(g,present):header.append(g);}
else{const hact=document.querySelector('.hact');trigger.classList.add('btn','ghost','sm');hact?hact.prepend(trigger):document.body.append(trigger);}
function updateCount(){const c=trigger.querySelector('.p57-sn-count');const k=notes.filter(n=>!n.view||n.view===view()).length;c.hidden=!k;c.textContent=k;}

addEventListener('keydown',e=>{if(e.altKey&&e.shiftKey&&e.code==='KeyN'){e.preventDefault();create();}});
let raf=0;const relayout=()=>{cancelAnimationFrame(raf);raf=requestAnimationFrame(placeAll);};
addEventListener('resize',relayout);new ResizeObserver(relayout).observe(document.body);
document.fonts?.ready.then(relayout);
new MutationObserver(()=>{relayout();updateCount();}).observe(document.body,{attributes:true,attributeFilter:['class']});
document.querySelectorAll('.view').forEach(v=>new MutationObserver(()=>{relayout();updateCount();}).observe(v,{attributes:true,attributeFilter:['class']}));
addEventListener('storage',e=>{if(e.key!==KEY)return;els.forEach(el=>el.remove());els.clear();notes=load();notes.forEach(build);updateCount();});
setInterval(()=>notes.forEach(n=>{const el=els.get(n.id);if(el&&!el.contains(document.activeElement))el.querySelector('.p57-sn-meta')&&refresh(n);}),60000);
notes.forEach(build);updateCount();
window.P57Sticky={create,remove:id=>{const n=notes.find(x=>x.id===id);if(n)remove(n);},list:()=>notes.slice(),setHidden};
})();
