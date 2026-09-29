from schematic_common import *
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,devices):
    z=Sheet(ax,i,devices)
    if i==1:
        mos(z,[('MPREF',5,19),('MPTAIL',24,21),('MPINR',18,13),('MPINF',31,13),('MNDR',18,5),('MNDF',31,5)])
        link(z,'MPINR','D','MNDR','D');link(z,'MPINF','D','MNDF','D')
        bus(z,'tail',[('MPTAIL','D'),('MPINR','S'),('MPINF','S')],17)
        bus(z,'vdd',[('MPREF','S'),('MPTAIL','S')],24)
        bus(z,'vss',[('MNDR','S'),('MNDF','S')],1.5)
        z.text(3,9,'外部40uA从ibias流向VSS；',8)
        z.text(3,7.6,'vref=0.4V，vout为反馈端。',8)
    else:
        mos(z,[('MPD',8,20),('MNSINK',8,6),('MPOUT',22,20),('MNOUT',22,6),('MPASS',37,17)])
        link(z,'MPD','D','MNSINK','D');link(z,'MPOUT','D','MNOUT','D')
        passive(z,[('CGATE',29,8),('COUT',37,5)])
        link(z,'MPOUT','D','CGATE','1',via=[(22,13),(29,13)],label=False)
        link(z,'MPASS','S','COUT','1')
        bus(z,'vdd',[('MPD','S'),('MPOUT','S'),('MPASS','D')],24)
        bus(z,'vss',[('MNSINK','S'),('MNOUT','S'),('CGATE','2'),('COUT','2')],1.5)
    return finish(z)

if __name__=='__main__':make_case(17,{1:'参考镜、PMOS差分输入与NMOS二极管',2:'镜像输出、NMOS功率管与原生MIM补偿'},layout)
