# SMIC18 Analog Design Bench V2 Reproduction

50 项模拟与混合信号电路从 Analog Design Bench V2 迁移至 SMIC18MMRF 的原理图级复现记录。包含电路与测试平台、gm/ID 初算、Spectre 测量、完整电路图、PDF/Markdown 报告和系统框图。

**Credit / 致谢：本工作基于 [Arcadia-1/analog-design-bench](https://github.com/Arcadia-1/analog-design-bench)。原始 benchmark、50 项任务规范、参考电路与验证脚本均来自该仓库；感谢 Arcadia-1 和 Analog Design Bench contributors。** 使用的固定版本为 [`c23f124`](https://github.com/Arcadia-1/analog-design-bench/tree/c23f124de1e461655d2e02ce6cfae2654ccea0d3)。本仓库记录 SMIC18 工艺迁移及其复现结果，原始 benchmark 的署名与许可保留在 [来源说明](NOTICE.md)。

**50/50 已交付：38 项原指标，8 项 10% 档，4 项 15% 档。** 适用范围为各题合同规定的 TT/nominal 条件，保留对应温度、电压、负载、代码与输入维度；不表示完整 PVT、Monte Carlo 或 PEX 签核。

[验收换算规则](contracts/acceptance-policy.md) · [复现环境与步骤](docs/REPRODUCING.md) · [发布范围与证据](docs/DISTRIBUTION.md) · [来源与许可](NOTICE.md) · [仓库校验](tools/verify_distribution.py)

50 份 MD 报告均有完整正文、可编辑表格与图像。其中 7 份由报告生成器同步保存，43 份从已交付矢量 PDF 恢复，来源已标注。28 项系统级工作附 Mermaid 框图。原 PDF 共 533 页，保持已审阅版本的字节和 SHA-256。

频谱离散谱线从图底基线向上绘制；第 40 项 ΔΣ 调制器使用对数频率轴，并附 20 dB/dec 理论参照，参照线不是实测拟合结果。

| 编号 | 模块 | 验收档 | 报告 MD | PDF | 电路图 | 系统框图 | 设计笔记 |
|---|---|---|---|---|---|---|---|
| 01 | class-d | 10% | [MD](cases/01-class-d/review_report.md) | [PDF](reports/01-class-d-review.pdf) | [SVG](cases/01-class-d/schematic/full.svg) | [Mermaid](cases/01-class-d/review_report.md#系统框图) | [笔记](notes/01-class-d.md) |
| 02 | mirror | 原指标 | [MD](cases/02-mirror/review_report.md) | [PDF](reports/02-mirror-review.pdf) | [SVG](cases/02-mirror/schematic/full.svg) | [Mermaid](cases/02-mirror/review_report.md#系统框图) | [笔记](notes/02-mirror.md) |
| 03 | selfbiased-gmr | 原指标 | [MD](cases/03-selfbiased-gmr/review_report.md) | [PDF](reports/03-selfbiased-gmr-review.pdf) | [SVG](cases/03-selfbiased-gmr/schematic/full.svg) | — | [笔记](notes/03-selfbiased-gmr.md) |
| 04 | gmr | 原指标 | [MD](cases/04-gmr/review_report.md) | [PDF](reports/04-gmr-review.pdf) | [SVG](cases/04-gmr/schematic/full.svg) | — | [笔记](notes/04-gmr.md) |
| 05 | bootstrap-driver | 10% | [MD](cases/05-bootstrap-driver/review_report.md) | [PDF](reports/05-bootstrap-driver-review.pdf) | [SVG](cases/05-bootstrap-driver/schematic/full.svg) | [Mermaid](cases/05-bootstrap-driver/review_report.md#系统框图) | [笔记](notes/05-bootstrap-driver.md) |
| 06 | ring-amplifier | 原指标 | [MD](cases/06-ring-amplifier/review_report.md) | [PDF](reports/06-ring-amplifier-review.pdf) | [SVG](cases/06-ring-amplifier/schematic/full.svg) | [Mermaid](cases/06-ring-amplifier/review_report.md#系统框图) | [笔记](notes/06-ring-amplifier.md) |
| 07 | ldo-ota5 | 15% | [MD](cases/07-ldo-ota5/review_report.md) | [PDF](reports/07-ldo-ota5-review.pdf) | [SVG](cases/07-ldo-ota5/schematic/full.svg) | [Mermaid](cases/07-ldo-ota5/review_report.md#系统框图) | [笔记](notes/07-ldo-ota5.md) |
| 08 | ppsf | 原指标 | [MD](cases/08-ppsf/review_report.md) | [PDF](reports/08-ppsf-review.pdf) | [SVG](cases/08-ppsf/schematic/full.svg) | — | [笔记](notes/08-ppsf.md) |
| 09 | cml-divider | 原指标 | [MD](cases/09-cml-divider/review_report.md) | [PDF](reports/09-cml-divider-review.pdf) | [SVG](cases/09-cml-divider/schematic/full.svg) | [Mermaid](cases/09-cml-divider/review_report.md#系统框图) | [笔记](notes/09-cml-divider.md) |
| 10 | tia | 15% | [MD](cases/10-tia/review_report.md) | [PDF](reports/10-tia-review.pdf) | [SVG](cases/10-tia/schematic/full.svg) | — | [笔记](notes/10-tia.md) |
| 11 | bandgap | 原指标 | [MD](cases/11-bandgap/review_report.md) | [PDF](reports/11-bandgap-review.pdf) | [SVG](cases/11-bandgap/schematic/full.svg) | — | [笔记](notes/11-bandgap.md) |
| 12 | beta | 原指标 | [MD](cases/12-beta/review_report.md) | [PDF](reports/12-beta-review.pdf) | [SVG](cases/12-beta/schematic/full.svg) | — | [笔记](notes/12-beta.md) |
| 13 | constant-gm | 原指标 | [MD](cases/13-constant-gm/review_report.md) | [PDF](reports/13-constant-gm-review.pdf) | [SVG](cases/13-constant-gm/schematic/full.svg) | — | [笔记](notes/13-constant-gm.md) |
| 14 | oscillator | 原指标 | [MD](cases/14-oscillator/review_report.md) | [PDF](reports/14-oscillator-review.pdf) | [SVG](cases/14-oscillator/schematic/full.svg) | — | [笔记](notes/14-oscillator.md) |
| 15 | unregulated-pump | 10% | [MD](cases/15-unregulated-pump/review_report.md) | [PDF](reports/15-unregulated-pump-review.pdf) | [SVG](cases/15-unregulated-pump/schematic/full.svg) | [Mermaid](cases/15-unregulated-pump/review_report.md#系统框图) | [笔记](notes/15-unregulated-pump.md) |
| 16 | miller | 10% | [MD](cases/16-miller/review_report.md) | [PDF](reports/16-miller-review.pdf) | [SVG](cases/16-miller/schematic/full.svg) | — | [笔记](notes/16-miller.md) |
| 17 | nmos-ldo | 原指标 | [MD](cases/17-nmos-ldo/review_report.md) | [PDF](reports/17-nmos-ldo-review.pdf) | [SVG](cases/17-nmos-ldo/schematic/full.svg) | [Mermaid](cases/17-nmos-ldo/review_report.md#系统框图) | [笔记](notes/17-nmos-ldo.md) |
| 18 | regulated-pump | 10% | [MD](cases/18-regulated-pump/review_report.md) | [PDF](reports/18-regulated-pump-review.pdf) | [SVG](cases/18-regulated-pump/schematic/full.svg) | [Mermaid](cases/18-regulated-pump/review_report.md#系统框图) | [笔记](notes/18-regulated-pump.md) |
| 19 | sc-converter | 原指标 | [MD](cases/19-sc-converter/review_report.md) | [PDF](reports/19-sc-converter-review.pdf) | [SVG](cases/19-sc-converter/schematic/full.svg) | [Mermaid](cases/19-sc-converter/review_report.md#系统框图) | [笔记](notes/19-sc-converter.md) |
| 20 | mux | 原指标 | [MD](cases/20-mux/review_report.md) | [PDF](reports/20-mux-review.pdf) | [SVG](cases/20-mux/schematic/full.svg) | [Mermaid](cases/20-mux/review_report.md#系统框图) | [笔记](notes/20-mux.md) |
| 21 | highpsrr-bandgap | 原指标 | [MD](cases/21-highpsrr-bandgap/review_report.md) | [PDF](reports/21-highpsrr-bandgap-review.pdf) | [SVG](cases/21-highpsrr-bandgap/schematic/full.svg) | — | [笔记](notes/21-highpsrr-bandgap.md) |
| 22 | bootstrap | 原指标 | [MD](cases/22-bootstrap/review_report.md) | [PDF](reports/22-bootstrap-review.pdf) | [SVG](cases/22-bootstrap/schematic/full.svg) | [Mermaid](cases/22-bootstrap/review_report.md#系统框图) | [笔记](notes/22-bootstrap.md) |
| 23 | resistor-dac | 原指标 | [MD](cases/23-resistor-dac/review_report.md) | [PDF](reports/23-resistor-dac-review.pdf) | [SVG](cases/23-resistor-dac/schematic/full.svg) | [Mermaid](cases/23-resistor-dac/review_report.md#系统框图) | [笔记](notes/23-resistor-dac.md) |
| 24 | ring-vco | 原指标 | [MD](cases/24-ring-vco/review_report.md) | [PDF](reports/24-ring-vco-review.pdf) | [SVG](cases/24-ring-vco/schematic/full.svg) | — | [笔记](notes/24-ring-vco.md) |
| 25 | complementary-ab | 原指标 | [MD](cases/25-complementary-ab/review_report.md) | [PDF](reports/25-complementary-ab-review.pdf) | [SVG](cases/25-complementary-ab/schematic/full.svg) | — | [笔记](notes/25-complementary-ab.md) |
| 26 | ota-c-biquad | 原指标 | [MD](cases/26-ota-c-biquad/review_report.md) | [PDF](reports/26-ota-c-biquad-review.pdf) | [SVG](cases/26-ota-c-biquad/schematic/full.svg) | [Mermaid](cases/26-ota-c-biquad/review_report.md#系统框图) | [笔记](notes/26-ota-c-biquad.md) |
| 27 | flash-adc4bit | 原指标 | [MD](cases/27-flash-adc4bit/review_report.md) | [PDF](reports/27-flash-adc4bit-review.pdf) | [SVG](cases/27-flash-adc4bit/schematic/full.svg) | [Mermaid](cases/27-flash-adc4bit/review_report.md#系统框图) | [笔记](notes/27-flash-adc4bit.md) |
| 28 | fct-amplifier | 15% | [MD](cases/28-fct-amplifier/review_report.md) | [PDF](reports/28-fct-amplifier-review.pdf) | [SVG](cases/28-fct-amplifier/schematic/full.svg) | [Mermaid](cases/28-fct-amplifier/review_report.md#系统框图) | [笔记](notes/28-fct-amplifier.md) |
| 29 | ahuja | 原指标 | [MD](cases/29-ahuja/review_report.md) | [PDF](reports/29-ahuja-review.pdf) | [SVG](cases/29-ahuja/schematic/full.svg) | — | [笔记](notes/29-ahuja.md) |
| 30 | gilbert-mixer | 原指标 | [MD](cases/30-gilbert-mixer/review_report.md) | [PDF](reports/30-gilbert-mixer-review.pdf) | [SVG](cases/30-gilbert-mixer/schematic/full.svg) | — | [笔记](notes/30-gilbert-mixer.md) |
| 31 | bottom-plate | 原指标 | [MD](cases/31-bottom-plate/review_report.md) | [PDF](reports/31-bottom-plate-review.pdf) | [SVG](cases/31-bottom-plate/schematic/full.svg) | [Mermaid](cases/31-bottom-plate/review_report.md#系统框图) | [笔记](notes/31-bottom-plate.md) |
| 32 | cml-tx | 10% | [MD](cases/32-cml-tx/review_report.md) | [PDF](reports/32-cml-tx-review.pdf) | [SVG](cases/32-cml-tx/schematic/full.svg) | [Mermaid](cases/32-cml-tx/review_report.md#系统框图) | [笔记](notes/32-cml-tx.md) |
| 33 | sampling-ota-gain1 | 10% | [MD](cases/33-sampling-ota-gain1/review_report.md) | [PDF](reports/33-sampling-ota-gain1-review.pdf) | [SVG](cases/33-sampling-ota-gain1/schematic/full.svg) | [Mermaid](cases/33-sampling-ota-gain1/review_report.md#系统框图) | [笔记](notes/33-sampling-ota-gain1.md) |
| 34 | sampling-ota-gain8 | 10% | [MD](cases/34-sampling-ota-gain8/review_report.md) | [PDF](reports/34-sampling-ota-gain8-review.pdf) | [SVG](cases/34-sampling-ota-gain8/schematic/full.svg) | [Mermaid](cases/34-sampling-ota-gain8/review_report.md#系统框图) | [笔记](notes/34-sampling-ota-gain8.md) |
| 35 | fd-miller | 原指标 | [MD](cases/35-fd-miller/review_report.md) | [PDF](reports/35-fd-miller-review.pdf) | [SVG](cases/35-fd-miller/schematic/full.svg) | — | [笔记](notes/35-fd-miller.md) |
| 36 | telescopic | 原指标 | [MD](cases/36-telescopic/review_report.md) | [PDF](reports/36-telescopic-review.pdf) | [SVG](cases/36-telescopic/schematic/full.svg) | — | [笔记](notes/36-telescopic.md) |
| 37 | nested-miller | 原指标 | [MD](cases/37-nested-miller/review_report.md) | [PDF](reports/37-nested-miller-review.pdf) | [SVG](cases/37-nested-miller/schematic/full.svg) | — | [笔记](notes/37-nested-miller.md) |
| 38 | capless-ldo | 原指标 | [MD](cases/38-capless-ldo/review_report.md) | [PDF](reports/38-capless-ldo-review.pdf) | [SVG](cases/38-capless-ldo/schematic/full.svg) | [Mermaid](cases/38-capless-ldo/review_report.md#系统框图) | [笔记](notes/38-capless-ldo.md) |
| 39 | line-driver | 原指标 | [MD](cases/39-line-driver/review_report.md) | [PDF](reports/39-line-driver-review.pdf) | [SVG](cases/39-line-driver/schematic/full.svg) | [Mermaid](cases/39-line-driver/review_report.md#系统框图) | [笔记](notes/39-line-driver.md) |
| 40 | delta-sigma | 原指标 | [MD](cases/40-delta-sigma/review_report.md) | [PDF](reports/40-delta-sigma-review.pdf) | [SVG](cases/40-delta-sigma/schematic/full.svg) | [Mermaid](cases/40-delta-sigma/review_report.md#系统框图) | [笔记](notes/40-delta-sigma.md) |
| 41 | lowpower-miller | 原指标 | [MD](cases/41-lowpower-miller/review_report.md) | [PDF](reports/41-lowpower-miller-review.pdf) | [SVG](cases/41-lowpower-miller/schematic/full.svg) | — | [笔记](notes/41-lowpower-miller.md) |
| 42 | sar-adc6bit | 原指标 | [MD](cases/42-sar-adc6bit/review_report.md) | [PDF](reports/42-sar-adc6bit-review.pdf) | [SVG](cases/42-sar-adc6bit/schematic/full.svg) | [Mermaid](cases/42-sar-adc6bit/review_report.md#系统框图) | [笔记](notes/42-sar-adc6bit.md) |
| 43 | inductive-lna | 原指标 | [MD](cases/43-inductive-lna/review_report.md) | [PDF](reports/43-inductive-lna-review.pdf) | [SVG](cases/43-inductive-lna/schematic/full.svg) | — | [笔记](notes/43-inductive-lna.md) |
| 44 | ota5 | 原指标 | [MD](cases/44-ota5/review_report.md) | [PDF](reports/44-ota5-review.pdf) | [SVG](cases/44-ota5/schematic/full.svg) | — | [笔记](notes/44-ota5.md) |
| 45 | divider | 原指标 | [MD](cases/45-divider/review_report.md) | [PDF](reports/45-divider-review.pdf) | [SVG](cases/45-divider/schematic/full.svg) | [Mermaid](cases/45-divider/review_report.md#系统框图) | [笔记](notes/45-divider.md) |
| 46 | flash-adc3bit | 原指标 | [MD](cases/46-flash-adc3bit/review_report.md) | [PDF](reports/46-flash-adc3bit-review.pdf) | [SVG](cases/46-flash-adc3bit/schematic/full.svg) | [Mermaid](cases/46-flash-adc3bit/review_report.md#系统框图) | [笔记](notes/46-flash-adc3bit.md) |
| 47 | charge-pump | 原指标 | [MD](cases/47-charge-pump/review_report.md) | [PDF](reports/47-charge-pump-review.pdf) | [SVG](cases/47-charge-pump/schematic/full.svg) | [Mermaid](cases/47-charge-pump/review_report.md#系统框图) | [笔记](notes/47-charge-pump.md) |
| 48 | sar-adc4bit | 原指标 | [MD](cases/48-sar-adc4bit/review_report.md) | [PDF](reports/48-sar-adc4bit-review.pdf) | [SVG](cases/48-sar-adc4bit/schematic/full.svg) | [Mermaid](cases/48-sar-adc4bit/review_report.md#系统框图) | [笔记](notes/48-sar-adc4bit.md) |
| 49 | lc-vco | 15% | [MD](cases/49-lc-vco/review_report.md) | [PDF](reports/49-lc-vco-review.pdf) | [SVG](cases/49-lc-vco/schematic/full.svg) | — | [笔记](notes/49-lc-vco.md) |
| 50 | gainboosted-folded | 原指标 | [MD](cases/50-gainboosted-folded/review_report.md) | [PDF](reports/50-gainboosted-folded-review.pdf) | [SVG](cases/50-gainboosted-folded/schematic/full.svg) | — | [笔记](notes/50-gainboosted-folded.md) |

## 目录与使用

- `cases/`：50 项电路、合同、结果、图纸、报告、LUT 记录和原实现快照。
- `reports/`：已审阅 PDF、批次汇总和历史验证回执。
- `scripts/`：电路生成、测量、审查、报告及 Mermaid 生成脚本。
- `runs/`：最终及数值确认运行的输入快照和运行元数据；大体积 PSF 波形留在本机归档。
- `upstream/`：固定版本的原 benchmark 内容、软件与许可证。
- `publication/`：此次上传的逐文件哈希与原归档映射。

阅读报告无需 EDA 环境。重新仿真需要自行取得 SMIC18 PDK、原厂 HD 单元库及 Cadence Spectre 许可，并按复现说明配置原有工具依赖。本仓库不分发 PDK 模型、原厂 CDL/HD 晶体管库、EDA 软件或许可证。
