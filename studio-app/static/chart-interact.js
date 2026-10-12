/* Interactive charts: the engine draws static SVG, so this reads each chart's
   own marks, axis and labels back out of the drawing and adds hover
   tooltips, legend filtering, keyboard stepping and a grow-in on first view. */
(() => {
'use strict';
if(document.documentElement.dataset.p57Charts)return;document.documentElement.dataset.p57Charts='1';
const charts=[...document.querySelectorAll('.wrap .chart svg')].filter(s=>!s.closest('.p57-chapter-hero'));
const clean=t=>(t||'').replace(/\s+/g,' ').trim();
const box=el=>{try{return el.getBBox();}catch{return null;}};
const colorOf=el=>(el.getAttribute('fill')&&el.getAttribute('fill')!=='#fff'&&el.getAttribute('fill')!=='none'?el.getAttribute('fill'):el.getAttribute('stroke')||'').toLowerCase();

function parseTick(t){const m=t.match(/^([^\d\-]*)(-?[\d,]*\.?\d+)(.*)$/);if(!m)return null;return{pre:m[1],num:parseFloat(m[2].replace(/,/g,'')),suf:m[3],dec:(m[2].split('.')[1]||'').length};}

function setup(svg){
 const fig=svg.closest('.chart');if(!fig||fig.dataset.interactive)return;fig.dataset.interactive='1';
 const texts=[...svg.querySelectorAll('text')].map(el=>({el,t:clean(el.textContent),b:box(el),anchor:el.getAttribute('text-anchor')||'start'})).filter(x=>x.b&&x.t);
 const rects=[...svg.querySelectorAll('rect')].map(el=>({el,b:box(el),c:colorOf(el)})).filter(x=>x.b&&x.b.width>0&&x.b.height>0&&x.c);
 // Legend swatches are the small squares with a caption to their right.
 const legend=new Map();
 const legendRects=rects.filter(r=>r.b.width<=12&&r.b.height<=12);
 for(const r of legendRects){const cap=texts.filter(x=>x.b.x>=r.b.x+r.b.width-1&&x.b.x-r.b.x<40&&Math.abs((x.b.y+x.b.height/2)-(r.b.y+r.b.height/2))<9).sort((a,b)=>a.b.x-b.b.x)[0];if(cap){legend.set(r.c,{name:cap.t,swatch:r,caption:cap});}}
 const bars=rects.filter(r=>!legendRects.includes(r));
 const dots=[...svg.querySelectorAll('circle')].map(el=>({el,b:box(el),c:colorOf(el),cx:+el.getAttribute('cx'),cy:+el.getAttribute('cy')})).filter(x=>x.b);
 const used=new Set([...legend.values()].map(l=>l.caption));
 const free=texts.filter(x=>!used.has(x));
 // Axis ticks: right-aligned numbers stacked down the left edge.
 const ticks=free.filter(x=>x.anchor==='end'&&parseTick(x.t)).map(x=>({y:x.b.y+x.b.height/2-3,...parseTick(x.t),x:x.b.x})).filter((x,i,a)=>a.filter(o=>Math.abs(o.x-x.x)<20).length>2);
 const scale=ticks.length>1?(()=>{const [a,b]=[ticks[0],ticks[ticks.length-1]];const k=(b.num-a.num)/(b.y-a.y);return{at:y=>a.num+(y-a.y)*k,fmt:v=>a.pre+v.toLocaleString('en-IN',{maximumFractionDigits:Math.max(a.dec,b.dec,Math.abs(v)<10?1:0)})+a.suf,zero:a.y-(a.num)/k};})():null;
 // Orientation: horizontal bars share a left edge (or, when diverging, a centre line);
 // vertical bars share a baseline.
 const share=f=>bars.length?bars.filter(f).length/bars.length:0;
 const minX=Math.min(...bars.map(r=>r.b.x)),maxB=Math.max(...bars.map(r=>r.b.y+r.b.height));
 const edges=bars.map(r=>[Math.round(r.b.x),Math.round(r.b.x+r.b.width)]).flat();const mode=edges.sort((a,b)=>edges.filter(v=>v===b).length-edges.filter(v=>v===a).length)[0];
 const horizontal=bars.length>0&&Math.max(share(r=>Math.abs(r.b.x-minX)<1.5),share(r=>Math.abs(r.b.x-mode)<1.5||Math.abs(r.b.x+r.b.width-mode)<1.5))>share(r=>Math.abs(r.b.y+r.b.height-maxB)<1.5);
 // Category labels sit below the lowest mark, i.e. under the x axis.
 const floor=Math.max(...bars.map(r=>r.b.y+r.b.height),...[...svg.querySelectorAll('circle')].map(c=>+c.getAttribute('cy')||0),0);
 const xLabels=free.filter(x=>x.b.y>=floor-2);
 const near=(list,score)=>list.map(x=>({x,s:score(x)})).filter(o=>o.s!=null&&o.s<Infinity).sort((a,b)=>a.s-b.s)[0]?.x;

 const marks=[];
 for(const r of bars){const b=r.b,cx=b.x+b.width/2,cy=b.y+b.height/2;let label,value;
  if(horizontal){label=near(free,x=>x.anchor==='end'&&x.b.x+x.b.width<=b.x+2?Math.abs((x.b.y+x.b.height/2)-cy)+x.b.x*.0001:null);
   value=near(free,x=>{if(x===label)return null;const yc=x.b.y+x.b.height/2;if(Math.abs(yc-cy)>b.height/2+6)return null;if(x.b.x>=b.x+b.width-2)return x.b.x-(b.x+b.width);if(x.b.x+x.b.width<=b.x+2&&x.b.x+x.b.width>b.x-60)return b.x-(x.b.x+x.b.width);return null;});}
  else{label=near(xLabels,x=>x.b.y>=b.y+b.height-1?Math.abs((x.b.x+x.b.width/2)-cx)+(x.b.y-(b.y+b.height))*.2:null);
   value=near(free,x=>x!==label&&x.b.y+x.b.height<=b.y+3&&b.y-(x.b.y+x.b.height)<16&&Math.abs((x.b.x+x.b.width/2)-cx)<Math.max(b.width,10)?Math.abs((x.b.x+x.b.width/2)-cx):null);}
  let v=value?.t;if(!v&&scale&&!horizontal)v=scale.fmt(scale.at(b.y)-scale.at(b.y+b.height));
  marks.push({el:r.el,kind:'bar',c:r.c,label:label?.t||'',value:v||'',cx,cy:b.y,b});}
 const lineChart=dots.length>1&&svg.querySelector('path');
 for(const d of dots){const label=near(xLabels,x=>x.b.y>d.cy?Math.abs((x.b.x+x.b.width/2)-d.cx):null);
  const value=lineChart?null:near(free,x=>Math.abs((x.b.y+x.b.height/2)-d.cy)<10&&x.b.x>d.cx?x.b.x-d.cx:null);
  const rowLabel=lineChart?null:near(free,x=>x.anchor==='end'&&x.b.x<d.cx&&Math.abs((x.b.y+x.b.height/2)-d.cy)<10?d.cx-x.b.x:null);
  marks.push({el:d.el,kind:'dot',c:d.c,label:(rowLabel||label)?.t||'',value:value?.t||(scale?scale.fmt(scale.at(d.cy)):''),cx:d.cx,cy:d.cy,b:d.b});}
 if(!marks.length)return;
 marks.forEach(m=>{m.series=legend.get(m.c)?.name||'';m.el.classList.add('p57-mark');});
 svg.p57Marks=marks;
 svg.classList.add('p57-chart-live');svg.setAttribute('tabindex','0');svg.setAttribute('role','img');
 const caption=fig.querySelector('figcaption')?.textContent||'Chart';svg.setAttribute('aria-label',caption+'. Use arrow keys to step through the values.');

 const tip=document.createElement('div');tip.className='p57-chart-tip';tip.hidden=true;tip.setAttribute('role','status');fig.append(tip);
 const hidden=new Set();
 function show(group,anchor){
  marks.forEach(m=>m.el.classList.toggle('p57-dim',!group.includes(m)));
  tip.replaceChildren();
  const head=document.createElement('strong');head.textContent=group[0].label||caption;tip.append(head);
  for(const m of group){if(hidden.has(m.c))continue;const row=document.createElement('span');const sw=document.createElement('i');sw.style.background=m.c;row.append(sw);
   const name=document.createElement('em');name.textContent=m.series||(group.length>1?'':'Value');const val=document.createElement('b');val.textContent=m.value||'—';row.append(name,val);tip.append(row);}
  tip.hidden=false;
  const sr=svg.getBoundingClientRect(),fr=fig.getBoundingClientRect(),k=sr.width/(svg.viewBox.baseVal?.width||sr.width);
  let x=sr.left-fr.left+anchor.cx*k,y=sr.top-fr.top+anchor.cy*k;
  const w=tip.offsetWidth,h=tip.offsetHeight;x=Math.min(Math.max(x-w/2,8),fr.width-w-8);y=y-h-14<0?y+18:y-h-14;
  tip.style.transform=`translate(${Math.round(x)}px,${Math.round(y)}px)`;
 }
 function hide(){tip.hidden=true;marks.forEach(m=>m.el.classList.remove('p57-dim'));}
 const visible=()=>marks.filter(m=>!hidden.has(m.c));
 function groupFor(m){if(m.kind==='dot'&&lineChart)return visible().filter(o=>o.kind==='dot'&&Math.abs(o.cx-m.cx)<2);return[m];}
 svg.addEventListener('pointermove',e=>{
  const pt=svg.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;const p=pt.matrixTransform(svg.getScreenCTM().inverse());
  let m=marks.find(o=>o.el===e.target&&!hidden.has(o.c));
  if(!m&&lineChart){m=visible().filter(o=>o.kind==='dot').sort((a,b)=>Math.abs(a.cx-p.x)-Math.abs(b.cx-p.x))[0];}
  if(!m){hide();return;}const g=groupFor(m);show(g,{cx:m.cx,cy:Math.min(...g.map(o=>o.cy))});
 });
 svg.addEventListener('pointerleave',hide);
 let step=-1;
 svg.addEventListener('keydown',e=>{const list=visible().filter((m,i,a)=>!(lineChart&&m.kind==='dot')||a.findIndex(o=>o.kind==='dot'&&Math.abs(o.cx-m.cx)<2)===i).sort((a,b)=>horizontal?a.cy-b.cy:a.cx-b.cx||a.cy-b.cy);
  if(!['ArrowRight','ArrowLeft','ArrowDown','ArrowUp','Escape'].includes(e.key)||!list.length)return;e.preventDefault();
  if(e.key==='Escape'){hide();step=-1;return;}step=(step+(e.key==='ArrowRight'||e.key==='ArrowDown'?1:-1)+list.length)%list.length;const m=list[step];const g=groupFor(m);show(g,{cx:m.cx,cy:Math.min(...g.map(o=>o.cy))});});
 svg.addEventListener('blur',hide);
 // Legend entries become filters.
 for(const [c,l] of legend){for(const el of [l.swatch.el,l.caption.el]){el.classList.add('p57-legend-item');el.setAttribute('role','button');el.setAttribute('tabindex','0');el.setAttribute('aria-pressed','true');el.setAttribute('aria-label','Show or hide '+l.name);
  const toggle=()=>{hidden.has(c)?hidden.delete(c):hidden.add(c);const on=!hidden.has(c);marks.filter(m=>m.c===c).forEach(m=>m.el.classList.toggle('p57-off',!on));[l.swatch.el,l.caption.el].forEach(x=>{x.setAttribute('aria-pressed',String(on));x.classList.toggle('p57-legend-off',!on);});hide();};
  el.addEventListener('click',toggle);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle();}});}}
 // Bars grow from their baseline the first time the chart is seen.
 marks.forEach((m,i)=>{m.el.style.setProperty('--i',String(Math.min(i,24)));m.el.classList.add(m.kind==='bar'?(horizontal?'p57-grow-x':'p57-grow-y'):'p57-pop');});
 const io='IntersectionObserver' in window?new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){svg.classList.add('p57-in');io.unobserve(svg);}}),{threshold:.25}):null;
 if(io)io.observe(svg);else svg.classList.add('p57-in');
}
charts.forEach(svg=>{try{setup(svg);}catch(err){/* a chart we cannot read stays static */}});
window.P57Charts={setup};
})();
