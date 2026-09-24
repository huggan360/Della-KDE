#!/usr/bin/env python3
from pathlib import Path
import os,sys,shutil,subprocess,json,datetime
ROOT=Path(__file__).resolve().parents[1]
CFG=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'));DATA=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
TARGET=DATA/'della-popup-borders';TARGET.mkdir(parents=True,exist_ok=True)
# The dock overlay is regenerated before each plasmashell start; nothing else is affected.
dropin=CFG/'systemd/user/plasma-plasmashell.service.d/60-della-borders.conf'
settings=CFG/'della-borders.ini'
baseline=ROOT/'backups/baseline'
if baseline.exists():
 folder=ROOT/'backups'/baseline.read_text().strip();manifest=json.loads((folder/'manifest.json').read_text())
 for p in [dropin,settings]:
  if not any(item['path']==str(p) for item in manifest):
   name=str(len(manifest));manifest.append({'path':str(p),'file':name,'existed':p.exists()})
   if p.exists():shutil.copy2(p,folder/name)
 (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
for name in ['LivingBorder.qml','refresh.py','settings.py']:
 shutil.copy2(ROOT/'popup-borders'/name,TARGET/name)
shutil.copy2(ROOT/'design-tokens.json',TARGET/'design-tokens.json')
subprocess.run([sys.executable,str(TARGET/'refresh.py'),'--strict'],check=True)
# Popups no longer use a QML module override; clear the files from earlier versions.
shutil.rmtree(TARGET/'qml',ignore_errors=True);(TARGET/'DialogBackground.qml').unlink(missing_ok=True)
def systemd_quote(s):return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'
dropin.parent.mkdir(parents=True,exist_ok=True)
dropin.write_text('[Service]\nExecStartPre='+systemd_quote(sys.executable)+' '+systemd_quote(str(TARGET/'refresh.py'))+'\n')
applications=DATA/'applications';applications.mkdir(parents=True,exist_ok=True)
# Desktop Entry quoting uses double quotes and backslash escaping.
def desktop_quote(s):return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')+'"'
entry='[Desktop Entry]\nType=Application\nName=Della Borders\nComment=Dock gradient border colors and animation\nIcon=preferences-desktop-color\nExec='+desktop_quote(sys.executable)+' '+desktop_quote(str(TARGET/'settings.py'))+'\nTerminal=false\nCategories=Settings;DesktopSettings;\n'
(applications/'della-borders.desktop').write_text(entry)
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
if '--no-restart' not in sys.argv:subprocess.run(['systemctl','--user','restart','plasma-plasmashell.service'],check=True)
print('Installed the living dock border. Open “Della Borders” in the application launcher.')
