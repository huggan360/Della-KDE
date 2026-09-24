#!/usr/bin/env python3
"""Install Della assets and plugins; settings changes require the explicit --apply flag."""
from pathlib import Path
import os,sys,shutil,subprocess,json,datetime,configparser
ROOT=Path(__file__).resolve().parent
TOKENS=json.loads((ROOT/'design-tokens.json').read_text());GLASS=TOKENS['glass']
APPEARANCE='DellaLight' if '--light' in sys.argv else 'Della'
APPLY_SETTINGS='--apply' in sys.argv
HOME=Path.home(); CFG=Path(os.environ.get('XDG_CONFIG_HOME',HOME/'.config')); DATA=Path(os.environ.get('XDG_DATA_HOME',HOME/'.local/share'))
def run(*args,**kw):
 if not APPLY_SETTINGS and str(args[0]) in {'plasma-apply-colorscheme','plasma-apply-desktoptheme'}:return subprocess.CompletedProcess(args,0)
 if not APPLY_SETTINGS and len(args)>=4 and str(args[0])=='qdbus6' and str(args[1])=='org.kde.KWin':return subprocess.CompletedProcess(args,0)
 if not APPLY_SETTINGS and str(args[0])=='systemctl' and 'restart' in args:return subprocess.CompletedProcess(args,0)
 return subprocess.run([str(x) for x in args],check=True,**kw)
def config(file,group,key,value):
 if APPLY_SETTINGS:run('kwriteconfig6','--file',CFG/file,'--group',group,'--key',key,str(value))
def replace_library(source,target):
 # Running KWin/plasmashell/apps have this library mapped: never rewrite it in place (that crashes
 # them). Skip identical copies; otherwise write a new file and atomically rename it over.
 if target.exists() and target.read_bytes()==source.read_bytes():return
 temp=target.with_name('.'+target.name+'.new');shutil.copy2(source,temp);os.replace(temp,target)
def script(code):
 if APPLY_SETTINGS:run('qdbus6','org.kde.plasmashell','/PlasmaShell','org.kde.PlasmaShell.evaluateScript',code)
def remove_legacy_panel_border():
 # Older Della builds installed a user-only Plasma shell copy with a 1px panel outline.
 # Remove only that marked copy and its matching systemd hook; stock Plasma remains intact.
 overlay=DATA/'plasma/shells/org.kde.plasma.desktop'
 if (overlay/'.della-overlay').exists():shutil.rmtree(overlay)
 dropin=CFG/'systemd/user/plasma-plasmashell.service.d/60-della-borders.conf'
 if dropin.exists() and 'della-popup-borders' in dropin.read_text(errors='ignore'):dropin.unlink()
 (DATA/'applications/della-borders.desktop').unlink(missing_ok=True)
 try:run('systemctl','--user','daemon-reload')
 except (subprocess.CalledProcessError,FileNotFoundError):pass
remove_legacy_panel_border()
for cmd in (['qdbus6','kwriteconfig6','plasma-apply-colorscheme','plasma-apply-desktoptheme'] if APPLY_SETTINGS else ['qdbus6']):
 if not shutil.which(cmd):sys.exit('Missing Plasma 6 dependency: '+cmd)
run('qdbus6','org.kde.plasmashell','/PlasmaShell','org.freedesktop.DBus.Peer.Ping',stdout=subprocess.DEVNULL)
backup=ROOT/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup.mkdir(parents=True)
konsolerc=configparser.ConfigParser(strict=False,interpolation=None);konsolerc.optionxform=str;konsolerc.read(CFG/'konsolerc')
profile_name=konsolerc.get('Desktop Entry','DefaultProfile',fallback='') or 'Della.profile'
konsole_profile=DATA/'konsole'/profile_name
paths=[CFG/p for p in ['kdeglobals','kwinrc','plasmarc','plasmashellrc','plasma-org.kde.plasma.desktop-appletsrc','Kvantum/kvantum.kvconfig','plasma-workspace/env/della.sh','dellarc','konsolerc']]+[konsole_profile]
manifest=[]
for i,p in enumerate(paths):
 exists=p.exists();manifest.append({'path':str(p),'file':str(i),'existed':exists})
 if exists:shutil.copy2(p,backup/str(i))
(backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'backups/latest').write_text(backup.name)
baseline=ROOT/'backups/baseline'
if not baseline.exists(): baseline.write_text(backup.name)
else:
 # Files Della started managing later are added to the pre-Della snapshot on first sight.
 folder=ROOT/'backups'/baseline.read_text().strip();base=json.loads((folder/'manifest.json').read_text())
 for item in manifest:
  if not any(b['path']==item['path'] for b in base):
   name='b'+item['file']+'-'+backup.name;base.append({'path':item['path'],'file':name,'existed':item['existed']})
   if item['existed']:shutil.copy2(backup/item['file'],folder/name)
 (folder/'manifest.json').write_text(json.dumps(base,indent=2))
rc=configparser.ConfigParser();rc.optionxform=str;rc.read(CFG/'dellarc')
if not rc.has_section('Glass'):rc.add_section('Glass')
defaults={'DarkTint':GLASS['darkTint'],'DarkOpacity':GLASS['darkOpacity'],'LightTint':GLASS['lightTint'],'LightOpacity':GLASS['lightOpacity'],'Radius':TOKENS['radius'],'TitleHeight':TOKENS['titleHeight'],'BlurStrength':GLASS['blurStrength'],'NoiseStrength':GLASS['noiseStrength']}
for k,v in defaults.items():rc['Glass'].setdefault(k,str(v))
rc['Glass']['Radius']=str(TOKENS['radius'])
rc['Glass']['Mode']='light' if APPEARANCE=='DellaLight' else 'dark'
if APPLY_SETTINGS:
 with (CFG/'dellarc').open('w') as f:rc.write(f,space_around_delimiters=False)
# Regenerate so Kvantum, color schemes and Konsole carry the chosen tint.
run(sys.executable,ROOT/'scripts/build-assets.py')
for src,dst in [('plasma/Della',DATA/'plasma/desktoptheme/Della'),('plasma/DellaLight',DATA/'plasma/desktoptheme/DellaLight'),('aurorae/Della',DATA/'aurorae/themes/Della'),('aurorae/DellaLight',DATA/'aurorae/themes/DellaLight'),('Kvantum/Della',CFG/'Kvantum/Della'),('Kvantum/DellaLight',CFG/'Kvantum/DellaLight')]:
 shutil.copytree(ROOT/'assets'/src,dst,dirs_exist_ok=True)
# Removed from the theme in favour of Breeze's standard task indicators; drop stale installed copies.
for theme in ['Della','DellaLight']:
 for stale in ['widgets/tasks.svg','widgets/button.svg','colors']:(DATA/'plasma/desktoptheme'/theme/stale).unlink(missing_ok=True)
# Global Theme entry (System Settings → Global Theme → Della); also used by the login screen.
lnf=DATA/'plasma/look-and-feel/org.kde.della.desktop';shutil.rmtree(lnf,ignore_errors=True);shutil.copytree(ROOT/'assets/look-and-feel/org.kde.della.desktop',lnf)
# Della Clock widget (centered date/time, KDE calendar popup) used by the top clock island.
clock=DATA/'plasma/plasmoids/org.kde.della.clock';shutil.rmtree(clock,ignore_errors=True);shutil.copytree(ROOT/'assets/plasmoids/org.kde.della.clock',clock)
(DATA/'color-schemes').mkdir(parents=True,exist_ok=True)
for name in ['Della','DellaLight']:
 shutil.copy2(ROOT/('assets/color-schemes/'+name+'.colors'),DATA/('color-schemes/'+name+'.colors'))
(DATA/'konsole').mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'assets/konsole/Della.colorscheme',DATA/'konsole/Della.colorscheme')
(DATA/'konsole/DellaLight.colorscheme').unlink(missing_ok=True)
if APPLY_SETTINGS:
 profile=configparser.ConfigParser(strict=False,interpolation=None);profile.optionxform=str;profile.read(konsole_profile)
 for section,values in {'General':{'Name':konsole_profile.stem,'Parent':'FALLBACK/'},'Appearance':{'ColorScheme':'Della'}}.items():
  if not profile.has_section(section):profile.add_section(section)
  for k,v in values.items():
   if k=='ColorScheme' or k not in profile[section]:profile[section][k]=v
 with konsole_profile.open('w') as f:profile.write(f,space_around_delimiters=False)
 config('konsolerc','Desktop Entry','DefaultProfile',konsole_profile.name)
# Wallpaper package with light (images/) and dark (images_dark/) variants; Plasma follows the color scheme.
wallpaper=DATA/'wallpapers/Della'
shutil.rmtree(wallpaper,ignore_errors=True);shutil.copytree(ROOT/'assets/wallpaper-package/Della',wallpaper)
# Local plugin directory, scoped to this user. Nothing is written to /usr.
LOCAL=HOME/'.local/lib/della/qt6/plugins'
# Prefer the system's managed Kvantum engine on other computers.
kvantum=any((Path(base)/'styles/libkvantum.so').exists() for base in ['/usr/lib/qt6/plugins','/usr/lib/x86_64-linux-gnu/qt6/plugins','/usr/lib64/qt6/plugins'])
local_kvantum=False
if not kvantum:
 source=ROOT/'runtime/usr/lib/qt6/plugins/styles/libkvantum.so'
 if source.exists():
  result=subprocess.run(['ldd',str(source)],text=True,capture_output=True)
  if result.returncode==0 and 'not found' not in result.stdout:
   (LOCAL/'styles').mkdir(parents=True,exist_ok=True);replace_library(source,LOCAL/'styles/libkvantum.so');kvantum=local_kvantum=True
 if not kvantum:
  print('Kvantum is unavailable. Install your distribution’s Qt6 Kvantum package and rerun for glass app interiors.')
# Window decoration, compiled against this computer's KDecoration3; Aurorae is the fallback.
build=subprocess.run(['sh',str(ROOT/'decoration/build.sh'),str(LOCAL)],text=True,capture_output=True)
decoration=build.returncode==0
if not decoration:print('Della decoration could not be built; using the Aurorae fallback.\n'+build.stderr[-1500:])
# Liquid Glass compositor effect (vendored kwin-effects-glass), built with tools inside glass-effect/.
glass_build=subprocess.run(['sh',str(ROOT/'glass-effect/build.sh'),str(LOCAL)],text=True,capture_output=True)
liquid=glass_build.returncode==0
if not liquid:print('Liquid Glass effect could not be built; using KWin\'s standard blur.\n'+glass_build.stderr[-1500:])
# Della Style: KDE Breeze-lineage Qt style (vendored Glass/Darkly source, modified for Della).
style_build=subprocess.run(['sh',str(ROOT/'app-style/build.sh'),str(LOCAL)],text=True,capture_output=True)
della_style=style_build.returncode==0
if not della_style:print('Della Style could not be built; apps use the Kvantum theme.\n'+style_build.stderr[-1500:])
if local_kvantum or decoration or liquid or della_style:
 envfile=CFG/'plasma-workspace/env/della.sh';envfile.parent.mkdir(parents=True,exist_ok=True)
 envfile.write_text('#!/bin/sh\n# Della local Qt6 plugins (style engine, window decoration)\nexport QT_PLUGIN_PATH="$HOME/.local/lib/della/qt6/plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"\n'
  # Runs at login before KWin starts: rebuild the decoration after a Plasma upgrade changed KDecoration3.
  # Compatibility link left by the Glasswave→Della rename; unused once this login starts.
  +'[ -L "$HOME/.local/lib/glasswave" ] && rm -f "$HOME/.local/lib/glasswave"\n'
  +'gw_plugin="$HOME/.local/lib/della/qt6/plugins/org.kde.kdecoration3/org.kde.della.so"\n'
  +'gw_lib=$(readlink -f /usr/lib/libkdecorations3.so 2>/dev/null || readlink -f /usr/lib64/libkdecorations3.so 2>/dev/null || true)\n'
  +'if [ -n "$gw_lib" ] && [ "$gw_lib" -nt "$gw_plugin" ]; then sh '+json.dumps(str(ROOT/'decoration/build.sh'))+' >/dev/null 2>&1 || true; fi\n'
  # Same for the Liquid Glass effect after a KWin upgrade; if the rebuild fails, remove the stale
  # plugin so KWin never loads it (the standard blur effect is then used instead).
  +'lg_plugin="$HOME/.local/lib/della/qt6/plugins/kwin/effects/plugins/glass.so"\n'
  +'lg_lib=$(readlink -f /usr/lib/libkwin.so 2>/dev/null || readlink -f /usr/lib64/libkwin.so 2>/dev/null || true)\n'
  # Della Style after a Qt upgrade; on failure fall back to the Kvantum theme.
  +'ds_plugin="$HOME/.local/lib/della/qt6/plugins/styles/della6.so"\n'
  +'ds_lib=$(readlink -f /usr/lib/libQt6Widgets.so.6 2>/dev/null || true)\n'
  +'if [ -f "$ds_plugin" ] && [ -n "$ds_lib" ] && [ "$ds_lib" -nt "$ds_plugin" ]; then sh '+json.dumps(str(ROOT/'app-style/build.sh'))+' >/dev/null 2>&1 || { rm -f "$ds_plugin"; kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum; }; fi\n'
  +'if [ -f "$lg_plugin" ] && [ -n "$lg_lib" ] && [ "$lg_lib" -nt "$lg_plugin" ]; then sh '+json.dumps(str(ROOT/'glass-effect/build.sh'))+' >/dev/null 2>&1 || { rm -f "$lg_plugin"; kwriteconfig6 --file kwinrc --group Plugins --key glassEnabled false; kwriteconfig6 --file kwinrc --group Plugins --key blurEnabled true; }; fi\n')
 current=os.environ.get('QT_PLUGIN_PATH','')
 if str(LOCAL) not in current.split(':'):
  run('dbus-update-activation-environment','--systemd','QT_PLUGIN_PATH='+str(LOCAL)+(':'+current if current else ''))
if kvantum:
 config('Kvantum/kvantum.kvconfig','General','theme',APPEARANCE)
 config('kdeglobals','KDE','widgetStyle','kvantum')
if della_style:
 config('kdeglobals','KDE','widgetStyle','Della')
 for key,value in {'TransparentDolphinView':'true','ViewDrawFocusIndicator':'false'}.items():config('dellastylerc','Style',key,value)
run('plasma-apply-colorscheme',APPEARANCE)
if decoration:
 config('kwinrc','org.kde.kdecoration2','library','org.kde.della')
 run('kwriteconfig6','--file',CFG/'kwinrc','--group','org.kde.kdecoration2','--key','theme','--delete')
else:
 config('kwinrc','org.kde.kdecoration2','library','org.kde.kwin.aurorae')
 config('kwinrc','org.kde.kdecoration2','theme','__aurorae__svg__'+APPEARANCE)
config('kwinrc','org.kde.kdecoration2','ButtonsOnLeft','')
config('kwinrc','org.kde.kdecoration2','ButtonsOnRight','IAX')
config('kwinrc','org.kde.kdecoration2','BorderSize','Normal')
config('kwinrc','org.kde.kdecoration2','BorderSizeAuto','true')
# Notifications in the top-right screen corner: KDE's "near the widget" mode centers them on the
# narrow tray island, which pushes them past the screen edge.
config('plasmanotifyrc','Notifications','PopupPosition','TopRight')
config('kdeglobals','WM','activeFont','Noto Sans,10,-1,5,700,0,0,0,0,0,0,0,0,0,0,1')
config('kwinrc','Effect-blur','BlurStrength',rc['Glass']['BlurStrength'])
config('kwinrc','Effect-blur','NoiseStrength',rc['Glass']['NoiseStrength'])
if liquid:
 # Liquid Glass replaces the stock blur effect (they conflict).
 config('kwinrc','Plugins','blurEnabled','false')
 config('kwinrc','Plugins','glassEnabled','true')
 for key,value in TOKENS['liquidGlass'].items():config('kwinrc','Effect-blurplus',key,str(value).lower() if isinstance(value,bool) else value)
else:
 config('kwinrc','Plugins','glassEnabled','false')
 config('kwinrc','Plugins','blurEnabled','true')
# Launcher entry for the tint/opacity/blur settings.
def desktop_quote(v):return '"'+v.replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$').replace('%','%%')+'"'
(DATA/'applications').mkdir(parents=True,exist_ok=True)
(DATA/'applications/della-glass.desktop').write_text('[Desktop Entry]\nType=Application\nName=Della Glass\nComment=Window glass tint, opacity and blur\nIcon=preferences-desktop-theme\nExec='+desktop_quote(sys.executable)+' '+desktop_quote(str(ROOT/'scripts/glass-settings.py'))+'\nTerminal=false\nCategories=Settings;DesktopSettings;\n')
run('plasma-apply-desktoptheme','default')
run('plasma-apply-desktoptheme',APPEARANCE)
# Remove the legacy shell overlay that drew a hairline around floating docks and islands.
# Della now leaves panel geometry and borders to Plasma; the glass effect supplies translucency.
popup_dropin=CFG/'systemd/user/plasma-plasmashell.service.d/60-della-borders.conf'
popup_dropin.unlink(missing_ok=True)
popup_runtime=DATA/'della-popup-borders'
popup_runtime_marker=DATA/'plasma/shells/org.kde.plasma.desktop/.della-overlay'
if popup_runtime.exists():shutil.rmtree(popup_runtime)
if popup_runtime_marker.exists():shutil.rmtree(popup_runtime_marker.parent)
subprocess.run(['systemctl','--user','daemon-reload'],check=False)
script((ROOT/'scripts/layout.js').read_text())
script('var force='+('true' if '--wallpaper' in sys.argv else 'false')+';desktops().forEach(function(d){d.currentConfigGroup=["Wallpaper","org.kde.image","General"];var cur=String(d.readConfig("Image")||"");'
 +'if(force||cur===""||cur.indexOf("Della")>=0||cur.indexOf("Glasswave")>=0||cur.indexOf("/Next")>=0){d.wallpaperPlugin="org.kde.image";d.currentConfigGroup=["Wallpaper","org.kde.image","General"];d.writeConfig("Image",'+json.dumps(wallpaper.as_uri())+');}});')
run('qdbus6','org.kde.KWin','/KWin','org.kde.KWin.reconfigure')
run('systemctl','--user','restart','plasma-plasmashell.service')
# A false loadEffect result also means the effect was already loaded.
if liquid:
 run('qdbus6','org.kde.KWin','/Effects','org.kde.kwin.Effects.unloadEffect','blur',stdout=subprocess.DEVNULL)
 run('qdbus6','org.kde.KWin','/Effects','org.kde.kwin.Effects.loadEffect','glass',stdout=subprocess.DEVNULL)
 run('qdbus6','org.kde.KWin','/Effects','org.kde.kwin.Effects.reconfigureEffect','glass',stdout=subprocess.DEVNULL)
else:
 run('qdbus6','org.kde.KWin','/Effects','org.kde.kwin.Effects.loadEffect','blur',stdout=subprocess.DEVNULL)
print('Della installed without changing KDE settings.' if not APPLY_SETTINGS else 'Della installed and settings applied. Backup: '+str(backup))
print('Use --apply only if you want Della to change the active theme, panels, wallpaper, and window settings.')
print('Log out/in once so KWin and Qt plugins load completely.')
