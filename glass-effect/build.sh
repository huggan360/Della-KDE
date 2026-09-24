#!/bin/sh
# Build the Liquid Glass compositor effect (kwin-effects-glass, GPL-3, vendored in src/) against
# the installed KWin, using tools kept inside this folder (no system packages, no root).
# Rerun after a KWin upgrade (the login script and install.py do this automatically).
# Usage: build.sh [output-plugin-dir]
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HOME/.local/lib/della/qt6/plugins}
T=$HERE/.tools
cd "$HERE"

# Local build tools: cmake + ninja (pip), KDE extra-cmake-modules and Vulkan headers matching
# the system (KWin's CMake package requires Vulkan headers even though the effect does not use them).
if [ ! -x "$T/bin/cmake" ]; then
    python3 -m venv "$T" && "$T/bin/pip" install -q cmake ninja
fi
KF=$(pacman -Q kconfig 2>/dev/null | awk '{print $2}' | cut -d- -f1 || true)
KF=${KF:-$(pkg-config --modversion KF6Config 2>/dev/null || echo 6.30.0)}
if [ ! -f "$T/ecm/share/ECM/cmake/ECMConfig.cmake" ] || [ "$(cat "$T/ecm.version" 2>/dev/null)" != "$KF" ]; then
    rm -rf "$T/ecm-src" "$T/ecm-build" "$T/ecm"
    git clone -q --depth 1 --branch "v$KF" https://github.com/KDE/extra-cmake-modules.git "$T/ecm-src" 2>/dev/null \
        || git clone -q --depth 1 https://github.com/KDE/extra-cmake-modules.git "$T/ecm-src"
    "$T/bin/cmake" -S "$T/ecm-src" -B "$T/ecm-build" -G Ninja -DCMAKE_MAKE_PROGRAM="$T/bin/ninja" -DCMAKE_INSTALL_PREFIX="$T/ecm" \
        -DBUILD_TESTING=OFF -DBUILD_HTML_DOCS=OFF -DBUILD_MAN_DOCS=OFF -DBUILD_QTHELP_DOCS=OFF >/dev/null
    "$T/bin/cmake" --install "$T/ecm-build" >/dev/null
    echo "$KF" > "$T/ecm.version"
fi
if [ -f /usr/include/vulkan/vulkan.h ]; then
    VULKAN=/usr/include
else
    if [ ! -f "$T/vulkan-headers/include/vulkan/vulkan.h" ]; then
        VK=$(pacman -Q vulkan-icd-loader 2>/dev/null | awk '{print $2}' | cut -d- -f1 | cut -d. -f1-3 || true)
        git clone -q --depth 1 --branch "v${VK:-1.4.357}" https://github.com/KhronosGroup/Vulkan-Headers.git "$T/vulkan-headers" 2>/dev/null \
            || git clone -q --depth 1 https://github.com/KhronosGroup/Vulkan-Headers.git "$T/vulkan-headers"
    fi
    VULKAN=$T/vulkan-headers/include
fi

rm -rf build stage
"$T/bin/cmake" -S src -B build -G Ninja -DCMAKE_MAKE_PROGRAM="$T/bin/ninja" -DCMAKE_PREFIX_PATH="$T/ecm" \
    -DVulkan_INCLUDE_DIR="$VULKAN" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$HERE/stage" -DBUILD_TESTING=OFF >/dev/null
"$T/bin/cmake" --build build >/dev/null
"$T/bin/cmake" --install build >/dev/null

# Install atomically: a running KWin keeps its mapped copy; the new file is picked up on load.
for kind in plugins configs; do
    mkdir -p "$OUT/kwin/effects/$kind"
    for so in "$HERE"/stage/lib/plugins/kwin/effects/$kind/*.so; do
        cp "$so" "$OUT/kwin/effects/$kind/.$(basename "$so").new"
        mv -f "$OUT/kwin/effects/$kind/.$(basename "$so").new" "$OUT/kwin/effects/$kind/$(basename "$so")"
    done
done
echo "Built Liquid Glass effect into $OUT/kwin/effects"
