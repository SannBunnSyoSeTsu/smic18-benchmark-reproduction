from schematic_common import *
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        names=['MPM4','MPM5','MPM12','MPM10','MPM11','MNM4','MNM11','MNM12','MNM13a','MNM13b','MNM13c','MNM13d']
        mos(s,[(n,6+10*(k%4),22-8*(k//4)) for k,n in enumerate(names)])
    elif i==2:
        mos(s,[('MPM3',10,21),('MPM0',32,21),('MNM1',10,13),('MNM0',32,13),('MNM3',7,4),('MNM14',21,4),('MNM2',35,4)])
        link(s,'MPM3','D','MNM1','D');link(s,'MPM0','D','MNM0','D');bus(s,'net2',[(n,'D') for n in ['MNM3','MNM14','MNM2']]+[('MNM1','S'),('MNM0','S')],8)
        s.passive('R3',18,18,False,True);s.passive('R1',25,18,False,True);link(s,'R3','1','R1','2')
    elif i==3:
        mos(s,[('MPM1',8,21),('MPM13',8,13),('MNM5',8,5)]+[(f'MNM15{letter}',17+7*k,13) for k,letter in enumerate('abcd')])
        s.passive('C0',21,22);s.passive('C1',36,22)
        link(s,'MPM1','D','MPM13','S');link(s,'MPM13','D','MNM5','D')
        bus(s,'vgp3',[(f'MNM15{x}','D') for x in 'abcd'],18);bus(s,'vgn3',[(f'MNM15{x}','S') for x in 'abcd'],8)
    elif i==4:
        mos(s,[('MPM8',10,21),('MPM7',10,13),('MNM8',10,5),('MNM9',30,13)])
        s.passive('C2',26,22);s.passive('C3',38,22)
        link(s,'MPM8','D','MPM7','S');link(s,'MPM7','D','MNM8','D')
        link(s,'MNM9','D','MPM8','D',via=[(30,18),(10,18)])
        link(s,'MNM9','S','MNM8','D',via=[(30,8),(10,8)])
    elif i==5:
        mos(s,[('MPM6',10,20),('MNM7',10,8),('MPM9',32,20),('MNM10',32,8)])
        link(s,'MPM6','D','MNM7','D');link(s,'MPM9','D','MNM10','D')
        s.passive('C10',19,14);s.passive('C11',25,14)
        link(s,'C10','1','C11','1',via=[(19,17),(25,17)])
    else:
        passive(s,[('L0',7,21,False),('L1',31,21,False),('C4',7,13,False),('C5',31,13,False),('C6',7,6,False),('C7',31,6,False)])
        mos(s,[('MSTARTP',17,13),('MSTARTN',41,13)])
    return finish(s)

if __name__=='__main__':make_case(6,{1:'基准电流与双极性级联偏置',2:'第一级差分输入、镜负载及共模检测',3:'第二级正支路与自调零存储',4:'第二级负支路与自调零存储',5:'互补输出级与输出共模电容反馈',6:'交流耦合、反馈电容与弱启动支路'},layout)
