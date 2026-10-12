/* Notes sheet, simplified: it opens on bulleted talking points for the section
   on screen, drawn from that section's own summary, figures and findings.
   Private notes and the teleprompter stay one tap away. */
(() => {
'use strict';
const drawer=document.querySelector('.p57-speaker');if(!drawer||drawer.querySelector('.p57-talk'))return;
const head=drawer.querySelector('.p57-speaker-head');
const clean=t=>(t||'').replace(/\s+/g,' ').trim();
const firstSentence=t=>{t=clean(t);const m=t.match(/^(.{30,220}?[.!?])(\s|$)/);return m?m[1]:t.length>200?t.slice(0,200).replace(/\s+\S*$/,'')+'…':t;};

// Views: points / my notes / prompter, as one segmented control.
const tabs=document.createElement('div');tabs.className='p57-talk-tabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Speaker view');
const views=[['points','Points'],['notes','My notes'],['prompter','Prompter']];
for(const [id,label] of views){const b=document.createElement('button');b.type='button';b.textContent=label;b.dataset.view=id;b.setAttribute('role','tab');b.onclick=()=>setView(id);tabs.append(b);}
const talk=document.createElement('section');talk.className='p57-talk';talk.setAttribute('aria-live','polite');
const where=document.createElement('p');where.className='p57-talk-where';
const title=document.createElement('h3');
const list=document.createElement('ul');list.className='p57-talk-list';
const foot=document.createElement('div');foot.className='p57-talk-foot';
const copy=document.createElement('button');copy.type='button';copy.textContent='Copy points';
copy.onclick=async()=>{const text=title.textContent+'\n'+[...list.children].map(li=>'• '+li.textContent).join('\n');try{await navigator.clipboard.writeText(text);copy.textContent='Copied';setTimeout(()=>copy.textContent='Copy points',1400);}catch{copy.textContent='Copy unavailable';}};
const toNotes=document.createElement('button');toNotes.type='button';toNotes.textContent='Add a note';toNotes.onclick=()=>{setView('notes');drawer.querySelector('.p57-notes-panel textarea')?.focus();};
foot.append(copy,toNotes);talk.append(where,title,list,foot);
head.after(tabs,talk);
function setView(id){drawer.dataset.view=id;tabs.querySelectorAll('button').forEach(b=>{b.setAttribute('aria-selected',String(b.dataset.view===id));});
 if(id==='notes')drawer.querySelectorAll('.p57-notes-panel,.p57-annot-panel').forEach(p=>p.hidden=false);
 try{localStorage.setItem('p57-speaker-view',id);}catch{}}
let start='points';try{start=localStorage.getItem('p57-speaker-view')||'points';}catch{}
setView(views.some(v=>v[0]===start)?start:'points');

// The section on screen: the last heading that has scrolled past the upper third.
const headings=()=>[...document.querySelectorAll('.wrap h2')].filter(h=>!h.closest('.p57-stage-hidden'));
function currentHeading(){const line=innerHeight*.35;let cur=null;for(const h of headings()){if(h.getBoundingClientRect().top<=line)cur=h;else break;}return cur||headings()[0];}
function nodesFor(h){const out=[];let start=h.closest('.p57-chapter-hero')||h;let el=start.nextElementSibling;while(el&&!(el.matches('h2')||el.querySelector?.(':scope>h2'))){out.push(el);el=el.nextElementSibling;}return out;}
function points(h){
 const nodes=nodesFor(h),pts=[],seen=new Set();
 const add=t=>{t=clean(t);if(t.length<8)return;const k=t.toLowerCase().slice(0,60);if(seen.has(k))return;seen.add(k);pts.push(t);};
 const hero=h.closest('.p57-chapter-hero');
 if(hero){add(hero.querySelector('.sub')?.textContent);add(firstSentence(hero.querySelector('.p57-hero-description')?.textContent));}
 for(const n of nodes){
  if(n.matches('.sub'))add(n.textContent);
  else if(n.matches('.call'))add(firstSentence(n.querySelector('p')?.textContent||n.textContent));
  else if(n.matches('.kpis,.stat')){const figs=[...n.querySelectorAll('.kpi,.stat>div')].slice(0,4).map(k=>`${clean(k.querySelector('.l')?.textContent)}: ${clean(k.querySelector('.v')?.textContent)}`).filter(t=>!t.startsWith(':'));if(figs.length)add(figs.join(' · '));}
  else if(n.matches('p'))add(firstSentence(n.textContent));
  else if(n.matches('.rec'))add('Action: '+clean(n.querySelector('h3')?.textContent));
  else if(n.matches('.hyp'))n.querySelectorAll('.hcard').forEach(c=>add(`${clean(c.querySelector('.tag')?.textContent)}: ${clean(c.querySelector('h3')?.textContent)}`));
  if(pts.length>=7)break;
 }
 return pts.slice(0,7);
}
let shown=null;
function render(force){if(drawer.hidden&&!force)return;const h=currentHeading();if(!h||(h===shown&&!force))return;shown=h;
 const chapter=h.closest('.wrap>section')?.querySelector('.p57-chapter-hero h2');
 where.textContent=chapter&&chapter!==h?clean(chapter.textContent).replace(/^Chapter\s+(\d+)\s*/i,'Chapter $1 · '):'';
 title.textContent=clean(h.textContent);
 const pts=points(h);list.replaceChildren(...(pts.length?pts:['No summary lines in this section yet. Add your own in My notes.']).map(t=>{const li=document.createElement('li');li.textContent=t;return li;}));
 talk.classList.remove('p57-talk-in');void talk.offsetWidth;talk.classList.add('p57-talk-in');
}
let raf=0;addEventListener('scroll',()=>{cancelAnimationFrame(raf);raf=requestAnimationFrame(()=>render(false));},{passive:true});
new MutationObserver(()=>{if(!drawer.hidden)render(true);}).observe(drawer,{attributes:true,attributeFilter:['hidden']});
render(true);
})();
