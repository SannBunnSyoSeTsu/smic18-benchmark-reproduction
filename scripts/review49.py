"""Chinese review, knowledge draft and provenance audit for native-passive LC VCO."""
from review_pdf import *
from case49_lc_vco import WINDOWS, CONTROLS, time_mean, point as extract_point
import argparse
import subprocess

CASE=ROOT/'cases/49-lc-vco'
INFO=[('f(0 V)','frequency0_Hz',1e-9,'GHz'),('f(1.8 V)','frequency1p8_Hz',1e-9,'GHz'),
 ('调谐比','tuning_ratio',1,''),('最小频率台阶','step_drop_Hz',1e-6,'MHz'),('最小差分摆幅','swing_min_Vpp',1,'Vpp'),
 ('起振至0.2 V','startup_s',1e9,'ns'),('负轨越界量','output_negative_excursion_V',1,'V'),('输出最大值/VDD','output_high_fraction',1,''),
 ('共模最小值/VDD','commonmode_min_fraction',1,''),('共模最大值/VDD','commonmode_max_fraction',1,''),
 ('IREF最小电压','reference_min_V',1,'V'),('最小参考余量','reference_headroom_V',1,'V'),('平均VDD功耗','power_W',1e3,'mW'),
 ('最大supply pushing','pushing_pct_per_V',1,'%/V')]
ROLE_NAMES={'negative_resistance':'负阻对','bias_unit':'PMOS参考/供流','var_feed':'变容偏置供流','varactor_bias':'NMOS偏置/尾管',
 'reg_input':'调节器输入对','reg_load':'调节器镜负载','reg_pullup':'调节器上拉','reg_pulldown':'调节器下拉'}
MULT={'negative_resistance':'1','bias_unit':'4 / 64','var_feed':'4','varactor_bias':'1 / 2','reg_input':'2','reg_load':'2','reg_pullup':'20','reg_pulldown':'4'}


def histories():
    rows=[]
    for run in sorted((ROOT/'runs/49').glob('*_nominal')):
        q=json.loads((run/'measurements.json').read_text());cs=sha(run/'inputs/circuit.scs');push=None
        for pr in sorted((ROOT/'runs/49').glob('*_push')):
            if (pr/'measurements.json').exists() and sha(pr/'inputs/circuit.scs')==cs:
                push=json.loads((pr/'measurements.json').read_text())['max_pushing_pct_per_V']
        rows.append((run,q,push))
    return rows


def knowledge(r,s):
    v=r['values'];pp=r['point']['plateaus'];push=r['pushing'];rows=[]
    for label,key,scale,unit in INFO:
        g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤'
        rows.append(f"| {label} | {g['value']*scale:.9g} {unit} | {sign}{g['limits']['original']*scale:.9g} | {sign}{g['limits']['10pct']*scale:.9g} | {sign}{g['limits']['15pct']*scale:.9g} |")
    size_rows=[]
    for key,q in s['roles'].items():
        size_rows.append(f"| {ROLE_NAMES[key]} | {q['model']} | {q['rounded_W_um']:.2f}/{q['L_um']:.2f} | {q['gmid']:.2f} | {q['Id_A']*1e6:.3f} | {MULT[key]} |")
    measure_rows=[]
    for i,p in enumerate(pp):
        lo,hi=[x['plateaus'][i]['frequency_Hz']/1e9 for x in push['points']]
        measure_rows.append(f"| {p['control_V']:.1f} | {p['frequency_Hz']/1e9:.9f} | {lo:.9f} | {hi:.9f} | {push['pushing_pct_per_V'][i]:.8f} | {p['swing_Vpp']:.7f} |")
    hist_rows=[]
    for run,a,ps in histories():
        q=a['values'];hist_rows.append(f"| {run.name} | {q['frequency0_Hz']/1e9:.6f} | {q['frequency1p8_Hz']/1e9:.6f} | {q['power_W']*1e3:.5f} | {ps if ps is not None else '未测'} |")
    body=f'''# 49：SMIC18MMRF 2 GHz 差分 LC VCO nominal 复现

## 验收结论与范围

本次为 `{r['status']}`：14 项标量门槛及不可放宽的四档严格单调、实际跨越 2 GHz、起振存在、每窗 20 个有效上升沿全部满足。需要 15% 放宽的是高控制端频率和调谐比；功耗在 10% 边界内，其余指标均满足原门槛。频率端点不是固定中心精度窗口，而是源任务分别定义的上下限，按正值上限/下限乘 1.15/0.85。没有更改控制电压、负载、时间窗口或起振判定阈值。

| 指标 | SMIC18 实测 | 原门槛 | 10% 边界 | 15% 边界 |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

只验证 TT、27°C、1.8 V，以及原 pushing 公式需要的 1.62/1.98 V 两端点；后两者承担 pushing 与振荡数据完整性检查，不代表全部供电角落指标通过。实际 1.62 V 起振 {push['points'][0]['startup_s']*1e9:.7f} ns，1.98 V 的 VDD 功耗 {push['points'][1]['power_W']*1e3:.7f} mW，明确不能据本结果声称完整 27 点 PVT 符合。原任务未要求相噪或抖动，本次未测；没有以理想公式代替噪声仿真，也没有 PEX/MC 结论。

## 冻结接口、激励和测量

源题为 `sky130-lc-vco-2ghz-pvt`，原 instruction、正式 verifier、reference、电路和公开 benches 均冻结于 `source/`。接口为 `lc_vco_2ghz (vss iref vctrl vdd outp outn)`。唯一外部模拟偏置为从 IREF 流向地的 50 uA 电流源。outp/outn 各承载 10 fF。VCTRL 依次为 0、0.6、1.2、1.8 V，变化结束时刻 40、80、120 ns；每次斜坡 100 ps。瞬态至 160 ns，maxstep=5 ps、skipdc=yes，仅强制 outp=0.61 V、outn=0.59 V 两个原初值。

固定窗口分别为 20–39、60–79、100–119、140–159 ns，不根据稳态是否建立移动窗口。频率严格为窗口内首 20 个差分上升零交叉的 `19/(t20−t1)`；第 20 个边沿必须在窗口结束前。摆幅使用差分峰峰值；端口与共模采用所有四个窗口的极值。起振为首次 abs(outp−outn) 达到 0.2 V。功耗为 `−1.8×∫I(VDD)dt/139 ns`，固定积分 20–159 ns，包含三次调谐转换、50 uA 参考支路、偏置调节器、谐振核以及负载充放电。源任务指标仅统计 VDD 端口，不把外部 VCTRL 驱动器的功耗计入该指标。

| VCTRL/V | f@1.8V/GHz | f@1.62V/GHz | f@1.98V/GHz | pushing/(%/V) | nominal Vdiff/Vpp |
|---:|---:|---:|---:|---:|---:|
{chr(10).join(measure_rows)}

每档 pushing 为 `100×abs(f1.98−f1.62)/mean(f1.98,f1.62)/0.36`，四档分别计算再取最大，绝不只选一个调谐点。最终最大值 {push['max_pushing_pct_per_V']:.9f} %/V，优于原 0.6 %/V。

## 电路与原厂无源器件

两只 n18 交叉耦合产生负电阻，由两层 p18 自偏置级联镜向两只电感的公共供流端供电。参考二极管各为 4 个 LUT 单元，供流镜各为 64 个相同单元，名义比例 16，目标谐振核电流 800 uA。电感采用原厂 `ind_rf r=60u n=3.5`，与 RF readme 示例相同；每只模型串联 L={s['inductor']['model_series_L_H']*1e9:.6f} nH、R={s['inductor']['model_series_R_ohm']:.6f} ohm。`omega L/R≈{s['inductor']['approx_Q_at_2GHz']:.3f}` 仅是串联支路近似 Q，仿真包含原厂衬底、损耗及寄生，不能把此估算视为实测器件 Q。两个原厂电感分别使用完整模型，未人为补加互感。

每个输出对地一只 RF MIM（20×30 um²，标称 0.6 pF）。每边由三个 30×30 um² 原厂 RF MIM 并联成 2.7 pF 交流耦合，再连接两个原厂 `pvar18w10l1_ckt_rf wr=10u lr=1u nf=20` 并联。变容端口 1 接原 VCTRL，端口 2 接 varp/varn，通过两个并联 W=1/L=3 um 的原厂 rpposab_3t 电阻连接 vbias。共 2 电感、8 RF MIM、4 RF 变容实例、4 工艺电阻、16 模拟 MOS 实例。DUT 内没有理想 R/L/C、理想偏置源或行为振荡器。

vbias 不是隐藏理想参考。MPVB 从真实 VDD 镜出约 50 uA，两个串联 NMOS 二极管建立 vrefvar；5 MOS 误差放大器及模拟推挽共源功率级跟随该参考。偏置电路给交流耦合电容提供真实启动充电，并吸收调谐引起的电荷。该功率级处理连续反馈误差信号，属于模拟电路；电路没有数字逻辑或标准单元需要，数字单元数为 0。所有 16 个自定义 MOS 均有 gm/ID LUT 尺寸依据。

## gm/ID 定尺寸与实际工作点

使用既有只读 SMIC18 TT/27°C、VBS=0、|VDS|=0.45 V、参考 W=10 um 的表。每类尺寸以 `W=ID/(ID/W)` 得到，再量化至 20 nm 网格；大总宽度由整数 m 复制同一单元，单元 W 最大 64.02 um，均在 n18/p18 的 100 um 范围内。没有修改 PDK、Bridge、现有 LUT 或原厂 RF 子电路。

| 作用 | 模型 | 单元 W/L /um | 目标 gm/ID /V⁻¹ | 目标单元电流/uA | m |
|---|---|---:|---:|---:|---:|
{chr(10).join(size_rows)}

负阻对目标 gm/ID=12，单元 400 uA，初值 gm=4.8 mS，表内 fT≈18.10 GHz。PMOS 短沟道参考目标 gm/ID=20，用较小偏置节点电容加快启动；变容偏置 PMOS 采用 L=1 um，其 gm/ID=17.75 由与短沟道参考相同的 LUT VGS 反查得到，不直接把不同 L 器件按几何比例镜像。NMOS 二极管目标 7.3，二极管堆叠上管实际具有体效应，因此 LUT 仅为初值。

以 VCTRL=0.6 V 窗口为例：供流级联管实际平均 801.387 uA、gm/ID=20.37；变容供流支路 48.502 uA、gm/ID=17.88；输入对单边 48.749 uA、gm/ID=15.24；上拉 414.180 uA、gm/ID=15.97；下拉 413.943 uA、gm/ID≈1.61。下拉 LUT 初值 gm/ID=3，对应参考偏置点，最终实际栅压较高，真实 ID 与 gm/ID 必须以 PSF 为准。所有偏置/调节器管的最终四个窗口最小饱和余量均为正；振荡负阻对的周期变化按动态工作解释，未强求 LUT 工作点在整周期恒定。

## 迭代证据与关键机理

原厂 RF MOS 变容模型含浮置源漏及高阻泄漏。仅看 DC 小信号 C–V 不能预测原题 UIC 加阶跃控制的轨迹：在输出直流偏置 0.55 V、2 GHz/0.15 V 实际正弦激励下，四个控制平台的等效电容依次约 1.0873、1.7454、1.4704、1.5240 pF，内部节点先跟随 VCTRL，随后被结钳位，导致非单调。独立 AC 与瞬态特征仿真保留在 `varactor_characterization.json` 与 `varactor_transient_characterization.json`，诊断激励不属于最终 DUT。

将变容偏置抬高并交流耦合解决了主要单调性，但大耦合电容由 50 uA 直接充电无法在固定窗口前完成；随后真实调节器解决充电问题。长沟道大参考镜的节点电容曾使镜像电流继续缓慢变化，短沟道高 gm/ID 参考减小此问题。供电 pushing 的最后瓶颈是 120 ns 控制跃变后的吸收电荷能力：弱下拉使低电源的 vbias 在 140–150 ns 仍偏离参考。最终减小耦合为每边 2.7 pF、把下拉 m 从 1 提至 4，并把谐振核目标从 1.1 mA 降至 0.8 mA，保留摆幅且控制总 VDD 功耗。

| nominal 运行 | f(0)/GHz | f(1.8)/GHz | P/mW | 同电路最大pushing/(%/V) |
|---|---:|---:|---:|---:|
{chr(10).join(hist_rows)}

前三轮存在非单调；后续几轮虽 nominal 接近或通过放宽边界，pushing 仍失败，未将这些尝试计为成功。最终才完整通过。全部失败运行均保留真实 PSF、冻结输入和元数据，不覆盖旧结果。最终代价是调谐比比原目标低约 13.33%，以及高控制端频率比原上限高约 12.89%，仍明确标为 15% 复现。

## 复核与可复现证据

Spectre 18.1，reltol=1e-5、vabstol=1e-8、iabstol=1e-14、conservative、traponly、maxstep=5 ps。每个正式运行存储 PSF ASCII 波形，并核查有限值、递增时间轴、160 ns 覆盖、每个窗口第 20 个零交叉和全部模型几何告警。末版两个正式运行无警告，无 CMI-2441。完整窗口所有周期的频率仅作交叉核验，最终指标仍使用原首 20 个边沿；最大相对差约 0.01854%，不把该确定性差异解释为随机抖动。

- 最终 nominal：`{r['run_dirs'][0]}`。
- 最终 pushing：`{r['run_dirs'][1]}`。
- 电路 SHA256：`{sha(CASE/'circuit.scs')}`。
- 证据：`latest_results.json`、`sizing.json`、`contract.json`、`source_provenance.json`、`verification_audit.json`、`pdf_provenance.json`。
- 运行命令：`/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case49_lc_vco.py`；随后相同命令加 `--mode push`。
- 报告命令：同一 Python 执行 `scripts/review_pdf.py 49`；PDF 位于 `reports/49-lc-vco-review.pdf`。

输入闭包包含未修改 RF 库、MIM、变容、电感及其相对 include；基础 MOS/电阻模型保留原绝对路径与递归哈希。源 reference 的 27 角落汇总只作为原题背景，不能用其最坏值与本次 nominal 数据混作工艺间定量优劣比较。相噪、振幅噪声、真实参考源、版图互耦、PEX、失配以及完整 PVT 仍需后续专门验证。
'''
    (CASE/'knowledge.md').write_text(body)


def make49():
    r=json.loads((CASE/'latest_results.json').read_text());s=json.loads((CASE/'sizing.json').read_text());v=r['values'];pp=r['point']['plateaus'];push=r['pushing']
    assert r['nominal_complete'] and r['status']=='complete_15pct'
    knowledge(r,s);d=data(ROOT/r['run_dirs'][0],'tran.tran');dp=data(ROOT/r['run_dirs'][1],'tran.tran');t=d['time'];tp=dp['time'];out=ROOT/'reports/49-lc-vco-review.pdf'
    with PdfPages(out,metadata={'Title':'49 SMIC18 2GHz LC VCO 审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('49 | 2 GHz 差分 LC VCO 审查',1,'结论：全部nominal维度及四档supply pushing在15%边界内通过。')
        para(fig,.85,'TT / 27°C；nominal为1.8 V，pushing端点1.62/1.98 V；唯一外部偏置IREF=50 uA，每输出10 fF。保留原四档控制、初值及固定测量窗口。',9.4)
        rows=[]
        for label,key,scale,unit in INFO:
            g=r['gates'][key];sgn='≥' if g['sense']=='min' else '≤';rows.append([label,f"{g['value']*scale:.5g}",f"{sgn}{g['limits']['original']*scale:.5g}",f"{sgn}{g['limits']['10pct']*scale:.5g}",f"{sgn}{g['limits']['15pct']*scale:.5g}",unit])
        table(fig,[.07,.335,.86,.44],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.16,.15,.15,.15,.10],8.3)
        para(fig,.294,'只有高控制端频率与调谐比需15%放宽；功耗满足10%边界，其余均达到原门槛。正值上限乘1.10/1.15，下限乘0.90/0.85；严格单调、覆盖2 GHz和数据完整性不放宽。',9.1)
        para(fig,.191,'四窗为20–39、60–79、100–119、140–159 ns；f=19/(t20−t1)，取各窗首20个差分上升零交叉。总VDD功耗按20–159 ns积分，包含三次调谐跃变与真实偏置调节器。',9.1)
        para(fig,.095,'未执行其余PVT、MC、PEX及相噪/抖动。供电端点用于pushing与振荡数据完整性，不代表所有供电角落的频率、起振和功耗指标均通过。',9.0)
        save(pdf,fig)

        fig=page('原厂 RF 谐振腔与真实偏置调节',2,'DUT：16只模拟MOS、2只电感、8只RF MIM、4只RF变容与4只工艺电阻。')
        ax=fig.add_axes([.07,.646,.86,.211]);ax.axis('off');ax.set(xlim=(0,12),ylim=(0,4))
        for x,y,w,h,label in [(.2,2.75,3.4,.85,'IREF 50 uA\nPMOS级联镜 ×16'),(4.45,2.75,3.3,.85,'两只原厂ind_rf\n交叉耦合n18负阻对'),(8.55,2.75,3.2,.85,'差分outp/outn\n各10 fF负载'),(.2,.7,3.4,1.0,'MPVB + 两只n18二极管\nVREFVAR'),(4.45,.7,3.3,1.0,'5管OTA + 模拟推挽\n真实VBias调节器'),(8.55,.7,3.2,1.0,'两边RF变容\n端口1直接接VCTRL')]:
            ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor=BLUE));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=8.3)
        for y in [1.2,3.18]:
            for x1,x2 in [(3.6,4.45),(7.75,8.55)]:ax.annotate('',xy=(x2,y),xytext=(x1,y),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.plot([10.1,10.1],[1.7,2.75],color=GREEN);ax.text(10.2,2.15,'2.7 pF耦合/边',fontsize=8,color=GREEN)
        ax.text(5.4,.13,'VBias经每边2只并联工艺电阻连接变容；OTA作连续模拟反馈。',ha='center',fontsize=8)
        rows=[['电感/每边','ind_rf r=60 um, n=3.5',f"Lseries={s['inductor']['model_series_L_H']*1e9:.6f} nH"],['串联损耗近似','Rs=3.703012 ohm','2GHz时omegaL/R≈10.652'],['固定MIM/每边','mim1_rf 20×30 um²','标称0.6 pF'],['交流耦合/每边','3×mim1_rf 30×30 um²','标称2.7 pF'],['变容/每边','2×pvar18w10l1_ckt_rf','wr=10 um, lr=1 um, nf=20'],['偏置电阻/每边','2×rpposab_3t并联','W=1 um, L=3 um']]
        table(fig,[.07,.394,.86,.205],['部分','原厂实例/几何','说明'],rows,[.22,.45,.33],8.2)
        para(fig,.350,'RF readme明确给出上述电感、变容和30×30 um² MIM示例。原厂模型包含导体损耗、衬底和寄生；串联Q只作初值估算，不是完整器件实测Q。未修改任何原厂内部器件。',9.2)
        para(fig,.251,'关键诊断：RF变容内含浮置源漏。UIC加控制阶跃时，0.55 V直流偏置下，\n四档Ceff约1.087/1.745/1.470/1.524 pF，并不单调。\n独立2GHz瞬态特征验证了内部节点跟随再钳位的历史效应。',9.1)
        para(fig,.149,'最终把变容直流偏置提升至约1.47 V，并用原厂MIM隔离输出的约0.56 V共模。参考、充电及调谐电荷吸收均由真实MOS电路提供，只有原接口50 uA为外部偏置。',9.1)
        para(fig,.084,'无数字逻辑；模拟推挽输出级跟随连续误差，不是数字反相器。DUT内没有理想R/L/C或隐藏电流、行为振荡源。',8.9)
        save(pdf,fig)

        fig=page('gm/ID 单元尺寸与动态工作点',3,'既有SMIC18 LUT只读；TT/27°C，参考W=10 um、VBS=0、|VDS|=0.45 V。')
        rows=[]
        for key,q in s['roles'].items():rows.append([ROLE_NAMES[key],q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:.2f}",f"{q['gmid']:.2f}",f"{q['Id_A']*1e6:g}",MULT[key]])
        table(fig,[.07,.609,.86,.241],['作用','模型','W/L /um','gm/ID','单位ID/uA','实例m'],rows,[.24,.10,.19,.14,.17,.16],8.4)
        para(fig,.567,'W=ID/(ID/W)，取20 nm网格；总宽度以整数m复制，单元W最大64.02 um，未超过100 um模型限制。负阻管初值gm=4.8 mS、fT≈18.10 GHz。',9.2)
        para(fig,.486,'PMOS参考用L=0.18 um/gmID=20以减小启动节点电容；长L=1 um的变容供流管反查相同VGS，得到gmID=17.75。二极管上管的实际体效应仍以PSF核查。',9.2)
        ops=r['operating_conditions'][1]['devices'];rows=[]
        for dev in ['MPREFU','MPREFL','MPCAS','MPVB','MNB2','MRI2','MRPU','MRPD','MNP']:
            q=ops[dev];rows.append([dev,f"{abs(q['ids'])*1e6:.4f}",f"{q['gmid']:.3f}",f"{q['min_saturation_headroom_V']:.5f}"])
        table(fig,[.07,.175,.86,.25],['VCTRL=0.6 V','|平均ID|/uA','实际gm/ID','最小饱和余量/V'],rows,[.23,.25,.23,.29],8.5)
        para(fig,.137,'工作点为60–79 ns时间加权平均；余量取|VDS|−|VDSAT|最小值。下拉实际gm/ID约1.61，区别于LUT初值3，源于最终较高栅压；不能把表值当实测。',9.0)
        para(fig,.087,'最终四个窗口全部偏置/调节器MOS饱和余量为正。负阻对按真实周期变化解释，LUT用于初始尺寸，不强求整周期工作点恒定。',8.8)
        save(pdf,fig)

        fig=page('原初值起振与四档固定窗口',4,'skipdc=yes；只设outp=0.61 V、outn=0.59 V，无额外kick或人工预充电。')
        ax=fig.add_axes([.11,.665,.83,.185]);ix=t<20e-9;vd=d['outp']-d['outn']
        ax.plot(t[ix]*1e9,vd[ix],color=BLUE,lw=.8);ax.axhline(.2,color=GREEN,ls='--',lw=.8);ax.axhline(-.2,color=GREEN,ls='--',lw=.8);ax.axvline(v['startup_s']*1e9,color=GRAY,ls=':')
        ax.set(xlabel='Time (ns)',ylabel='Vdiff (V)',xlim=(0,20));ax.grid(alpha=.2)
        ax=fig.add_axes([.11,.400,.83,.173])
        for c,(a,b) in zip(CONTROLS,WINDOWS):
            ix=(t>=a)&(t<=a+2e-9);ax.plot((t[ix]-a)*1e9,vd[ix],label=f'VCTRL={c:g}V',lw=.85)
        ax.set(xlabel='Time after window start (ns)',ylabel='Vdiff (V)',xlim=(0,2));ax.legend(ncol=2,fontsize=8,loc='upper right');ax.grid(alpha=.2)
        rows=[]
        for p in pp:rows.append([f"{p['control_V']:.1f}",f"{p['window_s'][0]*1e9:.0f}–{p['window_s'][1]*1e9:.0f}",f"{p['frequency_Hz']/1e9:.9f}",str(p['rising_crossing_count']),f"{p['selected_crossings_s'][-1]*1e9:.6f}",f"{p['swing_Vpp']:.6f}"])
        table(fig,[.07,.189,.86,.143],['CTRL/V','窗口/ns','19周期频率/GHz','沿数','第20沿/ns','Vdiff/Vpp'],rows,[.12,.16,.23,.10,.22,.17],8.3)
        para(fig,.145,f"起振={v['startup_s']*1e9:.8f} ns；频率严格递减，最小相邻差={v['step_drop_Hz']/1e6:.8f} MHz。所有20边沿终点均在原窗口内，未延迟采样以掩盖建立过程。",9.1)
        para(fig,.074,'全窗全部完整周期频率与首20沿合同值的最大相对差约0.01854%；它反映有限窗口与建立轨迹，不是随机相噪或抖动测量。',9.0)
        save(pdf,fig)

        fig=page('四档供电 pushing 与完整 VDD 功耗',5,'同一冻结电路、相同控制序列/初值/10 fF负载；两个端点在单bench独立实例运行。')
        ax=fig.add_axes([.11,.653,.83,.197])
        for label,p in [('1.62V',push['points'][0]),('1.80V',r['point']),('1.98V',push['points'][1])]:ax.plot(CONTROLS,[q['frequency_Hz']/1e9 for q in p['plateaus']],marker='o',ms=4,label=label)
        ax.set(xlabel='VCTRL (V)',ylabel='Frequency (GHz)',xticks=CONTROLS);ax.legend(fontsize=8);ax.grid(alpha=.2)
        rows=[]
        for i,c in enumerate(CONTROLS):
            lo,hi=[q['plateaus'][i]['frequency_Hz']/1e9 for q in push['points']];rows.append([f'{c:.1f}',f'{lo:.9f}',f'{hi:.9f}',f"{push['pushing_pct_per_V'][i]:.8f}"])
        table(fig,[.07,.447,.86,.146],['VCTRL/V','f@1.62V/GHz','f@1.98V/GHz','pushing/(%/V)'],rows,[.15,.28,.28,.29],8.7)
        para(fig,.408,'定义：100×|f1.98−f1.62| / mean(f1.98,f1.62) / 0.36 V。最大0.337977 %/V，四档全部满足原0.6 %/V。每个端点每窗均有至少20个有效上升沿，均达到0.2 V起振阈值。',9.2)
        ax=fig.add_axes([.11,.213,.83,.135]);bins=np.arange(20,160)
        means=[-time_mean(t,d['VDD:p'],a*1e-9,b*1e-9)*1e3 for a,b in zip(bins[:-1],bins[1:])]
        ax.plot(bins[:-1]+.5,means,color=BLUE,lw=1);ax.axhline(v['power_W']/1.8*1e3,color=GREEN,ls='--',lw=.8,label='139 ns mean')
        ax.set(xlabel='Time (ns)',ylabel='1 ns mean current (mA)',xlim=(20,159));ax.grid(alpha=.2);ax.legend(fontsize=7,loc='lower right')
        para(fig,.161,f"固定20–159 ns平均VDD功耗={v['power_W']*1e3:.8f} mW；四个单独平台约2.534–2.542 mW。图示1 ns分箱，指标仍以原始PSF积分，包含全部调谐转换及偏置支路。",9.0)
        para(fig,.079,'端点诊断：1.62 V起振14.2679 ns，1.98 V功耗2.93567 mW。端点只服务pushing，不能据此宣称全供电PVT通过。VCTRL外部驱动功耗不属于源题VDD指标。',8.9)
        save(pdf,fig)

        fig=page('保留失败迭代与证据核验',6,'八轮nominal及对应pushing/变容诊断都保留真实PSF，未把单项通过计作完整成功。')
        rows=[]
        for i,(run,q,p) in enumerate(histories(),1):
            z=q['values'];rows.append([i,f"{z['frequency0_Hz']/1e9:.5f}",f"{z['frequency1p8_Hz']/1e9:.5f}",f"{z['tuning_ratio']:.5f}",f"{z['power_W']*1e3:.5f}",'未测' if p is None else f'{p:.5f}'])
        table(fig,[.07,.583,.86,.266],['轮次','f0/GHz','f1.8/GHz','调谐比','P/mW','max pushing'],rows,[.10,.18,.18,.18,.18,.18],8.5)
        para(fig,.540,'1–3轮：直接变容或偏置尚未建立，频率非单调。4–6轮：提升变容偏置、缩短PMOS参考L并增强调节器后nominal改善，但pushing仍约4.05/1.96/1.26 %/V，不能验收。',9.2)
        para(fig,.445,'第7轮：每边耦合缩到2.7 pF，前三档pushing通过，但末档1.377 %/V；实测低供电vbias仍在140–150 ns恢复，且末两档差仅3.76 MHz。第8轮下拉m=4、核心800 uA，补足电荷吸收并控制总功耗。',9.2)
        para(fig,.338,'代价：最终调谐比相对原下限低13.33%，高控制端频率相对原上限高12.89%。因此只标15%复现，不表述为原规格全通过；原Sky130汇总是27角落最坏值，不能直接作为nominal工艺比较。',9.2)
        rows=[['仿真设置','reltol=1e-5；vabstol=1e-8；iabstol=1e-14；traponly'],['时间/边沿','conservative；maxstep=5 ps；160 ns全程；12窗×20边沿'],['实际PSF','时间严格递增、全部保存轨迹有限；真实窗口积分'],['模型/快照','无Spectre警告/CMI-2441；RF原文件哈希及include闭包'],['未验证范围','完整PVT、相噪/抖动、真实参考源、MC、PEX/电感互耦']]
        table(fig,[.07,.097,.86,.175],['检查','实现/限制'],rows,[.22,.78],8.5)
        para(fig,.063,'知识草稿：cases/49-lc-vco/knowledge.md；机器审计：verification_audit.json。',8.8)
        save(pdf,fig)

        fig=page('完整 DUT 与可重放证据',7,'模型include均位于bench层；下列电路不含任何隐藏激励或理想谐振元件。')
        body='\n'.join(x for x in (CASE/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.072,.856,body,fontsize=7.6,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.16)
        para(fig,.335,'运行：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python\n scripts/case49_lc_vco.py\n随后同一命令加 --mode push；PDF执行 scripts/review_pdf.py 49。',8.9)
        para(fig,.249,'最终nominal：'+r['run_dirs'][0]+'\n最终pushing：'+r['run_dirs'][1],8.3)
        para(fig,.178,'每个run含inputs/bench.scs、电路/合同/尺寸/RF模型快照，run.json记录基础模型递归哈希与额外RF哈希，output/bench.raw保存PSF，measurements.json保存实际测量。',8.9)
        para(fig,.097,'原任务材料见cases/49-lc-vco/source/，LUT/PDK/Bridge均未修改；PDF与全部渲染页哈希见pdf_provenance.json。',8.8)
        para(fig,.057,'电路SHA256：'+sha(CASE/'circuit.scs'),7.0)
        save(pdf,fig)
    write_json(CASE/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(CASE/'latest_results.json'),circuit_sha256=sha(CASE/'circuit.scs'),generated_at=now(),pages=7,render_review_pending=True))
    update_case(49,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out


def audit(visual_review=False):
    r=json.loads((CASE/'latest_results.json').read_text());s=json.loads((CASE/'sizing.json').read_text())
    c=json.loads((CASE/'contract.json').read_text());p=json.loads((CASE/'pdf_provenance.json').read_text())
    assert r['status']=='complete_15pct' and r['nominal_complete'] and r['functional_checks_pass']
    assert len(r['gates'])==14 and all(g['passes']['15pct'] for g in r['gates'].values())
    assert not r['pass_tiers']['original'] and not r['pass_tiers']['10pct'] and r['pass_tiers']['15pct']
    assert c['controls_V']==[0,.6,1.2,1.8] and c['temperature_C']==27 and c['nominal_VDD_V']==1.8
    assert c['pushing_VDD_V']==[1.62,1.98] and c['reference_sink_A']==50e-6 and c['load_each_F']==10e-15
    assert c['measurement_windows_s']==[list(w) for w in WINDOWS] and c['stop_s']==160e-9 and c['max_step_s']==5e-12
    assert c['initial_voltages_V']==dict(outp=.61,outn=.59) and c['skip_DC'] and c['power_window_s']==[20e-9,159e-9]
    for f in json.loads((CASE/'source_provenance.json').read_text())['files']:
        assert sha(f['original'])==f['sha256']==sha(ROOT/f['frozen'])
    for q in s['roles'].values():
        assert sha(q['lut_path'])==q['lut_sha256'] and q['lut_metadata']['temperature_C']==27
        assert q['rounded_W_um']<=100 and q['gmid']>0 and q['Id_A']>0
    assert abs(s['roles']['bias_unit']['Vgs_V']-s['roles']['var_feed']['Vgs_V'])<.001
    for name,h in s['model_files'].items():assert sha(name)==h
    text=(CASE/'circuit.scs').read_text();assert 'subckt lc_vco_2ghz (vss iref vctrl vdd outp outn)' in text
    assert not re.search(r'(?im)^\s*(include|model)\b|\b(vsource|isource|bsource|capacitor|resistor|inductor)\b',text)
    mos=re.findall(r'^(M\S+)\s+\([^\n]+\)\s+(n18|p18)\s+w=([0-9.]+)u\s+l=([0-9.]+)u(?:\s+m=([0-9.]+))?$',text,re.M)
    assert len(mos)==16 and all(0<float(q[2])<=100 and float(q[3])>=.18 and (not q[4] or float(q[4]).is_integer()) for q in mos)
    assert len(re.findall(r'^XL[PN] .* ind_rf r=60u n=3.5$',text,re.M))==2
    assert len(re.findall(r'^XC\S+ .* mim1_rf ',text,re.M))==8
    assert len(re.findall(r'^XV\S+ .* pvar18w10l1_ckt_rf wr=10u lr=1u nf=20$',text,re.M))==4
    assert len(re.findall(r'^RB\S+ .* rpposab_3t w=1u l=3u$',text,re.M))==4
    bias_devices=[q[0] for q in mos if q[0] not in ['MNP','MNN']]
    assert all(z['devices'][dev]['min_saturation_headroom_V']>0 for z in r['operating_conditions'] for dev in bias_devices)
    runs=[]
    for run in sorted((ROOT/'runs/49').iterdir()):
        if not (run/'run.json').exists():continue
        m=json.loads((run/'run.json').read_text());assert m['status']=='completed' and m['model_dimensions_valid'] and m['temperature_C']==27
        assert sha(ROOT/m['netlist'])==m['netlist_sha256']
        for dep in m['dependencies'].values():assert sha(ROOT/dep['snapshot'])==dep['sha256']
        for name,h in m['models'].items():assert sha(name)==h
        visited=set()
        def includes(f):
            f=f.resolve()
            if f in visited:return
            visited.add(f);assert f.is_file()
            for rel in re.findall(r'^\s*include\s+"([^"]+)"',f.read_text(errors='replace'),re.M|re.I):
                nxt=Path(rel);includes(nxt if nxt.is_absolute() else f.parent/nxt)
        includes(ROOT/m['netlist'])
        raws=[f for f in (run/'output/bench.raw').iterdir() if f.is_file() and f.name.endswith(('.tran','.ac'))]
        assert raws and all(f.stat().st_size>0 for f in raws)
        runs.append(dict(path=str(run.relative_to(ROOT)),label=m['label'],hashes_match=True,include_closure_complete=True,model_dimensions_valid=True,
            warnings=m['warnings'],raw_files=[dict(path=str(f.relative_to(ROOT)),bytes=f.stat().st_size) for f in raws]))
    final_runs=[ROOT/q for q in r['run_dirs']]
    for run in final_runs:
        for name in ['circuit.scs','sizing.json','contract.json','source_provenance.json']:assert sha(CASE/name)==sha(run/'inputs'/name)
        bench=(run/'inputs/bench.scs').read_text();assert 'stop=160n maxstep=5p skipdc=yes' in bench
        assert '39.9n 0 40n 0.6 79.9n 0.6 80n 1.2 119.9n 1.2 120n 1.8' in bench
        assert not json.loads((run/'run.json').read_text())['warnings']
    dn=data(final_runs[0],'tran.tran');de=data(final_runs[1],'tran.tran')
    assert dn['time'][0]==0 and de['time'][0]==0 and abs(dn['time'][-1]-160e-9)<1e-15 and abs(de['time'][-1]-160e-9)<1e-15
    calculated=[extract_point(dn,'',1.8),extract_point(de,'_LOW',1.62),extract_point(de,'_HIGH',1.98)]
    recorded=[r['point'],*r['pushing']['points']]
    edge_windows=[]
    for actual,saved in zip(calculated,recorded):
        assert actual==saved and actual['oscillation_data_complete']
        for q,(a,b) in zip(actual['plateaus'],WINDOWS):
            assert len(q['selected_crossings_s'])==20 and q['twentieth_crossing_inside'] and a<=q['selected_crossings_s'][0]<q['selected_crossings_s'][-1]<=b
            edge_windows.append(dict(VDD_V=actual['VDD_V'],control_V=q['control_V'],first_s=q['selected_crossings_s'][0],twentieth_s=q['selected_crossings_s'][-1],count=q['rising_crossing_count']))
    errors=[abs(q['all_complete_period_average_Hz']/q['frequency_Hz']-1) for q in r['point']['plateaus']]
    assert max(errors)<.0005
    nominal_fs=[q['frequency_Hz'] for q in r['point']['plateaus']];assert nominal_fs[0]>=2e9>=nominal_fs[-1] and all(a>b for a,b in zip(nominal_fs,nominal_fs[1:]))
    pushing=[100*abs(hi['frequency_Hz']-lo['frequency_Hz'])/((hi['frequency_Hz']+lo['frequency_Hz'])/2)/.36 for lo,hi in zip(calculated[1]['plateaus'],calculated[2]['plateaus'])]
    assert pushing==r['pushing']['pushing_pct_per_V'] and max(pushing)<.6
    pdf=ROOT/p['pdf'];assert sha(pdf)==p['sha256'] and sha(CASE/'latest_results.json')==p['results_sha256'] and sha(CASE/'circuit.scs')==p['circuit_sha256']
    info=subprocess.run(['pdfinfo',str(pdf)],check=True,text=True,capture_output=True).stdout;assert re.search(r'^Pages:\s+7$',info,re.M)
    pdftext=subprocess.run(['pdftotext',str(pdf),'-'],check=True,text=True,capture_output=True).stdout;assert pdftext.index('本模块利用')<pdftext.index('结论')
    pages=[]
    for i in range(1,8):
        f=ROOT/f'reports/49-review-page-{i}.png';assert f.is_file() and f.stat().st_size>0
        pages.append(dict(page=i,path=str(f.relative_to(ROOT)),sha256=sha(f)))
    assert visual_review,'Actual visual inspection of all seven final pages is required before marking the PDF ready.'
    report=dict(generated_at=now(),case_slot=49,status='passed',acceptance_tier='15pct',result_sha256=sha(CASE/'latest_results.json'),circuit_sha256=sha(CASE/'circuit.scs'),
        pdf_sha256=sha(pdf),pdf_pages=7,pdf_intro_before_verdict=True,all_final_pages_visually_reviewed=True,rendered_pages=pages,
        nominal_scalar_gates=14,all_nominal_gates_pass=True,unrelaxed_monotonicity_and_2GHz_coverage=True,source_hashes_match=True,LUT_hashes_match=True,
        native_RF_models_unmodified=True,DUT_analog_MOS_count=16,digital_cells=0,no_ideal_DUT_sources_or_passives=True,all_bias_saturation_headroom_positive=True,
        pushing_all_controls_original_pass=True,edge_windows=edge_windows,max_nominal_allperiod_frequency_relative_difference=max(errors),runs=runs,
        scope_exclusions=c['scope_excludes'],pushing_endpoints_full_PVT_not_claimed=True,
        endpoint_diagnostics=dict(startup_1p62_s=calculated[1]['startup_s'],power_1p98_W=calculated[2]['power_W']),
        knowledge_path=str((CASE/'knowledge.md').relative_to(ROOT)),knowledge_sha256=sha(CASE/'knowledge.md'))
    write_json(CASE/'verification_audit.json',report)
    p.update(render_review_pending=False,visually_reviewed_at=now(),all_pages_reviewed=True,rendered_pages=pages)
    write_json(CASE/'pdf_provenance.json',p)
    update_case(49,status='complete_15pct',nominal_complete=True,review_pdf=str(pdf.relative_to(ROOT)),review_pdf_ready=True,pdf_render_review_pending=False,
        knowledge_draft=str((CASE/'knowledge.md').relative_to(ROOT)),verification_audit=str((CASE/'verification_audit.json').relative_to(ROOT)))
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--audit',action='store_true');ap.add_argument('--visual-review-complete',action='store_true');args=ap.parse_args()
    print(json.dumps(audit(args.visual_review_complete),indent=2,ensure_ascii=False) if args.audit else make49())
