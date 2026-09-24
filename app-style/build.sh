#!/bin/sh
# Build Della Style (Qt6 application style; KDE Breeze lineage via Glass/Darkly, GPL, vendored in src/
# and modified for Della: glass tint, radius rules, row insets) with the local tools from glass-effect/.
# Usage: build.sh [output-plugin-dir]
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HOME/.local/lib/della/qt6/plugins}
TOOLS=$HERE/../glass-effect
[ -x "$TOOLS/.tools/bin/cmake" ] || sh "$TOOLS/build.sh" "$OUT" >/dev/null   # sets up cmake/ninja/ECM
T=$TOOLS/.tools
cd "$HERE"
rm -rf build stage
"$T/bin/cmake" -S src -B build -G Ninja -DCMAKE_MAKE_PROGRAM="$T/bin/ninja" -DCMAKE_PREFIX_PATH="$T/ecm" \
    -DBUILD_QT5=OFF -DBUILD_QT6=ON -DWITH_DECORATIONS=OFF -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$HERE/stage" >/dev/null
"$T/bin/cmake" --build build >/dev/null
"$T/bin/cmake" --install build >/dev/null
# Atomic install: running apps keep their mapped copy (never overwrite a loaded library in place).
mkdir -p "$OUT/styles"
cp "$HERE/stage/lib/plugins/styles/della6.so" "$OUT/styles/.della6.so.new"
mv -f "$OUT/styles/.della6.so.new" "$OUT/styles/della6.so"
echo "Built Della Style into $OUT/styles"
