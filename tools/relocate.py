"""Relocate a fresh offline copy. No network, device access or source-machine edits."""
import argparse,json,os,shlex,html
from pathlib import Path

BASE='home/samsung/codex_work/gello_shadow_session_20260921T061545_594387Z'
APP='oht_replay_unified_v1_20261030'
MODEL='media/samsung/samsung/oht_pi05_validation'

def configure(root,data):
 root=Path(root).resolve();data=Path(data).expanduser().resolve()
 base=root/BASE;app=base/APP
 replacements={p:str(root/p.lstrip('/')) for p in ['/home/samsung','/media/samsung/samsung/oht_pi05_validation','/usr/local/zed','/usr/local/cuda-11.8']}
 def rewrite(s):
  for old,new in replacements.items():s=s.replace(old,new)
  return s
 # Only executable/configuration text; never rewrite model/trajectory identities.
 for p in root.rglob('*'):
  if p.is_symlink() or not p.is_file():continue
  # Offline launchers already use $OHT_ROOT; their /home/... suffix is relative
  # to that variable. Rewriting it would append the installation root twice.
  # Packaging tools likewise use their own relocatable root, not source paths.
  if p.parent==root or root/'tools' in p.parents:continue
  if any(name in p.parts for name in ('reference_original','fixtures','hex_assets','vendor_joint')):continue
  if p.suffix in ('.py','.sh','.pth') or p.name=='pyvenv.cfg' or p.parent.name=='bin':
   if p.stat().st_size>4*1024**2:continue
   try:s=p.read_text()
   except (UnicodeError,OSError):continue
   if '\x00' in s:continue
   t=rewrite(s)
   # The native ZED SDK otherwise looks in /usr/local/zed/settings and may
   # spawn an online calibration download that inherits the camera handle.
   if p.name=='zed_camera_worker.py' and 'params.optional_settings_path' not in t:
    anchor='        params.coordinate_units = sl.UNIT.METER'
    if anchor not in t:raise RuntimeError('Cannot configure offline ZED settings: '+str(p))
    t=t.replace(anchor,anchor+'\n        params.optional_settings_path = '+repr(str(root/'usr/local/zed/settings')+'/'),1)
   if p.name=='pyvenv.cfg' and 'zed_m_setup' in str(p):t=t.replace('home = /usr/bin','home = '+str(root/'usr/bin'))
   if s!=t:p.write_text(t)
 # source machine's persistent services now point to this isolated copy.
 original=base/'teleop_capture_v5_hex_insert';manager=base/'dagger_capture_v1_20261022'
 for directory in [app,original,manager]:
  p=directory/'cameras.json';config=json.loads(p.read_text())
  p.write_text(rewrite(json.dumps(config,ensure_ascii=False,indent=2))+'\n')
  (directory/'ui_runtime').mkdir(exist_ok=True)
 (app/'dagger_settings.json').write_text(json.dumps({'original_root':str(original),'model_registry':str(manager/'dagger_models.json'),'policy_runtime':str(manager/'ui_runtime/policy'),'policy_service':'http://127.0.0.1:8769'},indent=2))
 (manager/'dagger_settings.json').write_text(json.dumps({'original_root':str(original),'model_python':str(root/MODEL/'runtime/bin/python'),'model_cache':str(root/MODEL/'cache/openpi'),'model_registry':str(manager/'dagger_models.json')},indent=2))
 registry=manager/'dagger_models.json';registry.write_text(rewrite(registry.read_text()))
 # Keep provenance paths inside reference bundles unchanged. They are not file dependencies.
 # Place fresh datasets on an explicit chosen filesystem; preserve mount checking.
 data.mkdir(parents=True,exist_ok=True)
 mount=data
 while not mount.is_mount():mount=mount.parent
 for directory,name in [(app,'unified'),(original,'shared'),(manager,'dagger_legacy')]:
  target=data/name/'episodes';target.mkdir(parents=True,exist_ok=True)
  link=directory/'episodes'
  if link.exists():
   if link.is_dir() and not link.is_symlink() and not any(link.iterdir()):link.rmdir()
   else:raise RuntimeError('Refuse to replace existing data: '+str(link))
  if link.is_symlink():raise RuntimeError('Refuse existing link: '+str(link))
  link.symlink_to(target)
  (directory/'episode_storage.json').write_text(json.dumps({'schema':1,'mount':str(mount),'directory':str(target)},indent=2))
 # A relocated package must regenerate kinematic/path caches on this robot.
 # No claims about the reference's physical validity on a different workstation.
 env='''#!/usr/bin/env bash
OHT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export OHT_ROOT
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export FONTCONFIG_FILE="$OHT_ROOT/fonts.conf"
export PATH="$OHT_ROOT/bin:$PATH"
export LD_LIBRARY_PATH="$OHT_ROOT/native/lib:$OHT_ROOT/usr/local/zed/lib:$OHT_ROOT/usr/local/zed/third_party/lib:$OHT_ROOT/usr/local/cuda-11.8/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
'''
 (root/'env.sh').write_text(env)
 (root/'fonts.conf').write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>'+html.escape(str(root/'fonts'))+'</dir><cachedir>'+html.escape(str(root/'font_cache'))+'</cachedir></fontconfig>')
 config={'root':str(root),'data_root':str(data),'app':str(app),'original':str(original),'manager':str(manager),'python':str(base/'.venv_teleop/bin/python'),'camera_python':str(root/'home/samsung/codex_work/realsense_capture_v1/.venv/bin/python'),'zed_python':str(root/'home/samsung/codex_work/zed_m_setup_20261016/.venv/bin/python'),'calibration_python':str(base/'.venv_camera_calibration_20261102/bin/python'),'model_python':str(root/MODEL/'runtime/bin/python'),'source_robot_ip':'192.168.8.100','source_onrobot_ip':'192.168.8.101'}
 (root/'installation.json').write_text(json.dumps(config,indent=2))
 print(json.dumps(config,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--data-dir',required=True);a=p.parse_args();configure(a.root,a.data_dir)
