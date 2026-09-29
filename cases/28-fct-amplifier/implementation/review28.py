from review_final_common import *
from module_overviews import overview
CASE=ROOT/'cases/28-fct-amplifier'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];rec=json.loads((CASE/'sample_records.json').read_text());sz=json.loads((CASE/'sizing.json').read_text());cf=json.loads((CASE/'numerical_confirmation.json').read_text());audit=json.loads((CASE/'verification_audit.json').read_text());sc=json.loads((CASE/'schematic_audit.json').read_text());p=Report(CASE)
    assert r['status']=='complete_15pct'
    p.page('28 | 900MS/s FCT余量放大器','结论：TT / 1.8V / 27°C，达到预定15%档；原指标和10%档未通过。')
    p.paragraph(.85,'固定400fF飞跨电容和50fF保持负载，分别完成10mV/bin5、20mV/bin3的32点相干采样。\n两组增益均未达到10%档下限；保持误差超过原1.5%，满足10%/15%档。')
    fields=[('增益 V/V','gain_vv',1,'5.5–6.5','4.95–7.15','4.675–7.475'),('SFDR dB','sfdr_db',1,'≥60','≥59.0849','≥58.5884'),('输出共模 V','cm_mean_v',1,'0.3–1.2','0.27–1.32','0.255–1.38'),('保持变化 %','hold_movement_ratio',100,'≤1.5','≤1.65','≤1.725'),('总功耗 mW','power_w',1e3,'≤5','≤5.5','≤5.75')]
    p.table([.06,.37,.88,.27],['指标','10mV','20mV','原指标','10%','15%'],[[name,*[f'{v[k][key]*scale:.7g}' for k in ('10mv','20mv')],a,b,c] for name,key,scale,a,b,c in fields],[.18,.15,.15,.17,.17,.18],8.1)
    p.paragraph(.29,f"保持输出范围：10mV组{v['10mv']['output_min_v']:.6f}–{v['10mv']['output_max_v']:.6f}V；20mV组{v['20mv']['output_min_v']:.6f}–{v['20mv']['output_max_v']:.6f}V。两组均满足原0.2–1.6V范围。")
    p.paragraph(.15,'验收档位仅按既定指标界限换算；输入、时钟、负载、预热周期、读数时刻和功耗窗口均保留。未执行其他工艺角、噪声、失配或PEX。')

    p.page('gm/ID初算与浮动电荷库','原模拟拓扑保留；数字时钟单元采用未改尺寸的原厂HD。')
    p.table([.07,.51,.86,.32],['角色','模型','单位W/L um','gm/ID','初算Id/uA'],[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",q['gmid'],f"{q['Id_A']*1e6:g}"] for k,q in sz['roles'].items()],[.24,.13,.25,.16,.22],8.5)
    par=sz['parameters'];p.paragraph(.45,f"主输入支路保留原并联比例后乘{par['input_scale']:g}，二极管偏置支路不随之缩放；输出下拉/上拉尺寸分别乘{par['output_n_scale']:g}/{par['output_p_scale']:g}，串联输出使能开关乘{par['output_switch_scale']:g}。完整实例映射保留在sizing.json。")
    p.paragraph(.28,f"两只主储能电容各{par['reservoir_pF']:g}pF，其余电容保持原连接和值。12个DUT时钟缓冲/反相器采用BUFHDV{par['clock_drive']}及INHDV{par['clock_drive']}。器件宽度超过单指范围时只增加并联数；PDK模型未修改。")
    p.paragraph(.11,'gm/ID确定原生器件初始电流密度，开关与浮动电荷转移过程不具有恒定gm/ID。尺寸和储能电容的取舍同时影响增益、共模、功耗及保持前建立误差。',8.8)

    fig=p.page('最终保持样本与双频谱','离散谱线从-100dBc基线向上画；未删谐波或非基波点。')
    axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.13,wspace=.38,hspace=.42)
    for col,kind in enumerate(('10mv','20mv')):
        q=rec[kind];dif=np.array(q['outp'])-np.array(q['outn']);axs[0,col].plot(dif*1e3,'o-',ms=2.6,label='Held @ +0.88ns');axs[0,col].plot(np.array(q['track_diff_V'])*1e3,'--',label='Track @ +0.78ns');axs[0,col].set(xlabel='Sample index',ylabel='Differential output (mV)',title=kind);axs[0,col].legend(fontsize=6.7)
        amp=np.array(q['spectrum']);tone=5 if kind=='10mv' else 3;db=20*np.log10(np.maximum(amp[1:]/amp[tone],1e-20));axs[1,col].stem(np.arange(1,17)*900/32,np.maximum(db,-100),bottom=-100,basefmt=' ');axs[1,col].set(xlabel='Frequency (MHz)',ylabel='Spectrum (dBc)',ylim=(-100,5))
    clean_axes(axs);p.chart('两种输入幅度的保持/提前100ps样本与单边DFT频谱；低于-100dBc只作显示截底，评分使用原始数据。')

    p.page('刺激、夹具与功耗边界','900MHz原始时序，64周期预热后取32个样本。')
    p.paragraph(.85,'输入共模1V，差分峰值10/20mV，分别为32点DFT的第5/3频点；两侧正弦相位±90°。采样相延迟T−0.1ns、宽T−0.8ns；转移相延迟T−0.8ns、宽0.5ns；两者边沿10ps。')
    p.paragraph(.66,'输出跟踪开关延迟T−1.03ns、宽0.72ns、边沿20ps。在第64至95周期的+0.88ns取保持值，+0.78ns取提前值。保持变化=RMS(提前差分−保持差分)/RMS(保持差分)，不是仅观察保持平台是否平坦。')
    p.paragraph(.46,'原夹具飞跨电容400fF、输出保持50fF、输出预充0.9V、输入偏置50uA。\n夹具理想开关Ron=0.1Ω并串1Ω、Roff=1e12Ω、阈值0.9V、迟滞0.5mV。\nSpectre继电器采用1uV转移正则化，两端各100aF；启动预充仅第1ns启用。')
    p.paragraph(.25,'原夹具双反相时钟缓冲固定映射BUFHDV16，在DUT调参前冻结。它保留逻辑极性和刺激，未声称与Sky130延迟完全相同。DUT五端口VDD、VCM、SAM、TRANSFER与IBIAS净供能在64T–96T积分；夹具电源单独记账，按原题排除。')
    p.paragraph(.10,'SFDR以去DC的直接DFT计算，所有非基波点（含Nyquist）参与最大杂散搜索。没有拟合后删点、换窗或改变取样时刻。',8.7)

    p.page('数值确认与独立核验','保留完整原始source、Spectre运行快照、报告Markdown与生成脚本。')
    bs,fs=cf['baseline_settings'],cf['refined_settings']
    p.paragraph(.85,f"maxstep{bs['maxstep_s']*1e12:g}→{fs['maxstep_s']*1e12:g}ps，全局reltol{bs['global_reltol']:g}→{fs['global_reltol']:g}（conservative实际再除10）；vabstol{bs['vabstol_V']:g}→{fs['vabstol_V']:g}V。{len(cf['metrics'])}项差异确认通过，包括SFDR差≤0.5dB；两次均为15%档。")
    p.table([.07,.44,.86,.27],['指标','最大基线/精算差','预声明上限'],[[key,f"{max(x['absolute_difference'] for x in cf['metrics'] if x['metric'].endswith('_'+key)):.7g}",str(limit)] for key,limit in [('gain_vv',.01),('sfdr_db',.5),('hold_movement_ratio',.0002),('power_w',5e-6)]],[.40,.32,.28],8.6)
    original=audit['original_nominal_checks'];p.paragraph(.38,f"独立逐点插值和五端口能量积分后，调用未改动的原analyze()与直接DFT；{len(audit['measurement_cross_checks'])}项交叉核对通过。原题每幅度6项检查共12项中{sum(x['passed'] for x in original)}项通过，增益和保持误差的原指标失败如实保留；预定15%档全部通过。")
    p.paragraph(.23,'早期SFDR差异检查失败，严格容差又触发理想开关处的默认恢复次数上限；最终两项恢复次数上限为10000，绝对容差保持10nV，减半步长并收紧相对容差；1nV试跑在读数窗口前因代价过高停止。原读数时刻强制输出、全部点保留，未改夹具或界限；失败与告警留档。',8.6)
    p.paragraph(.13,f"完整图纸{sc['sheets']}页，{sc['total_instances']}个定义实例、{sc['total_terminals']}个端子。入口：case28_fct_amplifier.py → confirm28.py → schematic28.py → audit28.py → review28.py。PDF及同文MD均保留。",8.3)
    p.paragraph(.07,'电路SHA-256：'+r['circuit_sha256'],8)
    p.netlist((CASE/'circuit.scs').read_text(),lines_per_page=50,wrap_long_lines=True);p.finish()
    (CASE/'knowledge.md').write_text(f'''# 28 · 900MS/s FCT余量放大器

{overview(28)}

## 结果与边界

TT/1.8V/27°C，达到既定15%档，原指标和10%档未通过。10mV/20mV两组增益分别{v['10mv']['gain_vv']:.9g}/{v['20mv']['gain_vv']:.9g}V/V，保持变化{v['10mv']['hold_movement_ratio']*100:.9g}%/{v['20mv']['hold_movement_ratio']*100:.9g}%，SFDR分别{v['10mv']['sfdr_db']:.9g}/{v['20mv']['sfdr_db']:.9g}dB。最坏净供电功耗{max(x['power_w'] for x in v.values())*1e3:.9g}mW。

增益低于原5.5和10%档4.95下限，达到15%档4.675下限；保持变化高于原1.5%，低于10%档1.65%。未更改原400fF飞跨电容、50fF负载、900MHz时序、64周期预热、32点样本或功率窗口。原夹具双反相缓冲固定用BUFHDV16映射，未声称跨工艺延迟完全一致。

## 实现与验证

原生gm/ID初算偏置、输入与开关角色；主输入缩放0.3、输出N/P缩放2.3/1.23、输出使能缩放0.6、主储能4pF。DUT时钟为未改尺寸HDV12。{bs['maxstep_s']*1e12:g}→{fs['maxstep_s']*1e12:g}ps、全局reltol{bs['global_reltol']:g}→{fs['global_reltol']:g}、vabstol{bs['vabstol_V']:g}→{fs['vabstol_V']:g}V确认通过，包括原预定SFDR差≤0.5dB。独立插值、五端口能量积分和原直接DFT/评分函数交叉核对通过，原指标失败项原样记录。

早期SFDR未收敛、严格容差触发理想开关恢复次数上限的失败均留在[numerical_stages](numerical_stages/)。最终增加两项求解恢复次数上限到10000，两次均保持10nV绝对电压容差并减半步长、收紧相对容差；1nV试跑在读数窗口前因求解代价过高停止。强制在原读数时刻输出并保留全部自适应点，没有改变电路、夹具、minstep或验收阈值。浮空节点、LTE临时放宽和恢复告警随原始日志保留。

只完成nominal，未覆盖其余PVT、噪声、失配、PEX。[可编辑报告](review_report.md)、[独立复核](measurement-review.md)、[样本与功率分项](sample_records.json)、[数值确认](numerical_confirmation.json)、[完整图纸](schematic/sheets.pdf)、[实现脚本](implementation/)均保留。

电路SHA-256：`{r['circuit_sha256']}`。
''')

if __name__=='__main__':main()
