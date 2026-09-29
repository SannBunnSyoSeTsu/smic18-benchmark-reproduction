from schematic_common import *
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,devices):
    z=Sheet(ax,i,devices)
    if i==1:
        mos(z,[('MPA',8,20),('MN1',8,6),('MPB',21,20),('MN2',21,10),('MPT',36,20)])
        passive(z,[('RSTART',3,16),('RS',21,4)])
        link(z,'MPA','D','MN1','D');link(z,'MPB','D','MN2','D');link(z,'MN2','S','RS','1')
        link(z,'RSTART','2','MN1','D',via=[(3,11),(8,11)],label=False)
        bus(z,'vin',[('MPA','S'),('MPB','S'),('MPT','S'),('RSTART','1')],24)
        bus(z,'vss',[('MN1','S'),('RS','2')],1.5)
    elif i==2:
        mos(z,[('MIR',5,19),('MIF',15,19),('MNDR',5,5),('MNDF',15,5),('MNSINK',26,5),('MNOUT',38,5),('MPD',26,19),('MPOUT',38,19)])
        link(z,'MIR','D','MNDR','D');link(z,'MIF','D','MNDF','D');link(z,'MPD','D','MNSINK','D');link(z,'MPOUT','D','MNOUT','D')
        bus(z,'tail',[('MIR','S'),('MIF','S')],23)
        bus(z,'vin',[('MPD','S'),('MPOUT','S')],23)
        bus(z,'vss',[(n,'S') for n in ['MNDR','MNDF','MNSINK','MNOUT']],1.5)
    else:
        mos(z,[('MPASS',8,22)])
        passive(z,[('CM',3,14),('RZ',3,7),('R1',21,13),('R2',21,5),('CF',27,13),('RESR',33,13),('C1',33,5),('C2',41,11)])
        link(z,'CM','2','RZ','1');link(z,'R1','2','R2','1');link(z,'RESR','2','C1','1')
        bus(z,'vout',[('MPASS','D'),('R1','1'),('CF','1'),('RESR','1'),('C2','1')],17)
        a=z.p('RZ','2');b=z.p('MPASS','D');link(z,'RZ','2','MPASS','D',via=[(1,a[1]),(1,19),(8,19)],label=False)
        link(z,'R1','2','CF','2',via=[(21,9),(27,9)],label=False)
        bus(z,'vss',[('R2','2'),('C1','2'),('C2','2')],1.5)
    return finish(z)

if __name__=='__main__':make_case(38,{1:'自偏置β倍增与尾源',2:'隔离体PMOS输入与镜像OTA',3:'PMOS功率管、分压器及全部内部补偿'},layout)
