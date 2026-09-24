#!/bin/sh
# Style the Plasma Login Manager greeter with Della while keeping KDE's standard login layout:
# the login user gets the Della Global Theme (colors, Plasma theme) and the wave wallpaper,
# installed in its own home (/var/lib/plasmalogin); nothing is added under /usr.
#   Install: pkexec sh login-screen/install-login.sh      (or sudo)
#   Remove:  pkexec sh login-screen/install-login.sh --remove
set -eu
[ "$(id -u)" = 0 ] || { echo "Run as root: pkexec sh $0" >&2; exit 1; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
LOGIN_USER=plasmalogin
LOGIN_HOME=$(getent passwd "$LOGIN_USER" | cut -d: -f6)
[ -n "$LOGIN_HOME" ] && [ -d "$LOGIN_HOME" ] || { echo "Plasma Login Manager user '$LOGIN_USER' not found" >&2; exit 1; }
SHARE=$LOGIN_HOME/.local/share
CONFIG=$LOGIN_HOME/.config
CONF=/etc/plasmalogin.conf
BACKUP=/etc/plasmalogin.conf.della-backup
WALLPAPER=$SHARE/wallpapers/Della
cfg() { kwriteconfig6 --file "$@"; }

# Forces startplasma to re-apply the look-and-feel defaults on the next greeter start.
reset_defaults() { rm -f "$CONFIG/kdedefaults/package"; }

if [ "${1:-}" = "--remove" ]; then
    rm -rf "$SHARE/plasma/look-and-feel/org.kde.della.desktop" "$SHARE/plasma/desktoptheme/Della" \
        "$SHARE/color-schemes/Della.colors" "$WALLPAPER"
    [ -f "$CONFIG/kdeglobals" ] && cfg "$CONFIG/kdeglobals" --group KDE --key LookAndFeelPackage --delete
    if [ -f "$BACKUP" ]; then cp -p "$BACKUP" "$CONF" && rm -f "$BACKUP"; fi
    reset_defaults
    echo "Della removed from the login screen; KDE's defaults return at the next login screen."
    exit 0
fi

for dir in "$ROOT/assets/look-and-feel/org.kde.della.desktop" "$ROOT/assets/plasma/Della" "$ROOT/assets/wallpaper-package/Della"; do
    [ -d "$dir" ] || { echo "Missing $dir (run scripts/build-assets.py first)" >&2; exit 1; }
done
# Migrate from the theme's former name (Glasswave): keep the original config backup, drop old files.
[ -f /etc/plasmalogin.conf.glasswave-backup ] && [ ! -f "$BACKUP" ] && mv /etc/plasmalogin.conf.glasswave-backup "$BACKUP"
rm -rf "$SHARE/plasma/look-and-feel/org.kde.glasswave.desktop" "$SHARE/plasma/desktoptheme/Glasswave" \
    "$SHARE/color-schemes/Glasswave.colors" "$SHARE/wallpapers/Glasswave"
[ -f "$CONF" ] && [ ! -f "$BACKUP" ] && cp -p "$CONF" "$BACKUP"

install -d -o "$LOGIN_USER" -g "$LOGIN_USER" "$LOGIN_HOME/.local" "$SHARE" "$SHARE/plasma" "$SHARE/plasma/look-and-feel" \
    "$SHARE/plasma/desktoptheme" "$SHARE/color-schemes" "$SHARE/wallpapers" "$CONFIG"
rm -rf "$SHARE/plasma/look-and-feel/org.kde.della.desktop" "$SHARE/plasma/desktoptheme/Della" "$WALLPAPER"
cp -r "$ROOT/assets/look-and-feel/org.kde.della.desktop" "$SHARE/plasma/look-and-feel/"
cp -r "$ROOT/assets/plasma/Della" "$SHARE/plasma/desktoptheme/"
cp "$ROOT/assets/color-schemes/Della.colors" "$SHARE/color-schemes/"
cp -r "$ROOT/assets/wallpaper-package/Della" "$WALLPAPER"

cfg "$CONFIG/kdeglobals" --group KDE --key LookAndFeelPackage org.kde.della.desktop
reset_defaults
chown -R "$LOGIN_USER:$LOGIN_USER" "$LOGIN_HOME/.local" "$CONFIG"
chmod -R u+rwX,go+rX "$SHARE/plasma" "$SHARE/color-schemes" "$SHARE/wallpapers"

# Greeter wallpaper (same keys the Login Screen settings page writes).
cfg "$CONF" --group Greeter --key WallpaperPluginId org.kde.image
cfg "$CONF" --group Greeter --group Wallpaper --group org.kde.image --key Image "file://$WALLPAPER"
echo "Della login screen installed. It appears the next time the login screen starts (log out)."
