"""Full bandgap schematics; all terminals audited against final Spectre source."""
from schematic_common import *

class BandgapSheet(Sheet):
    def bjt(self,name,x,y):
        d=self.devices[name];assert d['kind']=='BJT' and name not in self.instances
        self.ax.add_patch(Circle((x-.25,y),.72,fill=False,edgecolor=INK,lw=.75))
        self.line([(x-.65,y-.4),(x-.65,y+.4)],lw=1.3)
        self.line([(x-1.55,y),(x-.65,y)])
        self.line([(x,y+1),(x,y+.55),(x-.65,y+.2)])
        self.line([(x-.65,y-.2),(x,y-.55),(x,y-1)])
        self.ax.annotate('',xy=(x-.06,y-.52),xytext=(x-.53,y-.26),arrowprops=dict(arrowstyle='-|>',color=INK,lw=.9))
        pts={'C':(x,y+1),'B':(x-1.55,y),'E':(x,y-1),'SUB':(x+.95,y)}
        for pin,pt in pts.items():self.pins[(name,pin)]=dict(point=pt,net=d['pins'][pin],connected=False)
        self.instances[name]=dict(**d,sheet=self.index,origin=[x,y],rendered_pins={k:list(v) for k,v in pts.items()})
        self.text(x+.85,y+.62,name+'  '+d['model'],6.7,weight='bold')
        self.text(x+.85,y-.65,'area='+d['parameters']['area']+' × 4um²',6.5)
        self.text(x+.15,y+.83,'C',5.4);self.text(x+.15,y-.97,'E',5.4)
        self.text(x-1.45,y+.15,'B',5.4)
        self.line([(x+.48,y),(x+.95,y)],color=BULK,lw=.7)
        self.text(x+.65,y+.18,'SUB',4.8,color=BULK)
        self.wire(d['pins']['SUB'],pts['SUB'],(x+1.3,y),body=True)
        self.tag(d['pins']['SUB'],(x+1.3,y),body=True,dy=0)
        return name

def diode_bjt(s,name,x,y,net):
    s.bjt(name,x,y)
    s.wire(net,s.p(name,'C'),(x,y+3),(x-2,y+3),(x-2,y),s.p(name,'B'))
    s.tag(net,(x,y+3))

def layout(ax,i,dev):
    s=BandgapSheet(ax,i,dev)
    if i==1:
        s.text(1,24,'1:1:2 PMOS镜；NPN单位发射区2×2um，面积比1:8:2；外接5pF仅在测试台中。',7.7)
        for n,x in [('MP0',7),('MP1',21),('MP2',35)]:
            s.mos(n,x,18);s.wire('vdd',s.p(n,'S'),(x,22))
        s.wire('vdd',(7,22),(35,22));s.tag('vdd',(7,22))
        diode_bjt(s,'Q0',7,8,'va');diode_bjt(s,'Q1',21,8,'n1');diode_bjt(s,'QREF',35,8,'vctat')
        s.wire('va',s.p('MP0','D'),s.p('Q0','C'))
        for res,mp,q,x,upper,lower in [('RPTAT','MP1','Q1',21,'vb','n1'),('RREF','MP2','QREF',35,'vref','vctat')]:
            s.passive(res,x,14);s.wire(upper,s.p(mp,'D'),s.p(res,'1'));s.tag(upper,(x,16))
            s.wire(lower,s.p(res,'2'),s.p(q,'C'))
        s.passive('CREF',40,13);s.wire('vref',(35,16),(40,16),s.p('CREF','1'))
        for q,x in [('Q0',7),('Q1',21),('QREF',35)]:s.wire('vss',s.p(q,'E'),(x,3))
        s.wire('vss',s.p('CREF','2'),(40,3),(7,3));s.tag('vss',(7,3))
        s.text(1,1,'RPTAT建立PTAT电流，RREF叠加VBE；CREF为60pF名义片上MIM，包含在功耗及动态测试中。',7.5)
    elif i==2:
        s.text(1,24,'误差放大器调节pctrl，使va≈vb；输入对含体效应，尺寸与实际OP均列在正文。',7.7)
        for n,x in [('MPM',16),('MPD',30)]:s.mos(n,x,18);s.wire('vdd',s.p(n,'S'),(x,22))
        s.wire('vdd',(16,22),(30,22));s.tag('vdd',(16,22))
        for n,x,net in [('MINA',16,'pctrl'),('MINB',30,'nout')]:
            s.mos(n,x,12);s.wire(net,s.p(n,'D'),(x,17));s.tag(net,(x,15))
            s.wire('tail',s.p(n,'S'),(x,9))
        s.wire('tail',(16,9),(30,9));s.tag('tail',(22,9))
        s.mos('MTAIL',22,6);s.wire('tail',s.p('MTAIL','D'),(22,9));s.wire('vss',s.p('MTAIL','S'),(22,2));s.tag('vss',(22,2))
        s.mos('MNB',7,6);s.diode('MNB','nbias',9);s.tag('nbias',(7,9))
        s.wire('vss',s.p('MNB','S'),(7,2));s.tag('vss',(7,2))
        s.wire('nout',(30,15),(27.7,15),(27.7,18),s.p('MPD','G'))
        s.wire('nout',(27.7,18),(27.7,20),(12.9,20),(12.9,18),s.p('MPM','G'))
        s.passive('CCOMP',40,14);s.wire('pctrl',s.p('CCOMP','1'),(40,17));s.tag('pctrl',(40,17))
        s.wire('vss',s.p('CCOMP','2'),(40,11));s.tag('vss',(40,11))
        s.text(1,1,'MNB由第3页电阻串偏置；MTAIL倍数3。CCOMP=0.5pF；vref的滤波电容在第1页。',7.5)
    elif i==3:
        s.text(1,24,'RB0–RB7为连续串联工艺电阻；紫色衬底均接vss。启动不使用理想脉冲或外部偏置源。',7.7)
        for j,x in enumerate([6,16,26,36]):s.passive(f'RB{j}',x,19,vertical=False)
        for j,x in enumerate([36,26,16,6],4):s.passive(f'RB{j}',x,13,vertical=False,reverse=True)
        s.wire('vdd',s.p('RB0','1'),(3,19));s.tag('vdd',(3,19))
        for j in [0,1,2,4,5,6]:
            a,b=s.p(f'RB{j}','2'),s.p(f'RB{j+1}','1')
            s.wire(f'rb{j+1}',a,b);s.tag(f'rb{j+1}',((a[0]+b[0])/2,a[1]))
        s.wire('rb4',s.p('RB3','2'),(41,19),(41,13),s.p('RB4','1'));s.tag('rb4',(41,19))
        s.wire('nbias',s.p('RB7','2'),(3,13),(3,10));s.tag('nbias',(3,10))
        s.mos('MPST',24,7);s.mos('MNST',24,3);s.mos('MSTART',36,3)
        s.wire('st',s.p('MPST','D'),s.p('MNST','D'));s.tag('st',(24,5))
        s.wire('st',(24,5),(32,5),(32,3),s.p('MSTART','G'))
        s.wire('vref',s.p('MPST','G'),(21,7),(21,3),s.p('MNST','G'));s.tag('vref',(21,7),ha='right',dx=-.1)
        s.text(1,5,'启动：vref低 → st高 → MSTART拉低pctrl。\n稳态：vref升高 → st低 → 注入支路关闭。\n反相器本身的静态电流计入总功耗。',7.5)
    return s.finish()

if __name__=='__main__':
    make_case(11,{1:'PTAT / CTAT 核心与输出滤波',2:'误差放大器与补偿',3:'电阻偏置与自动关断启动'},layout)
