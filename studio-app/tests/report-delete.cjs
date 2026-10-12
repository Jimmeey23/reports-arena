const {JSDOM}=require('jsdom'),fs=require('fs'),assert=require('node:assert/strict');
(async()=>{
const dom=new JSDOM(fs.readFileSync('studio-app/static/index.html','utf8'),{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true}),w=dom.window,d=w.document;
w.scrollTo=()=>{};w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new w.Event('close'))};
const chapter={id:'sales',n:1,title:'Sales',sections:[]};const a={id:'a',studio:'Bandra',label:'September 2026',chapters:[chapter]},b={id:'b',studio:'Kemps Corner',label:'September 2026',chapters:[chapter]};
let state={sources:[],studios:[],runs:[a,b],warnings:[],kinds_present:[]},fail=false,calls=[];
w.fetch=async(url,options={})=>{calls.push({url,options});if(url==='/api/reports/delete'){if(fail)return {status:500,ok:false,json:async()=>({error:'Database unavailable'})};const body=JSON.parse(options.body);assert.equal(body.confirmation,body.run);state={...state,runs:state.runs.filter(r=>r.id!==body.run)};return {status:200,ok:true,json:async()=>({deleted:body.run})};}return {status:200,ok:true,json:async()=>state};};
w.eval(fs.readFileSync('studio-app/static/app.js','utf8'));await new Promise(r=>setTimeout(r,10));
const pause=()=>new Promise(r=>setTimeout(r,10));
const remove=()=>d.querySelector('#savedReports .report-delete').click();
remove();assert.match(d.querySelector('dialog').textContent,/September 2026 · Bandra/);d.querySelector('dialog .ghost').click();assert.equal(calls.filter(c=>c.url==='/api/reports/delete').length,0);
w.P57Workspace.open(a);w.P57Workspace.open(b);w.P57Workspace.open(a);
fail=true;remove();d.querySelector('.report-delete-confirm').click();await pause();assert.match(d.querySelector('.report-delete-error').textContent,/Database unavailable/);assert.equal(d.querySelectorAll('.saved-report-row').length,2);assert.equal(d.querySelector('.report-delete-confirm').disabled,false);
fail=false;d.querySelector('.report-delete-confirm').click();await pause();assert.equal(d.querySelectorAll('.saved-report-row').length,1);assert.equal(w.P57Workspace.entries.length,1);assert.match(d.querySelector('#stage').src,/\/b\/report$/);
remove();d.querySelector('.report-delete-confirm').click();await pause();assert.equal(w.P57Workspace.entries.length,0);assert.equal(d.querySelector('#stage').hasAttribute('src'),false);assert.equal(d.querySelector('#tabRead').disabled,true);assert.match(d.querySelector('#savedReports').textContent,/generated reviews will appear/);assert.deepEqual(JSON.parse(w.localStorage.getItem('p57-studio-workspace')).reports,[]);
w.close();console.log('Passed: delete confirmation and cancel, error retry, active report switch, final report removal and empty state.');
})().catch(e=>{console.error(e);process.exit(1)});
