"""Offline import/dependency checks only. Does not open cameras or connect to UR."""
import json,os,platform,shutil,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];C=json.loads((R/'installation.json').read_text());checks=[]
def record(name,ok,detail,required=True):
 checks.append(dict(name=name,ok=ok,detail=detail,required=required));print(('PASS' if ok else 'FAIL' if required else 'INFO')+' | '+name+' | '+str(detail))
def run(name,python,code,required=True,env=None):
 try:
  r=subprocess.run([python,'-B','-c',code],capture_output=True,text=True,timeout=50,env={**os.environ,**(env or {})})
  record(name,r.returncode==0,(r.stdout+r.stderr).strip()[-2500:],required)
 except Exception as e:record(name,False,str(e),required)
record('CPU',platform.machine()=='x86_64',platform.machine())
os_info=Path('/etc/os-release').read_text();record('OS baseline', 'VERSION_ID="20.04"' in os_info,os_info.splitlines()[:4],False)
record('Storage >= 30 GiB free',shutil.disk_usage(C['data_root']).free>=30*1024**3,C['data_root'],False)
run('Control',C['python'],"import numpy,scipy,serial,dynamixel_sdk;print(numpy.__version__,scipy.__version__)")
run('Private RTDE',C['python'],"import sys;sys.path.insert(0,"+repr(C['app']+'/teleop/sdk')+");import rtde_control;print(rtde_control.__file__);assert rtde_control.CODEX_NO_AUTO_RECONNECT;print(rtde_control.CODEX_GUARD_PATCH_VERSION)")
run('RealSense RGBD',C['camera_python'],"import cv2,numpy,pyrealsense2;print(cv2.__version__,numpy.__version__)")
run('Calibration',C['calibration_python'],"import cv2,yaml,scipy;assert hasattr(cv2,'aruco');print(cv2.__version__)")
run('ZED (import only)',C['zed_python'],"import numpy,cv2,pyzed.sl;print(pyzed.sl.Camera.get_sdk_version())")
# JAX CPU import only, no large model or GPU initialization during this check.
run('Policy libraries (CPU only)',C['model_python'],"import jax,flax,orbax.checkpoint,sentencepiece,openpi,openpi_client;print('jax',jax.__version__)",env={'JAX_PLATFORMS':'cpu','LD_LIBRARY_PATH':''})
run('T42 metadata',C['python'],"import sys;sys.path.insert(0,"+repr(C['app'])+");import json;from dagger_contracts import checkpoint;r=json.load(open("+repr(C['manager']+'/dagger_models.json')+"));entries=[checkpoint(x['path']) for x in r.values()];e=next(x for x in entries if x['spec']['id'].startswith('T42_') and x['step']==20000);print(e['spec']['id'],e['step'],'registered models',len(entries))")
try:
 p=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],text=True,capture_output=True,timeout=10)
 record('NVIDIA driver',p.returncode==0,(p.stdout+p.stderr).strip())
except Exception as e:record('NVIDIA driver',False,str(e))
record('GELLO serial path',bool(list(Path('/dev/serial/by-id').glob('*FTDI*'))),[str(p) for p in Path('/dev/serial/by-id').glob('*')],False)
record('Browser',bool(shutil.which('google-chrome') or shutil.which('chromium') or (R/'browser/google-chrome').exists()),'Chrome/Chromium for operator UI')
(R/'environment_report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print('Report:',R/'environment_report.json');print('No camera capture, robot connection, or model inference was started.')
raise SystemExit(1 if any(not c['ok'] and c['required'] for c in checks) else 0)
