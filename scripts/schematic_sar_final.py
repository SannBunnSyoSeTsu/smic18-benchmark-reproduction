"""Complete, netlist-backed SAR hierarchy drawings; no EDA execution."""
from schematic_common import *
from schematics_analog import mos,link,bus,finish
PLAN={}

def layout(ax,i,dev):
    s=Sheet(ax,i,dev);kind,items=PLAN[i]
    if kind=='top':
        for n,x,y in [('XCLKC',9,21),('XCMP',32,21),('XDP',12,8),('XDN',33,8)]:s.cell(n,x,y)
    elif kind=='logic_interface':s.cell('XLOG',22,12.5)
    elif kind=='cmp':
        mos(s,[('MPN',9,21),('MPP',29,21),('MLN',9,14),('MLP',29,14),('MINP',9,8),('MINN',29,8),('MTAIL',19,4)])
        for p,n,inp in [('MPN','MLN','MINP'),('MPP','MLP','MINN')]:link(s,p,'D',n,'D');link(s,n,'S',inp,'D')
        bus(s,'tail',[('MINP','S'),('MINN','S'),('MTAIL','D')],6)
        bus(s,'vdd',[('MPN','S'),('MPP','S')],24)
    elif kind=='cmp_reset':
        mos(s,[(n,7+11*k,19) for k,n in enumerate(['MRST_dx','MRST_dy','MRST_ln','MRST_lp'])])
        s.cell('XON',12,7);s.cell('XOP',32,7)
    elif kind=='cdac_front':
        s.cell('XS',13,14);s.passive('CD',32,14)
        link(s,'XS','vout','CD','1',via=[(24,14),(24,14.82)])
    elif kind=='cdac':
        for k,b in enumerate(items):
            x=10+23*k;s.passive(f'C{b}',x,21);mos(s,[(f'MN{b}',x,8),(f'MP{b}',x,15)])
            # NMOS/PMOS share the bottom plate, but their symbols have
            # opposite D/S orientation; route beside, not through, the PMOS.
            link(s,f'MP{b}','D',f'MN{b}','D')
            link(s,f'C{b}','2',f'MP{b}','D',via=[(x+5,20.18),(x+5,12),(x,12)])
    elif kind=='sample_tg':
        mos(s,[('MSN',12,13),('MSP',31,13)])
        link(s,'MSN','D','MSP','D',via=[(12,20),(39,20),(39,12)])
        link(s,'MSN','S','MSP','S',via=[(12,5),(23,5),(23,14)])
    else:
        for k,n in enumerate(items):
            x=11+(k%2)*21;y=21-(k//2)*9
            d=dev[n]
            if d['kind']=='MOS':s.mos(n,x,y)
            elif d['kind'] in ('C','R'):s.passive(n,x,y)
            else:s.cell(n,x,y)
    return finish(s)

def main(bits):
    slot=48 if bits==4 else 42;d=read_case(slot);titles={};blocks={};PLAN.clear()
    def page(block,title,kind,items=None):
        i=len(titles)+1;titles[i]=title;blocks[i]=block;PLAN[i]=(kind,items)
    page(d['top'],'顶层：差分采样阵列、比较器与采样时钟','top')
    page(d['top'],'顶层：异步控制器完整接口','logic_interface')
    page('sar_cmp','比较器：输入对、尾管与交叉再生','cmp')
    page('sar_cmp','比较器：四节点复位与输出缓冲','cmp_reset')
    page('sar_cdac','CDAC：采样接口与顶板寄生补偿电容','cdac_front')
    for b in range(1,bits,2):page('sar_cdac',f'CDAC：二进制权重支路 {b}–{min(b+1,bits-1)}','cdac',list(range(b,min(b+2,bits))))
    if bits==4:page('sar_sample','互补传输门：差分两侧共用此完整定义','sample_tg')
    else:
        names=list(d['subcircuits']['sar_sample']['devices'])
        for k in range(0,len(names),6):page('sar_sample',f'自举采样开关及保护器件 {k//6+1}/2','grid',names[k:k+6])
    names=list(d['subcircuits']['sar_logic']['devices'])
    for k in range(0,len(names),6):page('sar_logic',f'HD异步序列、判决与EOC寄存器 {k//6+1}/{math.ceil(len(names)/6)}','grid',names[k:k+6])
    return make_case(slot,titles,layout,blocks)
