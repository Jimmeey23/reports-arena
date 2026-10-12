const {JSDOM}=require('jsdom'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dom=new JSDOM('<title>Review</title><div class="wrap"><h2 id="sales">Sales at a glance</h2><div class="kpis"><div class="kpi"><div class="l">Sales revenue</div><div class="v">₹32,06,431</div></div></div><p>Sales grew 27.4%. Buyer numbers fell.</p><h2 id="next">Next steps</h2></div>',{url:'file:///report.html',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,d=w.document;w.HTMLElement.prototype.scrollIntoView=function(){};w.scrollTo=()=>{};
d.querySelector('#next').getBoundingClientRect=()=>({top:1000});
for(const file of ['report-tools.js','presenter.js','talking-points.js'])w.eval(fs.readFileSync(path.join(__dirname,'../static',file),'utf8'));
w.P57Speaker.notes();
const note=d.querySelector('#p57-speaker-notes');assert.match(note.value,/Sales revenue: ₹32,06,431/);assert.match(note.value,/Sales grew 27.4%/);assert.ok(w.P57Reader.speakerPoints(d.querySelector('h2')).length<=4);assert.ok(d.querySelector('.p57-talk-list strong'));
note.value='My private cue';note.dispatchEvent(new w.Event('input'));w.P57Speaker.notes();assert.equal(note.value,'My private cue');
w.dispatchEvent(new w.Event('pagehide'));w.close();console.log('Passed: source-backed speaker defaults, scannable points, four-cue limit, custom note preservation.');
