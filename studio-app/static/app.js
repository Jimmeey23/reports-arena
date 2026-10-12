/* Studio Intelligence — client */
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
// A fresh batch per page load; historical exports never enter new calculations.
const UPLOAD_BATCH = Array.from(crypto.getRandomValues(new Uint8Array(16)), b=>b.toString(16).padStart(2,'0')).join('');
const apiFetch = (url, options={}) => fetch(url,{...options,headers:{...options.headers,'X-Upload-Batch':UPLOAD_BATCH}});

const CHAP_ORDER = ['sales','class','instructor','lapse','format','cancels','overview','leads','behaviour'];
const CHAP_NEEDS = {sales:'sales', class:'sessions', instructor:'sessions', lapse:'lapsed',
                    format:'sessions', cancels:'sessions', overview:'sessions',
                    leads:'leads', behaviour:'checkins'};
const KIND_LABEL = {sessions:'Sessions export', checkins:'Check-in ledger (Part 4)', sales:'Raw sales',
                    newmembers:'New members', lapsed:'Membership ledger', leads:'Leads master', payroll:'Payroll'};
const KIND_HELP = {sessions:'classes, capacity, attendance, revenue', checkins:'what members actually did',
                   sales:'transactions, discounts, buyers', newmembers:'first visits, lifetime value',
                   lapsed:'membership life, renewals, churn', leads:'enquiries, trials, conversion',
                   payroll:'teaching cost, new vs retained'};

let STATE = null, SEL = {studio:null, year:null, month:null, chapters:new Set(CHAP_ORDER)},
    RUN = null, CH = 0, VOICES = [], narrating = false, utter = null, seq = 0;

/* ─────────────────────────────────────────── helpers */
function toast(msg, err){
  const t = $('#toast'); t.textContent = msg;
  t.className = 'toast on' + (err ? ' err' : '');
  clearTimeout(t._t); t._t = setTimeout(()=>t.className='toast', 4200);
}
const esc = s => (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function view(v){
  if(v !== 'read') document.body.classList.remove('report-full');
  $$('.view').forEach(s => s.classList.toggle('on', s.id === 'v-' + v));
  $$('#tabs button').forEach(b => b.classList.toggle('on', b.dataset.view === v));
  if (v === 'read'){
    $('#tabRead').disabled = !RUN;
    if (!RUN && STATE && STATE.runs.length) openRun(STATE.runs[0]);   /* never show an empty reader */
  }
}

/* ─────────────────────────────────────────── state */
async function loadState(){
  const r = await apiFetch('/api/state'); STATE = await r.json();
  const n = STATE.sources.length, rows = STATE.sources.reduce((a,s)=>a+s.rows,0);
  $('#brandSub').textContent = n
    ? `${n} files · ${rows.toLocaleString()} rows · ${STATE.studios.length} studios`
    : 'no data loaded yet';
  renderSources(); renderNeeds(); renderStudios(); renderRuns(); renderLibrary();
}

function renderNeeds(){
  const have = new Set(STATE.kinds_present);
  const all = ['sessions','checkins','sales','newmembers','lapsed','leads','payroll'];
  $('#needlist').innerHTML = all.map(k => `
    <li><span class="dot ${have.has(k)?'ok':'no'}"></span>
      <span>${KIND_LABEL[k]}</span>
      <span class="sub">${have.has(k) ? (STATE.sources.find(s=>s.kind===k)?.rows.toLocaleString()+' rows') : KIND_HELP[k]}</span>
    </li>`).join('');
  const missing = all.filter(k => !have.has(k));
  $('#dropMeta').textContent = have.size
    ? `${have.size} of 7 file types recognised${missing.length ? ' — still useful without ' + missing.map(m=>KIND_LABEL[m].split(' ')[0]).join(', ') : ' — the full review is available'}`
    : 'no exports recognised yet';
}

function renderSources(){
  const rows = STATE.sources.map(s => `
    <tr>
      <td>${esc(s.name)}</td>
      <td><span class="tag">${KIND_LABEL[s.kind] || s.kind}</span></td>
      <td>${s.rows.toLocaleString()}</td>
      <td><span class="tag ${s.folder==='uploaded'?'up':'bd'}">${s.folder}</span></td>
      <td style="text-align:right">${s.folder==='uploaded' ? `<button class="rm" data-rm="${esc(s.name)}">remove</button>` : ''}</td>
    </tr>`).join('');
  $('#srcs').innerHTML = rows || `<tr><td colspan="5" class="muted" style="padding:22px 24px">
      No fresh exports uploaded. Choose files to start a new review.</td></tr>`;
  $('#srcCount').textContent = STATE.sources.length ? STATE.sources.length + ' recognised' : '';
  $('#warnbox').innerHTML = (STATE.warnings||[]).map(w => `<div class="note">${esc(w)}</div>`).join('');
  $$('[data-rm]').forEach(b => b.onclick = async () => {
    await apiFetch('/api/remove', {method:'POST', body: JSON.stringify({name: b.dataset.rm})});
    toast('Removed ' + b.dataset.rm); loadState();
  });
}

function renderStudios(){
  const el = $('#studios');
  if (!STATE.studios.length){ el.innerHTML = `<p class="muted">No studio with usable session data yet.</p>`; return; }
  el.innerHTML = STATE.studios.filter(s => s.months.length).map(s => `
    <button class="pick ${SEL.studio===s.name?'on':''}" data-studio="${esc(s.name)}">
      <span class="pn">${esc(s.name)}</span>
      <span class="pm">${s.months.length} months · ${s.rows.toLocaleString()} rows</span>
    </button>`).join('');
  $$('[data-studio]').forEach(b => b.onclick = () => {
    SEL.studio = b.dataset.studio;
    const st = STATE.studios.find(s => s.name === SEL.studio);
    const last = st.months[st.months.length-1];
    SEL.year = last.year; SEL.month = last.month;
    renderStudios(); renderMonths(); renderChapters(); ready();
  });
}

function renderMonths(){
  const st = STATE.studios.find(s => s.name === SEL.studio);
  const el = $('#months');
  if (!st){ el.innerHTML = ''; $('#periodHint').textContent = 'pick a studio first'; return; }
  const ms = [...st.months].reverse();
  el.innerHTML = ms.map(m => `
    <button class="pick ${SEL.year===m.year&&SEL.month===m.month?'on':''}"
            data-m="${m.year}-${m.month}">
      <span class="pn">${m.label}</span>
      <span class="pm">${m.sessions} classes recorded</span>
    </button>`).join('');
  $$('[data-m]').forEach(b => b.onclick = () => {
    const [y,m] = b.dataset.m.split('-').map(Number);
    SEL.year = y; SEL.month = m; renderMonths(); ready();
  });
  $('#periodHint').textContent = `${st.months.length} months with session data`;
}

function renderChapters(){
  const have = new Set(STATE.kinds_present);
  const titles = {sales:'Sales performance', class:'Class performance', instructor:'Instructor performance',
    lapse:'Memberships lapsed and churned', format:'Format comparisons', cancels:'Late cancellations and discounts',
    overview:'Studio overview and intelligence', leads:'Lead performance and insights',
    behaviour:'Member behaviour and patterns'};
  $('#chapters').innerHTML = CHAP_ORDER.map((c,i) => {
    const ok = have.has(CHAP_NEEDS[c]);
    return `<button class="pick ${SEL.chapters.has(c)&&ok?'on':''}" data-ch="${c}" ${ok?'':'disabled style="opacity:.45"'}>
      <span class="ckb"></span>
      <span><span class="pn">${String(i+1).padStart(2,'0')} &nbsp;${titles[c]}</span>
      <span class="pm">${ok ? 'ready' : 'needs the ' + KIND_LABEL[CHAP_NEEDS[c]]}</span></span></button>`;
  }).join('');
  $$('[data-ch]').forEach(b => b.onclick = () => {
    const c = b.dataset.ch;
    SEL.chapters.has(c) ? SEL.chapters.delete(c) : SEL.chapters.add(c);
    renderChapters(); ready();
  });
}

function ready(){
  const ok = SEL.studio && SEL.year && SEL.chapters.size;
  $('#btnGen').disabled = !ok;
  $('#genInfo').textContent = !SEL.studio ? 'Choose a studio and a month.'
    : !SEL.chapters.size ? 'Choose at least one chapter.'
    : `${SEL.chapters.size} chapter${SEL.chapters.size>1?'s':''} · ${SEL.studio} · ${monthName(SEL.month)} ${SEL.year}`;
}
const monthName = m => ['January','February','March','April','May','June','July','August','September','October','November','December'][m-1];

/* ─────────────────────────────────────────── upload */
function wireUpload(){
  const drop = $('#drop'), input = $('#file');
  input.onclick = e => e.stopPropagation();
  drop.onclick = e => {
    if (!e.target.closest('input, label')) input.click();
  };
  input.onchange = () => {
    const files = [...input.files];
    input.value = '';
    send(files);
  };
  ['dragenter','dragover'].forEach(ev => drop.addEventListener(ev, e => {
    e.preventDefault(); drop.classList.add('over');
  }));
  ['dragleave','drop'].forEach(ev => drop.addEventListener(ev, e => {
    e.preventDefault(); drop.classList.remove('over');
  }));
  drop.addEventListener('drop', e => send(e.dataTransfer.files));
  $('#btnReload').onclick = async () => {
    toast('Re-scanning…');
    const r = await apiFetch('/api/reload', {method:'POST'});
    const d = await r.json(); STATE = d.state; renderAll(); toast('Re-scanned');
  };
}
async function send(files){
  if (!files || !files.length) return;
  const fd = new FormData();
  [...files].forEach(f => fd.append('files', f, f.name));
  $('#dropMeta').textContent = `uploading ${files.length} file${files.length>1?'s':''}…`;
  try{
    const r = await apiFetch('/api/upload', {method:'POST', body:fd});
    const d = await r.json();
    if (!r.ok || d.error) throw new Error(d.error || `Server returned ${r.status}`);
    STATE = d.state; renderAll();
    const good = d.saved.map(s => s.name).join(', ');
    $('#dropMeta').textContent = d.saved.length
      ? `Uploaded ${d.saved.length}: ${good}. Latest uploads replace older files of the same type.`
      : 'No files loaded.';
    toast(d.saved.length ? `Loaded ${d.saved.length}: ${good}` : 'Nothing recognised in those files', !d.saved.length);
    if (d.skipped.length) {
      $('#dropMeta').textContent += ' ' + d.skipped.map(([name, reason]) => `${name}: ${reason}`).join(' · ');
    }
  }catch(e){
    $('#dropMeta').textContent = 'Upload failed: ' + e.message;
    toast('Upload failed: ' + e.message, true);
  }
}
function renderAll(){ renderSources(); renderNeeds(); renderStudios(); renderMonths(); renderChapters(); renderRuns(); renderLibrary(); }

/* ─────────────────────────────────────────── generate */
async function generate(){
  $('#prog').classList.add('on'); $('#btnGen').disabled = true;
  $('#plog').textContent = ''; $('#genInfo').textContent = 'Working…';
  const body = {studio:SEL.studio, year:SEL.year, month:SEL.month, chapters:[...SEL.chapters],
                llm:{key:$('#llmKey').value.trim(), model:$('#llmModel').value}};
  const r = await apiFetch('/api/generate', {method:'POST', body: JSON.stringify(body)});
  const result = await r.json();
  if(!r.ok || result.error){toast(result.error || 'Could not start review', true);ready();$('#prog').classList.remove('on');return;}
  const {job} = result;
  const tick = setInterval(async () => {
    const j = await (await apiFetch('/api/job/'+job)).json();
    $('.bar i').style.width = (j.pct||2) + '%';
    if (j.log) $('#plog').textContent = j.log.slice(-9).join('\n');
    if (j.state === 'done'){
      clearInterval(tick);
      $('#genInfo').textContent = `Built in ${j.seconds}s`;
      await loadState();
      const run = STATE.runs.find(x => x.id === j.run);
      openRun(run);
      toast('Review ready — ' + run.chapters.length + ' chapters');
    } else if (j.state === 'error'){
      clearInterval(tick); toast('Build failed: ' + j.message, true);
      $('#genInfo').textContent = 'Failed — ' + j.message;
      $('#btnGen').disabled = false;
    } else { $('#genInfo').textContent = j.message; }
  }, 700);
}

/* ─────────────────────────────────────────── reader */
function renderRuns(){
  const el = $('#runs');
  if (!STATE.runs.length){ el.innerHTML = `<span class="muted" style="font-size:13px">No review built yet.</span>`; return; }
  el.innerHTML = `<span class="lbl">Reviews</span>` + STATE.runs.map(r =>
    `<button class="runchip ${RUN&&RUN.id===r.id?'on':''}" data-run="${r.id}">
       ${esc(r.label||'')} · ${esc((r.studio||'').replace('Supreme HQ, ',''))} · ${r.chapters.length} ch</button>`).join('');
  $$('[data-run]').forEach(b => b.onclick = () => openRun(STATE.runs.find(x => x.id === b.dataset.run)));
}

function openRun(run){
  if (!run) return;
  RUN = run; CH = 0;
  $('#runLabel').textContent = run.label || '';
  $('#runSub').textContent = `${run.studio} · built ${run.built || ''}`;
  $('#btnDownload').disabled = false;
  $('#chlist').innerHTML = run.chapters.map((c,i) => `
    <li data-i="${i}" class="${i===0?'on':''}">
      <span class="n">${String(c.n||i+1).padStart(2,'0')}</span>
      <span><span class="t">${esc(c.title)}</span><span class="s">${esc(c.subtitle||'')}</span></span>
    </li>`).join('');
  $$('#chlist li').forEach(li => li.onclick = () => { stopNarration(); show(+li.dataset.i); });
  view('read');
  document.body.classList.add('report-full');
  $('#stage').src = `/api/report/${run.id}/report`;
  loadVoices();
}

function show(i){
  if (!RUN || !RUN.chapters[i]) return;
  if (!narrating) stopNarration();
  CH = i;
  const c = RUN.chapters[i];
  $('#btnPrev').disabled = i === 0;
  $('#btnNext').disabled = i === RUN.chapters.length - 1;
  $$('#chlist li').forEach((l,k) => l.classList.toggle('on', k===i));
  $('#cNum').textContent = String(c.n || i+1).padStart(2,'0');
  $('#cTitle').textContent = c.title;
  $('#cSub').textContent = c.subtitle || '';
  $('#stage').src = `/api/report/${RUN.id}/${c.id}?t=${Date.now()}`;
  $('#sumText').textContent = c.summary_ai || c.summary || '';
  $('#aiTag').textContent = c.summary_ai ? 'rewritten by the model' : 'written from the data';
  $('#facts').innerHTML = (c.facts||[]).map(f => `<li>${esc(f)}</li>`).join('');
  $('#sumText').style.display = (c.summary_ai||c.summary) ? '' : 'none';
}

/* ─────────────────────────────────────────── narration */
function loadVoices(){
  if (!('speechSynthesis' in window)) return;
  const fill = () => {
    VOICES = speechSynthesis.getVoices();
    $('#voice').innerHTML = VOICES
      .filter(v => v.lang && v.lang.toLowerCase().startsWith('en'))
      .map(v => `<option value="${v.name}">${v.name} — ${v.lang}</option>`).join('')
      || '<option>system default</option>';
  };
  fill(); speechSynthesis.onvoiceschanged = fill;
}

function speak(text, onEnd){
  if (!('speechSynthesis' in window)) return toast('This browser cannot speak text', true);
  const u = new SpeechSynthesisUtterance(text);
  const name = $('#voice').value;
  const v = VOICES.find(x => x.name === name); if (v) u.voice = v;
  u.rate = parseFloat($('#rate').value); u.pitch = 1;
  u.onend = () => { if (narrating) onEnd && onEnd(); };
  utter = u; speechSynthesis.speak(u);
}
function stopNarration(){
  narrating = false; seq++;
  $('#btnPause').textContent = 'Pause';
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  $('#narrbar').classList.remove('on');
  $('#narrTxt').textContent = 'Listen';
  $('#narrStatus').textContent = 'Reading…';
}
/* read one chapter, or walk the whole review */
async function narrate(whole){
  if (narrating) return stopNarration();
  const order = whole ? RUN.chapters.map((_,i)=>i) : [CH];
  narrating = true; const my = ++seq;
  $('#narrbar').classList.add('on'); $('#narrTxt').textContent = 'Stop';
  const intro = whole ? `The ${RUN.label} performance review for ${RUN.studio}.` : '';
  if (whole && intro) { $('#narrStatus').textContent = 'Introduction'; await spoke(intro, my); if (!narrating||my!==seq) return; }
  for (const idx of order){
    if (!narrating || my !== seq) return;
    const c = RUN.chapters[idx];
    if (whole){ show(idx); await sleep(650); }
    $('#narrStatus').textContent = 'Chapter ' + (c.n||idx+1) + ' — ' + c.title;
    highlight(c.narration);
    await spoke(c.narration, my);
    if (!narrating || my !== seq) return;
    if (c.summary_ai && whole){ $('#narrStatus').textContent = 'Summary'; await spoke(c.summary_ai, my); }
  }
  if (my === seq) stopNarration();
}
function spoke(text, my){
  return new Promise(res => speak(text, () => res()));
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* scroll the chapter to whatever is being read */
function highlight(text){
  try{
    const d = $('#stage').contentDocument; if (!d) return;
    d.querySelectorAll('.si-narr').forEach(e => e.classList.remove('si-narr'));
    const bits = (text||'').split(/[.;]/).map(s => s.trim()).filter(s => s.length > 26);
    let first = null;
    bits.forEach(b => {
      const probe = b.slice(0, 34).toLowerCase();
      const walker = d.createTreeWalker(d.body, NodeFilter.SHOW_TEXT);
      let n;
      while ((n = walker.nextNode())){
        if (n.parentElement.closest('svg')) continue;
        if (n.nodeValue.toLowerCase().replace(/\s+/g,' ').includes(probe)){
          n.parentElement.classList.add('si-narr');
          if (!first) first = n.parentElement;
          break;
        }
      }
    });
    if (first) first.scrollIntoView({behavior:'smooth', block:'center'});
    if (!d.getElementById('si-style')){
      const st = d.createElement('style'); st.id = 'si-style';
      st.textContent = '.si-narr{background:linear-gradient(transparent 62%, #E2C3AC 62%);transition:background .4s}';
      d.head.appendChild(st);
    }
  }catch(e){}
}

/* ─────────────────────────────────────────── boot */
function wire(){
  wireUpload();
  $$('#tabs button').forEach(b => b.onclick = () => view(b.dataset.view));
  $('#btnGen').onclick = generate;
  $('#btnPrev').onclick = () => { stopNarration(); show(CH - 1); };
  $('#btnNext').onclick = () => { stopNarration(); show(CH + 1); };
  $('#btnFocus').onclick = () => { const on = $('.reader').classList.toggle('focused'); $('#btnFocus').setAttribute('aria-pressed', String(on)); };
  $('#btnPause').onclick = () => { if (!('speechSynthesis' in window)) return; if (speechSynthesis.paused) { speechSynthesis.resume(); $('#btnPause').textContent = 'Pause'; } else { speechSynthesis.pause(); $('#btnPause').textContent = 'Resume'; } }; 
  $('#allCh').onclick = () => { CHAP_ORDER.forEach(c => SEL.chapters.add(c)); renderChapters(); ready(); };
  $('#noneCh').onclick = () => { SEL.chapters.clear(); renderChapters(); ready(); };
  $('#btnNarr').onclick = () => narrate(false);
  $('#btnWhole').onclick = () => { if (narrating) return stopNarration(); narrate(true); };
  $('#btnStop').onclick = stopNarration;
  $('#rate').oninput = e => { $('#rateTxt').textContent = (+e.target.value).toFixed(1) + '×'; };
  $('#btnSummary').onclick = () => $('#summary').classList.toggle('on');
  $('#btnPrint').onclick = () => { try{ $('#stage').contentWindow.print(); }catch(e){} };
  $('#btnFull').onclick = () => { if (RUN) window.open(`/api/report/${RUN.id}/full`, '_blank'); };
  $('#btnDownload').onclick = () => { if (RUN) location.href = `/api/download?run=${RUN.id}`; };
  view('upload');
  loadState();
}
wire();

function renderLibrary(){
  const el=$('#savedReports');
  if(!el||!STATE)return;
  el.replaceChildren();
  if(!STATE.runs.length){el.textContent='Your generated reviews will appear here.';return;}
  STATE.runs.forEach(run=>{const b=document.createElement('button');b.className='saved-review';
    const title=document.createElement('strong');title.textContent=run.label+' · '+run.studio;
    const detail=document.createElement('span');detail.textContent=run.chapters.length+' chapters · '+(run.built||'Saved review');
    b.append(title,detail);b.onclick=()=>openRun(run);el.append(b);});
}
