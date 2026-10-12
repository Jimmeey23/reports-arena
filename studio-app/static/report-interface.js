(() => {
'use strict';
if(document.querySelector('.p57-reader-header'))return;
const root=document.documentElement;
const embedded=window.parent!==window;if(embedded)root.classList.add('p57-embedded');
const ICONS={
 contents:'<path d="M4 6h16M4 12h10M4 18h13"/>',
 edit:'<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
 settings:'<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
 notes:'<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
 ai:'<path d="M12 3l1.8 4.6L18.5 9l-4.7 1.6L12 15l-1.8-4.4L5.5 9l4.7-1.4z"/><path d="M18 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>'
};
function icon(name){return `<svg class="p57-hicon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;}
function label(button,name,text){button.innerHTML=icon(name)+'<span class="p57-hl"></span>';button.querySelector('.p57-hl').textContent=text;button.title=text;}
function group(...items){const g=document.createElement('div');g.className='p57-hgroup';g.append(...items.filter(Boolean));return g;}

const header=document.createElement('nav');header.className='p57-reader-header';header.setAttribute('aria-label','Report actions');
const brand=document.createElement('a');brand.href='/#top';brand.target='_top';brand.setAttribute('aria-label','Physique 57 Intelligence home');brand.onclick=e=>{if(embedded){e.preventDefault();window.parent.postMessage({type:'p57-home'},location.origin);}};brand.className='p57-reader-brand';brand.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none" aria-hidden="true"><rect x="1" y="1" width="46" height="46" rx="13" fill="#12313b"/><path d="M15 34V14h11a7 7 0 0 1 0 14H15" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M23 34h10" stroke="#8fd3c7" stroke-width="3.5" stroke-linecap="round"/><circle cx="34" cy="14" r="3" fill="#8fd3c7"/></svg><span>Physique 57 Intelligence <small>Monthly performance review</small></span>';header.append(brand);
let records;try{records=JSON.parse(document.getElementById('p57-source-records')?.textContent||'null');}catch{}
const context=document.createElement('div');context.className='p57-reader-context';
if(records?.period){const period=document.createElement('span');period.className='p57-reader-period';period.textContent=records.period;context.append(period);}
header.append(context);

const contents=document.querySelector('.p57-nav-trigger');if(contents)label(contents,'contents','Contents');
const edit=document.createElement('button');edit.type='button';label(edit,'edit','Edit report');
// Delegate to the existing editor control so save and finish semantics stay intact.
edit.onclick=()=>{const original=[...document.querySelectorAll('.p57-toolkit button')].find(b=>/^(Edit report text|Finish editing)$/.test(b.textContent.trim()));original?.click();};
const tools=document.querySelector('.p57-tool-trigger');if(tools){label(tools,'settings','Settings');tools.setAttribute('aria-label','Report settings');}
// Notes and the assistant live in the toolbar so nothing floats over the report.
const notes=document.getElementById('p57-notes-fab');if(notes){label(notes,'notes','Notes');notes.classList.add('p57-docked');}
const ai=document.getElementById('p57-ai-fab');if(ai){label(ai,'ai','Ask AI');ai.classList.add('p57-docked');}
header.append(group(contents),group(edit,tools),group(notes,ai));
document.body.append(header);
const observer=new MutationObserver(()=>{const on=root.classList.contains('p57-layout-on');edit.querySelector('.p57-hl').textContent=on?'Finish editing':'Edit report';edit.setAttribute('aria-pressed',String(on));});observer.observe(root,{attributes:true,attributeFilter:['class']});

// Settings: one sheet, grouped by what each control is for.
const bar=document.querySelector('.p57-toolkit');
if(bar){
 const head=bar.querySelector('.p57-panel-head');head?.querySelector('strong')&&(head.querySelector('strong').textContent='Settings');
 const text=el=>(el.tagName==='LABEL'?el.firstChild?.textContent:el.textContent||'').trim();
 const rules=[
  ['Appearance','Theme, colour and reading width.',el=>el.tagName==='LABEL'&&/^(Theme|Colour|Layout|Density|Text)$/.test(text(el))],
  ['Find','Search the report or jump to a section.',el=>el.matches('select[aria-label="Jump to section"],input[placeholder^="Find"],.rt-status')||/^Next match$/.test(text(el))],
  ['Reading','Evidence, charts and read-aloud.',el=>/^(Charts|Expand evidence|Collapse|Read section|Pause|Pause chapter motion|Resume chapter motion)$/.test(text(el))||(el.tagName==='LABEL'&&/^Speed/.test(text(el)))],
  ['Presenting','Notes, prompter and slides.',el=>/^(Present|Teleprompter|Speaker notes)/.test(text(el))],
  ['Editing and export','Changes stay in this browser until you download.',el=>el.matches('.p57-edit-status,.p57-save-status')||/^(Edit report text|Finish editing|Edit components|Save all changes|Download edited report|Print \/ PDF)/.test(text(el))],
  ['Guided session',null,el=>el.matches('.p57-session')]
 ];
 const sections=rules.map(([title,hint])=>{const s=document.createElement('section');s.className='p57-tool-section';s.dataset.group=title;const h=document.createElement('h4');h.textContent=title;s.append(h);if(hint){const p=document.createElement('p');p.className='p57-tool-hint';p.textContent=hint;s.append(p);}const body=document.createElement('div');body.className='p57-tool-body';s.append(body);return s;});
 const more=document.createElement('div');more.className='p57-tool-body';
 for(const el of [...bar.children]){
  if(el===head||el.matches('.rt-brand'))continue;
  if(el.matches('.p57-library-link')){continue;}
  const i=rules.findIndex(r=>r[2](el));
  (i>=0?sections[i].querySelector('.p57-tool-body'):more).append(el);
 }
 const session=sections[5];const block=session.querySelector('.p57-session');if(block){block.querySelector('h3')?.remove();}
 const scroller=document.createElement('div');scroller.className='p57-tool-scroll';
 scroller.append(...sections.filter(s=>s.querySelector('.p57-tool-body').children.length));
 if(more.children.length){const s=document.createElement('section');s.className='p57-tool-section';const h=document.createElement('h4');h.textContent='More';s.append(h,more);scroller.append(s);}
 const library=bar.querySelector('.p57-library-link');if(library){library.textContent='Back to report library';scroller.append(library);}
 bar.append(scroller);
}

// Right-hand sheets share one slot: opening one closes the others, and on
// wide screens the report reflows beside it instead of sitting underneath.
const sheets=[bar,document.querySelector('.p57-ai-panel'),document.querySelector('.p57-speaker')].filter(Boolean);
let syncing=false;
const sheetObserver=new MutationObserver(records=>{
 if(syncing)return;syncing=true;
 const opened=records.map(r=>r.target).find(t=>!t.hidden);
 if(opened)for(const s of sheets)if(s!==opened&&!s.hidden){s.hidden=true;if(s.matches('.p57-speaker'))root.classList.remove('p57-right-open');}
 root.classList.toggle('p57-sheet-open',sheets.some(s=>!s.hidden&&!s.matches('.p57-speaker')));
 tools?.setAttribute('aria-expanded',String(!!bar&&!bar.hidden));
 ai?.setAttribute('aria-pressed',String(!document.querySelector('.p57-ai-panel')?.hidden));
 syncing=false;
});
for(const s of sheets)sheetObserver.observe(s,{attributes:true,attributeFilter:['hidden']});

// On narrow screens the contents list covers the report, so start closed and
// close it again once a destination is chosen.
const narrow=()=>!!window.matchMedia&&window.matchMedia('(max-width:900px)').matches;
const nav=document.querySelector('.p57-navigation');
if(nav&&narrow()&&!nav.hidden)contents?.click();
nav?.addEventListener('click',e=>{if(narrow()&&e.target.closest('.p57-nav-list button')&&!nav.hidden)contents?.click();});
})();
