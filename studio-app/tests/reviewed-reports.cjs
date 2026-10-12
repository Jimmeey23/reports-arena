const {JSDOM}=require('jsdom'),fs=require('fs'),assert=require('node:assert/strict'),path=require('path');
for(const rid of ['20261011-232828-eb72','20261012-180820-period']){
 const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'../runs',rid,'report.html'),'utf8'),{url:'http://localhost:8017/api/report/'+rid+'/report',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,d=w.document;w.fetch=async()=>({ok:true,json:async()=>({})});w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};
 const ids=[...d.querySelectorAll('[id]')].map(e=>e.id);assert.equal(ids.length,new Set(ids).size);
 const cues=JSON.parse(d.querySelector('#p57-generated-speaker-notes').textContent);assert.ok(Object.keys(cues).length>100);
 for(const points of Object.values(cues))assert.ok(points.length<=4);
 for(const file of ['report-tools.js','presenter.js','talking-points.js'])w.eval(fs.readFileSync(path.join(__dirname,'../static',file),'utf8'));
 const heading=d.querySelector('#executive-summary');assert.deepEqual([...w.P57Reader.speakerPoints(heading)],cues['executive-summary']);
 w.P57Speaker.notes();const note=d.querySelector('#p57-speaker-notes');assert.ok(note);note.value='Keep my own cue';note.dispatchEvent(new w.Event('input'));w.P57Speaker.notes();assert.equal(note.value,'Keep my own cue');
 assert.doesNotMatch(d.body.textContent,/churning more slowly|was taken|₹nan|nan%/);w.dispatchEvent(new w.Event('pagehide'));w.close();
 console.log('Passed reviewed report:',rid,'unique anchors, generated cues, private edits, cleaned copy');
}
