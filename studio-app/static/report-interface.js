(() => {
'use strict';
if(document.querySelector('.p57-reader-header'))return;
const header=document.createElement('nav');header.className='p57-reader-header';header.setAttribute('aria-label','Report actions');
const brand=document.createElement('a');brand.href='/#top';brand.target='_top';brand.setAttribute('aria-label','Physique 57 Intelligence home');brand.onclick=e=>{if(window.parent!==window){e.preventDefault();window.parent.postMessage({type:'p57-home'},location.origin);}};brand.className='p57-reader-brand';brand.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none"><defs><linearGradient id="p57-brand" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse"><stop stop-color="#2563eb"/><stop offset="1" stop-color="#7c3aed"/></linearGradient></defs><rect x="1" y="1" width="46" height="46" rx="14" fill="url(#p57-brand)"/><path d="M15 34V14h11a7 7 0 0 1 0 14H15" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M23 34h10" stroke="#a5f3fc" stroke-width="3.5" stroke-linecap="round"/><circle cx="34" cy="14" r="3" fill="#a5f3fc"/></svg><span>Studio Intelligence <small>Monthly performance review</small></span>';header.append(brand);
let records;try{records=JSON.parse(document.getElementById('p57-source-records')?.textContent||'null');}catch{}
if(records?.period){const period=document.createElement('span');period.className='p57-reader-period';period.textContent=records.period;header.append(period);}
const contents=document.querySelector('.p57-nav-trigger');if(contents)header.append(contents);
const edit=document.createElement('button');edit.type='button';edit.textContent='Edit report';
// Delegate to the existing editor control so save and finish semantics stay intact.
edit.onclick=()=>{const original=[...document.querySelectorAll('.p57-toolkit button')].find(b=>/^(Edit report text|Finish editing)$/.test(b.textContent.trim()));original?.click();};header.append(edit);
const tools=document.querySelector('.p57-tool-trigger');if(tools){tools.textContent='Settings';header.append(tools);}document.body.append(header);
const notes=document.getElementById('p57-notes-fab');if(notes)notes.textContent='Notes';
const observer=new MutationObserver(()=>{edit.textContent=document.documentElement.classList.contains('p57-layout-on')?'Finish editing':'Edit report';});observer.observe(document.documentElement,{attributes:true,attributeFilter:['class']});
})();
