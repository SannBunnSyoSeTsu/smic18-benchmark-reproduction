from schematic_common import *
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        for k,n in enumerate(['XGIN','XGF','XGB','XGQ']):s.cell(n,10+(k%2)*23,18-(k//2)*12)
    elif i==2:
        s.cell('XCM1',10,19);s.cell('XCM2',32,19);s.mos('MREF',21,13)
        for k,x in enumerate([5,16,27,38]):s.passive(['RS1A','RS1B','RS2A','RS2B'][k],x,10);s.passive(['C1P','C1N','C2P','C2N'][k],x,4)
        bus(s,'vss',[(n,'2') for n in ['C1P','C1N','C2P','C2N']],1.5)
    elif i in [3,4,5]:
        load=i!=5;iy=13 if load else 19
        mos(s,[('MA',10,iy),('MB',30,iy),('MTA',10,5),('MTB',30,5)])
        s.passive('RDEG',20,9,vertical=False)
        for side,tail,pin,x in [('MA','MTA','1',10),('MB','MTB','2',30)]:
            link(s,side,'S',tail,'D');link(s,'RDEG',pin,tail,'D',via=[(x,9)],label=False)
        if load:
            mos(s,[('MLA',10,21),('MLB',30,21)]);link(s,'MLA','D','MA','D');link(s,'MLB','D','MB','D');bus(s,'vdd',[('MLA','S'),('MLB','S')],24)
        bus(s,'vss',[('MTA','S'),('MTB','S')],1.5)
    else:
        mos(s,[('MCL1',10,21),('MCL2',29,21),('MC1',10,13),('MC2',29,13),('MCTA',10,5),('MCTB',29,5)])
        s.passive('RCM',20,9,vertical=False);s.passive('CCM',39,13)
        for a,b,c,x,pin in [('MCL1','MC1','MCTA',10,'1'),('MCL2','MC2','MCTB',29,'2')]:
            link(s,a,'D',b,'D');link(s,b,'S',c,'D');link(s,'RCM',pin,c,'D',via=[(x,9)],label=False)
        bus(s,'vdd',[('MCL1','S'),('MCL2','S')],24);bus(s,'vss',[('MCTA','S'),('MCTB','S')],1.5)
    return finish(s)

if __name__=='__main__':make_case(26,{1:'输入、前向、反馈与阻尼跨导连接',2:'两路共模反馈、共享偏置和全部状态电容',3:'gmc_core：低通状态完整跨导',4:'gmc_core_bp：带通状态负载倍率1.5',5:'gmc_sink：独立阻尼跨导',6:'cmfb_amp：共模检测、复制负载与补偿'},layout,blocks={1:'fd_ota_c_biquad',2:'fd_ota_c_biquad',3:'gmc_core',4:'gmc_core_bp',5:'gmc_sink',6:'cmfb_amp'})
