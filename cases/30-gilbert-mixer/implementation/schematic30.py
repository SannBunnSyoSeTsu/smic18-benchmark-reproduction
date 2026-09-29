from schematic_common import *
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        mos(s,[('MREF',6,7),('MTAILP',19,7),('MTAILN',36,7),('MRFP',19,19),('MRFN',36,19)])
        s.passive('CBIAS',12,18);s.passive('RDEG',27,13,vertical=False)
        link(s,'CBIAS','1','MREF','D',via=[(12,21),(2,21),(2,10),(6,10)])
        link(s,'MRFP','S','MTAILP','D');link(s,'MRFN','S','MTAILN','D')
        link(s,'RDEG','1','MTAILP','D',via=[(19,13)]);link(s,'RDEG','2','MTAILN','D',via=[(36,13)])
        bus(s,'vss',[('MREF','S'),('MTAILP','S'),('MTAILN','S'),('CBIAS','2')],2)
    else:
        mos(s,[('MQ1',5,12),('MQ2',16,12),('MQ3',27,12),('MQ4',38,12)])
        s.passive('RLP',10,22);s.passive('RLN',32,22);s.passive('COUTP',10,5);s.passive('COUTN',32,5)
        bus(s,'drfp',[('MQ1','S'),('MQ2','S')],9);bus(s,'drfn',[('MQ3','S'),('MQ4','S')],8)
        bus(s,'ifoutp',[('RLP','2'),('MQ1','D'),('MQ4','D')],19)
        bus(s,'ifoutn',[('RLN','2'),('MQ2','D'),('MQ3','D')],16)
        bus(s,'vdd',[('RLP','1'),('RLN','1')],25)
        bus(s,'vss',[('COUTP','2'),('COUTN','2')],2)
    return finish(s)

if __name__=='__main__':make_case(30,{1:'偏置镜、RF跨导与源极退化',2:'LO四管换向、负载与输出电容'},layout)
