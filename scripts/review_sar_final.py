from review_final_common import *
from module_overviews import overview

def make(bits):
    slot=48 if bits==4 else 42;case=ROOT/f'cases/{slot}-sar-adc{bits}bit'
    r=json.loads((case/'latest_results.json').read_text());v=r['values'];rec=json.loads((case/'conversion_records.json').read_text());sz=json.loads((case/'sizing.json').read_text());sc=json.loads((case/'schematic_audit.json').read_text());audit=json.loads((case/'verification_audit.json').read_text());cf=json.loads((case/'numerical_confirmation.json').read_text());p=Report(case)
    p.page(f'{slot:02d} | {bits}位异步SAR ADC','结论：TT / 1.8V / 27°C，完整原始标称指标通过。')
    p.paragraph(.85,f'100MS/s，两组各{2**bits}个乱序码中心包含采样结束后的诱骗输入。两组均零错误，所有判码电平有效；时钟50Ω源阻抗、10fF/位输出负载保持原题。')
    rows=[]
    for name,key,scale in [('SNDR/dB','dynamic_sndr',1),('归一化ENOB/bit','dynamic_enob',1),('最坏单记录功耗/mW','power',1e3)]:
        q=r['gates'][key];rows.append([name,f"{q['value']*scale:.7g}",*[('>' if key=='dynamic_enob' or key=='dynamic_sndr' and bits==4 else '<' if key=='power' and bits==6 else '≥' if q['sense']=='min' else '≤')+f"{q['limits'][tier]*scale:.6g}" for tier in ['original','10pct','15pct']]])
    p.table([.07,.435,.86,.20],['指标','实测','原指标','10%','15%'],rows,[.30,.19,.17,.17,.17],8.6)
    extra=(f"第二频率/相位动态记录的SNDR={v['dynamic_alt_spectrum']['sndr_dB']:.6f}dB，ENOB={v['dynamic_alt_spectrum']['normalized_enob_bits']:.6f}bit。原SS/FF不在本次nominal范围。" if bits==4 else '动态64码由四个独立16码分段按原顺序组装；四段分别使用原相位延续。静态两种64码次序也各分四段，保留前一码的输入历史。')
    p.paragraph(.365,extra)
    p.paragraph(.195,f'归一化ENOB是原验收公式的确定性码序指标：以理想满量程谱功率除以实测非基波功率换算。有限相干码序可以得到大于{bits}的值；这不代表ADC产生超过{bits}位的信息，也不证明含热噪声、失配后的有效分辨率。')

    p.page('gm/ID初算、采样与异步控制','原生模拟MOS与正值理想电容；全部数字单元保持原厂HD尺寸。')
    roles=list(sz['roles'].items())
    p.table([.07,.465,.86,.38],['角色','模型','单位W/L um','gm/ID','初算Id/uA'],[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",q['gmid'],f"{q['Id_A']*1e6:g}"] for k,q in roles],[.25,.13,.25,.16,.21],8)
    par=sz['parameters'];p.paragraph(.40,f"实际比较器宽度为表中初算的{par['cmp_scale']:g}倍；CDAC单位电容{par['unit_fF']:g}fF，二进制权重扩展，顶板dummy为{par['dummy_fF']:g}fF。异步返回路径电容{par['delay_fF']:g}fF。gm/ID用于初始选型，动态再生过程的瞬时gm/ID不恒定。")
    p.paragraph(.23,('四位差分输入用互补传输门采样。VALID推进判决链，每位控制两侧CDAC，EOC把整字码锁到输出；与当前转换重叠的下一次采样不会提前覆盖正式输出。' if bits==4 else '六位采样采用1.5pF自举存储及原生保护管；比较器缩小至初算宽度的1/4以减轻回踢。VALID使用OR2HDV4，序列链使用DRNQHDV2，判决和输出仍用原厂DRNQ/DQ单元。未作寿命或跨PVT应力签核。'))

    fig=p.page('双次序保持检查与动态频谱','来自最终Spectre精算；频谱从-80dBc基线向上画。')
    axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.13,wspace=.38,hspace=.42)
    for ax,kind in zip(axs[0],['transfer','transfer_alt']):
        seq=[rec[k] for k in r['groups'] if (k if bits==4 else k[:-1])==kind];codes=sum([x['codes'] for x in seq],[]);expected=sum([x['expected'] for x in seq],[])
        ax.plot(expected,'-',color='#becad1',label='Expected');ax.plot(codes,'o',ms=2.8,label='Measured');ax.set(xlabel='Conversion index',ylabel='Code',title=kind);ax.legend(fontsize=7)
    q=rec['dynamic_spectrum'];codes=q['codes'];N=len(codes);tone=v['dynamic_spectrum']['tone_bin'];power=np.array(q['spectrum_power']);axs[1,0].step(range(N),codes,where='mid');axs[1,0].set(xlabel='Dynamic sample index',ylabel='Code')
    db=10*np.log10(np.maximum(power[1:]/power[tone],1e-20));axs[1,1].stem(np.arange(1,N//2+1)*100/N,np.maximum(db,-80),bottom=-80,basefmt=' ');axs[1,1].set(xlabel='Frequency (MHz)',ylabel='Spectrum (dBc)',ylim=(-80,5));clean_axes(axs)
    p.chart(f'两种完整{2**bits}码次序、动态码序与单边频谱。低于-80dBc的谱线仅在显示时截底；评分使用未经截断的原始功率。')
    p.paragraph(.075,'Nyquist点按原评分计半权功率；图中展示其原单边DFT幅值，未用于改变验收结果。',8.3)

    p.page('固定刺激、读出与能量口径','原始时钟、码次序、诱骗输入和功率窗口均保留。')
    p.paragraph(.85,'采样时钟周期10ns、延时1ps、上升/下降20ps、高电平宽1.98ns。输入共模0.9V，动态每侧峰值0.85V；VREFP=1.8V、VREFN=0V。采样后2.20–2.25ns把输入换成错误码中心，验证实际保持。')
    p.paragraph(.66,('四位静态从34.5ns起读16码，动态从44.5ns起读32码，每10ns一次；这是原题输出寄存器的一次转换延迟口径。两组动态分别为bin15/phase0和bin13/phase17°；功率窗口39.5–359.5ns。' if bits==4 else '六位每段静态从19ns起读16码，动态从29ns起读16码，每10ns一次。四段动态构成bin31的64点码序；每段功率窗口19.5–179.5ns。原评分取四段功率均值，本次额外要求最坏单段也小于3mW。'))
    p.paragraph(.46,'能量由VDD、VREFP、VCM、VINP、VINN及VCLKS六个源的有符号电压×电流相加，再截取原窗口作时间加权积分。包括理想输入源与时钟净供能；回收能量按原题有符号口径保留。没有仅统计核心VDD来压低功耗。')
    p.paragraph(.25,'矩形窗去DC，取第1至N/2-1点中除基波以外全部功率，并加Nyquist点的一半；未排除谐波或邻频点。P_FS=(N×2^bits/4)²，归一化ENOB=[10log10(P_FS/P_noise)-1.76]/6.02。')
    p.paragraph(.09,'输出低电平≤0.36V、高电平≥1.44V，完整码序与数字电平检查不可随10%/15%档放宽。',8.9)

    p.page('数值确认、独立审查与可复现材料','全部报告文本和表格保留Markdown；网表、HD源块和模型/LUT哈希归档。')
    powerdiff=max(x['absolute_difference'] for x in cf['metrics'] if x['metric'].endswith('power_W'))
    p.paragraph(.85,f"maxstep50→25ps，全局reltol1e-5→1e-6；conservative瞬态实际相对容差为1e-6→1e-7。{len(cf['metrics'])}项预先设定的差异检查均通过，所有转换码逐点一致，最大功率差{powerdiff*1e6:.6g}uW<5uW。")
    p.paragraph(.65,f"独立复核对原始波形另作逐点插值，调用未改动的原解码器、递归FFT和4项电气检查，共{len(audit['measurement_cross_checks'])}项数值交叉核对通过。{len(audit['run_provenance'])}次基线/精算均实际0错误；警告原样保留，不把Bridge日志分类误当作实际仿真错误。")
    p.paragraph(.45,f"完整图纸{sc['sheets']}页，覆盖{sc['total_instances']}个定义实例、{sc['total_terminals']}个端子和{sc['expanded_leaf_instances']}个展开叶实例。比较器、采样器、CDAC与异步控制器全部有定义图；HD单元保持厂商边界和实际井端。")
    p.paragraph(.25,f'复现入口：case{slot:02d}_sar_adc{bits}bit.py → confirm{slot:02d}.py → schematic{slot:02d}.py → audit{slot:02d}.py → review{slot:02d}.py。保留原source、完整码流、采样电平、FFT功率、数值计划、原始运行快照、PDF及可编辑review_report.md。完整电路图附后。')
    p.paragraph(.10,'未执行器件噪声、失配、参考阻抗、亚稳态统计、PEX或可靠性寿命分析；电路SHA-256：\n'+r['circuit_sha256'],8.1)
    p.netlist((case/'circuit.scs').read_text(),wrap_long_lines=bits==6);p.finish()
    (case/'knowledge.md').write_text(f'''# {slot:02d} · {bits}位异步SAR ADC

{overview(slot)}

## 结果与范围

TT/1.8V/27°C、100MS/s，全部原始标称指标通过。两种完整{2**bits}码次序及采样后诱骗输入检查零错误；SNDR={v['dynamic_spectrum']['sndr_dB']:.9g}dB，归一化ENOB={v['dynamic_spectrum']['normalized_enob_bits']:.9g}bit，最坏单记录六源净供电功率={r['gates']['power']['value']*1e3:.9g}mW。

归一化ENOB是有限相干码序按原公式换算的确定性指标，超过标称位数不代表额外信息位或含噪声的实际精度。{'仅保留原TT两种动态频率/相位，未执行SS/FF。' if bits==4 else '原四分段均值功率与额外最坏分段上限均通过。'} 未作噪声、失配、PEX、亚稳态统计或可靠性签核。

## 结构与验证

gm/ID初算原生采样、动态比较器与CDAC开关；二进制电容、{par['dummy_fF']:g}fF顶板dummy、{par['delay_fF']:g}fF异步返回延迟。数字逻辑全部使用未改尺寸的原厂HD单元。{'1.5pF自举采样与缩小比较器减少回踢；保护拓扑不等于可靠性已签核。' if bits==6 else '互补传输门采样，VALID推进逐位判决，EOC寄存完整输出码。'}

50Ω时钟、10fF/位负载、原采样时刻和能量窗口不变；六个独立源均计入功耗。50→25ps、全局reltol1e-5→1e-6精算全部码一致。原解码器、递归FFT和四项电气检查独立复核通过，完整图纸{sc['sheets']}页。

## 证据

[可编辑报告](review_report.md)、[独立测量](measurement-review.md)、[码流与谱功率](conversion_records.json)、[数值确认](numerical_confirmation.json)、[完整图纸](schematic/sheets.pdf)、[生成脚本](implementation/)均保留。PDF由Matplotlib生成，Markdown不是其编译输入。

电路SHA-256：`{r['circuit_sha256']}`。
''')
