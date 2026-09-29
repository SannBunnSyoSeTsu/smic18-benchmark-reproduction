"""Topology-specific complete schematics for 07/08/29/35/36/37/47/50.

Only the final netlists and geometry are read; no EDA runs or electrical edits.
Shared symbol/render/connection audits are provided by schematic_common.py.
"""
from __future__ import annotations
import argparse
from schematic_common import Sheet, make_case, confirm_visual


def mos(z,items):
    for name,x,y in items:z.mos(name,x,y)


def passive(z,items):
    for row in items:
        name,x,y,*args=row;z.passive(name,x,y,vertical=args[0] if args else True,reverse=args[1] if len(args)>1 else False)


def link(z,a,pa,b,pb,via=(),label=True):
    net=z.devices[a]['pins'][pa];assert net==z.devices[b]['pins'][pb],(a,pa,b,pb)
    pts=[z.p(a,pa),*via,z.p(b,pb)];z.wire(net,*pts)
    if label:
        x1,y1=pts[0];x2,y2=pts[1];z.tag(net,((x1+x2)/2,(y1+y2)/2))


def bus(z,net,pins,y):
    pts=[z.p(*p) for p in pins];xs=[p[0] for p in pts]
    if min(xs)!=max(xs):z.wire(net,(min(xs),y),(max(xs),y))
    for p in pts:z.wire(net,p,(p[0],y))
    z.tag(net,(min(xs),y),dy=.33)


def finish(z):
    for name,d in z.instances.items():
        if d['kind']=='MOS' and d['pins']['D']==d['pins']['G'] and not z.pins[(name,'G')]['connected']:
            x,y=d['origin'];yj=y+2.2 if d['model']=='n18' else y-2.2
            z.diode(name,d['pins']['D'],yj);z.tag(d['pins']['D'],(x-1,yj),ha='center',dx=0,dy=.35)
    return z.finish()


def parallel_rc(z,r,c,x,y1,y2,left,right):
    z.passive(r,x,y1,vertical=False);z.passive(c,x,y2,vertical=False)
    link(z,r,'1',c,'1',via=[(left,y1),(left,y2)],label=False)
    link(z,r,'2',c,'2',via=[(right,y1),(right,y2)],label=False)
    z.tag(z.devices[r]['pins']['1'],(left,(y1+y2)/2),ha='right',dx=-.2,dy=0)
    z.tag(z.devices[r]['pins']['2'],(right,(y1+y2)/2),dy=0)


def layout07(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MREF',3,5),('MPTREF',11,18),('MNPT',11,5),('MTAIL',29,21),('MINP',24,13),('MINN',36,13),('MLOAD',24,5),('MLOUT',36,5)])
        link(z,'MPTREF','D','MNPT','D');link(z,'MINP','D','MLOAD','D');link(z,'MINN','D','MLOUT','D')
        bus(z,'tail',[('MTAIL','D'),('MINP','S'),('MINN','S')],17)
        bus(z,'vin',[('MPTREF','S'),('MTAIL','S')],23.5)
        bus(z,'vss',[(n,'S') for n in ['MREF','MNPT','MLOAD','MLOUT']],1.5)
        link(z,'MLOAD','D','MLOUT','G',via=[(24,9),(32.5,9),(32.5,5)],label=False)
    else:
        mos(z,[('MBUF',10,20),('MSF',10,13),('MNBUF',10,6),('MPASS',29,19)])
        link(z,'MBUF','D','MSF','S');link(z,'MSF','D','MNBUF','D')
        link(z,'MSF','D','MBUF','G',via=[(6.2,12),(6.2,20)],label=False)
        bus(z,'vin',[('MBUF','S'),('MPASS','S')],23)
        passive(z,[('RLAG',29,10),('CLAG',29,5)])
        link(z,'RLAG','2','CLAG','1')
        bus(z,'vss',[('MNBUF','S'),('CLAG','2')],1.5)
        z.text(20,14.5,'gate_drive、gate、fb 为独立 DUT 端口',6.9)
    return finish(z)


def layout08(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MREF',3,6),('MBP',10,19),('MBN',10,6),('MPBN1',17,19),('MNBN1',17,11),('MPBP1',24,17),('MNBP1',24,6),('MPBN2',31,21),('MNBN2',31,14),('MPBP2',38,14),('MNBP2',38,6)])
        passive(z,[('RNB',31,8),('RPB',38,21)])
        for a,b in [('MBP','MBN'),('MPBN1','MNBN1'),('MPBP1','MNBP1'),('MPBN2','MNBN2'),('MPBP2','MNBP2')]:link(z,a,'D',b,'D')
        link(z,'MNBN2','S','RNB','1');link(z,'RPB','2','MPBP2','S')
        bus(z,'VDD',[(n,'S') for n in ['MBP','MPBN1','MPBN2']],23.5)
        bus(z,'VSS',[(n,'S') for n in ['MREF','MBN','MNBP1','MNBP2']],2)
    else:
        side='P' if index==2 else 'N';out='VO'+side
        top='MCN'+side;inp='MIN'+side;ipp='MIP'+side;bottom='MCP'+side
        mos(z,[(top,32,21),(inp,32,16),(ipp,32,10),(bottom,32,5)])
        link(z,top,'S',inp,'D');link(z,inp,'S',ipp,'S');link(z,ipp,'D',bottom,'S')
        for suffix,dev,y in [('gcn',top,21),('gn',inp,16),('gp',ipp,10),('gcp',bottom,5)]:
            r='R'+suffix+side;c='C'+suffix+side
            passive(z,[(r,8,y,False),(c,18,y,False)])
            link(z,r,'2',c,'1')
            link(z,r,'2',dev,'G',via=[(12,y),(12,y+2),(27,y+2),(27,y)],label=False)
        # Actual input and output bootstrap buses join their corresponding caps.
        link(z,'Cgn'+side,'2','Cgp'+side,'2',via=[(22,16),(22,10)])
        link(z,'Cgcn'+side,'2','Cgcp'+side,'2',via=[(25,21),(25,5)])
        link(z,'Cgcp'+side,'2',inp,'S',via=[(25,5),(25,13),(32,13)],label=False)
    return finish(z)


def layout29(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MREF',4,6),('MPB',14,19),('MNB',14,6),('MPNB',30,19),('MNCB',30,6)])
        passive(z,[('RCP',14,13),('RCN',30,12),('CBB',21,16,False),('CBP',21,9,False),('CBN',38,13)])
        link(z,'MPB','D','RCP','1');link(z,'RCP','2','MNB','D');link(z,'MPNB','D','RCN','1');link(z,'RCN','2','MNCB','D')
        link(z,'CBB','1','MPB','D',via=[(14,16)],label=False)
        link(z,'CBP','1','MNB','D',via=[(14,9)],label=False)
        link(z,'CBB','2','CBP','2',via=[(25,16),(25,9)],label=False)
        link(z,'MPNB','D','CBN','1',via=[(30,16.5),(38,16.5)],label=False)
        bus(z,'vdd',[('MPB','S'),('MPNB','S')],23.5)
        z.wire('vdd',(25,16),(25,23.5))
        bus(z,'vss',[('MREF','S'),('MNB','S'),('MNCB','S'),('CBN','2')],1.5)
    else:
        mos(z,[('MINN',4,15),('MINP',11,15),('MTAIL',7.5,6),('MFP',19,21),('MFN',29,21),('MFCP',19,15),('MFCN',29,15),('MCD',19,9),('MCO',29,9),('MMD',19,4),('MMO',29,4),('MLOAD',38,20),('MSECOND',38,7)])
        for a,b,c,d in [('MFP','MFCP','MCD','MMD'),('MFN','MFCN','MCO','MMO')]:
            link(z,a,'D',b,'S');link(z,b,'D',c,'D');link(z,c,'S',d,'D')
        link(z,'MINN','D','MFP','D',via=[(4,18.5),(19,18.5)],label=False)
        link(z,'MINP','D','MFN','D',via=[(11,17.5),(29,17.5)],label=False)
        bus(z,'tail',[('MINN','S'),('MINP','S'),('MTAIL','D')],11.5)
        link(z,'MCD','D','MMD','G',via=[(16,10),(16,4)],label=False)
        link(z,'MMD','G','MMO','G',via=[(16,4),(16,6.5),(26,6.5),(26,4)],label=False)
        link(z,'MLOAD','D','MSECOND','D')
        link(z,'MCO','D','MSECOND','G',via=[(29,12),(36,12),(36,7)],label=False)
        passive(z,[('CC',35,4,False,True)])
        link(z,'CC','1','MSECOND','D',via=[(43.5,4),(43.5,12),(38,12)],label=False)
        link(z,'CC','2','MFN','D',via=[(33,4),(33,17.5),(29,17.5)],label=False)
        bus(z,'vdd',[(n,'S') for n in ['MFP','MFN','MLOAD']],23.5)
        bus(z,'vss',[(n,'S') for n in ['MTAIL','MMD','MMO','MSECOND']],1.5)
    return finish(z)


def layout35(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MREF',3,5),('MBP',11,19),('MBN',11,5),('MOBP',20,19),('MOBN',20,5),('MNCB',29,20),('MDN',29,14),('MDP',39,14),('MPCB',39,5)])
        passive(z,[('RNB',29,7),('RPC',39,20)])
        link(z,'MBP','D','MBN','D');link(z,'MOBP','D','MOBN','D');link(z,'MNCB','D','MDN','D');link(z,'MDN','S','RNB','1');link(z,'RPC','2','MDP','S');link(z,'MDP','D','MPCB','D')
        bus(z,'vdd',[('MBP','S'),('MOBP','S'),('MNCB','S'),('RPC','1')],23.5)
        bus(z,'vss',[('MREF','S'),('MBN','S'),('MOBN','S'),('RNB','2'),('MPCB','S')],1.5)
    elif index==2:
        mos(z,[('MINP',4,15),('MINN',13,15),('MTAIL',7,5),('MSP',24,21),('MSN',37,21),('MPCP',24,15),('MPCN',37,15),('MNCP',24,10),('MNCN',37,10),('MSINKP',24,5),('MSINKN',37,5)])
        for a,b,c,d in [('MSP','MPCP','MNCP','MSINKP'),('MSN','MPCN','MNCN','MSINKN')]:
            link(z,a,'D',b,'S');link(z,b,'D',c,'D');link(z,c,'S',d,'D')
        link(z,'MINP','D','MSP','D',via=[(4,18),(24,18)],label=False)
        link(z,'MINN','D','MSN','D',via=[(13,17),(37,17)],label=False)
        bus(z,'tail',[('MINP','S'),('MINN','S'),('MTAIL','D')],11)
        bus(z,'vdd',[('MSP','S'),('MSN','S')],23.5)
        bus(z,'vss',[('MTAIL','S'),('MSINKP','S'),('MSINKN','S')],1.5)
    elif index==3:
        mos(z,[('MLOADP',10,20),('MLOADN',33,20),('MSECONDP',10,11),('MSECONDN',33,11)])
        link(z,'MLOADP','D','MSECONDP','D');link(z,'MLOADN','D','MSECONDN','D')
        passive(z,[('RZP',6,4,False),('CCP',16,4,False),('RZN',29,4,False),('CCN',39,4,False)])
        link(z,'RZP','2','CCP','1');link(z,'RZN','2','CCN','1')
        link(z,'RZP','1','MSECONDP','G',via=[(4,4),(4,11)],label=False)
        link(z,'RZN','1','MSECONDN','G',via=[(27,4),(27,11)],label=False)
        z.tag('stagep',(4,8.5),ha='right',dx=-.2,dy=0);z.tag('stagen',(27,8.5),ha='right',dx=-.2,dy=0)
        link(z,'CCP','2','MSECONDP','D',via=[(22,4),(22,15),(10,15)],label=False)
        link(z,'CCN','2','MSECONDN','D',via=[(42,4),(42,15),(33,15)],label=False)
        bus(z,'vdd',[('MLOADP','S'),('MLOADN','S')],23.5)
        bus(z,'vss',[('MSECONDP','S'),('MSECONDN','S')],7)
    else:
        mos(z,[('MCMD',5,20),('MCMM',15,20),('MCMREF',5,12),('MCMSENSE',15,12),('MCMT',10,5),('MCMND',21,5)])
        link(z,'MCMD','D','MCMREF','D');link(z,'MCMM','D','MCMSENSE','D')
        bus(z,'cmt',[('MCMREF','S'),('MCMSENSE','S'),('MCMT','D')],9)
        link(z,'MCMSENSE','D','MCMND','D',via=[(15,16),(21,16)],label=False)
        bus(z,'vdd',[('MCMD','S'),('MCMM','S')],23.5)
        bus(z,'vss',[('MCMT','S'),('MCMND','S')],1.5)
        parallel_rc(z,'RCMP','CCMP',34,20,17,28,40);parallel_rc(z,'RCMN','CCMN',34,13,10,28,40)
        z.wire('vcms',(40,17),(40,13))
    return finish(z)


def layout47(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MN0',4,6),('MPCB',12,19),('MN2',12,6),('MP2X',22,19),('MNCB',22,6),('MP0',34,21),('MPC0',34,16),('MNC1',34,10),('MN1',34,5)])
        link(z,'MPCB','D','MN2','D');link(z,'MP2X','D','MNCB','D')
        link(z,'MP0','D','MPC0','S');link(z,'MPC0','D','MNC1','D');link(z,'MNC1','S','MN1','D')
        passive(z,[('CIR',4,12,True,True),('CBPC',18,14),('CBNC',27,9),('CBP',41,13)])
        link(z,'CIR','1','MN0','D',label=False)
        link(z,'CBPC','1','MPCB','D',via=[(18,16),(12,16)],label=False)
        link(z,'CBNC','1','MNCB','D',via=[(27,12),(22,12)],label=False)
        link(z,'CBP','1','MPC0','D',via=[(41,14.5),(34,14.5)],label=False)
        bus(z,'vdd',[('MPCB','S'),('MP2X','S'),('MP0','S')],23.5)
        bus(z,'vss',[('MN0','S'),('MN2','S'),('MNCB','S'),('MN1','S'),('CBNC','2')],1.5)
    elif index==2:
        mos(z,[('MPM',14,22),('MPC',14,18),('MSUP',14,12),('MSDU',4.5,12),('MNWU',4.5,5),('MSDN',28,10),('MNC',28,6),('MNM',28,2),('MSDD',38,10),('MNWD',38,19)])
        passive(z,[('CNC',8,18,True,True),('CWU',10,5),('CND',33,5),('CWD',34,19,False)])
        link(z,'MPM','D','MPC','S');link(z,'MSDU','D','MNWU','D')
        bus(z,'nc',[('MPC','D'),('MSUP','S'),('MSDU','S'),('CNC','1')],15.3)
        link(z,'MSUP','D','MSDN','D')
        link(z,'MSDN','S','MNC','D',label=False);link(z,'MNC','S','MNM','D')
        bus(z,'nd',[('MNC','D'),('MSDD','S'),('CND','1')],8)
        link(z,'MNWD','S','MSDD','D')
        link(z,'CWU','1','MNWU','D',via=[(10,8.5),(4.5,8.5)],label=False)
        link(z,'CWD','1','MNWD','S',via=[(31,19),(31,16),(38,16)],label=False)
        link(z,'CWD','2','MNWD','G')
        bus(z,'vdd',[('MPM','S'),('MNWD','D')],24)
        bus(z,'vss',[('MNWU','S'),('MNM','S'),('CWU','2'),('CND','2')],.3)
    else:
        z.cell('XUP',10,17);z.cell('XUPD',30,17);z.cell('XDN',10,7)
        link(z,'XUP','ZN','XUPD','I')
        bus(z,'vdd',[(n,p) for n in ['XUP','XUPD'] for p in ['VDD','VNW']],19.7)
        bus(z,'vss',[(n,p) for n in ['XUP','XUPD'] for p in ['VSS','VPW']],12.5)
        bus(z,'vdd',[('XDN','VDD'),('XDN','VNW')],9.7)
        bus(z,'vss',[('XDN','VSS'),('XDN','VPW')],3.5)
        z.text(23,6.5,'每个反相器的 VDD / VSS / VNW / VPW 均显式引出。',6.8)
        z.text(23,4.8,'upb、upd、dnb 与第 2 页电流转向开关同名相连。',6.8)
    return finish(z)


def layout50(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MREF',3,5),('MPBP',10,19),('MNBP',10,5),('MPPC',18,14),('MNPC',18,5),('MPB2',25.5,21),('MNCB',25.5,14),('MNRS',32.5,18),('MNRBI',32.5,6),('MPRBI',39.5,20),('MPRS',39.5,10)])
        passive(z,[('RPC',18,20),('RNCB',25.5,7)])
        link(z,'MPBP','D','MNBP','D');link(z,'RPC','2','MPPC','S');link(z,'MPPC','D','MNPC','D')
        link(z,'MPB2','D','MNCB','D');link(z,'MNCB','S','RNCB','1')
        link(z,'MNRS','S','MNRBI','D');link(z,'MPRBI','D','MPRS','S')
        bus(z,'vdd',[('MPBP','S'),('RPC','1'),('MPB2','S'),('MNRS','D'),('MPRBI','S')],24)
        bus(z,'vss',[('MREF','S'),('MNBP','S'),('MNPC','S'),('RNCB','2'),('MNRBI','S'),('MPRS','D')],1.5)
    elif index==2:
        mos(z,[('MINP',4,17),('MINN',12,17),('MTAIL',8,5),('MFP',24,21),('MFN',37,21),('MFCP',24,15),('MFCN',37,15),('MMD',24,10),('MMO',37,10),('MCD',24,5),('MCO',37,5)])
        passive(z,[('RINP',4,12),('RINN',12,12)])
        for a,b,c,d in [('MFP','MFCP','MMD','MCD'),('MFN','MFCN','MMO','MCO')]:
            link(z,a,'D',b,'S');link(z,b,'D',c,'D');link(z,c,'S',d,'D')
        link(z,'MINP','D','MFP','D',via=[(4,19),(24,19)],label=False)
        link(z,'MINN','D','MFN','D',via=[(12,18.5),(37,18.5)],label=False)
        link(z,'MINP','S','RINP','1');link(z,'MINN','S','RINN','1')
        bus(z,'tail',[('RINP','2'),('RINN','2'),('MTAIL','D')],9)
        link(z,'MMD','D','MCD','G',via=[(20.5,11),(20.5,5)],label=False)
        link(z,'MCD','G','MCO','G',via=[(20.5,5),(20.5,7.5),(33.5,7.5),(33.5,5)],label=False)
        bus(z,'vdd',[('MFP','S'),('MFN','S')],23.5)
        bus(z,'vss',[('MTAIL','S'),('MCD','S'),('MCO','S')],1.5)
    elif index==3:
        mos(z,[('MHSF',4,19),('MHSI',4,6),('MHRF',13,19),('MHRI',13,6),('MPT',31,22),('MPA',25,15),('MPB',37,15),('MPMA',25,6),('MPMB',37,6)])
        link(z,'MHSF','S','MHSI','D');link(z,'MHRF','S','MHRI','D')
        link(z,'MPA','D','MPMA','D');link(z,'MPB','D','MPMB','D')
        bus(z,'apt',[('MPT','D'),('MPA','S'),('MPB','S')],18.5)
        link(z,'MHRF','S','MPA','G',via=[(13,13),(21,13),(21,15)],label=False)
        link(z,'MHSF','S','MPB','G',via=[(4,11),(32.5,11),(32.5,15)],label=False)
        link(z,'MPMA','D','MPMB','G',via=[(25,9),(33,9),(33,6)],label=False)
        passive(z,[('CGPC',41,17,True,True)])
        link(z,'CGPC','1','MPB','D',via=[(42.5,16.18),(42.5,12),(37,12)],label=False)
        bus(z,'vdd',[('MHSF','D'),('MHRF','D'),('MPT','S'),('CGPC','2')],24)
        bus(z,'vss',[(n,'S') for n in ['MHSI','MHRI','MPMA','MPMB']],1.5)
    else:
        mos(z,[('MNT',10,22),('MNA',5,15),('MNB',15,15),('MNMA',5,6),('MNMB',15,6),('MOBP',27,20),('MOBN',27,6),('MLOAD',38,21),('MOUTC',38,15),('MOUT',38,8)])
        link(z,'MNA','D','MNMA','D');link(z,'MNB','D','MNMB','D')
        bus(z,'ant',[('MNT','D'),('MNA','S'),('MNB','S')],18.5)
        link(z,'MNMA','D','MNMB','G',via=[(5,10),(12,10),(12,6)],label=False)
        passive(z,[('CGNC',20,8),('RCOMP',25,3,False,True),('CCOMP',35,3,False,True)])
        link(z,'CGNC','1','MNB','D',via=[(20,11),(15,11)],label=False)
        link(z,'MOBP','D','MOBN','D');link(z,'MLOAD','D','MOUTC','D');link(z,'MOUTC','S','MOUT','D')
        link(z,'CCOMP','2','RCOMP','1')
        link(z,'CCOMP','1','MOUTC','D',via=[(43.5,3),(43.5,18),(38,18)],label=False)
        link(z,'RCOMP','2','MOUT','G',via=[(23,3),(23,8)],label=False);z.tag('nfirst',(31,8),dy=.35)
        bus(z,'vdd',[('MNT','S'),('MOBP','S'),('MLOAD','S')],24)
        bus(z,'vss',[('MNMA','S'),('MNMB','S'),('MOBN','S'),('MOUT','S'),('CGNC','2')],1.5)
    return finish(z)


def layout37(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MREF',3,6),('MPDM',11,18),('MBP1',11,6),('MS2B',20,18),('MVBN',20,6),('MP1A',29,19),('MP1B',38,19),('MI1',29,12),('MI2',38,12),('MTAIL',33,5)])
        link(z,'MPDM','D','MBP1','D');link(z,'MS2B','D','MVBN','D')
        link(z,'MP1A','D','MI1','D');link(z,'MP1B','D','MI2','D')
        bus(z,'tail',[('MI1','S'),('MI2','S'),('MTAIL','D')],8.5)
        bus(z,'vdd',[(n,'S') for n in ['MPDM','MS2B','MP1A','MP1B']],23)
        bus(z,'vss',[(n,'S') for n in ['MREF','MBP1','MVBN','MTAIL']],1.5)
    else:
        mos(z,[('MPD2',8,19),('MA2',8,9),('MPM2',22,19),('MS2',22,9),('ML3',36,19),('MA3',36,9)])
        link(z,'MPD2','D','MA2','D');link(z,'MPM2','D','MS2','D');link(z,'ML3','D','MA3','D')
        bus(z,'vdd',[(n,'S') for n in ['MPD2','MPM2','ML3']],23)
        bus(z,'vss',[(n,'S') for n in ['MA2','MS2','MA3']],6)
        link(z,'MPD2','D','MPM2','G',via=[(8,16),(19.9,16),(19.9,19)],label=False)
        link(z,'MPM2','D','MA3','G',via=[(22,13),(31,13),(31,9)],label=False)
        passive(z,[('CM1',20,3.5,False,True),('CM2',20,1,False,True)])
        link(z,'MA3','D','CM1','1',via=[(36,11),(40,11),(40,3.5)],label=False)
        link(z,'CM1','1','CM2','1',via=[(40,3.5),(40,1)],label=False)
        link(z,'CM2','2','MPM2','D',via=[(17,1),(17,13),(22,13)],label=False)
    return finish(z)


def layout36(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        mos(z,[('MREF',3,6),('MPM',11,19),('MT5',11,6),('MR1',21,17),('MT1',21,6),('MPB2',29,20),('MD1',29,14),('MDP1',39,14),('MT4',39,6)])
        passive(z,[('RN',29,10),('RP',39,20)])
        link(z,'MPM','D','MT5','D');link(z,'MR1','S','MT1','D');link(z,'MPB2','D','MD1','D');link(z,'MD1','S','RN','1');link(z,'RP','2','MDP1','S');link(z,'MDP1','D','MT4','D')
        link(z,'RN','2','MT1','D',via=[(29,8.5),(21,8.5)],label=False)
        bus(z,'vdd',[('MPM','S'),('MR1','D'),('MPB2','S'),('RP','1')],23.5)
        bus(z,'vss',[(n,'S') for n in ['MREF','MT5','MT1','MT4']],1.5)
    elif index==2:
        mos(z,[('MPTN',12,21),('MPTP',31,21),('MPCN',12,16.5),('MPCP',31,16.5),('MNCP',12,12.5),('MNCN',31,12.5),('MINP',12,8),('MINN',31,8),('MTAIL',22,3.5)])
        for a,b,c,d in [('MPTN','MPCN','MNCP','MINP'),('MPTP','MPCP','MNCN','MINN')]:
            link(z,a,'D',b,'S');link(z,b,'D',c,'D');link(z,c,'S',d,'D')
        bus(z,'tail',[('MINP','S'),('MINN','S'),('MTAIL','D')],6)
        bus(z,'vdd',[('MPTN','S'),('MPTP','S')],23.5)
        bus(z,'vss',[('MTAIL','S')],1)
    else:
        mos(z,[('MCML',5,20),('MCMLO',15,20),('MCMS',5,12),('MCMR',15,12),('MCMT',10,5)])
        link(z,'MCML','D','MCMS','D');link(z,'MCMLO','D','MCMR','D');bus(z,'cmt',[('MCMS','S'),('MCMR','S'),('MCMT','D')],9)
        bus(z,'vdd',[('MCML','S'),('MCMLO','S')],23);bus(z,'vss',[('MCMT','S')],1.5)
        parallel_rc(z,'RSP','CSP',29,20,17,23,36);parallel_rc(z,'RSN','CSN',29,13,10,23,36)
        passive(z,[('CCP',25,5,False),('RZP',35,5,False),('CCN',25,2,False),('RZN',35,2,False)])
        link(z,'CCP','2','RZP','1');link(z,'CCN','2','RZN','1')
    return finish(z)


TITLES={
    7:{1:'偏置与五管误差放大器',2:'栅极缓冲、PMOS 调整管与工艺 RC 补偿'},
    8:{1:'互补输入与级联管的四路偏置',2:'VIP → VOP 推挽源跟随与自举网络',3:'VIN → VON 推挽源跟随与自举网络'},
    29:{1:'级联偏置与去耦网络',2:'折叠输入级、电流镜、输出级及 Ahuja 补偿'},
    35:{1:'输入级、输出级与级联偏置',2:'全差分折叠输入级与受控下拉支路',3:'双输出级及两路 Miller 串联 RC 反馈',4:'连续共模反馈与输出共模检测'},
    47:{1:'电流基准、级联偏置与去耦',2:'上下电流转向、虚设支路与输出',3:'原厂 HD 反相器与开关控制网络'},
    50:{1:'电流、级联及提升放大器参考偏置',2:'源极退化差分输入与增益提升折叠核心',3:'高侧电平移位与 P 侧增益提升环路',4:'N 侧增益提升、级联输出与 Miller 补偿'},
    37:{1:'偏置、输入差分对与第一级镜负载',2:'第二／第三级及两条嵌套 Miller 通路'},
    36:{1:'输入共模跟踪与级联偏置',2:'全差分套筒放大核心',3:'连续共模反馈、检测与双路补偿'},
}
LAYOUTS={7:layout07,8:layout08,29:layout29,35:layout35,37:layout37,36:layout36,47:layout47,50:layout50}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slot',type=int,choices=list(LAYOUTS));p.add_argument('--confirm-visual',action='store_true');args=p.parse_args()
    if args.confirm_visual:confirm_visual(args.slot)
    else:make_case(args.slot,TITLES[args.slot],LAYOUTS[args.slot])
