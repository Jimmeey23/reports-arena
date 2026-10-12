"""Exercise report deletion through HTTP with disposable files and databases."""
import json, tempfile, threading, unittest, urllib.request, urllib.error, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from engine.workspace import Workspace, WorkspaceError
from ai.store import Store

class DeleteReportTest(unittest.TestCase):
    def test_http_delete_cleans_report_records_and_survives_rescan(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = server.RUNS, server.WORKSPACE, server.AI_STORE, server.STATE, server.ACCESS_CODE
            try:
                server.RUNS = str(Path(tmp)/'runs');Path(server.RUNS).mkdir()
                server.WORKSPACE = Workspace(Path(tmp)/'workspace.sqlite3')
                server.AI_STORE = Store(str(Path(tmp)/'ai.sqlite3'));server.AI_STORE.supa=None
                server.ACCESS_CODE='';server.STATE={**server.STATE,'runs':{}}
                rid='disposable-report';other='disposable-report-extra'
                for run in (rid,other):
                    d=Path(server.RUNS)/run;d.mkdir();(d/'manifest.json').write_text(json.dumps(dict(label='Test',studio='Test',chapters=[])))
                    (d/'report.html').write_text('<body>Test</body>');server.AI_STORE.save_report(run,dict(studio='Test',label='Test'))
                source=Path(tmp)/'source.csv';source.write_text('keep')
                user='a'*32;server.WORKSPACE.save(user,rid+'/report',{'notes':{'one':'private'}})
                server.WORKSPACE.save(user,other+'/report',{'notes':{'one':'retain'}})
                meeting=server.WORKSPACE.host(user,rid+'/report')
                server.AI_STORE.upsert_edit(rid,'one','set','old')
                server.AI_STORE.save_message(rid+':test','user','Remove this')
                server.AI_STORE.save_message(other+':test','user','Keep this')
                http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
                worker=threading.Thread(target=http.serve_forever,daemon=True);worker.start()
                def post(body,origin=None):
                    headers={'Content-Type':'application/json'}
                    if origin:headers['Origin']=origin
                    req=urllib.request.Request(f'http://127.0.0.1:{http.server_port}/api/reports/delete',data=json.dumps(body).encode(),headers=headers)
                    try:
                        with urllib.request.urlopen(req) as r:return r.status,json.load(r)
                    except urllib.error.HTTPError as e:return e.code,json.load(e)
                try:
                    self.assertEqual(post({'run':rid})[0],400)
                    self.assertEqual(post({'run':'../escape','confirmation':'../escape'})[0],400)
                    self.assertEqual(post({'run':rid,'confirmation':rid},'https://other.test')[0],403)
                    self.assertEqual(post({'run':rid,'confirmation':rid})[0],200)
                    self.assertFalse((Path(server.RUNS)/rid).exists())
                    self.assertIsNone(server.AI_STORE.report(rid));self.assertEqual(server.AI_STORE.edits(rid),[])
                    self.assertEqual(server.AI_STORE.history(rid+':test'),[])
                    self.assertEqual(len(server.AI_STORE.history(other+':test')),1)
                    self.assertEqual(server.WORKSPACE.document(user,rid+'/report'),{})
                    with self.assertRaises(WorkspaceError):server.WORKSPACE.meeting(meeting['code'],user)
                    with self.assertRaises(WorkspaceError):server.WORKSPACE.save(user,rid+'/report',{'notes':{}})
                    self.assertTrue(source.exists());self.assertIsNotNone(server.AI_STORE.report(other))
                    self.assertEqual(server.WORKSPACE.document(user,other+'/report')['notes']['one'],'retain')
                    server.WORKSPACE=Workspace(Path(tmp)/'workspace.sqlite3')
                    self.assertIn(rid,server.WORKSPACE.deleted_reports());self.assertNotIn(rid,server.scan_runs())
                    self.assertEqual(post({'run':rid,'confirmation':rid})[0],404)
                finally:http.shutdown();http.server_close()
            finally:server.RUNS,server.WORKSPACE,server.AI_STORE,server.STATE,server.ACCESS_CODE=old

if __name__=='__main__':unittest.main()
