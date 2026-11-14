"""Local reproducible API checks. Uses environment passwords; does not print secrets/tokens."""
import os,sys,json,urllib.request,urllib.error
BASE=os.environ.get('TRACKER_TEST_API','http://127.0.0.1:8091')
P1=os.environ.get('TRACKER_STUDENT_PASSWORD');P2=os.environ.get('TRACKER_STAFF_PASSWORD')
if not P1 or not P2:raise SystemExit('Set TRACKER_STUDENT_PASSWORD and TRACKER_STAFF_PASSWORD locally, or run manual UI tests')
def request(path,payload=None,token=None):
 data=None if payload is None else json.dumps(payload).encode()
 headers={'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(BASE+path,data=data,headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=5) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.load(e)

def check(label,result,expected):
 assert result[0]==expected,(label,result[0],expected)
 print(f'PASS {label}: HTTP {result[0]}')
check('Health',request('/health'),200)
check('Missing token',request('/summary'),401)
check('Wrong password',request('/login',{'username':'student','password':'not-the-correct-password'}),401)
student=request('/login',{'username':'student','password':P1});check('Student login',student,200)
staff=request('/login',{'username':'staff','password':P2});check('Staff login',staff,200)
s=student[1]['token'];t=staff[1]['token']
check('Authenticated summary',request('/summary',token=s),200)
check('Forbidden staff action',request('/assign',{'id':1,'reviewer':'Demo','deadline':'2026-11-20'},s),403)
check('Tampered token',request('/summary',token=s+'X'),401)
check('Staff token recognized',request('/summary',token=t),200)
check('Logout',request('/logout',{},s),200)
check('Revoked token',request('/summary',token=s),401)
print('Security smoke tests completed. No credential or token values printed.')
