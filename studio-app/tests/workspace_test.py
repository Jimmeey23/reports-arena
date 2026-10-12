import importlib.util, json, tempfile, threading, unittest, urllib.request, urllib.error, time
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.workspace import Workspace, WorkspaceError
from engine.reader import enhance_report

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'workspace.db'
        self.store=Workspace(self.path)
        self.host='a'*32;self.guest='b'*32
    def tearDown(self):self.temp.cleanup()
    def test_persist_merge_and_private_notes(self):
        self.store.save(self.host,'r/report',{'notes':{'s':'Private strategy'},'edits':{'text-1':'Revised conclusion'}})
        self.store.save(self.host,'r/report',{'preferences':{'theme':'dark'},'annotations':{'s':'Discuss attendance'}})
        restored=Workspace(self.path).document(self.host,'r/report')
        self.assertEqual(restored['notes']['s'],'Private strategy')
        meeting=self.store.host(self.host,'r/report')
        guest=self.store.meeting(meeting['code'],self.guest)
        self.assertNotIn('notes',guest);self.assertNotIn('owner',guest)
        self.assertEqual(guest['edits']['text-1'],'Revised conclusion')
        self.assertEqual(self.store.document(self.guest,'r/report'),{})
        with self.assertRaises(WorkspaceError) as caught:self.store.update(meeting['code'],self.guest,{'scroll':.8})
        self.assertEqual(caught.exception.status,403)
        self.store.update(meeting['code'],self.host,{'section':'s','scroll':.75,'tables':[{'index':0,'filter':'member','sort':1,'descending':True}]})
        restored=Workspace(self.path).meeting(meeting['code'],self.guest)['view']
        self.assertEqual(restored['scroll'],.75)
        self.assertEqual(restored['tables'][0]['filter'],'member')
        self.store.update(meeting['code'],self.host,end=True)
        self.assertFalse(self.store.meeting(meeting['code'],self.guest)['active'])
    def test_reader_refresh_is_idempotent(self):
        html='<html><head></head><body><p>Evidence</p></body></html>'
        once=enhance_report(html)
        self.assertEqual(once,enhance_report(once))
        self.assertIn('Speaker workspace',once)
        self.assertIn('Guided session',once)

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server
        cls.server=server
        cls.temp=tempfile.TemporaryDirectory()
        cls.old={k:getattr(server,k) for k in ['DATA','UPLOADS','RUNS','WORKSPACE','STATE']}
        server.DATA=cls.temp.name;server.UPLOADS=str(Path(cls.temp.name)/'old');server.RUNS=str(Path(cls.temp.name)/'runs')
        Path(server.UPLOADS).mkdir();Path(server.RUNS).mkdir()
        server.WORKSPACE=Workspace(Path(cls.temp.name)/'workspace.db')
        server.STATE=dict(dataset=None,files=[],sig='',studios={},warnings=[],logs=[],jobs={},runs={})
        old=Path(server.UPLOADS)/'old.csv';old.write_text('Session ID,Capacity,Booked,CheckedIn,Date,Location,Class\n9,20,4,4,2026-09-01,Old studio,Barre\n')
        saved=Path(server.RUNS)/'saved';saved.mkdir()
        (saved/'manifest.json').write_text(json.dumps({'label':'Saved review','studio':'Bandra','chapters':[]}))
        (saved/'report.html').write_text('<html><head><title>Saved review</title></head><body><div class="wrap"><h2>Overview</h2><p>Original</p></div></body></html>')
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.url='http://127.0.0.1:'+str(cls.http.server_port)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close()
        for k,v in cls.old.items():setattr(cls.server,k,v)
        cls.temp.cleanup()
    def request(self,path,body=None,headers=None):
        request=urllib.request.Request(self.url+path,data=body,headers=headers or {},method='POST' if body is not None else 'GET')
        try:
            with urllib.request.urlopen(request) as r:return r.status,r.read()
        except urllib.error.HTTPError as e:return e.code,e.read()
    def test_empty_start_fresh_upload_isolation_and_generate(self):
        status,raw=self.request('/api/state');state=json.loads(raw)
        self.assertEqual(state['sources'],[]);self.assertEqual(len(state['runs']),1)
        csv='SessionID,Capacity,Booked,CheckedIn,Date,Location,Class,Trainer,Revenue,Time,Day\n'+''.join(f'{i},20,5,5,2026-09-{i:02d},Fresh studio,Barre,Instructor,1000,08:00,Monday\n' for i in range(1,7))
        body=('--test\r\nContent-Disposition: form-data; name="files"; filename="fresh.csv"\r\nContent-Type: text/csv\r\n\r\n'+csv+'\r\n--test--\r\n').encode()
        batch='c'*32;headers={'Content-Type':'multipart/form-data; boundary=test','X-Upload-Batch':batch}
        status,raw=self.request('/api/upload',body,headers);self.assertEqual(status,200)
        self.assertEqual([s['name'] for s in json.loads(raw)['state']['sources']],['fresh.csv'])
        _,raw=self.request('/api/state',headers={'X-Upload-Batch':'d'*32});self.assertEqual(json.loads(raw)['sources'],[])
        req=json.dumps({'studio':'Fresh studio','year':2026,'month':9,'chapters':['class']}).encode()
        status,_=self.request('/api/generate',req);self.assertEqual(status,400)
        status,raw=self.request('/api/generate',req,{'X-Upload-Batch':batch});self.assertEqual(status,200)
        jid=json.loads(raw)['job']
        for _ in range(100):
            _,raw=self.request('/api/job/'+jid);job=json.loads(raw)
            if job['state']!='running':break
            time.sleep(.05)
        self.assertEqual(job['state'],'done',job)
        status,html=self.request('/api/report/'+job['run']+'/report');self.assertEqual(status,200);self.assertIn(b'p57-tool-trigger',html);self.assertIn(b'id="p57-source-records"',html);self.assertIn(b'"total": 6',html)
        self.server.STATE['runs']={};self.server.scan_runs();self.assertIn(job['run'],self.server.STATE['runs'])
    def test_meeting_routes_and_durable_workspace(self):
        host={'X-P57-User':'e'*32};guest={'X-P57-User':'f'*32}
        status,raw=self.request('/api/meetings',json.dumps({'report':'saved/report'}).encode(),host);self.assertEqual(status,200)
        code=json.loads(raw)['code']
        status,raw=self.request('/api/workspace',json.dumps({'report':'saved/report','patch':{'notes':{'s':'Private'},'edits':{'text-0':'Edited'}}}).encode(),host);self.assertEqual(status,200)
        status,raw=self.request('/api/meetings/'+code,headers=guest);self.assertEqual(status,200);self.assertNotIn('notes',json.loads(raw))
        status,_=self.request('/api/meetings/'+code,json.dumps({'view':{'section':'s','scroll':.5}}).encode(),guest);self.assertEqual(status,403)
        status,_=self.request('/api/meetings/'+code,json.dumps({'view':{'section':'s','scroll':.5}}).encode(),host);self.assertEqual(status,200)
        self.server.WORKSPACE=Workspace(Path(self.temp.name)/'workspace.db')
        _,raw=self.request('/api/workspace?report=saved/report',headers=host);self.assertEqual(json.loads(raw)['edits']['text-0'],'Edited')
        status,_=self.request('/api/meetings',json.dumps({'report':'saved/../server'}).encode(),host);self.assertEqual(status,400)

    def test_ai_settings_use_llm_module(self):
        with patch.object(self.server.llm, 'configure') as configure, \
             patch.object(self.server.llm, 'status', return_value={'configured': True, 'model': 'test-model'}), \
             patch.object(self.server.AI_STORE, 'config_put') as config_put:
            status, raw = self.request('/api/ai/key', json.dumps({'model': 'test-model'}).encode())
            self.assertEqual(status, 200, raw)
            self.assertEqual(json.loads(raw), {'ok': True, 'configured': True, 'model': 'test-model'})
            configure.assert_called_once_with(key=None, model='test-model')
            self.assertEqual(config_put.call_args.args[0], 'ai')

    def test_raw_rejects_parent_directory(self):
        (Path(self.server.RUNS).parent/'secret.txt').write_text('do not serve')
        self.assertEqual(self.request('/api/raw/../secret.txt')[0], 404)
        self.assertEqual(self.request('/api/raw/saved/manifest.json')[0], 200)

    def test_ai_status_hides_endpoint(self):
        _, raw = self.request('/api/ai/status')
        self.assertNotIn('base', json.loads(raw)['llm'])

    def test_access_code_gate(self):
        no_redirect = urllib.request.build_opener(type('NoRedirect', (urllib.request.HTTPRedirectHandler,), {'redirect_request': lambda *a: None}))
        def call(path, body=None, headers=None):
            req = urllib.request.Request(self.url+path, data=body, headers=headers or {}, method='POST' if body is not None else 'GET')
            try:
                with no_redirect.open(req) as r: return r.status, r.headers, r.read()
            except urllib.error.HTTPError as e: return e.code, e.headers, e.read()
        with patch.object(self.server, 'ACCESS_CODE', 'letmein'):
            self.assertEqual(call('/api/health')[0], 200)
            self.assertEqual(call('/api/state')[0], 401)
            self.assertEqual(call('/api/ai/key', json.dumps({'base': 'https://evil.example'}).encode())[0], 401)
            status, headers, _ = call('/api/report/saved/report', headers={'Accept': 'text/html'})
            self.assertEqual(status, 303)
            self.assertTrue(headers['Location'].startswith('/api/login?next='))
            self.assertEqual(call('/api/login', b'code=wrong&next=/', {'Content-Type': 'application/x-www-form-urlencoded'})[0], 401)
            status, headers, _ = call('/api/login', b'code=letmein&next=//evil.example', {'Content-Type': 'application/x-www-form-urlencoded'})
            self.assertEqual(status, 303)
            self.assertEqual(headers['Location'], '/')
            cookie = headers['Set-Cookie'].split(';', 1)[0]
            self.assertIn('HttpOnly', headers['Set-Cookie'])
            self.assertEqual(call('/api/state', headers={'Cookie': cookie})[0], 200)
            self.assertEqual(call('/api/state', headers={'Cookie': 'p57_session=9999999999.forged'})[0], 401)
        with patch.object(self.server, 'ACCESS_CODE', 'rotated'):
            self.assertEqual(call('/api/state', headers={'Cookie': cookie})[0], 401)

    def test_download_path_and_legacy_query(self):
        for path in ('/api/download/saved', '/api/download?run=saved'):
            status, html = self.request(path)
            self.assertEqual(status, 200, html)
            self.assertIn(b'Saved review', html)
        self.assertEqual(self.request('/api/download/missing')[0], 404)

if __name__=='__main__':unittest.main()
