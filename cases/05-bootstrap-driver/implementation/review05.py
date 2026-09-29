from review_final_common import *
from module_overviews import overview
CASE=ROOT/'cases/05-bootstrap-driver'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];sz=json.loads((CASE/'sizing.json').read_text());cf=json.loads((CASE/'numerical_confirmation.json').read_text());audit=json.loads((CASE/'verification_audit.json').read_text());sc=json.loads((CASE/'schematic_audit.json').read_text());p=Report(CASE)
    assert r['status']=='complete_10pct';low=lambda key:min(x[key] for x in v.values());high=lambda key:max(x[key] for x in v.values())
    p.page('05 | 全NMOS半桥自举驱动','结论：TT / 1.8V / 27°C，20/50/80ns三种脉宽达到预定10%档。')
    p.paragraph(.85,'平均高侧VGS低于原1.65V下限，80ns输入组的HL死区略小于原3ns，均满足10%档。峰值、电流、非交叠、原生3.3V器件节点筛查及面积上限不放宽。')
    rows=[['平均VGS/V',f"{low('VGS_avg_V'):.6f}–{high('VGS_avg_V'):.6f}",'1.65–1.85','1.485–2.035','1.4025–2.1275'],['死区/ns',f"{min(low('dead_HL_s'),low('dead_LH_s'))*1e9:.6f}–{max(high('dead_HL_s'),high('dead_LH_s'))*1e9:.6f}",'3–7','2.7–7.7','2.55–8.05'],['最大功耗/mW',f"{high('power_W')*1e3:.6f}",'<3.5','<3.85','<4.025'],['高侧VGS峰值/V',f"{high('VGS_peak_V'):.6f}",'<2.15','同左','同左'],['高侧电流峰值/A',f"{high('HS_peak_A'):.6f}",'<0.8','同左','同左'],['VBST−VLX峰值/V',f"{high('VBST_cap_peak_V'):.6f}",'<2.15','同左','同左'],['低侧栅峰值/V',f"{high('GN2_peak_V'):.6f}",'<2.15','同左','同左'],['VBST对地峰值/V',f"{high('VBST_peak_V'):.6f}",'原<5.65；本次<3.63','同左','同左']]
    p.table([.055,.23,.89,.40],['指标','实测三组范围/最坏','原指标','10%','15%'],rows,[.25,.25,.22,.14,.14],7.9)
    p.paragraph(.16,f"DUT展开WLm面积{r['area_um2']:.6f}um²≤35000um²，外接自举电容200pF≤100nF。额外3.63V绝对节点筛查保留，并非完整器件端电压或寿命签核。",8.7)

    p.page('gm/ID初算、存储面积与实际器件','数字单元保持原厂HD；模拟MOS/MIM使用原生SMIC18模型。')
    roles=[(k,q) for k,q in sz['roles'].items() if k!='mirror_n']
    p.table([.07,.57,.86,.27],['角色','模型','初算总W/L um','gm/ID','初算Id/uA'],[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",q['gmid'],f"{q['Id_A']*1e6:g}"] for k,q in roles],[.23,.12,.27,.15,.23],8.1)
    p.paragraph(.51,'实际补电PMOS为初算0.1倍，NMOS跟随为0.4倍，底板复位为0.07倍；新增PMOS跟随支路为强PMOS初算2倍。每指宽度不超过90um，通过m实现总宽。gm/ID仅作初始电流密度选择，不代表动态工作点恒定。')
    p.paragraph(.34,'片上自举存储为30×30um原生MIM及80×9.6um、m=34的n18 MOS电容。MOS电容D/S/B接VLX、G接VBST，保留原生C-V非线性；此处按面积和储能需求选几何，不作放大器gm/ID解释。')
    p.paragraph(.18,'两条八级HD延时链各级MIM几何10×11um。主驱动四级并联数1/1/2/8，完整原厂INHDV16/32；补电与复位小缓冲使用INHDV1/4/16/32。独立面积展开计入所有重复层次、HD内部MOS、MOS电容及MIM，排除题目固定的外接功率管。')

    fig=p.page('三种脉宽的实际换向波形','最终精算0.60–0.70us；分别显示高侧VGS、低侧栅极与开关节点。')
    axs=fig.subplots(3,1);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.13,hspace=.48)
    for ax,(label,path) in zip(axs,r['groups'].items()):
        d=data(ROOT/path,'tran.tran');t=d['time'];mask=(t>=.6e-6)&(t<=.7e-6);x=(t[mask]-.6e-6)*1e9
        ax.plot(x,(d['hi_g']-d['vsw'])[mask],label='High-side VGS');ax.plot(x,d['lo_g'][mask],label='Low-side gate');ax.plot(x,d['vsw'][mask],'--',label='Switch node');ax.axhline(.9,color='#999999',lw=.6);ax.set(xlabel='Time within cycle (ns)',ylabel='Voltage (V)',title=label,ylim=(-.1,2));ax.legend(fontsize=6.8,loc='upper right')
    clean_axes(axs);p.chart('三种输入脉宽的换向波形。输入高电平对应低侧命令，所以20ns输入组的高侧导通时间较长；波形没有更改原控制极性。')
    p.paragraph(.075,'原死区判定取固定窗口内第2次下降与第2次上升跨越0.9V；同时确认每侧各5次升/降沿且全部非交叠。',8.2)

    p.page('补电互锁、跟随支路与固定夹具','保留原负载、外部功率管、封装与两条自举连线寄生。')
    p.paragraph(.85,'交叉反馈延时链产生非交叠命令。浮动高侧缓冲由VBST/VLX供电；补电PMOS经独立高压电平转换与浮动HD缓冲驱动，只在低侧命令有效时补电。底板复位也由该命令控制，替换原电平下降反馈路径。')
    p.paragraph(.66,'新增p33跟随管D接VSW、G接VSS、S/B接VLX，在高共模阶段帮助VLX跟随开关节点，降低两条2nH连线造成的共模过冲；它不改变外部寄生参数。MOS电容抑制自举两端的差模振铃。')
    p.paragraph(.46,'输入周期100ns、边沿3ns、源电阻50Ω、脉宽20/50/80ns。两只外部功率NMOS均W=50um、m=450，迁移为原生n18最小L=0.18um；高侧体端保留连接外接自举电容底端，低侧体接0，负载3.6Ω。')
    p.paragraph(.26,'DUT正/负供电各0.3nH+3mΩ；外接200pF自举电容每根连线各2nH+5mΩ。原功耗=|1.8×平均I(VDDDUT)|，窗口0.5–1us，包含自举补电；外部功率级VHS支路另测，不计入DUT功耗。')
    p.paragraph(.10,'VGS平均值按VSW>0.9V的时间掩码积分；所有峰值也在原0.5–1us窗口读取。原TT中的80/125°C及FS/SF不在本次nominal范围。',8.7)

    p.page('数值确认、独立检查与限制','未改模型；保留原始MD、生成脚本与每次Spectre运行快照。')
    p.paragraph(.85,f"maxstep100→50ps，全局reltol1e-5→1e-6，conservative实际相对容差1e-6→1e-7；保留traponly。{len(cf['metrics'])}项预声明误差界限全部通过，三种脉宽均维持10%档。原日志中的trapezoidal-ringing notices保留，峰值和时序的精算差异按计划逐项约束。")
    p.table([.07,.47,.86,.25],['输入脉宽','平均VGS/V','DUT功耗/mW','HL/ns','LH/ns'],[[label,f"{q['VGS_avg_V']:.7f}",f"{q['power_W']*1e3:.7f}",f"{q['dead_HL_s']*1e9:.7f}",f"{q['dead_LH_s']*1e9:.7f}"] for label,q in v.items()],[.20,.20,.20,.20,.20],8.6)
    p.paragraph(.41,f"独立积分、峰值搜索、第2下降/第2上升边沿及WLm层次展开共{len(audit['measurement_cross_checks'])}项交叉核对通过。原8项电气界限中{sum(x['passed'] for x in audit['original_nominal_checks'])}项通过；平均VGS下限及最短死区的原指标失败如实保留。")
    p.paragraph(.23,f"完整电路图{sc['sheets']}页，{sc['total_instances']}个定义实例、{sc['total_terminals']}个端子。复现入口：case05_bootstrap_driver.py → confirm05.py → schematic05.py → audit05.py → review05.py。静态图纸连接审查不等同于版图LVS或隔离阱验证。")
    p.paragraph(.10,'没有进行全端子应力、可靠性寿命、PVT、失配或PEX签核。电路SHA-256：\n'+r['circuit_sha256'],8.1)
    p.netlist((CASE/'circuit.scs').read_text(),wrap_long_lines=True);p.finish()
    (CASE/'knowledge.md').write_text(f'''# 05 · 全NMOS半桥自举驱动

{overview(5)}

## 结果与范围

TT/1.8V/27°C，原20/50/80ns输入脉宽全部达到10%档，原指标未通过。平均高侧VGS范围{low('VGS_avg_V'):.9g}–{high('VGS_avg_V'):.9g}V；死区范围{min(low('dead_HL_s'),low('dead_LH_s'))*1e9:.9g}–{max(high('dead_HL_s'),high('dead_LH_s'))*1e9:.9g}ns；最坏DUT功耗{high('power_W')*1e3:.9g}mW。平均VGS低于原1.65V，最短死区略低于原3ns。

峰值限制未放宽：高侧VGS {high('VGS_peak_V'):.9g}V、自举两端{high('VBST_cap_peak_V'):.9g}V、低侧栅{high('GN2_peak_V'):.9g}V均<2.15V；高侧电流{high('HS_peak_A'):.9g}A<0.8A。VBST对地{high('VBST_peak_V'):.9g}V，满足额外3.63V节点筛查；它不是全端子应力或寿命签核。展开WLm面积{r['area_um2']:.9g}um²≤35000，外接自举200pF≤100nF。

## 实现与核验

原生gm/ID初算3.3V电平转换/补电与1.8V底板复位；原厂HD非交叠及四级驱动。补电与底板复位由低侧命令互锁，增加浮动充电缓冲与p33跟随支路。原生MIM加80×9.6um、m34的MOS电容储能，PDK模型和外部功率管/负载/寄生保持冻结。

100→50ps与全局reltol1e-5→1e-6确认36项数值差异通过；独立37项测量/面积核对通过，原8项电气界限中的失败项保留。五周期窗口每侧各5次升/降沿，全部非交叠。只完成三种脉宽nominal，未做其他温度、FS/SF、失配、PEX或可靠性。

[可编辑报告](review_report.md)、[独立复核](measurement-review.md)、[边沿记录](switching_records.json)、[面积展开](area_audit.json)、[数值确认](numerical_confirmation.json)、[完整图纸](schematic/sheets.pdf)、[生成脚本](implementation/)均保留。PDF由Matplotlib生成，MD不是其编译输入。

电路SHA-256：`{r['circuit_sha256']}`。
''')

if __name__=='__main__':main()
