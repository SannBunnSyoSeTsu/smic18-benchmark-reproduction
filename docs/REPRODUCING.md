# 阅读、核对与重新仿真

## 无需 EDA 的检查

在 Python 3.11 或更新版本中运行：

```bash
python tools/verify_distribution.py
```

检查 50 个电路、50 份报告与结果、28 份 Mermaid、已审阅 PDF 的原始哈希、仓库文件清单，以及上传包不包含原厂 HD 库和大体积仿真输出。此命令不重新运行 Spectre。

## 原验证环境

工艺为 SMIC18MMRF；模拟模型使用 `ms018_v1p7_spe.lib`，数字单元来自 SCC018UG_HD_RVT。模型和库本体需要使用者从合法安装中提供。历史案例使用 Spectre 18.1，后续案例使用 24.1；各条运行记录与报告保留实际环境，不将历史记录伪装成统一工具版本。

原流程使用 `virtuoso-bridge-lite` 的 Spectre runner/PSF parser，以及独立 `gmoverid_smic18` 工程中的 `gmidsmic.GmIdTable`。这些是本地运行依赖；仓库内保留所用 LUT 和尺寸记录，但不复制 Bridge 的虚拟环境或整个 EDA 安装。

## 重新运行的边界与步骤

1. 阅读选定案例的 `contract.json`、报告和 `latest_results.json`，确定原刺激、负载、测量窗口、适用 nominal 维度与验收档。
2. 在独立工作副本中配置 Python 依赖、合法 PDK、原厂 HD CDL、Spectre、Bridge 和 gm/ID 查询工程。原脚本中的路径是历史环境路径，尤其检查 `scripts/common.py`、`scripts/batch29.py` 与 `scripts/hd_cells.py`。输入快照中的绝对 include 路径同样需要按当前安装调整。
3. 使用 `scripts/hd_cells.py` 和案例的 `hd_cells_manifest.json`，从本机原厂 CDL 提取该案例需要的单元。仓库不提供 `hd_cells.scs`；提取须保持原器件尺寸与型号。
4. 按案例报告记录的入口运行电路/测试平台生成与测量。最后七项的典型入口为 `caseNN_*.py`、`confirmNN.py`、`auditNN.py`、`reviewNN.py`；较早案例按其 `implementation/` 和报告内的实际入口执行。
5. 重新运行会产生新的路径、环境与文件哈希。应生成新的审计记录；历史 `verification_audit.json` 与 `pdf_provenance.json` 只证明已归档的那次结果。所有需要 PSF 的测量交叉核对必须使用本机原始波形或重新仿真的输出。

报告生成使用 Python/Matplotlib 与 Poppler，Markdown 是可编辑同文报告或明确标注的 PDF 恢复文本，并非所有 PDF 的编译输入。Mermaid 源文件可直接在 GitHub 阅读，SVG/PNG 预览同时保留。

本次 GitHub 发布只整理已完成证据，没有重新仿真或扩大 PVT、失配、PEX 范围。原 47 GB 工程和所有失败迭代、运行日志、原始波形仍保存在本机。
