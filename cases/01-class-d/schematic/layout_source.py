"""All Class-D power devices, control cells and local driver definitions."""
from schematic_common import *

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        ps=[n for n,d in dev.items() if d['model']=='p18'];ns=[n for n,d in dev.items() if d['model']=='n18']
        for names,y in [(ps,19),(ns,7)]:
            for k,name in enumerate(names):
                x=22+(k-(len(names)-1)/2)*10;s.mos(name,x,y)
                s.wire('sw',s.p(name,'D'),(x,13))
        s.wire('sw',(7,13),(37,13));s.tag('sw',(22,13))
        s.text(2,1,'每个功率管：单位W/L=50/0.18um，AD=AS=15um²，PD=PS=100.6um。',8)
        s.text(2,.1,'分组保持总宽度与真实寄生电阻；这是假定扩散几何，尚未布局或PEX。',8)
    elif i==2:
        names=['XINV','XHP','XBP','XDP','XLN','XBN','XDN']
        for k,name in enumerate(names):s.cell(name,5+(k%4)*11,19-(k//4)*12)
        s.wire('poff',s.p('XHP','ZN'),s.p('XBP','I'));s.tag('poff',(21.5,19))
        s.wire('noff',s.p('XLN','ZN'),s.p('XBN','I'));s.tag('noff',(10.5,7))
        s.text(1,.3,'交叉反馈：noffd→XHP，poffd→XLN；driver_p同相，driver_n反相。子电路在后页完全展开。',7.5)
    elif i==3:
        for k,x in enumerate([4,14,24,34]):
            name=f'XD{k}';s.cell(name,x,17);s.passive(f'CD{k}',x+3.2,7)
            out='O' if k==3 else f'd{k+1}'
            s.wire(out,s.p(name,'ZN'),(x+3.2,17),(x+3.2,7.82));s.tag(out,(x+3.2,12))
            if k:
                prior=f'd{k}';s.wire(prior,s.p(f'XD{k-1}','ZN'),s.p(name,'I'));s.tag(prior,(x-6,17))
        s.text(1,1,'四级反相链整体同相；每级输出接原厂MIM至vss，名义0.1pF。顶层调用两次。',8)
    elif i==4:
        for k,name in enumerate(dev):s.cell(name,7+(k%4)*10,21-(k//4)*8)
        s.text(1,.2,'driver_p四级反相：INHDV4→INHDV32→2×bank4→8×bank4，总体同相。',7.6)
    elif i==5:
        for k,name in enumerate(dev):s.cell(name,7+(k%3)*15,19-(k//3)*12)
        s.text(1,1,'driver_n三级反相：INHDV8→bank4→4×bank4，总体反相。noff低时gn高。',8)
    elif i==6:
        for k,name in enumerate(dev):s.cell(name,6+k*10.5,14)
        s.text(1,4,'bank4定义：四个未改尺寸的INHDV32同输入、同输出并联。每个单元供电和井端独立标明。',8)
        s.text(1,2,'INHDV32内部PMOS W28.16/L0.18um，NMOS W18.72/L0.18um；源CDL与哈希另附。',8)
    return s.finish()

if __name__=='__main__':
    make_case(1,{1:'上、下功率管与实际体端',2:'HD非交叠控制与栅极驱动连接',3:'delay4：HD延迟链与工艺MIM',4:'driver_p：四级PMOS栅极驱动',5:'driver_n：三级NMOS栅极驱动',6:'bank4：四个原厂HD单元并联'},layout,blocks={1:'half_bridge',2:'half_bridge',3:'delay4',4:'driver_p',5:'driver_n',6:'bank4'})
