"""Start only local UI/model manager or explicitly requested cameras. No motion calls."""
import json,os,subprocess,time,sys,urllib.request,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=json.loads((R/'installation.json').read_text())
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def status(port):
 try:return json.load(opener.open(f'http://127.0.0.1:{port}/health',timeout=1))
 except Exception:return None

def server(key,port):
 app=Path(C[key]);state=status(port)
 if state:
  if state.get('root')!=str(app):raise RuntimeError(f'Port {port} is occupied by a different installation. Nothing stopped.')
  return
 # Bind errors leave any other service intact.
 runtime=app/'ui_runtime';runtime.mkdir(exist_ok=True)
 with (runtime/'offline_server.log').open('ab') as log:
  proc=subprocess.Popen([C['python'],'-B','-u',str(R/'tools/model_manager.py') if key=='manager' else str(app/'collection_ui_server.py'),'--port',str(port)],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
 for _ in range(80):
  if proc.poll() is not None:raise RuntimeError('Startup failed: '+str(runtime/'offline_server.log'))
  state=status(port)
  if state and state.get('root')==str(app):
   (runtime/(str(port)+'.pid')).write_text(str(proc.pid)+'\n');return
  time.sleep(.2)
 raise RuntimeError('Service not ready. Inspect '+str(runtime/'offline_server.log'))

if sys.argv[1]=='start':
 server('manager',8769);server('app',8779)
 print('OHT ready: http://127.0.0.1:8779 (no model loaded, no robot motion started)')
 browser=Path(shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser') or R/'browser/google-chrome')
 cmd=[str(browser),'--user-data-dir='+str(R/'browser_profile'),'--no-first-run','--no-default-browser-check','--app=http://127.0.0.1:8779'] if browser.exists() else ['xdg-open','http://127.0.0.1:8779']
 try:subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 except OSError:print('Open the URL in your installed Chrome/Chromium browser.')
elif sys.argv[1]=='cameras':
 script="from camera_resident import ensure; print(ensure())"
 subprocess.run([C['python'],'-B','-c',script],cwd=C['app'],check=True)
 print('Camera startup requested. Use OHT preview to view readiness; no robot connection started.')
else:raise SystemExit('Expected: start | cameras')
