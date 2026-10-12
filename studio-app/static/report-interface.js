(() => {
'use strict';
if(document.querySelector('.p57-reader-header'))return;
const header=document.createElement('nav');header.className='p57-reader-header';header.setAttribute('aria-label','Report actions');
const brand=document.createElement('div');brand.className='p57-reader-brand';brand.innerHTML='<b>P57</b><span>Studio Intelligence / Monthly review</span>';header.append(brand);
let records;try{records=JSON.parse(document.getElementById('p57-source-records')?.textContent||'null');}catch{}
if(records?.period){const period=document.createElement('span');period.className='p57-reader-period';period.textContent=records.period;header.append(period);}
const contents=document.querySelector('.p57-nav-trigger');if(contents)header.append(contents);
const edit=document.createElement('button');edit.type='button';edit.textContent='Edit report';
// Delegate to the existing editor control so save and finish semantics stay intact.
edit.onclick=()=>{const original=[...document.querySelectorAll('.p57-toolkit button')].find(b=>/^(Edit report text|Finish editing)$/.test(b.textContent.trim()));original?.click();};header.append(edit);
const tools=document.querySelector('.p57-tool-trigger');if(tools){tools.textContent='Settings & tools';header.append(tools);}document.body.append(header);
const notes=document.getElementById('p57-notes-fab');if(notes)notes.textContent='Notes';
const observer=new MutationObserver(()=>{edit.textContent=document.documentElement.classList.contains('p57-layout-on')?'Finish editing':'Edit report';});observer.observe(document.documentElement,{attributes:true,attributeFilter:['class']});
})();
