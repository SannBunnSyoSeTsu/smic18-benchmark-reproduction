# 42-sar-adc6bit 审查报告

PDF由Python/Matplotlib排版生成。此Markdown从同一报告文本、表格和网表保存，便于编辑；它不是PDF编译输入。完整生成脚本随implementation目录保存。

<!-- SYSTEM-BLOCK-DIAGRAM -->
## 系统框图

CDAC、比较器及异步握手均为实际DUT；内部比较时钟由有效判决推进，不能画成外部理想逐位控制。

实线表示信号或能量通路，虚线表示时钟、控制或偏置。DUT框外为外部端口或测试夹具；精确端子连接见后附基本电路图。

```mermaid
flowchart TB
    subgraph DUT["DUT"]
        direction TB
        S["差分自举采样"]
        D["双支路电容DAC"]
        C["动态比较器"]
        L["HD异步控制与判决寄存"]
        R["完成后锁存6位输出"]
    end
    VIN["差分输入"]
    REF["参考电压"]
    CLK["外部采样时钟"]
    OUT["数字读数"]
    VIN --> S
    S -->|"采样电荷"| D
    REF --> D
    D -->|"差分余量"| C
    C -->|"判决 / valid"| L
    L -.->|"逐位试探"| D
    L -.->|"内部比较时钟"| C
    L -.->|"EOC / 判决位"| R
    R --> OUT
    CLK -.->|"采样"| S
    CLK -.->|"复位 / 转换启动"| L
```

[独立Mermaid源文件](system_block_diagram.mmd) · [框图SVG](markdown_assets/system-block.svg)
<!-- END-SYSTEM-BLOCK-DIAGRAM -->

## 42 | 6位异步SAR ADC

本模块以差分自举采样、电容DAC和动态比较器完成六位逐次逼近转换。异步HD控制器依次保存判决，转换结束再更新输出；自举采样改善宽输入摆幅下的导通能力，代价是额外存储电容、开关应力和时序约束。芯片中可用于中低分辨率高速采集与混合信号接口，噪声、匹配和参考驱动仍需单独验证。

结论：TT / 1.8V / 27°C，完整原始标称指标通过。

100MS/s，两组各64个乱序码中心包含采样结束后的诱骗输入。两组均零错误，所有判码电平有效；时钟50Ω源阻抗、10fF/位输出负载保持原题。

| 指标 | 实测 | 原指标 | 10% | 15% |
| --- | --- | --- | --- | --- |
| SNDR/dB | 38.29858 | ≥35 | ≥34.0849 | ≥33.5884 |
| 归一化ENOB/bit | 6.173151 | >5.9 | >5.31 | >5.015 |
| 最坏单记录功耗/mW | 1.709667 | <3 | <3.3 | <3.45 |

动态64码由四个独立16码分段按原顺序组装；四段分别使用原相位延续。静态两种64码次序也各分四段，保留前一码的输入历史。

归一化ENOB是原验收公式的确定性码序指标：以理想满量程谱功率除以实测非基波功率换算。有限相干码序可以得到大于6的值；这不代表ADC产生超过6位的信息，也不证明含热噪声、失配后的有效分辨率。

## gm/ID初算、采样与异步控制

原生模拟MOS与正值理想电容；全部数字单元保持原厂HD尺寸。

| 角色 | 模型 | 单位W/L um | gm/ID | 初算Id/uA |
| --- | --- | --- | --- | --- |
| input | n18 | 9.02/0.18 | 14.0 | 100 |
| tail | n18 | 8.14/0.18 | 8.0 | 300 |
| latch_n | n18 | 4.06/0.18 | 10.0 | 100 |
| latch_p | p18 | 6.12/0.18 | 10.0 | 50 |
| sample_n | n18 | 6.78/0.18 | 8.0 | 250 |
| sample_p | p18 | 20.04/0.18 | 8.0 | 250 |
| dac_n | n18 | 0.68/0.18 | 8.0 | 25 |
| dac_p | p18 | 2/0.18 | 8.0 | 25 |
| boot_n | n18 | 5.1/0.18 | 8.0 | 200 |
| boot_p | p18 | 14.8/0.18 | 8.0 | 200 |

实际比较器宽度为表中初算的0.25倍；CDAC单位电容30fF，二进制权重扩展，顶板dummy为10fF。异步返回路径电容10fF。gm/ID用于初始选型，动态再生过程的瞬时gm/ID不恒定。

六位采样采用1.5pF自举存储及原生保护管；比较器缩小至初算宽度的1/4以减轻回踢。VALID使用OR2HDV4，序列链使用DRNQHDV2，判决和输出仍用原厂DRNQ/DQ单元。未作寿命或跨PVT应力签核。

## 双次序保持检查与动态频谱

来自最终Spectre精算；频谱从-80dBc基线向上画。

两种完整64码次序、动态码序与单边频谱。低于-80dBc的谱线仅在显示时截底；评分使用未经截断的原始功率。

![两种完整64码次序、动态码序与单边频谱。低于-80dBc的谱线仅在显示时截底；评分使用未经截断的原始功率。](markdown_assets/figure-03-01.png)

[查看矢量图](markdown_assets/figure-03-01.svg)

Nyquist点按原评分计半权功率；图中展示其原单边DFT幅值，未用于改变验收结果。

## 固定刺激、读出与能量口径

原始时钟、码次序、诱骗输入和功率窗口均保留。

采样时钟周期10ns、延时1ps、上升/下降20ps、高电平宽1.98ns。输入共模0.9V，动态每侧峰值0.85V；VREFP=1.8V、VREFN=0V。采样后2.20–2.25ns把输入换成错误码中心，验证实际保持。

六位每段静态从19ns起读16码，动态从29ns起读16码，每10ns一次。四段动态构成bin31的64点码序；每段功率窗口19.5–179.5ns。原评分取四段功率均值，本次额外要求最坏单段也小于3mW。

能量由VDD、VREFP、VCM、VINP、VINN及VCLKS六个源的有符号电压×电流相加，再截取原窗口作时间加权积分。包括理想输入源与时钟净供能；回收能量按原题有符号口径保留。没有仅统计核心VDD来压低功耗。

矩形窗去DC，取第1至N/2-1点中除基波以外全部功率，并加Nyquist点的一半；未排除谐波或邻频点。P_FS=(N×2^bits/4)²，归一化ENOB=[10log10(P_FS/P_noise)-1.76]/6.02。

输出低电平≤0.36V、高电平≥1.44V，完整码序与数字电平检查不可随10%/15%档放宽。

## 数值确认、独立审查与可复现材料

全部报告文本和表格保留Markdown；网表、HD源块和模型/LUT哈希归档。

maxstep50→25ps，全局reltol1e-5→1e-6；conservative瞬态实际相对容差为1e-6→1e-7。29项预先设定的差异检查均通过，所有转换码逐点一致，最大功率差0.0304524uW<5uW。

独立复核对原始波形另作逐点插值，调用未改动的原解码器、递归FFT和4项电气检查，共27项数值交叉核对通过。24次基线/精算均实际0错误；警告原样保留，不把Bridge日志分类误当作实际仿真错误。

完整图纸17页，覆盖83个定义实例、481个端子和105个展开叶实例。比较器、采样器、CDAC与异步控制器全部有定义图；HD单元保持厂商边界和实际井端。

复现入口：case42_sar_adc6bit.py → confirm42.py → schematic42.py → audit42.py → review42.py。保留原source、完整码流、采样电平、FFT功率、数值计划、原始运行快照、PDF及可编辑review_report.md。完整电路图附后。

未执行器件噪声、失配、参考阻抗、亚稳态统计、PEX或可靠性寿命分析；电路SHA-256：
4aaf6d34c8b340befe6ed823cd465696013bfeb81a7958240afa39fd1c254f39

## 完整网表与电路图

[Spectre 网表](circuit.scs) · [全部分图 PDF](schematic/sheets.pdf) · [电路总图](schematic/full.svg) · [端子连接](schematic/connectivity.json)

<details>
<summary>展开完整 Spectre 网表</summary>

```spectre
simulator lang=spectre
subckt sar_cmp (clk outn outp vss vdd vinn vinp)
MTAIL (tail clk vss vss) n18 w=2.035u l=.18u
MINP (dx vinp tail vss) n18 w=2.255u l=.18u
MINN (dy vinn tail vss) n18 w=2.255u l=.18u
MLN (ln lp dx vss) n18 w=1.015u l=.18u
MLP (lp ln dy vss) n18 w=1.015u l=.18u
MPN (ln lp vdd vdd) p18 w=1.53u l=.18u
MPP (lp ln vdd vdd) p18 w=1.53u l=.18u
MRST_dx (dx clk vdd vdd) p18 w=1.53u l=.18u
MRST_dy (dy clk vdd vdd) p18 w=1.53u l=.18u
MRST_ln (ln clk vdd vdd) p18 w=1.53u l=.18u
MRST_lp (lp clk vdd vdd) p18 w=1.53u l=.18u
XON (ln outp vdd vss vdd vss) INHDV4
XOP (lp outn vdd vss vdd vss) INHDV4
ends sar_cmp
subckt sar_sample (clk clkb vin vout vdd vss)
CBOOT (cbt cbb) capacitor c=1.5p
MDCHG (cbb clkb vss vss) n18 w=5.1u l=.18u m=1
MPCHG (cg clk vdd vdd) p18 w=14.8u l=.18u m=1
MLIM (vdd vg cbt cbt) p18 w=14.8u l=.18u m=1
MPRE (vdd clk pre vss) n18 w=5.1u l=.18u m=2
MGTRK (cg clk cbb vss) n18 w=5.1u l=.18u m=2
MBPP (vg cg cbt cbt) p18 w=14.8u l=.18u m=1
MPVIN (cbb vg vin vss) n18 w=5.1u l=.18u m=2
MCASC (vg vdd clk vss) n18 w=5.1u l=.18u m=2
MGUARD (vg vdd pre vss) n18 w=5.1u l=.18u m=2
MSN (vout vg vin vss) n18 w=6.78u l=.18u
ends sar_sample
subckt sar_cdac (clks clkb dctrl5 dctrl4 dctrl3 dctrl2 dctrl1 vss vdd vin vrefn vrefp vtop)
XS (clks clkb vin vtop vdd vss) sar_sample
CD (vtop vss) capacitor c=10f
C1 (vtop bot1) capacitor c=30f
MN1 (bot1 dctrl1 vrefn vss) n18 w=0.68u l=.18u
MP1 (bot1 dctrl1 vrefp vdd) p18 w=2u l=.18u
C2 (vtop bot2) capacitor c=60f
MN2 (bot2 dctrl2 vrefn vss) n18 w=1.36u l=.18u
MP2 (bot2 dctrl2 vrefp vdd) p18 w=4u l=.18u
C3 (vtop bot3) capacitor c=120f
MN3 (bot3 dctrl3 vrefn vss) n18 w=2.72u l=.18u
MP3 (bot3 dctrl3 vrefp vdd) p18 w=8u l=.18u
C4 (vtop bot4) capacitor c=240f
MN4 (bot4 dctrl4 vrefn vss) n18 w=5.44u l=.18u
MP4 (bot4 dctrl4 vrefp vdd) p18 w=16u l=.18u
C5 (vtop bot5) capacitor c=480f
MN5 (bot5 dctrl5 vrefn vss) n18 w=10.88u l=.18u
MP5 (bot5 dctrl5 vrefp vdd) p18 w=32u l=.18u
ends sar_cdac
subckt sar_logic (clkc cmpck dcmpn dcmpp dctrln5 dctrln4 dctrln3 dctrln2 dctrln1 dctrlp5 dctrlp4 dctrlp3 dctrlp2 dctrlp1 do5 do4 do3 do2 do1 do0 vss vdd)
XGATE (clkc rdyb clk_gate vdd vss vdd vss) AND2HDV1
XLOOP (nvalid clk_gate loop vdd vss vdd vss) AND2HDV1
XVALID (dcmpp dcmpn valid vdd vss vdd vss) OR2HDV4
XNVALID (valid nvalid vdd vss vdd vss) INHDV1
XRDY (clk0 rdyb vdd vss vdd vss) INHDV1
XDELAY1 (loop delay1 vdd vss vdd vss) INHDV1
CDEL (delay1 vss) capacitor c=10f
XDELAY2 (delay1 cmpck vdd vss vdd vss) INHDV8
XSEQ5 (valid vdd clk5 clkc vdd vss vdd vss) DRNQHDV2
XDECp5 (clk5 dcmpn dctrlp5_raw clkc vdd vss vdd vss) DRNQHDV1
XMSBp (dctrlp5_raw dctrlp5 vdd vss vdd vss) INHDV8
XDECn5 (clk5 dcmpp dctrln5_raw clkc vdd vss vdd vss) DRNQHDV1
XMSBn (dctrln5_raw dctrln5 vdd vss vdd vss) INHDV8
XSEQ4 (valid clk5 clk4 clkc vdd vss vdd vss) DRNQHDV2
XDECp4 (clk4 dcmpp dctrlp4 clkc vdd vss vdd vss) DRNQHDV1
XDECn4 (clk4 dcmpn dctrln4 clkc vdd vss vdd vss) DRNQHDV1
XSEQ3 (valid clk4 clk3 clkc vdd vss vdd vss) DRNQHDV2
XDECp3 (clk3 dcmpp dctrlp3 clkc vdd vss vdd vss) DRNQHDV1
XDECn3 (clk3 dcmpn dctrln3 clkc vdd vss vdd vss) DRNQHDV1
XSEQ2 (valid clk3 clk2 clkc vdd vss vdd vss) DRNQHDV2
XDECp2 (clk2 dcmpp dctrlp2 clkc vdd vss vdd vss) DRNQHDV1
XDECn2 (clk2 dcmpn dctrln2 clkc vdd vss vdd vss) DRNQHDV1
XSEQ1 (valid clk2 clk1 clkc vdd vss vdd vss) DRNQHDV2
XDECp1 (clk1 dcmpp dctrlp1 clkc vdd vss vdd vss) DRNQHDV1
XDECn1 (clk1 dcmpn dctrln1 clkc vdd vss vdd vss) DRNQHDV1
XSEQ0 (valid clk1 clk0 clkc vdd vss vdd vss) DRNQHDV2
XDECp0 (clk0 dcmpp dctrlp0_raw vdd vss vdd vss) DQHDV1
XLSBp (dctrlp0_raw clk0 dctrlp0 vdd vss vdd vss) AND2HDV1
XDECn0 (clk0 dcmpn dctrln0_raw vdd vss vdd vss) DQHDV1
XLSBn (dctrln0_raw clk0 dctrln0 vdd vss vdd vss) AND2HDV1
XEOC (clk0 nvalid eoc vdd vss vdd vss) AND2HDV1
XOUT0 (eoc dctrlp0 do0 vdd vss vdd vss) DQHDV1
XOUT1 (eoc dctrlp1 do1 vdd vss vdd vss) DQHDV1
XOUT2 (eoc dctrlp2 do2 vdd vss vdd vss) DQHDV1
XOUT3 (eoc dctrlp3 do3 vdd vss vdd vss) DQHDV1
XOUT4 (eoc dctrlp4 do4 vdd vss vdd vss) DQHDV1
XOUT5 (eoc dctrlp5 do5 vdd vss vdd vss) DQHDV1
ends sar_logic
subckt sar_adc_6bit_async (clks dout5 dout4 dout3 dout2 dout1 dout0 vss vdd vinn vinp vrefn vrefp)
XCLKC (clks clkc vdd vss vdd vss) INHDV8
XCMP (cmpck dcmpn dcmpp vss vdd vresn vresp) sar_cmp
XDP (clks clkc dctrlp5 dctrlp4 dctrlp3 dctrlp2 dctrlp1 vss vdd vinp vrefn vrefp vresp) sar_cdac
XDN (clks clkc dctrln5 dctrln4 dctrln3 dctrln2 dctrln1 vss vdd vinn vrefn vrefp vresn) sar_cdac
XLOG (clkc cmpck dcmpn dcmpp dctrln5 dctrln4 dctrln3 dctrln2 dctrln1 dctrlp5 dctrlp4 dctrlp3 dctrlp2 dctrlp1 dout5 dout4 dout3 dout2 dout1 dout0 vss vdd) sar_logic
ends sar_adc_6bit_async
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

![电路分图 17](schematic/sheet-17.png)
