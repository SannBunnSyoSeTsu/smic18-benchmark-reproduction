# 来源与许可

原 benchmark：[Arcadia-1/analog-design-bench](https://github.com/Arcadia-1/analog-design-bench/tree/c23f124de1e461655d2e02ce6cfae2654ccea0d3)，固定版本 `c23f124de1e461655d2e02ce6cfae2654ccea0d3`。

上游署名：Copyright 2026 Analog Design Bench contributors。

感谢 **Arcadia-1** 公开原始 Analog Design Bench 仓库、任务规范、参考电路和验证流程。本仓库的 SMIC18 复现建立在这些工作之上，不将原始 benchmark 宣称为本项目原创。

运行工具另使用 [Arcadia-1/virtuoso-bridge-lite](https://github.com/Arcadia-1/virtuoso-bridge-lite) 的 Spectre runner 与 PSF parser，作为外部依赖保留来源；本仓库未复制其虚拟环境或商业 EDA 安装。

原许可证及完整文本保存在 [upstream/LICENSE](upstream/LICENSE)、[Apache-2.0](upstream/LICENSES/Apache-2.0.txt) 和 [CC BY-NC 4.0](upstream/LICENSES/CC-BY-NC-4.0.txt)。上游软件适用 Apache-2.0，benchmark 任务、网表、数据、图像和文档适用 CC BY-NC 4.0；文件自身的许可声明优先。上游不授予 benchmark 内容的商业使用权。

本项目对原任务进行了 SMIC18 工艺迁移、尺寸计算、标准单元映射、nominal 仿真与中文分析；原 Sky130 reference 结果与新测量结果分别保存，不混作一次验证。受上游内容许可约束的改编材料继续保留其署名与许可条件。仓库没有为其余新增材料另行授予统一开源许可；上传到 GitHub 不改变第三方权利。

PDK、原厂标准单元和商业 EDA 工具保留各自许可。库实现和许可证文件未随本仓库分发，只有库名称、使用清单和哈希用于追溯。原上游 README 中的 benchmark 语料声明与标识原样保留。
