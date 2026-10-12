const {JSDOM}=require('jsdom'),fs=require('fs'),assert=require('node:assert/strict'),path=require('path');
const code=fs.readFileSync(path.join(__dirname,'../static/report-edit.js'),'utf8');
let rows=[],fail=false;
function reader(){
 const dom=new JSDOM('<html><head><title>Review</title></head><body><header><h1>Cover</h1></header><div class="wrap"><section id="sales"><div class="p57-chapter-hero"><h2>Sales</h2></div><p>Original</p><table><tbody><tr><td>123</td></tr></tbody></table></section></div></body></html>',{url:'http://localhost/api/report/test/report',runScripts:'outside-only'});
 const w=dom.window,d=w.document;
 const make=(tag,text,cls)=>{let e=d.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;};
 const bar=make('nav');d.body.append(bar);
 w.P57Reader={make,bar,button(text,fn){const b=make('button',text);b.onclick=fn;bar.append(b);return b;}};
 w.fetch=async(url,opt)=>{if(opt){if(fail)return{ok:false};let row=JSON.parse(opt.body);rows=rows.filter(e=>!(e.el_id===row.el_id&&e.op===row.op));rows.push(row);return{ok:true,json:async()=>({edits:rows})};}return{ok:true,json:async()=>({edits:rows})};};
 w.eval(code);return dom;
}
const tick=()=>new Promise(r=>setTimeout(r,0));
(async()=>{
 let dom=reader(),w=dom.window,d=w.document;await tick();
 assert(d.querySelector('header h1').closest('[data-el]'));assert(d.querySelector('.p57-chapter-hero').dataset.el);assert(d.querySelector('td').dataset.el);
 let cell=d.querySelector('td');cell.innerHTML='456';await w.P57Edit.saveElement(cell,cell.innerHTML);
 const anchor=d.querySelector('section>p');await w.P57Edit.insertAfter(anchor,'<p>First</p>');await w.P57Edit.commitEdit();await w.P57Edit.insertAfter(anchor,'<p>Second</p>');await w.P57Edit.commitEdit();
 let inserted=d.querySelector('.p57-block-inserted');inserted.innerHTML='<p>Edited insertion</p>';await w.P57Edit.saveElement(inserted,inserted.innerHTML);
 assert.equal(rows.filter(e=>e.op==='insert').length,2);rows.push({el_id:cell.dataset.el,op:'style',html:JSON.stringify({'text-align':'right','font-size':'20px'})});
 dom.window.close();dom=reader();w=dom.window;d=w.document;await tick();
 assert.equal(d.querySelector('td').textContent,'456');assert.equal(d.querySelector('td').style.textAlign,'right');assert.equal(d.querySelector('td').style.fontSize,'20px');assert.equal(d.querySelectorAll('.p57-block-inserted').length,2);assert.match(d.querySelector('.wrap').textContent,/Edited insertion/);
 w.P57Edit.setLayout(true);d.querySelector('td').dispatchEvent(new w.MouseEvent('dblclick',{bubbles:true}));assert.equal(d.querySelector('td').getAttribute('contenteditable'),'true');d.querySelector('td').textContent='789';await w.P57Edit.commitEdit();assert.equal(rows.find(e=>e.el_id===cell.dataset.el&&e.op==='set').html,'789');
 fail=true;cell=d.querySelector('td');cell.innerHTML='999';await w.P57Edit.saveElement(cell,cell.innerHTML);assert.match(d.querySelector('.p57-edit-status').textContent,/failed/);assert(w.localStorage.getItem('p57-layout-edits:test:pending').includes('999'));
 fail=false;[...d.querySelectorAll('button')].find(e=>e.textContent==='Save all changes').click();await tick();assert.equal(rows.find(e=>e.el_id===cell.dataset.el&&e.op==='set').html,'999');
 dom.window.close();console.log('Passed: cover, heroes, table cells, inline save, multiple insertions, reload persistence, edited insertion replay, failed-save recovery.');
})().catch(e=>{console.error(e);process.exit(1);});
