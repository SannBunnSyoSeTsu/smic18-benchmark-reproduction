"""Draw all devices in case 25; read-only netlist/geometry, no simulation.

Run with the existing Bridge Python.  The layout is topology specific; unknown
instances or changed connectivity fail explicitly instead of disappearing.
After actually viewing all generated sheets and the full image, run
``schematic25.py --confirm-visual`` to record that review without regenerating.
"""
from __future__ import annotations
import argparse
import collections
import datetime
import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'cases/25-complementary-ab'
OUT=CASE/'schematic'
FONT=next(p for p in ['/usr/share/fonts/wqy-microhei/wqy-microhei.ttc','/usr/share/fonts/google-droid/DroidSansFallback.ttf','/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc'] if Path(p).is_file())
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=FONT).get_name(),'pdf.fonttype':42,
                     'svg.fonttype':'path','axes.unicode_minus':False})
INK='#173448';WIRE='#243e4c';BULK='#7c4385';GREEN='#14745e';MUTED='#5b6c78'
EXTENT=(0,44,0,25)
TITLES={1:'参考与共栅／转向偏置',2:'互补输入、源退化与尾电流转向',
        3:'折叠求和、镜负载与双路补偿',4:'浮动 Class-AB、复制偏置与输出'}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def number(s):
    m=re.fullmatch(r'([-+\d.eE]+)([fpnumkMG]?)',s)
    if not m:raise ValueError('Unsupported nonnumeric value: '+s)
    return float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'M':1e6,'G':1e9}[m[2]]


def read_design():
    text=(CASE/'circuit.scs').read_text();g=json.loads((CASE/'geometry.json').read_text())
    assert sha(CASE/'circuit.scs')==g['circuit_sha256'],'Geometry/netlist changed out of sync'
    sub=re.search(r'^subckt\s+(\w+)\s+\(([^)]+)\)',text,re.M)
    devices={}
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('//') or line.startswith(('simulator ','subckt ','ends ')):continue
        m=re.fullmatch(r'(\w+)\s+\(([^)]+)\)\s+(\w+)\s+(.+)',line)
        if not m:raise ValueError('Unparsed electrical line: '+line)
        name,nodes,model,tail=m.groups();params=dict(re.findall(r'(\w+)\s*=\s*([^\s]+)',tail))
        kind='MOS' if model in ('n18','p18') else {'resistor':'R','capacitor':'C'}.get(model)
        if kind is None:raise ValueError('Unsupported device: '+line)
        pins=dict(zip(['D','G','S','B'] if kind=='MOS' else ['1','2'],nodes.split()))
        assert len(nodes.split())==(4 if kind=='MOS' else 2) and name not in devices
        q=dict(name=name,kind=kind,model=model,pins=pins,parameters=params,source_line=raw)
        if kind=='MOS':q.update(W_unit_um=number(params['w'])*1e6,L_um=number(params['l'])*1e6,m=number(params.get('m','1')))
        else:q['value_SI']=number(params['r' if kind=='R' else 'c'])
        devices[name]=q
    mos={q['name']:q for q in g['devices']}
    assert set(mos)=={n for n,q in devices.items() if q['kind']=='MOS'}
    for n,q in mos.items():
        d=devices[n];assert list(d['pins'].values())==q['pins'] and d['model']==q['model']
        for key in ['W_unit_um','L_um','m']:assert math.isclose(d[key],q[key],rel_tol=1e-10,abs_tol=1e-10),(n,key)
    return devices,sub[1],sub[2].split(),g


class Sheet:
    """A drawing manifest stores the rendered pin coordinates and actual wires."""
    def __init__(self,ax,index,devices):
        self.ax=ax;self.index=index;self.devices=devices;self.instances={};self.pins={};self.wires=[];self.labels=[]
        ax.set(xlim=EXTENT[:2],ylim=EXTENT[2:]);ax.axis('off')

    def line(self,pts,**kw):
        obj,=self.ax.plot(*zip(*pts),color=kw.pop('color',INK),lw=kw.pop('lw',.85),**kw);return obj

    def text(self,x,y,s,size=7,color=INK,**kw):
        return self.ax.text(x,y,s,fontsize=size,color=color,**kw)

    def mos(self,name,x,y):
        d=self.devices[name];assert d['kind']=='MOS' and name not in self.instances
        pm=d['model']=='p18'
        self.line([(x-.6,y-.52),(x-.6,y+.52)],lw=1.25).set_gid(name+'_channel')
        self.line([(x-.94,y-.53),(x-.94,y+.53)],lw=.9)
        for v in [-1,1]:self.line([(x,y+v),(x,y+v*.43),(x-.6,y+v*.43)])
        if pm:
            self.line([(x-1.55,y),(x-1.16,y)])
            self.ax.add_patch(Circle((x-1.05,y),.105,edgecolor=INK,facecolor='white',lw=.8))
        else:self.line([(x-1.55,y),(x-.94,y)])
        self.line([(x+.86,y),(x+.2,y)],color=BULK,lw=.85)
        arrow=((x-.5,y),(x+.2,y)) if pm else ((x+.2,y),(x-.5,y))
        self.ax.add_patch(FancyArrowPatch(*arrow,arrowstyle='-|>',mutation_scale=6.3,lw=.7,color=BULK))
        pts={'D':(x,y-1 if pm else y+1),'S':(x,y+1 if pm else y-1),'G':(x-1.55,y),'B':(x+.86,y)}
        for pin,(xx,yy) in pts.items():
            self.pins[(name,pin)]=dict(point=(xx,yy),net=d['pins'][pin],connected=False)
        self.text(x+.14,y+.71,'S' if pm else 'D',5.4)
        self.text(x+.14,y-.84,'D' if pm else 'S',5.4)
        self.text(x-1.46,y+.18,'G',5.4);self.text(x+.37,y+.16,'B',5.4,color=BULK)
        self.text(x+.67,y+.69,name+'  '+d['model'],6.7,weight='bold').set_gid(name+'_name')
        self.text(x+.67,y-.79,f"{d['W_unit_um']:g}/{d['L_um']:g}  m={d['m']:g}",6.2,fontfamily='DejaVu Sans Mono').set_gid(name+'_WLm')
        self.instances[name]=dict(**d,sheet=self.index,origin=[x,y],rendered_pins={k:list(v) for k,v in pts.items()})
        self.wire(d['pins']['B'],pts['B'],(x+1.15,y),body=True)
        self.tag(d['pins']['B'],(x+1.15,y),body=True,ha='left',dy=.01)
        return name

    def passive(self,name,x,y,vertical=True,reverse=False):
        d=self.devices[name];assert d['kind'] in ('R','C') and name not in self.instances
        def tr(u,v):return (x+v,y+u) if vertical else (x+u,y+v)
        ends=[tr(.82,0),tr(-.82,0)]
        if not vertical:ends=ends[::-1]
        if reverse:ends=ends[::-1]
        if d['kind']=='R':
            self.line([tr(-.82,0),tr(-.5,0)]);self.line([tr(.5,0),tr(.82,0)])
            self.line([tr(-.5,-.17),tr(.5,-.17),tr(.5,.17),tr(-.5,.17),tr(-.5,-.17)])
            value=d['value_SI'];val=f'{value/1000:g}k' if value>=1000 else f'{value:g}'
            val+=' Ω'
        else:
            self.line([tr(-.82,0),tr(-.115,0)]);self.line([tr(.115,0),tr(.82,0)])
            for u in [-.115,.115]:self.line([tr(u,-.39),tr(u,.39)],lw=1.0)
            val=f"{d['value_SI']*1e12:g} pF"
        if vertical:self.text(x+.65,y+.2,name,6.7,weight='bold');self.text(x+.65,y-.35,val,6.5)
        else:self.text(x,y+.65,name+'  '+val,6.7,ha='center',weight='bold')
        for k,point in zip(['1','2'],ends):self.pins[(name,k)]=dict(point=point,net=d['pins'][k],connected=False)
        self.instances[name]=dict(**d,sheet=self.index,origin=[x,y],rendered_pins={k:list(v) for k,v in zip(['1','2'],ends)})

    def p(self,name,pin):return self.pins[(name,pin)]['point']

    def wire(self,net,*pts,body=False):
        pts=[tuple(x) for x in pts]
        assert len(pts)>=2 and all(a[0]==b[0] or a[1]==b[1] for a,b in zip(pts,pts[1:])),(net,pts)
        for pin,q in self.pins.items():
            if q['point'] in pts:
                assert q['net']==net,('Wrong routed pin',pin,q['net'],net)
                q['connected']=True
        self.line(pts,color=BULK if body else WIRE,lw=.7 if body else .85)
        self.wires.append(dict(net=net,points=[list(p) for p in pts],body=body))

    def tag(self,net,point,body=False,ha='left',dx=.15,dy=.17):
        x,y=point;label=net.upper() if net in ['vdd','vss','iref','vinn','vinp','vout'] else net
        self.text(x+dx,y+dy,label,6.35 if body else 7.0,color=BULK if body else GREEN,
                  ha=ha,va='center',weight='normal' if body else 'bold',fontfamily='DejaVu Sans Mono')
        self.labels.append(dict(net=net,point=list(point),text=label,body=body))

    def diode(self,name,net,yjoin):
        x,y=self.instances[name]['origin'];g=self.p(name,'G');d=self.p(name,'D')
        self.wire(net,g,(x-2.05,y),(x-2.05,yjoin),(x,yjoin),d)

    def finish(self):
        # Every remaining gate and terminal has a real conductor ending at an
        # explicit global net label, including every body (never implicit ties).
        for (name,pin),q in self.pins.items():
            if q['connected']:continue
            x,y=q['point'];d=self.instances[name]
            if pin=='G':end=(x-.55,y);self.wire(q['net'],(x,y),end);self.tag(q['net'],end,ha='right',dx=-.09,dy=0)
            elif d['kind']!='MOS' and all(pt[1]==d['origin'][1] for pt in d['rendered_pins'].values()):
                direction=1 if x>=d['origin'][0] else -1
                end=(x+.8*direction,y);self.wire(q['net'],(x,y),end)
                self.tag(q['net'],end,ha='left' if direction>0 else 'right',dx=.14*direction,dy=0)
            else:
                direction=1 if y>=d['origin'][1] else -1
                end=(x,y+.64*direction);self.wire(q['net'],(x,y),end);self.tag(q['net'],end)
        assert all(q['connected'] for q in self.pins.values())
        # Dots only on conductive junctions, never on plain wire crossings.
        segments=[]
        for wire in self.wires:
            for a,b in zip(wire['points'],wire['points'][1:]):
                if a!=b:segments.append((wire['net'],tuple(a),tuple(b)))
        points={(net,p) for net,a,b in segments for p in (a,b)}
        pinpts={q['point'] for q in self.pins.values()}
        for net,p in points:
            touching=[(a,b) for n,a,b in segments if n==net and on_segment(p,a,b)]
            degree=sum(1 if p in (a,b) else 2 for a,b in touching)
            if degree>=3 and p not in pinpts:
                self.ax.add_patch(Circle(p,.072,facecolor=WIRE,edgecolor='none',zorder=5))
        return self


def on_segment(p,a,b):
    return ((a[0]==b[0]==p[0] and min(a[1],b[1])-1e-9<=p[1]<=max(a[1],b[1])+1e-9)
        or (a[1]==b[1]==p[1] and min(a[0],b[0])-1e-9<=p[0]<=max(a[0],b[0])+1e-9))


def layout(ax,index,devices):
    z=Sheet(ax,index,devices);M=z.mos;P=z.passive;p=z.p;w=z.wire;tag=z.tag
    if index==1:
        for n,x,y in [('MREF',3,5),('MBP',9,17),('MBN',9,5),('MNCB',16,17),('MND',16,10),('MPD',23,14),('MPCB',23,5),('MNRB',30,17),('MNREF',30,10),('MPREF',37,14),('MPRB',37,5)]:M(n,x,y)
        for n,x,y in [('RNC',16,4),('RPC',23,18),('RNR',30,4),('RPR',37,18)]:P(n,x,y)
        w('vdd',(9,22.3),(37,22.3));tag('vdd',(9,22.3),dy=.35)
        for n in ['MBP','MNCB','MNRB']:x,_=p(n,'S');w('vdd',p(n,'S'),(x,22.3))
        for n in ['RPC','RPR']:x,_=p(n,'1');w('vdd',p(n,'1'),(x,22.3))
        w('vss',(3,1.4),(37,1.4));tag('vss',(3,1.4),dy=-.35)
        for n in ['MREF','MBN','MPCB','MPRB']:x,_=p(n,'S');w('vss',p(n,'S'),(x,1.4))
        for n in ['RNC','RNR']:x,_=p(n,'2');w('vss',p(n,'2'),(x,1.4))
        w('iref',p('MREF','D'),(3,10));z.diode('MREF','iref',8);tag('iref',(3,10))
        w('vbp',p('MBP','D'),p('MBN','D'));z.diode('MBP','vbp',13);tag('vbp',(9,11.8))
        w('vcn',p('MNCB','D'),p('MND','D'));z.diode('MND','vcn',13);tag('vcn',(16,14.5))
        w('ncb',p('MND','S'),p('RNC','1'));tag('ncb',(16,7))
        w('pcb',p('RPC','2'),p('MPD','S'));tag('pcb',(23,16.1))
        w('vcp',p('MPD','D'),p('MPCB','D'));z.diode('MPD','vcp',10.5);tag('vcp',(23,8.5))
        w('vrefn',p('MNRB','D'),p('MNREF','D'));z.diode('MNREF','vrefn',13);tag('vrefn',(30,14.5))
        w('nrefsrc',p('MNREF','S'),p('RNR','1'));tag('nrefsrc',(30,7))
        w('prefsrc',p('RPR','2'),p('MPREF','S'));tag('prefsrc',(37,16.1))
        w('vrefp',p('MPREF','D'),p('MPRB','D'));z.diode('MPREF','vrefp',10.5);tag('vrefp',(37,8.5))
    elif index==2:
        for n,x,y in [('MNINN',4,17.5),('MNINP',10,17.5),('MNT',7,5.5),('MPSD',18,20),('MNSW',18,14),('MPSM',24,20),('MPSW',24,11),('MNSD',24,4),('MNSM',18,4),('MPT',35,21),('MPINN',32,11.5),('MPINP',38,11.5)]:M(n,x,y)
        for n,x,y in [('RINN',4,13.5),('RINP',10,13.5),('RIPN',32,15.5),('RIPP',38,15.5)]:P(n,x,y)
        for n,x,y in [('RCM1',31,5),('CCM1',37,5),('RCM2',31,2),('CCM2',37,2)]:P(n,x,y,vertical=False)
        w('vdd',(18,23),(38,23));tag('vdd',(18,23),dy=.4)
        for n in ['MPSD','MPSM','MPT']:x,_=p(n,'S');w('vdd',p(n,'S'),(x,23))
        w('vss',(7,1),(24,1));tag('vss',(7,1),dy=-.35)
        for n in ['MNT','MNSM','MNSD']:x,_=p(n,'S');w('vss',p(n,'S'),(x,1))
        for mos,res,net in [('MNINN','RINN','ntn'),('MNINP','RINP','ntp')]:w(net,p(mos,'S'),p(res,'1'));tag(net,(p(mos,'S')[0],15.0))
        w('ntail',p('RINN','2'),(4,11),(10,11),p('RINP','2'));w('ntail',p('MNT','D'),(7,11));tag('ntail',(7,10))
        for mos,res,net in [('MPINN','RIPN','ptn'),('MPINP','RIPP','ptp')]:w(net,p(mos,'S'),p(res,'2'));tag(net,(p(mos,'S')[0],13.6))
        w('ptail',p('RIPN','1'),(32,18),(38,18),p('RIPP','1'));w('ptail',p('MPT','D'),(35,18));tag('ptail',(32,18),dy=.35)
        w('swnd',p('MPSD','D'),p('MNSW','D'));z.diode('MPSD','swnd',17);tag('swnd',(18,16))
        w('swpd',p('MPSW','D'),p('MNSD','D'));z.diode('MNSD','swpd',7);tag('swpd',(24,8.5))
        for r,c,n in [('RCM1','CCM1','cmin'),('RCM2','CCM2','cmip')]:w(n,p(r,'2'),p(c,'1'));tag(n,((p(r,'2')[0]+p(c,'1')[0])/2,p(r,'2')[1]),dy=-.32)
    elif index==3:
        for n,x,y in [('MFBASE',4,19),('MFADD',11,19),('MFSUB',4,10),('MFREF',11,10),('MPM1',22,21),('MPM2',34,21),('MPC1',22,17),('MPC2',34,17),('MNC1',22,11),('MNC2',34,11),('MFS1',22,7),('MFS2',34,7)]:M(n,x,y)
        for n,x,y in [('CCP',8,3),('RZP',18,3),('CCN',8,.9),('RZN',18,.9)]:P(n,x,y,vertical=False)
        w('vdd',(4,23),(34,23));tag('vdd',(4,23),dy=.35)
        for n in ['MFBASE','MFADD','MPM1','MPM2']:x,_=p(n,'S');w('vdd',p(n,'S'),(x,23))
        w('vss',(4,4.8),(34,4.8));tag('vss',(4,4.8),dy=.35)
        for n in ['MFSUB','MFREF','MFS1','MFS2']:x,_=p(n,'S');w('vss',p(n,'S'),(x,4.8))
        w('vbsink',p('MFBASE','D'),(4,14),(11,14),p('MFADD','D'))
        for n in ['MFSUB','MFREF']:x,_=p(n,'D');w('vbsink',p(n,'D'),(x,14))
        z.diode('MFREF','vbsink',12.5);tag('vbsink',(5.2,14),dy=.4)
        for a,b,n in [('MPM1','MPC1','fp1'),('MPM2','MPC2','fp2')]:w(n,p(a,'D'),p(b,'S'));tag(n,(p(a,'D')[0],19))
        w('ml',p('MPC1','D'),p('MNC1','D'));tag('ml',(22,14))
        w('ml',p('MPM1','G'),(18,21),(18,14),(22,14))
        for a,b,n in [('MNC1','MFS1','fn1'),('MNC2','MFS2','fn2')]:w(n,p(a,'S'),p(b,'D'));tag(n,(p(a,'S')[0],9))
        for cap,res,node,other in [('CCP','RZP','zp','fp2'),('CCN','RZN','zn','fn2')]:
            w(node,p(cap,'2'),p(res,'1'));tag(node,(13,p(cap,'2')[1]),dy=-.30)
            w('vout',p(cap,'1'),(4,p(cap,'1')[1]));tag('vout',(4,p(cap,'1')[1]),ha='right',dx=-.18,dy=0)
            w(other,p(res,'2'),(25,p(res,'2')[1]));tag(other,(25,p(res,'2')[1]),dy=0)
    elif index==4:
        for n,x,y in [('MABNS',6,20),('MABNU',6,13),('MABNL',6,6),('MABPL',17,20),('MABPU',17,13),('MABPS',17,6),('MABN',27,14),('MABP',33,14),('MOUTP',40,20),('MOUTN',40,5)]:M(n,x,y)
        P('CGP',27,21,reverse=True);P('CGN',27,6)
        w('vdd',(6,23),(40,23));tag('vdd',(6,23),dy=.4)
        for n in ['MABNS','MABPL','MOUTP']:x,_=p(n,'S');w('vdd',p(n,'S'),(x,23))
        w('vdd',p('CGP','2'),(27,23))
        w('vss',(6,1.5),(40,1.5));tag('vss',(6,1.5),dy=-.35)
        for n in ['MABNL','MABPS','MOUTN']:x,_=p(n,'S');w('vss',p(n,'S'),(x,1.5))
        w('vss',p('CGN','2'),(27,1.5))
        w('vabn',p('MABNS','D'),p('MABNU','D'));z.diode('MABNU','vabn',16.5);tag('vabn',(6,17.5))
        w('xn',p('MABNU','S'),p('MABNL','D'));z.diode('MABNL','xn',9.5);tag('xn',(6,10.5))
        w('yp',p('MABPL','D'),p('MABPU','S'));z.diode('MABPL','yp',16.5);tag('yp',(17,17.5))
        w('vabp',p('MABPU','D'),p('MABPS','D'));z.diode('MABPU','vabp',9.5);tag('vabp',(17,10.5))
        w('gp',p('MABN','D'),(27,17),(33,17),p('MABP','S'));w('gp',p('CGP','1'),(27,17))
        w('gp',(33,17),(36,17),(36,20),p('MOUTP','G'));tag('gp',(30,17),dy=.35)
        w('gn',p('MABN','S'),(27,10),(33,10),p('MABP','D'));w('gn',p('CGN','1'),(27,10))
        w('gn',(33,10),(36,10),(36,5),p('MOUTN','G'));tag('gn',(30,10),dy=.35)
        w('vout',p('MOUTP','D'),p('MOUTN','D'));tag('vout',(40,11.6),dy=.35)
    return z.finish()


def intersections(sheets):
    """Reject different-net collinear overlaps or endpoint contacts.

    Interior orthogonal crossings are explicitly unconnected (no dot).
    """
    failures=[];crossings=[]
    for sh in sheets:
        seg=[]
        for wi in sh.wires:
            seg.extend((wi['net'],tuple(a),tuple(b)) for a,b in zip(wi['points'],wi['points'][1:]) if a!=b)
        for i,(n,a,b) in enumerate(seg):
            for m,c,d in seg[i+1:]:
                if n==m:continue
                va=a[0]==b[0];vc=c[0]==d[0]
                if va==vc:
                    if (a[0] if va else a[1])!=(c[0] if vc else c[1]):continue
                    ia=1 if va else 0
                    if max(min(a[ia],b[ia]),min(c[ia],d[ia]))<=min(max(a[ia],b[ia]),max(c[ia],d[ia])):
                        failures.append(dict(sheet=sh.index,nets=[n,m],reason='collinear overlap/contact',segments=[a,b,c,d]))
                else:
                    v1,v2,h1,h2=(a,b,c,d) if va else (c,d,a,b)
                    p=(v1[0],h1[1])
                    if on_segment(p,a,b) and on_segment(p,c,d):
                        rec=dict(sheet=sh.index,nets=[n,m],point=p)
                        if p in [a,b,c,d]:failures.append(dict(**rec,reason='different-net endpoint contact'))
                        else:crossings.append(dict(**rec,junction=False))
    return failures,crossings


def routed_pin_audit(sheets):
    """Independently trace each rendered pin to a label through drawn segments.

    Split wires at all same-net endpoints and junctions. Global labels then
    join disconnected local components, exactly as stated on the drawing.
    """
    checked=[]
    for sh in sheets:
        for net in {w['net'] for w in sh.wires}:
            segments=[(tuple(a),tuple(b)) for w in sh.wires if w['net']==net
                      for a,b in zip(w['points'],w['points'][1:]) if a!=b]
            labels={tuple(q['point']) for q in sh.labels if q['net']==net}
            pinrows=[(key,q) for key,q in sh.pins.items() if q['net']==net]
            points={p for seg in segments for p in seg}|labels|{q['point'] for _,q in pinrows}
            parent={p:p for p in points}
            def find(p):
                while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
                return p
            for a,b in segments:
                along=[p for p in points if on_segment(p,a,b)]
                for p in along[1:]:parent[find(p)]=find(along[0])
            for p in labels:assert any(on_segment(p,a,b) for a,b in segments),('Unwired label',sh.index,net,p)
            labelroots={find(p) for p in labels}
            for key,q in pinrows:
                assert find(q['point']) in labelroots,('Pin has no drawn route to a label',sh.index,key,net)
                checked.append(dict(sheet=sh.index,instance=key[0],pin=key[1],net=net,path_to_named_net=True))
    return checked


def frame(fig,index,rect,devices,full=False):
    left,bottom,width,height=rect
    ax=fig.add_axes([left+width*.015,bottom+height*.11,width*.97,height*.775])
    fig.text(left+width*.035,bottom+height*.96,f'25 · {index}/4  {TITLES[index]}',fontsize=13.5,color=INK,weight='bold',va='top')
    fig.text(left+width*.035,bottom+height*.914,'晶体管级连接图｜尺寸为单位 W/L（um），m 为并联倍数｜所有数值读取最终 circuit.scs',fontsize=7.8,color=MUTED)
    fig.text(left+width*.035,bottom+height*.065,'实心点为电气连接；交叉无点不连接。同名网络在全部分图间相连；大写名称为外部端口。',fontsize=7.4,color=MUTED)
    fig.text(left+width*.035,bottom+height*.040,'每只 MOS 均标 D/G/S/B；紫色为体端支路及其实际网络。n18 无栅极圆圈；p18 有圆圈。外部测试负载不属于 DUT。',fontsize=7.2,color=MUTED)
    if index==2:fig.text(left+width*.035,bottom+height*.018,'体端重点：MPINN / MPINP 的 B=ptail，S=ptn / ptp；MPSW 的 B=S=ptail。',fontsize=7.2,color=BULK)
    return layout(ax,index,devices)


def make(dpi=130):
    devices,sub,ports,geometry=read_design();OUT.mkdir(parents=True,exist_ok=True)
    circuit_sha=sha(CASE/'circuit.scs');geometry_sha=sha(CASE/'geometry.json');sheets=[]
    with PdfPages(OUT/'sheets.pdf',metadata={'Title':'25 完整晶体管分图：45 MOS与全部R/C','Author':'SMIC18 schematic renderer'}) as pdf:
        for index in range(1,5):
            fig=plt.figure(figsize=(11.69,8.27),facecolor='white')
            sheet=frame(fig,index,(0,0,1,1),devices);sheets.append(sheet)
            fig.savefig(OUT/f'sheet-{index}.svg');fig.savefig(OUT/f'sheet-{index}.png',dpi=dpi);pdf.savefig(fig);plt.close(fig)
    fig=plt.figure(figsize=(23.39,16.54),facecolor='white')
    for i,box in enumerate([(0,.5,.5,.5),(.5,.5,.5,.5),(0,0,.5,.5),(.5,0,.5,.5)],1):frame(fig,i,box,devices,full=True)
    fig.lines.extend([plt.Line2D([.5,.5],[.01,.99],transform=fig.transFigure,color='#c9d6de',lw=.5),plt.Line2D([.01,.99],[.5,.5],transform=fig.transFigure,color='#c9d6de',lw=.5)])
    fig.savefig(OUT/'full.svg');fig.savefig(OUT/'full.pdf',metadata={'Title':'25 完整晶体管总图 A2','Author':'SMIC18 schematic renderer'});fig.savefig(OUT/'full.png',dpi=100);plt.close(fig)
    names=[n for s in sheets for n in s.instances];assert collections.Counter(names)==collections.Counter(devices.keys()),'Missing/duplicate drawn instances'
    # Compare every terminal, including passive node order, with the parsed netlist.
    rendered={n:d for s in sheets for n,d in s.instances.items()}
    nets=collections.defaultdict(list)
    for n,d in devices.items():
        assert d['pins']==rendered[n]['pins'] and d['parameters']==rendered[n]['parameters']
        for pin,net in d['pins'].items():nets[net].append(dict(instance=n,pin=pin,sheet=rendered[n]['sheet'],point=rendered[n]['rendered_pins'][pin]))
    assert set(nets)=={q['net'] for s in sheets for q in s.labels},'Every net must have an explicit label'
    issues,crossings=intersections(sheets)
    pinpaths=routed_pin_audit(sheets)
    net_pages={n:sorted({q['sheet'] for q in pins}) for n,pins in nets.items()}
    connectivity=dict(generated_at=now(),subcircuit=sub,external_ports=ports,circuit_sha256=circuit_sha,geometry_sha256=geometry_sha,instances=rendered,nets=dict(nets),net_to_sheets=net_pages,cross_sheet_networks={n:v for n,v in net_pages.items() if len(v)>1},routed_pin_checks=pinpaths,sheets=[dict(index=s.index,title=TITLES[s.index],wires=s.wires,net_labels=s.labels) for s in sheets],unconnected_crossings=crossings,geometric_conflicts=issues,convention='Identical labels join across/all sheets. A dot marks a junction. Orthogonal crossings without a dot do not join. Purple branches explicitly connect B pins. This is schematic mapping, not layout LVS.')
    write(OUT/'connectivity.json',connectivity)
    assert not issues,('Correct graphical wire conflicts before accepting the drawing',issues)
    assert circuit_sha==sha(CASE/'circuit.scs') and geometry_sha==sha(CASE/'geometry.json'),'Source changed while drawing'
    artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    counts=dict(collections.Counter(d['kind'] for d in devices.values()))
    audit=dict(generated_at=now(),status='coverage_passed_visual_pending',circuit_sha256=circuit_sha,geometry_sha256=geometry_sha,renderer_sha256=sha(__file__),instance_counts=counts,total_instances=len(devices),drawn_instances=len(names),total_terminals=sum(len(x['pins']) for x in devices.values()),all_instances_drawn_exactly_once_per_complete_view=True,all_terminals_mapped=True,all_rendered_pins_have_drawn_path_to_correct_net_label=len(pinpaths)==sum(len(x['pins']) for x in devices.values()),all_45_body_connections_explicit=counts['MOS']==45,all_R_C_values_read_from_netlist=True,geometry_matches_netlist=True,all_unit_widths_valid=geometry['all_unit_widths_valid'],all_external_ports_present=all(x in nets for x in ports),all_internal_nets_preserved=True,total_nets=len(nets),geometric_wire_conflicts=issues,crossings_without_junction_count=len(crossings),sheets=4,sheet_page_size='A4 landscape',full_page_size='A2 landscape',render_review_pending=True,artifacts=artifacts,scope='Only transistor-level schematic generation and static coverage. No circuit edit, performance extraction, external model call or simulation.',rebuild='Existing Bridge Python scripts/schematic25.py; after viewing all five PNGs, scripts/schematic25.py --confirm-visual')
    write(CASE/'schematic_audit.json',audit)
    return audit


def confirm_visual():
    p=CASE/'schematic_audit.json';a=json.loads(p.read_text())
    assert sha(CASE/'circuit.scs')==a['circuit_sha256'] and sha(CASE/'geometry.json')==a['geometry_sha256']
    for path,h in a['artifacts'].items():assert sha(ROOT/path)==h
    a.update(status='passed',render_review_pending=False,all_pages_visually_reviewed=True,visual_reviewed_at=now(),visual_review_note='Four split PNG pages and full A2 PNG actually inspected; transistor polarity, D/G/S/B, bulk labels, passive values, local connections, cross-page names and text readability reviewed.')
    write(p,a);return a


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--confirm-visual',action='store_true');p.add_argument('--dpi',type=int,default=130);args=p.parse_args()
    a=confirm_visual() if args.confirm_visual else make(args.dpi)
    print(json.dumps({k:a[k] for k in ['status','instance_counts','total_instances','total_terminals','sheets','render_review_pending']},ensure_ascii=False,indent=2))
