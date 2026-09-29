from schematic_common import *
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        for k,n in enumerate(['XENB','XNAND','XPH0','XPH1','XDR0','XDR1']):s.cell(n,7+(k%3)*14,20-(k//3)*12)
    elif i==2:
        mos(s,[('MPM',27,21),('MPD',39,21),('MREFIN',27,13),('MFBIN',39,13),('MTAIL',33,5),('MREF',5,5),('MOFFN',15,5),('MOFFP',5,21),('MOFFCTRL',15,21)])
        link(s,'MPM','D','MREFIN','D');link(s,'MPD','D','MFBIN','D');bus(s,'tail',[('MREFIN','S'),('MFBIN','S'),('MTAIL','D')],9)
        bus(s,'AVDD',[(n,'S') for n in ['MPM','MPD','MOFFP','MOFFCTRL']],24)
        bus(s,'AVSS',[(n,'S') for n in ['MTAIL','MREF','MOFFN']],1.5)
    elif i==3:
        mos(s,[('MCTRL',7,21),('MENREF',7,5),('MENFB',19,5)])
        passive(s,[('CN',7,13),('CP',19,13),('RZ0',32,21),('RZ1',32,16),('RZ2',32,11),('CC',32,5)])
        link(s,'RZ0','2','RZ1','1');link(s,'RZ1','2','RZ2','1');link(s,'RZ2','2','CC','1')
        bus(s,'AVSS',[('MENREF','S'),('MENFB','S')],1.5)
    elif i in [4,5]:
        pre='RN' if i==4 else 'RP'
        for col,x in enumerate([8,27]):
            for k in range(6):
                s.passive(f'{pre}{col}_{k}',x,22-k*4)
                if k:link(s,f'{pre}{col}_{k-1}','2',f'{pre}{col}_{k}','1')
    else:
        mos(s,[('MPRE0',7,20),('MRECT0',18,20),('MPRE1',29,20),('MRECT1',40,20)])
        passive(s,[('CF0',7,7),('CF1',29,7)])
        for k in [0,1]:
            bus(s,f'p{k}',[(f'MPRE{k}','S'),(f'MRECT{k}','S'),(f'CF{k}','1')],14)
        bus(s,'VOUT',[('MRECT0','D'),('MRECT1','D')],24)
    return finish(s)

if __name__=='__main__':make_case(18,{1:'全部HD相位逻辑与可变供电驱动',2:'gm/ID误差放大器与关闭钳位',3:'幅度调节、使能开关与零点补偿',4:'参考分压：两串原生多晶电阻',5:'输出反馈：1.6:1原生多晶分压',6:'双相原生nnt33预充、整流与MIM'},layout)
