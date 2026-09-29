"""Complete39-instance native RF LNA drawings, no collapsed analog arrays."""
from schematic_common import Sheet,make_case
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,devices):
    s=Sheet(ax,i,devices)
    if i==1:
        mos(s,[('MREF',5,6),('MNSINK',17,6),('MPDIO',17,20),('MPMIR',34,20),('MCTOP',34,13),('MCBOT',34,6)])
        link(s,'MPDIO','D','MNSINK','D');link(s,'MPMIR','D','MCTOP','D');link(s,'MCTOP','S','MCBOT','D')
        bus(s,'vdd',[('MPDIO','S'),('MPMIR','S')],23.5)
        bus(s,'vss',[('MREF','S'),('MNSINK','S'),('MCBOT','S')],2)
        passive(s,[('RBIAS',5,18)])
        s.text(1,24.8,'50uA外部参考；MIN电流目标3mA，偏置复制支路目标0.3mA。',7.4)
    elif i==2:
        mos(s,[('MIN',25,11),('MCAS',25,16)])
        link(s,'MIN','D','MCAS','S')
        passive(s,[('XLG0',3,11,False),('XLG1',10,11,False),('XLG2',17,11,False),('XLD0',25,23),('XLD1',25,20),('XCOUT0',34,18,False),('XCMATCH0',34,11),('XCMATCH1',40,11)])
        link(s,'XLG0','2','XLG1','1');link(s,'XLG1','2','XLG2','1');link(s,'XLG2','2','MIN','G')
        link(s,'XLD0','2','XLD1','1');link(s,'XLD1','2','MCAS','D')
        link(s,'MCAS','D','XCOUT0','1',via=[(25,18)],label=False)
        bus(s,'rfout',[('XCOUT0','2'),('XCMATCH0','1'),('XCMATCH1','1')],15)
        for j in range(6):s.passive(f'XLS{j}',3+7*j,4)
        bus(s,'ns',[(f'XLS{j}','1') for j in range(6)]+[('MIN','S')],7)
        bus(s,'vss',[(f'XLS{j}','2') for j in range(6)],1)
        # Space labels above horizontal coil symbols.
        for label in ax.texts:
            x,y=label.get_position()
            if x in [3,10,17] and abs(y-11.36)<1e-8:label.set_position((x,11.85))
            elif x in [3,10,17] and abs(y-11.82)<1e-8:label.set_position((x,12.4))
            elif x==34 and abs(y-18.36)<1e-8:label.set_position((x,18.9))
            elif x==34 and abs(y-18.82)<1e-8:label.set_position((x,19.45))
        s.text(1,24.8,'每个完整spiral均r=60um/n=3.5；并联/串联实例逐一保留。',7.4)
    else:
        for prefix,count,y in [('XCIN',6,21),('XCBN',6,13),('XCBC',4,5)]:
            for j in range(count):s.passive(prefix+str(j),3+7*j,y)
            for pin,by in [('1',y+2),('2',y-2)]:
                net=devices[prefix+'0']['pins'][pin];bus(s,net,[(prefix+str(j),pin) for j in range(count)],by)
        s.text(1,24.8,'输入耦合5.4pF、iref去耦5.4pF、vcas去耦3.6pF；各单位30×30um。',7.2)
    return finish(s)

if __name__=='__main__':make_case(43,{1:'电流镜与共栅偏置复制',2:'输入、共栅、源退化与输出匹配',3:'输入耦合及两组完整去耦电容'},layout)
