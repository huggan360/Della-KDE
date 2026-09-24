#!/usr/bin/env python3
"""One-time migration of an installed Glasswave setup to Della (the renamed theme).
Keeps the user's tint and dock-border settings, installs Della, then removes Glasswave's files."""
from pathlib import Path
import os,sys,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home();CFG=Path(os.environ.get('XDG_CONFIG_HOME',HOME/'.config'));DATA=Path(os.environ.get('XDG_DATA_HOME',HOME/'.local/share'))
def run(*args):subprocess.run([str(a) for a in args],check=True)

# 1. Settings carry over.
for old,new in [('glasswaverc','dellarc'),('glasswave-borders.ini','della-borders.ini')]:
 if (CFG/old).exists() and not (CFG/new).exists():(CFG/old).rename(CFG/new)
# 2. Local plugins: rename the directory (running programs keep their mapped files) and leave a
#    link so this session's QT_PLUGIN_PATH still resolves until the next login removes it.
old_lib,new_lib=HOME/'.local/lib/glasswave',HOME/'.local/lib/della'
if old_lib.is_dir() and not old_lib.is_symlink() and not new_lib.exists():old_lib.rename(new_lib)
if not old_lib.exists():old_lib.symlink_to(new_lib)
# 3. Old dock-border shell overlay and its plasmashell hook.
overlay=DATA/'plasma/shells/org.kde.plasma.desktop'
if (overlay/'.glasswave-overlay').exists():shutil.rmtree(overlay)
(CFG/'systemd/user/plasma-plasmashell.service.d/60-glasswave-borders.conf').unlink(missing_ok=True)
# 4. Install Della and switch to it.
mode=['--light'] if 'Mode=light' in (CFG/'dellarc').read_text() else [] if (CFG/'dellarc').exists() else []
run(sys.executable,ROOT/'install.py',*mode)
run(sys.executable,ROOT/'popup-borders/install-borders.py')
# 5. Remove Glasswave's installed copies (Della is active now).
for p in [DATA/'plasma/desktoptheme/Glasswave',DATA/'aurorae/themes/Glasswave',DATA/'aurorae/themes/GlasswaveLight',
          DATA/'wallpapers/Glasswave',DATA/'plasma/look-and-feel/org.kde.glasswave.desktop',DATA/'glasswave-popup-borders',
          CFG/'Kvantum/Glasswave',CFG/'Kvantum/GlasswaveLight']:
 shutil.rmtree(p,ignore_errors=True)
for p in [DATA/'color-schemes/Glasswave.colors',DATA/'color-schemes/GlasswaveLight.colors',DATA/'konsole/Glasswave.colorscheme',
          DATA/'konsole/GlasswaveLight.colorscheme',DATA/'applications/glasswave-glass.desktop',DATA/'applications/glasswave-borders.desktop',
          CFG/'plasma-workspace/env/glasswave.sh',new_lib/'qt6/plugins/org.kde.kdecoration3/org.kde.glasswave.so']:
 p.unlink(missing_ok=True)
print('Migrated Glasswave → Della. Log out/in once to finish (removes the temporary compatibility link).')
