from review_final_common import *
from module_overviews import overview
CASE=ROOT/'cases/40-delta-sigma'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];rec=json.loads((CASE/'conversion_records.json').read_text());sz=json.loads((CASE/'sizing.json').read_text());audit=json.loads((CASE/'verification_audit.json').read_text());sc=json.loads((CASE/'schematic_audit.json').read_text());cf=json.loads((CASE/'numerical_confirmation.json').read_text());p=Report(CASE)
    p.page('40 | 一阶开关电容ΔΣ调制器','结论：TT / 1.8V / 27°C，三组原始标称电气指标通过。')
    p.paragraph(.85,'采样10MHz，512点记录，OSR32带内带宽156.25kHz。原两档输入幅度、直流偏置和反极性刺激均保留，积分器和比较器以原生晶体管夹具实现。')
    rows=[]
    for k,title in [('nominal','主记录'),('mid_pos','较小幅度正极性'),('mid_inv','较小幅度反极性')]:rows.append([title,f"{v[k]['sndr32_dB']:.6f}",f"{v[k]['source_mean_power_W']*1e3:.6f}",f"{v[k]['time_weighted_power_W']*1e3:.6f}"])
    p.table([.07,.445,.86,.20],['记录','SNDR32/dB','原算术功耗/mW','时间加权功耗/mW'],rows,[.29,.22,.25,.24],8.2)
    p.paragraph(.385,'三组SNDR均≥40dB，两种功耗口径均≤2mW。原功耗使用非均匀自适应点电流的算术均值，并非能量平均值；报告额外列出真正时间加权的VDD功耗，避免两者混用。')
    p.paragraph(.22,f"三组增益{v['nominal']['gain']:.6f}/{v['mid_pos']['gain']:.6f}/{v['mid_inv']['gain']:.6f}，DC跟踪误差均0.00859375；正反极性幅度比{v['suite']['polarity_amplitude_ratio']:.8f}，相位偏差{v['suite']['polarity_phase_error_deg']:.6g}°。积分状态峰值{max(v[k]['state_peak_V'] for k in rec):.6f}V<2V。")
    p.paragraph(.08,'本次为确定性原理图标称复现。未执行噪声、失配、PVT、PEX或数字抽取滤波器验证。',9)

    p.page('gm/ID初算与夹具边界','DUT为sigma_adc；ds_ota和ds_comparator是明确分离的原生外部夹具。')
    p.table([.07,.405,.86,.44],['角色','模型','初算总W/L um','gm/ID','初算Id/uA'],[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",q['gmid'],f"{q['Id_A']*1e6:g}"] for k,q in sz['roles'].items()],[.26,.12,.24,.17,.21],7.8)
    p.paragraph(.35,'Cs=200fF/侧，Ci=450fF/侧；两路比较判决先经互补保持门存入300fF，再控制一位DAC。DAC、输入采样和积分转移均使用原生互补开关，参考低轨0.5V、高轨1.3V。100GΩ泄放支路保留。')
    p.paragraph(.20,'外部OTA和StrongARM的拓扑、50uA参考电流比例及负载保持，器件尺寸由目标工艺gm/ID明确迁移，随后在DUT调参中固定。原Sky130器件几何并未原样移植；此复现不声称两工艺夹具动态完全相同。')
    p.paragraph(.07,'原生宽MOS分为相同并联指，图上标单位W/L及m；所有终端与井端从最终网表读取。',8.8)

    fig=p.page('一位码流与带内外频谱','对数频率轴观察一阶噪声整形；20dB/dec虚线仅为斜率参照。')
    axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.15,wspace=.40,hspace=.44)
    q=rec['nominal'];c=np.array(q['codes']);t=np.array(q['sample_times_s']);axs[0,0].step((t[:80]-t[0])*1e6,c[:80],where='post');axs[0,0].set(xlabel='Time from FFT record start (us)',ylabel='Signed bit',ylim=(-1.2,1.2))
    power=np.array(q['spectrum_power']);freq=np.arange(1,256)*10e6/512;db=10*np.log10(np.maximum(power[1:256]/power[4],1e-20))
    for ax,mask,scale,xlabel in [(axs[0,1],np.ones(255,dtype=bool),1e-6,'Frequency (MHz)'),(axs[1,0],freq<=200e3,1e-3,'Frequency (kHz)')]:
        ax.vlines(freq[mask]*scale,-100,np.maximum(db[mask],-100),color=BLUE,lw=.8,label='Raw FFT bins')
        ax.set(xscale='log',xlabel=xlabel,ylabel='Power / bin (dBc)',ylim=(-100,5),xlim=(freq[0]*scale*.9,(5e6 if scale==1e-6 else 200e3)*scale))
        rf=np.geomspace(30e3,1e6 if scale==1e-6 else 190e3,80)
        ax.plot(rf*scale,-65+20*np.log10(rf/50e3),'--',color=GREEN,lw=1.3,label='20 dB/dec reference')
        ax.axvline(156.25e3*scale,color=GRAY,ls=':',lw=.8)
        ax.legend(fontsize=6.2,loc='upper right' if scale==1e-6 else 'upper left')
        ticks=[.02,.1,1,5] if scale==1e-6 else [20,50,100,200]
        ax.set_xticks(ticks,labels=[f'{x:g}' for x in ticks])
        ax.grid(which='minor',alpha=.12)
    for k in rec:axs[1,1].plot([8,16,32],[v[k][f'sndr{o}_dB'] for o in [8,16,32]],'o-',label=k)
    axs[1,1].set(xlabel='OSR',ylabel='In-band SNDR (dB)',xticks=[8,16,32]);axs[1,1].legend(fontsize=7);clean_axes(axs)
    p.chart('原始FFT各频点采用对数频率轴，谱线从-100dBc向上画；156.25kHz竖虚线标带宽。20dB/dec参照线使用任意竖直偏移，不是拟合结果；只作显示截底，评分未截断谱功率。')
    p.paragraph(.09,f"N=512，Δf=19.53125kHz。虚线为20dB/dec理论参照，未拟合实测斜率。\n未作随机噪声仿真；SNDR32−SNDR16={v['suite']['osr_improvement_dB']:.4f}dB≥6dB。",8.5)

    p.page('原刺激、采样边界与功率解释','保留三种功能维度；不把终止时间之后的外推点纳入FFT。')
    p.paragraph(.85,'主记录每侧0.24V、bin4/45°、每侧DC±20mV；较小幅度0.22V、bin2/45°与225°，DC同步反号。共模0.9V，输出每侧1pF、输入偏置5MΩ；比较器固定±0.5mV差分偏置保留。')
    p.paragraph(.67,'两相周期100ns、边沿5ns、脉宽34ns，第二相延后50ns；比较时钟首次延后100ns，各时钟均有50Ω源阻抗。全部58us从零状态skipdc启动，原数值cmin=1fF保留。')
    p.paragraph(.49,'原提取器由首末导出时间生成采样点；Spectre恰好导出0和58us时，它可能额外生成58.02us并倒夹到终点。本次合同明确只取20ns至57.92us的580个实际记录内点，再取最后512点，即6.82–57.92us。这个边界修正已明示，不伪称原extract()逐行未改。')
    p.paragraph(.29,'调用未修改的原analyze()，矩形窗去DC。OSR32取第1–8频点，去基波后全部剩余功率进分母；噪声整形比为第9–255点平均功率与带内非基波平均功率之比。未删除谐波或选取更有利的窗口。')
    p.paragraph(.105,'VDD功耗包括OTA、比较器和从VDD取得的50uA参考，积分0–58us包含启动；理想外部时钟、输入和参考电压源能量不在原2mW上限内，因此不等于完整ADC系统功耗。')

    p.page('精度确认、独立审计与完整材料','预定误差界限、失败迭代及全部运行日志保留。')
    p.paragraph(.85,f"maxstep1→0.5ns，全局reltol1e-5→1e-6；conservative瞬态实际reltol1e-6→1e-7。{len(cf['metrics'])}项差异检查全部通过，三组最终码流一致，SNDR完全不变。两种功耗差分别按预定75uW和10uW界限检查，未把自适应点算术均值当能量平均值。")
    p.paragraph(.65,f"独立复核重新提取实际时刻的互补判决，调用原analyze()并应用原main()中的9组不等式；{len(audit['measurement_cross_checks'])}项交叉核对全部通过。基线和精算共{len(audit['run_provenance'])}次Spectre实际0错误，模型、源文件、LUT与运行快照哈希一致。")
    p.paragraph(.45,'保留的早期方案因DAC非线性或比较器复位耦合导致反极性SNDR不足。最终增加互补开关并把判决存储从50fF增至300fF；原刺激、积分时间、固定夹具与输出负载没有随结果调整。')
    p.paragraph(.28,f"完整图纸{sc['sheets']}页，{sc['total_instances']}个定义实例、{sc['total_terminals']}个端子，包含所有外部原生模拟夹具。复现顺序：case40_delta_sigma.py → confirm40.py → schematic40.py → audit40.py → review40.py。PDF文本、表格和网表同时保留review_report.md，图纸附后。")
    p.paragraph(.105,'电路SHA-256：\n'+r['circuit_sha256'],8.2)
    p.netlist((CASE/'circuit.scs').read_text());p.finish()
    (CASE/'knowledge.md').write_text(f'''# 40 · 一阶开关电容ΔΣ调制器

{overview(40)}

## 标称结果

TT/1.8V/27°C、10MHz、N512、OSR32，三组原指标通过。主/较小正/较小反极性SNDR为{v['nominal']['sndr32_dB']:.9g}/{v['mid_pos']['sndr32_dB']:.9g}/{v['mid_inv']['sndr32_dB']:.9g}dB。最坏原算术电流功耗{max(v[k]['source_mean_power_W'] for k in rec)*1e3:.9g}mW，真实时间加权VDD功耗{max(v[k]['time_weighted_power_W'] for k in rec)*1e3:.9g}mW，均低于2mW。

## 结构与边界

Cs200fF、Ci450fF、判决保持300fF，互补开关控制一位DAC及电荷转移。外部OTA与StrongARM夹具以原生gm/ID尺寸明确迁移，随后固定，拓扑与50uA参考比例保留；不声称原Sky130晶体管动态原样一致。

原提取器在Spectre恰好导出0/58us时可能外推58.02us后夹到终点；合同明确只取实际记录内580点20ns..57.92us，再取最后512点6.82..57.92us。原analyze()未改，原9组电气不等式全部复核。原自适应点电流算术均值与物理时间加权能量均明确列出，理想外部时钟/输入/参考能量未计入原上限。

## 验证与证据

频谱横轴采用log频率，保留原512点矩形窗FFT和全部评分频点；图中20dB/dec虚线是任意竖直偏移的一阶NTF低频渐近参照，不是对确定性码流的斜率拟合。分辨率19.53125kHz，未据此宣称随机噪声PSD验证通过。

1→0.5ns、全局reltol1e-5→1e-6，最终码流一致，全部预设精度检查通过。{len(audit['measurement_cross_checks'])}项独立数值复核，完整图纸{sc['sheets']}页。未作PVT、噪声、失配、PEX或数字抽取验证。

[报告Markdown](review_report.md)、[独立测量](measurement-review.md)、[合同](contract.json)、[数值确认](numerical_confirmation.json)、[码流/频谱](conversion_records.json)、[完整生成脚本](implementation/)均保留。PDF由Matplotlib生成，Markdown不是其编译输入。

电路SHA-256：`{r['circuit_sha256']}`。
''')

if __name__=='__main__':make()
