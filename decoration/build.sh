#!/bin/sh
# Build the Della window decoration against the installed KDecoration3/KF6/Qt6.
# Rerun after a major Plasma upgrade (install.py does this automatically).
# Usage: build.sh [output-plugin-dir]
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HOME/.local/lib/della/qt6/plugins}/org.kde.kdecoration3
BUILD=$HERE/build
mkdir -p "$BUILD" "$OUT"

MOC=
for m in /usr/lib/qt6/moc /usr/lib/qt6/libexec/moc /usr/lib64/qt6/libexec/moc /usr/lib/x86_64-linux-gnu/qt6/libexec/moc; do
    [ -x "$m" ] && MOC=$m && break
done
[ -n "$MOC" ] || { echo "Qt6 moc not found (install Qt6 base development tools)" >&2; exit 1; }
[ -d /usr/include/KDecoration3 ] || { echo "KDecoration3 headers missing (install kdecoration development files)" >&2; exit 1; }

INCLUDES="$(pkg-config --cflags-only-I Qt6Widgets) -I/usr/include/KDecoration3 -I/usr/include/KF6/KCoreAddons -I/usr/include/KF6/KConfigCore -I/usr/include/KF6/KConfig"
# moc must see KPluginFactory to expand K_PLUGIN_FACTORY_WITH_JSON into plugin metadata.
"$MOC" -I"$HERE" $INCLUDES "$HERE/delladecoration.cpp" -o "$BUILD/delladecoration.moc"
${CXX:-g++} -std=c++20 -O2 -fPIC -shared -Wall -Wno-deprecated-declarations \
    -I"$BUILD" $(pkg-config --cflags Qt6Widgets) $INCLUDES \
    "$HERE/delladecoration.cpp" -o "$BUILD/org.kde.della.so" \
    -lkdecorations3 -lKF6CoreAddons -lKF6ConfigCore $(pkg-config --libs Qt6Widgets)
# Install atomically so a running KWin never maps a half-written plugin.
cp "$BUILD/org.kde.della.so" "$OUT/.org.kde.della.so.new"
mv -f "$OUT/.org.kde.della.so.new" "$OUT/org.kde.della.so"
echo "Built $OUT/org.kde.della.so"
