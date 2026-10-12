(() => {
'use strict';
const R=window.P57Reader;if(!R||document.querySelector('.p57-stage-controls'))return;
const {make,button}=R,root=document.documentElement;
const stages=[];const cover=document.querySelector('body>header');if(cover)stages.push({title:cover.querySelector('h1')?.textContent||'Cover',nodes:[cover]});
const wrap=document.querySelector('.wrap');
function collect(container){let stage=null;for(const node of container.children){if(node.matches('section')&&node.querySelector('h2')){collect(node);continue;}if(node.matches('.toc'))continue;const h=node.matches('h2')?node:node.querySelector(':scope > h2');if(h||!stage){stage={title:h?.textContent||'Key metrics',nodes:[]};stages.push(stage);}stage.nodes.push(node);}}
if(wrap)collect(wrap);if(!stages.length)return;
const dock=make('nav',null,'p57-stage-controls');dock.hidden=true;dock.setAttribute('aria-label','Presentation controls');document.body.append(dock);
const launch=button('Present',()=>active?finish():start(),document.querySelector('.p57-reader-header')||R.bar);launch.title='Section presentation with agenda, timer and audience controls';
let active=false,index=0,elapsed=0,paused=false,laser=false,fullOwned=false;
const agenda=make('select');agenda.setAttribute('aria-label','Presentation agenda');stages.forEach((s,i)=>{const o=make('option',String(i+1).padStart(2,'0')+' · '+s.title);o.value=i;agenda.append(o);});agenda.onchange=()=>show(Number(agenda.value));
const previous=button('← Previous',()=>show(index-1),dock);dock.append(agenda);const next=button('Next →',()=>show(index+1),dock);
const clock=make('span','00:00','p57-stage-clock');clock.setAttribute('aria-label','Presentation elapsed time');dock.append(clock);
const timing=button('Pause timer',()=>{paused=!paused;timing.textContent=paused?'Resume timer':'Pause timer';},dock);button('Reset timer',()=>{elapsed=0;clock.textContent='00:00';},dock);
const pointer=button('Laser',()=>{laser=!laser;pointer.setAttribute('aria-pressed',String(laser));dot.hidden=!laser;},dock);pointer.setAttribute('aria-pressed','false');
const shade=make('div',null,'p57-stage-blackout');shade.hidden=true;shade.setAttribute('role','status');shade.textContent='Audience screen paused · press B or Escape to return';document.body.append(shade);
button('Blackout',()=>shade.hidden=!shade.hidden,dock);button('Fullscreen',async()=>{try{if(document.fullscreenElement){await document.exitFullscreen();fullOwned=false;}else{await root.requestFullscreen();fullOwned=true;}}catch{R.status.textContent='Fullscreen is unavailable.';}},dock);button('Finish',finish,dock);
const dot=make('div',null,'p57-stage-laser');dot.hidden=true;dot.setAttribute('aria-hidden','true');document.body.append(dot);
function start(){if(root.classList.contains('p57-layout-on'))window.P57Edit?.setLayout(false);active=true;launch.textContent='Finish presenting';root.classList.add('p57-presenting');dock.hidden=false;elapsed=0;paused=false;timing.textContent='Pause timer';show(0);}
function show(value){index=Math.max(0,Math.min(stages.length-1,value));for(const s of stages)for(const node of s.nodes)node.classList.toggle('p57-stage-hidden',s!==stages[index]);agenda.value=String(index);previous.disabled=index===0;next.disabled=index===stages.length-1;window.scrollTo({top:0,behavior:'instant'});}
function finish(){active=false;launch.textContent='Present';root.classList.remove('p57-presenting');for(const s of stages)for(const node of s.nodes)node.classList.remove('p57-stage-hidden');dock.hidden=true;shade.hidden=true;dot.hidden=true;laser=false;pointer.setAttribute('aria-pressed','false');if(fullOwned&&document.fullscreenElement)document.exitFullscreen().catch(()=>{});fullOwned=false;}
const interval=setInterval(()=>{if(active&&!paused){elapsed++;clock.textContent=String(Math.floor(elapsed/60)).padStart(2,'0')+':'+String(elapsed%60).padStart(2,'0');}},1000);
window.addEventListener('pointermove',e=>{if(active&&laser){dot.style.left=e.clientX+'px';dot.style.top=e.clientY+'px';}});
window.addEventListener('keydown',e=>{if(!active||e.target.closest?.('input,textarea,select,[contenteditable=true]'))return;if(e.key==='Escape'){e.preventDefault();if(!shade.hidden)shade.hidden=true;else finish();}else if(['ArrowRight','PageDown','ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(index+(['ArrowRight','PageDown'].includes(e.key)?1:-1));}else if(e.key.toLowerCase()==='b'){e.preventDefault();shade.hidden=!shade.hidden;}});
window.addEventListener('pagehide',()=>clearInterval(interval));window.P57Stage={start,finish,show,stages};
})();
