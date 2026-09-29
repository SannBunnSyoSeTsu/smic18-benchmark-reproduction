from review_final_common import *
from module_overviews import overview
CASE=ROOT/'cases/06-ring-amplifier'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];z=json.loads((CASE/'sizing.json').read_text());a=json.loads((CASE/'verification_audit.json').read_text());sc=json.loads((CASE/'schematic_audit.json').read_text());cf=json.loads((CASE/'numerical_confirmation.json').read_text());p=Report(CASE)
    p.page('06 | 三级环形放大器审查','结论：TT / 1.8V / 27°C，四个输入记录及全部原始标称指标通过。')
    p.paragraph(.85,'标称电源1.8V、外部25uA偏置、每侧10pF负载；评分取第三周期。下表均为最终精算值，功能与数值复核记录随报告保存。',9.2)
    worst=lambda key:max(v[k][key] for k in ['pos20','neg20'])
    rows=[['正区间增益',f"{v['transfer']['positive_gain']:.8g}",'7.2–8.8'],['双极性增益',f"{v['transfer']['bipolar_gain']:.8g}",'7.2–8.8'],['零输入残差/mV',f"{v['transfer']['zero_residual_V']*1e3:.7g}",'≤5'],['最坏静态误差/%',f"{worst('static_error_fraction')*100:.7g}",'≤1'],['最坏共模误差/mV',f"{worst('cm_error_V')*1e3:.7g}",'≤50'],['最坏功耗/uW',f"{worst('power_W')*1e6:.7g}",'≤400'],['最坏建立时间/ns',f"{worst('settle_s')*1e9:.7g}",'≤50'],['最坏纹波/mV',f"{worst('ripple_V')*1e3:.7g}",'≤5']]
    p.table([.07,.27,.86,.38],['指标','精算值','原门槛'],rows,[.47,.28,.25],8.5)
    p.paragraph(.20,'外部25uA偏置电流下，每侧输出固定10pF。输入+20、+10、0、−20mV均单独仿真；增益同时检查正区间斜率与双极性斜率，不能以单个输出幅值替代。')
    p.paragraph(.10,'本次全部原门槛已通过，10%/15%放宽未用于结论。其他PVT、随机失配、器件噪声和PEX未验证。',9)

    p.page('gm/ID角色与自调零结构','电路由输入级、带偏置记忆的第二级和互补输出级构成。')
    p.table([.07,.525,.86,.32],['角色','模型','单元W/L um','gm/ID初算','I初算/uA'],[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:.6g}"] for k,q in z['roles'].items()],[.24,.13,.23,.18,.22],7.8)
    p.paragraph(.465,'gm/ID LUT提供器件角色的起点，各实例的镜像倍率、输出驱动倍率和长度记录于sizing.json。输入及负载采用0.36um，级联电平转换采用0.18um，输出与启动采用1um；第二级正负支路的级联尺寸匹配，避免不必要的静态不对称。')
    p.paragraph(.29,'输入耦合电容800fF，输出反馈电容109.5fF，级间自调零存储100fF，输出共模检测电容每只500fF。有限级增益、输出动态和记忆节点共同影响实际闭环斜率，不能直接把800/109.5当实测增益。')
    p.paragraph(.125,'表中宽度是gm/ID角色单元，并非所有实例最终宽度；例如输出倍率1.2、尾支路倍率0.7。最终几何和体端应以附后完整网表、图纸与instance_roles映射为准。',9)

    fig=p.page('四点传输与双极性建立','所有曲线来自最后一次精算；固定第三周期评分。')
    axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.17,wspace=.4,hspace=.43)
    for name,label in [('pos20','+20mV'),('neg20','-20mV')]:
        d=data(ROOT/r['groups'][name],'tran.tran');t=d['time'];q=(t>=1.04e-6)&(t<=1.18e-6);axs[0,0].plot((t[q]-1.05e-6)*1e9,(d['voutp'][q]-d['voutn'][q])*1e3,label=label)
        q=(t>=1.35e-6)&(t<=1.46e-6);axs[1,0].plot((t[q]-1e-6)*1e9,(d['voutp'][q]+d['voutn'][q])/2,label=label)
    axs[0,0].set(xlabel='Time after input step (ns)',ylabel='Differential output (mV)');axs[0,0].legend(fontsize=7)
    axs[1,0].set(xlabel='Time in third period (ns)',ylabel='Output common mode (V)');axs[1,0].axhline(.9,color='k',ls=':',lw=.7)
    xs=[-.02,0,.01,.02];ys=[v[k]['mean_diff_V'] for k in ['neg20','zero','pos10','pos20']];axs[0,1].plot(np.array(xs)*1e3,np.array(ys)*1e3,'o-',label='measured');axs[0,1].plot(np.array(xs)*1e3,np.array(xs)*8000,ls=':',label='gain 8');axs[0,1].set(xlabel='Input differential (mV)',ylabel='Averaged output (mV)');axs[0,1].legend(fontsize=7)
    d=data(ROOT/r['groups']['zero'],'tran.tran');q=(d['time']>=1e-6);axs[1,1].plot((d['time'][q]-1e-6)*1e9,(d['voutp'][q]-d['voutn'][q])*1e3);axs[1,1].set(xlabel='Time in third period (ns)',ylabel='Zero-input residual (mV)');clean_axes(axs)
    p.chart('双极性建立、完整四点传输、共模恢复与零输入残差。')
    p.paragraph(.10,'建立时间以进入并保持在固定±160mV目标的±10%带内为准；不是以最终实测输出重新定义目标。',9)

    p.page('零状态启动与固定测量','保留原采样复位外部网络；新增启动器件全部属于DUT。')
    p.paragraph(.85,'Spectre沿用skipdc=yes，从零状态起算；保留原1fF数值节点并联电容。输入含1GH直流通路时，零状态下的交流耦合节点不能自动取得足够偏置，初版第一级截止。两只0.5/1um NMOS以ibias为门极，将输入源连接到耦合节点，帮助其充电；输入节点升高后，导通自然减弱。')
    p.paragraph(.655,'上述弱启动是实际晶体管电路，不是初值或隐藏刺激。第二级采用匹配的级联尺寸；输出管倍率1.2，反馈电容109.5fF。在未改变25uA参考、10pF负载和复位周期的条件下完成建立与功耗折中。')
    p.paragraph(.48,'周期500ns，前50ns复位，输入边沿20ps。七只外部复位继电器Ron=100Ω、Roff=1TΩ，控制差分阈值0.25±0.1V，控制负端接0.5V；模型显式hysteresis=0.1V，过渡宽度1uV。第三周期1.05us施加输入，输出均值及纹波窗1.4–1.45us，供电均值窗1.2–1.45us。')
    p.paragraph(.30,'静态误差取两极性相对于±160mV的最大比例误差；共模取两输出均值相对0.9V误差；纹波为窗内相对自身平均差分输出的最大偏差；功耗为|1.8×平均I(VDD)|。外部偏置、时钟与复位源能量未纳入原VDD指标。')
    p.paragraph(.12,'理想R/C/L为原题允许抽象；1GH电感用作直流偏置路径，不能按真实片上电感面积理解。完整电路图为原理图连通性审查，不是物理实现或版图LVS。',9)

    p.page('精度、审计与保留的源文件','数值计划在精算之前固定；独立计算使用原始外部端口轨迹。')
    p.paragraph(.85,f"maxstep0.25→0.125ns，reltol1e−6→1e−7；{len(cf['metrics'])}项差异界限全部通过，结论维持原始指标通过。独立审计以显式边界插值、逐段梯形积分和最后带内交叉重算，{len(a['measurement_cross_checks'])}项数值核对及7组原始门槛均通过。")
    p.paragraph(.67,f"基线与精算共{len(a['run_provenance'])}次仿真实际0错误；所有日志警告保留于审计。模型尺寸合法，源资料、模型与LUT哈希核对一致。完整{sc['sheets']}页图纸覆盖{sc['total_instances']}个定义实例、{sc['total_terminals']}个端子。")
    p.paragraph(.50,'case06_ring_amp.py → confirm06.py → schematic06.py → audit06.py → review06.py。原始源码、网表快照、精算计划、测量说明、PDF、review_report.md和knowledge.md均保存。PDF使用Python/Matplotlib排版，Markdown与同一正文同步保存，便于后续编辑。')
    p.paragraph(.33,'范围仅原理图级TT、1.8V、27°C和原四点功能矩阵。未验证额外PVT、失配、输入噪声、真实电感/电容寄生、长时间偏置漂移及版图。运行和报告重新生成后，需再次逐页实际检查。')
    p.paragraph(.14,'电路SHA-256：\n'+r['circuit_sha256'],8)
    p.netlist((CASE/'circuit.scs').read_text());p.finish()
    (CASE/'knowledge.md').write_text(f'''# 06 · 三级环形放大器

{overview(6)}

## 标称结果

四个输入+20/+10/0/−20mV，固定25uA偏置、10pF/侧负载、500ns周期、50ns复位。原始指标全部通过：正区间增益{v['transfer']['positive_gain']:.9g}，双极性增益{v['transfer']['bipolar_gain']:.9g}，最坏静态误差{worst('static_error_fraction')*100:.8g}%，建立{worst('settle_s')*1e9:.8g}ns，VDD功耗{worst('power_W')*1e6:.8g}uW，零残差{v['transfer']['zero_residual_V']*1e3:.8g}mV。

## 启动与尺寸迁移

保留三级SC/环形路径及全部外部复位端口。交流耦合输入的零状态启动需要实际弱充电支路：两只0.5/1um原生NMOS门极接ibias，其电导随输入节点上升而减弱。没有额外初值、辅助时钟或理想启动源。第二级级联尺寸保持双侧匹配，输出倍率1.2，Cs=800fF、Cf=109.5fF；有限放大增益和动态状态使实际斜率不能只按电容比推算。

## 验证口径和局限

第三周期1.05us阶跃；均值/纹波1.4–1.45us，供电1.2–1.45us；建立目标固定±160mV的±10%带。maxstep0.25→0.125ns、reltol1e−6→1e−7通过预定差异限。独立逐段积分和交叉检测重算{len(a['measurement_cross_checks'])}项标量，检查全部7组原门槛。

复位开关以Spectre模型vth=0.25V、hysteresis=0.1V、trans=1uV实现迟滞；早期仅vt1/vt2的平滑电导翻译已归档并作废，最终全部结果重跑。

保留skipdc零状态及源bench的1fF节点数值并联电容。R/C/L为原题允许的理想抽象，1GH不能理解为可实现的片上电感。仅TT/1.8V/27°C原四点，未覆盖噪声、失配、PVT、PEX或长期偏置漂移。VDD功耗不包含原题排除的外部偏置/复位/时钟源。

## 可编辑资料

[报告Markdown](review_report.md)与Matplotlib PDF使用相同正文保存；[独立测量](measurement-review.md)、[验收合同](contract.json)、[数值确认](numerical_confirmation.json)、[尺寸角色](sizing.json)、[生成脚本](implementation/)保留。全部{sc['sheets']}页完整图纸及端子映射随报告保存。

电路SHA-256：`{r['circuit_sha256']}`。
''')

if __name__=='__main__':make()
