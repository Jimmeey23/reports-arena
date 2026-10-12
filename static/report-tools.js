(() => {
'use strict';
if(document.querySelector('.rt-toolbar'))return;
const root=document.documentElement;
const make=(tag,txt,cls)=>{const e=document.createElement(tag);if(txt)e.textContent=txt;if(cls)e.className=cls;return e;};
const bar=make('nav',null,'rt-toolbar');bar.setAttribute('aria-label','Report tools');
const brand=make('div',null,'rt-brand');brand.append(make('b','PHYSIQUE 57'),make('small','Studio intelligence · Monthly review'));bar.append(brand);
const progress=make('div',null,'rt-progress');document.body.prepend(bar,progress);
let prefs={};try{prefs=JSON.parse(localStorage.getItem('p57-report-appearance')||'{}');}catch{}
function save(){try{localStorage.setItem('p57-report-appearance',JSON.stringify(prefs));}catch{}}
function select(label,items,key,apply){const l=make('label',label),s=make('select');s.setAttribute('aria-label',label);items.forEach(([v,t])=>{const o=make('option',t);o.value=v;s.append(o);});s.value=prefs[key]||items[0][0];apply(s.value);s.onchange=()=>{prefs[key]=s.value;save();apply(s.value);if(key==='theme'){const accent=prefs.accent||'#0f2c5e';root.style.setProperty('--a1',s.value==='dark'?'#8cb6ff':accent);root.style.setProperty('--a2',s.value==='dark'?'#8cb6ff':accent);}};l.append(s);bar.append(l);return s;}
function button(text,fn,parent=bar){const b=make('button',text);b.type='button';b.onclick=fn;parent.append(b);return b;}
select('Theme',[['light','Crisp paper'],['warm','Warm parchment'],['dark','Midnight']],'theme',v=>root.dataset.theme=v);
select('Colour',[['#0f2c5e','Navy'],['#0f666b','Teal'],['#59416f','Plum'],['#376348','Forest'],['#7e492c','Copper']],'accent',v=>{root.style.setProperty('--a1',prefs.theme==='dark'?'#8cb6ff':v);root.style.setProperty('--a2',prefs.theme==='dark'?'#8cb6ff':v);});
select('Layout',[['adaptive','Wide'],['reading','Reading'],['grid','Metric grid']],'layout',v=>root.dataset.layout=v);
select('Density',[['comfortable','Comfortable'],['compact','Compact']],'density',v=>root.dataset.density=v);
select('Text',[['16','100%'],['18','112%'],['20','125%']],'size',v=>root.style.setProperty('--report-size',v+'px'));
const jump=make('select');jump.setAttribute('aria-label','Jump to section');jump.append(make('option','Jump to section…'));document.querySelectorAll('h2').forEach((h,i)=>{if(!h.id)h.id='rt-section-'+i;const o=make('option',h.textContent);o.value=h.id;jump.append(o);});jump.onchange=()=>{if(jump.value)document.getElementById(jump.value)?.scrollIntoView();};bar.append(jump);
button('Charts',()=>{const hidden=root.classList.toggle('rt-hide-charts');status.textContent=hidden?'Charts hidden.':'Charts visible.';});
button('Expand evidence',()=>document.querySelectorAll('details').forEach(d=>d.open=true));button('Collapse',()=>document.querySelectorAll('details').forEach(d=>d.open=false));
button('Present',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await root.requestFullscreen();}catch{status.textContent='Fullscreen is unavailable in this browser.';}});
button('Print / PDF',()=>window.print());
if ('speechSynthesis' in window) {
  let speaking=false;
  const listen=button('Read section',()=>{
    if(speaking){speechSynthesis.cancel();speaking=false;listen.textContent='Read section';return;}
    const heading=jump.value?document.getElementById(jump.value):document.querySelector('.wrap h2');
    let text=heading?.textContent||document.title;
    for(let e=heading?.closest('.p57-chapter-hero')?.nextElementSibling||heading?.nextElementSibling;e&&e.tagName!=='H2';e=e.nextElementSibling)if(!e.matches('table,.rt-table-wrap,details,.chart'))text+=' '+e.textContent;
    const speech=new SpeechSynthesisUtterance(text);speech.rate=Number(speed.value);speech.onend=speech.onerror=()=>{speaking=false;listen.textContent='Read section';pause.textContent='Pause';};
    speechSynthesis.cancel();speechSynthesis.speak(speech);speaking=true;listen.textContent='Stop reading';
  });
  const pause=button('Pause',()=>{if(speechSynthesis.paused){speechSynthesis.resume();pause.textContent='Pause';}else if(speaking){speechSynthesis.pause();pause.textContent='Resume';}});
  const speed=select('Speed',[['1','1×'],['0.8','0.8×'],['1.2','1.2×'],['1.4','1.4×']],'speechSpeed',()=>{});
  window.addEventListener('pagehide',()=>speechSynthesis.cancel());
}

const dialog=make('dialog',null,'rt-dialog');dialog.setAttribute('aria-label','Report detail');document.body.append(dialog);
function openDialog(title,content){dialog.replaceChildren();const h=make('header');h.append(make('h3',title));button('Close',()=>dialog.close(),h);dialog.append(h,content);dialog.showModal();}
dialog.onclick=e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}};
button('Notes',()=>{const box=make('div'),note=make('textarea'),hint=make('p','Private notes saved in this browser for this report.');note.setAttribute('aria-label','Report notes');const key='p57-notes:'+document.title;try{note.value=localStorage.getItem(key)||'';}catch{}note.oninput=()=>{try{localStorage.setItem(key,note.value);hint.textContent='Saved in this browser.';}catch{hint.textContent='Browser storage is unavailable.';}};box.append(hint,note);button('Export notes',()=>download(note.value,'report-notes.txt','text/plain'),box);openDialog('Review notes',box);});
const status=make('span','','rt-status');status.setAttribute('role','status');bar.append(status);
const search=make('input');search.type='search';search.placeholder='Find in report';search.setAttribute('aria-label','Find in report');bar.append(search);
let matches=[],match=0;
search.oninput=()=>{const q=search.value.trim().toLowerCase();matches=q.length<2?[]:[...document.querySelectorAll('.wrap h2,.wrap h3,.wrap p,.wrap td,header h1')].filter(e=>e.textContent.toLowerCase().includes(q));match=0;find();};
function find(){status.textContent=search.value?(matches.length?`${match+1} / ${matches.length} matches`:'No matches'):'';if(matches.length){const e=matches[match];for(let p=e.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;e.closest('tr')?.removeAttribute('hidden');e.scrollIntoView({block:'center'});}}
button('Next match',()=>{if(matches.length){match=(match+1)%matches.length;find();}});
function download(data,name,type){const url=URL.createObjectURL(new Blob([data],{type}));const a=make('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const csvValue=v=>{v=String(v);if(/^[=+@-]/.test(v))v="'"+v;return '"'+v.replace(/"/g,'""')+'"';};
document.querySelectorAll('.wrap table').forEach((table,ti)=>{
const rows=[...table.rows],heads=[...rows[0]?.cells||[]];if(!heads.length||!heads.some(c=>c.tagName==='TH'))return;
const data=rows.slice(1);const titles=heads.map(c=>c.textContent.trim());const wrap=make('div',null,'rt-table-wrap'),tools=make('div',null,'rt-table-tools');table.before(wrap);wrap.append(tools,table);
const filter=make('input');filter.type='search';filter.placeholder='Filter these records…';filter.setAttribute('aria-label',`Filter table ${ti+1}`);const count=make('span',`${data.length} records`);tools.append(filter,count);
filter.oninput=()=>{const q=filter.value.toLowerCase();data.forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));count.textContent=`${data.filter(r=>!r.hidden).length} / ${data.length} records`;};
button('Export CSV',()=>{const visible=rows.filter(r=>!r.hidden);download('\uFEFF'+visible.map(r=>[...r.cells].map(c=>csvValue(c.textContent.trim())).join(',')).join('\r\n'),`report-table-${ti+1}.csv`,'text/csv;charset=utf-8');},tools);
heads.forEach((th,ci)=>{if(th.colSpan!==1)return;const b=make('button',titles[ci]+' ↕');b.setAttribute('aria-label',`Sort by ${titles[ci]}`);th.replaceChildren(b);th.setAttribute('aria-sort','none');let desc=false;b.onclick=()=>{desc=!desc;const val=r=>{const t=r.cells[ci]?.textContent.trim()||'';const clean=t.replace(/[₹,%\s]/g,'').replace(/−/g,'-');return /^[-+]?\d*\.?\d+$/.test(clean)?Number(clean):t;};const sorted=[...data].sort((a,b)=>{const x=val(a),y=val(b);return (typeof x==='number'&&typeof y==='number'?x-y:String(x).localeCompare(String(y),undefined,{numeric:true}))*(desc?-1:1);});sorted.forEach(r=>r.parentElement.append(r));heads.forEach(h=>h.setAttribute('aria-sort','none'));th.setAttribute('aria-sort',desc?'descending':'ascending');};});
data.forEach(row=>{if(row.cells.length!==heads.length)return;row.classList.add('rt-record');const first=row.cells[0],b=make('button',first.textContent.trim());b.style.cssText='background:none;border:0;color:inherit;font:inherit;padding:0;text-align:left;text-decoration:underline;text-underline-offset:3px';b.setAttribute('aria-label','View record: '+b.textContent);first.replaceChildren(b);b.onclick=()=>{const dl=make('dl');[...row.cells].forEach((c,i)=>dl.append(make('dt',titles[i]),make('dd',c.textContent.trim())));openDialog('Record details · '+titles[0],dl);};});
});
window.addEventListener('scroll',()=>{const max=root.scrollHeight-innerHeight;progress.style.width=(max>0?scrollY/max*100:0)+'%';},{passive:true});
window.P57Reader = {bar,button,make,prefs,save,select,jump,status,dialog,openDialog,download,csvValue};
window.addEventListener('beforeprint',()=>{document.querySelectorAll('details').forEach(d=>{d.dataset.printOpen=d.open?'1':'0';d.open=true;});});window.addEventListener('afterprint',()=>document.querySelectorAll('details').forEach(d=>{d.open=d.dataset.printOpen==='1';}));
})();
