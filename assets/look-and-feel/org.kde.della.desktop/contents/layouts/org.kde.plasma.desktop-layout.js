// Della: floating dock (bottom), clock island (top centre), tray island (top right).
function island(location, alignment, height) {
    var p = new Panel;
    p.location = location;
    p.alignment = alignment;
    p.lengthMode = "fit";
    p.floating = true;
    p.opacity = "translucent";
    p.height = height;
    return p;
}

var dock = island("bottom", "center", 48);
var kickoff = dock.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = ["General"];
kickoff.writeConfig("icon", "start-here-kde-symbolic");
kickoff.currentConfigGroup = ["Shortcuts"];
kickoff.writeConfig("global", "Alt+F1");
dock.addWidget("org.kde.plasma.pager");
var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("iconSpacing", 0);
// Launchers for apps that are not installed are skipped by the task manager.
tasks.writeConfig("launchers", ["applications:systemsettings.desktop", "applications:org.kde.konsole.desktop",
    "preferred://filemanager", "preferred://browser", "applications:obsidian.desktop", "applications:code.desktop"]);
dock.addWidget("org.kde.plasma.marginsseparator");

var clockIsland = island("top", "center", 34);
clockIsland.hiding = "dodgewindows";
clockIsland.addWidget("org.kde.della.clock");

var trayIsland = island("top", "right", 34);
trayIsland.hiding = "dodgewindows";
var memory = trayIsland.addWidget("org.kde.plasma.systemmonitor");
memory.currentConfigGroup = ["Appearance"];
memory.writeConfig("chartFace", "org.kde.ksysguard.piechart");
memory.writeConfig("title", "Memory Usage");
memory.currentConfigGroup = ["Sensors"];
memory.writeConfig("highPrioritySensorIds", '["memory/physical/used"]');
memory.writeConfig("lowPrioritySensorIds", '["memory/physical/total"]');
memory.writeConfig("totalSensors", '["memory/physical/usedPercent"]');
trayIsland.addWidget("org.kde.plasma.systemtray");

var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = "org.kde.image";
}
