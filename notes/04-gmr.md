# 04 · GM-R：源极体效应、增益精度与负载极点

本模块把差分电压放大为差分电压，利用源极电阻退化改善线性度并设定跨导。相比未退化差分对，它降低跨导非线性和对晶体管参数的敏感度，代价是增益与电压余量。芯片中常用作模拟前端、ADC前置放大和连续时间滤波器的增益级。

状态：**SMIC18MMRF / TT / 1.8 V / 27°C，全部对应 nominal 原始指标通过**。只宣称原理图级 nominal；未执行其他PVT、失配或版图验证。审查PDF已逐页检查中文、图表和网表可读性。

[审查 PDF](../cases/04-gmr/review.pdf) · [精确电路](../cases/04-gmr/circuit.scs) · [验收合同](../cases/04-gmr/contract.json) · [实测结果](../cases/04-gmr/latest_results.json)

当前报告：**4页正文＋1页完整电路图，共5页**。下文历史交付记录中的页数对应当时的正文版本。

<!-- REPORT-MARKDOWN -->
## 可编辑报告与系统结构

[完整报告MD](../cases/04-gmr/review_report.md) · [对应PDF](../cases/04-gmr/review.pdf)
<!-- END-REPORT-MARKDOWN -->

## 设计与实测

输入对 n18 97.50/0.36 µm，每支目标250 µA、gm/ID=18；尾管由34.78/1 µm单元并联10个，参考管同W/L单个，gm/ID=16。源极退化每侧600 Ω，最终负载每侧1989 Ω，外部负载每侧1 pF。VCM保留端口，内部不取电。

实测：1 MHz差分增益2.002687 V/V，上端−3 dB带宽74.2695 MHz，总DC功耗0.958864 mW（包含50 µA参考）。3 MHz、100 mV差分峰值下，基波增益1.997394 V/V，正弦拟合SDR为63.8824 dB，残差RMS为90.3294 µV。全部原始nominal门槛通过。

## 工程认识

输入管实际gm=4.419 mS、gmb=1.073 mS，体效应不可忽略。有限ro之前的退化跨导近似gm/[1+(gm+gmb)RS]；只用gm/(1+gm·RS)会高估增益。输入源压0.3285 V，零体偏置LUT给出的尺寸须以实际OP确认；实测输入gm/ID=18.31。

初始RL=1900 Ω导致增益不足，调为1989 Ω提高增益并降低输出极点。但这两次旧运行的尾管写成W=347.8 µm单实例，超出PDK模型100 µm上限，故全部撤回。最终将尾管改为与参考完全同尺寸的10个并联单元，重新验证得到本页结果，日志无模型越界警告。旧数据保留在PDF迭代表中并明确标注失效。

尾管目标500 µA，实际482.70 µA；参考与输出镜管VDS不同，几何比并非精确电流比。尾节点仅0.1837 V、饱和余量81 mV，结论严格限定nominal。没有把这里的尾源余量外推到低压或PVT。

SDR沿用原测试的DC+sin+cos最小二乘拟合，窗口0.5–1.5 µs；它是指定刺激下的失真比，不含随机噪声。功耗检查保留VDD/VCM/VIN/VIP全部端口，避免用额外共模端口供电隐藏功耗。

[完整 LUT 查询](../cases/04-gmr/sizing.json)

## 复现与证据

[完整电路总图 SVG](../cases/04-gmr/schematic/full.svg) · [总图 PDF](../cases/04-gmr/schematic/full.pdf) · [1页电路分图](../cases/04-gmr/schematic/sheets.pdf) · [引脚与层次连接映射](../cases/04-gmr/schematic/connectivity.json) · [图纸审计](../cases/04-gmr/schematic_audit.json)

- [Spectre 运行记录](../runs/04/20260922T062025898382Z_gmr/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [工程脚本](../scripts) · [项目状态](../status.json)

原Sky130案例保持原样；本页是目标工艺实测的新记录。模型文件留在既有本地PDK目录，没有上传或修改。
