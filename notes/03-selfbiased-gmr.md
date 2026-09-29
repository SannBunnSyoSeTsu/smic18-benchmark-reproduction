# 03 · 自偏置退化GM-R：跨导控制、端口功耗与失真口径

本模块提供约两倍差分电压增益，并结合自偏置与源极退化来控制跨导和失真。相比直接固定电流偏置的差分对，β倍增环使跨导与电阻相关，源极电阻进一步削弱器件非线性的影响。芯片中可用作模拟前端或连续时间信号通路的线性增益级；跨工艺温度的稳定性仍需另行验证。

状态：**SMIC18MMRF / TT / 1.8 V / 27°C，全部对应 nominal 原始指标通过**。只宣称原理图级 nominal；未执行其他PVT、失配或版图验证。审查PDF已逐页检查中文、图表和网表可读性。

[审查 PDF](../cases/03-selfbiased-gmr/review.pdf) · [精确电路](../cases/03-selfbiased-gmr/circuit.scs) · [验收合同](../cases/03-selfbiased-gmr/contract.json) · [实测结果](../cases/03-selfbiased-gmr/latest_results.json)

当前报告：**4页正文＋2页完整电路图，共6页**。下文历史交付记录中的页数对应当时的正文版本。

<!-- REPORT-MARKDOWN -->
## 可编辑报告与系统结构

[完整报告MD](../cases/03-selfbiased-gmr/review_report.md) · [对应PDF](../cases/03-selfbiased-gmr/review.pdf)
<!-- END-REPORT-MARKDOWN -->

## 电路与实测

本例独立实现自偏置源极退化放大器，未把第04项结果直接计入。β倍增n18单元5.04/0.36 µm，目标20 µA、gm/ID=16，MB2 m=4，RB=3 kΩ；输入每支同单元m=12.5，尾源m=25。p18镜18.76/1 µm。每侧RS=500 Ω、RL=1770 Ω。50 µA参考由14.88/1 µm n18终止，并驱动W0.24/L4 µm的弱启动下拉。DUT仅MOS与正值R，VCM端口保留但内部不用。

全部原nominal通过：1 MHz差分增益2.0008587 V/V、相对该增益的上端−3 dB带宽86.0638 MHz、全外部端口DC功耗1.079304 mW。3 MHz/100 mV差分峰值下，拟合基波增益1.9950292、SDR61.9817 dB、残差112.292 µVrms。原增益窗口1.98–2.02、带宽60 MHz、功耗1.5 mW和SDR60 dB均保持。

## 自偏置和退化分别解决什么

β倍增环使主管gm与RB相关，源极退化再降低有效跨导和信号非线性。实际输入gm4.078 mS、gmb1.000 mS，近似gm_eff=gm/[1+(gm+gmb)RS]，不能忽略体效应。MB2实际gm/ID21.04、处于弱反型，不能对整个自偏置环无条件使用强反型平方律。

主管电流22.068 µA；尾源25个相同单位却只流505.942 µA，因其VDS0.1794 V明显低于主管0.5220 V。相同W/L单元保证几何一致，不等于镜像电流无误差。尾源饱和余量77.64 mV；本次只作nominal，不宣称其余14个工艺温度点的增益均稳定。

## 迭代与测量

初版RL1900 Ω增益2.14485、基波增益2.13841，超出窗口。保持偏置及RS，将RL改为1770 Ω后增益回到目标，带宽80.25→86.06 MHz，SDR约61.98 dB。这次调整有明确的负载增益/极点依据，并保留两次运行。

SDR使用0.5–1.5 µs最终窗口的1001个等间隔样点，拟合DC+sin+cos，再求基波功率/残差均方。它不包含随机噪声。功耗统计VDD、VCM、VIN、VIP各端口功率绝对值；IREF已经从VDD供电，避免隐藏辅助端口功耗。

启动下拉采用第13项补充的窄管专属LUT，目标gm/ID8.558，实际8.591、电流0.372 µA。它持续导通并计入功耗；本任务没有冷启动斜坡门槛，也未为本电路额外宣称冷启动通过。4页PDF含开篇功能/应用说明、尺寸、工作点、频响、残差与精确网表。

[完整LUT查询](../cases/03-selfbiased-gmr/sizing.json) · LUT副本（保留于原本地归档，未随仓库上传）

## 复现与证据

[完整电路总图 SVG](../cases/03-selfbiased-gmr/schematic/full.svg) · [总图 PDF](../cases/03-selfbiased-gmr/schematic/full.pdf) · [2页电路分图](../cases/03-selfbiased-gmr/schematic/sheets.pdf) · [引脚与层次连接映射](../cases/03-selfbiased-gmr/schematic/connectivity.json) · [图纸审计](../cases/03-selfbiased-gmr/schematic_audit.json)

- [Spectre 运行记录](../runs/03/20260922T073138775167Z_gmr/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [工程脚本](../scripts) · [项目状态](../status.json)

原Sky130案例保持原样；本页是目标工艺实测的新记录。模型文件留在既有本地PDK目录，没有上传或修改。
