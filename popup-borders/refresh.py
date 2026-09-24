#!/usr/bin/env python3
"""Regenerate the user-only shell overlay that draws the living gradient around the dock.
Runs before plasmashell starts (systemd ExecStartPre), so it always follows the installed
Plasma: every shell file is a fresh copy of the system file except a patched Panel.qml.
If Plasma's Panel.qml changes shape, the overlay is removed and Plasma runs unmodified.
"""
from pathlib import Path
import os,shutil,json,sys
ROOT=Path(__file__).resolve().parent
CFG=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
DATA=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
SHELL='org.kde.plasma.desktop'
DEST=DATA/'plasma/shells'/SHELL
MARKER='.della-overlay'
ANCHOR='    Keys.onEscapePressed: {'

def system_shell():
 dirs=os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':')
 for d in dirs+['/usr/share']:
  p=Path(d)/'plasma/shells'/SHELL
  if (p/'contents/views/Panel.qml').exists() and p.resolve()!=DEST.resolve():return p
 raise RuntimeError('Cannot find the installed Plasma desktop shell')

def remove_overlay():
 # Only ever delete a directory this script created.
 if (DEST/MARKER).exists():shutil.rmtree(DEST)

def build(staged):
 system=system_shell()
 token=json.loads((ROOT/'design-tokens.json').read_text())
 settings=(CFG/'della-borders.ini').as_uri()
 for source in system.rglob('*'):
  target=staged/source.relative_to(system)
  if source.is_dir():target.mkdir(parents=True,exist_ok=True)
  # Real copies, not symlinks: the lock screen (kscreenlocker) rejects package files that
  # resolve outside the package folder and would fall back to its emergency locker.
  else:target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 panel=staged/'contents/views/Panel.qml'
 original=(system/'contents/views/Panel.qml').read_text()
 if original.count(ANCHOR)!=1 or 'id: floatingTranslucentItem' not in original or 'readonly property bool bottomEdge' not in original:
  raise RuntimeError('Plasma Panel.qml layout has changed')
 border=f'''    // Della: living gradient ring on the floating dock (bottom panel) only.
    LivingBorder {{
        anchors.fill: floatingTranslucentItem
        radius: {token["radius"]}
        borderWidth: {token["popupBorderWidth"]}
        settingsFile: {json.dumps(settings)}
        visible: borderEnabled && root.bottomEdge && root.floatingness > 0.99 && floatingTranslucentItem.imagePath !== ""
    }}
    // Della: other floating panels (clock, tray) get the window-edge hairline.
    Rectangle {{
        anchors.fill: floatingTranslucentItem
        radius: {token["radius"]}
        color: "transparent"
        border.width: 1
        // Follows the color scheme: light hairline in dark mode, dark hairline in light mode.
        border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.15)
        antialiasing: true
        visible: !root.bottomEdge && root.floatingness > 0.99 && floatingTranslucentItem.imagePath !== ""
    }}

'''
 panel.unlink();panel.write_text(original.replace(ANCHOR,border+ANCHOR))
 (staged/'contents/views/LivingBorder.qml').write_text((ROOT/'LivingBorder.qml').read_text())
 (staged/MARKER).write_text(json.dumps({'system':str(system),'radius':token['radius'],'borderWidth':token['popupBorderWidth']},indent=2))

def main():
 staged=DEST.with_name(SHELL+'.della-new')
 if staged.exists():shutil.rmtree(staged)
 if DEST.exists() and not (DEST/MARKER).exists():
  print('Della: a user copy of the desktop shell exists; not touching it',file=sys.stderr);return 1
 try:
  build(staged)
  remove_overlay()
  staged.rename(DEST)
  print('Della: refreshed the dock border overlay from the installed Plasma shell')
 except Exception as exc:
  if staged.exists():shutil.rmtree(staged)
  remove_overlay()
  print('Della: using the stock Plasma shell:',exc,file=sys.stderr)
  if '--strict' in sys.argv:return 1
 return 0
if __name__=='__main__':sys.exit(main())
