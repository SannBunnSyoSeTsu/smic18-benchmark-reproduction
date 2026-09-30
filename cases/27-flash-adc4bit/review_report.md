# 27-flash-adc4bit 审查报告

PDF由Python/Matplotlib排版生成。此Markdown从同一报告文本、表格和网表保存，便于编辑；它不是PDF编译输入。完整生成脚本随implementation目录保存。

<!-- SYSTEM-BLOCK-DIAGRAM -->
## 系统框图

比较器、锁存和编码均在DUT；输入、参考和时钟属于固定测试端口。

实线表示信号或能量通路，虚线表示时钟、控制或偏置。DUT框外为外部端口或测试夹具；精确端子连接见后附基本电路图。

```mermaid
flowchart TB
    subgraph DUT["DUT"]
        direction TB
        SH["共享差分采样保持"]
        REFS["15个电阻参考阈值"]
        CMP["15路动态比较器"]
        LAT["HD锁存温度计码"]
        ENC["HD编码与4位输出"]
    end
    VIN["模拟输入"]
    REF["外部参考电压"]
    CLK["外部时钟"]
    OUT["数字读数"]
    REF --> REFS
    REFS -->|"阈值"| CMP
    CMP -->|"判决"| LAT
    LAT -->|"温度计码"| ENC
    ENC -->|"二进制码"| OUT
    CLK -.->|"评估 / 复位"| CMP
    VIN --> SH
    SH -->|"保持信号"| CMP
    CLK -.->|"采样相"| SH
```

[独立Mermaid源文件](system_block_diagram.mmd) · [框图SVG](markdown_assets/system-block.svg)
<!-- END-SYSTEM-BLOCK-DIAGRAM -->

## 27 | 4位差分Flash ADC审查

本模块在采样结束时并行比较差分输入与15个参考阈值，把温度计码编码为四位二进制。共享差分保持电容隔离转换期间的输入变化，动态比较器减少静态偏置电流，HD锁存与异或树保存和编码判决；代价是比较器、参考负载、采样电容与回踢随位数增长。芯片中可用于高速低位数ADC和流水线子ADC。

结论：SMIC18MMRF / TT / 1.8V / 27°C，全部原始标称电气指标通过。

50MS/s、四位差分输入，正式验收包含完整16码中心、90点线性度斜坡和32点动态记录。下表采用最终精算结果。

| 指标 | 实测 | 原指标 | 10% | 15% |
| --- | --- | --- | --- | --- |
| SNDR/dB | 26.2773 | ≥22 | ≥21.0849 | ≥20.5884 |
| SFDR/dB | 29.5314 | ≥26 | ≥25.0849 | ≥24.5884 |
| 供电功耗/mW | 2.42199 | ≤5 | ≤5.5 | ≤5.75 |
| INL/LSB | 0.0843373 | ≤0.5 | ≤0.55 | ≤0.575 |
| DNL/LSB | 0.156627 | ≤0.5 | ≤0.55 | ≤0.575 |

16码中心零错误、零缺码；90点斜坡覆盖全部16码、恰好15个相邻上跳，单调性通过。输出在每个评分时刻满足低≤0.36V或高≥1.44V，功能检查不放宽。

原题仅要求确定性TT标称。无器件噪声、失配或亚稳态统计；本报告的SNDR为原码序的确定性谱指标，不代表实测有效位数或芯片良率。

## 器件初算与完整结构

共享差分保持、15个StrongARM、15个SR和HD异或编码。

| 角色 | 模型 | 单元W/L um | gm/ID初算 | 电流初算/uA |
| --- | --- | --- | --- | --- |
| input | n18 | 9.02/0.18 | 14 | 100 |
| tail | n18 | 8.14/0.18 | 8 | 300 |
| latch_n | n18 | 4.06/0.18 | 10 | 100 |
| latch_p | p18 | 6.12/0.18 | 10 | 50 |
| sample_n | n18 | 54.26/0.18 | 8 | 2000 |
| sample_p | p18 | 160.28/0.18 | 8 | 2000 |

模拟比较器的输入对、时钟尾管和交叉再生对由目标工艺gm/ID LUT初算；复位、放电和再生期间的瞬时gm/ID并不恒定。所有数字逻辑使用原厂INHDV1/16、NAND2HDV1、XOR2HDV1，保留原CDL器件与井端。

差分保持电容每侧20pF；每个比较器输入由两只200kΩ电阻混合保持输入与反向参考阈值。参考梯16×100Ω。采样NMOS和PMOS各拆为四只等效并联，m=4且单管W为表中总宽的1/4，避免超过模型宽度范围。

完整图纸为16页，覆盖156个定义实例、637个端子，展开308个叶实例。模拟子电路全展开，HD保持原厂叶单元边界及实际电源/体端；图纸核对不等同于版图LVS。

## 传输、线性度与频谱

图中样本均来自最终精算的原始Spectre结果。

完整16码中心、90点静态斜坡、32码动态记录和原评分频谱。

![完整16码中心、90点静态斜坡、32码动态记录和原评分频谱。](markdown_assets/figure-03-01.png)

[查看矢量图](markdown_assets/figure-03-01.svg)

动态信号7.8125MHz，差分峰值1.7V，共模0.9V。图中INL/DNL来自离散斜坡阈值，精度受其采样网格限制。

## 固定条件与测量口径

50MS/s；clock=0采样、上升沿结束采样、clock=1转换。

外部时钟20ns周期，1ps延时，20ps升降沿、9.96ns高电平宽度，经50Ω源阻抗驱动；四位输出各10fF。全部判码在转换边沿后9ns，门限0.9V。DUT内部只使用原生MOS、理想正值R/C与原厂HD单元。

传输测试在69ns起连续16点判码；静态差分斜坡−1.7→+1.7V历时1.8us，在9ns起每20ns读取90点。每个阈值取发生相邻上跳的两次输入读数中点，首末阈值拟合端点LSB，之后计算INL和相邻间距DNL。

动态测试从69ns读取32点，矩形窗、去DC、基波为第5频点。SNDR分母为第1–15点中除基波外的全部功率；SFDR为最大非基波功率。原题不计Nyquist频点，此口径明确保留，未删除其他谐波或邻频点。

供电功率为60–720ns时间加权均值 −1.8×[I(VDD)+I(VREFP)]，实测2.421988mW。外部时钟净供能另列0.217053mW；输入理想驱动功耗不在原供电上限内，不能据此声称完整系统功耗。

使用源任务正式bench及原Python测量函数，未以公开短记录代替正式验收；本次输出电平有效性检查额外保留为非放宽功能约束。

## 数值确认、独立审计与可编辑材料

PDF正文和Markdown从同一文本/表格/网表保存；图纸附后。

maxstep100→50ps，reltol1e−5→1e−6；事先固定的15项差异界限全部通过，三组全部转换码一致。最大功率差0.0145549uW，小于预定3uW。没有通过放宽原刺激、负载或采样窗来取得结果。

独立审计直接把原始Spectre轨迹交给未修改的原Python分析函数，重算传输、端点线性度、递归DFT和截窗能量；15项数值交叉核对及原6项电气检查通过。6次基线/精算均实际0错误，日志保留30条警告并注明类型；不声称零警告。

原Sky130网表语法检查器不能解析原生Spectre/HD；本次单独验证所有允许叶模型、完整接口、模型尺寸、HD原CDL哈希及图纸端子覆盖，只将该原生结构合格结果提供给原电气评分函数，未伪称运行原Sky130语法检查器。

case27_flash_adc.py → confirm27.py → schematic27.py → audit27.py → review27.py。保留source原始资料、全部码流/频谱、数值计划、网表快照、模型和LUT哈希、HD源块、PDF、review_report.md、knowledge.md及生成脚本。更新报告后需要重新实际逐页查看。

电路SHA-256：
3b70836f6c1c5d9bd5affd551b9be5fa04763a168d4a5a936beba835fb24c620

## 完整网表与电路图

[Spectre 网表](circuit.scs) · [全部分图 PDF](schematic/sheets.pdf) · [电路总图](schematic/full.svg) · [端子连接](schematic/connectivity.json)

<details>
<summary>展开完整 Spectre 网表</summary>

```spectre
simulator lang=spectre
subckt fa_comp (clk vinp vinn outp outn vdd vss)
MTAIL (tail clk vss vss) n18 w=8.14u l=.18u
MIN1 (dx vinp tail vss) n18 w=9.02u l=.18u
MIN2 (dy vinn tail vss) n18 w=9.02u l=.18u
MNL1 (outn outp dx vss) n18 w=4.06u l=.18u
MNL2 (outp outn dy vss) n18 w=4.06u l=.18u
MPL1 (outn outp vdd vdd) p18 w=6.12u l=.18u
MPL2 (outp outn vdd vdd) p18 w=6.12u l=.18u
MPC1 (outn clk vdd vdd) p18 w=6.12u l=.18u
MPC2 (outp clk vdd vdd) p18 w=6.12u l=.18u
MPC3 (dx clk vdd vdd) p18 w=6.12u l=.18u
MPC4 (dy clk vdd vdd) p18 w=6.12u l=.18u
ends fa_comp
subckt fa_sr (sn rn q qb vdd vss)
XG1 (sn qb q vdd vss vdd vss) NAND2HDV1
XG2 (rn q qb vdd vss vdd vss) NAND2HDV1
ends fa_sr
subckt fa_sample (a b en enb vdd vss)
MN (a en b vss) n18 w=13.565u l=.18u m=4
MP (a enb b vdd) p18 w=40.07u l=.18u m=4
ends fa_sample
subckt flash_adc_4bit (clk dout3 dout2 dout1 dout0 vss vdd vinn vinp vrefn vrefp)
XCLK (clk clks vdd vss vdd vss) INHDV16
XSP (vinp vhp clks clk vdd vss) fa_sample
XSN (vinn vhn clks clk vdd vss) fa_sample
CHP (vhp s8) capacitor c=20p
CHN (vhn s8) capacitor c=20p
RL1 (s1 vrefn) resistor r=100
RL2 (s2 s1) resistor r=100
RL3 (s3 s2) resistor r=100
RL4 (s4 s3) resistor r=100
RL5 (s5 s4) resistor r=100
RL6 (s6 s5) resistor r=100
RL7 (s7 s6) resistor r=100
RL8 (s8 s7) resistor r=100
RL9 (s9 s8) resistor r=100
RL10 (s10 s9) resistor r=100
RL11 (s11 s10) resistor r=100
RL12 (s12 s11) resistor r=100
RL13 (s13 s12) resistor r=100
RL14 (s14 s13) resistor r=100
RL15 (s15 s14) resistor r=100
RL16 (vrefp s15) resistor r=100
R1pA (vhp vp1) resistor r=200000
R1pB (s15 vp1) resistor r=200000
R1nA (vhn vn1) resistor r=200000
R1nB (s1 vn1) resistor r=200000
XC1 (clk vp1 vn1 cp1 cn1 vdd vss) fa_comp
XS1 (cn1 cp1 q1 qb1 vdd vss) fa_sr
R2pA (vhp vp2) resistor r=200000
R2pB (s14 vp2) resistor r=200000
R2nA (vhn vn2) resistor r=200000
R2nB (s2 vn2) resistor r=200000
XC2 (clk vp2 vn2 cp2 cn2 vdd vss) fa_comp
XS2 (cn2 cp2 q2 qb2 vdd vss) fa_sr
R3pA (vhp vp3) resistor r=200000
R3pB (s13 vp3) resistor r=200000
R3nA (vhn vn3) resistor r=200000
R3nB (s3 vn3) resistor r=200000
XC3 (clk vp3 vn3 cp3 cn3 vdd vss) fa_comp
XS3 (cn3 cp3 q3 qb3 vdd vss) fa_sr
R4pA (vhp vp4) resistor r=200000
R4pB (s12 vp4) resistor r=200000
R4nA (vhn vn4) resistor r=200000
R4nB (s4 vn4) resistor r=200000
XC4 (clk vp4 vn4 cp4 cn4 vdd vss) fa_comp
XS4 (cn4 cp4 q4 qb4 vdd vss) fa_sr
R5pA (vhp vp5) resistor r=200000
R5pB (s11 vp5) resistor r=200000
R5nA (vhn vn5) resistor r=200000
R5nB (s5 vn5) resistor r=200000
XC5 (clk vp5 vn5 cp5 cn5 vdd vss) fa_comp
XS5 (cn5 cp5 q5 qb5 vdd vss) fa_sr
R6pA (vhp vp6) resistor r=200000
R6pB (s10 vp6) resistor r=200000
R6nA (vhn vn6) resistor r=200000
R6nB (s6 vn6) resistor r=200000
XC6 (clk vp6 vn6 cp6 cn6 vdd vss) fa_comp
XS6 (cn6 cp6 q6 qb6 vdd vss) fa_sr
R7pA (vhp vp7) resistor r=200000
R7pB (s9 vp7) resistor r=200000
R7nA (vhn vn7) resistor r=200000
R7nB (s7 vn7) resistor r=200000
XC7 (clk vp7 vn7 cp7 cn7 vdd vss) fa_comp
XS7 (cn7 cp7 q7 qb7 vdd vss) fa_sr
R8pA (vhp vp8) resistor r=200000
R8pB (s8 vp8) resistor r=200000
R8nA (vhn vn8) resistor r=200000
R8nB (s8 vn8) resistor r=200000
XC8 (clk vp8 vn8 cp8 cn8 vdd vss) fa_comp
XS8 (cn8 cp8 q8 qb8 vdd vss) fa_sr
R9pA (vhp vp9) resistor r=200000
R9pB (s7 vp9) resistor r=200000
R9nA (vhn vn9) resistor r=200000
R9nB (s9 vn9) resistor r=200000
XC9 (clk vp9 vn9 cp9 cn9 vdd vss) fa_comp
XS9 (cn9 cp9 q9 qb9 vdd vss) fa_sr
R10pA (vhp vp10) resistor r=200000
R10pB (s6 vp10) resistor r=200000
R10nA (vhn vn10) resistor r=200000
R10nB (s10 vn10) resistor r=200000
XC10 (clk vp10 vn10 cp10 cn10 vdd vss) fa_comp
XS10 (cn10 cp10 q10 qb10 vdd vss) fa_sr
R11pA (vhp vp11) resistor r=200000
R11pB (s5 vp11) resistor r=200000
R11nA (vhn vn11) resistor r=200000
R11nB (s11 vn11) resistor r=200000
XC11 (clk vp11 vn11 cp11 cn11 vdd vss) fa_comp
XS11 (cn11 cp11 q11 qb11 vdd vss) fa_sr
R12pA (vhp vp12) resistor r=200000
R12pB (s4 vp12) resistor r=200000
R12nA (vhn vn12) resistor r=200000
R12nB (s12 vn12) resistor r=200000
XC12 (clk vp12 vn12 cp12 cn12 vdd vss) fa_comp
XS12 (cn12 cp12 q12 qb12 vdd vss) fa_sr
R13pA (vhp vp13) resistor r=200000
R13pB (s3 vp13) resistor r=200000
R13nA (vhn vn13) resistor r=200000
R13nB (s13 vn13) resistor r=200000
XC13 (clk vp13 vn13 cp13 cn13 vdd vss) fa_comp
XS13 (cn13 cp13 q13 qb13 vdd vss) fa_sr
R14pA (vhp vp14) resistor r=200000
R14pB (s2 vp14) resistor r=200000
R14nA (vhn vn14) resistor r=200000
R14nB (s14 vn14) resistor r=200000
XC14 (clk vp14 vn14 cp14 cn14 vdd vss) fa_comp
XS14 (cn14 cp14 q14 qb14 vdd vss) fa_sr
R15pA (vhp vp15) resistor r=200000
R15pB (s1 vp15) resistor r=200000
R15nA (vhn vn15) resistor r=200000
R15nB (s15 vn15) resistor r=200000
XC15 (clk vp15 vn15 cp15 cn15 vdd vss) fa_comp
XS15 (cn15 cp15 q15 qb15 vdd vss) fa_sr
XE0_0_0 (q1 q2 b0l0n0 vdd vss vdd vss) XOR2HDV1
XE0_0_2 (q3 q4 b0l0n1 vdd vss vdd vss) XOR2HDV1
XE0_0_4 (q5 q6 b0l0n2 vdd vss vdd vss) XOR2HDV1
XE0_0_6 (q7 q8 b0l0n3 vdd vss vdd vss) XOR2HDV1
XE0_0_8 (q9 q10 b0l0n4 vdd vss vdd vss) XOR2HDV1
XE0_0_10 (q11 q12 b0l0n5 vdd vss vdd vss) XOR2HDV1
XE0_0_12 (q13 q14 b0l0n6 vdd vss vdd vss) XOR2HDV1
XE0_1_0 (b0l0n0 b0l0n1 b0l1n0 vdd vss vdd vss) XOR2HDV1
XE0_1_2 (b0l0n2 b0l0n3 b0l1n1 vdd vss vdd vss) XOR2HDV1
XE0_1_4 (b0l0n4 b0l0n5 b0l1n2 vdd vss vdd vss) XOR2HDV1
XE0_1_6 (b0l0n6 q15 b0l1n3 vdd vss vdd vss) XOR2HDV1
XE0_2_0 (b0l1n0 b0l1n1 b0l2n0 vdd vss vdd vss) XOR2HDV1
XE0_2_2 (b0l1n2 b0l1n3 b0l2n1 vdd vss vdd vss) XOR2HDV1
XE0_3_0 (b0l2n0 b0l2n1 b0l3n0 vdd vss vdd vss) XOR2HDV1
XB0a (b0l3n0 outb0 vdd vss vdd vss) INHDV1
XB0b (outb0 dout0 vdd vss vdd vss) INHDV1
XE1_0_0 (q2 q4 b1l0n0 vdd vss vdd vss) XOR2HDV1
XE1_0_2 (q6 q8 b1l0n1 vdd vss vdd vss) XOR2HDV1
XE1_0_4 (q10 q12 b1l0n2 vdd vss vdd vss) XOR2HDV1
XE1_1_0 (b1l0n0 b1l0n1 b1l1n0 vdd vss vdd vss) XOR2HDV1
XE1_1_2 (b1l0n2 q14 b1l1n1 vdd vss vdd vss) XOR2HDV1
XE1_2_0 (b1l1n0 b1l1n1 b1l2n0 vdd vss vdd vss) XOR2HDV1
XB1a (b1l2n0 outb1 vdd vss vdd vss) INHDV1
XB1b (outb1 dout1 vdd vss vdd vss) INHDV1
XE2_0_0 (q4 q8 b2l0n0 vdd vss vdd vss) XOR2HDV1
XE2_1_0 (b2l0n0 q12 b2l1n0 vdd vss vdd vss) XOR2HDV1
XB2a (b2l1n0 outb2 vdd vss vdd vss) INHDV1
XB2b (outb2 dout2 vdd vss vdd vss) INHDV1
XB3a (q8 outb3 vdd vss vdd vss) INHDV1
XB3b (outb3 dout3 vdd vss vdd vss) INHDV1
ends flash_adc_4bit
```

</details>

![电路分图 1](schematic/sheet-1.png)

![电路分图 2](schematic/sheet-2.png)

![电路分图 3](schematic/sheet-3.png)

![电路分图 4](schematic/sheet-4.png)

![电路分图 5](schematic/sheet-5.png)

![电路分图 6](schematic/sheet-6.png)

![电路分图 7](schematic/sheet-7.png)

![电路分图 8](schematic/sheet-8.png)

![电路分图 9](schematic/sheet-9.png)

![电路分图 10](schematic/sheet-10.png)

![电路分图 11](schematic/sheet-11.png)

![电路分图 12](schematic/sheet-12.png)

![电路分图 13](schematic/sheet-13.png)

![电路分图 14](schematic/sheet-14.png)

![电路分图 15](schematic/sheet-15.png)

![电路分图 16](schematic/sheet-16.png)
