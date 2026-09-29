"""Full two-phase charge-pump transistor and vendor-cell sheet."""
from schematic_common import *

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    for name,x in [('XEN',7),('XPH0',23),('XPH1',38)]:s.cell(name,x,20)
    s.wire('gated',s.p('XEN','ZN'),s.p('XPH0','I'))
    s.tag('gated',(14,20))
    s.wire('ph0',s.p('XPH0','ZN'),s.p('XPH1','I'));s.tag('ph0',(30,20))
    for k,x in [(0,10),(1,31)]:
        pre=f'MPRE{k}';rect=f'MRECT{k}';cap=f'CF{k}';pn=f'p{k}'
        s.mos(pre,x,11);s.mos(rect,x+10,11);s.passive(cap,x,5)
        s.wire(pn,s.p(pre,'S'),(x,8),s.p(cap,'1'))
        s.wire(pn,s.p(rect,'S'),(x+10,8),(x,8));s.tag(pn,(x+3,8))
        gx,gy=s.p(rect,'G');s.wire(pn,(gx,gy),(gx-.5,gy),(gx-.5,8))
        if f'MCL{k}' in dev:
            cl=f'MCL{k}';s.mos(cl,x+10,4);s.diode(cl,pn,7);s.wire(pn,s.p(cl,'D'),(x+10,8))
    s.text(1,.4,'厚氧NMOS体端均接AVSS；预充交叉耦合，整流管门极接泵节点。外部1nF与50uA负载在测试台。',7.4)
    return s.finish()

if __name__=='__main__':make_case(15,{1:'HD时钟门控、交叉耦合预充与双相整流'},layout)
