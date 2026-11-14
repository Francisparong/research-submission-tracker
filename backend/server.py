"""Week 13 EDUCATIONAL prototype. Demo role header is NOT secure authentication."""
import json, os, sqlite3, datetime, logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
BASE=Path(__file__).resolve().parent
DB=BASE/'tracker.db'
logging.basicConfig(level=logging.INFO, format='%(message)s')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def connect():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def setup():
 with connect() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS submissions(id INTEGER PRIMARY KEY, title TEXT NOT NULL, student TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'submitted',version INTEGER NOT NULL DEFAULT 1,reviewer TEXT,deadline TEXT,created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, submission_id INTEGER, event_type TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL);''')
def event(c,sid,typ,attempt,status,detail):
 c.execute('INSERT INTO events(submission_id,event_type,attempt,status,detail,created_at) VALUES(?,?,?,?,?,?)',(sid,typ,attempt,status,detail,now()))
 logging.info(json.dumps({'time':now(),'submission_id':sid,'event':typ,'attempt':attempt,'status':status,'detail':detail}))
class Handler(BaseHTTPRequestHandler):
 def end_headers(self):
  self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Content-Type, X-Demo-Role');self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS');super().end_headers()
 def do_OPTIONS(self):self.send_response(204);self.end_headers()
 def respond(self,code,data):
  b=json.dumps(data).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def body(self):
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n>10000:raise ValueError('request too large')
   obj=json.loads(self.rfile.read(n));assert isinstance(obj,dict);return obj
  except Exception:raise ValueError('Invalid JSON object')
 def role(self):return self.headers.get('X-Demo-Role','student')
 def do_GET(self):
  path=urlparse(self.path).path
  with connect() as c:
   if path=='/health':return self.respond(200,{'ok':True,'mode':'week13-demo'})
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
   with connect() as c:
    if path=='/submissions':
     if self.role()!='student':return self.respond(403,{'error':'Demo student role required'})
     title=str(b.get('title','')).strip(); student=str(b.get('student','')).strip()
     if not title or not student or len(title)>150:return self.respond(400,{'error':'title and student required; title max 150 characters'})
     cur=c.execute('INSERT INTO submissions(title,student,created_at) VALUES(?,?,?)',(title,student,now()))
     event(c,cur.lastrowid,'version_status',1,'success','v1 submitted')
     return self.respond(201,{'id':cur.lastrowid,'status':'submitted','version':1})
    if path=='/assign':
     if self.role()!='staff':return self.respond(403,{'error':'Demo staff role required'})
     sid=int(b['id']); reviewer=str(b.get('reviewer','')).strip();deadline=str(b.get('deadline','')).strip()
     if not reviewer or not deadline:return self.respond(400,{'error':'reviewer and YYYY-MM-DD deadline required'})
     datetime.date.fromisoformat(deadline)
     cur=c.execute("UPDATE submissions SET reviewer=?,deadline=?,status='under_review' WHERE id=?",(reviewer,deadline,sid))
     if not cur.rowcount:return self.respond(404,{'error':'submission not found'})
     event(c,sid,'review_assignment',1,'success',f'assigned to {reviewer}, deadline {deadline}')
     return self.respond(200,{'id':sid,'status':'under_review'})
    if path=='/revision':
     if self.role()!='student':return self.respond(403,{'error':'Demo student role required'})
     sid=int(b['id']);cur=c.execute("UPDATE submissions SET version=version+1,status='resubmitted' WHERE id=?",(sid,))
     if not cur.rowcount:return self.respond(404,{'error':'submission not found'})
     version=c.execute('SELECT version FROM submissions WHERE id=?',(sid,)).fetchone()[0]
     event(c,sid,'version_status',1,'success',f'v{version} resubmitted')
     return self.respond(200,{'id':sid,'version':version,'status':'resubmitted'})
    if path=='/automation/run':
     if self.role()!='staff':return self.respond(403,{'error':'Demo staff role required'})
     sid=int(b['id']);fault=b.get('simulate','none')
     if fault not in ('none','transient','permanent'):return self.respond(400,{'error':'simulate must be none, transient, or permanent'})
     row=c.execute('SELECT * FROM submissions WHERE id=?',(sid,)).fetchone()
     if not row:return self.respond(404,{'error':'submission not found'})
     overdue=bool(row['deadline'] and row['deadline']<datetime.date.today().isoformat())
     typ='overdue_escalation' if overdue else 'deadline_reminder'
     # Demonstrates bounded maximum of 3 attempts and human review, NOT external email delivery.
     for attempt in range(1,4):
      fail=(fault=='permanent' or (fault=='transient' and attempt==1))
      if fail:
       event(c,sid,typ,attempt,'failed','simulated dependency unavailable')
      else:
       event(c,sid,typ,attempt,'success','demo notification recorded (not sent externally)')
       return self.respond(200,{'id':sid,'event':typ,'attempts':attempt,'result':'success','recovered':attempt>1})
     event(c,sid,typ,3,'manual_review','max 3 attempts reached; human follow-up needed')
     return self.respond(200,{'id':sid,'event':typ,'attempts':3,'result':'manual_review'})
   self.respond(404,{'error':'Not found'})
  except (ValueError,KeyError,TypeError,AssertionError) as ex:self.respond(400,{'error':str(ex)})
if __name__=='__main__':
 setup(); print('Research Submission Tracker API at http://127.0.0.1:8091');ThreadingHTTPServer(('127.0.0.1',8091),Handler).serve_forever()
