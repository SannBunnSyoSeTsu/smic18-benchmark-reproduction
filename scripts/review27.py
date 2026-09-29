from review_final_common import *
from module_overviews import overview
CASE=ROOT/'cases/27-flash-adc4bit'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];z=json.loads((CASE/'sizing.json').read_text());a=json.loads((CASE/'verification_audit.json').read_text());sc=json.loads((CASE/'schematic_audit.json').read_text());rec=json.loads((CASE/'conversion_records.json').read_text());cf=json.loads((CASE/'numerical_confirmation.json').read_text());p=Report(CASE)
    p.page('27 | 4位差分Flash ADC审查','结论：SMIC18MMRF / TT / 1.8V / 27°C，全部原始标称电气指标通过。')
    p.paragraph(.85,'50MS/s、四位差分输入，正式验收包含完整16码中心、90点线性度斜坡和32点动态记录。下表采用最终精算结果。',9.2)
    rows=[]
    for label,key,scale in [('SNDR/dB','sndr_dB',1),('SFDR/dB','sfdr_dB',1),('供电功耗/mW','power',1e3),('INL/LSB','inl_LSB',1),('DNL/LSB','dnl_LSB',1)]:
        q=r['gates'][key];sign='≤' if q['sense']=='max' else '≥';rows.append([label,f"{q['value']*scale:.6g}",*[sign+f"{q['limits'][t]*scale:.6g}" for t in ['original','10pct','15pct']]])
    p.table([.07,.395,.86,.245],['指标','实测','原指标','10%','15%'],rows,[.28,.19,.18,.18,.17],8.5)
    p.paragraph(.33,'16码中心零错误、零缺码；90点斜坡覆盖全部16码、恰好15个相邻上跳，单调性通过。输出在每个评分时刻满足低≤0.36V或高≥1.44V，功能检查不放宽。')
    p.paragraph(.17,'原题仅要求确定性TT标称。无器件噪声、失配或亚稳态统计；本报告的SNDR为原码序的确定性谱指标，不代表实测有效位数或芯片良率。')

    p.page('器件初算与完整结构','共享差分保持、15个StrongARM、15个SR和HD异或编码。')
    p.table([.07,.60,.86,.245],['角色','模型','单元W/L um','gm/ID初算','电流初算/uA'],[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()],[.25,.13,.24,.19,.19],8.1)
    p.paragraph(.54,'模拟比较器的输入对、时钟尾管和交叉再生对由目标工艺gm/ID LUT初算；复位、放电和再生期间的瞬时gm/ID并不恒定。所有数字逻辑使用原厂INHDV1/16、NAND2HDV1、XOR2HDV1，保留原CDL器件与井端。')
    p.paragraph(.37,'差分保持电容每侧20pF；每个比较器输入由两只200kΩ电阻混合保持输入与反向参考阈值。参考梯16×100Ω。采样NMOS和PMOS各拆为四只等效并联，m=4且单管W为表中总宽的1/4，避免超过模型宽度范围。')
    p.paragraph(.20,f"完整图纸为{sc['sheets']}页，覆盖{sc['total_instances']}个定义实例、{sc['total_terminals']}个端子，展开{sc['expanded_leaf_instances']}个叶实例。模拟子电路全展开，HD保持原厂叶单元边界及实际电源/体端；图纸核对不等同于版图LVS。")

    fig=p.page('传输、线性度与频谱','图中样本均来自最终精算的原始Spectre结果。')
    axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.16,wspace=.4,hspace=.43)
    q=rec['transfer'];axs[0,0].plot(range(16),q['codes'],'o-');axs[0,0].set(xlabel='Commanded code',ylabel='Measured code',xticks=[0,4,8,12,15],yticks=[0,4,8,12,15])
    q=rec['linearity'];axs[0,1].step(q['input_diff_V'],q['codes'],where='mid');axs[0,1].set(xlabel='Differential input at readout (V)',ylabel='Ramp code')
    q=rec['dynamic'];axs[1,0].step(np.arange(32),q['codes'],where='mid');axs[1,0].set(xlabel='Sample index',ylabel='Dynamic code')
    power=np.array(q['spectrum_power']);axs[1,1].stem(np.arange(1,16)*50/32,10*np.log10(np.maximum(power[1:16]/power[5],1e-9)),bottom=-65,basefmt=' ');axs[1,1].set(xlabel='Frequency (MHz)',ylabel='Spectrum (dBc)',ylim=(-65,5));clean_axes(axs)
    p.chart('完整16码中心、90点静态斜坡、32码动态记录和原评分频谱。')
    p.paragraph(.105,'动态信号7.8125MHz，差分峰值1.7V，共模0.9V。图中INL/DNL来自离散斜坡阈值，精度受其采样网格限制。',9)

    p.page('固定条件与测量口径','50MS/s；clock=0采样、上升沿结束采样、clock=1转换。')
    p.paragraph(.85,'外部时钟20ns周期，1ps延时，20ps升降沿、9.96ns高电平宽度，经50Ω源阻抗驱动；四位输出各10fF。全部判码在转换边沿后9ns，门限0.9V。DUT内部只使用原生MOS、理想正值R/C与原厂HD单元。')
    p.paragraph(.675,'传输测试在69ns起连续16点判码；静态差分斜坡−1.7→+1.7V历时1.8us，在9ns起每20ns读取90点。每个阈值取发生相邻上跳的两次输入读数中点，首末阈值拟合端点LSB，之后计算INL和相邻间距DNL。')
    p.paragraph(.49,'动态测试从69ns读取32点，矩形窗、去DC、基波为第5频点。SNDR分母为第1–15点中除基波外的全部功率；SFDR为最大非基波功率。原题不计Nyquist频点，此口径明确保留，未删除其他谐波或邻频点。')
    p.paragraph(.31,f"供电功率为60–720ns时间加权均值 −1.8×[I(VDD)+I(VREFP)]，实测{v['dynamic']['power_W']*1e3:.6f}mW。外部时钟净供能另列{v['dynamic']['clock_power_W']*1e3:.6f}mW；输入理想驱动功耗不在原供电上限内，不能据此声称完整系统功耗。")
    p.paragraph(.135,'使用源任务正式bench及原Python测量函数，未以公开短记录代替正式验收；本次输出电平有效性检查额外保留为非放宽功能约束。')

    p.page('数值确认、独立审计与可编辑材料','PDF正文和Markdown从同一文本/表格/网表保存；图纸附后。')
    maxp=max(x['absolute_difference'] for x in cf['metrics'] if x['metric'].endswith('power_W'))
    p.paragraph(.85,f"maxstep100→50ps，reltol1e−5→1e−6；事先固定的{len(cf['metrics'])}项差异界限全部通过，三组全部转换码一致。最大功率差{maxp*1e6:.6g}uW，小于预定3uW。没有通过放宽原刺激、负载或采样窗来取得结果。")
    nlogs=len(a['run_provenance']);nw=sum(len(x['warnings']) for x in a['run_provenance']);p.paragraph(.67,f"独立审计直接把原始Spectre轨迹交给未修改的原Python分析函数，重算传输、端点线性度、递归DFT和截窗能量；{len(a['measurement_cross_checks'])}项数值交叉核对及原6项电气检查通过。{nlogs}次基线/精算均实际0错误，日志保留{nw}条警告并注明类型；不声称零警告。")
    p.paragraph(.49,'原Sky130网表语法检查器不能解析原生Spectre/HD；本次单独验证所有允许叶模型、完整接口、模型尺寸、HD原CDL哈希及图纸端子覆盖，只将该原生结构合格结果提供给原电气评分函数，未伪称运行原Sky130语法检查器。')
    p.paragraph(.31,'case27_flash_adc.py → confirm27.py → schematic27.py → audit27.py → review27.py。保留source原始资料、全部码流/频谱、数值计划、网表快照、模型和LUT哈希、HD源块、PDF、review_report.md、knowledge.md及生成脚本。更新报告后需要重新实际逐页查看。')
    p.paragraph(.12,'电路SHA-256：\n'+r['circuit_sha256'],8)
    p.netlist((CASE/'circuit.scs').read_text());p.finish()
    (CASE/'knowledge.md').write_text(f'''# 27 · 4位差分Flash ADC

{overview(27)}

## 标称复现结果

50MS/s、TT/1.8V/27°C，全部原始指标通过。16码中心零错误；90点线性度斜坡覆盖全码、15个相邻转换且单调。INL={v['linearity']['inl_LSB']:.9g}LSB，DNL={v['linearity']['dnl_LSB']:.9g}LSB；SNDR={v['dynamic']['sndr_dB']:.9g}dB，SFDR={v['dynamic']['sfdr_dB']:.9g}dB，VDD+VREFP功耗={v['dynamic']['power_W']*1e3:.9g}mW。

## 结构与可迁移经验

共享20pF/侧保持电容、200kΩ混合电阻、16×100Ω参考梯、15个StrongARM和SR，以及原厂HD异或树。比较器按目标工艺gm/ID角色初算；采样PMOS总宽超过模型单管范围时拆成m=4等效并联，维持总宽且消除尺寸越界。异步SR在比较器复位时保存判决。

## 验证与范围

完整原始刺激、50Ω时钟、10fF/位负载和边沿后9ns判码保持。动态矩形FFT保留原题第1–15点口径（Nyquist未计入原题）；供电能量包含VDD和VREFP，时钟另列，理想输入驱动未纳入5mW上限。不是噪声、失配、亚稳态统计、PVT或PEX签核。

maxstep100→50ps、reltol1e−5→1e−6确认全部码序不变；独立原分析函数完成{len(a['measurement_cross_checks'])}项数值交叉核对和6项电气检查。源材料、模型、LUT和HD哈希核对通过，完整图纸{sc['sheets']}页。

## 可编辑报告与证据

[报告Markdown](review_report.md)由与Matplotlib PDF相同的文本和表格保存，并非PDF编译输入；[独立测量说明](measurement-review.md)、[验收合同](contract.json)、[数值确认](numerical_confirmation.json)、[代码/频谱记录](conversion_records.json)、[完整生成脚本](implementation/)均保留。

电路SHA-256：`{r['circuit_sha256']}`。
''')

if __name__=='__main__':make()
