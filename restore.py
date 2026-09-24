#!/usr/bin/env python3
from pathlib import Path
import json,shutil,subprocess,sys
root=Path(__file__).resolve().parent
backup=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'backups'/(root/'backups/baseline').read_text().strip()
manifest=json.loads((backup/'manifest.json').read_text())
# Stop only the desktop shell so it cannot overwrite restored panel settings.
subprocess.run(['systemctl','--user','stop','plasma-plasmashell.service'],check=True)
try:
 for item in manifest:
  p=Path(item['path'])
  if item['existed']:p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(backup/item['file'],p)
  elif p.exists():p.unlink()
 # The dock-border shell overlay is generated, not backed up: remove it so Plasma uses its own shell.
 overlay=Path.home()/'.local/share/plasma/shells/org.kde.plasma.desktop'
 if (overlay/'.della-overlay').exists():shutil.rmtree(overlay)
finally:subprocess.run(['systemctl','--user','start','plasma-plasmashell.service'],check=True)
subprocess.run(['qdbus6','org.kde.KWin','/KWin','org.kde.KWin.reconfigure'],check=True)
print('Restored',backup,'— log out/in to reset application styles and session environment.')
