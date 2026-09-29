# 30 · 2.4GHz Gilbert混频器：转换增益、隔离与双音线性度

本模块用差分跨导级将射频电压变为电流，再由本振驱动的Gilbert开关四管换向，得到差频中频信号。双平衡结构有助于抑制本振和射频直通，源极退化改善线性度；代价是持续偏置功耗、转换增益和堆叠电压余量的权衡。芯片中可用于无线接收机下变频前端。

状态：**SMIC18MMRF / TT / 1.8 V / 27°C，全部对应 nominal 原始指标通过**。只宣称原理图级 nominal；未执行其他PVT、失配或版图验证。审查PDF已逐页检查中文、图表和网表可读性。

[审查 PDF](../cases/30-gilbert-mixer/review.pdf) · [精确电路](../cases/30-gilbert-mixer/circuit.scs) · [验收合同](../cases/30-gilbert-mixer/contract.json) · [实测结果](../cases/30-gilbert-mixer/latest_results.json)

当前报告：**6页正文＋2页完整电路图，共8页**。下文历史交付记录中的页数对应当时的正文版本。

<!-- REPORT-MARKDOWN -->
## 可编辑报告与系统结构

[完整报告MD](../cases/30-gilbert-mixer/review_report.md) · [对应PDF](../cases/30-gilbert-mixer/review.pdf)
<!-- END-REPORT-MARKDOWN -->

## 标称验收结果

SMIC18MMRF TT、1.8V、27°C。RF2.3/2.4/2.5GHz各执行平衡和2%RF/LO幅度、2°LO负相位偏差两种状态，LO=RF−0.2GHz；另外执行四组原双音/压缩激励。全部52个标量门槛及原7组检查达到原要求，无需放宽。[结果](../cases/30-gilbert-mixer/latest_results.json)保留原/10%/15%边界。

|指标|最差实测|原要求|
|---|---:|---:|
|转换增益/dB|5.425622|≥3|
|不平衡LO→IF/dB|-90.207919|≤-45|
|不平衡RF→IF/dB|-50.931063|≤-45|
|不平衡LO→RF/dB|-129.234901|≤-45|
|输出DC失衡/µV|30.219808|≤30000|
|输出共模/V|0.744375|≥0.45|
|到VDD余量/V|1.055323|≥0.2|
|供电功耗/mW|1.241590|≤2|
|带外杂散/dBc|-49.428152|≤-30|
|IIP3/dBm|-2.435600|≥-4|
|基波/IM3斜率|0.976558 / 3.254322|0.8–1.2 / 1.8–4|
|双音增益差/dB|1.359512|≤1.5|
|输入增大后的压缩/dB|1.019106|≤2|

极深隔离为无失配原理图的相消结果，不能据此声称芯片实现-129dB隔离；精度边界见下文。

|RF/GHz|条件|转换增益/dB|RF→IF/dB|杂散/dBc|
|---:|---|---:|---:|---:|
|2.3|平衡|5.426746|-66.874571|-50.118849|
|2.3|2%/2°|5.425622|-53.282982|-50.725400|
|2.4|平衡|5.493623|-66.717537|-49.741538|
|2.4|2%/2°|5.492599|-50.931063|-50.337589|
|2.5|平衡|5.554042|-66.633374|-49.428152|
|2.5|2%/2°|5.553117|-54.239580|-50.012184|

## 电路尺寸与实际余量

共9个真实常规n18、3个理想电阻和3个理想电容，15实例48端子。原题允许理想R/C，不采用LVT别名、理想放大器或受控源。

[gm/ID初算](../cases/30-gilbert-mixer/sizing.json)每单位50µA：偏置51.64/1µm、gm/ID18；RF管3.02/0.18µm、12；LO管11.52/0.18µm、18。两尾管和RF管各m6.5，目标325µA/侧；RF总宽19.63µm，LO四管各m6.5，总宽74.88µm。源间650Ω退化，输出负载两只3.3kΩ，内部75fF/腿及偏置1pF。

实际DC尾电流317.959607µA；RF管gm/ID9.9791，VDS0.123543V略低于VDSAT0.128448V。没有把初算饱和假设当成实际满足，也不宣称所有管子深饱和。LO管DC gm/ID20.4112；这些是静止LO诊断，实际转换、隔离和失真均由大信号LO瞬态验收。

测试台每腿50Ω源阻抗，输出每腿另接200fF。外部50µA参考从VDD取得，计入供电功耗；RF/LO理想驱动源功耗不在原供电指标中。布局、封装和走线寄生未加入。

## 频谱和线性度口径

[合同](../cases/30-gilbert-mixer/contract.json)固定RF每腿20mV峰值，LO每腿350mV峰值，共模0.9V。窗口5–15ns采用2048点矩形相干DFT，100MHz整数频点；杂散带25–175MHz及225MHz–3GHz，保留实际落入带内的谱线。增益/隔离以DUT端差分峰值计算，未使用理想源幅度替代实际端口电压。

双音2.4/2.45GHz、LO2.2GHz，每腿每音10/20mV；窗口10–30ns、2048点、50MHz谱间距。基波取200/250MHz平均，IM3取150/300MHz较大值，两输入幅度分别外推IIP3后取最小，以100Ω差分端口换算dBm。原始谱峰保留在[频谱记录](../cases/30-gilbert-mixer/spectral_records.json)。

低幅度基波37.914871/32.421566mV，IM3 102.167030/65.598958µV；高幅度基波74.545145/63.854871mV，IM3 974.767773/562.911668µV。斜率与两音增益差一起检查，约束偶然抵消。单音每腿20→80mV时增益5.506084→4.486977dB，压缩1.019106dB。IIP3是有限输入幅度外推，不是无限小信号导数。

原ngspice linearize在Spectre迁移中被明确2048点相干重采样替代；原时间窗口、频点、幅度和比值定义保持，未使用补零或谱窗掩盖泄漏。

## 数值和独立审查

[数值计划](../cases/30-gilbert-mixer/numerical_plan.json)先于精算冻结，maxstep3→1.5ps、reltol1e-6→1e-7，全10运行复算，[105对照](../cases/30-gilbert-mixer/numerical_confirmation.json)通过；最大原始幅度差4.612082µV<10µV，增益0.02dB、杂散0.15dB、IIP3 0.05dBm等固定容差均满足。确认文件初次写入遇到numpy布尔值序列化错误，修正写入后从已有两套运行生成；没有因此重跑电路、调整界限或改变实测结果。

隔离精度用线性泄漏比差≤2e-5确认；对每个实测泄漏比加2e-5仍满足原-45dB，因此支持门槛判断，但不支持极深相消数值的绝对物理精度。[独立审计](../cases/30-gilbert-mixer/verification_audit.json)另用直接复数DFT、逐区间积分和原7组检查函数复核105标量，深零点DFT与FFT用绝对线性比1e-12核对。20运行0错误、0警告，源资料/模型/LUT/输入快照哈希均保持。参见[测量复核](../cases/30-gilbert-mixer/measurement-review.md)和[独立明细](../cases/30-gilbert-mixer/independent_measurement_details.json)。

8页PDF为6页正文加2页完整图纸，全部实际逐页查看，[完整总图](../cases/30-gilbert-mixer/schematic/full.pdf)也已检查。电路SHA-256：e405fd9038a74aff43c984389a5b0cdfbc7eb96bc6f992c541b4bea568d89879。

工程根目录以既有Bridge Python依次运行scripts/case30_gilbert.py、confirm30.py、schematic30.py、audit30.py、review30.py；重新生成须再次实际查看。未验证其他PVT、原10个失配种子、噪声、版图及PEX。PDK、原LUT、Bridge和Spectre环境不变。

[完整 LUT 查询](../cases/30-gilbert-mixer/sizing.json)

## 复现与证据

[完整电路总图 SVG](../cases/30-gilbert-mixer/schematic/full.svg) · [总图 PDF](../cases/30-gilbert-mixer/schematic/full.pdf) · [2页电路分图](../cases/30-gilbert-mixer/schematic/sheets.pdf) · [引脚与层次连接映射](../cases/30-gilbert-mixer/schematic/connectivity.json) · [图纸审计](../cases/30-gilbert-mixer/schematic_audit.json)

- [Spectre 运行记录](../runs/30/20260928T182524916915Z_rf2.3_bal/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182528195467Z_rf2.3_imb/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182531414405Z_rf2.4_bal/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182534620719Z_rf2.4_imb/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182537803171Z_rf2.5_bal/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182541116910Z_rf2.5_imb/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182544470748Z_two_low/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182550377287Z_two_high/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182556400790Z_small/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/30/20260928T182602491674Z_large/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [工程脚本](../scripts) · [项目状态](../status.json)

原Sky130案例保持原样；本页是目标工艺实测的新记录。模型文件留在既有本地PDK目录，没有上传或修改。
