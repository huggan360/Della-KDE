// SPDX-License-Identifier: MIT
// Della Clock: one centered label ("Wed 23 Sep  14:05") in the system font; click for the calendar.
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.workspace.calendar as PlasmaCalendar
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property date now: new Date()
    readonly property string timeFormat: Qt.locale().timeFormat(Locale.ShortFormat).replace(/:ss|\.ss/, "")
    readonly property string text: Qt.locale().toString(now, "ddd d MMM") + "  " + Qt.locale().toString(now, timeFormat)

    Timer {
        interval: 1000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.now = new Date()
    }

    preferredRepresentation: compactRepresentation
    toolTipMainText: Qt.locale().toString(now, Qt.locale().dateFormat(Locale.LongFormat))
    toolTipSubText: Qt.locale().toString(now, timeFormat)

    compactRepresentation: MouseArea {
        // Equal padding on both sides; the label is centered, so the island stays balanced.
        readonly property real padding: Kirigami.Units.smallSpacing * 2
        Layout.minimumWidth: label.implicitWidth + 2 * padding
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.fillHeight: true
        hoverEnabled: true
        onClicked: root.expanded = !root.expanded

        PlasmaComponents.Label {
            id: label
            anchors.centerIn: parent
            // The panel adds one layout spacing after its last widget (the containment's lastSpacer,
            // KDE bug 454095); shift by half of it so the text is centered in the island itself.
            anchors.horizontalCenterOffset: Kirigami.Units.smallSpacing / 2
            text: root.text
            font: Kirigami.Theme.defaultFont
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    fullRepresentation: PlasmaCalendar.MonthView {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 20
        Layout.minimumHeight: Kirigami.Units.gridUnit * 20
        today: root.now
        firstDayOfWeek: Qt.locale().firstDayOfWeek
    }
}
