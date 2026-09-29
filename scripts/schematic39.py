"""All22MOS and5passives, actual node connections and bodies."""
from schematic_common import Sheet,make_case
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,d):
    s=Sheet(ax,i,d)
    if i==1:
        mos(s,[('MREF',3,5),('MBP',11,20),('MBN',11,5),('MABNS',23,21),('MABNU',23,14),('MABNL',23,6),('MABPL',37,21),('MABPU',37,14),('MABPS',37,6)])
        link(s,'MBP','D','MBN','D');link(s,'MABNS','D','MABNU','D');link(s,'MABNU','S','MABNL','D');link(s,'MABPL','D','MABPU','S');link(s,'MABPU','D','MABPS','D')
        bus(s,'vdd',[('MBP','S'),('MABNS','S'),('MABPL','S')],23.5)
        bus(s,'vss',[('MREF','S'),('MBN','S'),('MABNL','S'),('MABPS','S')],1.5)
    elif i==2:
        mos(s,[('MP3',5,20),('MP5',17,20),('MINP',5,13),('MINN',17,13),('MTAIL',11,5),('MP4',29,20),('MN7',29,8),('MP6',39,20),('MN8',39,8)])
        link(s,'MP3','D','MINP','D');link(s,'MP5','D','MINN','D');link(s,'MP4','D','MN7','D')
        bus(s,'tail',[('MINP','S'),('MINN','S'),('MTAIL','D')],10)
        bus(s,'vdd',[('MP3','S'),('MP5','S'),('MP4','S'),('MP6','S')],23.5)
        bus(s,'vss',[('MTAIL','S'),('MN7','S'),('MN8','S')],1.5)
    else:
        mos(s,[('MCN',7,19),('MCP',18,19),('MOUTP',34,20),('MOUTN',34,9)])
        # Floating pairD/S are cross-connected through explicitly labeled nets.
        link(s,'MCN','D','MCP','S',via=[(7,22),(18,22)])
        link(s,'MCN','S','MCP','D',via=[(7,16),(18,16)])
        passive(s,[('RBAT',12,10,False),('CCP',5,4,False),('RZP',15,4,False),('CCN',27,4,False),('RZN',38,4,False)])
        link(s,'MOUTP','D','MOUTN','D');s.tag('vout',(34,14))
        link(s,'CCP','2','RZP','1');link(s,'CCN','2','RZN','1')
        bus(s,'vdd',[('MOUTP','S')],23.5);bus(s,'vss',[('MOUTN','S')],6.5)
    return finish(s)

if __name__=='__main__':make_case(39,{1:'单参考偏置与互补复制堆叠',2:'输入对、尾电流与电流镜',3:'浮动Class-AB、输出与双路补偿'},layout)
