# 第25题参考电路静态迁移分析

本报告只依据源 instruction、reference 晶体管网表、公开 AC/step bench 和既有 SMIC18 gm/ID LUT 作静态分析；没有运行任何仿真。尺寸与电压均为初值或关系式，不是 SMIC18 性能通过结论。已与 root 的初始架构核对，最终电路及验证由 root 完成。

源目录：`Analog-Circuit-Knowledge-Base/Analog-Design-Bench-V2-Lessons/sources/upstream/tasks/sky130-complementary-folded-cascode-ab-opamp-pvt`。

## 1. 保留的电路功能与合同要点

参考是互补 NMOS/PMOS 输入、双向尾电流转向、折叠汇流、Monticelli 并联浮动电流控制与共源推挽输出。其两条串联 RC 补偿接在 **vout–fp2** 与 **vout–fn2**，不是直接接到 gp/gn。gp 对 VDD、gn 对 VSS 各有 0.5 pF 局部阻尼；两条 15 kohm/4 pF 对称支路从输入引向 ntail，提高高频共模跟随。

源 reference 大量使用 LVT 输入/转向/PMOS 输出器件；迁移到正常阈值 n18/p18 时，原 W/L、偏置电平与异沟长电流比例不能直接照搬。原文件声明 Sky130 `w` 为总宽度、`nf` 为分指，不应再把其 W 乘 nf 来算总宽度。SMIC 大总宽度采用合法单元 W 和整数 m，n18/p18 每单元 W 不超过 100 um。

nominal 必须保留五个 AC 共模：0.1、0.2、0.9、1.6、1.7 V；AC 输出始终由 **DC-only** 反馈锁在 0.9 V。0.1/1.7 V 采用 80 dB/55°原门槛，其余三点 90 dB/60°，各点 UGB≥1 MHz，nominal 五点 max/min≤2。不能把 AC 输出也移到输入共模，否则把输出近轨问题混入输入共模测量。

4 pF 必须保留；tracking、step、noise、THD 使用并联 10 kohm 到 VDD/2。20 uA 从 VDD 注入 IREF，必须在 VDD 供电电流内。静态功耗同时覆盖 AC 工作点与闭环 0..VDD 扫描的最大值；step 最后 100 ns 的 **全区间极值** 都必须满足误差，不能只取最后一点。THD 的 0.9±0.4 V 会连续穿过输入交接区，比五点 AC 更容易暴露交接失真。源固定 mismatch seeds 属非nominal统计/失配范围，需在最终合同明确排除，不能把未测项写成通过。

## 2. 互补输入和电流转向的精确 KCL

记基本 NMOS 尾电流为 T_N、PMOS 尾电流为 T_P；NMOS 转向管 MN10 的电流为 S_N，PMOS 转向管 MP10 的电流为 S_P。P 转向镜 MP9/MP8 比为 α，N 转向镜 MN12/MN11 比为 β。输入对承载的总电流为：

\[
I_N=T_N+\beta S_P-S_N,\qquad I_P=T_P+\alpha S_N-S_P.
\]

低共模时 N 输入对失去余量，MN10 从 swnd 向 ntail 提供 S_N，P 转向镜将其送到 ptail，使 P 输入对电流增加；高共模时 P 输入对退出，MP10 通过 swpd 向 N 转向镜送 S_P，增加 N 输入电流。两管应在输入对衰减时逐步接手，不宜由理想比较器硬切换。

近似交接条件（必须含实际体效应与退化电阻压降）：

\[
V_{CM,N}\simeq V_{refn}+V_{GS,inN}-V_{GS,swN}+I_{N,side}R_N,
\]
\[
V_{CM,P}\simeq V_{refp}+|V_{SG,swP}|-|V_{SG,inP}|-I_{P,side}R_P.
\]

此外 N 路要求 `VCM−VGS,inN−I_side·RN ≥ VDSAT,tailN`；P 路要求 `VDD−VCM−|VSG,inP|−I_side·RP ≥ VDSAT,tailP`。正常 Vth 会改变这两条边界。vrefn/vrefp 应围绕实际输入与转向器件的 VGS 差设计，而非机械设置为 VDD/2。

N 输入体端接 VSS，源抬高时阈值增加；参考中的 P 输入体端接 ptail，源与 ptail 之间只有退化电阻，反向体偏通常较小。两边即使零体偏 LUT 上 gm/ID 相等，真实 gm/ID 和交接电平也不会严格相等。

root 的初值为 α=β=1，T_N=T_P=40 uA，重叠区每边输入管20 uA、L=1 um、gm/ID=22。重叠区每管 gm 约440 uS；保留 RN=500 ohm/RP=300 ohm 时，一阶有效差分总跨导约：

\[
G_{m,eff}\approx{440\over1+0.440\times0.500}+{440\over1+0.440\times0.300}\simeq750\ \mu S.
\]

这是忽略体效应、有限尾阻及折叠损耗的初值。弱/中反型下增加存活输入对的电流有利于保持 gm；在固定尺寸强反型近似中，双倍尾电流只带来 sqrt(2) 倍 gm，所以转向本身不保证严格恒 gm。应以五点 UGB 和连续交接区的线性表现验证。

## 3. 折叠电流与偏置电压

令每边底部 NMOS sink 电流为 B。对称输入时，N 折叠共栅支路电流为：

\[
K=B-I_P/2.
\]

K 流入左侧 ml 汇流节点；右侧它由 gp→gn 的浮动 AB 控制提供。上侧 PMOS 主镜每边电流为 `I_top=K+I_N/2`。因此保持 K 恒定的条件是：

\[
B=K_0+T_P/2+(\alpha/2)S_N-(1/2)S_P.
\]

**源参考的细节：** MP11/MP1=2.5，MP12/MP8=1，MN13/MN11=0.5，故 `B≈2.5IREF+S_N−0.5S_P`。源后续把 α 改为1.5，得到 `K≈2.5IREF−T_P/2+0.25S_N`，并非注释所说严格不变。若保留 α=1.5，应将补偿 S_N 的镜像系数设为0.75，不能继续误认为系数1抵消了全部变化。

**root 当前方案：** `B=60 uA+0.5S_N−0.5S_P`、T_P=40 uA、α=1，给出恒定 K=40 uA。中间输入共模时 I_top=60 uA；低/高共模极限它随 I_N/2 变化，约为40–80 uA。上 PMOS 主镜的电流并不恒定，应对这个区间保留饱和和速度余量。

关键内部电平关系是：

- `fn ≈ VCN−VGS,Ncas(VSB=fn)`；要求 `fn≥VDSAT,sink`，且 `min(ml,gn)−fn≥VDSAT,Ncas`。
- `fp ≈ VCP+|VSG,Pcas(VBS=VDD−fp)|`；要求 `VDD−fp≥VDSAT,Pmirror`，且 `fp−max(ml,gp)≥VDSAT,Pcas`。

不能只验证 N/P cascode 自己有电流，还要核对被其“顶住”的 sink 与主镜都保持余量。以 root 输出偏置下述 GN≈0.516 V、GP≈1.267 V 的零体偏初值估计，fn 可先落在约0.20–0.25 V；P 主镜 gm/ID=10 的 LUT VDSAT 约0.172 V，fp 初值约1.50–1.55 V较合理。**这不是推荐固定理想电压源**：VCN/VCP 仍需由真实复制偏置建立，并以带体效应工作点核查。不能把 VDSAT 用 Vov 或固定100 mV代替。

## 4. Monticelli 浮动 AB：体端与节点关系确认

参考两只浮动器件 N3、MP17 均传递 gp→gn 电流，彼此是并联支路：

\[
K=I_{ABN}+I_{ABP},\qquad V_{GP}>V_{GN}.
\]

两支路各对应一套二极管栈，电压恒等式为：

\[
V_{ABN}=V_{GS,Nupper}+V_{GS,Nlower},\quad V_{GN}=V_{ABN}-V_{GS,ABN},
\]
\[
V_{DD}-V_{ABP}=|V_{SG,Pbody}|+|V_{SG,Prail}|,\quad V_{GP}=V_{ABP}+|V_{SG,ABP}|.
\]

以下连接消除“上/下管”命名歧义：

| 器件 | D | G | S | B | 作用 |
|---|---|---|---|---|---|
| Nstack1 | vabn | vabn | x1 | VSS | 带体效应的 N 复制管 |
| Nstack2 | x1 | x1 | VSS | VSS | 复制 N 输出的零体偏 VGS |
| Nfloat | gp | vabn | gn | VSS | 匹配 Nstack1，预期 gn≈x1 |
| Nout | vout | gn | VSS | VSS | 匹配 Nstack2 的电流密度 |
| Pstack1 | vabp | vabp | y1 | VDD | 带体效应的 P 复制管 |
| Pstack2 | y1 | y1 | VDD | VDD | 复制 P 输出的零体偏 VSG |
| Pfloat | gn | vabp | gp | VDD | 匹配 Pstack1，预期 gp≈y1 |
| Pout | vout | gp | VDD | VDD | 匹配 Pstack2 的电流密度 |

**特别确认 PMOS：** Pstack1 的 bulk 接 VDD 正确；Pstack2 与 Pout 的 source/bulk 都接 VDD。当 Pfloat 与 Pstack1 的单位电流密度相等且 `gp≈y1` 时，两者既有相同 VSG，也有相同反向体偏 `VDD−source`。于是 `VDD−gp≈VDD−y1`，Pout 的 VSG 复制 Pstack2。若只把 Pstack1 bulk 改接 y1，零体偏 Pstack1 将无法复制 body=VDD 的 Pfloat，静态电流的偏置关系会被破坏。

root 的10 uA栈电流、m=1复制单元与每条浮动支路m=2/20 uA设计，在理想匹配下满足上述电流密度关系；两条浮动支路之和正好为 K=40 uA。下栈单元采用 L=1 um/gmID=14，输出相同单元 m=20，给出静态输出电流约200 uA。输出端中点无外部直流电流时，N/P 两管各约200 uA；供电中只计穿通的一个200 uA电流，不应把上拉和下拉相加为400 uA。

由下栈零体偏 LUT，GN≈0.51575 V、GP≈1.8−0.53310=1.26690 V，间隔约0.75115 V，给并联浮动管提供较充裕的 VDS。偏置栈上管与浮动管的体效应均使其所需 |VGS| 增加，故 **VABN不能简单取2×0.51575 V，VABP也不能简单取1.8−2×0.53310 V**。应让真实相同结构自动产生此体效应电平。实际电流还会因浮动管与二极管管不同的 VDS、输出负载和有限 ro 偏离理想镜像。

## 5. 既有 SMIC18 LUT 的数值初值

仅查询已有文件。以下为 TT/27°C、VBS=0、参考W=10 um；L1 使用 |VDS|=0.45 V，L4 使用项目现有补表 |VDS|=0.9 V。宽度是理论总宽度，实施时再量化和分配整数 m。

| 功能/模型 | L/um | gm/ID | 目标ID/uA | 总W/um | VGS幅值/V | VDSAT/V | fT/MHz | gm·ro |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| N 输入 n18 | 1 | 22 | 20 | 65.0073 | 0.40565 | 0.06252 | 232.27 | 264.51 |
| P 输入 p18 | 1 | 22 | 20 | 277.7180 | 0.42858 | 0.06463 | 54.37 | 454.55 |
| N AB下栈/输出单元 n18 | 1 | 14 | 10 | 4.4318 | 0.51575 | 0.12218 | 758.50 | 202.51 |
| P AB下栈/输出单元 p18 | 1 | 14 | 10 | 21.0465 | 0.53310 | 0.12414 | 164.69 | 317.54 |
| P 主镜 p18 | 4 | 10 | 60 | 232.0255 | 0.58264 | 0.17235 | 16.77 | 808.13 |
| N 长尾参考点 n18 | 4 | 15 | 40 | 84.4756 | 0.48806 | 0.11470 | 48.24 | 532.57 |

P 输入可用约69.42 um×m4，P主镜可用按10 uA单位约38.68 um×m6；两者均避免单元W超100 um。具体单位数由 root 的统一镜像单位规则决定。AB输出保留与下栈完全相同的 W/L、只变m。跨 L 共用栅压时，要反查 **同VGS** 的电流密度；例如 L4尾管若共享L1偏置参考，不能把 L4表内gmID=15与L1同gmID视为同栅压。

本表 L4 p18 的 fT 仅16.77 MHz是实质风险信号：并非直接等于电路极点，但大主镜门电容与 ml 汇流节点会限制非主极点。增大所有 L 以追90 dB会明显伤害 PM 和 UGB。先保留长主镜增益，再通过真实极点/环路证据决定哪类cascode或镜像器件需要缩短；不要把短沟LUT的高fT套到L4器件上。

查表文件与 SHA256：

- `gmoverid_smic18/lut/tt/n18_L1000nm_VDS0p450.json`：`9a855796a988085c4ea8631f0ed07dab1f85ce009a1f90fed978235ad0efe452`。
- `gmoverid_smic18/lut/tt/p18_L1000nm_VDS0p450.json`：`ef45dd88a2dfbe7f5b10b434d7d80bca24869fe6ec766cdb876fc4b1ed2976e8`。
- `smic18_benchmark_repro/lut_supplement/tt/n18_L4000nm_VDS0.900.json`：`1f39ea54bebfad40311239583f77e4c8ef824484edd63a9c585169c3dd0db010`。
- `smic18_benchmark_repro/lut_supplement/tt/p18_L4000nm_VDS0.900.json`：`bc683c432bec0eef7b3fc74ffec05a1fcf8f3326135cf1945f4ac9b5595bd4ed`。

## 6. 最优先的风险与验证顺序

1. **AB栈与浮动管的体效应/密度不一致。** 会直接改变两输出栅的间隔和静态穿通电流；首先核对gp≈y1、gn≈x1及K=I_ABN+I_ABP，随后验证静态功耗完整输入扫描。
2. **fold-sink转向比例不匹配。** 会使 AB 控制电流随共模移动，连带影响输出静态电流、UGB与失真。root当前恒K公式正确，应保留每个转向电流和fold KCL诊断。
3. **正常Vth加体效应造成输入/折叠节点失去余量。** 先检查五个共模的输入有效路径、tail headroom、fp/fn、ml/gp/gn，再解释增益。近轨退出的那一对截止正常，正在工作的路径不能同时失效。
4. **局部浮动AB的大信号松弛振荡。** 源reference专门缩小控制管并加CGP/CGN抑制此模式；全局小信号PM过关不代表大阶跃不会发生局部持续振荡。必须保留双向step及100 ns尾区间全极值，不能只看UGB/PM。
5. **长L主镜寄生与两条Miller支路的零点。** 原5 kohm/6 pF不能视作工艺无关最优值；补偿接折叠节点，不能直接使用简单两级Miller `R=1/gmout` 公式就声称消零。源对称15 kohm/4 pF尾部bootstrap也会改变MHz共模路径，CMRR@1 MHz应独立实测。
6. **输入交接、10 kohm负载和噪声/失真的联合权衡。** gmID22、大P输入面积有利于低电流和噪声，但增加输入/折叠寄生；源退化电阻有助于交接平滑且引入热噪声。0.2↔1.6 V step时负载约±70 uA，近轨tracking约±80 uA；Class-AB必须提供这些电流以及4 pF动态电流，不能只在无直流负载下检查输出。

最后的 PDF 晶体管级示意图应画出全部自定义 MOS、体端连接、转向镜比例、两套 AB 偏置堆栈、两只浮动管、两条 RC Miller 与输入尾部bootstrap；块图可辅助，但不能代替完整晶体管级电路。该示意图应来自最终实际网表，不能直接复用仍含Sky130 LVT及旧转向比例的原图。
