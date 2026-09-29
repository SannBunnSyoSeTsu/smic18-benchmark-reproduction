from schematic_common import *
from schematics_analog import mos,link,bus,finish

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        for k in range(8):
            s.passive(f'RL{k+1}',4+5*k,20,vertical=False,reverse=True)
            if k:link(s,f'RL{k}','1',f'RL{k+1}','2',label=False)
        for k in range(1,8):
            x=6.5+5*(k-1);s.passive(f'CT{k}',x,10);link(s,f'RL{k}','1',f'CT{k}','1',via=[(x,20)])
        bus(s,'vss',[(f'CT{k}','2') for k in range(1,8)],6)
    elif i==2:
        for k in range(7):s.cell('XC'+str(k+1),5+(k%4)*11,19-(k//4)*12)
    elif i==3:
        for k in range(7):s.cell('XS'+str(k+1),7+(k%3)*14,20-(k//3)*8)
    elif i==4:
        for k in range(12):s.cell(f'XE{k+1}',5+(k%4)*11,20-(k//4)*8)
    elif i==5:
        mos(s,[('MPL1',8,21),('MPL2',23,21),('MNL1',8,14),('MNL2',23,14),('MIN1',8,8),('MIN2',23,8),('MTAIL',16,4)]+[(f'MPC{k+1}',38,22-k*6) for k in range(4)])
        for p,n,inp in [('MPL1','MNL1','MIN1'),('MPL2','MNL2','MIN2')]:link(s,p,'D',n,'D');link(s,n,'S',inp,'D')
        bus(s,'tail',[('MIN1','S'),('MIN2','S'),('MTAIL','D')],6);bus(s,'vdd',[('MPL1','S'),('MPL2','S')],24)
    else:
        s.cell('XG1',10,16);s.cell('XG2',32,16)
        link(s,'XG1','ZN','XG2','A2',via=[(22,16),(22,15.5)])
        link(s,'XG2','ZN','XG1','A2',via=[(39,16),(39,8),(5,8),(5,15.5)])
    return finish(s)

if __name__=='__main__':make_case(46,{1:'500Ω电阻梯与七个0.3pF参考滤波',2:'七路StrongARM比较器完整接口',3:'七路HD交叉NAND决策保持',4:'全部HD温度计码至三位编码',5:'fa_comp：动态比较与四路预充晶体管',6:'fa_sr：两个原厂NAND的实际反馈'},layout,blocks={1:'flash_adc_3bit',2:'flash_adc_3bit',3:'flash_adc_3bit',4:'flash_adc_3bit',5:'fa_comp',6:'fa_sr'})
