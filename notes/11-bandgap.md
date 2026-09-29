# 11 · 一阶带隙基准：温度补偿、真实启动与供电扰动

本模块利用双极管VBE与不同电流密度产生的ΔVBE相加，提供约1.2V的低温漂片上基准。相比单独使用VBE或电阻分压，闭环带隙可同时降低温度与供电变化的影响，代价是偏置电流、启动电路和滤波电容面积。它适合偏置、阈值及稳压器参考；本设计为高阻核心，直接驱动ADC采样负载还需要缓冲器。

状态：**SMIC18MMRF / TT / 1.8 V / 27°C，全部对应 nominal 原始指标通过**。只宣称原理图级 nominal；未执行其他PVT、失配或版图验证。审查PDF已逐页检查中文、图表和网表可读性。

[审查 PDF](../cases/11-bandgap/review.pdf) · [精确电路](../cases/11-bandgap/circuit.scs) · [验收合同](../cases/11-bandgap/contract.json) · [实测结果](../cases/11-bandgap/latest_results.json)

当前报告：**8页正文＋3页完整电路图，共11页**。下文历史交付记录中的页数对应当时的正文版本。

本项动态测试为1.8V/27°C/5pF；TT温漂保留1.8V下−40/0/27/60/100/125°C六点，线性调整率保留27°C下1.62/1.8/1.98V三点。全部14项适用原门槛通过。现用Spectre24.1，历史26项18.1结果保持原样。

<!-- REPORT-MARKDOWN -->
## 可编辑报告与系统结构

[完整报告MD](../cases/11-bandgap/review_report.md) · [对应PDF](../cases/11-bandgap/review.pdf)
<!-- END-REPORT-MARKDOWN -->

## 验收结果与测量条件

| 指标 | SMIC18实测 | 原门槛 |
|---|---:|---:|
| 标称VREF | 1.225072800V | 1.18–1.26V |
| 全部温度/电压表征点VREF | 1.223566970–1.225692025V | 1.18–1.26V |
| 标称 / 表征点最大VDD功耗 | 97.088078 / 124.189957µW | ≤150µW |
| 六温度点温漂 | 7.453174ppm/°C | ≤50ppm/°C |
| 线性调整率 | 4.468537mV/V | ≤20mV/V |
| 两种启动斜坡后的最大入窗时间 | 2.960µs | ≤10µs |
| 启动后10–20µs窗口最大中心偏差 | 5.072697mV | ≤40mV |
| 启动正过冲 | 0mV | ≤100mV |
| 启动峰值电流 | 0.579963mA | ≤1.5mA |
| 正向启动能量 | 2.326947nJ | ≤5nJ |
| 10Hz–100MHz最大电源耦合 | 0.0327892V/V | ≤0.2V/V |
| 10Hz–1MHz输出积分噪声 | 232.492752µVrms | ≤500µVrms |
| 双向供电阶跃最大输出偏移 | 10.900929mV | ≤100mV |
| 固定1mV带内的最坏建立时间 | 3.983µs | ≤10µs |
| 阶跃末端最大独立DC目标误差 | 12.028µV | ≤1mV |

表内标称值和表征极值分别展示；实际14项门槛及原始/10%/15%边界见PDF第一页和results中的gates。电压精度始终围绕1.22V，原误差±40mV；阶跃1mV判定带保持固定。所有项均达到原边界。

温漂沿原定义计算 `(max(VREF)-min(VREF))/(mean(VREF)*165)*1e6`，不是最佳拟合斜率，也不是连续温扫最大值。线性调整率为三个供电点的极差除以0.36V。最大电源耦合出现在约1.07152MHz。

## 核心电路与工艺迁移

Q0/Q1/QREF采用原厂 `npn18a4`，单位发射区为2×2µm，area为1/8/2；C/B/E/SUB四端均明确连接。Q0与Q1支路电流近似相等，Q1面积较大，使两支路产生ΔVBE。误差放大器调节公共PMOS栅极pctrl，使va≈vb；RPTAT承受ΔVBE，输出支路通过两倍镜像电流在RREF上产生PTAT电压，与QREF的VBE相加。

最终RPTAT和RREF均为 `rpposab_3t`，W=1µm、L分别为16.5µm和73.3µm，衬底接vss。偏置由八段W=1µm、L=162.5µm的同模型电阻串联，从VDD向二极管连接MNB供电，再以MTAIL镜出约三倍电流。没有理想电流源给DUT供偏置。

输出滤波CREF为原厂MIM，W=100µm、L=617.91967µm，名义60pF；CCOMP跨接pctrl与vss，W=50µm、L=10.298661µm，名义0.5pF。外部5pF仍在正式bench中，不计入DUT的27个实例。输出电容板面积约0.0618mm²；这是模型几何估计，未完成版图、DRC或寄生验证。

## gm/ID依据和实际工作点

全部12个MOS实例从已有SMIC18 TT LUT得到初始尺寸，L=1µm。镜与偏置查询VDS=0.9V，输入对及镜负载查询VDS=0.45V。精确查询、表文件哈希和取整前后尺寸见[sizing.json](../cases/11-bandgap/sizing.json)，原LUT快照保存在[lut](../cases/11-bandgap/lut)。独立gmoverid技能文件在迁移后缺失，本次沿用现有验证过的GmIdTable接口和目标PDK实测数据；没有修改原LUT。

| 角色 | 器件 | 模型 | 单位W/L（µm） | m | 初算gm/ID |
|---|---|---|---:|---|---:|
| 三路电流镜 | MP0/MP1/MP2 | p18 | 25.30/1 | 1/1/2 | 15 |
| 误差输入对 | MINA/MINB | n18 | 13.00/1 | 1/1 | 22 |
| 有源镜负载 | MPD/MPM | p18 | 12.52/1 | 1/1 | 16 |
| 电阻偏置及尾管 | MNB/MTAIL | n18 | 0.88/1 | 1/3 | 12 |
| 启动检测P管 | MPST | p18 | 2.82/1 | 1 | 12 |
| 启动检测及注入N管 | MNST/MSTART | n18 | 0.58/1 | 1/1 | 12 |

真实OP另存于results并列于PDF第三页。输入对实际gm/ID约22/V，其源节点约0.266V，体效应已包含在电路仿真中。启动检测器为大信号反相器，不能把MNST的稳态低VDS或MSTART截止误判为放大管不饱和。MSTART稳态注入约6.656pA；MPST/MNST仍有约2.38µA直通电流，已计入总VDD功耗。

## 启动与补偿的失败迭代

首版RREF=70.3µm、CCOMP=3pF、CREF=20pF时，VREF约1.20587V，温漂约51ppm/°C。RREF改为73.3µm后直流补偿通过，但原3pF/20pF电容组合仍产生约423mV启动过冲、0.438V/V电源耦合及约164mV向下供电阶跃偏移，不能交付。

最终保持MOS、供电、5pF外部负载和测量窗口不变，将CCOMP减至0.5pF、CREF增至60pF，完成全部动态测试。较大的输出电容提供滤波，也会增加启动能量和面积；不能只看低温漂就宣布带隙完成。失败与中间运行保留在[runs/11](../runs/11)。

两次启动均从零节点初始状态、`skipdc=yes`开始，VDD斜坡为1µs和10µs。入窗时间从斜坡结束计算；分别为2.960µs和0µs。过冲以斜坡结束20µs时输出为参考，正向能量积分 `VDD*max(0,-I(VDD))`。报告的零正过冲是保存的2ns时间网格上的测量结果。

供电在5µs从1.8V升至1.98V、15µs降至1.62V，边沿10ns，仿真至30µs；上升/下降输出峰值偏移为5.332849/10.900929mV。独立DC目标分别为1.225692025/1.224083351V。建立时间保守取最后越过1mV边界后的首个样点，得到2.803/3.983µs，并要求之后持续保持；没有用未收敛的瞬态尾值重定义目标。

## 证据与独立复核

最终五组运行使用同一电路，SHA-256为 `35c5a82bce4de256e274a922797be82a4e0696d81bbd295a1da8830424083029`。

- AC/噪声：[20260926T020532404519Z_acnoise](../runs/11/20260926T020532404519Z_acnoise)
- 1µs启动：[20260926T020533129366Z_startup1](../runs/11/20260926T020533129366Z_startup1)
- 供电阶跃：[20260926T020534268332Z_step](../runs/11/20260926T020534268332Z_step)
- 工作点、温度与供电扫：[20260926T020742387816Z_static](../runs/11/20260926T020742387816Z_static)
- 10µs启动：[20260926T020743564236Z_startup10](../runs/11/20260926T020743564236Z_startup10)

原instruction、参考网表、verifier及全部正式bench已只读复制到[source](../cases/11-bandgap/source)。通过内存格式适配，将实际Spectre波形交给未改写的上游analyze函数，并独立重算温漂及线性调整率，20项比较一致；没有调用原完整PVT评分函数后冒称全题通过。见[测量复核](../cases/11-bandgap/measurement-review.md)和[verification_audit.json](../cases/11-bandgap/verification_audit.json)。

图纸采用此前模块的完整晶体管图方案，共3张分图，覆盖12个MOS、3个NPN定义、10个电阻及2个MIM电容。独立解析源网表后核对27个实例、94个端子的型号、参数和连接，错误为0；体端/衬底端及全部内部网络均保留。PDF含8页正文和3页图纸，每页已实际渲染检查。见[连接审计](../cases/11-bandgap/schematic_independent_review.json)和[PDF目检记录](../cases/11-bandgap/pdf_provenance.json)。

本机实际使用已有Spectre24.1及Bridge虚拟环境；历史26项的Spectre18.1结果保持原样。五组最终Spectre日志均为0 errors、0 warnings，许可检查成功。现有Bridge在日志任意位置同时出现license和error时会误报license error，正常结束的“0 errors”也触发它。本次保留原始元数据，结合正常许可日志、完成状态及完整数据作独立判定；没有为了消除该文字修改Bridge或Spectre环境。

## 复现与交付边界

在工程根目录执行以下命令可重建；第一条实际运行会创建新的仿真目录。重建后需重新审查图纸和PDF，不能沿用本次目检状态。

```bash
source /home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/activate
python scripts/case11_bandgap.py
python scripts/case11_bandgap.py --extract
python scripts/schematic11.py
python scripts/audit11.py
python scripts/review11.py
```

已验证的电路、合同、模型与LUT保持哈希关联。生成脚本的交付快照见[implementation](../cases/11-bandgap/implementation)，用于保留来源；运行入口仍是工程根目录的scripts。

本次只完成第11项。用户明确授权仅本次对话更新知识库，知识笔记、报告和证据已从工作工程同步到`Analog-Circuit-Knowledge-Base/SMIC18-Benchmark-Reproduction`；长期AGENTS规则保持原样。未执行的项目包括非TT工艺角、热低压/冷高压动态配对、固定种子61000–61029失配、版图与PEX、输出缓冲及ADC采样负载驱动。

[完整 LUT 查询](../cases/11-bandgap/sizing.json)

## 复现与证据

[完整电路总图 SVG](../cases/11-bandgap/schematic/full.svg) · [总图 PDF](../cases/11-bandgap/schematic/full.pdf) · [3页电路分图](../cases/11-bandgap/schematic/sheets.pdf) · [引脚与层次连接映射](../cases/11-bandgap/schematic/connectivity.json) · [图纸审计](../cases/11-bandgap/schematic_audit.json)

- [Spectre 运行记录](../runs/11/20260926T020532404519Z_acnoise/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/11/20260926T020533129366Z_startup1/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/11/20260926T020534268332Z_step/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/11/20260926T020742387816Z_static/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [Spectre 运行记录](../runs/11/20260926T020743564236Z_startup10/run.json) · 原始输出（保留于原本地归档，未随仓库上传）
- [工程脚本](../scripts) · [项目状态](../status.json)

原Sky130案例保持原样；本页是目标工艺实测的新记录。模型文件留在既有本地PDK目录，没有上传或修改。
