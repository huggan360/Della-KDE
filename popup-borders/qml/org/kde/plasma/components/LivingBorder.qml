// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Shapes
import QtCore
import org.kde.kirigami as Kirigami

Item {
    id: root
    objectName: "dellaLivingBorder"
    // Only a visual layer: no mouse areas, focus, or input handlers.
    property url settingsFile: ""
    property real radius: 10
    property real borderWidth: 2
    property bool borderEnabled: true
    property bool animateBorder: true
    property bool followAccent: true
    property color customColor1: "#80dbf6"
    property color customColor2: "#b6aaff"
    property real cycleSeconds: 32
    property real phase: 0
    readonly property color accent: Kirigami.Theme.highlightColor
    readonly property color firstColor: followAccent ? Qt.lighter(accent, 1.4) : customColor1
    readonly property color secondColor: followAccent ? Qt.hsla((accent.hslHue + 0.13) % 1, Math.max(0.45, accent.hslSaturation), Math.max(0.58, accent.hslLightness), 1) : customColor2
    // Continuous velocity at the cycle boundary; slow drift with gentle surges.
    readonly property real angle: 45 + 360 * phase - 25 * Math.sin(2 * Math.PI * phase) - 9 * Math.sin(4 * Math.PI * phase)
    readonly property real radians: angle * Math.PI / 180
    readonly property real extent: Math.sqrt(width * width + height * height) / 2
    visible: borderEnabled && width > 8 && height > 8

    Settings { id: preferences; location: root.settingsFile }
    function asBool(value) { return value === true || value === 1 || String(value).toLowerCase() === "true"; }
    function reload() {
        preferences.sync();
        borderEnabled = asBool(preferences.value("enabled", true));
        animateBorder = asBool(preferences.value("animated", true));
        followAccent = asBool(preferences.value("followAccent", true));
        customColor1 = preferences.value("color1", "#80dbf6");
        customColor2 = preferences.value("color2", "#b6aaff");
        cycleSeconds = Math.max(10, Math.min(120, Number(preferences.value("cycleSeconds", 32))));
    }
    Component.onCompleted: reload()
    Timer { interval: 1000; repeat: true; running: root.visible && (!root.Window.window || root.Window.window.visible); onTriggered: root.reload() }
    NumberAnimation on phase {
        from: 0; to: 1; duration: root.cycleSeconds * 1000
        loops: Animation.Infinite
        running: root.visible && root.animateBorder && (!root.Window.window || root.Window.window.visible)
    }
    function roundedRect(x, y, w, h, r) {
        r = Math.max(0, Math.min(r, w / 2, h / 2));
        return "M " + (x+r) + " " + y + " H " + (x+w-r)
            + " A " + r + " " + r + " 0 0 1 " + (x+w) + " " + (y+r)
            + " V " + (y+h-r) + " A " + r + " " + r + " 0 0 1 " + (x+w-r) + " " + (y+h)
            + " H " + (x+r) + " A " + r + " " + r + " 0 0 1 " + x + " " + (y+h-r)
            + " V " + (y+r) + " A " + r + " " + r + " 0 0 1 " + (x+r) + " " + y + " Z ";
    }
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: -1
            fillRule: ShapePath.OddEvenFill
            fillGradient: LinearGradient {
                x1: root.width/2 - Math.cos(root.radians)*root.extent
                y1: root.height/2 - Math.sin(root.radians)*root.extent
                x2: root.width/2 + Math.cos(root.radians)*root.extent
                y2: root.height/2 + Math.sin(root.radians)*root.extent
                GradientStop { position: 0; color: root.firstColor }
                GradientStop { position: 0.48; color: root.secondColor }
                GradientStop { position: 1; color: root.firstColor }
            }
            PathSvg {
                path: root.roundedRect(0,0,root.width,root.height,root.radius)
                    + root.roundedRect(root.borderWidth,root.borderWidth,root.width-2*root.borderWidth,root.height-2*root.borderWidth,root.radius-root.borderWidth)
            }
        }
    }
}
