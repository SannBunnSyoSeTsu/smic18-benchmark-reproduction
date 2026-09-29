"""Topology-specific static drawings for the eight mixed/HD report retrofits.

This script reads the frozen DUT and HD declarations.  It does not import any
simulation runner, alter netlists, or estimate electrical results.  Each local
analog subcircuit has its own complete transistor sheet; the common renderer
records both definition coverage and expanded hierarchical connectivity.
"""
from __future__ import annotations
import argparse
import json
from schematic_common import Sheet, make_case, confirm_visual, read_case, GREEN, MUTED, BULK


def note(z, s, x=1.2, y=24.1):
    z.text(x, y, s, 8.0, color=MUTED)


def stage(z, i, x, *, ring14=False):
    """Physical starvers around an unchanged vendor inverter; wells stay global."""
    z.mos(f'MPS{i}', x-.8, 19)
    z.cell(f'XINV{i}', x, 13)
    for label in z.ax.texts:
        if label.get_text().startswith(f'XINV{i}  '):
            label.set_position((x+.75,16.7));label.set_ha('left')
    z.mos(f'MNS{i}', x-.8, 7)
    for pin, mos, terminal in [('VDD', f'MPS{i}', 'D'), ('VSS', f'MNS{i}', 'D')]:
        net=z.devices[mos]['pins'][terminal]
        z.wire(net, z.p(mos,terminal), z.p(f'XINV{i}',pin))
        z.tag(net, (x-.8,17 if pin=='VDD' else 9.4), dy=.1)
    cap=f'CT{i}' if ring14 else f'CS{i}'
    z.passive(cap,x,2.5,vertical=False)


def layout02(ax,index,devices):
    z=Sheet(ax,index,devices);M=z.mos;P=z.passive;C=z.cell;p=z.p;w=z.wire;t=z.tag
    if index==1:
        note(z,'两路参考、级联偏置与原厂 HD 二位译码；sel0…sel3 接下一页开关。')
        M('MICC',4.5,6);M('MPTAT',11.5,6)
        for n,net in [('MICC','icc_ref'),('MPTAT','iptat_ref')]:
            x,_=p(n,'D');z.diode(n,net,9);w(net,p(n,'D'),(x,12));t(net,(x,12))
        P('RTOP',18,19);M('MBC',18,12);P('RBOT',18,5)
        w('vcb',p('RTOP','2'),p('MBC','D'));z.diode('MBC','vcb',15)
        t('vcb',(18,16.5));w('vb',p('MBC','S'),p('RBOT','1'));t('vb',(18,8.2))
        for n,x,y in [('XNB0',28,19),('XNB1',38,19),('XSEL0',28,11),('XSEL1',38,11),('XSEL2',28,3.5),('XSEL3',38,3.5)]:C(n,x,y)
    else:
        note(z,'四条可选加权支路汇入 isum，再由共栅 MCASC 输出；各电流镜源端均接 vss。')
        for i in range(4):
            x=4.6+9.5*i
            M(f'MIC{i}',x,8);M(f'MPT{i}',x,3);M(f'MSW{i}',x+4,15)
            pre=f'pre{i}';w(pre,p(f'MIC{i}','D'),(x,9.7),(x+4.4,9.7),(x+4.4,4.7),(x,4.7),p(f'MPT{i}','D'))
            w(pre,p(f'MSW{i}','S'),(x+4,12),(x+4.4,12),(x+4.4,9.7));t(pre,(x+4.4,10.5))
            w('isum',p(f'MSW{i}','D'),(x+4,19))
        w('isum',(8.6,19),(37.1,19));t('isum',(9.5,19),dy=.35)
        M('MCASC',22.5,22);w('isum',p('MCASC','S'),(22.5,19))
    return z.finish()


def layout14(ax,index,devices):
    z=Sheet(ax,index,devices);p=z.p;w=z.wire;t=z.tag
    note(z,'2 µA 外部参考建立限流偏置；Pi/Qi 是虚拟电源，全部 HD 井端仍接 AVDD/AVSS。')
    z.mos('MNREF',4,4);z.diode('MNREF','IBN2U',6.6);t('IBN2U',(4,6.6),dy=.35)
    z.mos('MPREF',11,19);z.mos('MNBP',11,5)
    w('VBP',p('MPREF','D'),p('MNBP','D'));z.diode('MPREF','VBP',16);t('VBP',(11,11))
    z.cell('XBUF0',4,19);z.cell('XBUF1',4,11)
    for i,x in enumerate([20,29,38],1):stage(z,i,x,ring14=True)
    return z.finish()


def layout20(ax,index,devices):
    z=Sheet(ax,index,devices);p=z.p;w=z.wire;t=z.tag
    if index==1:
        note(z,'第一级：每对互补使能传输门选择相邻输入；tg 的两只模拟 MOS 完整展开在第 3 页。')
        for pair,x in enumerate([6,16,26,36]):
            for k,y in [(2*pair,17),(2*pair+1,6)]:z.cell(f'XSW{k}',x,y)
            net=f'n0_{pair}';xx=x+3.9
            w(net,p(f'XSW{2*pair}','O'),(xx,17),(xx,6),p(f'XSW{2*pair+1}','O'));t(net,(xx,11.5))
    elif index==2:
        note(z,'第二、三级继续二选一形成 VO；底部 HD 反相器产生 SB0/SB1/SB2。')
        for a,b,x,net in [(8,9,7,'n1_0'),(10,11,22,'n1_1'),(12,13,37,'VO')]:
            z.cell(f'XSW{a}',x,19);z.cell(f'XSW{b}',x,11)
            xx=x+4;w(net,p(f'XSW{a}','O'),(xx,19),(xx,11),p(f'XSW{b}','O'));t(net,(xx,15.1))
        for i,x in enumerate([7,22,37]):z.cell(f'XINV{i}',x,3.5)
    else:
        note(z,'可复用 tg 定义：NMOS 与 PMOS 并联在 I/O 之间；EN/ENB 互补，体端独立连接。')
        z.mos('MN',22,17);z.mos('MP',22,7)
        w('I',p('MN','S'),(10,16),(10,8),p('MP','S'));t('I',(10,12),ha='right',dx=-.2,dy=0)
        w('O',p('MN','D'),(22,18.7),(34,18.7),(34,5.3),(22,5.3),p('MP','D'));t('O',(34,12),dy=0)
        z.text(5,3,'层次映射：顶层 XSW0…XSW13 各实例化一次本图，共 28 只模拟 MOS。',8,color=MUTED)
    return z.finish()


def bootstrap(z, *, dual_clock=False):
    """Shared readable arrangement, with the exact per-case instance parameters."""
    p=z.p;w=z.wire;t=z.tag
    if dual_clock:
        z.cell('XCLKN',5,19);z.cell('XCLKP',5,11)
        z.mos('MPRE',13,5);z.mos('MDCHG',5,4)
    else:
        z.cell('XINV',5,19);z.mos('MPRE',5,11);z.mos('MDCHG',5,5)
    for n,x,y in [('MPCHG',13,17),('MGTRK',13,11),('MBPP',27,17),('MLIM',37,17),('MCASC',27,11),('MPVIN',27,5),('MPRGUARD',37,5)]:z.mos(n,x,y)
    z.passive('CBOOT',19,15)
    w('CBT',p('CBOOT','1'),(19,21),(37,21),p('MLIM','S'))
    w('CBT',p('MBPP','S'),(27,21));t('CBT',(22,21),dy=.35)
    yy=7.6 if dual_clock else 8
    w('CBB',p('CBOOT','2'),(19,yy))
    w('CBB',p('MDCHG','D'),(5,yy),(27,yy),p('MPVIN','D'))
    w('CBB',p('MGTRK','S'),(13,yy));t('CBB',(17,yy),dy=-.35)
    w('CG',p('MPCHG','D'),p('MGTRK','D'));t('CG',(13,14.5))
    w('VG',p('MBPP','D'),(27,14),p('MCASC','D'))
    w('VG',(27,14),(37,14),p('MPRGUARD','D'));t('VG',(34,14),dy=.35)


def layout22(ax,index,devices):
    z=Sheet(ax,index,devices)
    if index==1:
        note(z,'差分两路各使用一个完整 boot_cell；输入 VIN 只提供自举跟随电位，VG 为各路栅驱动。')
        z.cell('XBP',13,13);z.cell('XBN',31,13)
        z.wire('clk',z.p('XBP','CLK'),(8,13.5),(8,21),(26,21),(26,13.5),z.p('XBN','CLK'))
        z.tag('clk',(17,21),dy=.35)
        z.text(6,5,'XBP：VIN→vinp，VG→gatep     XBN：VIN→vinn，VG→gaten',9,color=GREEN)
        z.text(6,3.7,'下页完整定义各展开一次：18 MOS + 2 自举电容 + 2 原厂 HD 反相器。',8,color=MUTED)
    else:
        note(z,'自举电容、预充电、跟踪和保护支路全展开；MLIM/MBPP 的体端实际接 CBT。')
        bootstrap(z)
    return z.finish()


def resistor_bank(z,names,columns):
    xs=[4+8*i for i in range(5)] if columns==5 else [3+7*i for i in range(6)]
    for row in range((len(names)+columns-1)//columns):
        group=names[row*columns:(row+1)*columns];y=19-8*row
        for n,x in zip(group,xs):
            z.passive(n,x,y);z.wire('vout',z.p(n,'1'),(x,y+2.1))
            z.text(x+.39,y+.14,'B',5.1,color=BULK)
        if len(group)>1:z.wire('vout',(xs[0],y+2.1),(xs[len(group)-1],y+2.1))
        z.tag('vout',(xs[0],y+2.1),dy=.33)


def layout23(ax,index,devices):
    z=Sheet(ax,index,devices);p=z.p;w=z.wire;t=z.tag
    if index==1:
        note(z,'每位 HD 反相器驱动互补模拟开关；共漏 sw0…sw4 分别接 1/2/4/8/16 条单位电阻。')
        for i,x in enumerate([4,12,20,28,36]):
            z.cell(f'XINV{i}',x,19);z.mos(f'MSP{i}',x,12);z.mos(f'MSN{i}',x,5)
            w(f'nb{i}',p(f'XINV{i}','ZN'),(x+3.1,19));t(f'nb{i}',(x+3.1,19),ha='center',dx=0,dy=-.55)
            w(f'sw{i}',p(f'MSP{i}','D'),p(f'MSN{i}','D'));t(f'sw{i}',(x,8.5))
            w(f'nb{i}',p(f'MSP{i}','G'),(x-2.4,12),(x-2.4,5),p(f'MSN{i}','G'));t(f'nb{i}',(x-2.4,8.5),ha='right',dx=-.12,dy=0)
    elif index==2:
        note(z,'低四位 15 条原厂三端单位电阻：每条独立绘制，1 端共接 vout，B 端均接 vss。')
        resistor_bank(z,[f'RB{i}_{j}' for i in range(4) for j in range(2**i)],5)
    else:
        note(z,'最高位 16 条原厂单位电阻并联接 sw4；RT 提供 vout→vss 的固定终端。')
        resistor_bank(z,[f'RB4_{j}' for j in range(16)]+['RT'],6)
    return z.finish()


def layout24(ax,index,devices):
    z=Sheet(ax,index,devices);p=z.p;w=z.wire;t=z.tag
    if index==1:
        note(z,'VCTRL 经源退化建立 pdio/ndio 偏置；前三级虚拟供电单元，HD 井端保持全局电源。')
        for n,x,y in [('MPDIO',5,19),('MVIN',5,12),('MPSRC',12,19),('MNDIO',12,5)]:z.mos(n,x,y)
        z.passive('RDEG',5,5)
        w('pdio',p('MPDIO','D'),p('MVIN','D'));z.diode('MPDIO','pdio',16);t('pdio',(5,14.5))
        w('ndeg',p('MVIN','S'),p('RDEG','1'));t('ndeg',(5,8.2))
        w('ndio',p('MPSRC','D'),p('MNDIO','D'));z.diode('MNDIO','ndio',8);t('ndio',(12,12))
        for i,x in enumerate([21,29,37],1):stage(z,i,x)
    else:
        note(z,'第四、五级闭合五级环：n5 回接第一级输入；两级原厂 HD 缓冲器输出 vout。')
        stage(z,4,9);stage(z,5,22)
        z.cell('XBUF0',35,18);z.cell('XBUF1',35,8)
        z.text(31,2.5,'n5 → XINV1.I（第 1 页）',8,color=MUTED)
    return z.finish()


def layout31(ax,index,devices):
    z=Sheet(ax,index,devices);p=z.p;w=z.wire;t=z.tag
    if index==1:
        note(z,'HD 延迟链产生 early/late；三路完整 boot_drv 分别驱动输入、共模与顶板短接 MOS。')
        for i,x in enumerate([5,15,25,35]):z.cell(f'XCLK{i}',x,19)
        for i,net in enumerate(['earlyb','early','lateb']):w(net,p(f'XCLK{i}','ZN'),p(f'XCLK{i+1}','I'));t(net,(10+10*i,19),dy=.3)
        z.passive('CDELAY',30,15);w('lateb',p('CDELAY','1'),(30,19))
        for n,x in [('XBP',6),('XBN',21),('XBC',36)]:z.cell(n,x,11)
        for n,x in [('MIP',5),('MCP',15),('MIN',27),('MCN',37)]:z.mos(n,x,4)
        z.mos('MTS',22,2.2);z.passive('CP',10,6.4,vertical=False);z.passive('CN',32,6.4,vertical=False)
        w('vsp',p('MIP','D'),(5,6.4),p('CP','1'));t('vsp',(6.2,6.4),dy=.35)
        w('vtopp',p('CP','2'),(15,6.4),p('MCP','D'))
        w('vtopp',(15,6.4),(22,6.4),p('MTS','D'));t('vtopp',(16,6.4),dy=.35)
        w('vsn',p('MIN','D'),(27,6.4),p('CN','1'));t('vsn',(28,6.4),dy=.35)
        w('vtopn',p('CN','2'),(37,6.4),p('MCN','D'));t('vtopn',(34,6.4),dy=.35)
        w('vtopn',p('MTS','S'),(22,1),(41,1),(41,6.4),(37,6.4))
    else:
        note(z,'boot_drv 完整可复用定义：顶层 XBP/XBN/XBC 各展开一次，所有 MOS 体端均显式标注。')
        bootstrap(z,dual_clock=True)
    return z.finish()


def layout45(ax,index,devices):
    z=Sheet(ax,index,devices);p=z.p;w=z.wire;t=z.tag
    note(z,'原厂上升沿 DFF：D 接 QN 形成二分频；RDN 低有效异步复位，NOR 在 reset=1 时屏蔽输出。')
    z.cell('XR',8,17);z.cell('XFF',23,11);z.cell('XOUT',37,11)
    w('rdn',p('XR','ZN'),(16,17),(16,10),p('XFF','RDN'));t('rdn',(16,15))
    w('qn',p('XFF','QN'),(28,11),(28,19),(18,19),(18,11),p('XFF','D'));t('qn',(23,19),dy=.35)
    w('qn',(28,11),(31,11),(31,11.5),p('XOUT','A1'))
    z.text(6,4.5,'HD 叶单元保持完整原厂定义：INHDV2 + DRNQNHDV1 + NOR2HDV16。',9,color=MUTED)
    z.text(6,3.2,'每个单元的 VDD、VSS、VNW、VPW 都是独立绘出的实际端口；供电/井连接未省略。',8,color=MUTED)
    return z.finish()


CONFIG={
    2:({1:'参考、级联偏置与 HD 译码',2:'四路加权电流镜、选择开关与输出'},layout02,None),
    14:({1:'参考偏置、三级限流环及 HD 输出缓冲'},layout14,None),
    20:({1:'八路选择树：第一级传输门',2:'上层选择与 HD 互补时钟',3:'完整可复用 tg 晶体管电路'},layout20,{1:'input_mux_8to1',2:'input_mux_8to1',3:'tg'}),
    22:({1:'双路自举驱动顶层连接',2:'完整 boot_cell 自举与保护电路'},layout22,{1:'bootstrap_gate_driver',2:'boot_cell'}),
    23:({1:'五位 HD 控制与互补 MOS 开关',2:'低四位全部三端电阻',3:'最高位全部三端电阻与终端'},layout23,None),
    24:({1:'控制偏置与环形级 1–3',2:'环形级 4–5 与 HD 输出缓冲'},layout24,None),
    31:({1:'分相时钟、三路驱动与底板采样',2:'完整可复用 boot_drv 自举电路'},layout31,{1:'bottom_plate_sampler',2:'boot_drv'}),
    45:({1:'原厂 HD 二分频与异步复位'},layout45,None),
}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('slots',nargs='*',type=int,default=list(CONFIG))
    ap.add_argument('--confirm-visual',action='store_true',help='Only after viewing all current sheets and the full overview.')
    args=ap.parse_args()
    for slot in args.slots:
        assert slot in CONFIG,slot
        if args.confirm_visual:a=confirm_visual(slot)
        else:
            titles,layout,blocks=CONFIG[slot];a=make_case(slot,titles,layout,blocks)
        print(json.dumps({'slot':slot,'status':a['status'],'sheets':a['sheets'],'terminals':a['total_terminals'],'definitions':a['total_instances'],'expanded_leaves':a['expanded_leaf_instances']},ensure_ascii=False))


if __name__=='__main__':main()
