"""Loopback model management adapter; no robot routes and no camera startup."""
import argparse,json,secrets,signal,sys,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
R=Path(__file__).resolve().parents[1];C=json.loads((R/'installation.json').read_text())
sys.path.insert(0,C['manager'])
from dagger_models import Models

def main():
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8769);args=p.parse_args()
 models=Models(Path(C['manager']));token=secrets.token_hex(32)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def reply(self,code,obj):
   raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def do_GET(self):
   if self.path=='/health':self.reply(200,dict(schema='oht-offline-model-manager-v1',root=C['manager']))
   elif self.path=='/api/session':self.reply(200,dict(token=token))
   elif self.path=='/api/status':self.reply(200,dict(policy=models.snapshot()))
   else:self.reply(404,dict(error='Not found'))
  def do_POST(self):
   if self.path!='/api/dagger':return self.reply(404,dict(error='No robot or camera commands are supported here'))
   if self.headers.get('Origin')!=f'http://127.0.0.1:{args.port}' or not secrets.compare_digest(self.headers.get('X-UI-Token',''),token):return self.reply(403,dict(error='Invalid origin or token'))
   try:
    n=int(self.headers.get('Content-Length','0'))
    if not 0<n<=4096:raise ValueError('Invalid body size')
    d=json.loads(self.rfile.read(n))
    if d.get('kind')!='load':raise ValueError('Only explicit model loading is supported')
    self.reply(200,models.load(d['model_id'],d['gpu'],d.get('execution','legacy')))
   except Exception as e:self.reply(400,dict(error=str(e)))
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
 def stop(*a):threading.Thread(target=server.shutdown,daemon=True).start()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 try:server.serve_forever()
 finally:server.server_close();models.close()
if __name__=='__main__':main()
