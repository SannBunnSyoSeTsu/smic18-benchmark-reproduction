# 41 · 低功耗Miller：级联镜、单位电流密度与供电抑制

本模块以较低静态功耗提供高增益和闭环电压放大。相比普通镜负载的两级Miller运放，第一级级联镜可提高输出阻抗并减弱供电耦合，代价是额外偏置与电压余量。芯片中可用作低功耗传感器读出、基准缓冲或误差放大器；接入具体系统后仍需按其负载和环路重新设计。

状态：**SMIC18MMRF / TT / 1.8 V / 27°C，全部对应 nominal 原始指标通过**。只宣称原理图级 nominal；未执行其他PVT、失配或版图验证。审查PDF已逐页检查中文、图表和网表可读性。

[审查 PDF](../cases/41-lowpower-miller/review.pdf) · [精确电路](../cases/41-lowpower-miller/circuit.scs) · [验收合同](../cases/41-lowpower-miller/contract.json) · [实测结果](../cases/41-lowpower-miller/latest_results.json)

当前报告：**5页正文＋2页完整电路图，共7页**。下文历史交付记录中的页数对应当时的正文版本。

<!-- REPORT-MARKDOWN -->
## 可编辑报告与系统结构

[完整报告MD](../cases/41-lowpower-miller/review_report.md) · [对应PDF](../cases/41-lowpower-miller/review.pdf)
<!-- END-REPORT-MARKDOWN -->

## 设计和完整nominal结果

输入n18为30.76/1 µm，目标30 µA/支、gm/ID=18；NMOS偏置单元3.22/1 µm、gm/ID=12，参考/尾源/输出电流源/共栅偏置分别m=5/6/14/1。所有PMOS使用同一3.14/0.36 µm单元、gm/ID=10；镜负载和共栅管各m=3，第二级m=14，偏置二极管m=1。补偿700 Ω串2 pF；外部负载始终2 pF。

原nominal全部通过：10 Hz增益88.5831 dB、UGB38.0852 MHz、相位裕量64.5454°、总功耗471.164 µW（含50 µA参考）。静态单位反馈输出误差16.054 µV。噪声增益20的闭环带宽2.14287 MHz；10 Hz至该频率输入积分噪声23.2385 µVrms。1 kHz/1 MHz闭环PSRR+为90.8303/32.4615 dB，1 kHz CMRR89.7416 dB。

0.3–1.5 V整个原扫描范围都满足20 mV连续跟踪条件，仅声明1.2 Vpp，不外推到扫描边界外。100 mV上/下阶跃建立15.9493/17.4775 ns，最坏终值误差16.1346 µV（0.0161346%）。0.5 V上/下阶跃压摆率28.7094/26.5581 V/µs。频率、时序、负载、双向动态检查均保留原任务口径。

## 单元电流密度和漏压对齐

第二级PMOS与第一级镜负载使用相同W/L单位，通过m分别承载约140 µA和30 µA。相近的单位电流密度使其VSG相近，输入两管漏压1.17225/1.17703 V仅相差4.774 mV。本次确定性系统失调很小；没有执行MC，不能由此宣称随机失调同样只有16 µV。

级联PMOS镜提高第一级阻抗并抑制供电扰动。22 kΩ源端电阻让偏置二极管的源极1.57631 V，与两个共栅管的源极1.57599/1.57603 V接近，因而体偏置也接近。实际偏置VBP=0.88527 V。

## 饱和余量和补偿的边界

共栅支路消耗额外电压空间：上层MPM的VSD=223.97 mV、VSDSAT=179.04 mV，余量只有44.93 mV。nominal所有相关管处在饱和区，但这不构成跨PVT稳健性的证据。高增益、高PSRR和低失调都应与这个余量一起记录。

第二级实际gm=1.42786 mS，1/gm=700.35 Ω，接近串联补偿电阻700 Ω。近似抵消前馈零点是选值依据；最终仍验收实际复数环路，确认相位裕量64.55°和无0 dB回穿。

## 测量可比性

沿用原题电压注入T=−Vout/Vinn，不能混用第44题的双注入定义。闭环PSRR/CMRR均为指定单位注入下的−20log10|Vout|。噪声积分终点来自独立噪声增益20的AC测试。压摆刺激在10/71 ns开始，保留本题时序，不直接复用第16题较长时序。三次最终Spectre运行没有模型尺寸越界；5页PDF已逐页审查。

[完整 LUT 查询](../cases/41-lowpower-miller/sizing.json)

## 复现与证据

[完整电路总图 SVG](../cases/41-lowpower-miller/schematic/full.svg) · [总图 PDF](../cases/41-lowpower-miller/schematic/full.pdf) · [2页电路分图](../cases/41-lowpower-miller/schematic/sheets.pdf) · [引脚与层次连接映射](../cases/41-lowpower-miller/schematic/connectivity.json) · [图纸审计](../cases/41-lowpower-miller/schematic_audit.json)

- [Spectre 运行记录](../runs/41/20260922T065822810909Z_static/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/41/20260922T065823009181Z_noise/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/41/20260922T065823206274Z_dynamic/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [工程脚本](../scripts) · [项目状态](../status.json)

原Sky130案例保持原样；本页是目标工艺实测的新记录。模型文件留在既有本地PDK目录，没有上传或修改。
