// On a standard one-panel desktop, move the clock and tray into glass islands.
// Existing multi-panel layouts retain their widgets and placement.
var initial=panels();
var bottom=initial.filter(function(p){return p.location==='bottom';})[0];
if(!bottom){bottom=new Panel;bottom.location='bottom';bottom.addWidget('org.kde.plasma.kickoff');bottom.addWidget('org.kde.plasma.icontasks');}
// An island already exists if a top panel holds any of `types`; never create duplicates.
// New islands hide when a window covers them. `replacement` swaps in a Della widget
// Keep Plasma's stock clock so its layout and calendar follow KDE defaults.
function island(types,alignment,replacement){
 var host=null,widget=null;
 panels().forEach(function(p){p.widgets().forEach(function(w){if(types.indexOf(w.type)>=0){host=p;widget=w;}});});
 if(host && host.location==='top')return;
 var p=new Panel;p.location='top';p.alignment=alignment;p.lengthMode='fit';p.height=34;p.hiding='dodgewindows';
 if(replacement){if(widget)widget.remove();p.addWidget(replacement);}
 else if(widget)p.addWidget(widget);else p.addWidget(types[0]);
}
// Remove the earlier custom clock widget and use Plasma's standard clock/calendar.
panels().forEach(function(p){
 var ws=p.widgets();
 for(var k=0;k<ws.length;k++) if(ws[k].type==='org.kde.della.clock') ws[k].remove();
});
island(['org.kde.plasma.digitalclock'],'center');
island(['org.kde.plasma.systemtray'],'right');
// Restyle existing panels without deleting widgets, launchers, or notes.
var list = panels();
for (var i=0; i<list.length; i++) {
 var p=list[i];
 p.floating=true;
 p.opacity='translucent';
 p.lengthMode='fit';
 if(p.location==='bottom') {p.height=48; p.alignment='center';}
 else {p.height=34;}
 var widgets=p.widgets();
 for(var j=0;j<widgets.length;j++){
  var w=widgets[j];
  if(w.type==='org.kde.plasma.kickoff'){
   w.currentConfigGroup=['General']; w.writeConfig('icon','start-here-kde-symbolic');
  }
  if(w.type==='org.kde.plasma.icontasks'){
   w.currentConfigGroup=['General'];w.writeConfig('iconSpacing',0);
  }
 }
}
print('Restyled '+list.length+' existing panels.');
