"""Topology-specific drawings for cases03/04/10/12/13/16/41/44/49; no simulation."""
import argparse
import json
from schematic_common import *

TITLES={
 3:{1:'自偏置 β 倍增与启动支路',2:'源退化差分信号通路'},
 4:{1:'源退化 GM–R 差分放大器与偏置'},
 10:{1:'电流输入与第一级模拟反馈增益',2:'第二级模拟反馈增益与输出'},
 12:{1:'β 倍增核心、工艺电阻与电流输出',2:'弱上拉、启动检测与注入支路'},
 13:{1:'自偏置 β 倍增与启动支路',2:'恒 gm 电阻负载差分信号通路'},
 16:{1:'输入差分级、电流镜负载与尾偏置',2:'输出级、偏置复制与串联 Miller 补偿'},
 41:{1:'共栅镜负载、输入级与低压偏置',2:'互补输出级与串联 Miller 补偿'},
 44:{1:'五管 OTA 信号核心与参考复制'},
 49:{1:'叠接电流源与变容参考偏置',2:'变容偏置调节器：差分放大与推挽输出',3:'差分 LC 谐振腔与交叉耦合负阻',4:'交流耦合、变容阵列与直流偏置电阻'},
}


def supply(z,net,names,y):
    pts=[z.p(n,p) for n,p in names]
    if len(pts)>1:z.wire(net,(min(p[0] for p in pts),y),(max(p[0] for p in pts),y))
    for pt in pts:z.wire(net,pt,(pt[0],y))
    z.tag(net,(min(p[0] for p in pts),y),dy=.35 if y>12 else -.35)


def vertical(z,a,ap,b,bp,net,label_y=None):
    z.wire(net,z.p(a,ap),z.p(b,bp))
    z.tag(net,(z.p(a,ap)[0],label_y if label_y is not None else (z.p(a,ap)[1]+z.p(b,bp)[1])/2))


def bias_beta(z,upper=False):
    M=z.mos;P=z.passive;p=z.p;w=z.wire
    vdd,vss,iref=('VDD','VSS','IREF') if upper else ('vdd','vss','iref')
    for n,x,y in [('MREF',4,6),('MST',12,6),('MB1',23,8),('MB2',35,11),('MP1',23,19),('MP2',35,19)]:M(n,x,y)
    P('RB',35,5)
    supply(z,vdd,[('MP1','S'),('MP2','S')],23)
    supply(z,vss,[('MREF','S'),('MST','S'),('MB1','S'),('RB','2')],1.3)
    w(iref,p('MREF','D'),(4,11));z.diode('MREF',iref,9);z.tag(iref,(4,11))
    vertical(z,'MP1','D','MB1','D','nb',13);z.diode('MB1','nb',14)
    vertical(z,'MP2','D','MB2','D','nc',15);z.diode('MP2','nc',16)
    vertical(z,'MB2','S','RB','1','rb2',8)


def diff_resistors(z,degen=True,reference=False):
    M=z.mos;P=z.passive;p=z.p;w=z.wire
    d=z.devices;left,right=(19,32) if reference else (12,28)
    center=(left+right)/2;vss=d['MTAIL']['pins']['S'];vdd=d['RLP']['pins']['1']
    if reference:
        M('MREF',6,8);w('IREF',p('MREF','D'),(6,13));z.diode('MREF','IREF',11);z.tag('IREF',(6,13))
    for n,x in [('MINN',left),('MINP',right)]:M(n,x,13 if degen else 11)
    # Map by the actual drain rather than assuming polarity from the suffix.
    load=[]
    for n in ['RLN','RLP']:
        node=d[n]['pins']['2'];x=left if node==d['MINN']['pins']['D'] else right
        P(n,x,20);load.append((n,'1'))
        inp='MINN' if x==left else 'MINP'
        vertical(z,n,'2',inp,'D',node,17)
    M('MTAIL',center,4)
    if degen:
        for n,inp,x in [('RSN','MINN',left),('RSP','MINP',right)]:
            P(n,x,9);vertical(z,inp,'S',n,'1',d[n]['pins']['1'],11)
        w('tail',p('RSN','2'),(left,6.5),(right,6.5),p('RSP','2'))
        w('tail',p('MTAIL','D'),(center,6.5));z.tag('tail',(center,6.5),dy=.35)
    else:
        w('tail',p('MINN','S'),(left,8),(right,8),p('MINP','S'))
        w('tail',p('MTAIL','D'),(center,8));z.tag('tail',(center,8),dy=.35)
    supply(z,vdd,load,23)
    supply(z,vss,[('MTAIL','S')]+([('MREF','S')] if reference else []),1.4)
    if vdd=='VDD':z.text(2,23.6,'VCM 为保留接口，DUT 内部未连接。',7,color=MUTED)


def differential_mirror(z,names):
    ref,tail,ni1,ni2,pm1,pm2=names;M=z.mos;p=z.p;w=z.wire;d=z.devices
    for n,x,y in [(ref,5,6),(tail,25,4),(ni1,18,11),(ni2,32,11),(pm1,18,19),(pm2,32,19)]:M(n,x,y)
    vdd=d[pm1]['pins']['S'];vss=d[ref]['pins']['S'];bias=d[ref]['pins']['D']
    supply(z,vdd,[(pm1,'S'),(pm2,'S')],23)
    supply(z,vss,[(ref,'S'),(tail,'S')],1.4)
    w(bias,p(ref,'D'),(5,11));z.diode(ref,bias,9);z.tag(bias,(5,11))
    for a,b in [(pm1,ni1),(pm2,ni2)]:vertical(z,a,'D',b,'D',d[b]['pins']['D'],15)
    mirror=d[pm1]['pins']['G'];z.diode(pm1,mirror,16)
    w(mirror,p(pm2,'G'),(28,19),(28,16),(18,16))
    w('tail',p(ni1,'S'),(18,8),(32,8),p(ni2,'S'));w('tail',p(tail,'D'),(25,8));z.tag('tail',(25,8),dy=.35)


def layout_for(slot):
    def layout(ax,index,devices):
        z=Sheet(ax,index,devices);M=z.mos;P=z.passive;p=z.p;w=z.wire;tag=z.tag
        if slot==3:
            if index==1:bias_beta(z,True)
            else:diff_resistors(z)
        elif slot==4:diff_resistors(z,reference=True)
        elif slot==13:
            if index==1:bias_beta(z)
            else:diff_resistors(z,degen=False)
        elif slot in (16,44) and index==1:
            differential_mirror(z,('MREF','MTAIL','MINN','MINP','MPD','MPM') if slot==16 else ('M6','M5','M1','M2','M3','M4'))
        elif slot==16:
            for n,x,y in [('MBP',10,19),('MBN',10,6),('MLOAD',31,19),('MSECOND',31,6)]:M(n,x,y)
            supply(z,'vdd',[('MBP','S'),('MLOAD','S')],23);supply(z,'vss',[('MBN','S'),('MSECOND','S')],1.4)
            vertical(z,'MBP','D','MBN','D','obias',12);z.diode('MBP','obias',15)
            vertical(z,'MLOAD','D','MSECOND','D','vout',14)
            P('RZ',17,11,vertical=False);P('CC',24,11,vertical=False)
            w('comp',p('RZ','2'),p('CC','1'));tag('comp',(20,11),dy=-.35)
            w('vout',p('CC','2'),(31,11))
        elif slot==10:
            pn,nn,rf=('MP1','MN1','RF1') if index==1 else ('MP2','MN2','RFB2')
            gate=devices[pn]['pins']['G'];out=devices[pn]['pins']['D']
            M(pn,25,17);M(nn,25,7);P(rf,15,21,vertical=False)
            vertical(z,pn,'D',nn,'D',out,12)
            w(gate,p(pn,'G'),(18,17),(18,7),p(nn,'G'));tag(gate,(18,15),dx=-.2,ha='right')
            w(out,p(rf,'1'),(12,21),(12,12),(25,12))
            w(gate,p(rf,'2'),(18,21),(18,17))
            supply(z,'vdd',[(pn,'S')],24);supply(z,'vss',[(nn,'S')],1.4)
            if index==1:
                M('MREF',4,7);w('iref',p('MREF','D'),(4,12));z.diode('MREF','iref',10);tag('iref',(4,12))
                P('RB',18,3);w(gate,p('RB','1'),(18,7))
            else:
                P('RIN2',9,14,vertical=False);w('nbuf',p('RIN2','2'),(18,14))
            z.text(29,22.7,'连续模拟 CMOS 增益级\n器件采用 gm/ID 尺寸',8,color=MUTED)
        elif slot==12:
            if index==1:
                for n,x,y in [('MP1',10,19),('MN2',10,11),('MP2',24,19),('MN1',24,7),('MOUT',37,7)]:M(n,x,y)
                P('RGM',10,5)
                supply(z,'vdd',[('MP1','S'),('MP2','S')],23)
                supply(z,'vss',[('RGM','2'),('MN1','S'),('MOUT','S')],1.4)
                vertical(z,'MP1','D','MN2','D','na',15);z.diode('MP1','na',16)
                vertical(z,'MP2','D','MN1','D','vref',13);z.diode('MN1','vref',12)
                w('na',p('MP2','G'),(20,19),(20,16),(10,16))
                vertical(z,'MN2','S','RGM','1','nr',8)
                w('vref',p('MN2','G'),(6,11),(6,15),(3,15));tag('vref',(3,15),ha='right',dx=-.15)
            else:
                for n,x,y in [('MPUP',12,19),('MDET',12,7),('MSTART',31,7)]:M(n,x,y)
                supply(z,'vdd',[('MPUP','S')],23);supply(z,'vss',[('MDET','S'),('MSTART','S')],1.4)
                vertical(z,'MPUP','D','MDET','D','nx',14)
                w('nx',p('MSTART','G'),(27,7),(27,14),(12,14))
                z.text(22,21,'na：接核心 PMOS 镜节点\nvref：接核心自偏置节点',8,color=MUTED)
        elif slot==41:
            if index==1:
                for n,x,y in [('MREF',4,4),('MCBN',11,4),('MPCB',11,13),('MPD',23,21),('MPM',35,21),('MCD',23,17),('MCM',35,17),('MINN',23,10),('MINP',35,10),('MTAIL',29,4)]:M(n,x,y)
                P('RB',11,19)
                supply(z,'vdd',[('RB','1'),('MPD','S'),('MPM','S')],24)
                supply(z,'vss',[('MREF','S'),('MCBN','S'),('MTAIL','S')],1.3)
                w('iref',p('MREF','D'),(4,9));z.diode('MREF','iref',7);tag('iref',(4,9))
                vertical(z,'RB','2','MPCB','S','nrb',16)
                vertical(z,'MPCB','D','MCBN','D','vbp',9);z.diode('MPCB','vbp',10)
                for a,b,n in [('MPD','MCD','nc3'),('MPM','MCM','nc4')]:vertical(z,a,'D',b,'S',n,19)
                for a,b,n in [('MCD','MINN','nleft'),('MCM','MINP','stage1')]:vertical(z,a,'D',b,'D',n,14)
                w('nleft',p('MPD','G'),(20,21),(20,14),(23,14))
                w('tail',p('MINN','S'),(23,7),(35,7),p('MINP','S'));w('tail',p('MTAIL','D'),(29,7));tag('tail',(29,7),dy=.35)
            else:
                M('MSECOND',27,19);M('MLOAD',27,5)
                supply(z,'vdd',[('MSECOND','S')],23);supply(z,'vss',[('MLOAD','S')],1.4)
                vertical(z,'MSECOND','D','MLOAD','D','vout',14)
                P('RZ',11,11,vertical=False);P('CC',19,11,vertical=False)
                w('comp',p('RZ','2'),p('CC','1'));tag('comp',(15,11),dy=-.35)
                w('vout',p('CC','2'),(27,11))
                z.text(5,20,'stage1：第一级高阻输出\niref：参考复制偏置',8,color=MUTED)
        elif slot==49:
            if index==1:
                for n,x,y in [('MPREFU',6,20),('MPREFL',6,14),('MPFEED',18,20),('MPCAS',18,14),('MPVB',32,20),('MNB2',32,12),('MNB1',32,5)]:M(n,x,y)
                supply(z,'vdd',[('MPREFU','S'),('MPFEED','S'),('MPVB','S')],23)
                supply(z,'vss',[('MNB1','S')],1.3)
                vertical(z,'MPREFU','D','MPREFL','S','pbu',17);z.diode('MPREFU','pbu',17)
                w('iref',p('MPREFL','D'),(6,10));z.diode('MPREFL','iref',11);tag('iref',(6,10))
                vertical(z,'MPFEED','D','MPCAS','S','pcas',17)
                w('tankct',p('MPCAS','D'),(18,10));tag('tankct',(18,10))
                vertical(z,'MPVB','D','MNB2','D','vrefvar',16);z.diode('MNB2','vrefvar',15.5)
                vertical(z,'MNB2','S','MNB1','D','nbmid',9);z.diode('MNB1','nbmid',8.5)
            elif index==2:
                for n,x,y in [('MRT',19,4),('MRI1',12,12),('MRI2',26,12),('MRL1',12,20),('MRL2',26,20),('MRPU',37,20),('MRPD',37,4)]:M(n,x,y)
                supply(z,'vdd',[('MRL1','S'),('MRL2','S'),('MRPU','S')],23)
                supply(z,'vss',[('MRT','S'),('MRPD','S')],1.3)
                vertical(z,'MRL1','D','MRI1','D','ra',16);z.diode('MRL1','ra',16)
                vertical(z,'MRL2','D','MRI2','D','rout',16)
                w('rtail',p('MRI1','S'),(12,8),(26,8),p('MRI2','S'));w('rtail',p('MRT','D'),(19,8));tag('rtail',(19,8),dy=.35)
                w('rout',p('MRPU','G'),(32,20),(32,4),p('MRPD','G'));w('rout',(26,16),(32,16))
                vertical(z,'MRPU','D','MRPD','D','vbias',13)
            elif index==3:
                for n,x in [('XLP',12),('XLN',30)]:P(n,x,20,reverse=True)
                for n,x in [('XCP',5),('XCN',38)]:P(n,x,13)
                M('MNP',12,6);M('MNN',30,6)
                supply(z,'tankct',[('XLP','2'),('XLN','2')],23)
                supply(z,'vss',[('MNP','S'),('MNN','S'),('XCP','2'),('XCN','2')],1.4)
                for ind,mos,cap,node,cx in [('XLP','MNP','XCP','outp',5),('XLN','MNN','XCN','outn',38)]:
                    vertical(z,ind,'1',mos,'D',node,17);xx=p(ind,'1')[0]
                    w(node,p(cap,'1'),(cx,16),(xx,16))
                w('outn',p('MNP','G'),(9,6),(9,9),(30,9))
                w('outp',p('MNN','G'),(25,6),(25,11),(12,11))
            else:
                for side,dx,node,var in [('P',0,'outp','varp'),('N',22,'outn','varn')]:
                    for k,x in enumerate([5,11,17]):P(f'XCC{side}{k}',x+dx,20)
                    caps=[f'XCC{side}{k}' for k in range(3)]
                    supply(z,node,[(n,'1') for n in caps],22.5)
                    for n in caps:w(var,p(n,'2'),(p(n,'2')[0],17.5))
                    w(var,(5+dx,17.5),(20+dx,17.5),(20+dx,8),(5+dx,8));tag(var,(20+dx,15))
                    for k,x in enumerate([5,11]):
                        n=f'XV{side}{k}';P(n,x+dx,10);w(var,p(n,'2'),(x+dx,8))
                    supply(z,'vctrl',[(f'XV{side}0','1'),(f'XV{side}1','1')],13)
                    for suffix,y in [('',3),('2',6)]:
                        n=f'RB{side}{suffix}';P(n,10+dx,y,vertical=False)
                        w('vbias',p(n,'1'),(7+dx,y));w(var,p(n,'2'),(17+dx,y))
                    w('vbias',(7+dx,3),(7+dx,6));tag('vbias',(7+dx,4.5),ha='right',dx=-.15)
                    w(var,(17+dx,3),(17+dx,8))
        else:raise ValueError((slot,index))
        return z.finish()
    return layout


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('slots',nargs='*',type=int,default=list(TITLES));parser.add_argument('--confirm-visual',action='store_true');args=parser.parse_args()
    for slot in args.slots:
        a=confirm_visual(slot) if args.confirm_visual else make_case(slot,TITLES[slot],layout_for(slot))
        print(json.dumps({k:a[k] for k in ['status','instance_counts','total_instances','total_terminals','sheets']},ensure_ascii=False))
