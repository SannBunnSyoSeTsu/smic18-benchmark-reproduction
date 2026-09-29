# 第21项独立测量复核

Current agent independently re-integrated actual Spectre trajectories and passed the resulting metrics to the unchanged upstream checks(rows,{NOMINAL}); no other3PVT points simulated or claimed.

|指标|报告|独立结果|绝对差|
|---|---:|---:|---:|
|vref_V|1.23446077309|1.23446077309|0|
|temp_min_V|1.23028877093|1.23028877093|0|
|temp_max_V|1.23650604127|1.23650604127|0|
|temp_average_V|1.23396207287|1.23396207287|0|
|tempco_ppm_C|40.3076916069|40.3076916069|0|
|supply_gain_low_dB|-70.6250787497|-70.6250787497|0|
|supply_gain_1MHz_dB|-35.3922744838|-35.3922744838|7.11e-15|
|startup_average_V|1.23446077307|1.23446077307|2.22e-16|
|startup_error_fraction|1.42159829524e-11|1.42158030807e-11|1.8e-16|

原上游五项nominal检查均通过；温度平均值采用梯形积分除以125°C。启动按90–100µs时间平均与独立27°C DC值比较；不使用瞬态自己的尾值作目标。

图纸独立复核32实例、114端子，错误0；源文件、PDK、LUT及三组最终输入哈希一致。
