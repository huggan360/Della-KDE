// Based on KDE's DialogBackground.qml, copyright 2023 Marco Martin.
// SPDX-License-Identifier: LGPL-2.0-or-later
import QtQuick
import org.kde.ksvg as KSvg

KSvg.FrameSvgItem {
    id: background
    anchors.fill: parent
    imagePath: "widgets/background"
    LivingBorder {
        anchors.fill: parent
        z: 100
        settingsFile: "file:///home/hugo/.config/della-borders.ini"
        // Match the Della popup geometry, excluding small tooltips.
        visible: borderEnabled && background.width >= 140 && background.height >= 100
    }
}
