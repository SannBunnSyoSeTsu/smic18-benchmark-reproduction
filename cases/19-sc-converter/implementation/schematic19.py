from schematic_common import *
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        names=['XRX1','XRX2','XNA','XNB','XA1','XA2','XA3','XFB1','XB1','XB2','XB3','XFB2']
        for k,n in enumerate(names):s.cell(n,5+(k%4)*11,20-(k//4)*8)
    elif i in [2,3]:
        b='A' if i==2 else 'B'
        for k,n in enumerate([f'XDP{b}',f'XDN3{b}1',f'XDN3{b}2',f'XDNP{b}1',f'XDNP{b}2']):s.cell(n,7+(k%3)*14,20-(k//3)*12)
    else:
        b='A' if i==4 else 'B'
        mos(s,[(f'MP1{b}',8,21),(f'MN2{b}',33,21),(f'MN3{b}',8,5),(f'MN4{b}',33,5)])
        passive(s,[(f'CF{b}',8,13),(f'CBP{b}',22,5)]+([('CO',32,13)] if i==5 else []))
        link(s,f'MP1{b}','D',f'CF{b}','1');link(s,f'CF{b}','2',f'MN3{b}','D')
        link(s,f'MP1{b}','D',f'MN2{b}','D',via=[(8,17),(27,17),(27,24),(33,24)],label=False)
        link(s,f'MN3{b}','D',f'MN4{b}','D',via=[(8,9),(33,9)],label=False)
        link(s,f'CBP{b}','1',f'MN3{b}','D',via=[(22,9),(8,9)],label=False)
        bus(s,'vss',[(f'MN4{b}','S'),(f'CBP{b}','2')],1.5)
        if i==5:link(s,'CO','2',f'MN4{b}','S',via=[(39,s.p('CO','2')[1]),(39,1.5),(33,1.5)],label=False)
        s.text(2,.1,'A/B两支路交替串联充电与并联向输出供电；原厂MIM保留工艺模型。',7.5)
    return finish(s)

if __name__=='__main__':make_case(19,{1:'HD时钟接收与交叉反馈非交叠',2:'A支路全部HD栅极驱动',3:'B支路全部HD栅极驱动',4:'A支路四开关和飞跨/底板电容',5:'B支路四开关和飞跨/输出电容'},layout)
