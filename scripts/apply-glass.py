#!/usr/bin/env python3
"""Apply ~/.config/dellarc (mode, tint, opacity, blur) to every glass layer:
the window decoration, Kvantum app surfaces, the KDE color scheme and Konsole."""
from pathlib import Path
import os,sys,shutil,subprocess,configparser
ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home(); CFG=Path(os.environ.get('XDG_CONFIG_HOME',HOME/'.config')); DATA=Path(os.environ.get('XDG_DATA_HOME',HOME/'.local/share'))
def run(*args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
def config(file,group,key,value):run('kwriteconfig6','--file',CFG/file,'--group',group,'--key',key,str(value))
rc=configparser.ConfigParser();rc.optionxform=str;rc.read(CFG/'dellarc')
glass=rc['Glass'] if rc.has_section('Glass') else {}
name='DellaLight' if glass.get('Mode','dark')=='light' else 'Della'

run(sys.executable,ROOT/'scripts/build-assets.py',stdout=subprocess.DEVNULL)
for variant in ['Della','DellaLight']:
 shutil.copytree(ROOT/'assets/Kvantum'/variant,CFG/'Kvantum'/variant,dirs_exist_ok=True)
 shutil.copy2(ROOT/f'assets/color-schemes/{variant}.colors',DATA/f'color-schemes/{variant}.colors')
(DATA/'konsole').mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'assets/konsole/Della.colorscheme',DATA/'konsole/Della.colorscheme')
config('Kvantum/kvantum.kvconfig','General','theme',name)
for theme in ['Della','DellaLight']:
 shutil.copytree(ROOT/'assets/plasma'/theme,DATA/'plasma/desktoptheme'/theme,dirs_exist_ok=True)
# Panels/popups: Della (dark) or Della Light (frostier); bounce so updated files are reloaded.
run('plasma-apply-desktoptheme','default',stdout=subprocess.DEVNULL)
run('plasma-apply-desktoptheme',name,stdout=subprocess.DEVNULL)

# plasma-apply-colorscheme skips a scheme that is already active, so bounce through the other variant.
other='Della' if name=='DellaLight' else 'DellaLight'
run('plasma-apply-colorscheme',other,stdout=subprocess.DEVNULL)
run('plasma-apply-colorscheme',name,stdout=subprocess.DEVNULL)

konsolerc=configparser.ConfigParser(strict=False,interpolation=None);konsolerc.optionxform=str;konsolerc.read(CFG/'konsolerc')
profile=konsolerc.get('Desktop Entry','DefaultProfile',fallback='')
if profile and (DATA/'konsole'/profile).exists():
 # The terminal stays dark glass in light mode too.
 run('kwriteconfig6','--file',DATA/'konsole'/profile,'--group','Appearance','--key','ColorScheme','Della')

if 'BlurStrength' in glass:config('kwinrc','Effect-blur','BlurStrength',glass['BlurStrength'])
# Liquid Glass (when active) takes the same blur strength for windows and titlebars.
if 'BlurStrength' in glass:
 for key in ['BlurStrength','DecorationBlurStrength']:config('kwinrc','Effect-blurplus',key,glass['BlurStrength'])
if 'NoiseStrength' in glass:config('kwinrc','Effect-blur','NoiseStrength',glass['NoiseStrength'])
subprocess.run(['qdbus6','org.kde.KWin','/Effects','org.kde.kwin.Effects.reconfigureEffect','blur'],stdout=subprocess.DEVNULL)
subprocess.run(['qdbus6','org.kde.KWin','/Effects','org.kde.kwin.Effects.reconfigureEffect','glass'],stdout=subprocess.DEVNULL)
# The decoration rereads dellarc on reconfigure, so titlebars change immediately.
run('qdbus6','org.kde.KWin','/KWin','org.kde.KWin.reconfigure')
print(f'Applied {name} glass. Reopen applications to refresh their window interiors.')
