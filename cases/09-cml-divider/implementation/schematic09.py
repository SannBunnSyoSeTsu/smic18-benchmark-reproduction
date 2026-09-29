"""Both CML latches at transistor level, including the reference diode."""
from schematic_common import *

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    master=i==1
    if master:
        dp,dn,rp,rn,tc,rc,tail='MMDP','MMDN','MMRP','MMRN','MMTC','MMTRC','MMTAIL'
        p,n,dnode,rnode,tnode='mp','mn','nmd','nmr','mtail';rpname,rnname='RMP','RMN'
    else:
        dp,dn,rp,rn,tc,rc,tail='MSDP','MSDN','MSRP','MSRN','MSTC','MSTRC','MSTAIL'
        p,n,dnode,rnode,tnode='outp','outn','nsd','nsr','stail';rpname,rnname='RSP','RSN'
    s.text(1,24,'数据差分对在左，再生差分对在右；两只时钟管分配同一尾电流。'+('主级接收交换极性的输出反馈。' if master else '从级接收mp/mn，使用相反时钟相位。'),7.2)
    for res,x in [(rpname,9),(rnname,20)]:
        s.passive(res,x,21,reverse=True);s.wire('vdd',s.p(res,'2'),(x,23));s.tag('vdd',(x,23))
    for name,x,net,res in [(dp,9,p,rpname),(dn,20,n,rnname)]:
        s.mos(name,x,16);s.wire(net,s.p(name,'D'),s.p(res,'1'));s.tag(net,(x,18.5))
        s.wire(dnode,s.p(name,'S'),(x,13))
    s.wire(dnode,(9,13),(20,13));s.tag(dnode,(14,13))
    for name,x,net in [(rp,31,p),(rn,41,n)]:
        s.mos(name,x,16);s.wire(net,s.p(name,'D'),(x,19));s.tag(net,(x,19));s.wire(rnode,s.p(name,'S'),(x,13))
    s.wire(rnode,(31,13),(41,13));s.tag(rnode,(36,13))
    s.mos(tc,14,9);s.mos(rc,36,9)
    s.wire(dnode,s.p(tc,'D'),(14,13));s.wire(rnode,s.p(rc,'D'),(36,13))
    for name,x in [(tc,14),(rc,36)]:s.wire(tnode,s.p(name,'S'),(x,6))
    s.wire(tnode,(14,6),(36,6));s.tag(tnode,(25,6))
    s.mos(tail,25,3);s.wire(tnode,s.p(tail,'D'),(25,6));s.wire('vss',s.p(tail,'S'),(25,1));s.tag('vss',(25,1))
    if master:
        s.mos('MBIAS',5,4);s.diode('MBIAS','iref',7);s.tag('iref',(5,7));s.wire('vss',s.p('MBIAS','S'),(5,1));s.tag('vss',(5,1))
        s.text(1,10,'外部150uA参考\n由bench的VDD提供。',7.0)
    else:s.text(1,6,'iref偏置二极管见第1页。\n每侧10fF负载在bench中；\n50ohm输入源阻抗也在bench中。',7.1)
    return s.finish()

if __name__=='__main__':make_case(9,{1:'主锁存器与参考偏置',2:'从锁存器与差分输出'},layout)
