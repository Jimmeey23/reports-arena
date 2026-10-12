/* Chapter openers: each chapter gets its own animated motif, drawn from what
   the chapter measures, plus a scrolling contents strip under the cover. */
(() => {
'use strict';
const NS='http://www.w3.org/2000/svg';
if(document.querySelector('.p57-art'))return;

// Pseudo-random but stable per chapter, so the artwork never shuffles between visits.
function rng(seed){let s=0;for(const c of seed)s=(s*31+c.charCodeAt(0))>>>0;return()=>((s=(s*1664525+1013904223)>>>0)/4294967296);}
const r2=n=>Math.round(n*10)/10;

const MOTIFS={
 // Revenue: columns rising out of a baseline, a trend line drawn over them.
 sales(rand){let o='';const n=9;for(let i=0;i<n;i++){const h=40+rand()*120+i*10,x=40+i*38;o+=`<rect class="a-rise" x="${x}" y="${220-h}" width="22" height="${h}" rx="5" style="--d:${i*.12}s"/>`;}
  let d='M51 '+(200-50);for(let i=1;i<n;i++)d+=` L${51+i*38} ${r2(190-40-i*14-rand()*30)}`;return o+`<path class="a-draw" d="${d}" pathLength="1"/>`;},
 // Classes: a studio floor of seats filling in waves.
 class(rand){let o='';for(let r=0;r<6;r++)for(let c=0;c<11;c++){const filled=rand()>.28;o+=`<circle class="a-seat${filled?' on':''}" cx="${40+c*31}" cy="${40+r*31}" r="9" style="--d:${r2((c+r)*.09)}s"/>`;}return o;},
 // Instructors: orbits around a centre, each carrying a client.
 instructor(rand){let o='<circle class="a-core" cx="200" cy="125" r="16"/>';for(let i=0;i<4;i++){const rr=44+i*30;o+=`<circle class="a-ring" cx="200" cy="125" r="${rr}"/><g class="a-orbit" style="--t:${10+i*5}s;--s:${r2(rand()*-8)}s"><circle class="a-dot" cx="${200+rr}" cy="125" r="${6-i}"/></g>`;}return o;},
 // Lapsed members: a cluster that slowly lets points drift away.
 lapse(rand){let o='';for(let i=0;i<34;i++){const a=rand()*Math.PI*2,d=rand()*58;const drift=i%3===0;o+=`<circle class="${drift?'a-drift':'a-stay'}" cx="${r2(170+Math.cos(a)*d)}" cy="${r2(125+Math.sin(a)*d)}" r="${r2(4+rand()*4)}" style="--d:${r2(rand()*6)}s;--x:${r2(120+rand()*90)}px;--y:${r2(-60+rand()*120)}px"/>`;}return o;},
 // Formats: overlapping circles that breathe, like a Venn of disciplines.
 format(){return[[160,110],[230,110],[195,165]].map(([x,y],i)=>`<circle class="a-venn" cx="${x}" cy="${y}" r="70" style="--d:${i*.9}s"/>`).join('');},
 // Cancellations: a booking ring with gaps that keep reopening.
 cancel(){let o='';for(let i=0;i<3;i++)o+=`<circle class="a-dash" cx="200" cy="125" r="${54+i*32}" pathLength="100" style="--t:${12+i*6}s;--dir:${i%2?-1:1}"/>`;return o+'<circle class="a-core" cx="200" cy="125" r="12"/>';},
 // Leads: enquiries flowing down a funnel.
 lead(rand){let o='<path class="a-funnel" d="M60 30 H340 L240 150 V225 H160 V150 Z"/>';for(let i=0;i<16;i++){const x=80+rand()*240;o+=`<circle class="a-fall" cx="${r2(x)}" cy="20" r="4" style="--d:${r2(rand()*5)}s;--x:${r2(200-x)}px"/>`;}return o;},
 // Overview: a slow radial of spokes, one per measure.
 overview(rand){let o='';for(let i=0;i<36;i++){const a=i/36*Math.PI*2,l=50+rand()*70;o+=`<line class="a-spoke" x1="${r2(200+Math.cos(a)*30)}" y1="${r2(125+Math.sin(a)*30)}" x2="${r2(200+Math.cos(a)*(30+l))}" y2="${r2(125+Math.sin(a)*(30+l))}" style="--d:${r2(i*.08)}s"/>`;}return `<g class="a-spin">${o}</g><circle class="a-core" cx="200" cy="125" r="20"/>`;},
 // Anything else: layered waves.
 wave(){let o='';for(let i=0;i<4;i++){let d=`M0 ${120+i*18}`;for(let x=0;x<=800;x+=100)d+=` Q${x+50} ${i%2?90+i*18:150+i*18} ${x+100} ${120+i*18}`;o+=`<path class="a-wave" d="${d}" style="--t:${8+i*3}s"/>`;}return o;}
};
function motifFor(id,title){const t=(id+' '+title).toLowerCase();
 if(/sales|revenue|money/.test(t))return'sales';if(/instructor|trainer/.test(t))return'instructor';if(/class|session|capacity/.test(t))return'class';
 if(/lapse|churn|member/.test(t))return'lapse';if(/format/.test(t))return'format';if(/cancel|discount/.test(t))return'cancel';
 if(/lead|funnel|acquisition/.test(t))return'lead';if(/overview|intelligence|studio/.test(t))return'overview';return'wave';}

document.querySelectorAll('.wrap>section').forEach((section,index)=>{
 const hero=section.querySelector(':scope>.p57-chapter-hero');if(!hero)return;
 const title=hero.querySelector('h2')?.textContent||'';const kind=motifFor(section.id||'',title);
 hero.querySelector('.p57-hero-art')?.remove();
 const art=document.createElementNS(NS,'svg');art.setAttribute('viewBox','0 0 400 250');art.setAttribute('aria-hidden','true');art.setAttribute('class','p57-art p57-hero-art');
 art.innerHTML=MOTIFS[kind](rng(section.id||String(index)));hero.dataset.motif=kind;hero.style.setProperty('--hue',String(index*37%360));
 hero.append(art);
});

// Cover strip: the chapters of this review, scrolling under the title.
const cover=document.querySelector('body>header:not(.top)');
const chapters=[...document.querySelectorAll('.wrap>section .p57-chapter-hero h2')].map(h=>h.textContent.replace(/^Chapter\s+\d+\s*/i,'').trim());
if(cover&&chapters.length&&!cover.querySelector('.p57-cover-strip')){
 const strip=document.createElement('div');strip.className='p57-cover-strip p57-marquee';strip.setAttribute('aria-label','Chapters in this review');
 const track=document.createElement('div');track.className='p57-marquee-track';
 for(let k=0;k<2;k++){const g=document.createElement('div');g.className='p57-marquee-group';if(k)g.setAttribute('aria-hidden','true');
  chapters.forEach((c,i)=>{const s=document.createElement('span');const n=document.createElement('b');n.textContent=String(i+1).padStart(2,'0');s.append(n,document.createTextNode(c));g.append(s);});track.append(g);}
 strip.append(track);cover.append(strip);
}
})();
