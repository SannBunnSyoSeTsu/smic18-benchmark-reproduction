# GitHub 发布范围与证据

本目录为已交付复现工程的独立发布副本。50 份最终 PDF、电路、合同、结果和验证记录沿用原归档；本机完整工程没有因发布而重写。

已包含：50 份 MD/PDF、完整电路图、28 份 Mermaid 及其 SVG/PNG、设计/测量/报告脚本、gm/ID 查询记录、原 benchmark 固定版本，以及 296 个最终或数值确认运行的输入与元数据。

未上传：约 46 GB 仿真运行输出、EDA 安装与虚拟环境、PDK 模型、原厂 CDL 和提取的 `hd_cells.scs`、浏览器下载包、额度监控和登录配置。复现实测与报告中的数值不因这些文件未分发而改变；完整重新核验需要本机原波形或重新运行仿真。

原历史 JSON、输入快照及 Python 脚本保留原字节，因此可能包含原本机路径。它们表示历史来源，不是 GitHub 下载地址。Markdown 的文档链接改成仓库相对链接；未分发的本地记录显示为文字说明，不留下伪有效链接。变动的 MD 清单以及源/发布 SHA-256 记录在 `publication/source-manifest.json`。

43 份从 PDF 恢复的 MD 的原逐格检查为 201 张表、8,098 个单元格；28 份 Mermaid 使用真实解析器检查并逐图查看。历史回执保存在 `reports/`，本次发布的独立检查由 `tools/verify_distribution.py` 运行。

上游固定提交：`c23f124de1e461655d2e02ce6cfae2654ccea0d3`。具体归属和使用条件见 [来源与许可](../NOTICE.md)。

2026-09-30：50 份报告完成可读性修订，当前文档验收见 [修订记录](MARKDOWN-REVISION.md) 和 `publication/readability-audit.json`。`reports/` 及旧 `markdown_delivery.json` 属于此前交付回执，不能用作修订后 MD 的哈希。原 PDF、电路、合同和结果保持原值。
