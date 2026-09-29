from schematic_common import *
from schematics_analog import finish
PLAN={}

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    for j,n in enumerate(PLAN[i]):
        x=10+22*(j%2);y=21-9*(j//2)
        if dev[n]['kind']=='MOS':s.mos(n,x,y)
        elif dev[n]['kind'] in ('C','R'):s.passive(n,x,y)
        else:s.cell(n,x,y)
    return finish(s)

def main():
    d=read_case(5);titles={};blocks={};PLAN.clear()
    labels=dict(bootstrap_driver='浮动驱动、互锁补电与跟随支路',lvl3='3.3V器件电平转换器',buffer='主栅极四级HD缓冲',buffers='补电/复位四级HD缓冲',non_overlap='交叉反馈非交叠控制',delay_chain='八级HD/MIM延时链',inv='HD反相器接口',nand='HD与非门接口')
    order=['bootstrap_driver','lvl3','non_overlap','delay_chain','buffer','buffers','inv','nand']
    for name in order:
        names=list(d['subcircuits'][name]['devices'])
        for k in range(0,len(names),6):
            i=len(titles)+1;titles[i]=f'{labels[name]} {k//6+1}/{math.ceil(len(names)/6)}';blocks[i]=name;PLAN[i]=names[k:k+6]
    return make_case(5,titles,layout,blocks)

if __name__=='__main__':main()
