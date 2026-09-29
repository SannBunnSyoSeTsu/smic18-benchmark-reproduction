# 13 · 恒跨导增益：自偏置、体效应和宽度专属LUT

本模块放大差分信号，并用β倍增环使输入跨导与电阻建立联系。相比固定电流偏置的电阻负载差分对，设计目标是降低增益对迁移率等工艺温度变化的敏感度。芯片中可用作模拟前端或连续时间滤波器的稳定增益级；本报告只验证nominal，尚未证明跨PVT增益稳定性。

状态：**SMIC18MMRF / TT / 1.8 V / 27°C，全部对应 nominal 原始指标通过**。只宣称原理图级 nominal；未执行其他PVT、失配或版图验证。审查PDF已逐页检查中文、图表和网表可读性。

[审查 PDF](../cases/13-constant-gm/review.pdf) · [精确电路](../cases/13-constant-gm/circuit.scs) · [验收合同](../cases/13-constant-gm/contract.json) · [实测结果](../cases/13-constant-gm/latest_results.json)

当前报告：**4页正文＋2页完整电路图，共6页**。下文历史交付记录中的页数对应当时的正文版本。

<!-- REPORT-MARKDOWN -->
## 可编辑报告与系统结构

[完整报告MD](../cases/13-constant-gm/review_report.md) · [对应PDF](../cases/13-constant-gm/review.pdf)
<!-- END-REPORT-MARKDOWN -->

## 电路和实测结果

β倍增偏置主NMOS单元W19.94/L1 µm，目标45 µA、gm/ID=14；源退化支路m=4、尾源m=2、输入对各m=1。PMOS镜为42.20/1 µm，目标gm/ID=10。RB=1.45 kΩ、每侧RL=5.6 kΩ。外部50 µA参考由14.88/1 µm n18二极管终止，并控制W0.24/L4 µm启动下拉。

最终1 MHz差分增益3.601451 V/V，−3 dB带宽55.4226 MHz（相对1 MHz增益），1 GHz增益0.199794 V/V。负载压降VDD−VCM,out=259.777 mV，总功耗424.366 µW，包含参考与持续启动电流。对称确定性模型零输入差分不平衡为0；没有MC，因此不宣称真实失调为0。

61点±60 mV DC扫描中，±2 mV得到中心增量增益3.601900；±30 mV为3.571418、±60 mV为3.480033，最坏相对误差3.3834%，小于原8%。这项“增量增益误差”的口径不是全扫导数，也不是SFDR。

## 显式冷启动

Spectre skipdc=yes，从全部节点0 V开始。VDD/VCM在0.1–1.1 µs上升，IREF在1.2–1.22 µs由0升到50 µA，差分输入在10–10.02 µs由0升到20 mV。8–9 µs的零输入不平衡约5.3e−17 V；14–15 µs的绝对输出/20 mV为3.588420，前后负载压降259.777/259.785 mV，均满足原窗口。

启动波形中自偏置在IREF加载前已经随电源建立，说明该指定斜坡下寄生充放电也参与启动。这里只证明给定冷启动合同；不能由单条波形证明所有电源斜率或启动机制均稳健。启动下拉最终仍有0.3720 µA，并未关断，已经计入功耗。

## gm≈1/RB只是初算

RB1.2 kΩ初版自偏置电流偏高，增益4.195、功耗520.1 µW；增益连15%误差窗口也超出。保持W/L和RL，仅把RB提高到1.45 kΩ，全部原nominal通过。

最终主管电流46.998 µA、gm=0.64959 mS，gm×RB≈0.942。输入每支46.388 µA、gm=0.65120 mS、gm/ID=14.038。即使主/输入单位电流密度相近，输入源极约0.342 V的体效应使VGS从主管的0.5182 V提高至0.6080 V。中等反型、体效应、镜支路漏压差与有限ro意味着RL/RB=3.862不能直接当作3.601的实测增益。

## 窄启动管需要相应几何的查表依据

最初用Wref10 µm的L4表，以gm/ID=12、200 nA选得W0.24 µm；该窄管实际gm/ID约8.59、电流约372 nA。为解决这项具体差异，补扫同W0.24/L4、VDS1.35 V的nominal表。在参考二极管LUT预测VGS=0.54648 V处选到gm/ID=8.558、电流375.48 nA；实际VGS0.54572 V、gm/ID8.591，与选点一致。最终W/L保持不变，依赖的新表和表征PSF均保留。

所有原nominal指标通过；27点PVT的增益max/min≤1.15仍不在当前复现范围，不能用一个点自行构造比值1来宣称通过。4页PDF包含全部尺寸、工作点、启动/线性曲线及精确网表。

[完整 LUT 查询](../cases/13-constant-gm/sizing.json) · 使用的LUT副本（保留于原本地归档，未随仓库上传）

## 复现与证据

[完整电路总图 SVG](../cases/13-constant-gm/schematic/full.svg) · [总图 PDF](../cases/13-constant-gm/schematic/full.pdf) · [2页电路分图](../cases/13-constant-gm/schematic/sheets.pdf) · [引脚与层次连接映射](../cases/13-constant-gm/schematic/connectivity.json) · [图纸审计](../cases/13-constant-gm/schematic_audit.json)

- [Spectre 运行记录](../runs/13/20260922T072020462547Z_static/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/13/20260922T072020597713Z_startup/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [工程脚本](../scripts) · [项目状态](../status.json)

原Sky130案例保持原样；本页是目标工艺实测的新记录。模型文件留在既有本地PDK目录，没有上传或修改。
