# 2026-09-29新增七项：全部交付

本批17、18、19、26、30、38、46全部完成，累计43/50。六项原门槛通过；18项只有50µA负载的AVDD电流217.336564µA采用10%边界220µA。仅各题约定TT/nominal功能范围，不是完整PVT/失配签核。

|编号|模块|等级|审查PDF|完整图纸|知识笔记|
|---|---|---|---|---|---|
|17|0.4V NMOS LDO：电流镜电平转换、原生MIM与双负载稳定性|原门槛|[8页](17-nmos-ldo-review.pdf)|[2页总图](../cases/17-nmos-ldo/schematic/full.pdf)|[知识](../notes/17-nmos-ldo.md)|
|18|稳压电荷泵：开关功率级、反馈调节与完整功耗|10%档|[13页](18-regulated-pump-review.pdf)|[6页总图](../cases/18-regulated-pump/schematic/full.pdf)|[知识](../notes/18-regulated-pump.md)|
|19|2:1开关电容变换器：双相电荷转移与负载效率|原门槛|[11页](19-sc-converter-review.pdf)|[5页总图](../cases/19-sc-converter/schematic/full.pdf)|[知识](../notes/19-sc-converter.md)|
|26|全差分OTA-C双二阶：带通状态、共模反馈与线性度|原门槛|[14页](26-ota-c-biquad-review.pdf)|[6页总图](../cases/26-ota-c-biquad/schematic/full.pdf)|[知识](../notes/26-ota-c-biquad.md)|
|30|2.4GHz Gilbert混频器：转换增益、隔离与双音线性度|原门槛|[8页](30-gilbert-mixer-review.pdf)|[2页总图](../cases/30-gilbert-mixer/schematic/full.pdf)|[知识](../notes/30-gilbert-mixer.md)|
|38|无外部电容LDO：内部补偿、负载恢复与供电抑制|原门槛|[10页](38-capless-ldo-review.pdf)|[3页总图](../cases/38-capless-ldo/schematic/full.pdf)|[知识](../notes/38-capless-ldo.md)|
|46|3位Flash ADC：比较器阵列、HD编码与完整动态验收|原门槛|[13页](46-flash-adc3bit-review.pdf)|[6页总图](../cases/46-flash-adc3bit/schematic/full.pdf)|[知识](../notes/46-flash-adc3bit.md)|

全部77页PDF及30页图纸和7份总图已实际查看；完成270项数值对照和368项独立标量核对，另有第18项48组负载×器件的端电压记录检查。原题源资料、PDK、原LUT和既有Bridge/Spectre环境不改；知识入库逐项核对旧文件哈希保持。

18、46的LTE警告保留；18的关闭DC/采样筛查、30的极深隔离数值边界、46的16点满量程归一ENOB解释均在分项报告明确记录。

本批机器审计（保留于原本地归档，未随仓库上传） · [全部43项交付目录](current-delivery-index.md) · [全局交付审计](delivery-audit.json)。

当前累计33项原门槛、7项10%档、3项15%档。剩余05、06、27、28、40、42、48；本批已停止，无活动模块，未开始下一项。额度监控未重启，未调用外部设计模型。
