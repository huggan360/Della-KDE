#!/usr/bin/env python3
"""User-facing color and animation settings for the Della popup border."""
from pathlib import Path
import os,sys
from PySide6.QtCore import QSettings,Qt
from PySide6.QtGui import QColor,QPainter,QPen,QLinearGradient,QFont
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QCheckBox,QPushButton,QColorDialog,QSpinBox,QFormLayout
CFG=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'));CFG.mkdir(parents=True,exist_ok=True)
settings=QSettings(str(CFG/'della-borders.ini'),QSettings.IniFormat)
app=QApplication(sys.argv);app.setApplicationName('Della Borders');app.setDesktopFileName('della-borders')
window=QWidget();window.setWindowTitle('Della — dock border');window.setMinimumWidth(440)
layout=QVBoxLayout(window);layout.setContentsMargins(24,24,24,24);layout.setSpacing(16)
title=QLabel('Dock border');f=title.font();f.setPointSize(18);f.setBold(True);title.setFont(f);layout.addWidget(title)
subtitle=QLabel('2px living gradient around the dock · 14px outer, 12px inner radius');layout.addWidget(subtitle)
enabled=QCheckBox('Show the dock border');enabled.setChecked(settings.value('enabled',True,type=bool));layout.addWidget(enabled)
follow=QCheckBox('Follow the KDE theme accent');follow.setChecked(settings.value('followAccent',False,type=bool));layout.addWidget(follow)
colors=[QColor(settings.value('color1','#2bb3a1')),QColor(settings.value('color2','#3f7fe6'))]
row=QHBoxLayout();buttons=[]
def save():
 for k,v in {'enabled':enabled.isChecked(),'followAccent':follow.isChecked(),'animated':animated.isChecked(),'color1':colors[0].name(),'color2':colors[1].name(),'cycleSeconds':speed.value()}.items():settings.setValue(k,v)
 settings.sync()
 for i,b in enumerate(buttons):b.setEnabled(not follow.isChecked());b.setText(('First color: ' if i==0 else 'Second color: ')+colors[i].name())
def choose(index):
 color=QColorDialog.getColor(colors[index],window,'Choose gradient color')
 if color.isValid():colors[index]=color;save()
for i in range(2):
 b=QPushButton();b.clicked.connect(lambda checked=False,index=i:choose(index));row.addWidget(b);buttons.append(b)
layout.addLayout(row)
animated=QCheckBox('Animate with gentle changes of speed');animated.setChecked(settings.value('animated',True,type=bool));layout.addWidget(animated)
form=QFormLayout();speed=QSpinBox();speed.setRange(10,120);speed.setSuffix(' seconds');speed.setValue(settings.value('cycleSeconds',32,type=int));form.addRow('Time per rotation',speed);layout.addLayout(form)
note=QLabel('Changes appear on the dock within a second.\nDisable animation for a static 45° gradient.');note.setWordWrap(True);layout.addWidget(note)
for c in [enabled,follow,animated]:c.toggled.connect(save)
speed.valueChanged.connect(save)
close=QPushButton('Done');close.clicked.connect(window.close);layout.addWidget(close,alignment=Qt.AlignRight)
save();window.show();sys.exit(app.exec())
