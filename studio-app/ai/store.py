"""Persistence for the AI layer: chat history, report edits, answer cache.

Two interchangeable backends behind one interface:

* ``SupabaseStore`` - used when SUPABASE_URL and SUPABASE_KEY are present.
  Talks to Supabase's PostgREST API with the standard library, so no SDK is
  required.  Suggested schema (run once in the Supabase SQL editor)::

      create table if not exists chat_messages (
        id bigint generated always as identity primary key,
        session_id text not null, role text not null, content text not null,
        meta jsonb default '{}'::jsonb, created_at timestamptz default now());
      create table if not exists report_edits (
        id bigint generated always as identity primary key,
        run_id text not null, el_id text not null, op text not null,
        html text default '', sort int default 0,
        updated_at timestamptz default now(),
        unique (run_id, el_id, op));
      create table if not exists ai_cache (
        key text primary key, value jsonb not null,
        created_at timestamptz default now());
      create table if not exists reports (
        run_id text primary key, studio text, label text, built_at text,
        meta jsonb default '{}'::jsonb, created_at timestamptz default now());
      create table if not exists app_config (
        key text primary key, value jsonb not null,
        updated_at timestamptz default now());

* ``SqliteStore``   - the default local fallback (``data/ai.sqlite3``), used
  automatically when Supabase is not configured or is unreachable.

All reads try Supabase first and silently degrade to SQLite, so a deployment
keeps working through transient network failures.
"""
from __future__ import annotations
import json, os, sqlite3, threading, time, urllib.parse, urllib.request, urllib.error


def _now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


# ------------------------------------------------------------------ supabase
class SupabaseStore:
    def __init__(self, url, key):
        self.rest = url.rstrip('/') + '/rest/v1'
        self.key = key
        self.schema_ok = True

    def _req(self, table, method='GET', query='', body=None, prefer=None):
        u = f'{self.rest}/{table}'
        if query:
            u += '?' + query
        headers = {'apikey': self.key, 'Authorization': f'Bearer {self.key}',
                   'Content-Type': 'application/json'}
        if prefer:
            headers['Prefer'] = prefer
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(u, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                raw = res.read().decode('utf-8', 'replace')
                return json.loads(raw) if raw.strip() else []
        except Exception:
            self.schema_ok = False
            raise

    # -- chat
    def save_message(self, session_id, role, content, meta=None):
        self._req('chat_messages', 'POST', body=dict(session_id=session_id, role=role,
                                                      content=content, meta=meta or {}),
                  prefer='return=minimal')

    def history(self, session_id, limit=8):
        q = urllib.parse.urlencode(dict(session_id=f'eq.{session_id}',
                                        order='created_at.asc', limit=str(limit * 4)))
        rows = self._req('chat_messages', query=q)
        return rows[-limit * 2:]

    # -- edits
    def upsert_edit(self, run_id, el_id, op, html='', sort=0):
        self._req('report_edits', 'POST',
                  query='on_conflict=run_id,el_id,op',
                  body=dict(run_id=run_id, el_id=el_id, op=op, html=html, sort=sort,
                            updated_at=_now()),
                  prefer='resolution=merge-duplicates,return=minimal')

    def delete_edit(self, run_id, el_id, op):
        q = urllib.parse.urlencode(dict(run_id=f'eq.{run_id}', el_id=f'eq.{el_id}', op=f'eq.{op}'))
        self._req('report_edits', 'DELETE', query=q)

    def edits(self, run_id):
        q = urllib.parse.urlencode(dict(run_id=f'eq.{run_id}', order='sort.asc'))
        return self._req('report_edits', query=q)

    # -- cache
    def cache_get(self, key):
        try:
            rows = self._req('ai_cache', query=urllib.parse.urlencode(dict(key=f'eq.{key}')))
            return rows[0]['value'] if rows else None
        except Exception:
            return None

    def cache_put(self, key, value):
        self._req('ai_cache', 'POST', query='on_conflict=key',
                  body=dict(key=key, value=value),
                  prefer='resolution=merge-duplicates,return=minimal')

    # -- reports
    def save_report(self, run_id, meta):
        self._req('reports', 'POST', query='on_conflict=run_id',
                  body=dict(run_id=run_id, studio=meta.get('studio', ''),
                            label=meta.get('label', ''), built_at=meta.get('built', ''),
                            meta=meta),
                  prefer='resolution=merge-duplicates,return=minimal')

    def report(self, run_id):
        rows = self._req('reports', query=urllib.parse.urlencode(dict(run_id=f'eq.{run_id}')))
        return rows[0] if rows else None

    def list_reports(self, studio=None, limit=24):
        q = dict(order='created_at.desc', limit=str(limit))
        if studio:
            q['studio'] = f'eq.{studio}'
        return self._req('reports', query=urllib.parse.urlencode(q))

    # -- config
    def config_put(self, key, value):
        self._req('app_config', 'POST', query='on_conflict=key',
                  body=dict(key=key, value=value, updated_at=_now()),
                  prefer='resolution=merge-duplicates,return=minimal')

    def config_get(self, key):
        rows = self._req('app_config', query=urllib.parse.urlencode(dict(key=f'eq.{key}')))
        return rows[0]['value'] if rows else None

    def config_all(self):
        return {r['key']: r['value'] for r in self._req('app_config')}


# ------------------------------------------------------------------ sqlite
class SqliteStore:
    SCHEMA = """
    create table if not exists chat_messages(
      id integer primary key autoincrement, session_id text, role text,
      content text, meta text default '{}', created_at text);
    create table if not exists report_edits(
      run_id text, el_id text, op text, html text default '', sort integer default 0,
      updated_at text, primary key(run_id, el_id, op));
    create table if not exists ai_cache(key text primary key, value text, created_at text);
    create table if not exists reports(
      run_id text primary key, studio text, label text, built_at text,
      meta text default '{}', created_at text);
    create table if not exists app_config(key text primary key, value text, updated_at text);
    """

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        with sqlite3.connect(path) as db:
            db.executescript(self.SCHEMA)

    def _conn(self):
        return sqlite3.connect(self.path)

    def save_message(self, session_id, role, content, meta=None):
        with self.lock, self._conn() as db:
            db.execute('insert into chat_messages(session_id, role, content, meta, created_at) values(?,?,?,?,?)',
                       (session_id, role, content, json.dumps(meta or {}), _now()))

    def history(self, session_id, limit=8):
        with self._conn() as db:
            rows = db.execute(
                'select role, content, meta from chat_messages where session_id=? order by id desc limit ?',
                (session_id, limit * 2)).fetchall()
        return [dict(role=r, content=c, meta=json.loads(m or '{}')) for r, c, m in reversed(rows)]

    def upsert_edit(self, run_id, el_id, op, html='', sort=0):
        with self.lock, self._conn() as db:
            db.execute('insert into report_edits(run_id, el_id, op, html, sort, updated_at) values(?,?,?,?,?,?) '
                       'on conflict(run_id, el_id, op) do update set html=excluded.html, '
                       'sort=excluded.sort, updated_at=excluded.updated_at',
                       (run_id, el_id, op, html, sort, _now()))

    def delete_edit(self, run_id, el_id, op):
        with self.lock, self._conn() as db:
            db.execute('delete from report_edits where run_id=? and el_id=? and op=?', (run_id, el_id, op))

    def edits(self, run_id):
        with self._conn() as db:
            rows = db.execute('select el_id, op, html, sort from report_edits where run_id=? order by sort, el_id',
                              (run_id,)).fetchall()
        return [dict(el_id=e, op=o, html=h, sort=s) for e, o, h, s in rows]

    def cache_get(self, key):
        with self._conn() as db:
            row = db.execute('select value from ai_cache where key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key, value):
        with self.lock, self._conn() as db:
            db.execute('insert into ai_cache(key, value, created_at) values(?,?,?) '
                       'on conflict(key) do update set value=excluded.value',
                       (key, json.dumps(value), _now()))

    # -- reports
    def save_report(self, run_id, meta):
        with self.lock, self._conn() as db:
            db.execute('insert into reports(run_id, studio, label, built_at, meta, created_at) values(?,?,?,?,?,?) '
                       'on conflict(run_id) do update set studio=excluded.studio, label=excluded.label, '
                       'built_at=excluded.built_at, meta=excluded.meta',
                       (run_id, meta.get('studio', ''), meta.get('label', ''), meta.get('built', ''),
                        json.dumps(meta), _now()))

    def report(self, run_id):
        with self._conn() as db:
            row = db.execute('select run_id, studio, label, built_at, meta from reports where run_id=?',
                             (run_id,)).fetchone()
        if not row:
            return None
        return dict(run_id=row[0], studio=row[1], label=row[2], built_at=row[3],
                    meta=json.loads(row[4] or '{}'))

    def list_reports(self, studio=None, limit=24):
        with self._conn() as db:
            if studio:
                rows = db.execute('select run_id, studio, label, built_at, meta from reports '
                                  'where studio=? order by created_at desc limit ?', (studio, limit)).fetchall()
            else:
                rows = db.execute('select run_id, studio, label, built_at, meta from reports '
                                  'order by created_at desc limit ?', (limit,)).fetchall()
        return [dict(run_id=r[0], studio=r[1], label=r[2], built_at=r[3], meta=json.loads(r[4] or '{}'))
                for r in rows]

    # -- config
    def config_put(self, key, value):
        with self.lock, self._conn() as db:
            db.execute('insert into app_config(key, value, updated_at) values(?,?,?) '
                       'on conflict(key) do update set value=excluded.value, updated_at=excluded.updated_at',
                       (key, json.dumps(value), _now()))

    def config_get(self, key):
        with self._conn() as db:
            row = db.execute('select value from app_config where key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def config_all(self):
        with self._conn() as db:
            rows = db.execute('select key, value from app_config').fetchall()
        return {k: json.loads(v) for k, v in rows}


# ------------------------------------------------------------------ facade
class Store:
    """Supabase when configured, SQLite otherwise; Supabase failures fall
    back to SQLite transparently."""

    def __init__(self, sqlite_path):
        url = os.environ.get('SUPABASE_URL', '').strip()
        key = os.environ.get('SUPABASE_KEY', '').strip() or os.environ.get('SUPABASE_SERVICE_KEY', '').strip()
        self.supa = SupabaseStore(url, key) if url and key else None
        self.local = SqliteStore(sqlite_path)
        self.backend = 'supabase' if self.supa else 'sqlite'

    def _try(self, fn, *a, **k):
        if self.supa:
            try:
                return fn(self.supa, *a, **k)
            except Exception:
                pass
        return fn(self.local, *a, **k)

    def save_message(self, session_id, role, content, meta=None):
        self.local.save_message(session_id, role, content, meta)
        if self.supa:
            try:
                self.supa.save_message(session_id, role, content, meta)
            except Exception:
                pass

    def history(self, session_id, limit=8):
        return self._try(lambda s: s.history(session_id, limit))

    def upsert_edit(self, run_id, el_id, op, html='', sort=0):
        self.local.upsert_edit(run_id, el_id, op, html, sort)
        if self.supa:
            try:
                self.supa.upsert_edit(run_id, el_id, op, html, sort)
            except Exception:
                pass

    def delete_edit(self, run_id, el_id, op):
        self.local.delete_edit(run_id, el_id, op)
        if self.supa:
            try:
                self.supa.delete_edit(run_id, el_id, op)
            except Exception:
                pass

    def edits(self, run_id):
        return self._try(lambda s: s.edits(run_id))

    def cache_get(self, key):
        v = self.local.cache_get(key)
        if v is None and self.supa:
            v = self.supa.cache_get(key)
        return v

    def cache_put(self, key, value):
        self.local.cache_put(key, value)
        if self.supa:
            try:
                self.supa.cache_put(key, value)
            except Exception:
                pass

    # -- reports: persisted so generated reviews survive and so the AI can be
    # handed prior periods for the same studio as comparison context.
    def save_report(self, run_id, meta):
        self.local.save_report(run_id, meta)
        if self.supa:
            try:
                self.supa.save_report(run_id, meta)
            except Exception:
                pass

    def report(self, run_id):
        return self._try(lambda s: s.report(run_id))

    def list_reports(self, studio=None, limit=24):
        return self._try(lambda s: s.list_reports(studio, limit))

    # -- config: user-made changes and settings (model choice, toggles); keys
    # themselves stay in the environment and are never stored here.
    def config_put(self, key, value):
        self.local.config_put(key, value)
        if self.supa:
            try:
                self.supa.config_put(key, value)
            except Exception:
                pass

    def config_get(self, key):
        return self._try(lambda s: s.config_get(key))

    def config_all(self):
        return self._try(lambda s: s.config_all())
