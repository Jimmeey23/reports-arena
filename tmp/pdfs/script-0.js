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

(() => {
'use strict';
const R=window.P57Reader;if(!R||document.querySelector('.p57-tool-trigger'))return;
const {make,button,bar}=R,root=document.documentElement;
const online=/^https?:$/.test(location.protocol), route=location.pathname.match(/^\/api\/report\/([^/]+)\/([^/]+)/);
const report=route?route[1]+'/'+(['full','all'].includes(route[2])?'report':route[2]):document.title;
let user;try{user=localStorage.getItem('p57-user');if(!user){user=Array.from(crypto.getRandomValues(new Uint8Array(16)), b=>b.toString(16).padStart(2,'0')).join('');localStorage.setItem('p57-user',user);}}catch{user=Array.from(crypto.getRandomValues(new Uint8Array(16)), b=>b.toString(16).padStart(2,'0')).join('');}
const cacheKey='p57-workspace:'+report;
let saved={preferences:{},notes:{},edits:{},annotations:{}},pending={},inFlight={},saveTimer,saving=false,disposed=false;
try{saved={...saved,...JSON.parse(localStorage.getItem(cacheKey)||'{}')};}catch{}
pending=saved._pending||{};delete saved._pending;
const embedded=document.getElementById('p57-saved-workspace');if(embedded)try{saved={...saved,...JSON.parse(embedded.textContent)};}catch{}
const notice=make('div','', 'p57-save-status');notice.setAttribute('role','status');
async function api(path,method='GET',body){const res=await fetch(path,{method,headers:{'Content-Type':'application/json','X-P57-User':user},body:body?JSON.stringify(body):undefined});const data=await res.json();if(!res.ok)throw Error(data.error||'Could not save changes');return data;}
function unsaved(){const patch={};for(const kind of new Set([...Object.keys(inFlight),...Object.keys(pending)]))patch[kind]={...inFlight[kind],...pending[kind]};return patch;}
function cache(){try{localStorage.setItem(cacheKey,JSON.stringify({...saved,_pending:unsaved()}));}catch{notice.textContent='Browser storage unavailable; server saving continues.';}}
function change(kind,key,value){saved[kind]||={};saved[kind][key]=value;pending[kind]||={};pending[kind][key]=value;cache();notice.textContent=online?'Saving…':'Saved in this browser';clearTimeout(saveTimer);saveTimer=setTimeout(flush,350);}
async function flush(){if(saving||!Object.keys(pending).length||!online)return;const patch=pending;pending={};inFlight=patch;saving=true;try{await api('/api/workspace','POST',{report,patch});notice.textContent='Saved across sessions';cache();}catch(e){for(const [kind,fields]of Object.entries(patch))pending[kind]={...fields,...pending[kind]};notice.textContent='Saved locally. Server retry pending: '+e.message;}finally{saving=false;inFlight={};cache();if(Object.keys(pending).length&&!disposed)saveTimer=setTimeout(flush,2000);}}
window.addEventListener('pagehide',()=>{disposed=true;cache();if(online&&Object.keys(unsaved()).length)fetch('/api/workspace',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json','X-P57-User':user},body:JSON.stringify({report,patch:unsaved()})}).catch(()=>{});cancelAnimationFrame(frame);clearInterval(pollTimer);});
// Report fills the viewport. All authoring/presentation chrome lives behind one icon.
const trigger=make('button','✦','p57-tool-trigger');trigger.type='button';trigger.setAttribute('aria-label','Open annotation and presenter controls');trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-controls','p57-toolkit');document.body.append(trigger);
bar.id='p57-toolkit';bar.classList.add('p57-toolkit');bar.hidden=true;
const heading=make('div',null,'p57-panel-head');heading.append(make('strong','Report tools'));button('Close',()=>toggleTools(false),heading);bar.prepend(heading);
function toggleTools(open){bar.hidden=!open;trigger.setAttribute('aria-expanded',String(open));if(open)bar.querySelector('button')?.focus();}
trigger.onclick=()=>toggleTools(bar.hidden);
const back=make('a','← Report library','p57-library-link');back.href='/';back.target='_top';bar.append(back,notice);
const headings=[...document.querySelectorAll('.wrap h2')];let current=headings[0]?.id||'overview';
const nav=make('aside',null,'p57-navigation');nav.setAttribute('aria-label','Report navigation');const navHead=make('div',null,'p57-panel-head');navHead.append(make('strong','Contents'));button('Close',()=>setNav(false),navHead);nav.append(navHead);
const navTrigger=make('button','☰','p57-nav-trigger');navTrigger.setAttribute('aria-label','Toggle report navigation');navTrigger.setAttribute('aria-controls','p57-navigation');nav.id='p57-navigation';document.body.append(navTrigger,nav);
let navTimer,navPinned=!!saved.preferences.navPinned;
function setNav(open){nav.hidden=!open;root.classList.toggle('p57-left-open',open);navTrigger.setAttribute('aria-expanded',String(open));if(open)idleNav();}
function idleNav(){clearTimeout(navTimer);if(!navPinned)navTimer=setTimeout(()=>setNav(false),5000);}
navTrigger.onclick=()=>setNav(nav.hidden);
const pin=button('Pin navigation',()=>{navPinned=!navPinned;pin.setAttribute('aria-pressed',String(navPinned));pin.textContent=navPinned?'Unpin navigation':'Pin navigation';change('preferences','navPinned',navPinned);idleNav();},nav);
const navList=make('div',null,'p57-nav-list');nav.append(navList);
headings.forEach((h,i)=>{const b=button(`${String(i+1).padStart(2,'0')}  ${h.textContent}`,()=>go(h.id),navList);b.dataset.section=h.id;});
function go(id){current=id;document.getElementById(id)?.scrollIntoView({block:'start',behavior:'instant'});renderNotes();markNav();publishSoon();}
function markNav(){navList.querySelectorAll('button').forEach(b=>b.setAttribute('aria-current',b.dataset.section===current?'location':'false'));}
setNav(true);for(const event of ['pointerdown','keydown','scroll'])window.addEventListener(event,idleNav,{passive:true});
// Speaker drawer is private; hosted audiences receive only the report view and annotations.
const drawer=make('aside',null,'p57-speaker');drawer.id='p57-speaker';drawer.hidden=true;drawer.setAttribute('aria-label','Speaker notes and teleprompter');document.body.append(drawer);

// Header with section label and collapsible icons
const dh=make('div',null,'p57-panel-head p57-speaker-head');
const titleGroup=make('div',null,'p57-title-group');
titleGroup.append(make('strong','Speaker workspace','p57-speaker-main-title'));
const sectionLabel=make('div','','p57-section-label');
titleGroup.append(sectionLabel);

const actionsBar=make('div',null,'p57-speaker-actions');

// Notes icon toggle
const noteBtn=make('button','','p57-icon-btn p57-notes-toggle');
noteBtn.type='button';noteBtn.title='Private speaker notes';
noteBtn.setAttribute('aria-label','Toggle private speaker notes');
noteBtn.setAttribute('aria-expanded','false');
const noteDot=make('span','','p57-indicator-dot');noteDot.hidden=true;
noteBtn.append(make('span','📝','p57-btn-icon'),make('span','Notes','p57-btn-text'),noteDot);

// Annotations icon toggle
const annotBtn=make('button','','p57-icon-btn p57-annot-toggle');
annotBtn.type='button';annotBtn.title='Report annotations';
annotBtn.setAttribute('aria-label','Toggle report annotations');
annotBtn.setAttribute('aria-expanded','false');
const annotDot=make('span','','p57-indicator-dot');annotDot.hidden=true;
annotBtn.append(make('span','💬','p57-btn-icon'),make('span','Annotations','p57-btn-text'),annotDot);

// Settings toggle
const settingsBtn=make('button','','p57-icon-btn p57-settings-toggle');
settingsBtn.type='button';settingsBtn.title='Prompter settings';
settingsBtn.setAttribute('aria-label','Toggle teleprompter settings');
settingsBtn.setAttribute('aria-expanded','false');
settingsBtn.append(make('span','⚙️','p57-btn-icon'));

const closeDrawer=button('Close',()=>{drawer.hidden=true;root.classList.remove('p57-right-open');stopPrompt();},actionsBar);
closeDrawer.classList.add('p57-close-btn');

actionsBar.prepend(noteBtn,annotBtn,settingsBtn);
dh.append(titleGroup,actionsBar);
drawer.append(dh);

// Collapsible Panel: Private Speaker Notes
const notesPanel=make('div',null,'p57-collapsible-panel p57-notes-panel');notesPanel.hidden=true;
const notesHead=make('div',null,'p57-panel-subhead');
const notesTitleWrap=make('div',null,'p57-panel-title');
notesTitleWrap.append(make('strong','Private speaker notes'),make('span','Private','p57-badge p57-badge-private'));
const notesCollapse=button('Collapse ▴',()=>toggleNotes(false),notesHead);
notesCollapse.className='p57-collapse-btn';
notesHead.prepend(notesTitleWrap);

const note=make('textarea');note.id='p57-speaker-notes';note.setAttribute('aria-label','Private speaker notes');
note.placeholder='Talking points for this section… (auto-populates teleprompter)';
let promptDirty=false;
note.oninput=()=>{change('notes',current,note.value);promptDirty=true;noteDot.hidden=!note.value.trim();};
notesPanel.append(notesHead,note,make('div','Private to host · Notes automatically populate the teleprompter screen.','p57-panel-hint'));

function toggleNotes(show){
  const open=(show!==undefined)?show:notesPanel.hidden;
  notesPanel.hidden=!open;
  noteBtn.classList.toggle('active',open);
  noteBtn.setAttribute('aria-expanded',String(open));
  if(open){annotPanel.hidden=true;annotBtn.classList.remove('active');annotBtn.setAttribute('aria-expanded','false');note.focus();}
}
noteBtn.onclick=()=>toggleNotes();

// Collapsible Panel: Report Annotation
const annotPanel=make('div',null,'p57-collapsible-panel p57-annot-panel');annotPanel.hidden=true;
const annotHead=make('div',null,'p57-panel-subhead');
const annotTitleWrap=make('div',null,'p57-panel-title');
annotTitleWrap.append(make('strong','Report annotation'),make('span','Shared','p57-badge p57-badge-shared'));
const annotCollapse=button('Collapse ▴',()=>toggleAnnot(false),annotHead);
annotCollapse.className='p57-collapse-btn';
annotHead.prepend(annotTitleWrap);

const annotation=make('textarea');annotation.id='p57-annotation';annotation.setAttribute('aria-label','Report annotation');
annotation.placeholder='Annotation visible to your hosted audience…';
annotation.oninput=()=>{change('annotations',current,annotation.value);renderAnnotations();annotDot.hidden=!annotation.value.trim();};
const annotActions=make('div',null,'p57-panel-actions');
button('Quote selected text',()=>{const text=window.getSelection()?.toString().trim();if(!text)return;annotation.value+=(annotation.value?'\n':'')+'“'+text+'”';annotation.oninput();},annotActions);
annotActions.append(make('span','Shown in report callouts for this section','p57-panel-hint'));
annotPanel.append(annotHead,annotation,annotActions);

function toggleAnnot(show){
  const open=(show!==undefined)?show:annotPanel.hidden;
  annotPanel.hidden=!open;
  annotBtn.classList.toggle('active',open);
  annotBtn.setAttribute('aria-expanded',String(open));
  if(open){notesPanel.hidden=true;noteBtn.classList.remove('active');noteBtn.setAttribute('aria-expanded','false');annotation.focus();}
}
annotBtn.onclick=()=>toggleAnnot();

// Collapsible Panel: Settings
const settingsPanel=make('div',null,'p57-collapsible-panel p57-settings-panel');settingsPanel.hidden=true;
const settingsHead=make('div',null,'p57-panel-subhead');
settingsHead.append(make('strong','Prompter options'));
const settingsCollapse=button('Collapse ▴',()=>toggleSettings(false),settingsHead);
settingsCollapse.className='p57-collapse-btn';
const settingsGrid=make('div',null,'p57-settings-grid');
settingsPanel.append(settingsHead,settingsGrid);

function toggleSettings(show){
  const open=(show!==undefined)?show:settingsPanel.hidden;
  settingsPanel.hidden=!open;
  settingsBtn.classList.toggle('active',open);
  settingsBtn.setAttribute('aria-expanded',String(open));
}
settingsBtn.onclick=()=>toggleSettings();

drawer.append(notesPanel,annotPanel,settingsPanel);

// Full available height teleprompter screen
const prompterArea=make('div',null,'p57-teleprompter-area');
const prompterBar=make('div',null,'p57-prompt-bar');
prompterBar.append(make('span','● TELEPROMPTER','p57-prompter-badge'),make('span','Eye-line guide active · Auto-scrolls','p57-prompter-subhint'));

const prompterViewport=make('div',null,'p57-prompt-viewport');
const prompt=make('div',null,'p57-prompt');prompt.tabIndex=0;prompt.setAttribute('aria-label','Teleprompter script');
const prompterGuide=make('div',null,'p57-prompt-guide');prompterGuide.setAttribute('aria-hidden','true');
prompterViewport.append(prompt,prompterGuide);
prompterArea.append(prompterBar,prompterViewport);
drawer.append(prompterArea);

// Bottom controls bar
const controls=make('div',null,'p57-prompt-controls');drawer.append(controls);
let frame=0,playing=false,lastFrame=0;
function stopPrompt(){playing=false;cancelAnimationFrame(frame);play.textContent='Start';play.classList.remove('p57-playing');}
function tick(t){if(!playing)return;const dt=lastFrame?Math.min(t-lastFrame,100)/1000:0;lastFrame=t;prompt.scrollTop+=Number(speed.value)*dt;if(prompt.scrollTop>=prompt.scrollHeight-prompt.clientHeight-1){stopPrompt();return;}frame=requestAnimationFrame(tick);}
const play=button('Start',()=>{if(playing)return stopPrompt();if(promptDirty){updatePrompt();promptDirty=false;}playing=true;lastFrame=0;play.textContent='Pause';play.classList.add('p57-playing');frame=requestAnimationFrame(tick);},controls);
play.classList.add('p57-btn-play');
button('Reset',()=>{stopPrompt();prompt.scrollTop=0;},controls);
function range(label,min,max,value,key,apply){const l=make('label',label),input=make('input');input.type='range';input.min=min;input.max=max;input.value=saved.preferences[key]||value;input.setAttribute('aria-label',label);input.oninput=()=>{apply(input.value);change('preferences',key,input.value);};l.append(input);settingsGrid.append(l);apply(input.value);return input;}
const speed=range('Scroll speed',5,100,25,'promptSpeed',()=>{});
range('Prompt text size',18,48,26,'promptFont',v=>prompt.style.fontSize=v+'px');
range('Drawer width',300,640,420,'drawerWidth',v=>root.style.setProperty('--p57-panel-width',v+'px'));
const mirror=button('Mirror',()=>{const on=prompt.classList.toggle('mirrored');mirror.setAttribute('aria-pressed',String(on));mirror.classList.toggle('active',on);change('preferences','promptMirror',on);},controls);

const timerBox=make('div',null,'p57-timer-group');
let timerStart=0,timerElapsed=0;const timer=make('output','00:00','p57-timer');timerBox.append(timer);
button('Start / pause timer',()=>{if(timerStart){timerElapsed+=Date.now()-timerStart;timerStart=0;}else timerStart=Date.now();},timerBox);
button('Reset timer',()=>{timerStart=0;timerElapsed=0;timer.textContent='00:00';},timerBox);
controls.append(timerBox);

const timerInterval=setInterval(()=>{const secs=Math.floor((timerElapsed+(timerStart?Date.now()-timerStart:0))/1000);timer.textContent=String(Math.floor(secs/60)).padStart(2,'0')+':'+String(secs%60).padStart(2,'0');},1000);
window.addEventListener('pagehide',()=>clearInterval(timerInterval));

function updatePrompt(){const h=document.getElementById(current);let text=note.value.trim();if(!text){text=h?.textContent||document.title;for(let e=h?.closest('.p57-chapter-hero')?.nextElementSibling||h?.nextElementSibling;e&&e.tagName!=='H2';e=e.nextElementSibling)if(e.matches('p,.sub,.call'))text+='\n\n'+e.textContent;}prompt.textContent=text;}
function renderNotes(){
  const h=document.getElementById(current);
  sectionLabel.textContent=h?.textContent||'Overview';
  note.value=saved.notes[current]||'';
  annotation.value=saved.annotations[current]||'';
  noteDot.hidden=!note.value.trim();
  annotDot.hidden=!annotation.value.trim();
  updatePrompt();
  stopPrompt();
  prompt.scrollTop=0;
}
function openSpeaker(expandNotes=false){
  toggleTools(false);
  drawer.hidden=false;
  root.classList.add('p57-right-open');
  if(expandNotes)toggleNotes(true);
  else{toggleNotes(false);toggleAnnot(false);toggleSettings(false);}
  renderNotes();
}
const oldNotes=[...bar.querySelectorAll('button')].find(b=>b.textContent==='Notes');
if(oldNotes){oldNotes.textContent='Speaker notes / annotations';oldNotes.onclick=()=>openSpeaker(true);}
button('Teleprompter',()=>openSpeaker(false));
// Only narrative fields are editable; computed table values retain their source definitions.
const editables=[...document.querySelectorAll('.wrap p,.wrap h3,.wrap h4,.wrap .sub,body>header h1,body>header .lede')].filter(e=>!e.closest('table,svg,.rt-table-tools'));
const originalText=new Map(editables.map(e=>[e,e.textContent]));
const originalHTML=new Map(editables.map(e=>[e,e.innerHTML]));
editables.forEach((e,i)=>e.dataset.editId='text-'+i);
let editing=false;const edit=button('Edit report text',()=>{if(meeting&&!meeting.is_host)return;editing=!editing;edit.textContent=editing?'Finish editing':'Edit report text';edit.setAttribute('aria-pressed',String(editing));editables.forEach(e=>{e.contentEditable=editing?'true':'false';});toggleTools(false);});
editables.forEach(e=>e.addEventListener('input',()=>change('edits',e.dataset.editId,e.textContent)));
function applyEdits(edits=saved.edits){editables.forEach(e=>{if(document.activeElement===e)return;if(Object.hasOwn(edits,e.dataset.editId)){if(e.textContent!==edits[e.dataset.editId])e.textContent=edits[e.dataset.editId];}else if(e.innerHTML!==originalHTML.get(e))e.innerHTML=originalHTML.get(e);});}
let annotationSnapshot='';
function renderAnnotations(values=saved.annotations){const snapshot=JSON.stringify(values||{});if(snapshot===annotationSnapshot)return;annotationSnapshot=snapshot;document.querySelectorAll('.p57-annotation-callout').forEach(e=>e.remove());for(const [id,text]of Object.entries(values||{})){if(!text)continue;const h=document.getElementById(id);if(h){const a=make('aside',text,'p57-annotation-callout');a.setAttribute('aria-label','Report annotation');h.after(a);}}}
let restoringPreferences=false;
function applyPreferences(){restoringPreferences=true;for(const s of bar.querySelectorAll('select')){const label=s.getAttribute('aria-label'),key={Theme:'theme',Colour:'accent',Layout:'layout',Density:'density',Text:'size',Speed:'speechSpeed'}[label];if(key&&saved.preferences[key]){s.value=saved.preferences[key];s.dispatchEvent(new Event('change'));}}if(saved.preferences.promptFont)prompt.style.fontSize=saved.preferences.promptFont+'px';if(saved.preferences.promptSpeed)speed.value=saved.preferences.promptSpeed;prompt.classList.toggle('mirrored',!!saved.preferences.promptMirror);navPinned=!!saved.preferences.navPinned;pin.textContent=navPinned?'Unpin navigation':'Pin navigation';pin.setAttribute('aria-pressed',String(navPinned));if(saved.preferences.drawerWidth)root.style.setProperty('--p57-panel-width',saved.preferences.drawerWidth+'px');idleNav();restoringPreferences=false;}
const prefKeys={Theme:'theme',Colour:'accent',Layout:'layout',Density:'density',Text:'size',Speed:'speechSpeed'};
bar.addEventListener('change',e=>{const key=prefKeys[e.target.getAttribute('aria-label')];if(key&&!restoringPreferences)change('preferences',key,e.target.value);});
R.jump.addEventListener('change',()=>{if(R.jump.value){current=R.jump.value;renderNotes();markNav();publishSoon();}});
// Meeting codes allow every visitor to host or join; host identity is never sent to guests.
const session=make('section',null,'p57-session');session.append(make('h3','Guided session'));bar.append(session);
const meetingStatus=make('p','Host a report or join with a meeting code.');meetingStatus.setAttribute('role','status');session.append(meetingStatus);
let meeting=null,following=true,pollTimer=0,publication=0,pollBusy=false,applying=false,personalView=null;
const tables=[...document.querySelectorAll('.rt-table-wrap')];
const originalRows=new Map(tables.map(w=>[w,[...w.querySelectorAll('tbody tr')]]));
function tableState(){return tables.map((wrap,index)=>{const header=wrap.querySelector('th[aria-sort=ascending],th[aria-sort=descending]');return{index,filter:wrap.querySelector('input')?.value||'',sort:header?[...header.parentElement.cells].indexOf(header):-1,descending:header?.getAttribute('aria-sort')==='descending'};});}
function applyTableState(states=[]){for(const state of states){const wrap=tables[state.index];if(!wrap)continue;const filter=wrap.querySelector('input');if(filter&&filter.value!==state.filter){filter.value=state.filter||'';filter.dispatchEvent(new Event('input'));}if(state.sort<0){if(!wrap.querySelector('th[aria-sort=ascending],th[aria-sort=descending]'))continue;for(const row of originalRows.get(wrap))row.parentElement.append(row);wrap.querySelectorAll('th').forEach(th=>th.setAttribute('aria-sort','none'));continue;}const th=wrap.querySelectorAll('th')[state.sort],desired=state.descending?'descending':'ascending';if(th&&th.getAttribute('aria-sort')!==desired){th.querySelector('button')?.click();if(th.getAttribute('aria-sort')!==desired)th.querySelector('button')?.click();}}}
const host=button('Host this report',async()=>{try{if(!route||!online)throw Error('Open this report from the app to host.');await flush();meeting=await api('/api/meetings','POST',{report});try{localStorage.setItem('p57-host:'+report,meeting.code);}catch{}startMeeting();}catch(e){meetingStatus.textContent=e.message;}},session);
const joinInput=make('input');joinInput.placeholder='Meeting code';joinInput.maxLength=9;joinInput.setAttribute('aria-label','Meeting code');session.append(joinInput);
button('Join session',async()=>{try{const m=await api('/api/meetings/'+encodeURIComponent(joinInput.value.replace(/-/g,'').trim().toUpperCase()));if(!m.active)throw Error('This session has ended.');navigateMeeting(m);}catch(e){meetingStatus.textContent=e.message;}},session);
const follow=button('Following host',()=>{following=!following;follow.textContent=following?'Following host':'Explore independently';follow.setAttribute('aria-pressed',String(following));},session);follow.hidden=true;
const leave=button('Leave session',()=>{clearInterval(pollTimer);clearTimeout(publication);meeting=null;sessionBadge.hidden=true;copy.hidden=true;host.disabled=false;edit.disabled=false;history.replaceState(null,'',location.pathname);follow.hidden=true;leave.hidden=true;end.hidden=true;meetingStatus.textContent='You left the guided session.';editing=false;editables.forEach(e=>e.contentEditable='false');applyEdits();renderAnnotations();applyPreferences();if(personalView){document.querySelectorAll('details').forEach((d,i)=>d.open=personalView.evidence.includes(i));root.classList.toggle('rt-hide-charts',personalView.chartsHidden);applyTableState(personalView.tables);current=personalView.section;window.scrollTo({top:personalView.scroll*Math.max(0,root.scrollHeight-innerHeight),behavior:'instant'});personalView=null;}renderNotes();markNav();edit.textContent='Edit report text';edit.setAttribute('aria-pressed','false');},session);leave.hidden=true;
const end=button('End hosted session',async()=>{try{await api('/api/meetings/'+meeting.code,'POST',{end:true});try{localStorage.removeItem('p57-host:'+report);}catch{}leave.click();meetingStatus.textContent='Hosted session ended.';}catch(e){meetingStatus.textContent=e.message;}},session);end.hidden=true;
const shareField=make('input');shareField.readOnly=true;shareField.hidden=true;shareField.setAttribute('aria-label','Meeting link to copy');session.append(shareField);
const copy=button('Copy meeting link',async()=>{if(!meeting)return;const link=location.origin+'/api/report/'+meeting.report+'?meeting='+meeting.code;try{await navigator.clipboard.writeText(link);meetingStatus.textContent='Meeting link copied · '+meeting.code;}catch{shareField.hidden=false;shareField.value=link;shareField.select();meetingStatus.textContent='Copy the selected meeting link.';}},session);copy.hidden=true;
const sessionBadge=make('button','','p57-session-badge');sessionBadge.hidden=true;sessionBadge.onclick=()=>toggleTools(true);document.body.append(sessionBadge);
function navigateMeeting(m){if(m.report!==report){window.top.location.href='/api/report/'+m.report+'?meeting='+m.code;return;}meeting=m;history.replaceState(null,'',location.pathname+'?meeting='+m.code);startMeeting();}
function startMeeting(){if(!personalView)personalView=viewState();following=true;follow.textContent='Following host';follow.setAttribute('aria-pressed','true');clearInterval(pollTimer);host.disabled=meeting.is_host;follow.hidden=meeting.is_host;leave.hidden=false;end.hidden=!meeting.is_host;sessionBadge.hidden=false;copy.hidden=false;editing=false;editables.forEach(e=>e.contentEditable='false');edit.disabled=!meeting.is_host;pollTimer=setInterval(poll,1000);poll();if(meeting.is_host)publishSoon();}
function viewState(){const max=root.scrollHeight-innerHeight;return{section:current,scroll:max>0?Math.min(1,Math.max(0,scrollY/max)):0,evidence:[...document.querySelectorAll('details')].flatMap((d,i)=>d.open?[i]:[]),chartsHidden:root.classList.contains('rt-hide-charts'),tables:tableState()};}
function publishSoon(){if(!meeting?.is_host||applying)return;clearTimeout(publication);const code=meeting.code;publication=setTimeout(async()=>{if(!meeting?.is_host||meeting.code!==code||!meeting.active)return;try{await api('/api/meetings/'+code,'POST',{view:viewState()});}catch(e){meetingStatus.textContent=e.message;}},150);}
async function poll(){if(pollBusy||!meeting)return;pollBusy=true;try{const code=meeting.code;const m=await api('/api/meetings/'+code);if(!meeting||meeting.code!==code)return;meeting=m;sessionBadge.textContent=(m.is_host?'Hosting · ':'Live · ')+m.code;meetingStatus.textContent=`${m.is_host?'Hosting':'Joined'} · ${m.code} · ${m.participants} connected`;if(!m.active){clearInterval(pollTimer);sessionBadge.textContent='Session ended';meetingStatus.textContent='The host ended this session.';host.disabled=false;edit.disabled=false;return;}if(!m.is_host&&following){applying=true;document.querySelectorAll('details').forEach((d,i)=>d.open=(m.view.evidence||[]).includes(i));root.classList.toggle('rt-hide-charts',!!m.view.chartsHidden);applyTableState(m.view.tables);applyEdits(m.edits);renderAnnotations(m.annotations);const changed=current!==m.view.section;if(m.view.section)current=m.view.section;window.scrollTo({top:m.view.scroll*Math.max(0,root.scrollHeight-innerHeight),behavior:'instant'});if(changed)renderNotes();markNav();applying=false;}}catch(e){meetingStatus.textContent='Connection interrupted. Retrying… '+e.message;}finally{pollBusy=false;}}
let scrollThrottle=0;window.addEventListener('scroll',()=>{if(applying)return;clearTimeout(scrollThrottle);scrollThrottle=setTimeout(()=>{const seen=headings.filter(h=>h.getBoundingClientRect().top<innerHeight*.4).at(-1);if(seen&&current!==seen.id){current=seen.id;if(drawer.hidden)renderNotes();else if(document.activeElement!==note&&document.activeElement!==annotation)renderNotes();markNav();}publishSoon();},120);},{passive:true});
document.addEventListener('toggle',publishSoon,true);
document.addEventListener('input',e=>{if(e.target.closest('.rt-table-tools'))publishSoon();});
document.addEventListener('click',e=>{if(e.target.closest('th button')||e.target.textContent==='Charts')publishSoon();});
window.addEventListener('keydown',e=>{if(e.key==='Escape'){toggleTools(false);drawer.hidden=true;root.classList.remove('p57-right-open');setNav(false);stopPrompt();}if(e.altKey&&e.key.toLowerCase()==='n'){e.preventDefault();openSpeaker();}});
// Export embeds saved text, notes, annotations and appearance alongside the original reader.
button('Download edited report',async()=>{try{await flush();let html;if(online&&route){const response=await fetch(location.pathname);if(!response.ok)throw Error('Report download failed');html=await response.text();}else{throw Error('Use the app to export an edited report.');}const state=JSON.stringify(saved).replace(/</g,'\\u003c');const pos=html.toLowerCase().lastIndexOf('</head>');html=html.slice(0,pos)+`<script type="application/json" id="p57-saved-workspace">${state}<\/script>`+html.slice(pos);const url=URL.createObjectURL(new Blob([html],{type:'text/html'}));const a=make('a');a.href=url;a.download='Edited_Performance_Review.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){notice.textContent=e.message;}});
applyEdits();renderAnnotations();renderNotes();markNav();applyPreferences();
(async()=>{if(!online)return;try{const remote=await api('/api/workspace?report='+encodeURIComponent(report));for(const kind of ['notes','preferences','edits','annotations'])saved[kind]={...saved[kind],...remote[kind],...pending[kind]};cache();applyEdits();renderAnnotations();renderNotes();applyPreferences();notice.textContent='Saved workspace restored';if(Object.keys(pending).length)flush();const code=new URLSearchParams(location.search).get('meeting');let previous;try{previous=localStorage.getItem('p57-host:'+report);}catch{}if(code||previous){const m=await api('/api/meetings/'+encodeURIComponent(code||previous));if(m.active&&(code||m.is_host))navigateMeeting(m);}}catch(e){notice.textContent='Local workspace restored. '+e.message;}})();
})();

(() => {
'use strict';
const R=window.P57Reader;if(!R||document.querySelector('[data-p57-explorer-ready]'))return;
document.body.dataset.p57ExplorerReady='1';
const {make,button,openDialog,dialog,download,csvValue}=R;
let frozen=null;try{frozen=JSON.parse(document.getElementById('p57-source-records')?.textContent||'null');}catch{}
const aliases={Date:['_dt','Date','Created At','Date (IST)'],Member:['Member Name','Name','Full Name','First Name'], 'Member ID':['Member ID'],Format:['_cls','Class','SessionName','Class Type'],Instructor:['_trainer','Trainer','Instructor'],'Capacity':['Capacity'],Booked:['Booked'],Attendances:['CheckedIn','Checked In'], 'Late cancellations':['LateCancelled','Is Late Cancelled'],'Revenue':['val','Revenue','Payment Value'],'Discount':['disc','Discount Value'],'Gross':['gross'],'Product':['Cleaned Product','Membership Name','Product Name'],'Category':['Cleaned Category','Category'],'Associate':['Sold By','Associate','Owner'],'Payment method':['Payment Method'],'Source':['Source Name'],'Status':['Status','Derived Status'],'Trial status':['Trial Status'],'Won':['won'],'Amount paid':['Amount Paid'],'Completed sessions':['Total Sessions Completed'],'Remaining sessions':['Remaining Sessions'],'Lifetime value':['LTVn','Ltv','LTV'],'Day':['_day','Day'],'Time':['Time']};
const key=(name)=>name.toLowerCase().replace(/[^a-z0-9]/g,'');
function normalise(row){const result={},used=new Set();for(const [name,fields]of Object.entries(aliases)){const f=fields.find(f=>Object.hasOwn(row,f));if(f!=null){result[name]=row[f];used.add(f);}}for(const [name,value]of Object.entries(row))if(!used.has(name)&&!name.startsWith('_')&&!/email|phone|token|unique.?id/i.test(name))result[name]=value;return result;}
const numeric=v=>{if(typeof v==='number')return Number.isFinite(v)?v:null;if(typeof v==='boolean')return v?1:0;if(typeof v!=='string')return null;const s=v.replace(/[₹,%\s]/g,'').replace(/−/g,'-');return /^[-+]?\d+(\.\d+)?$/.test(s)?Number(s):null;};
const fmt=v=>v==null||v===''?'n/a':typeof v==='number'?v.toLocaleString('en-IN',{maximumFractionDigits:2}):typeof v==='boolean'?(v?'Yes':'No'):String(v);
const sum=(rows,field)=>{const values=rows.map(r=>numeric(r[field])).filter(v=>v!=null);return values.length?values.reduce((a,b)=>a+b,0):null;};
function owner(el){return el.closest('.wrap>section')||el.closest('section')||document.querySelector('.wrap');}
function chapter(el){const section=owner(el),heading=section?.querySelector('h2')?.textContent||document.title;const text=(section?.id||heading||'').toLowerCase();if(/sales/.test(text))return'sales';if(/instructor/.test(text))return'instructor';if(/format/.test(text))return'format';if(/lapse|churn|membership/.test(text))return'lapse';if(/cancel|discount/.test(text))return'cancels';if(/lead/.test(text))return'leads';if(/behaviour|behavior/.test(text))return'behaviour';if(/overview/.test(text))return'overview';return'class';}
function focus(label,cid){const text=label.toLowerCase();let source=['sales'].includes(cid)?'sales':cid==='lapse'?'lapsed':cid==='leads'?'leads':cid==='behaviour'?'checkins':'sessions';let definition='Saved source records for this studio and the selected report period.',predicate=null;
if(/discount|cash|transaction|buyer/.test(text)){source='sales';definition=/average buyer/.test(text)?'Cash collected ÷ distinct buyers. Every transaction for the period contributes to cash; Member ID defines distinct buyers.':/discount/.test(text)?'Sum of recorded discounts. Only transactions with a non-zero recorded discount are shown.':'Cash is the sum of recorded payment values; transactions count source sales rows.';if(/discount/.test(text))predicate=r=>(numeric(r.Discount)||0)!==0;}
else if(/utilisation|utilization/.test(text))definition='Utilisation = summed attendances ÷ summed capacity × 100. All sessions form the denominator; empty sessions remain included.';
else if(/revenue per (class|attend)/.test(text))definition=/attend/.test(text)?'Session revenue ÷ summed attendances. Both revenue and attendance records are retained.':'Session revenue ÷ number of studio sessions. Empty sessions remain included.';
else if(/empty class/.test(text)){predicate=r=>numeric(r.Attendances)===0;definition='Sessions with zero recorded attendances; unknown attendance values are excluded.';}
else if(/attendance/.test(text)){predicate=r=>(numeric(r.Attendances)||0)>0;definition='Sum of recorded attendances. Only sessions contributing at least one attendance are shown.';}
else if(/paid membership/.test(text)){source='lapsed';predicate=r=>(numeric(r['Amount paid'])||0)>0;definition='Membership ledger rows with Amount Paid > 0. This is the studio-wide ledger, not purchases restricted to the report month.';}
else if(/median life/.test(text)){source='lapsed';predicate=r=>numeric(r['Observed life days'])!=null;definition='Median observed life among paid memberships with a purchase date. Ends use the earliest churn/end date; open memberships are censored at the report generation date.';}
else if(/never attended/.test(text)){source='lapsed';predicate=r=>numeric(r['Completed sessions'])===0;definition='Membership ledger rows with zero completed sessions. Missing completion values are excluded.';}
else if(/trial|won|open file/.test(text)){source='leads';definition='Studio-wide leads ledger. Trialled = Trial Completed rows ÷ all leads; Won = Won rows ÷ all leads. Both rates retain denominator records.';}
else if(/visits|members who came|came exactly once|top tenth/.test(text)){source='checkins';definition='Attended check-in records for the report month. Visits per member = attended visits ÷ distinct Member IDs.';}
else if(/seats released|value at average/.test(text)){definition='Late cancellations summed across sessions. Opportunity value is an estimate using average revenue per attendance, not a booked cash loss.';predicate=r=>(numeric(r['Late cancellations'])||0)>0;}
return{source,definition,predicate};}
function evidence(el,label){const section=owner(el);return [...(section?.querySelectorAll('table')||[])].filter(t=>!t.closest('.p57-explorer-grid')).map((table,index)=>{const header=[...table.rows[0]?.cells||[]].map(c=>c.textContent.replace(/\s*↕$/,'').trim());const rows=[...table.rows].slice(1).filter(r=>r.cells.length===header.length).map(r=>Object.fromEntries(header.map((h,i)=>[h,r.cells[i].textContent.trim()])));const terms=label.toLowerCase().split(/\W+/).filter(t=>t.length>3);const score=terms.reduce((n,t)=>n+(header.some(h=>h.toLowerCase().includes(t))?3:0),0)+(table.closest('details')?1:0);return{title:table.closest('details')?.querySelector('summary')?.textContent.trim()||`Saved table ${index+1} · ${header.slice(0,3).join(' / ')}`,rows,header,score,table};}).filter(x=>x.rows.length).sort((a,b)=>b.score-a.score);}
function openExplorer(el,label,selection=null){const cid=chapter(el);if(!selection&&cid==='format'&&/^(fullest|emptiest|best per class)$/i.test(label)){const value=el.querySelector('.d')?.textContent.trim();if(value)selection={field:'Format',value};}const metric=focus(label,cid),sources=frozen?.datasets||{},snapshotSource=sources[metric.source];let recordSource=snapshotSource;if(/20\d{2}/.test(label)&&frozen?.period&&!frozen.period.includes(label.match(/20\d{2}/)[0]))recordSource=null;if(recordSource&&selection){const field=Object.keys(aliases).find(f=>key(f)===key(selection.field))||selection.field;if(!recordSource.rows.some(r=>Object.hasOwn(normalise(r),field)))recordSource=null;}const available=evidence(el,label),content=make('div');let dataset=recordSource?{...recordSource,rows:recordSource.rows.map(normalise)}:(selection?available.find(t=>t.table===el.closest('table')):null)||available[0];let base=dataset?.rows||[],selectedGroup=selection?.value,groupField=selection?.field;
if(recordSource&&groupField){const canonical=Object.keys(aliases).find(f=>key(f)===key(groupField));groupField=canonical||groupField;}
const context=make('p',`${frozen?.studio||document.title} · ${frozen?.period||'Saved report'} · ${recordSource?dataset.scope:'Saved report evidence tables'}`, 'p57-explorer-context');content.append(context,make('div',recordSource?metric.definition:(frozen?'No matching frozen source population exists for this selection. Showing the saved supporting table without substituting other periods.':'This report predates frozen source-record snapshots. These are the saved supporting tables; they are not reconstructed from newer uploads.'),'p57-explorer-definition'));
const toolbar=make('div',null,'p57-explorer-toolbar'),search=make('input');search.type='search';search.placeholder='Search these records…';search.setAttribute('aria-label','Search metric records');toolbar.append(search);
let widen=false,page=0,sort=null,group='',columns=[],filtered=[];
if(selectedGroup){button('Show all groups',()=>{widen=!widen;page=0;render();},toolbar);content.append(make('p',`Selected ${selection.field}: ${selectedGroup}`,'p57-explorer-context'));}
if(!recordSource&&available.length){const tableChoice=make('select');tableChoice.setAttribute('aria-label','Supporting evidence table');available.forEach((t,i)=>{const o=make('option',t.title);o.value=i;tableChoice.append(o);});tableChoice.onchange=()=>{dataset=available[+tableChoice.value];base=dataset.rows;columns=keys();group='';page=0;render();};toolbar.append(tableChoice);}
const groupSelect=make('select');groupSelect.setAttribute('aria-label','Group metric records by');toolbar.append(make('span','Group by'),groupSelect);
const colDetails=make('details',null,'p57-explorer-columns');colDetails.append(make('summary','Columns'));const colBox=make('div');colDetails.append(colBox);toolbar.append(colDetails);
button('Export CSV',()=>download('\uFEFF'+[columns.map(csvValue).join(','),...filtered.map(r=>columns.map(c=>csvValue(fmt(r[c]))).join(','))].join('\r\n'),`metric-${cid}-records.csv`,'text/csv;charset=utf-8'),toolbar);
content.append(toolbar);const summary=make('div',null,'p57-explorer-summary'),warning=make('p','', 'p57-explorer-warning'),breakdown=make('details',null,'p57-breakdown-table');breakdown.append(make('summary','Computed breakdowns · expand to inspect'));const groupGrid=make('div',null,'p57-explorer-grid');breakdown.append(groupGrid);const grid=make('div',null,'p57-explorer-grid'),pager=make('div',null,'p57-explorer-pager');content.append(summary,warning,breakdown,grid,pager);
function keys(){return [...new Set(base.flatMap(r=>Object.keys(r)))].filter(k=>base.some(r=>r[k]!=null&&r[k]!==''));}
if(recordSource&&/trialled|^won$/i.test(label))base=base.map(r=>({'Counts toward numerator':/^won$/i.test(label)?r.Won===true||r.Status==='Won':r['Trial status']==='Trial Completed',...r}));
columns=[...new Set([...( /median life/i.test(label)?['Observed life days','Amount paid']:[]),...keys()])].filter(k=>keys().includes(k)).slice(0,12);
function totals(rows){const fields=['Revenue','Discount','Capacity','Attendances','Amount paid','Completed sessions'].filter(k=>rows.some(r=>numeric(r[k])!=null));return fields.map(k=>[k,sum(rows,k)]);}
function table(headers,rows,target){const t=make('table'),head=make('thead'),tr=make('tr');headers.forEach(h=>{const th=make('th');button(h,()=>{sort={field:h,desc:sort?.field===h?!sort.desc:true};render();},th);tr.append(th);});head.append(tr);t.append(head);const body=make('tbody');rows.forEach(row=>{const r=make('tr');headers.forEach(h=>r.append(make('td',fmt(row[h]))));body.append(r);});t.append(body);target.replaceChildren(t);}
function groups(rows){const map=new Map();for(const r of rows){const name=fmt(r[group]);if(!map.has(name))map.set(name,[]);map.get(name).push(r);}return [...map].map(([name,rs])=>{const row={[group]:name,Records:rs.length};for(const [k,n]of totals(rs))row[k]=n;const cap=sum(rs,'Capacity'),att=sum(rs,'Attendances'),rev=sum(rs,'Revenue');if(cap!=null)row['Utilisation %']=cap&&att!=null?att/cap*100:null;if(rs.some(r=>r['Member ID']!=null))row['Distinct members']=new Set(rs.map(r=>r['Member ID']).filter(x=>x!=null)).size;if(rs.some(r=>r['Trial status']!=null)){row['Trialled %']=rs.filter(r=>r['Trial status']==='Trial Completed').length/rs.length*100;row['Won %']=rs.filter(r=>r.Won===true||r.Status==='Won').length/rs.length*100;}if(rev!=null){row['Revenue / record']=rev/rs.length;if(att>0)row['Revenue / attendance']=rev/att;}return row;}).sort((a,b)=>b.Records-a.Records);}
function render(){const allKeys=keys();const preferred={sessions:'Format',sales:'Product',lapsed:'Status',leads:'Source',checkins:'Member ID'}[metric.source];groupSelect.replaceChildren();const empty=make('option','No grouping');empty.value='';groupSelect.append(empty);allKeys.filter(k=>base.some(r=>r[k]!=null&&numeric(r[k])==null)||k==='Member ID').forEach(k=>{const o=make('option',k);o.value=k;groupSelect.append(o);});groupSelect.value=group;
colBox.replaceChildren();allKeys.forEach(k=>{const l=make('label',k),c=make('input');c.type='checkbox';c.checked=columns.includes(k);c.onchange=()=>{columns=c.checked?[...columns,k]:columns.filter(x=>x!==k);render();};l.prepend(c);colBox.append(l);});
const q=search.value.trim().toLowerCase();filtered=base.filter(r=>(!recordSource||!metric.predicate||metric.predicate(r))&&(!selectedGroup||widen||!groupField||fmt(r[groupField])===selectedGroup)&&(!q||columns.some(c=>fmt(r[c]).toLowerCase().includes(q))));
if(recordSource&&/top tenth/i.test(label)){const counts=new Map();for(const r of base){const id=r['Member ID'];if(id!=null)counts.set(id,(counts.get(id)||0)+1);}const ids=new Set([...counts].sort((a,b)=>b[1]-a[1]).slice(0,Math.max(1,Math.floor(counts.size*.1))).map(([id])=>id));filtered=filtered.filter(r=>ids.has(r['Member ID']));}
if(recordSource&&/came exactly once/i.test(label)){const counts=new Map();for(const r of base){const id=r['Member ID'];if(id!=null)counts.set(id,(counts.get(id)||0)+1);}filtered=filtered.filter(r=>counts.get(r['Member ID'])===1);}
let shown=group?groups(filtered):[...filtered];if(sort)shown.sort((a,b)=>{const x=numeric(a[sort.field]),y=numeric(b[sort.field]);return(sort.desc?-1:1)*(x!=null&&y!=null?x-y:fmt(a[sort.field]).localeCompare(fmt(b[sort.field]),undefined,{numeric:true}));});
const derived=[];const capacity=sum(filtered,'Capacity'),attendances=sum(filtered,'Attendances'),revenue=sum(filtered,'Revenue');if(recordSource&&/utilisation|utilization/.test(label.toLowerCase()))derived.push(['Utilisation %',capacity&&attendances!=null?attendances/capacity*100:null]);if(recordSource&&/average buyer|visits per member/.test(label.toLowerCase())){const members=new Set(filtered.map(r=>r['Member ID']).filter(v=>v!=null)).size;derived.push(['Distinct members',members],['Per member',members?(/buyer/.test(label.toLowerCase())?revenue:filtered.length)/members:null]);}if(recordSource&&/trialled|^won$/i.test(label))derived.push(['Counts toward numerator',filtered.filter(r=>r['Counts toward numerator']).length]);
summary.replaceChildren();for(const [l,v]of [['Records',filtered.length],...derived,...totals(filtered).slice(0,4)]){const e=make('div',l);e.append(make('strong',fmt(v)));summary.append(e);}warning.textContent=dataset?.truncated?`Snapshot contains the first ${base.length.toLocaleString()} of ${dataset.total.toLocaleString()} source records. Totals and breakdowns here describe the retained subset; they do not replace the report headline.`:'';
const pages=Math.max(1,Math.ceil(shown.length/50));page=Math.min(page,pages-1);table(group?[...new Set(shown.flatMap(Object.keys))]:columns,shown.slice(page*50,(page+1)*50),grid);
const breakdownField=group||preferred;if(breakdownField&&allKeys.includes(breakdownField)){const old=group;group=breakdownField;const data=groups(filtered);group=old;table([...new Set(data.flatMap(Object.keys))],data.slice(0,12),groupGrid);breakdown.hidden=false;}else breakdown.hidden=true;
pager.replaceChildren();const prev=button('← Previous',()=>{page--;render();},pager);prev.disabled=page===0;pager.append(make('span',`Page ${page+1} / ${pages} · ${shown.length} ${group?'groups':'records'}`));const next=button('Next →',()=>{page++;render();},pager);next.disabled=page===pages-1;
}
search.oninput=()=>{page=0;render();};groupSelect.onchange=()=>{group=groupSelect.value;page=0;sort=null;render();};render();dialog.classList.add('p57-explorer-dialog');openDialog(label+' · Evidence explorer',content);}
// Metric cards and metric cells open scoped evidence, rather than an isolated label/value.
document.querySelectorAll('.kpi').forEach(card=>{card.classList.add('p57-kpi-action');card.setAttribute('role','button');card.tabIndex=0;const label=card.querySelector('.l')?.textContent||'Metric';card.setAttribute('aria-label','Explore '+label);card.onclick=()=>openExplorer(card,label);card.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();card.click();}};});
document.querySelectorAll('.wrap table').forEach(table=>{const headers=[...table.rows[0]?.cells||[]].map(c=>c.textContent.replace(/\s*↕$/,'').trim());[...table.rows].slice(1).forEach(row=>{[...row.cells].forEach((cell,i)=>{if(i===0){const b=cell.querySelector('button');if(b)b.onclick=()=>openExplorer(cell,headers[0],{field:headers[0],value:cell.textContent.trim()});}else if(numeric(cell.textContent)!=null){cell.tabIndex=0;cell.setAttribute('role','button');cell.setAttribute('aria-label',`Explore ${headers[i]} for ${row.cells[0].textContent.trim()}`);cell.onclick=()=>openExplorer(cell,headers[i],{field:headers[0],value:row.cells[0].textContent.trim()});cell.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();cell.click();}};}});});});
button('Pause chapter motion',()=>{const paused=document.documentElement.classList.toggle('p57-motion-paused');R.status.textContent=paused?'Chapter motion paused.':'Chapter motion resumed.';});
// Existing h2 nodes and their stable IDs remain the anchors used by notes/hosting.
const sections=[...document.querySelectorAll('.wrap>section')];sections.forEach((section,index)=>{if(section.querySelector('.p57-chapter-hero'))return;const heading=section.querySelector('h2');if(!heading)return;const match=heading.textContent.match(/Chapter\s+(\d+)/i),number=match?match[1].padStart(2,'0'):String(index+1).padStart(2,'0');const subtitle=heading.nextElementSibling?.classList.contains('sub')?heading.nextElementSibling:null;const description=section.querySelector('.call p')?.textContent||subtitle?.textContent||'Explore the findings, supporting evidence and actions for this chapter.';const hero=make('div',null,'p57-chapter-hero');hero.dataset.tone=['navy','teal','plum'][index%3];heading.before(hero);hero.append(make('span',number,'p57-hero-number'),make('div',`Physique 57 · Studio intelligence · Chapter ${number}`,'p57-hero-eyebrow'),heading);if(subtitle)hero.append(subtitle);hero.append(make('p',description.length>360?description.slice(0,360).replace(/\s+\S*$/,'')+'…':description,'p57-hero-description'));
const art=document.createElementNS('http://www.w3.org/2000/svg','svg');art.setAttribute('viewBox','0 0 400 240');art.setAttribute('aria-hidden','true');art.classList.add('p57-hero-art');for(let i=0;i<7;i++){const ellipse=document.createElementNS(art.namespaceURI,'ellipse');ellipse.setAttribute('cx','240');ellipse.setAttribute('cy','120');ellipse.setAttribute('rx',String(50+i*24));ellipse.setAttribute('ry',String(28+i*15));ellipse.setAttribute('fill','none');ellipse.setAttribute('stroke','#b5e2ed');ellipse.setAttribute('stroke-width','1.2');ellipse.setAttribute('transform','rotate(-25 240 120)');art.append(ellipse);}hero.append(art);
const strip=make('div',null,'p57-marquee'),track=make('div',null,'p57-marquee-track');strip.setAttribute('aria-label','Chapter key metrics');strip.tabIndex=0;const values=[...section.querySelectorAll('.kpi')].map(k=>[k.querySelector('.l')?.textContent,k.querySelector('.v')?.textContent]);for(let repeat=0;repeat<2;repeat++){const group=make('div',null,'p57-marquee-group');if(repeat)group.setAttribute('aria-hidden','true');for(const [label,value]of values.length?values:[['Evidence','Explore'],['Findings','Review'],['Actions','Decide']]){const item=make('span',label);item.append(make('b',value));group.append(item);}track.append(group);}strip.append(track);hero.append(strip);});
})();
