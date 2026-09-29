# 第11项独立测量复核

Current agent independent calculation pass. Actual Spectre waveforms adapted in memory to the original verifier Plot interface; upstream analyze executes unchanged. Original full-PVT score function was not invoked.

|检查|报告|独立结果|绝对差|
|---|---:|---:|---:|
|startup1:window_min_V|1.22447648043|1.22447648043|2.22e-16|
|startup1:window_max_V|1.22507152362|1.22507152362|0|
|startup1:final_V|1.22507152362|1.22507152362|0|
|startup1:overshoot_V|0|0|0|
|startup1:peak_current_A|0.000579962913269|0.000579962913269|0|
|startup1:energy_J|2.12327706854e-09|2.12327706854e-09|5.79e-24|
|startup10:window_min_V|1.22502431465|1.22502431465|0|
|startup10:window_max_V|1.22507269652|1.22507269652|0|
|startup10:final_V|1.22507269652|1.22507269652|0|
|startup10:overshoot_V|0|0|0|
|startup10:peak_current_A|5.54632447631e-05|5.54632447631e-05|0|
|startup10:energy_J|2.32694675293e-09|2.32694675293e-09|5.38e-24|
|AC maximum|0.0327891937297|0.0327891937297|0|
|Output noise integral|0.00023249275175|0.00023249275175|0|
|step up peak|0.00533284850497|0.00533284850497|0|
|step up last outside|2.802e-06|2.802e-06|0|
|step down peak|0.0109009294861|0.0109009294861|0|
|step down last outside|3.982e-06|3.982e-06|0|
|temperature coefficient|7.45317379554|7.45317379554|0|
|line regulation|0.00446853657091|0.00446853657091|0|

原始波形、输入网表、合同、PDK与LUT哈希检查通过。图纸独立核对27个实例、94个端子，错误0。未执行全PVT/MC评分。
