"""Week 14 educational prototype: authenticated localhost API. TLS required before deployment."""
import os, sys, json, secrets, hashlib, hmac, datetime, sqlite3, logging, ssl, re, getpass
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from threading import Lock
BASE=Path(__file__).resolve().parent
DB=BASE/'tracker.db'
HOST='127.0.0.1'; PORT=int(os.environ.get('TRACKER_PORT','8091'))
TTL=int(os.environ.get('TRACKER_SESSION_SECONDS','900'))
if not 5<=TTL<=86400: raise RuntimeError('TRACKER_SESSION_SECONDS must be between 5 and 86400')
ORIGIN_RE=re.compile(r'^http://(localhost|127\.0\.0\.1):\d{2,5}$')
logging.basicConfig(level=logging.INFO,format='%(message)s')
SESSIONS={}; LOCK=Lock(); USERS={}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def connect():
 c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;return c
def setup():
 with connect() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS submissions(id INTEGER PRIMARY KEY,title TEXT NOT NULL,student TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'submitted',version INTEGER NOT NULL DEFAULT 1,reviewer TEXT,deadline TEXT,created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, submission_id INTEGER,event_type TEXT NOT NULL,attempt INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL,detail TEXT,created_at TEXT NOT NULL);''')
def event(c,sid,typ,attempt,status,detail):
 c.execute('INSERT INTO events(submission_id,event_type,attempt,status,detail,created_at) VALUES(?,?,?,?,?,?)',(sid,typ,attempt,status,detail,now()))
 logging.info(json.dumps({'time':now(),'submission_id':sid,'event':typ,'attempt':attempt,'status':status,'detail':detail}))
def configure_users():
 for user in ('student','staff'):
  value=os.environ.get('TRACKER_'+user.upper()+'_PASSWORD')
  if not value:
   if not sys.stdin.isatty():raise RuntimeError('Set TRACKER_STUDENT_PASSWORD and TRACKER_STAFF_PASSWORD using environment variables')
   value=getpass.getpass('Enter local '+user+' demo password (not echoed): ')
  if len(value)<12 or len(value)>128:raise RuntimeError(user+' demo password must be 12-128 characters')
  salt=secrets.token_bytes(16);USERS[user]=(salt,hashlib.scrypt(value.encode(),salt=salt,n=2**14,r=8,p=1))
  del value

def authenticate(user,password):
 stored=USERS.get(user)
 if not stored:return False
 salt,digest=stored
 return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1),digest)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args):logging.info('%s %s'%(self.client_address[0],fmt%args))
 def end_headers(self):
  origin=self.headers.get('Origin','')
  if ORIGIN_RE.fullmatch(origin):
   self.send_header('Access-Control-Allow-Origin',origin);self.send_header('Vary','Origin')
   self.send_header('Access-Control-Allow-Headers','Content-Type, Authorization')
   self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
  self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
  super().end_headers()
 def do_OPTIONS(self):
  if not ORIGIN_RE.fullmatch(self.headers.get('Origin','')):return self.respond(403,{'error':'Origin not allowed'})
  self.send_response(204);self.end_headers()
 def respond(self,code,data):
  content=json.dumps(data).encode('utf8');self.send_response(code)
  self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
 def body(self):
  n=int(self.headers.get('Content-Length','0'))
  if n<=0 or n>8192:raise ValueError('Invalid request size')
  payload=json.loads(self.rfile.read(n))
  if not isinstance(payload,dict):raise ValueError('Expected JSON object')
  return payload
 def principal(self):
  header=self.headers.get('Authorization','')
  if not header.startswith('Bearer '):return (None,'missing')
  token=header[7:].strip()
  if not token:return (None,'invalid')
  with LOCK:
   record=SESSIONS.get(hashlib.sha256(token.encode()).hexdigest())
   if record is None:return (None,'invalid')
   role,expiry=record
   if datetime.datetime.now(datetime.timezone.utc).timestamp()>=expiry:
    return (None,'expired')
  return (role,None)
 def require(self,role=None):
  principal,err=self.principal()
  if err:return self.respond(401,{'error':'Token '+err})
  if role and principal!=role:return self.respond(403,{'error':'Forbidden for this role'})
  return principal
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/health':return self.respond(200,{'ok':True,'mode':'week14-auth-demo','transport':'https' if isinstance(self.connection,ssl.SSLSocket) else 'http-local-only'})
  if not isinstance(self.require(),str):return
  with connect() as c:
   if path=='/submissions':return self.respond(200,[dict(x) for x in c.execute('SELECT * FROM submissions ORDER BY id DESC')])
   if path=='/events':return self.respond(200,[dict(x) for x in c.execute('SELECT * FROM events ORDER BY id DESC LIMIT 100')])
   if path=='/summary':
    rows=[dict(x) for x in c.execute('SELECT status,COUNT(*) AS count FROM submissions GROUP BY status')]
    return self.respond(200,{'total':sum(x['count'] for x in rows),'by_status':rows,'manual_review':c.execute("SELECT COUNT(*) FROM events WHERE status='manual_review'").fetchone()[0]})
  self.respond(404,{'error':'Not found'})
 def do_POST(self):
  path=urlparse(self.path).path
  try:
   b=self.body()
   if path=='/login':
    username=b.get('username');password=b.get('password')
    if not isinstance(username,str) or not isinstance(password,str):return self.respond(400,{'error':'Invalid login payload'})
    if len(password)>128:return self.respond(400,{'error':'Invalid login payload'})
    if not authenticate(username,password):return self.respond(401,{'error':'Invalid credentials'})
    token=secrets.token_urlsafe(32)
    expires=datetime.datetime.now(datetime.timezone.utc).timestamp()+TTL
    with LOCK:SESSIONS[hashlib.sha256(token.encode()).hexdigest()]=(username,expires)
    return self.respond(200,{'token':token,'role':username,'expires_in':TTL})
   if path=='/logout':
    _,err=self.principal()
    if err:return self.respond(401,{'error':'Unauthorized'})
    key=hashlib.sha256(self.headers['Authorization'][7:].strip().encode()).hexdigest()
    with LOCK:SESSIONS.pop(key,None)
    return self.respond(200,{'ok':True})
   role=self.require('staff' if path in ('/assign','/automation/run') else 'student' if path in ('/submissions','/revision') else None)
   if not isinstance(role,str):return
   with connect() as c:
    if path=='/submissions':
     title=str(b.get('title','')).strip();student=str(b.get('student','')).strip()
     if not title or not student or len(title)>150 or len(student)>100:return self.respond(400,{'error':'title and student required; max lengths 150/100'})
     cur=c.execute('INSERT INTO submissions(title,student,created_at) VALUES(?,?,?)',(title,student,now()))
     event(c,cur.lastrowid,'version_status',1,'success','v1 submitted');return self.respond(201,{'id':cur.lastrowid,'status':'submitted','version':1})
    if path=='/assign':
     sid=int(b['id']);reviewer=str(b.get('reviewer','')).strip();deadline=str(b.get('deadline','')).strip()
     if not reviewer or len(reviewer)>100:raise ValueError('reviewer required; maximum 100 characters')
     datetime.date.fromisoformat(deadline)
     cur=c.execute("UPDATE submissions SET reviewer=?,deadline=?,status='under_review' WHERE id=?",(reviewer,deadline,sid))
     if not cur.rowcount:return self.respond(404,{'error':'submission not found'})
     event(c,sid,'review_assignment',1,'success',f'assigned reviewer; deadline {deadline}')
     return self.respond(200,{'id':sid,'status':'under_review'})
    if path=='/revision':
     sid=int(b['id']);cur=c.execute("UPDATE submissions SET version=version+1,status='resubmitted' WHERE id=?",(sid,))
     if not cur.rowcount:return self.respond(404,{'error':'submission not found'})
     v=c.execute('SELECT version FROM submissions WHERE id=?',(sid,)).fetchone()[0];event(c,sid,'version_status',1,'success',f'v{v} resubmitted')
     return self.respond(200,{'id':sid,'version':v,'status':'resubmitted'})
    if path=='/automation/run':
     sid=int(b['id']);fault=b.get('simulate','none')
     if fault not in ('none','transient','permanent'):return self.respond(400,{'error':'invalid simulate mode'})
     row=c.execute('SELECT * FROM submissions WHERE id=?',(sid,)).fetchone()
     if not row:return self.respond(404,{'error':'submission not found'})
     typ='overdue_escalation' if row['deadline'] and row['deadline']<datetime.date.today().isoformat() else 'deadline_reminder'
     for attempt in range(1,4):
      if fault=='permanent' or (fault=='transient' and attempt==1):event(c,sid,typ,attempt,'failed','simulated dependency unavailable')
      else:
       event(c,sid,typ,attempt,'success','demo notification recorded (not sent externally)')
       return self.respond(200,{'id':sid,'event':typ,'attempts':attempt,'result':'success','recovered':attempt>1})
     event(c,sid,typ,3,'manual_review','max 3 attempts reached; human follow-up needed')
     return self.respond(200,{'id':sid,'result':'manual_review','attempts':3})
   return self.respond(404,{'error':'Not found'})
  except (ValueError,TypeError,KeyError,OverflowError,json.JSONDecodeError):return self.respond(400,{'error':'Invalid request'})
if __name__=='__main__':
 configure_users();setup()
 srv=ThreadingHTTPServer((HOST,PORT),Handler)
 cert=os.environ.get('TRACKER_TLS_CERT');key=os.environ.get('TRACKER_TLS_KEY')
 if bool(cert)!=bool(key):raise RuntimeError('Provide both TRACKER_TLS_CERT and TRACKER_TLS_KEY')
 if cert:
  ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2
  ctx.load_cert_chain(certfile=cert,keyfile=key);srv.socket=ctx.wrap_socket(srv.socket,server_side=True)
 print(('HTTPS' if cert else 'HTTP LOCAL DEVELOPMENT ONLY')+f' Research Tracker at {HOST}:{PORT}',flush=True)
 srv.serve_forever()
