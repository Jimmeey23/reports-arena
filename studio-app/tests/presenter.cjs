const {JSDOM}=require('jsdom'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const html='<html><head><title>Report</title></head><body><header><h1>Studio review</h1></header><div class="wrap"><h2 id="overview">Overview</h2><p>Source-backed conclusion.</p><h2 id="actions">Actions</h2><p>Follow up with <strong>members</strong>.</p></div></body></html>';
(async()=>{
const dom=new JSDOM(html,{url:'http://localhost/api/report/test/report',runScripts:'outside-only',pretendToBeVisual:true});const w=dom.window,d=w.document;
w.HTMLElement.prototype.scrollIntoView=function(){};w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;};w.scrollTo=()=>{};
let stored={notes:{overview:'Restored private note'},edits:{'text-1':'Persisted conclusion.'},preferences:{theme:'warm'}},requests=[];
w.fetch=async(url,o={})=>{requests.push({url,options:o});let data={};if(url.startsWith('/api/workspace')&&o.method!=='POST')data=stored;else if(url==='/api/workspace'){const {patch}=JSON.parse(o.body);for(const k in patch)stored[k]={...stored[k],...patch[k]};data=stored;}else if(url==='/api/meetings')data={code:'ABCD2345',report:'test/report',view:{section:'overview',scroll:0},active:true,is_host:true,participants:1};else if(url.startsWith('/api/meetings/'))data={code:'ABCD2345',report:'test/report',view:{section:'actions',scroll:.5},active:true,is_host:true,participants:2};return{ok:true,json:async()=>data};};
for(const name of ['report-tools.js','presenter.js'])w.eval(fs.readFileSync(path.join(__dirname,'../static',name),'utf8'));
await new Promise(r=>setTimeout(r,20));
const button=t=>[...d.querySelectorAll('button')].find(b=>b.textContent===t);
assert.equal(d.querySelector('.p57-toolkit').hidden,true);assert.equal(d.querySelector('.p57-speaker').hidden,true);assert.equal(d.querySelector('.wrap p').textContent,'Persisted conclusion.');assert.equal(d.documentElement.dataset.theme,'warm');assert.equal(d.querySelector('.wrap p strong').textContent,'members');
d.querySelector('.p57-tool-trigger').click();assert.equal(d.querySelector('.p57-toolkit').hidden,false);
button('Speaker notes / annotations').click();assert.equal(d.querySelector('.p57-speaker').hidden,false);assert.equal(d.querySelector('#p57-speaker-notes').value,'Restored private note');
const note=d.querySelector('#p57-speaker-notes');note.value='Updated script';note.dispatchEvent(new w.Event('input'));
button('Start').click();assert.equal(d.querySelector('.p57-prompt').textContent,'Updated script');button('Pause').click();button('Reset').click();assert.equal(d.querySelector('.p57-prompt').scrollTop,0);
button('Mirror').click();assert.equal(d.querySelector('.p57-prompt').classList.contains('mirrored'),true);
const annotation=d.querySelector('#p57-annotation');annotation.value='Discuss this with attendees';annotation.dispatchEvent(new w.Event('input'));assert.match(d.querySelector('.p57-annotation-callout').textContent,/attendees/);
button('Edit report text').click();const paragraph=d.querySelector('.wrap p');assert.equal(paragraph.contentEditable,'true');paragraph.textContent='Saved revision';paragraph.dispatchEvent(new w.Event('input'));
await new Promise(r=>setTimeout(r,450));assert.equal(stored.edits['text-1'],'Saved revision');assert.equal(stored.notes.overview,'Updated script');assert.equal(stored.annotations.overview,'Discuss this with attendees');
await button('Host this report').onclick();await new Promise(r=>setTimeout(r,20));assert.match(d.querySelector('.p57-session-badge').textContent,/ABCD2345/);assert.match(d.querySelector('.p57-session p').textContent,/2 connected/);
assert.equal(requests.some(r=>r.url==='/api/meetings'),true);
// No focus inside navigation: it closes after five seconds of inactivity.
d.querySelector('.p57-nav-trigger').click();if(d.querySelector('.p57-navigation').hidden)d.querySelector('.p57-nav-trigger').click();
await new Promise(r=>setTimeout(r,5200));assert.equal(d.querySelector('.p57-navigation').hidden,true);
w.dispatchEvent(new w.Event('pagehide'));dom.window.close();console.log('Passed: collapsed floating toolkit, private speaker drawer, restored edits/theme, notes save, teleprompter start/pause/reset/mirror, annotation save, host controls, auto-collapse.');
})().catch(e=>{console.error(e);process.exit(1);});
