"""Complete native-device schematic for the high-PSRR bandgap."""
from schematic_common import *
from schematic11 import BandgapSheet,diode_bjt

def layout(ax,i,dev):
    s=BandgapSheet(ax,i,dev)
    if i==1:
        s.text(1,24,'级联1:1:2电流镜；NPN面积比1:8:2；VBG与1pF外部负载在第3页标明。',7.5)
        for n,cas,x in [('MP0','MPC0',7),('MP1','MPC1',21),('MP2','MPC2',35)]:
            s.mos(n,x,20);s.mos(cas,x,16)
            s.wire('AVDD',s.p(n,'S'),(x,23))
            net=dev[n]['pins']['D'];s.wire(net,s.p(n,'D'),s.p(cas,'S'));s.tag(net,(x,18))
        s.wire('AVDD',(7,23),(35,23));s.tag('AVDD',(7,23))
        for q,x,net in [('Q0',7,'va'),('Q1',21,'n1'),('QREF',35,'vctat')]:
            diode_bjt(s,q,x,5,net);s.wire('AVSS',s.p(q,'E'),(x,2))
        s.wire('va',s.p('MPC0','D'),s.p('Q0','C'))
        for n,cas,q,x,net,lower in [('RPTAT','MPC1','Q1',21,'vb','n1'),('RREF','MPC2','QREF',35,'vcore','vctat')]:
            s.passive(n,x,11);s.wire(net,s.p(cas,'D'),s.p(n,'1'));s.tag(net,(x,14))
            s.wire(lower,s.p(n,'2'),s.p(q,'C'))
        s.passive('CCORE',40,10);s.wire('vcore',(35,14),(40,14),s.p('CCORE','1'))
        s.wire('AVSS',s.p('CCORE','2'),(40,2),(7,2));s.tag('AVSS',(7,2))
        s.text(1,.9,'RPTAT=1×16.5um；RREF=1×73.3um；CCORE名义60pF。工艺无源的SUB端明确保留。',7.3)
    elif i==2:
        s.text(1,24,'第四路级联镜给MNB供偏置；MTAIL为3倍。输入对调节pctrl，使va≈vb。',7.5)
        s.mos('MPA',7,20);s.mos('MPCA',7,16)
        s.wire('AVDD',s.p('MPA','S'),(7,23));s.wire('namp',s.p('MPA','D'),s.p('MPCA','S'));s.tag('namp',(7,18))
        s.mos('MNB',7,8);s.diode('MNB','nbias',11)
        s.wire('nbias',s.p('MPCA','D'),s.p('MNB','D'));s.tag('nbias',(7,13))
        s.wire('AVSS',s.p('MNB','S'),(7,3));s.tag('AVSS',(7,3))
        for n,x in [('MPM',22),('MPD',36)]:s.mos(n,x,20);s.wire('AVDD',s.p(n,'S'),(x,23))
        s.wire('AVDD',(7,23),(36,23));s.tag('AVDD',(7,23))
        for n,mp,x,net in [('MINA','MPM',22,'pctrl'),('MINB','MPD',36,'nout')]:
            s.mos(n,x,11);s.wire(net,s.p(n,'D'),s.p(mp,'D'));s.tag(net,(x,14))
            s.wire('tail',s.p(n,'S'),(x,8))
        s.wire('tail',(22,8),(36,8));s.tag('tail',(29,8))
        s.mos('MTAIL',29,5);s.wire('tail',s.p('MTAIL','D'),(29,8));s.wire('AVSS',s.p('MTAIL','S'),(29,2));s.tag('AVSS',(29,2))
        s.wire('nout',(36,17),(33.7,17),(33.7,20),s.p('MPD','G'))
        s.wire('nout',(33.7,20),(33.7,21.9),(18.9,21.9),(18.9,20),s.p('MPM','G'))
        s.passive('CCOMP',15,6);s.wire('pctrl',s.p('CCOMP','1'),(15,9));s.tag('pctrl',(15,9))
        s.wire('AVSS',s.p('CCOMP','2'),(15,3));s.tag('AVSS',(15,3))
        s.text(1,.9,'核心派生偏置避免VDD直接改变误差放大器电流；CCOMP名义0.5pF。所有MOS体端均显式绘制。',7.3)
    elif i==3:
        s.text(1,24,'MPCB与五段工艺电阻建立级联栅偏置；启动关断及输出RC滤波均为实际器件。',7.5)
        s.mos('MPCB',8,20);s.diode('MPCB','cbias',17.5)
        s.wire('AVDD',s.p('MPCB','S'),(8,23));s.tag('AVDD',(8,23));s.tag('cbias',(8,17.5))
        for j,y in enumerate([15,12,9,6,3]):s.passive('RCB'+str(j),8,y)
        s.wire('cbias',s.p('MPCB','D'),s.p('RCB0','1'))
        for j in range(4):
            a,b=s.p(f'RCB{j}','2'),s.p(f'RCB{j+1}','1');s.wire(f'rcb{j+1}',a,b);s.tag(f'rcb{j+1}',(8,(a[1]+b[1])/2),ha='right',dx=-.3)
        s.wire('AVSS',s.p('RCB4','2'),(8,1.5));s.tag('AVSS',(8,1.5))
        s.mos('MPST',27,20);s.mos('MNST',27,16);s.mos('MSTART',39,16)
        s.wire('st',s.p('MPST','D'),s.p('MNST','D'));s.tag('st',(27,18))
        s.wire('st',(27,18),(35,18),(35,16),s.p('MSTART','G'))
        s.wire('vcore',s.p('MPST','G'),(24,20),(24,16),s.p('MNST','G'));s.tag('vcore',(24,20),ha='right',dx=-.1)
        s.text(20,12,'vcore低时，MSTART拉低pctrl启动。\nvcore建立后注入关闭；检测器电流计入功耗。',7.1)
        s.passive('RFILT',27,8,vertical=False);s.wire('vcore',s.p('RFILT','1'),(22,8));s.tag('vcore',(22,8))
        s.passive('CFILT',38,5);s.wire('VBG',s.p('RFILT','2'),(38,8),s.p('CFILT','1'));s.tag('VBG',(38,8))
        s.wire('AVSS',s.p('CFILT','2'),(38,2));s.tag('AVSS',(38,2))
        s.text(20,1,'CFILT名义20pF；1pF外部CLOAD仅在bench中。\n接口顺序：AVDD AVSS VBG SUB；SUB由bench接AVSS。',7.0)
    return s.finish()

if __name__=='__main__':make_case(21,{1:'级联PTAT/CTAT核心',2:'自偏置误差放大器与补偿',3:'级联偏置、启动与工艺RC输出'},layout)
