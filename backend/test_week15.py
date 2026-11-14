"""Week 15 repeatable API regression suite, offline localhost with isolated temp SQLite DB.
Run: python -m unittest -v test_week15.py
No submitted record, account secret, or personal data is used.
"""
import http.client
import importlib.util
import json
import logging
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name('server.py')
spec = importlib.util.spec_from_file_location('research_tracker_week15', MODULE_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        app.DB = Path(cls.tmp.name) / 'isolated_test.db'
        app.setup()
        # Fixed test-only credentials generated and held exclusively in memory.
        cls.password_student = 'TestStudentOnly_2026!'
        cls.password_staff = 'TestStaffOnly_2026!'
        with patch.dict(app.os.environ, {
            'TRACKER_STUDENT_PASSWORD': cls.password_student,
            'TRACKER_STAFF_PASSWORD': cls.password_staff,
        }):
            app.configure_users()
        cls.httpd = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.port = cls.httpd.server_port
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        _, cls.student = cls.request('POST','/login',{'username':'student','password':cls.password_student})
        _, cls.staff = cls.request('POST','/login',{'username':'staff','password':cls.password_staff})

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.thread.join(timeout=3); cls.tmp.cleanup()

    @classmethod
    def request(cls, method, path, body=None, token=None, content_type='application/json'):
        conn = http.client.HTTPConnection('127.0.0.1',cls.port,timeout=5)
        headers = {'Content-Type':content_type}
        if token: headers['Authorization'] = 'Bearer '+token
        data = json.dumps(body).encode() if body is not None else None
        conn.request(method,path,body=data,headers=headers)
        r = conn.getresponse(); raw = r.read(); status = r.status
        conn.close()
        return status, json.loads(raw) if raw else None

    def submit(self, title='Demo Title', student='Demo Student'):
        return self.request('POST','/submissions',{'title':title,'student':student},self.student['token'])

    def test_01_health(self):
        status, res=self.request('GET','/health'); self.assertEqual(status,200); self.assertTrue(res['ok'])
    def test_02_missing_auth(self):
        self.assertEqual(self.request('GET','/summary')[0],401)
    def test_03_wrong_password(self):
        self.assertEqual(self.request('POST','/login',{'username':'student','password':'bad'})[0],401)
    def test_04_login(self):
        self.assertEqual(self.request('GET','/summary',token=self.student['token'])[0],200)
    def test_05_forbidden_role(self):
        self.assertEqual(self.request('POST','/assign',{'id':1,'reviewer':'Test','deadline':'2026-12-01'},self.student['token'])[0],403)
    def test_06_tampered_token(self):
        self.assertEqual(self.request('GET','/summary',token=self.student['token']+'bad')[0],401)
    def test_07_empty_title(self):
        self.assertEqual(self.submit(title='')[0],400)
    def test_08_boundary_150_title(self):
        self.assertEqual(self.submit(title='A'*150)[0],201)
    def test_09_boundary_151_title(self):
        self.assertEqual(self.submit(title='A'*151)[0],400)
    def test_10_non_string_title(self):
        self.assertEqual(self.submit(title=123)[0],400)
    def test_11_non_string_student(self):
        self.assertEqual(self.submit(student={'name':'demo'})[0],400)
    def test_12_wrong_content_type(self):
        self.assertEqual(self.request('POST','/login',{'username':'student','password':self.password_student},content_type='text/plain')[0],400)
    def test_13_invalid_assignment_date(self):
        _, row=self.submit(title='Date Test')
        self.assertEqual(self.request('POST','/assign',{'id':row['id'],'reviewer':'Demo Reviewer','deadline':'2026-99-99'},self.staff['token'])[0],400)
    def test_14_positive_assignment(self):
        _, row=self.submit(title='Assignment Test')
        self.assertEqual(self.request('POST','/assign',{'id':row['id'],'reviewer':'Demo Reviewer','deadline':'2026-12-01'},self.staff['token'])[0],200)
    def test_15_dependency_transient_recovery(self):
        _, row=self.submit(title='Transient Test')
        status,data=self.request('POST','/automation/run',{'id':row['id'],'simulate':'transient'},self.staff['token'])
        self.assertEqual(status,200);self.assertEqual(data['attempts'],2);self.assertTrue(data['recovered'])
    def test_16_dependency_permanent_manual_review(self):
        _, row=self.submit(title='Permanent Test')
        status,data=self.request('POST','/automation/run',{'id':row['id'],'simulate':'permanent'},self.staff['token'])
        self.assertEqual(status,200);self.assertEqual(data['result'],'manual_review')
    def test_17_invalid_id_type(self):
        self.assertEqual(self.request('POST','/revision',{'id':'1'},self.student['token'])[0],400)
    def test_18_logout_rejects_token(self):
        _, login=self.request('POST','/login',{'username':'student','password':self.password_student})
        self.assertEqual(self.request('POST','/logout',{},login['token'])[0],200)
        self.assertEqual(self.request('GET','/summary',token=login['token'])[0],401)
    def test_19_path_log_sanitized(self):
        with patch.object(app.logging,'info') as log:
            self.request('GET','/health?private_marker=DO_NOT_LOG')
            rendered=' '.join(str(c) for c in log.call_args_list)
            self.assertNotIn('DO_NOT_LOG',rendered)
    def test_20_health_origin_preflight(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        conn.request('OPTIONS','/submissions',headers={'Origin':'http://localhost:50000'})
        r=conn.getresponse();r.read();self.assertEqual(r.status,204);conn.close()

if __name__ == '__main__': unittest.main(verbosity=2)
