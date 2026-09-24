#!/usr/bin/env python3
"""Della Glass: choose light/dark, tint, glass opacity and blur for windows and Konsole."""
from pathlib import Path
import os,sys,json,subprocess,configparser
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QColor,QPainter,QLinearGradient,QPainterPath,QPen
from PySide6.QtWidgets import (QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QColorDialog,
                               QSlider,QFormLayout,QButtonGroup,QRadioButton,QMessageBox)
ROOT=Path(__file__).resolve().parents[1]
CFG=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
TOKENS=json.loads((ROOT/'design-tokens.json').read_text());GLASS=TOKENS['glass']
DEFAULTS={'Mode':GLASS['mode'],'DarkTint':GLASS['darkTint'],'DarkOpacity':GLASS['darkOpacity'],'LightTint':GLASS['lightTint'],
          'LightOpacity':GLASS['lightOpacity'],'BlurStrength':GLASS['blurStrength'],'NoiseStrength':GLASS['noiseStrength']}
PRESETS={'dark':[('Graphite','#1b1e26'),('Midnight','#131a2e'),('Ocean','#0f2230'),('Violet','#21182e'),('Rose','#2a1820'),('Forest','#142219')],
         'light':[('Frost','#f5f6f9'),('Sky','#e8f1fb'),('Lilac','#f0ebfa'),('Blush','#fbeef0'),('Mint','#ebf7f1'),('Sand','#f8f3ea')]}
rc=configparser.ConfigParser();rc.optionxform=str;rc.read(CFG/'dellarc')
if not rc.has_section('Glass'):rc.add_section('Glass')
state={k:rc['Glass'].get(k,str(v)) for k,v in DEFAULTS.items()}

class Preview(QWidget):
    """A glass window over a colorful backdrop, drawn with the chosen tint and opacity."""
    def __init__(self):
        super().__init__();self.setMinimumHeight(150)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        r=QRectF(self.rect())
        bg=QLinearGradient(r.topLeft(),r.bottomRight())
        for stop,color in [(0,'#3b5bdb'),(.45,'#9c36b5'),(.75,'#f76707'),(1,'#1098ad')]:bg.setColorAt(stop,QColor(color))
        clip=QPainterPath();clip.addRoundedRect(r,14,14);p.setClipPath(clip);p.fillRect(r,bg)
        light=state['Mode']=='light'
        tint=QColor(state['LightTint' if light else 'DarkTint']);tint.setAlphaF(float(state['LightOpacity' if light else 'DarkOpacity']))
        win=r.adjusted(40,24,-40,-24);path=QPainterPath();path.addRoundedRect(win,14,14)
        # Approximate the compositor's blur by softening the backdrop under the glass.
        soft=QColor(255,255,255,70 if light else 40);p.fillPath(path,soft);p.fillPath(path,tint)
        edge=QColor(0,0,0,36) if light else QColor(255,255,255,40);p.setPen(QPen(edge,1));p.drawPath(path)
        text=QColor(26,28,34) if light else QColor(244,246,250);p.setPen(text)
        f=p.font();f.setBold(True);p.setFont(f)
        p.drawText(QRectF(win.left(),win.top(),win.width(),36),Qt.AlignCenter,'Della — Konsole')
        f.setBold(False);f.setFamily('monospace');p.setFont(f)
        p.drawText(win.adjusted(18,48,0,0),Qt.AlignLeft|Qt.AlignTop,'~ ❯ echo "one sheet of glass"')

app=QApplication(sys.argv);app.setApplicationName('Della Glass');app.setDesktopFileName('della-glass')
window=QWidget();window.setWindowTitle('Della — glass');window.setMinimumWidth(480)
layout=QVBoxLayout(window);layout.setContentsMargins(24,24,24,24);layout.setSpacing(14)
title=QLabel('Window glass');f=title.font();f.setPointSize(18);f.setBold(True);title.setFont(f);layout.addWidget(title)
layout.addWidget(QLabel('Titlebars, app backgrounds and Konsole share this tint.'))
preview=Preview();layout.addWidget(preview)

modes=QButtonGroup(window);row=QHBoxLayout()
for mode,label in [('dark','Dark'),('light','Light')]:
    b=QRadioButton(label);b.setChecked(state['Mode']==mode);b.toggled.connect(lambda on,m=mode:on and set_mode(m));modes.addButton(b);row.addWidget(b)
row.addStretch();layout.addLayout(row)
swatches=QHBoxLayout();layout.addLayout(swatches)
custom=QPushButton();layout.addWidget(custom)
form=QFormLayout();opacity=QSlider(Qt.Horizontal);opacity.setRange(15,95);blur=QSlider(Qt.Horizontal);blur.setRange(1,15)
form.addRow('Glass opacity',opacity);form.addRow('Background blur',blur);layout.addLayout(form)

def key(name):return ('Light' if state['Mode']=='light' else 'Dark')+name
def refresh():
    while swatches.count():swatches.takeAt(0).widget().deleteLater()
    for name,color in PRESETS[state['Mode']]:
        b=QPushButton(name);b.setToolTip(color);b.clicked.connect(lambda checked=False,c=color:set_tint(c));swatches.addWidget(b)
    custom.setText('Custom tint: '+state[key('Tint')])
    opacity.blockSignals(True);opacity.setValue(round(float(state[key('Opacity')])*100));opacity.blockSignals(False)
    blur.blockSignals(True);blur.setValue(int(state['BlurStrength']));blur.blockSignals(False)
    preview.update()
def set_mode(mode):state['Mode']=mode;refresh()
def set_tint(color):state[key('Tint')]=color;refresh()
def choose():
    c=QColorDialog.getColor(QColor(state[key('Tint')]),window,'Glass tint')
    if c.isValid():set_tint(c.name())
custom.clicked.connect(choose)
opacity.valueChanged.connect(lambda v:(state.__setitem__(key('Opacity'),str(v/100)),preview.update()))
blur.valueChanged.connect(lambda v:state.__setitem__('BlurStrength',str(v)))

def apply():
    for k,v in state.items():rc['Glass'][k]=str(v)
    with (CFG/'dellarc').open('w') as f:rc.write(f,space_around_delimiters=False)
    result=subprocess.run([sys.executable,str(ROOT/'scripts/apply-glass.py')],capture_output=True,text=True)
    if result.returncode:QMessageBox.warning(window,'Della',result.stderr[-1200:])
    else:status.setText('Applied. Titlebars update now; reopen apps to refresh their interiors.')
def reset():
    state.update({k:str(v) for k,v in DEFAULTS.items() if k!='Mode'});refresh()
buttons=QHBoxLayout();r=QPushButton('Defaults');r.clicked.connect(reset);buttons.addWidget(r);buttons.addStretch()
a=QPushButton('Apply');a.setDefault(True);a.clicked.connect(apply);buttons.addWidget(a)
d=QPushButton('Close');d.clicked.connect(window.close);buttons.addWidget(d);layout.addLayout(buttons)
status=QLabel('');status.setWordWrap(True);layout.addWidget(status)
refresh();window.show();sys.exit(app.exec())
