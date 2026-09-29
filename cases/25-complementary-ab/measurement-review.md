# 第25题 nominal 测量独立审查

审查范围为 `scripts/case25_complementary_ab.py` 对源正式 `tests/verify.py` 和全部相关 benches 的 nominal 映射；使用已有 PSF 作纯数值复核，没有启动任何电气仿真，没有修改设计/提取脚本、PDK或环境。

**结论：六组正式测量覆盖完整，噪声与 THD 的关键定义正确。当前同一电路的37个标量门槛全部达到原值；没有发现会推翻这版 nominal 结果的测量缺口。** 三个固定 `tt_mm` seed 与其余PVT在已冻结nominal范围之外，未把无失配的 `matched_offset_V` 当作seed offset验证。

审查时电路 SHA256 为 `96b5209db247cee7e96e92e1189b494a6d08dca1efd22237326692957ccbff80`；脚本读取版本 SHA256 为 `0d3af37613b4fbcffc588c67316d41af70d3360f37abcc24b9e793227be65a4a`（已含 root 的 true-STB 诊断函数）。本记录用于度量定义与已有结果复核，后续审计代码的补强不需要重做电气仿真。

## 1. nominal 维度与公式逐项对照

| 项目 | 源正式定义 | SMIC实现与结论 |
|---|---|---|
| 工艺/偏置 | TT/1.8 V/27°C；VDD→IREF 20 uA | 相同。20 uA从被测VDD引出，功耗包含该支路 |
| 五点AC | VCM=0.1/0.2/0.9/1.6/1.7 V；输出DC=0.9 V | 五实例保持独立共模，LFB+VSHIFT复制原DC-only反馈；4 pF与1 TΩ到0.9 V均保留 |
| 增益 | `20log10(abs(-Vout/Vinn))` @10 Hz；近轨80 dB、核心90 dB | 相同，未把VCM近轨误改为输出近轨 |
| UGB/PM | 首次下降0 dB交点；PM=展开相位+180°；各点≥1 MHz，近轨55°、核心60° | 相同；100点/dec比原20点/dec更密；另拒绝重复下降交点或回穿，更严格 |
| UGB平坦度 | 完整矩阵max/min≤2 | nominal只约化PVT维度，五个CM全部保留；比值1.32958198 |
| 闭环tracking | 0..1.8 V、步进5 mV；4 pF //10 kohm到0.9 V；反馈1 mohm | 相同，361个点；核心0.2..1.6 V误差≤5 mV、扩展0.1..1.7 V≤20 mV分别取全区间最大值 |
| ICMR | 固定20 mV误差判断；低端≤0.1 V、高端余量≤0.1 V、跨度≥1.5 V | 判断阈值不放宽；本版所有点误差<20 mV，原规定的高端报告范围为1.795 V，得到0..1.795 V；与正式verifier一致 |
| 静态功耗 | 五个AC工作点和0..VDD闭环扫描最大VDD功耗≤1.5 mW | 五个AC功耗与全扫描功耗分别设门槛，等价且完整；只统计原题VDD端口，不擅自改为所有bench电源功率之和 |
| 双向SR | 0.2↔1.6 V，10 ns输入边沿；0.48/1.32 V阈值；SR=0.84/Δt | 完整保留上升与下降，各≥2 V/us；输出负载相同 |
| 建立尾误差 | 2.9..3.0 us与4.9..5.0 us内最大绝对指令误差≤5 mV | 对两个完整尾窗口求极值，包含端点插值，不仅采末点；1 ns保存间隔较源2 ns更密 |
| CMRR | 固定VCM=0.9 V；差分1 V参考与共模1 V；4 pF、100 Mohm对地DC返回 | 差分±0.5 V、共模1 V相同；1 kHz与1 MHz均测；分开理想供电与原共用零AC阻抗理想供电等效 |
| PSRR | 固定VCM=0.9 V；差分1 V参考与VDD上1 V AC；4 pF、100 Mohm | 10 Hz与1 MHz均测；CMRR/PSRR复用同一条件下的差分参考实例有效 |
| 输入噪声 | 原noise bench的DC闭环、AC开环输入折算；10 Hz..1 MHz | 拓扑、VIN输入参考和4 pF //10 kohm负载相同；501点输入电压噪声谱平方积分，见下节 |
| THD | 1 kHz、0.9 V中心、0.4 Vpk、5 ms瞬态；最后一个周期Fourier | 使用4..5 ms、DC+第1..9次谐波；4000点相干最小二乘与原200点后处理交叉一致，见下节 |
| 有界失真残差 | 3.5..5 ms内max(abs(Vout−Vin))/0.4≤0.005 | 相同；没有去掉DC误差、相位误差或重新拟合后才算残差 |

37个门槛组成：五点AC各增益/UGB/PM/功耗共20项，加UGB比值1项；tracking误差2、功耗1、ICMR3共6项；噪声1项；CMRR/PSRR4项；双向SR与尾误差3项；THD与残差2项。STB属于补充稳定性诊断，不替换源AC测量。

## 2. 噪声：原bench实际是AC开环输入折算

源 `tb_noise.spi` 虽在注释和 instruction 使用“unity-gain input-referred noise”，实际连接为：

```text
VIN vinp DC0.9 AC1
LFB vout vinn 1e15 H
CFB vinn vac 1e6 F
VAC vac DC0 AC0
noise v(vout) VIN dec30 10 1Meg
input_noise_vrms = inoise_total
```

DC时LFB使输出经反相输入闭环；噪声/AC频段LFB近似开路、CFB将反相输入钳在AC地，VIN是非反相输入参考。因此原指标是这个工作点和负载下的 **开环输出噪声经输入传递函数折算**，不是实际单位增益闭环输出噪声积分。

SMIC的 `noise (vout 0) noise iprobe=VIN` 保留了此定义。真实PSF明确声明 `input probe=VIN`，`in` 与 `out` 均为 `V/sqrt(Hz)`，`gain` 为 `V/V`。故脚本的：

\[
v_{n,in,rms}=\sqrt{\int_{10}^{10^6} |n_{in}(f)|^2\,df}
\]

没有再次开方，也没有把PSD当成幅度谱积分。对501个已有频率点独立核对，`out/gain=in` 的最大相对误差为8.88×10⁻¹⁶。

- 脚本线性PSD梯形积分：**12.8944301761 uVrms**。
- 对同一谱按相邻点幂律作解析积分：**12.8943802251 uVrms**。
- 差异约3.87 ppm，对70 uVrms门槛没有影响。

正式报告宜写“原bench定义的输入折算噪声（DC闭环偏置、AC开环）”，避免把它误称为已测实际单位增益闭环输出噪声。此处应保留冻结bench，不需要为了修正注释而改变实际测试负载或拓扑。

## 3. THD：默认谐波映射与原200点结果

任务未覆盖 `nfreqs`、`fourgridsize` 或 `polydegree` 默认设置。ngspice官方手册说明默认 `nfreqs=10`、均匀重采样网格200点；官方 `fourier.c` 的循环明确从索引0到9，0为DC，归一化基波为1，THD累加索引2..9。它取最后一个基波周期，并排除该周期终点的重复采样。[官方手册](https://ngspice.sourceforge.io/docs/ngspice-44-manual.pdf)、[官方Fourier实现](https://github.com/ngspice/ngspice/blob/master/src/frontend/fourier.c)

因此，当前 `range(1,10)` 的9个交流谐波加DC项是正确映射，不缺第10次谐波：原“10”包含DC。目标公式为：

\[
THD(\%)=100\sqrt{A_2^2+\cdots+A_9^2}/A_1.
\]

源 `tran 0.5u 5m 3m` 的3 ms仅控制开始保存时间，不取消0..3 ms启动过程；最后周期仍是4..5 ms。SMIC保存完整0..5 ms，然后使用4..5 ms，因此不存在启动状态差异。

已有THD PSF含20001点、最大保存间隔250 ns，终点为4.999999999997437 ms（浮点精度内等于5 ms）。用同一PSF独立FFT复核：

| 后处理 | THD/% | 基波峰值/V |
|---|---:|---:|
| 原默认200个等间隔点，4..5 ms，h2..h9 | 0.0020861054184107 | 0.4000212011532994 |
| 4000点，4..5 ms，h2..h9 | 0.0020861054114441 | 0.4000212011533035 |
| root脚本4000点DC+正余弦最小二乘 | 0.0020861054114736 | 与上行一致 |

三者差异远小于有效精度，均低于原0.01%上限。当前4000点方法是加密，不是改变谐波带宽或挑选不同周期。有界残差为0.000267987621倍指令幅度，即0.0267987621%；它按完整3.5..5 ms指令误差计算，与Fourier THD分别验收。

## 4. 已有运行一致性与需保留的审计说明

本次实际核查以下六组 `run.json` 均为 completed，`model_dimensions_valid=true`，冻结电路SHA全部等于当前电路；没有混用第一版cc6p电路的结果：

| 组 | 运行目录尾名 |
|---|---|
| ac | `20260923T041729784311Z_ac` |
| track | `20260923T041737996305Z_track` |
| noise | `20260923T041738178168Z_noise` |
| reject | `20260923T041738398537Z_reject` |
| step | `20260923T041738565376Z_step` |
| thd | `20260923T041823802535Z_thd` |

两个实际审计注意点：

1. **AC并非零警告。** `run.json` 有两条 `SPECTRE-294`，内容是保存信号1480个、初始化可能较慢；它们不是模型尺寸或收敛错误。其余五组warnings为空。最终PDF应如实说明，不写“所有最终运行无任何警告”。
2. **读取版本的extract把 `model_dimensions_valid` 直接写成True。** 当前逐run元数据实际为True，故不影响本版结论；最终verification audit仍应从每个run.json推导/核对。建议同时验证每组电路SHA、时间/频率边界与应有门槛数量，不仅凭六个组名齐全判定归档完整。`--reuse`已有电路SHA筛选，而`--extract`直接读cache，因此归档审计是必要的实际证据链核查。

ICMR实现中的 `hi=1.795` 在本版不是缺口：0..1.8 V所有361点最大误差仅3.37617 mV，源verifier在全范围满足20 mV时明确把有效高端记为VDD−5 mV。连续区间检查比源第一交点处理更严格，不会在本版制造假通过。

root另行完成的true-STB五个共模诊断给出PM约86.57..86.94°、只有一次下降0 dB交点且没有回穿，与原AC夹具结果相近。该诊断提供额外稳定性证据，不改变原门槛或本报告的测量完整性判定。

**交付边界：** 本审查只确认冻结nominal合同的测量覆盖、公式与已保存数据一致性；完整25点PVT、额外代表角落、三seed失配以及PEX不在本轮结论内。最终PDF仍需root生成并逐页检查完整晶体管级示意图与全部指标表。

## root收尾修正

独立审查后，root已将extract的模型有效性改为从全部7个最终run.json读取，并检查completed、冻结电路SHA一致；不再硬编码True。现有PSF重新提取仍为complete_original，未重跑电气。完整图纸随后由独立代理绘制并目检，最终交付审计另行核对PDF及图纸哈希。
