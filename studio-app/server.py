#!/usr/bin/env python3
"""Studio Intelligence - a small, dependency-free web app that turns the
studio's own day-end exports into a nine-chapter performance review.

Run:  python3 server.py [--port 8000]
Nothing outside the standard library is required.
"""
from __future__ import annotations
import os, sys, json, time, uuid, threading, mimetypes, traceback, sqlite3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine.data import Dataset, discover, sniff
from engine.build import build
from engine.reader import enhance_report
from engine.workspace import Workspace, WorkspaceError
from engine.metrics import MONTH_NAMES
from ai import agent, llm, metrics_pack
from ai.store import Store, _now as _now_iso

DATA = os.path.join(HERE, 'data')
UPLOADS = os.path.join(DATA, 'uploaded')
RUNS = os.path.join(HERE, 'runs')
SEED = []  # Source files are accepted only from an explicit fresh upload batch.
STATIC = os.path.join(HERE, 'static')
for d in (DATA, UPLOADS, RUNS):
    os.makedirs(d, exist_ok=True)

WORKSPACE = Workspace(os.environ.get('P57_WORKSPACE_DB', os.path.join(DATA, 'workspace.sqlite3')))
AI_STORE = Store(os.path.join(DATA, 'ai.sqlite3'))
LOCK = threading.Lock()
STATE = dict(dataset=None, files=[], sig='', studios={}, warnings=[], logs=[], jobs={}, runs={})


# --------------------------------------------------------------------- helpers
def source_paths(batch=None):
    if not batch:
        return []
    directory = batch_dir(batch)
    return discover(directory) if os.path.isdir(directory) else []


def batch_dir(batch):
    import re
    if not re.fullmatch(r'[a-f0-9]{32}', batch or ''):
        raise WorkspaceError(400, 'Choose fresh exports to start an upload batch')
    return os.path.join(DATA, 'batches', batch)


def batch_dataset(batch):
    paths = source_paths(batch)
    return Dataset(paths, log=lambda *a: None, priority={batch_dir(batch): 2}) if batch else None


def signature(paths):
    return '|'.join(f'{p}:{os.path.getsize(p)}:{int(os.path.getmtime(p))}' for p in sorted(paths))


def load(force=False, log=lambda *a: None):
    """(Re)load every file on disk if anything changed."""
    paths = source_paths()
    sig = signature(paths)
    with LOCK:
        if not force and STATE['dataset'] is not None and sig == STATE['sig']:
            return STATE['dataset']
        STATE['logs'] = []
    t0 = time.time()
    D = Dataset(paths, log=lambda s: (log(s), STATE['logs'].append(s)),
                priority={UPLOADS: 2, (SEED[0] if SEED else '/none'): 1})
    with LOCK:
        STATE['dataset'] = D
        STATE['files'] = paths
        STATE['sig'] = sig
        STATE['warnings'] = D.warnings
        STATE['studios'] = D.studios()
        STATE['loaded_at'] = time.time()
        STATE['load_seconds'] = round(time.time() - t0, 1)
    log(f'loaded {len(D.sources)} sources in {STATE["load_seconds"]}s')
    return D


def scan_runs():
    """Register every review already written to runs/ and drop the ones
    whose folder has been removed."""
    on_disk = set(os.listdir(RUNS))
    for gone in [r for r in STATE['runs'] if r not in on_disk]:
        STATE['runs'].pop(gone, None)
    for rid in sorted(on_disk, reverse=True):
        d = os.path.join(RUNS, rid)
        mf = os.path.join(d, 'manifest.json')
        if rid in STATE['runs'] or not os.path.isfile(mf):
            continue
        try:
            m = json.loads(Path(mf).read_text())
        except Exception:
            continue
        STATE['runs'][rid] = dict(
            id=rid, dir=d, label=m.get('label', ''), studio=m.get('studio', ''), built=m.get('built', ''),
            seconds=m.get('seconds'), sources=m.get('sources', []), warnings=m.get('warnings', []),
            chapters=[dict(id=c['id'], n=c.get('n'), title=c['title'], subtitle=c.get('subtitle'),
                           kpis=c.get('kpis'), summary=c.get('summary'), summary_ai=c.get('summary_ai', ''),
                           facts=c.get('facts', []), narration=c.get('narration'),
                           sections=c.get('sections', []),
                           recs=len(c.get('recs', []))) for c in m.get('chapters', [])])
    return STATE['runs']


def bake_first_review(D=None):
    """On a cold start with no reviews yet, build the default one so the
    Review tab has something in it the moment the app opens."""
    if not STATE['runs'] and scan_runs():
        return
    D = D if D is not None else load(log=print)
    cands = [s for s in STATE['studios'] if any(sess for (_, _, sess) in D.months(s))]
    if not cands:
        return
    today = time.localtime()
    now_key = (today.tm_year, today.tm_mon)
    want = os.environ.get('DEMO_STUDIO', '').strip()
    pick = want if want in cands else max(cands, key=lambda s: STATE['studios'][s])
    months = [t for t in D.months(pick) if (t[0], t[1]) < now_key] or D.months(pick)
    y, m, _ = months[-1]
    print(f'  baking the first review: {pick} / {MONTH_NAMES[m-1]} {y}')
    rid = time.strftime('%Y%m%d-%H%M%S') + '-demo'
    res = build(D, pick, y, m, os.path.join(RUNS, rid), log=print)
    mf = res['manifest']
    STATE['runs'][rid] = dict(id=rid, dir=os.path.join(RUNS, rid), label=mf['label'], studio=mf['studio'],
                              built=mf['built'], seconds=mf['seconds'], sources=mf['sources'],
                              warnings=mf['warnings'],
                              chapters=[dict(id=c['id'], n=c['n'], title=c['title'], subtitle=c.get('subtitle'),
                                             kpis=c.get('kpis'), summary=c.get('summary'),
                                             summary_ai=c.get('summary_ai', ''), facts=c.get('facts', []),
                                             narration=c.get('narration'), sections=c.get('sections', []),
                                             recs=len(c.get('recs', [])))
                                        for c in res['chapters']],
                              metrics=res['metrics'])
    try:
        AI_STORE.save_report(rid, dict(
            run_id=rid, studio=mf['studio'], label=mf['label'], built=mf['built'],
            seconds=mf['seconds'], sources=mf['sources'],
            chapters=[dict(id=c['id'], title=c['title'],
                           kpis=[dict(label=k.get('label'), value=k.get('value'), detail=k.get('detail', ''))
                                 for k in (c.get('kpis') or [])[:6]],
                           facts=(c.get('facts') or [])[:3]) for c in res['chapters']]))
    except Exception:
        pass


def run_pack(rid):
    """Load the AI metrics pack for a run (file snapshot, manifest fallback)."""
    rid = os.path.basename(rid or '')
    if rid not in scan_runs():
        return None
    return metrics_pack.load_pack(RUNS, rid)


def state_payload(batch=None):
    D = batch_dataset(batch)
    studios = []
    if D is not None:
        for name, rows in D.studios().items():
            months = D.months(name)
            studios.append(dict(name=name, rows=rows,
                                months=[dict(year=y, month=m, sessions=n, label=f'{MONTH_NAMES[m-1]} {y}')
                                        for (y, m, n) in months]))
    return dict(studios=studios,
                sources=[dict(name=os.path.basename(s.path), kind=s.kind, rows=s.rows,
                              folder='uploaded')
                         for s in (D.sources if D else [])],
                warnings=D.warnings if D else [],
                load_seconds=STATE.get('load_seconds'),
                kinds_present=sorted(D.kinds) if D else [],
                runs=[{kk: vv for kk, vv in v.items() if kk != 'metrics'}
                      for k, v in sorted(STATE['runs'].items(), reverse=True)],
                logs=STATE['logs'][-40:])


# --------------------------------------------------------------------- jobs
def start_job(kind, fn):
    jid = uuid.uuid4().hex[:12]
    job = dict(id=jid, kind=kind, state='running', pct=2, message='starting', log=[], started=time.time())
    STATE['jobs'][jid] = job

    def run():
        try:
            fn(job)
            job['state'] = 'done'; job['pct'] = 100; job['message'] = 'complete'
        except Exception as e:
            job['state'] = 'error'; job['message'] = str(e)
            job['log'].append(traceback.format_exc().splitlines()[-3:])
        job['seconds'] = round(time.time() - job['started'], 1)
    threading.Thread(target=run, daemon=True).start()
    return jid


def do_generate(job, studio, year, month, chapters, llm, D):
    job['pct'] = 6; job['message'] = 'reading the uploaded exports'
    job['pct'] = 25; job['message'] = f'computing {MONTH_NAMES[month-1]} {year} for {studio}'
    rid = time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:4]
    outdir = os.path.join(RUNS, rid)
    key = None
    if llm and llm.get('key'):
        key = (llm['key'], llm.get('model') or 'gpt-4o-mini')
    res = build(D, studio, year, month, outdir,
                log=lambda s: job['log'].append(s), use_llm=key,
                chapters=chapters or None)
    job['pct'] = 92; job['message'] = 'writing chapters'
    m = res['manifest']
    STATE['runs'][rid] = dict(
        id=rid, dir=outdir, label=m['label'], studio=m['studio'], built=m['built'], seconds=m['seconds'],
        sources=m['sources'], warnings=m['warnings'],
        chapters=[dict(id=c['id'], n=c['n'], title=c['title'], subtitle=c.get('subtitle'),
                       kpis=c.get('kpis'), summary=c.get('summary'), summary_ai=c.get('summary_ai', ''),
                       facts=c.get('facts', []), narration=c.get('narration'),
                       sections=c.get('sections', []),
                       recs=len(c.get('recs', []))) for c in res['chapters']],
        metrics=res['metrics'])
    # Persist the review itself (Supabase when configured, local SQLite otherwise)
    # with a compact metric digest, so reports survive and earlier periods of the
    # same studio can be handed to the AI as comparison context.
    try:
        AI_STORE.save_report(rid, dict(
            run_id=rid, studio=m['studio'], label=m['label'], built=m['built'],
            seconds=m['seconds'], sources=m['sources'],
            chapters=[dict(id=c['id'], title=c['title'],
                           kpis=[dict(label=k.get('label'), value=k.get('value'), detail=k.get('detail', ''))
                                 for k in (c.get('kpis') or [])[:6]],
                           facts=(c.get('facts') or [])[:3]) for c in res['chapters']]))
    except Exception as e:
        job['log'].append(f'report persistence skipped: {e}')
    job['run'] = rid
    job['pct'] = 99


# --------------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    server_version = 'StudioIntelligence/1.0'

    def log_message(self, fmt, *a):
        if os.environ.get('QUIET'):
            return
        sys.stderr.write('  %s\n' % (fmt % a))

    # ------------------------------------------------------------------ output
    def _send(self, code, body, ctype='application/json', extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, default=str).encode()
        elif isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _file(self, path, ctype=None):
        if not os.path.isfile(path):
            return self._send(404, dict(error='not found'))
        ctype = ctype or mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(path, 'rb') as f:
            data = f.read()
        if path.startswith(RUNS + os.sep) and path.endswith('.html'):
            data = enhance_report(data.decode('utf-8')).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        if path.startswith(STATIC + os.sep):
            self.send_header('Cache-Control', 'no-store')
        if path.endswith('.html'):
            self.send_header('Content-Disposition', 'inline')
        self.end_headers()
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            pass

    # ------------------------------------------------------------------ routes
    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        try:
            if p in ('/', '/index.html'):
                return self._file(os.path.join(STATIC, 'index.html'), 'text/html; charset=utf-8')
            if p.startswith('/static/'):
                return self._file(os.path.join(STATIC, os.path.basename(p)))
            if p == '/api/state':
                if STATE['dataset'] is None:
                    load()
                scan_runs()
                return self._send(200, state_payload(self.headers.get('X-Upload-Batch')))
            if p == '/api/workspace':
                return self._send(200, WORKSPACE.document(self.headers.get('X-P57-User'), q.get('report',[''])[0]))
            if p.startswith('/api/meetings/'):
                return self._send(200, WORKSPACE.meeting(p.rsplit('/',1)[-1], self.headers.get('X-P57-User')))
            if p.startswith('/api/job/'):
                j = STATE['jobs'].get(p.rsplit('/', 1)[-1])
                return self._send(200, j or dict(error='unknown job'), )
            if p.startswith('/api/report/'):
                bits = p.split('/')
                rid, name = bits[3], (bits[4] if len(bits) > 4 else 'full')
                run = STATE['runs'].get(rid)
                if not run:
                    return self._send(404, dict(error='unknown run'))
                name = name.replace('.html', '')
                if name not in ['full','all','report'] + [c['id'] for c in run['chapters']]:
                    return self._send(404, dict(error='unknown chapter'))
                f = os.path.join(RUNS, rid, ('report' if name in ('full', 'all') else name) + '.html')
                # Re-enhance on serve so asset (toolbar/editor/explorer) updates
                # reach existing runs without a rebuild; the enhancer dedupes.
                try:
                    data = enhance_report(Path(f).read_text()).encode('utf-8')
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    return self._file(f, 'text/html; charset=utf-8')
                return
            if p.startswith('/api/raw/'):
                parts = p.split('/')
                rid, name = parts[3], parts[4] if len(parts) > 4 else ''
                return self._file(os.path.join(RUNS, rid, os.path.basename(name)))
            if p == '/api/download':
                rid = q.get('run', [''])[0]
                f = os.path.join(RUNS, rid, 'report.html')
                if not os.path.isfile(f):
                    return self._send(404, dict(error='unknown run'))
                data = enhance_report(Path(f).read_text()).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Disposition',
                                 f'attachment; filename="Performance_Review_{rid}.html"')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                try:
                    self.wfile.write(data)
                except BrokenPipeError:
                    pass
                return
            if p == '/api/config':
                return self._send(200, dict(backend=AI_STORE.backend, config=AI_STORE.config_all()))
            if p == '/api/reports/history':
                studio = q.get('studio', [None])[0]
                rows = AI_STORE.list_reports(studio=studio, limit=int(q.get('limit', ['24'])[0]))
                return self._send(200, dict(backend=AI_STORE.backend, reports=rows))
            if p == '/api/ai/status':
                pack = run_pack(q.get('run', [''])[0]) if q.get('run') else None
                return self._send(200, dict(llm=llm.status(), backend=AI_STORE.backend,
                                            context_tokens=agent.context_estimate(pack) if pack else None))
            if p == '/api/ai/context':
                pack = run_pack(q.get('run', [''])[0])
                if not pack:
                    return self._send(404, dict(error='unknown run'))
                return self._send(200, pack)
            if p == '/api/edits':
                rid = os.path.basename(q.get('run', [''])[0])
                if rid not in scan_runs():
                    return self._send(404, dict(error='unknown run'))
                return self._send(200, dict(run=rid, edits=AI_STORE.edits(rid)))
            return self._send(404, dict(error='no route', path=p))
        except WorkspaceError as e:
            return self._send(e.status, dict(error=e.message))
        except Exception as e:
            traceback.print_exc()
            return self._send(500, dict(error=str(e)))

    # ------------------------------------------------------------------ upload
    def _multipart(self):
        ctype = self.headers.get('Content-Type', '')
        if 'boundary=' not in ctype:
            return []
        boundary = ctype.split('boundary=', 1)[1].strip().strip('"').encode()
        n = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(n)
        parts, out = raw.split(b'--' + boundary), []
        for part in parts:
            if b'Content-Disposition' not in part:
                continue
            head, _, body = part.partition(b'\r\n\r\n')
            if not _:
                continue
            head = head.decode('utf-8', 'ignore')
            if 'filename="' not in head:
                continue
            fn = head.split('filename="', 1)[1].split('"', 1)[0]
            out.append((os.path.basename(fn), body.rstrip(b'\r\n')))
        return out

    def do_POST(self):
        u = urlparse(self.path)
        try:
            if u.path in ('/api/workspace','/api/meetings') or u.path.startswith('/api/meetings/'):
                n = int(self.headers.get('Content-Length',0))
                if n > 2_100_000:
                    return self._send(413,dict(error='Changes are too large'))
                req = json.loads(self.rfile.read(n) or b'{}')
                user = self.headers.get('X-P57-User')
                if u.path == '/api/workspace':
                    return self._send(200,WORKSPACE.save(user,str(req.get('report','')),req.get('patch',{})))
                if u.path == '/api/meetings':
                    report = str(req.get('report',''))
                    bits = report.split('/')
                    if len(bits)!=2 or bits[0] not in scan_runs() or not os.path.isfile(os.path.join(RUNS,bits[0],('report' if bits[1]=='full' else bits[1])+'.html')) or bits[1] not in ['full','report'] + [c['id'] for c in STATE['runs'][bits[0]]['chapters']]:
                        raise WorkspaceError(400,'Open a saved report before hosting')
                    return self._send(200,WORKSPACE.host(user,report))
                return self._send(200,WORKSPACE.update(u.path.rsplit('/',1)[-1],user,req.get('view'),req.get('end',False)))
            if u.path == '/api/upload':
                parts = self._multipart()
                if not parts:
                    return self._send(400, dict(error='no files in the request'))
                upload_dir = batch_dir(self.headers.get('X-Upload-Batch'))
                os.makedirs(upload_dir, exist_ok=True)
                saved, skipped = [], []
                for fn, blob in parts:
                    if not blob:
                        skipped.append((fn, 'file is empty'))
                        continue
                    tmp = os.path.join(upload_dir, '_tmp_' + fn)
                    with open(tmp, 'wb') as f:
                        f.write(blob)
                    kind = sniff(tmp)
                    if not kind:
                        os.remove(tmp)
                        skipped.append((fn, 'header row not recognised'))
                        continue
                    dest = os.path.join(upload_dir, fn)
                    os.replace(tmp, dest)
                    saved.append(dict(name=fn, kind=kind, bytes=len(blob)))
                    print(f'  uploaded {fn} -> {kind} ({len(blob)/1e6:.1f} MB)')
                return self._send(200, dict(saved=saved, skipped=skipped,
                    state=state_payload(self.headers.get('X-Upload-Batch'))))

            if u.path == '/api/generate':
                n = int(self.headers.get('Content-Length', 0))
                req = json.loads(self.rfile.read(n) or b'{}')
                studio = req.get('studio'); year = int(req.get('year')); month = int(req.get('month'))
                chapters = req.get('chapters') or []
                llm = req.get('llm') or {}
                if not studio:
                    return self._send(400, dict(error='choose a studio'))
                D = batch_dataset(self.headers.get('X-Upload-Batch'))
                if not D or not D.sources:
                    raise WorkspaceError(400, 'Upload fresh exports before generating a report')
                if studio not in D.studios() or not any(y==year and m==month for y,m,_ in D.months(studio)):
                    raise WorkspaceError(400, 'Choose a studio and month from the fresh exports')
                jid = start_job('generate', lambda j: do_generate(j, studio, year, month, chapters, llm, D))
                return self._send(200, dict(job=jid))

            if u.path == '/api/remove':
                n = int(self.headers.get('Content-Length', 0))
                req = json.loads(self.rfile.read(n) or b'{}')
                name = os.path.basename(req.get('name', ''))
                f = os.path.join(batch_dir(self.headers.get('X-Upload-Batch')), name)
                if os.path.isfile(f):
                    os.remove(f)
                return self._send(200, dict(removed=name, state=state_payload(self.headers.get('X-Upload-Batch'))))

            if u.path == '/api/reload':
                scan_runs()
                return self._send(200, dict(state=state_payload(self.headers.get('X-Upload-Batch'))))

            if u.path == '/api/config':
                n = int(self.headers.get('Content-Length', 0))
                if n > 200_000:
                    return self._send(413, dict(error='Request too large'))
                req = json.loads(self.rfile.read(n) or b'{}')
                key = str(req.get('key', ''))[:80]
                if not key:
                    return self._send(400, dict(error='provide a key'))
                AI_STORE.config_put(key, req.get('value'))
                return self._send(200, dict(ok=True, key=key, backend=AI_STORE.backend))

            if u.path in ('/api/ai/chat', '/api/ai/edit', '/api/ai/create', '/api/ai/key', '/api/edits'):
                n = int(self.headers.get('Content-Length', 0))
                if n > 2_100_000:
                    return self._send(413, dict(error='Request too large'))
                req = json.loads(self.rfile.read(n) or b'{}')
                if u.path == '/api/ai/key':
                    llm.configure(key=req.get('key'), model=req.get('model'), base=req.get('base'))
                    st = llm.status()
                    # Persist the non-secret configuration so it survives restarts.
                    # The key itself is never stored; it stays in the environment.
                    try:
                        AI_STORE.config_put('ai', dict(model=st['model'], base=st.get('base', ''),
                                                       configured=st['configured'],
                                                       updated=_now_iso()))
                    except Exception:
                        pass
                    return self._send(200, dict(ok=True, configured=st['configured'], model=st['model']))
                rid = os.path.basename(str(req.get('run', '')))
                pack = run_pack(rid)
                if not pack:
                    return self._send(404, dict(error='unknown run'))
                session = str(req.get('session') or 'anon')
                if u.path == '/api/ai/chat':
                    return self._send(200, agent.chat(str(req.get('question', ''))[:1200], pack,
                                                      AI_STORE, f'{rid}:{session}',
                                                      extra_context=str(req.get('context', '')),
                                                      run_id=rid))
                if u.path == '/api/ai/edit':
                    return self._send(200, agent.edit_element(str(req.get('instruction', ''))[:400],
                                                              str(req.get('html', '')), pack))
                if u.path == '/api/ai/create':
                    return self._send(200, agent.create_element(str(req.get('instruction', ''))[:400], pack))
                if u.path == '/api/edits':
                    el_id = str(req.get('el_id', ''))[:160]
                    op = str(req.get('op', ''))
                    if not el_id or op not in ('set', 'delete', 'restore', 'insert'):
                        return self._send(400, dict(error='provide el_id and op in set|delete|restore|insert'))
                    if op == 'delete':
                        AI_STORE.upsert_edit(rid, el_id, 'delete')
                    elif op == 'restore':
                        AI_STORE.delete_edit(rid, el_id, 'delete')
                        AI_STORE.delete_edit(rid, el_id, 'set')
                    else:
                        AI_STORE.upsert_edit(rid, el_id, op, str(req.get('html', ''))[:200_000],
                                             int(req.get('sort', 0)))
                    return self._send(200, dict(run=rid, edits=AI_STORE.edits(rid)))

            return self._send(404, dict(error='no route', path=u.path))
        except WorkspaceError as e:
            return self._send(e.status, dict(error=e.message))
        except Exception as e:
            traceback.print_exc()
            return self._send(500, dict(error=str(e)))


def hydrate_report_store():
    """Persist every review already on disk into the report store (Supabase when
    configured, SQLite otherwise) so saved reports and the AI's cross-period
    context survive across environments. Runs already persisted are skipped."""
    for rid, run in STATE['runs'].items():
        try:
            if AI_STORE.report(rid):
                continue
            m = json.loads(Path(os.path.join(run['dir'], 'manifest.json')).read_text())
            AI_STORE.save_report(rid, dict(
                run_id=rid, studio=m.get('studio', ''), label=m.get('label', ''),
                built=m.get('built', ''), seconds=m.get('seconds'),
                sources=m.get('sources', []),
                chapters=[dict(id=c['id'], title=c.get('title', ''),
                               kpis=[dict(label=k.get('label'), value=k.get('value'),
                                          detail=k.get('detail', ''))
                                     for k in (c.get('kpis') or [])[:6]],
                               facts=(c.get('facts') or [])[:3])
                          for c in m.get('chapters', [])]))
        except Exception:
            continue


def main():
    port = 8000
    if '--port' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1])
    print('Studio Intelligence')
    for d in SEED:
        print(f'  watching {d}')
    print(f'  uploads  {UPLOADS}')
    scan_runs()  # Saved reviews persist; startup never imports or generates data.
    hydrate_report_store()  # Push on-disk reviews into the persistent report store.
    srv = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print(f'  listening on http://0.0.0.0:{port}')
    srv.serve_forever()


if __name__ == '__main__':
    main()
