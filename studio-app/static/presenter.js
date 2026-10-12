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
const navTrigger=make('button','','p57-nav-trigger');navTrigger.innerHTML='<span class="p57-menu-glyph" aria-hidden="true"><i></i><i></i><i></i></span><span>Contents</span>';navTrigger.setAttribute('aria-label','Toggle report navigation');navTrigger.setAttribute('aria-controls','p57-navigation');nav.id='p57-navigation';document.body.append(navTrigger,nav);
let navTimer,navPinned=saved.preferences.navPinned!==false;
function setNav(open){nav.hidden=!open;root.classList.toggle('p57-left-open',open);navTrigger.setAttribute('aria-expanded',String(open));if(open)idleNav();}
function idleNav(){clearTimeout(navTimer);if(!navPinned&&!nav.hidden)navTimer=setTimeout(()=>{if(nav.matches(':hover')||nav.contains(document.activeElement))idleNav();else setNav(false);},60000);}
navTrigger.onclick=()=>setNav(nav.hidden);
const pin=button('Pin navigation',()=>{navPinned=!navPinned;pin.setAttribute('aria-pressed',String(navPinned));pin.textContent=navPinned?'Unpin navigation':'Pin navigation';change('preferences','navPinned',navPinned);idleNav();},nav);
const navList=make('div',null,'p57-nav-list');nav.append(navList);
const chapterSections=[...document.querySelectorAll('.wrap > section')];
function chapterGroup(title,target,topics,index){
 const group=make('div',null,'p57-nav-chapter');
 const main=button(`${String(index+1).padStart(2,'0')}  ${title.replace(/^Chapter\s+\d+\s*/i,'').trim()}`,()=>go(target.id),group);
 main.classList.add('p57-nav-chapter-label');main.dataset.section=target.id;
 const children=make('div',null,'p57-nav-children');children.setAttribute('role','group');children.setAttribute('aria-label',title+' subtopics');
 topics.forEach(h=>{const child=button(h.textContent,()=>go(h.id),children);child.dataset.section=h.id;});
 group.append(children);navList.append(group);
}
if(chapterSections.length){chapterSections.forEach((section,i)=>{const topics=[...section.querySelectorAll('h2')],main=topics.shift();if(main)chapterGroup(main.textContent,main,topics,i);});}
else if(headings.length){const cover=document.querySelector('body > header');if(cover&&!cover.id)cover.id='p57-report-cover';const title=document.querySelector('body > header h1')?.textContent||document.title;chapterGroup(title,document.querySelector('body > header')||headings[0],headings,0);}

function go(id){current=id;document.getElementById(id)?.scrollIntoView({block:'start',behavior:'instant'});renderNotes();markNav();publishSoon();}
function markNav(){navList.querySelectorAll('button').forEach(b=>b.setAttribute('aria-current',b.dataset.section===current?'location':'false'));navList.querySelectorAll('.p57-nav-chapter').forEach(group=>group.classList.toggle('p57-nav-chapter-active',!!group.querySelector('[aria-current=location]')));}
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
range('Drawer width',300,440,360,'drawerWidth',v=>root.style.setProperty('--p57-panel-width',Math.max(300,Math.min(440,Number(v)||360))+'px'));
const mirror=button('Mirror',()=>{const on=prompt.classList.toggle('mirrored');mirror.setAttribute('aria-pressed',String(on));mirror.classList.toggle('active',on);change('preferences','promptMirror',on);},controls);

const timerBox=make('div',null,'p57-timer-group');
let timerStart=0,timerElapsed=0;const timer=make('output','00:00','p57-timer');timerBox.append(timer);
button('Start / pause timer',()=>{if(timerStart){timerElapsed+=Date.now()-timerStart;timerStart=0;}else timerStart=Date.now();},timerBox);
button('Reset timer',()=>{timerStart=0;timerElapsed=0;timer.textContent='00:00';},timerBox);
controls.append(timerBox);

const timerInterval=setInterval(()=>{const secs=Math.floor((timerElapsed+(timerStart?Date.now()-timerStart:0))/1000);timer.textContent=String(Math.floor(secs/60)).padStart(2,'0')+':'+String(secs%60).padStart(2,'0');},1000);
window.addEventListener('pagehide',()=>clearInterval(timerInterval));

function speakerPoints(h){
  if(!h)return [];
  const items=[],seen=new Set();
  const add=(label,text)=>{text=(text||'').replace(/\s+/g,' ').trim();if(!text||seen.has(text))return;seen.add(text);items.push(label+': '+text);};
  const start=h.closest('.p57-chapter-hero')||h;
  const summary=start.querySelector?.('.p57-hero-description');
  const sentence=t=>(t||'').match(/^.*?[.!?](?=\s|$)/)?.[0]||t;
  if(summary)add('Lead with',sentence(summary.textContent));
  for(let e=start.nextElementSibling;e&&!e.matches('h2,.p57-chapter-hero');e=e.nextElementSibling){
    if(e.matches('.kpis,.stat'))[...e.querySelectorAll('.kpi,.stat>div')].slice(0,3).forEach(k=>{const value=k.querySelector('.v')?.textContent;if(value)add(k.querySelector('.l')?.textContent||'Key figure',value);});
    else if(e.matches('.call,p'))add(items.length?'Highlight':'Lead with',sentence(e.querySelector('p')?.textContent||e.textContent));
    else if(e.matches('.rec'))add('Next step',e.querySelector('h3')?.textContent);
    if(items.length>=4)break;
  }
  return items.slice(0,4);
}
R.speakerPoints=speakerPoints;
function updatePrompt(){const h=document.getElementById(current);let text=note.value.trim();if(!text){text=h?.textContent||document.title;for(let e=h?.closest('.p57-chapter-hero')?.nextElementSibling||h?.nextElementSibling;e&&e.tagName!=='H2';e=e.nextElementSibling)if(e.matches('p,.sub,.call'))text+='\n\n'+e.textContent;}prompt.replaceChildren(...text.split(/\n\s*\n|\n(?=[•-])/).filter(Boolean).map(t=>make('p',t,'p57-prompt-point')));}
function renderNotes(){
  const h=document.getElementById(current);
  sectionLabel.textContent=h?.textContent||'Overview';
  note.value=Object.hasOwn(saved.notes,current)?saved.notes[current]:(meeting&&!meeting.is_host?'':speakerPoints(h).map(t=>'• '+t).join('\n\n'));
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
// Hooks for the floating report-interface controls (speaker notes launcher,
// AI assistant, layout editor).
window.P57Speaker={section:()=>current,open:openSpeaker,notes:()=>openSpeaker(true),drawer,bar,notice};
// Only narrative fields are editable; computed table values retain their source definitions.
const editables=[...document.querySelectorAll('.wrap p,.wrap h3,.wrap h4,.wrap .sub,body>header h1,body>header .lede')].filter(e=>!e.closest('table,svg,.rt-table-tools'));
const originalText=new Map(editables.map(e=>[e,e.textContent]));
const originalHTML=new Map(editables.map(e=>[e,e.innerHTML]));
editables.forEach((e,i)=>e.dataset.editId='text-'+i);
let editing=false;const edit=button('Edit report text',()=>{if(meeting&&!meeting.is_host)return;if(window.P57Edit){window.P57Edit.setLayout(!root.classList.contains('p57-layout-on'));toggleTools(false);return;}editing=!editing;edit.textContent=editing?'Finish editing':'Edit report text';edit.setAttribute('aria-pressed',String(editing));editables.forEach(e=>{e.contentEditable=editing?'true':'false';});toggleTools(false);});
editables.forEach(e=>e.addEventListener('input',()=>change('edits',e.dataset.editId,e.textContent)));
function applyEdits(edits=saved.edits){editables.forEach(e=>{if(document.activeElement===e)return;if(Object.hasOwn(edits,e.dataset.editId)){if(e.textContent!==edits[e.dataset.editId])e.textContent=edits[e.dataset.editId];}else if(!window.P57Edit&&e.innerHTML!==originalHTML.get(e))e.innerHTML=originalHTML.get(e);});}
let annotationSnapshot='';
function renderAnnotations(values=saved.annotations){const snapshot=JSON.stringify(values||{});if(snapshot===annotationSnapshot)return;annotationSnapshot=snapshot;document.querySelectorAll('.p57-annotation-callout').forEach(e=>e.remove());for(const [id,text]of Object.entries(values||{})){if(!text)continue;const h=document.getElementById(id);if(h){const a=make('aside',text,'p57-annotation-callout');a.setAttribute('aria-label','Report annotation');h.after(a);}}}
let restoringPreferences=false;
function applyPreferences(){restoringPreferences=true;for(const s of bar.querySelectorAll('select')){const label=s.getAttribute('aria-label'),key={Theme:'theme',Colour:'accent',Layout:'layout',Density:'density',Text:'size',Speed:'speechSpeed'}[label];if(key&&saved.preferences[key]){s.value=saved.preferences[key];s.dispatchEvent(new Event('change'));}}if(saved.preferences.promptFont)prompt.style.fontSize=saved.preferences.promptFont+'px';if(saved.preferences.promptSpeed)speed.value=saved.preferences.promptSpeed;prompt.classList.toggle('mirrored',!!saved.preferences.promptMirror);navPinned=saved.preferences.navPinned!==false;pin.textContent=navPinned?'Unpin navigation':'Pin navigation';pin.setAttribute('aria-pressed',String(navPinned));if(saved.preferences.drawerWidth)root.style.setProperty('--p57-panel-width',Math.max(300,Math.min(440,Number(saved.preferences.drawerWidth)||360))+'px');idleNav();restoringPreferences=false;}
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
button('Download edited report',async()=>{try{await window.P57Edit?.commitEdit();await flush();let html;if(online&&route){const response=await fetch(location.pathname);if(!response.ok)throw Error('Report download failed');html=await response.text();}else{throw Error('Use the app to export an edited report.');}const state=JSON.stringify(saved).replace(/</g,'\\u003c');const structural=JSON.stringify(window.P57Edit?.edits||[]).replace(/</g,'\\u003c');const pos=html.toLowerCase().lastIndexOf('</head>');html=html.slice(0,pos)+`<script type="application/json" id="p57-saved-workspace">${state}<\/script><script type="application/json" id="p57-structural-edits">${structural}<\/script>`+html.slice(pos);const url=URL.createObjectURL(new Blob([html],{type:'text/html'}));const a=make('a');a.href=url;a.download='Edited_Performance_Review.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){notice.textContent=e.message;}});
applyEdits();renderAnnotations();renderNotes();markNav();applyPreferences();
(async()=>{if(!online)return;try{const remote=await api('/api/workspace?report='+encodeURIComponent(report));for(const kind of ['notes','preferences','edits','annotations'])saved[kind]={...saved[kind],...remote[kind],...pending[kind]};cache();applyEdits();renderAnnotations();renderNotes();applyPreferences();notice.textContent='Saved workspace restored';if(Object.keys(pending).length)flush();const code=new URLSearchParams(location.search).get('meeting');let previous;try{previous=localStorage.getItem('p57-host:'+report);}catch{}if(code||previous){const m=await api('/api/meetings/'+encodeURIComponent(code||previous));if(m.active&&(code||m.is_host))navigateMeeting(m);}}catch(e){notice.textContent='Local workspace restored. '+e.message;}})();
})();
