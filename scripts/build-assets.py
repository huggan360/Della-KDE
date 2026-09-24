#!/usr/bin/env python3
"""Generate the original Della vector artwork. No downloaded theme assets."""
from pathlib import Path
import json, configparser
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets'
TOKENS=json.loads((ROOT/'design-tokens.json').read_text())
RADIUS=TOKENS['radius']
PANEL_PADDING=TOKENS['panelPadding']
POPUP_PADDING=TOKENS['popupPadding']
def inner_radius(inset): return max(0,RADIUS-inset)
# Controls sit inside a window's padding, so their radius is the window radius minus that inset.
CONTROL_RADIUS=inner_radius(TOKENS['controlInset'])
import os
GLASS=dict(TOKENS['glass'])
_rc=configparser.ConfigParser();_rc.optionxform=str
_rc.read(Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'dellarc')
if _rc.has_section('Glass'):
 for key,token in [('Mode','mode'),('DarkTint','darkTint'),('LightTint','lightTint')]:
  if key in _rc['Glass']:GLASS[token]=_rc['Glass'][key]
 for key,token in [('DarkOpacity','darkOpacity'),('LightOpacity','lightOpacity')]:
  if key in _rc['Glass']:GLASS[token]=float(_rc['Glass'][key])
def rgb(hexcolor):return ','.join(str(int(hexcolor[i:i+2],16)) for i in (1,3,5))
def kind_radius(kind):
 if kind in ['window','menu','tooltip']:return RADIUS
 if kind=='menuitem':return inner_radius(4)
 if kind in ['scrollbarslider','tr']:return 4
 return CONTROL_RADIUS
def write(p,s):
 p=A/p; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s)
def svg(body): return '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">'+body+'</svg>'
def paint(color,alpha):
 if color.startswith('ColorScheme-'):return f'class="{color}" style="fill:currentColor;fill-opacity:{alpha}"'
 return f'fill="{color}" fill-opacity="{alpha}"'
SCHEME_STYLE='<defs><style type="text/css" id="current-color-scheme">.ColorScheme-Background{color:#171e25;}.ColorScheme-Text{color:#eef0f3;}</style></defs>'
def scheme_svg(body):return svg(SCHEME_STYLE+body)
def frame(prefix='',r=RADIUS,fill='#152133',alpha=.52,line='#c5f4ff',la=.28,center=None,even=False,shine=0):
 # Each tile has its own exact bounds; no clipping/filter dependencies in KSvg.
 n=64; b=r; e=n-r; sep='-' if prefix else ''; out=''
 shapes={'center':f'<rect x="{b}" y="{b}" width="{n-2*b}" height="{n-2*b}"/>','top':f'<path d="M {b},0 H {e} V {b} H {b} Z"/>','bottom':f'<path d="M {b},{e} H {e} V {n} H {b} Z"/>','left':f'<path d="M 0,{b} H {b} V {e} H 0 Z"/>','right':f'<path d="M {e},{b} H {n} V {e} H {e} Z"/>','topleft':f'<path d="M 0,{b} A {b},{b} 0 0 1 {b},0 V {b} Z"/>','topright':f'<path d="M {e},0 A {b},{b} 0 0 1 {n},{b} H {e} Z"/>','bottomleft':f'<path d="M 0,{e} H {b} V {n} A {b},{b} 0 0 1 0,{e} Z"/>','bottomright':f'<path d="M {e},{e} H {n} A {b},{b} 0 0 1 {e},{n} Z"/>'}
 edges={'top':f'M {b},0 H {e} V 1 H {b} Z','bottom':f'M {b},{n-1} H {e} V {n} H {b} Z','left':f'M 0,{b} H 1 V {e} H 0 Z','right':f'M {n-1},{b} H {n} V {e} H {n-1} Z','topleft':f'M 0,{b} A {b},{b} 0 0 1 {b},0 V 1 A {b-1},{b-1} 0 0 0 1,{b} Z','topright':f'M {e},0 A {b},{b} 0 0 1 {n},{b} H {n-1} A {b-1},{b-1} 0 0 0 {e},1 Z','bottomleft':f'M 0,{e} A {b},{b} 0 0 0 {b},{n} V {n-1} A {b-1},{b-1} 0 0 1 1,{e} Z','bottomright':f'M {n},{e} A {b},{b} 0 0 1 {e},{n} V {n-1} A {b-1},{b-1} 0 0 0 {n-1},{e} Z'}
 for k,s in shapes.items():
  ident=center if k=='center' and center else prefix+sep+k
  out+=f'<g id="{ident}"><g {paint(fill,alpha)}>{s}</g>'
  if k in edges and la: out+=f'<path d="{edges[k]}" {paint(line,la if even or "top" in k else la*.5)}/>'
  if k=='top' and shine:
   # Light catching the top glass edge, brightest mid-span (the tile stretches across the surface).
   gid=f'shine-{prefix or "frame"}'
   out+=f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{b}" y1="0" x2="{e}" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity="{shine}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient><rect x="{b}" y="0" width="{e-b}" height="1" fill="url(#{gid})"/>'
  out+='</g>'
 return out

def mask_frame(r=RADIUS):
 n=64;b=r;e=n-r;out=''
 shapes={'center':f'<rect x="{b}" y="{b}" width="{n-2*b}" height="{n-2*b}"/>','top':f'<path d="M {b},1 H {e} V {b} H {b} Z"/>','bottom':f'<path d="M {b},{e} H {e} V {n-1} H {b} Z"/>',
  'left':f'<path d="M 1,{b} H {b} V {e} H 1 Z"/>','right':f'<path d="M {e},{b} H {n-1} V {e} H {e} Z"/>',
  'topleft':f'<path d="M 1,{b} A {b-1},{b-1} 0 0 1 {b},1 V {b} Z"/>','topright':f'<path d="M {e},1 A {b-1},{b-1} 0 0 1 {n-1},{b} H {e} Z"/>',
  'bottomleft':f'<path d="M 1,{e} H {b} V {n-1} A {b-1},{b-1} 0 0 1 1,{e} Z"/>','bottomright':f'<path d="M {e},{e} H {n-1} A {b-1},{b-1} 0 0 1 {e},{n-1} Z"/>'}
 for k,shape in shapes.items():out+=f'<g id="mask-{k}"><g fill="#000">{shape}</g></g>'
 return out

def hints(m=10,side=None):return ''.join(f'<rect id="hint-{d}-margin" x="100" y="100" width="{side if side is not None and d in ("left","right") else m}" height="{side if side is not None and d in ("left","right") else m}"/>' for d in ['top','bottom','left','right'])+'<rect id="hint-stretch-borders" width="1" height="1"/>'
meta={'KPlugin':{'Id':'Della','Name':'Della','Description':'Original smoked glass, ice highlights and soft rounded surfaces','Version':'1.0','License':'MIT','Authors':[{'Name':'Hugo'}]},'X-Plasma-API':'5.0'}
write(Path('plasma/Della/metadata.json'),json.dumps(meta,indent=2))
write(Path('plasma/Della/plasmarc'),'[ContrastEffect]\nenabled=true\ncontrast=0.12\nintensity=1.0\nsaturation=1.0\n\n[BlurBehindEffect]\nenabled=true\n\n[AdaptiveTransparency]\nenabled=true\n')
GLASS_EDGE=dict(line='ColorScheme-Text',la=.15,even=True)
SHELL_SURFACES={'panel-background','translucentbackground'}
SHELL_ALPHA=GLASS['darkOpacity']
for name,r,alpha in [('panel-background',RADIUS,SHELL_ALPHA),('background',RADIUS,SHELL_ALPHA),('translucentbackground',RADIUS,SHELL_ALPHA),('tooltip',RADIUS,SHELL_ALPHA)]:
 body=frame(r=r,fill='ColorScheme-Background',alpha=alpha,**(dict(la=0) if name in SHELL_SURFACES else GLASS_EDGE))+mask_frame(r)+(hints(PANEL_PADDING,side=12) if name=='panel-background' else hints(4) if name=='tooltip' else hints(POPUP_PADDING))
 write(Path(f'plasma/Della/widgets/{name}.svg'),scheme_svg(body))
# Dialog and panel opacity variants use the same geometry.
write(Path('plasma/Della/dialogs/background.svg'),scheme_svg(frame(r=RADIUS,fill='ColorScheme-Background',alpha=SHELL_ALPHA,**GLASS_EDGE)+mask_frame(RADIUS)+hints(10)))
for variant,alpha in [('opaque',1),('translucent',SHELL_ALPHA)]:
 write(Path(f'plasma/Della/{variant}/widgets/panel-background.svg'),scheme_svg(frame(r=RADIUS,fill='ColorScheme-Background',alpha=alpha,la=0)+mask_frame(RADIUS)+hints(PANEL_PADDING,side=12)))
# No widgets/tasks.svg: the dock uses KDE's standard Breeze task indicators and icon sizing.
# No widgets/button.svg: shell buttons (notification close, launcher, tray) use KDE's standard Breeze buttons.
# Window decoration: true compositor blur mask and independent button states.
meta['KPackageStructure']='KWin/Aurorae'
write(Path('aurorae/Della/metadata.json'),json.dumps(meta,indent=2))
write(Path('aurorae/Della/metadata.desktop'),'[Desktop Entry]\nName=Della\nX-KDE-PluginInfo-Name=Della\nX-KDE-PluginInfo-Version=1.0\nX-KDE-PluginInfo-License=MIT\nType=Service\n')
body=frame('decoration',RADIUS,alpha=.48)+frame('decoration-inactive',RADIUS,alpha=.60,la=.12)+mask_frame(RADIUS)
body+='<rect id="decoration-maximized-center" x="100" y="0" width="64" height="64" fill="#152133" fill-opacity=".65"/>'
write(Path('aurorae/Della/decoration.svg'),svg(body+'<rect id="hint-stretch-borders" width="1" height="1"/>'))
write(Path('aurorae/Della/Dellarc'),'''[General]
ActiveTextColor=231,245,255
InactiveTextColor=149,173,193
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=140
Shadow=false
UseTextShadow=false
LeftButtons=
RightButtons=IAX
[Layout]
BorderLeft=1
BorderRight=1
BorderBottom=10
TitleHeight=26
TitleEdgeTop=8
TitleEdgeBottom=6
TitleEdgeLeft=16
TitleEdgeRight=14
TitleEdgeTopMaximized=4
TitleEdgeBottomMaximized=4
TitleEdgeLeftMaximized=10
TitleEdgeRightMaximized=10
ButtonWidth=22
ButtonHeight=22
ButtonSpacing=3
ButtonMarginTop=2
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
''')
glyphs={'close':'M 8,8 L 16,16 M 16,8 L 8,16','minimize':'M 7,9 L 12,14 L 17,9','maximize':'M 7,14 L 12,9 L 17,14','restore':'M 8,10 H 14 V 16 H 8 Z M 10,8 H 16 V 14','alldesktops':'M 8,8 H 16 V 16 H 8 Z','keepabove':'M 7,14 L 12,9 L 17,14','keepbelow':'M 7,10 L 12,15 L 17,10','shade':'M 7,15 L 12,10 L 17,15 M 7,7 H 17','help':'M 9,9 C 9,5 17,5 16,10 L 12,13 M 12,16 V 17','appmenu':'M 7,8 H 17 M 7,12 H 17 M 7,16 H 17'}
for name,path in glyphs.items():
 body=''
 for i,(state,opacity) in enumerate([('active',.10),('inactive',.045),('hover',.26),('hover-inactive',.20),('pressed',.38),('pressed-inactive',.3),('deactivated',.025)]):
  hover=state.startswith('hover') or state.startswith('pressed')
  col='#eff0f1'
  bg='#da4453' if name=='close' else '#ffffff'
  body+=f'<g id="{state}-center" transform="translate({i*30},0)"><rect width="24" height="24" fill="none"/>'
  if hover:body+=f'<circle cx="12" cy="12" r="10" fill="{bg}" fill-opacity="{.9 if name=="close" else .18}"/>'
  body+=f'<path d="{path}" fill="none" stroke="{col}" stroke-opacity="{.5 if state in ("inactive","deactivated") else 1}" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></g>'

 write(Path(f'aurorae/Della/{name}.svg'),svg(body))
# KDE palette, based on the standard KDE color-scheme schema.
c=configparser.ConfigParser();c.optionxform=str
c.read('/usr/share/color-schemes/BreezeDark.colors')
for sec in c.sections():
 if sec.startswith('Colors:'):
  for key,val in {'BackgroundNormal':rgb(GLASS['darkTint']),'BackgroundAlternate':rgb(GLASS['darkTint']),'ForegroundNormal':'238,240,243','ForegroundInactive':'135,156,179','DecorationFocus':'43,179,161','DecorationHover':'63,127,230','ForegroundLink':'99,160,245'}.items(): c[sec][key]=val
c['Colors:Selection']['BackgroundNormal']='31,158,143'
c['General']['Name']='Della'
for key in list(c['WM']):
 if 'Foreground' in key:c['WM'][key]='238,240,243'
 else:c['WM'][key]=rgb(GLASS['darkTint'])
p=A/'color-schemes/Della.colors';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('w') as f:c.write(f,space_around_delimiters=False)
# Original Qt Widgets assets. Kvantum supplies the style engine and fallback glyphs.
body=''
for kind in ['button','toolbutton','lineedit','menuitem','itemview','tab','tabframe','header','progress','progress-pattern','scrollbarslider','tr','toolbar','menu','tooltip','window','group','dock']:
 for state in ['normal','focused','pressed','toggled','disabled']:
  fill='#eef2f8'; alpha={'normal':.07,'focused':.16,'pressed':.26,'toggled':.21,'disabled':.035}[state];la=.18
  if kind in ['window','menu','tooltip']:
   fill='TINTCOLOR';alpha={'window':'TINTALPHA','menu':.82,'tooltip':.88}[kind];la=.22
  elif kind in ['toolbar','dock','tabframe','group']:alpha=0;la=0
  elif kind=='tab':
   # Tab bars (Konsole, Dolphin) stay one sheet of glass: only hover and the current tab show.
   alpha={'normal':0,'focused':.10,'pressed':.16,'toggled':.14,'disabled':0}[state];la=.14 if state=='toggled' else 0
  elif kind in ['progress-pattern','scrollbarslider','tr']:alpha=.60;la=0
  elif kind in ['menuitem','itemview','toolbutton'] and state=='normal':alpha=0;la=0
  pre=kind+'-'+state
  body+=frame(pre,kind_radius(kind),fill,alpha,la=la,center=pre)
write(Path('Kvantum/Della/Della.svg'),svg(body))
write(Path('Kvantum/Della/Della.kvconfig'),'''[%General]
author=Hugo
comment=Original Della smoked-glass widget theme
composite=true
translucent_windows=true
blurring=true
popup_blurring=true
reduce_window_opacity=0
reduce_menu_opacity=0
respect_DE=true
no_window_pattern=true
dark_titlebar=true
animate_states=true
group_toolbar_buttons=false
slim_toolbars=false
toolbar_item_spacing=6
toolbar_interior_spacing=5
layout_spacing=8
layout_margin=10
scroll_width=8
scroll_arrows=false
transient_scrollbar=true
small_icon_size=16
large_icon_size=32
button_icon_size=16
toolbar_icon_size=22
check_size=16
alt_mnemonic=true
x11drag=menubar_and_primary_toolbar
menu_shadow_depth=0
tooltip_shadow_depth=0
menu_blur_radius=16
tooltip_blur_radius=16
[GeneralColors]
window.color=TINTCOLOR
base.color=TINTCOLOR
alt.base.color=#1b2839
button.color=#263c50
light.color=#364f64
mid.light.color=#30465c
dark.color=#0c1420
mid.color=#213246
highlight.color=#1f9e8f
inactive.highlight.color=#1d5e57
text.color=#eef0f3
window.text.color=#eef0f3
button.text.color=#eef0f3
disabled.text.color=#879cb3
tooltip.text.color=#eef0f3
highlight.text.color=#ffffff
link.color=#63a0f5
link.visited.color=#b6aaff
[Hacks]
transparent_dolphin_view=true
transparent_ktitle_label=true
blur_translucent=true
respect_darkness=true
force_size_grip=false
[WindowTranslucent]
interior=true
interior.element=window
frame=false
[Window]
interior=true
interior.element=window
frame=false
'''+''.join(f'''\n[{section}]
frame=true
frame.element={element}
interior=true
interior.element={element}
frame.top={radius}
frame.bottom={radius}
frame.left={radius}
frame.right={radius}
text.normal.color=#eef0f3
text.focus.color=#ffffff
text.press.color=#ffffff
text.toggle.color=#ffffff
text.margin.left=4
text.margin.right=4
text.margin.top=2
text.margin.bottom=2
''' for section,element,radius in [(section,element,0 if element=='toolbar' else kind_radius(element)) for section,element in [('PanelButtonCommand','button'),('PanelButtonTool','toolbutton'),('LineEdit','lineedit'),('Menu','menu'),('MenuItem','menuitem'),('ToolTip','tooltip'),('ItemView','itemview'),('Tab','tab'),('TabFrame','tabframe'),('HeaderSection','header'),('Toolbar','toolbar'),('Progressbar','progress'),('ProgressbarContents','progress-pattern'),('ScrollbarSlider','scrollbarslider'),('ScrollbarTransientSlider','tr')]]))
# Wallpaper: assets/wallpaper-package/Della (static light/dark package, see SOURCE.txt).
print('Generated original Della assets in',A)
# Complete the Qt material states, including Qt's expanded/border fallbacks.
p=A/'Kvantum/Della/Della.svg'
body=p.read_text().removesuffix('</svg>')
for base in ['button','toolbutton','lineedit','tab','menuitem','itemview']:
 for mode in ['border-','expand-']:
  for state in ['normal','focused','pressed','toggled','disabled']:
   alpha={'normal':.07,'focused':.16,'pressed':.26,'toggled':.21,'disabled':.035}[state]
   pre=mode+base+'-'+state
   body+=frame(pre,kind_radius(base),'#eef2f8',alpha,la=.18,center=pre)
for state in ['normal','focused','pressed','toggled','disabled']:
 for kind,r,fill,alpha in [('common',CONTROL_RADIUS,'#eef2f8',.06),('slider',2,'#eef2f8',.16)]:
  pre=kind+'-'+state;body+=frame(pre,r,fill,alpha,la=0,center=pre)
 for kind in ['checkbox','radio']:
  for check in ['', '-checked','-tristate']:
   ident=kind+check+'-'+state;fill='#2bb3a1' if check else '#24394e';stroke='#b5ebfa' if state=='focused' else '#6a8ba1'
   shape='<circle cx="10" cy="10" r="8"' if kind=='radio' else '<rect x="2" y="2" width="16" height="16" rx="5"'
   body+=f'<g id="{ident}"><rect width="20" height="20" fill="none"/>{shape} fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
   if check:
    if kind=='radio':body+='<circle cx="10" cy="10" r="3" fill="#142032"/>'
    else:body+='<path d="M 6,10 L 9,13 L 14,7" fill="none" stroke="#142032" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
   body+='</g>'
 for kind in ['slidercursor','slidercursor-tickless']:
  body+=f'<g id="{kind}-{state}"><circle cx="10" cy="10" r="9" fill="#2bb3a1"/><circle cx="10" cy="10" r="5" fill="#bff0e8"/></g>'
 for direction,path in [('up','M 4,10 L 8,6 L 12,10'),('down','M 4,6 L 8,10 L 12,6'),('left','M 10,4 L 6,8 L 10,12'),('right','M 6,4 L 10,8 L 6,12'),('plus','M 4,8 H 12 M 8,4 V 12'),('minus','M 4,8 H 12')]:
  body+=f'<g id="arrow-{direction}-{state}"><rect width="16" height="16" fill="none"/><path d="{path}" fill="none" stroke="#c0e9f7" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></g>'
p.write_text(body+'</svg>')
p=A/'Kvantum/Della/Della.kvconfig'
s=p.read_text().replace('frame=true\n','frame=true\nframe.expansion=0\nframe.patternsize=0\n')
s+='''
[Dialog]
interior=true
interior.element=window
[DialogTranslucent]
interior=true
interior.element=window
[GenericFrame]
frame=false
interior=false
[Focus]
frame=false
interior=false
[Slider]
frame=true
frame.element=slider
frame.top=2
frame.bottom=2
frame.left=2
frame.right=2
interior=true
interior.element=slider
[SliderCursor]
frame=false
interior=true
interior.element=slidercursor
[CheckBox]
frame=false
interior=true
interior.element=checkbox
[RadioButton]
frame=false
interior=true
interior.element=radio
'''
p.write_text(s)
# Light application preset; shell panels stay neutral clear glass in either mode.
import shutil
light=A/'aurorae/DellaLight';shutil.copytree(A/'aurorae/Della',light,dirs_exist_ok=True)
for p in light.glob('*.svg'):
 s=p.read_text().replace('#152133','#f2f3f5').replace('#eff0f1','#25282d').replace('#c5f4ff','#ffffff')
 p.write_text(s)
p=light/'Dellarc';s=p.read_text().replace('ActiveTextColor=231,245,255','ActiveTextColor=35,39,46').replace('InactiveTextColor=149,173,193','InactiveTextColor=103,111,120');p.unlink();(light/'DellaLightrc').write_text(s)
p=light/'metadata.json';m=json.loads(p.read_text());m['KPlugin']['Id']='DellaLight';m['KPlugin']['Name']='Della Light';p.write_text(json.dumps(m,indent=2))
p=light/'metadata.desktop';p.write_text(p.read_text().replace('Della','DellaLight'))
light=A/'Kvantum/DellaLight';light.mkdir(parents=True,exist_ok=True)
replacements={'#1b2839':'#e4e9ee','#263c50':'#dae6ed','#364f64':'#ffffff','#30465c':'#e5edf2','#0c1420':'#b5c1cb','#213246':'#ced8e0','#eef0f3':'#242b33','#879cb3':'#788692','#2bb3a1':'#178c7e','#63a0f5':'#2f69c8','#b6aaff':'#6f5aae','#182638':'#dfe6ec','#eef2f8':'#1a1d24','#c0e9f7':'#344d5a','#24394e':'#cbdce5','#142032':'#eef6fa'}
for ext in ['svg','kvconfig']:
 s=(A/f'Kvantum/Della/Della.{ext}').read_text()
 for old,new in replacements.items():s=s.replace(old,new)
 (light/f'DellaLight.{ext}').write_text(s.replace('TINTCOLOR',GLASS['lightTint']).replace('TINTALPHA',str(GLASS['lightOpacity'])))
for ext in ['svg','kvconfig']:
 p=A/f'Kvantum/Della/Della.{ext}';p.write_text(p.read_text().replace('TINTCOLOR',GLASS['darkTint']).replace('TINTALPHA',str(GLASS['darkOpacity'])))
c=configparser.ConfigParser();c.optionxform=str;c.read(A/'color-schemes/Della.colors')
for sec in c.sections():
 if sec.startswith('Colors:'):
  for key,val in {'BackgroundNormal':rgb(GLASS['lightTint']),'BackgroundAlternate':rgb(GLASS['lightTint']),'ForegroundNormal':'36,43,51','ForegroundInactive':'120,134,146','DecorationFocus':'23,140,126','ForegroundLink':'47,105,200'}.items():c[sec][key]=val
c['Colors:Selection']['BackgroundNormal']='31,158,143';c['Colors:Selection']['ForegroundNormal']='255,255,255';c['General']['Name']='Della Light'
for k in list(c['WM']):c['WM'][k]='36,43,51' if 'Foreground' in k else rgb(GLASS['lightTint'])
with (A/'color-schemes/DellaLight.colors').open('w') as f:c.write(f,space_around_delimiters=False)
# Konsole: the terminal is painted with exactly the glass tint and opacity, so the titlebar,
# tab bar and terminal read as one sheet. Konsole replaces (not stacks) its background pixels.
ANSI={'Color0':'35,38,39','Color0Faint':'49,54,59','Color0Intense':'127,140,141','Color1':'237,21,21','Color1Faint':'120,50,40','Color1Intense':'192,57,43','Color2':'17,209,22','Color2Faint':'23,162,98','Color2Intense':'28,220,154','Color3':'246,116,0','Color3Faint':'182,86,25','Color3Intense':'253,188,75','Color4':'29,153,243','Color4Faint':'27,102,143','Color4Intense':'61,174,233','Color5':'155,89,182','Color5Faint':'97,74,115','Color5Intense':'142,68,173','Color6':'26,188,156','Color6Faint':'24,108,96','Color6Intense':'22,160,133','Color7':'252,252,252','Color7Faint':'99,104,109','Color7Intense':'255,255,255'}
for name,tint,opacity,fg,fgfaint,fgintense in [('Della',GLASS['darkTint'],GLASS['darkOpacity'],'244,246,250','200,204,212','255,255,255')]:
 colors=dict(ANSI,Background=rgb(tint),BackgroundFaint=rgb(tint),BackgroundIntense=rgb(tint),Foreground=fg,ForegroundFaint=fgfaint,ForegroundIntense=fgintense)
 text=''.join(f'[{k}]\nColor={v}\n\n' for k,v in colors.items())
 text+=f'[General]\nBlur=true\nColorRandomization=false\nDescription={name.replace("Light"," Light")}\nOpacity={opacity}\nWallpaper=\n'
 write(Path(f'konsole/{name}.colorscheme'),text)
# Global Theme (look-and-feel): defaults only. Layouts, lock screen, splash and the login greeter
# fall back to KDE's Breeze QML, so they keep KDE's standard design with Della's colors,
# Plasma theme and wallpaper. The login screen follows this package too (login-screen/).
lnf=A/'look-and-feel/org.kde.della.desktop'
write(lnf.relative_to(A)/'metadata.json',json.dumps({'KPlugin':{'Id':'org.kde.della.desktop','Name':'Della','Description':'Frosted glass windows, clear-glass panels and teal/blue waves','License':'MIT','Authors':[{'Name':'Hugo'}],'Website':''},'KPackageStructure':'Plasma/LookAndFeel'},indent=2))
write(lnf.relative_to(A)/'contents/defaults','''[kdeglobals][KDE]
widgetStyle=kvantum

[kdeglobals][General]
ColorScheme=Della

[plasmarc][Theme]
name=Della

[Wallpaper]
Image=Della

[kwinrc][org.kde.kdecoration2]
library=org.kde.della
theme=

[ksplashrc][KSplash]
Theme=org.kde.breeze.desktop
''')
try:
 from PySide6.QtGui import QImage
 from PySide6.QtCore import Qt
 src=QImage(str(ROOT/'assets/wallpaper-package/Della/contents/images_dark/3840x2160.jpg'))
 (lnf/'contents/previews').mkdir(parents=True,exist_ok=True)
 src.scaled(1920,1080,Qt.KeepAspectRatio,Qt.SmoothTransformation).save(str(lnf/'contents/previews/fullscreenpreview.jpg'),'JPG',90)
 src.scaled(640,360,Qt.KeepAspectRatio,Qt.SmoothTransformation).save(str(lnf/'contents/previews/preview.png'))
except ImportError:
 pass
# Default desktop layout for the Global Theme (applied when "desktop and window layout" is chosen).
write(lnf.relative_to(A)/'contents/layouts/org.kde.plasma.desktop-layout.js','''// Della: floating dock (bottom), clock island (top centre), tray island (top right).
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
''')
# Della Light Plasma theme: same recolorable artwork, frostier panels (like light windows).
# apply-glass.py / install.py switch between Della and Della Light with the light/dark mode.
import shutil
light=A/'plasma/DellaLight';shutil.rmtree(light,ignore_errors=True);shutil.copytree(A/'plasma/Della',light)
for q in light.rglob('*.svg'):
 q.write_text(q.read_text().replace(f'fill-opacity:{SHELL_ALPHA}',f'fill-opacity:{GLASS["lightOpacity"]}'))
m=json.loads((light/'metadata.json').read_text());m['KPlugin']['Id']='DellaLight';m['KPlugin']['Name']='Della Light';(light/'metadata.json').write_text(json.dumps(m,indent=2))
