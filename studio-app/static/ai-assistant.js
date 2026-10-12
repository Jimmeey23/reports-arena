/* Floating AI assistant: a chat agent connected to the run's computed
metrics (via /api/ai/*), plus a speaker-notes launcher on the report
interface. Answers come from the deterministic metrics engine first; a
configured model only extends coverage - numbers are always grounded. */
(() => {
'use strict';
const R = window.P57Reader; if(!R) return;
const {make} = R;
const route = location.pathname.match(/^\/api\/report\/([^/]+)/);
const run = route ? route[1] : null;
const online = /^https?:$/.test(location.protocol) && !!run;
if(!online) return;   // standalone exports keep manual tools only

const S = window.P57Speaker;
// ---------- speaker notes launcher, directly on the report interface
const notesFab = make('button', '📝', 'p57-fab');
notesFab.id = 'p57-notes-fab';
notesFab.title = 'Speaker notes';
notesFab.setAttribute('aria-label', 'Open speaker notes');
notesFab.onclick = () => S ? S.notes() : null;
document.body.append(notesFab);

// ---------- state
let session;
try{
  session = localStorage.getItem('p57-ai-session:' + run);
  if(!session){ session = Array.from(crypto.getRandomValues(new Uint8Array(8)), b => b.toString(16).padStart(2,'0')).join(''); localStorage.setItem('p57-ai-session:' + run, session); }
}catch{ session = 'anon'; }
let llmConfigured = false, ctxEl = null, ctxMode = null, busy = false;

// ---------- panel
const fab = make('button', 'AI', 'p57-fab');
fab.id = 'p57-ai-fab';
fab.title = 'Ask the studio analyst';
fab.setAttribute('aria-label', 'Open the AI assistant');
document.body.append(fab);

const panel = make('div', null, 'p57-ai-panel'); panel.hidden = true;
const head = make('div', null, 'p57-ai-head');
head.append(make('strong', 'Studio analyst'));
const modeBadge = make('span', '…', 'p57-ai-mode');
const gear = make('button', '⚙', 'AI settings'); gear.title = 'AI settings';
const close = make('button', '✕', 'Close');
head.append(modeBadge, gear, close);
const ctx = make('div', null, 'p57-ai-ctx'); ctx.hidden = true;
const log = make('div', null, 'p57-ai-log'); log.setAttribute('aria-live', 'polite');
const suggest = make('div', null, 'p57-ai-suggest');
const inputRow = make('div', null, 'p57-ai-input');
const box = make('textarea'); box.rows = 1; box.placeholder = 'Ask about any metric, chapter or figure…';
box.setAttribute('aria-label', 'Ask the studio analyst');
const send = make('button', 'Send');
inputRow.append(box, send);
const foot = make('div', null, 'p57-ai-foot');
panel.append(head, ctx, log, suggest, inputRow, foot);
document.body.append(panel);

function setMode(){ modeBadge.textContent = llmConfigured ? 'AI model linked' : 'Built-in analyst'; }
async function refreshStatus(){
  try{
    const res = await fetch('/api/ai/status?run=' + encodeURIComponent(run));
    const st = await res.json();
    llmConfigured = !!(st.llm && st.llm.configured);
    foot.textContent = llmConfigured
      ? `Model ${st.llm.model} · grounded in ${st.context_tokens || '–'} tokens of computed metrics`
      : 'Deterministic mode · answers come straight from the computed metrics · add an AI key in ⚙ for free-form questions';
  }catch{ foot.textContent = 'Assistant offline'; }
  setMode();
}

// ---------- rendering
function md(text){
  const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/^\s*[-•]\s+/gm, '· ')
    .replace(/^(\d+)\.\s+/gm, '<b>$1.</b> ');
}
function bubble(role, text, meta){
  const m = make('div', null, 'p57-ai-msg ' + role);
  m.innerHTML = md(text);
  if(meta && meta.chapters && meta.chapters.length){
    const src = make('span', null, 'src');
    src.textContent = 'Sources: ' + meta.chapters.join(' · ') + (meta.mode === 'deterministic' ? ' · computed directly' : '');
    m.append(src);
  }
  log.append(m);
  log.scrollTop = log.scrollHeight;
  return m;
}
function chips(list){
  suggest.replaceChildren();
  list.forEach(q => { const b = make('button', q); b.onclick = () => ask(q); suggest.append(b); });
}
chips(['Summarise this review', 'What was the cash collected?', 'Capacity utilisation vs last year?', 'Top trainers by revenue', 'How is the fill rate calculated?', 'What should we fix first?']);

// ---------- chat
async function api(path, body){
  const res = await fetch(path, {method: body ? 'POST' : 'GET',
    headers: {'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : undefined});
  const data = await res.json();
  if(!res.ok) throw Error(data.error || 'Request failed');
  return data;
}
async function ask(text){
  text = (text || '').trim();
  if(!text || busy) return;
  clearCtxBanner(false);
  bubble('user', text);
  box.value = '';
  busy = true; send.disabled = true;
  const wait = bubble('busy', 'Thinking…');
  try{
    const sel = window.getSelection()?.toString().trim() || '';
    const data = await api('/api/ai/chat', {run, question: text, session, context: ctxEl ? ctxEl.textContent.slice(0, 500) : sel});
    wait.remove();
    bubble('ai', data.answer || 'I have nothing on that in this review.', data);
    if(data.cached) foot.textContent = 'Served from cache · 0 tokens';
  }catch(e){ wait.remove(); bubble('err', e.message); }
  busy = false; send.disabled = false;
}
// send/enter behaviour is bound once below, after ctxMode exists

// ---------- element editing with AI
function ctxBanner(html){
  ctx.hidden = false;
  ctx.replaceChildren(make('b', 'Working on: '), make('span', html.slice(0, 140) + (html.length > 140 ? '…' : '')));
  const x = make('button', '✕'); x.onclick = () => clearCtxBanner(true);
  ctx.append(x);
}
function clearCtxBanner(reset){
  ctx.hidden = true;
  if(reset){ ctxEl = null; ctxMode = null; box.placeholder = 'Ask about any metric, chapter or figure…'; }
}
function preview(accepted){
  const wrap = make('div', null, 'p57-ai-preview');
  const body = make('div', null, 'p57-ai-preview-body'); body.innerHTML = md(accepted);
  const acts = make('div', null, 'p57-ai-preview-actions');
  const ok = make('button', 'Apply', 'ok'), no = make('button', 'Discard', 'no');
  acts.append(ok, no); wrap.append(body, acts); log.append(wrap); log.scrollTop = log.scrollHeight;
  return {ok, no, wrap};
}
async function runEdit(){
  const instruction = box.value.trim();
  if(!instruction || !ctxEl || busy) return;
  bubble('user', '✦ ' + instruction);
  box.value = '';
  busy = true; send.disabled = true;
  const wait = bubble('busy', ctxMode === 'create' ? 'Drafting a new block…' : 'Rewriting…');
  try{
    let data;
    if(ctxMode === 'create'){
      data = await api('/api/ai/create', {run, instruction});
      wait.remove();
      if(data.error) throw Error(data.error);
      const p = preview(data.html.replace(/^<p>|<\/p>$/g, ''));
      p.ok.onclick = async () => {
        if(window.P57Edit) await window.P57Edit.insertAfter(ctxEl, data.html);
        p.wrap.remove(); bubble('ai', 'Block added. Hover it in Layout mode to keep editing.');
        clearCtxBanner(true);
      };
      p.no.onclick = () => { p.wrap.remove(); };
    }else{
      data = await api('/api/ai/edit', {run, instruction, html: ctxEl.textContent});
      wait.remove();
      if(data.error) throw Error(data.error);
      const p = preview(data.html);
      p.ok.onclick = async () => {
        const el = ctxEl;
        if(el.tagName === 'P' || el.tagName === 'H3' || el.tagName === 'H4' || el.classList.contains('sub')) el.textContent = data.html;
        else el.innerHTML = '<p>' + data.html + '</p>';
        if(window.P57Edit) await window.P57Edit.saveElement(el, el.innerHTML);
        p.wrap.remove(); bubble('ai', 'Applied. The block is saved for everyone viewing this run.');
        clearCtxBanner(true);
      };
      p.no.onclick = () => { p.wrap.remove(); };
    }
  }catch(e){ wait.remove(); bubble('err', e.message); }
  busy = false; send.disabled = false;
}

window.P57AI = {
  open(){ panel.hidden = false; refreshStatus(); box.focus(); },
  close(){ panel.hidden = true; },
  openForElement(el, mode){
    ctxEl = el; ctxMode = mode || 'rewrite';
    ctxBanner(el.textContent || 'empty block');
    box.placeholder = mode === 'create' ? 'Describe the block to add…' : 'Tell the AI how to rewrite this block…';
    chips(mode === 'create'
      ? ['Add a callout with the month headline numbers', 'Add a paragraph comparing fill vs last year']
      : ['Make it shorter', 'Make it punchier for executives', 'Turn it into three bullet points']);
    window.P57AI.open();
  },
};
fab.onclick = () => { panel.hidden ? window.P57AI.open() : window.P57AI.close(); };
close.onclick = () => window.P57AI.close();
document.addEventListener('keydown', e => { if(e.key === 'Escape' && !panel.hidden) window.P57AI.close(); });
box.addEventListener('input', () => { box.style.height = 'auto'; box.style.height = Math.min(110, box.scrollHeight) + 'px'; });
box.addEventListener('keydown', e => { if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); ctxMode ? runEdit() : ask(box.value); } });
send.onclick = () => ctxMode ? runEdit() : ask(box.value);

// ---------- settings dialog
gear.onclick = () => {
  const wrapEl = make('div', null, 'p57-ai-settings');
  wrapEl.append(make('p', 'Connect an OpenAI-compatible model for free-form questions and AI rewrites. ' +
    'Without a key the built-in analyst answers from the computed metrics at zero tokens. ' +
    'Keys are held by the server process only — never stored in your browser.'));
  const key = make('input'); key.type = 'password'; key.placeholder = 'API key (sk-…)'; key.setAttribute('aria-label', 'AI API key');
  const model = make('input'); model.placeholder = 'Model, e.g. gpt-4o-mini'; model.setAttribute('aria-label', 'Model name');
  const base = make('input'); base.placeholder = 'Endpoint (optional)'; base.setAttribute('aria-label', 'Chat completions endpoint');
  const l1 = make('label', 'API key'); l1.append(key);
  const l2 = make('label', 'Model'); l2.append(model);
  const l3 = make('label', 'Endpoint'); l3.append(base);
  wrapEl.append(l1, l2, l3);
  const saveBtn = make('button', 'Save AI settings');
  saveBtn.onclick = async () => {
    try{
      const st = await api('/api/ai/key', {key: key.value, model: model.value, base: base.value});
      llmConfigured = st.configured; setMode();
      foot.textContent = st.configured ? 'Model ' + st.model + ' connected' : 'AI key removed — deterministic mode';
      R.dialog.close();
    }catch(e){ alert(e.message); }
  };
  wrapEl.append(saveBtn);
  R.openDialog('AI settings', wrapEl);
};
refreshStatus();
})();
