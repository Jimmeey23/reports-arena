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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine.data import Dataset, discover, sniff
from engine.build import build
from engine.metrics import MONTH_NAMES

DATA = os.path.join(HERE, 'data')
UPLOADS = os.path.join(DATA, 'uploaded')
RUNS = os.path.join(HERE, 'runs')
SEED = [p for p in [os.environ.get('SEED_DIR_1', '/home/user/uploads'),
                    os.environ.get('SEED_DIR_2', '/home/user/google_drive')] if p and os.path.isdir(p)]
STATIC = os.path.join(HERE, 'static')
for d in (DATA, UPLOADS, RUNS):
    os.makedirs(d, exist_ok=True)

LOCK = threading.Lock()
STATE = dict(dataset=None, files=[], sig='', studios={}, warnings=[], logs=[], jobs={}, runs={})


# --------------------------------------------------------------------- helpers
def source_paths():
    out = []
    for d in SEED:
        out += discover(d)
    out += discover(UPLOADS)
    return out


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
            m = json.load(open(mf))
        except Exception:
            continue
        STATE['runs'][rid] = dict(
            id=rid, dir=d, label=m.get('label', ''), studio=m.get('studio', ''), built=m.get('built', ''),
            seconds=m.get('seconds'), sources=m.get('sources', []), warnings=m.get('warnings', []),
            chapters=[dict(id=c['id'], n=c.get('n'), title=c['title'], subtitle=c.get('subtitle'),
                           kpis=c.get('kpis'), summary=c.get('summary'), summary_ai=c.get('summary_ai', ''),
                           facts=c.get('facts', []), narration=c.get('narration'),
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
                                             narration=c.get('narration'), recs=len(c.get('recs', [])))
                                        for c in res['chapters']],
                              metrics=res['metrics'])


def state_payload():
    D = STATE['dataset']
    studios = []
    if D is not None:
        for name, rows in STATE['studios'].items():
            months = D.months(name)
            studios.append(dict(name=name, rows=rows,
                                months=[dict(year=y, month=m, sessions=n, label=f'{MONTH_NAMES[m-1]} {y}')
                                        for (y, m, n) in months]))
    return dict(studios=studios,
                sources=[dict(name=os.path.basename(s.path), kind=s.kind, rows=s.rows,
                              folder='uploaded' if s.path.startswith(UPLOADS) else 'bundled')
                         for s in (D.sources if D else [])],
                warnings=STATE['warnings'],
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


def do_generate(job, studio, year, month, chapters, llm):
    job['pct'] = 6; job['message'] = 'reading the uploaded exports'
    D = load(log=lambda s: job['log'].append(s))
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
                       recs=len(c.get('recs', []))) for c in res['chapters']],
        metrics=res['metrics'])
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
                return self._send(200, state_payload())
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
                f = os.path.join(RUNS, rid, ('report' if name in ('full', 'all') else name) + '.html')
                return self._file(f, 'text/html; charset=utf-8')
            if p.startswith('/api/raw/'):
                parts = p.split('/')
                rid, name = parts[3], parts[4] if len(parts) > 4 else ''
                return self._file(os.path.join(RUNS, rid, os.path.basename(name)))
            if p == '/api/download':
                rid = q.get('run', [''])[0]
                f = os.path.join(RUNS, rid, 'report.html')
                if not os.path.isfile(f):
                    return self._send(404, dict(error='unknown run'))
                data = open(f, 'rb').read()
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
            return self._send(404, dict(error='no route', path=p))
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
            if u.path == '/api/upload':
                parts = self._multipart()
                if not parts:
                    return self._send(400, dict(error='no files in the request'))
                saved, skipped = [], []
                for fn, blob in parts:
                    if not blob:
                        skipped.append((fn, 'file is empty'))
                        continue
                    tmp = os.path.join(UPLOADS, '_tmp_' + fn)
                    with open(tmp, 'wb') as f:
                        f.write(blob)
                    kind = sniff(tmp)
                    if not kind:
                        os.remove(tmp)
                        skipped.append((fn, 'header row not recognised'))
                        continue
                    dest = os.path.join(UPLOADS, fn)
                    os.replace(tmp, dest)
                    saved.append(dict(name=fn, kind=kind, bytes=len(blob)))
                    print(f'  uploaded {fn} -> {kind} ({len(blob)/1e6:.1f} MB)')
                D = load(force=True, log=lambda s: None)
                return self._send(200, dict(saved=saved, skipped=skipped,
                                            state=state_payload()))

            if u.path == '/api/generate':
                n = int(self.headers.get('Content-Length', 0))
                req = json.loads(self.rfile.read(n) or b'{}')
                studio = req.get('studio'); year = int(req.get('year')); month = int(req.get('month'))
                chapters = req.get('chapters') or []
                llm = req.get('llm') or {}
                if not studio:
                    return self._send(400, dict(error='choose a studio'))
                jid = start_job('generate', lambda j: do_generate(j, studio, year, month, chapters, llm))
                return self._send(200, dict(job=jid))

            if u.path == '/api/remove':
                n = int(self.headers.get('Content-Length', 0))
                req = json.loads(self.rfile.read(n) or b'{}')
                name = os.path.basename(req.get('name', ''))
                f = os.path.join(UPLOADS, name)
                if os.path.isfile(f):
                    os.remove(f)
                D = load(force=True, log=lambda s: None)
                return self._send(200, dict(removed=name, state=state_payload()))

            if u.path == '/api/reload':
                load(force=True, log=lambda s: None)
                scan_runs()
                return self._send(200, dict(state=state_payload()))

            return self._send(404, dict(error='no route', path=u.path))
        except Exception as e:
            traceback.print_exc()
            return self._send(500, dict(error=str(e)))


def main():
    port = 8000
    if '--port' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1])
    print('Studio Intelligence')
    for d in SEED:
        print(f'  watching {d}')
    print(f'  uploads  {UPLOADS}')
    def boot():
        D = load(log=print)          # always: the pickers need the studio list
        try:
            bake_first_review(D)     # only does work when there is no review yet
        except Exception as e:
            print('  first review could not be baked:', e)
    threading.Thread(target=boot, daemon=True).start()
    srv = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print(f'  listening on http://0.0.0.0:{port}')
    srv.serve_forever()


if __name__ == '__main__':
    main()
