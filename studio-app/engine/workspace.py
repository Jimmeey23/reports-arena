"""Durable report preferences, annotations and meeting-code presentation sessions."""
import json, secrets, sqlite3, time, re
from pathlib import Path

class WorkspaceError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message

class Workspace:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS deleted_reports(run_id TEXT PRIMARY KEY, deleted REAL);
            CREATE TABLE IF NOT EXISTS documents(user TEXT, report TEXT, value TEXT, updated REAL,
                PRIMARY KEY(user,report));
            CREATE TABLE IF NOT EXISTS meetings(code TEXT PRIMARY KEY, owner TEXT, report TEXT,
                view TEXT, active INTEGER, updated REAL);
            CREATE TABLE IF NOT EXISTS participants(code TEXT, user TEXT, seen REAL,
                PRIMARY KEY(code,user));
            ''')
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db
    def deleted_reports(self):
        with self.connect() as db:
            return {r[0] for r in db.execute('SELECT run_id FROM deleted_reports')}
    def delete_report(self, run_id):
        with self.connect() as db:
            prefix = run_id + '/'
            db.execute('DELETE FROM participants WHERE code IN (SELECT code FROM meetings WHERE substr(report,1,?)=?)', (len(prefix),prefix))
            db.execute('DELETE FROM meetings WHERE substr(report,1,?)=?', (len(prefix),prefix))
            db.execute('DELETE FROM documents WHERE substr(report,1,?)=?', (len(prefix),prefix))
            db.execute('INSERT OR REPLACE INTO deleted_reports VALUES(?,?)', (run_id,time.time()))
    def identity(self, user):
        if not re.fullmatch(r'[a-f0-9]{32,64}', user or ''):
            raise WorkspaceError(400, 'Browser identity is missing or invalid')
    def document(self, user, report):
        self.identity(user)
        with self.connect() as db:
            row = db.execute('SELECT value FROM documents WHERE user=? AND report=?', (user,report)).fetchone()
        return json.loads(row['value']) if row else {}
    def save(self, user, report, patch):
        self.identity(user)
        if not isinstance(patch, dict) or len(json.dumps(patch)) > 2_000_000:
            raise WorkspaceError(400, 'Invalid report changes')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM deleted_reports WHERE run_id=?',(report.split('/')[0],)).fetchone():
                raise WorkspaceError(404, 'This report has been deleted')
            row = db.execute('SELECT value FROM documents WHERE user=? AND report=?',(user,report)).fetchone()
            value = json.loads(row['value']) if row else {}
            for key in ('preferences','notes','edits','annotations'):
                if key in patch:
                    if not isinstance(patch[key],dict):
                        raise WorkspaceError(400, 'Changes must use field maps')
                    value.setdefault(key,{}).update(patch[key])
            db.execute('INSERT OR REPLACE INTO documents VALUES(?,?,?,?)',
                (user,report,json.dumps(value),time.time()))
        return value
    def host(self, user, report):
        self.identity(user)
        with self.connect() as db:
            for _ in range(10):
                code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
                try:
                    db.execute('INSERT INTO meetings VALUES(?,?,?,?,1,?)',
                        (code,user,report,json.dumps({'section':'','scroll':0}),time.time()))
                    break
                except sqlite3.IntegrityError:
                    continue
            else:
                raise WorkspaceError(503, 'Could not allocate meeting code')
        return self.meeting(code, user)
    def meeting(self, code, user):
        self.identity(user)
        code = str(code).replace('-','').strip().upper()
        with self.connect() as db:
            row = db.execute('SELECT * FROM meetings WHERE code=?',(code,)).fetchone()
            if not row:
                raise WorkspaceError(404, 'Meeting code was not found')
            if row['active']:
                db.execute('INSERT OR REPLACE INTO participants VALUES(?,?,?)',(code,user,time.time()))
            count = db.execute('SELECT count(*) FROM participants WHERE code=? AND seen>?',
                (code,time.time()-20)).fetchone()[0]
        saved = self.document(row['owner'], row['report'])
        return dict(code=code, report=row['report'], view=json.loads(row['view']),
                    active=bool(row['active']), is_host=row['owner']==user,
                    participants=count, edits=saved.get('edits',{}),
                    annotations=saved.get('annotations',{}), updated=row['updated'])
    def update(self, code, user, view=None, end=False):
        self.identity(user)
        if view is not None and (not isinstance(view,dict) or len(json.dumps(view))>60000):
            raise WorkspaceError(400,'Invalid presentation view')
        with self.connect() as db:
            row = db.execute('SELECT * FROM meetings WHERE code=?',(code,)).fetchone()
            if not row:
                raise WorkspaceError(404,'Meeting code was not found')
            if row['owner'] != user:
                raise WorkspaceError(403,'Only the host can guide this session')
            if not row['active']:
                raise WorkspaceError(409,'This session has ended')
            if view is not None:
                scroll = min(1, max(0, float(view.get('scroll',0))))
                evidence=view.get('evidence',[])
                if not isinstance(evidence,list) or len(evidence)>1000:
                    raise WorkspaceError(400,'Invalid evidence view')
                tables=view.get('tables',[])
                if not isinstance(tables,list) or len(tables)>300:
                    raise WorkspaceError(400,'Invalid table view')
                normalized=[]
                for table in tables:
                    if not isinstance(table,dict) or not isinstance(table.get('index'),int) or not isinstance(table.get('sort',-1),int):
                        raise WorkspaceError(400,'Invalid table view')
                    normalized.append(dict(index=table['index'],filter=str(table.get('filter',''))[:200],sort=table.get('sort',-1),descending=bool(table.get('descending',False))))
                view = {'section':str(view.get('section',''))[:200], 'scroll':scroll,
                        'evidence':[int(i) for i in evidence if isinstance(i,int) and 0<=i<1000],
                        'chartsHidden':bool(view.get('chartsHidden',False)), 'tables':normalized}
            db.execute('UPDATE meetings SET view=?,active=?,updated=? WHERE code=?',
                (json.dumps(view) if view is not None else row['view'],0 if end else 1,time.time(),code))
        return self.meeting(code,user)
