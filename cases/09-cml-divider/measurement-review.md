# 第09项独立测量复核

Current agent independently passed actual Spectre time/outp/outn rows to unchanged upstream divider_metrics and speed_check forTT. Power independently computed from originalVDD port. No other process corners claimed.

|指标|报告|独立结果|绝对差|
|---|---:|---:|---:|
|1g:output_swing_Vpp|0.715014821754|0.715014821754|0|
|1g:minimum_cycle_swing_Vpp|0.712886753855|0.712886753855|0|
|1g:target_tone_Vpp|0.776786025686|0.776786025686|5.55e-16|
|1g:alternating_cycles|40|40|0|
|2g:output_swing_Vpp|0.694056739841|0.694056739841|0|
|2g:minimum_cycle_swing_Vpp|0.676257211526|0.676257211526|0|
|2g:target_tone_Vpp|0.738822719333|0.738822719333|1.11e-15|
|2g:alternating_cycles|40|40|0|
|5g:output_swing_Vpp|0.592520451166|0.592520451166|0|
|5g:minimum_cycle_swing_Vpp|0.536488318015|0.536488318015|0|
|5g:target_tone_Vpp|0.655095895391|0.655095895391|5.55e-16|
|5g:alternating_cycles|40|40|0|
|10g:output_swing_Vpp|0.416915785849|0.416915785849|0|
|10g:minimum_cycle_swing_Vpp|0.210371387555|0.210371387555|0|
|10g:target_tone_Vpp|0.430827709681|0.430827709681|5e-16|
|10g:alternating_cycles|40|40|0|
|quiescent VDD power|0.00145535107038|0.00145535107038|0|

四频点的40周期符号、逐周期摆幅和时间加权fIN/2投影均沿原定义。输入PWL轨迹对照原PULSE解析式检查一致；输出频率另从正向过零间隔测得，未将命令频率直接当作实测。

图纸19实例/68端子核对通过；模型、LUT与最终五组电路快照一致。
