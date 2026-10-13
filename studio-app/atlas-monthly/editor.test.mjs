import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
const staticDir=new URL('../static/',import.meta.url);
const fixture=`<html><head><title>Editor test</title><style>
.kpis{display:grid!important;padding:40px}.chart{display:block!important;min-height:400px}
</style><style>${readFileSync(new URL('report-edit.css',staticDir),'utf8')}</style></head><body>
<header><div class="inner"><h1>Report title</h1></div></header>
<div class="wrap"><nav class="toc"><ul><li><a href="#sales">Sales</a></li></ul></nav>
<section id="sales"><h2>Sales</h2><div class="kpis">
<div class="kpi"><div class="l">Revenue</div><div class="v">₹100</div><div class="d">This month</div></div>
<div class="kpi"><div class="l">Visits</div><div class="v">10</div></div></div>
<div class="call"><h4>Insight</h4><p id="narrative">Member visits increased.</p></div>
<figure class="chart"><svg><rect width="100" height="100"/></svg><figcaption>Visits</figcaption></figure>
<div class="rt-table-wrap"><div class="rt-table-tools">Filter Export CSV</div><table><thead><tr><th>Measure</th></tr></thead><tbody><tr><td>Attendance</td></tr></tbody></table></div>
</section></div></body></html>`;
const model=readFileSync(new URL('report-edit-model.js',staticDir),'utf8');
const editor=readFileSync(new URL('report-edit.js',staticDir),'utf8');
let server=[];let failPost=false;
async function open({offline=false,edits=server}={}){
 const dom=new JSDOM(fixture,{url:offline?'file:///report.html':'http://localhost/api/report/test/full',runScripts:'outside-only'});
 const w=dom.window,d=w.document;
 const make=(tag,text,cls)=>{const el=d.createElement(tag);if(text)el.textContent=text;if(cls)el.className=cls;return el;};
 const bar=make('nav');d.body.prepend(bar);
 w.P57Reader={make,bar,button:(text,fn,parent=bar)=>{const b=make('button',text);b.onclick=fn;parent.append(b);return b;},dialog:{close(){}},openDialog:(title,form)=>d.body.append(form)};
 if(offline){const s=make('script');s.id='p57-structural-edits';s.type='application/json';s.textContent=JSON.stringify(edits);d.head.append(s);}
 w.fetch=async(url,init)=>{if(init?.method==='POST'){
   if(failPost)throw Error('network unavailable');const row=JSON.parse(init.body);
   if(row.op==='restore')server=server.filter(e=>!(e.el_id===row.el_id&&e.op==='delete'));
   else{server=server.filter(e=>!(e.el_id===row.el_id&&e.op===row.op));server.push(row);}
 }return {ok:true,json:async()=>({edits:server})};};
 w.eval(model);w.eval(editor);await new Promise(resolve=>w.setTimeout(resolve,0));
 return {dom,w,d,edit:w.P57Edit};
}
const {dom,w,d,edit}=await open();
const cards=d.querySelectorAll('.kpi'),kpis=d.querySelector('.kpis');
await edit.removeElement(cards[0].querySelector('.v'));
assert.equal(w.getComputedStyle(cards[0]).display,'none','Deleting the value collapses the orphan metric card');
assert.notEqual(w.getComputedStyle(kpis).display,'none','The remaining card stays visible');
assert.equal(d.querySelectorAll('.p57-block-deleted').length,0,'No in-document deletion placeholders');
await edit.removeElement(cards[1]);
assert.equal(w.getComputedStyle(kpis).display,'none','Deleting the final card collapses its grid');
await edit.undo();
assert.notEqual(w.getComputedStyle(kpis).display,'none');
assert.notEqual(w.getComputedStyle(cards[1]).display,'none');
await edit.redo();assert.equal(w.getComputedStyle(kpis).display,'none');
const p=d.getElementById('narrative'),call=p.parentElement;
await edit.saveElement(p,'<br>');
assert.equal(w.getComputedStyle(call).display,'none','Clearing narrative removes its now empty callout');
await edit.undo();assert.notEqual(w.getComputedStyle(call).display,'none');assert.ok(p.textContent.includes('increased'));
await edit.removeElement(d.querySelector('.chart svg'));
assert.equal(w.getComputedStyle(d.querySelector('.chart')).display,'none','Removing a chart removes its caption-only wrapper');
await edit.removeElement(d.querySelector('tbody tr'));
assert.equal(w.getComputedStyle(d.querySelector('.rt-table-wrap')).display,'none','The empty table and its filter toolbar collapse');
// Actual inline controls, not just the public editor methods.
edit.setLayout(true);p.dispatchEvent(new w.MouseEvent('mouseover',{bubbles:true}));
const toolbar=d.querySelector('[aria-label="Report component editing"]');
assert.ok(toolbar.querySelector('[aria-label="Editing target"]'));
[...toolbar.querySelectorAll('button')].find(b=>b.textContent==='Edit text').click();
p.innerHTML='';
[...d.querySelectorAll('.p57-block-tools button')].find(b=>b.textContent==='Save').click();
await new Promise(resolve=>w.setTimeout(resolve,0));
assert.equal(w.getComputedStyle(call).display,'none');
await edit.undo();assert.notEqual(w.getComputedStyle(call).display,'none');
// Persisted changes survive reload and standalone export without empty shells.
const reloaded=await open();
assert.equal(reloaded.w.getComputedStyle(reloaded.d.querySelector('.kpis')).display,'none');
assert.equal(reloaded.w.getComputedStyle(reloaded.d.querySelector('.chart')).display,'none');
reloaded.edit.setLayout(true);
[...reloaded.d.querySelectorAll('button')].find(b=>b.textContent==='Restore removed components').click();
[...reloaded.d.querySelectorAll('.p57-component-inspector button')].find(b=>b.textContent==='Restore').click();
await new Promise(resolve=>reloaded.w.setTimeout(resolve,0));
assert.notEqual(reloaded.w.getComputedStyle(reloaded.d.querySelector('.kpi')).display,'none','Persisted removals can be restored after reload');
await reloaded.edit.undo();assert.equal(reloaded.w.getComputedStyle(reloaded.d.querySelector('.kpi')).display,'none');
const offline=await open({offline:true});
assert.equal(offline.w.getComputedStyle(offline.d.querySelector('.rt-table-wrap')).display,'none');
assert.equal(offline.d.querySelectorAll('.p57-block-deleted').length,0);
// Undo must cancel a failed delete save so Save all cannot delete it again.
const target=d.querySelector('.call');failPost=true;await edit.removeElement(target);
failPost=false;await edit.undo();
assert.deepEqual(JSON.parse(w.localStorage.getItem('p57-layout-edits:test:pending')),[]);
assert.notEqual(w.getComputedStyle(target).display,'none');
const chapter=d.querySelector('section');await edit.removeElement(chapter);
assert.equal(d.querySelector('.toc li').hidden,true);await edit.undo();assert.equal(d.querySelector('.toc li').hidden,false);
// Appearance-only editing also participates in Undo/Redo.
p.dispatchEvent(new w.MouseEvent('mouseover',{bubbles:true}));
[...d.querySelectorAll('.p57-block-tools button')].find(b=>b.textContent==='Design').click();
const inspector=d.querySelector('.p57-component-inspector');
inspector.querySelector('[aria-label="Spacing"]').value='24px';
[...inspector.querySelectorAll('button')].find(b=>b.textContent==='Save component').click();
await new Promise(resolve=>w.setTimeout(resolve,0));assert.equal(p.style.padding,'24px');
await edit.undo();assert.equal(p.style.padding,'');await edit.redo();assert.equal(p.style.padding,'24px');
await edit.insertAfter(p,'<p>Added narrative</p>');await edit.commitEdit();
const inserted=d.querySelector('.p57-block-inserted');assert.ok(inserted);
await edit.undo();assert.equal(w.getComputedStyle(inserted).display,'none');
await edit.redo();assert.notEqual(w.getComputedStyle(inserted).display,'none');
await edit.removeElement(d.querySelector('header .inner'));
assert.equal(w.getComputedStyle(d.querySelector('header')).display,'none','Removing cover content collapses the cover shell');
const exportedCover=await open({offline:true});
assert.equal(exportedCover.w.getComputedStyle(exportedCover.d.querySelector('header')).display,'none','Cover edit IDs survive exported filenames');
const filtering=new JSDOM(fixture,{runScripts:'outside-only'});
filtering.window.eval(model);filtering.window.document.querySelector('tbody tr').hidden=true;
filtering.window.P57EditModel.cleanup();
assert.notEqual(filtering.window.getComputedStyle(filtering.window.document.querySelector('.rt-table-wrap')).display,'none','Table search filtering is independent of structural removal');
console.log('Editor: deletion, container cleanup, inline Save, Undo/Redo, persistence, offline export, failed-save Undo and navigation passed.');
dom.window.close();reloaded.dom.window.close();offline.dom.window.close();filtering.window.close();exportedCover.dom.window.close();
