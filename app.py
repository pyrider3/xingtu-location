from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import json,subprocess,os,signal,threading,time,shutil,tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
D=Path(__file__).resolve().parent
TOOL=Path(os.environ.get('PYMOBILEDEVICE3', str(D/'.venv/bin/pymobiledevice3')))
ROUTE=Path(tempfile.gettempdir()) / ('xingtu-location-' + str(os.getuid()) + '.gpx')
state={'process':None,'location':None,'log':[],'active':False,'phase':'idle','last_sent':None}; lock=threading.Lock()
cancel=None

def stop():
 global cancel
 if cancel: cancel.set()
 p=state['process']
 if p and p.poll() is None:
  p.terminate()
  try:p.wait(timeout=4)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 state.update(process=None,active=False,phase='idle')
 cancel=None

def supervise(event, lat, lon):
 while not event.is_set():
  state['phase']='connecting'
  try:
   p=subprocess.Popen([str(TOOL),'-v','developer','dvt','simulate-location','play','--userspace',str(ROUTE)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
   state['process']=p
   for line in p.stdout:
    if event.is_set(): break
    line=line.strip(); state['log'].append(line); state['log'][:]=state['log'][-20:]
    if 'waiting for 5.000s' in line:
     state['phase']='sending';state['last_sent']=time.time()
   p.wait()
  except Exception as e: state['log'].append(str(e))
  if not event.is_set():
   state['phase']='retrying'
   event.wait(5)

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def send(self,obj,code=200):
  data=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
 def do_GET(self):
  if self.path=='/':
   data=(D/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data);return
  if self.path=='/status':
   p=state['process']; connected=subprocess.run(['idevice_id','-l'],capture_output=True,text=True,timeout=5).stdout.strip()!=''
   self.send({'connected':connected,'running':state['active'],'phase':state['phase'],'last_sent':state['last_sent'],'location':state['location'],'log':state['log'][-5:]});return
  self.send({},404)
 def do_POST(self):
  if self.headers.get('Origin') not in (None,'http://127.0.0.1:8765','http://localhost:8765'):return self.send({'error':'请求来源不允许'},403)
  global cancel
  try:
   body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
   with lock:
    if self.path=='/set':
     lat=float(body['lat']);lon=float(body['lon'])
     if not (-90<=lat<=90 and -180<=lon<=180):raise ValueError('坐标超出范围')
     stop(); t=datetime(2026,1,1,tzinfo=timezone.utc)
     pts=''.join(f'<trkpt lat="{lat}" lon="{lon}"><time>{(t+timedelta(seconds=5*i)).isoformat()}</time></trkpt>' for i in range(17281))
     ROUTE.write_text('<gpx><trk><trkseg>'+pts+'</trkseg></trk></gpx>')
     cancel=threading.Event()
     state.update(process=None,location={'lat':lat,'lon':lon},log=[],active=True,phase='connecting',last_sent=None)
     threading.Thread(target=supervise,args=(cancel,lat,lon),daemon=True).start();self.send({'ok':True})
    elif self.path=='/stop':
     stop();state['location']=None
     try:
      result=subprocess.run([str(TOOL),'developer','dvt','simulate-location','clear','--userspace'],capture_output=True,timeout=12)
      self.send({'ok':True,'cleared':result.returncode == 0})
     except Exception: self.send({'ok':True,'cleared':False})
    elif self.path=='/shutdown':
     stop();state['location']=None
     try:
      result=subprocess.run([str(TOOL),'developer','dvt','simulate-location','clear','--userspace'],capture_output=True,timeout=12)
      cleared=result.returncode == 0
     except Exception: cleared=False
     self.send({'ok':True,'cleared':cleared})
     threading.Thread(target=self.server.shutdown,daemon=True).start()
    else:self.send({},404)
  except Exception as e:self.send({'error':str(e)},400)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
