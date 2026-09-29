# 第06项独立复核

Independent explicit boundary interpolation and scalar trapezoid sums recompute the original external-port means, last commanded-band entry, ripple and supply power. Both gain slopes and seven published original electrical checks are evaluated independently; no design extractor is imported. Native model-based relay vth=.25/hysteresis=.1 implements original switching memory with 1uV transition regularization and unchanged 0.5V reference; vt1/vt2 alone would not implement hysteresis.

|指标|报告|独立|差异|
|---|---:|---:|---:|
|pos20_mean_diff_V|0.160690067151|0.160690067151|1.11e-16|
|pos20_static_error_fraction|0.00431291969135|0.00431291969135|6.939e-16|
|pos20_cm_error_V|0.00762915136372|0.00762915136372|0|
|pos20_power_W|0.000296966052127|0.000296966052127|4.337e-19|
|pos20_settle_s|3.52281926528e-08|3.52281926528e-08|0|
|pos20_ripple_V|0.000433608444148|0.000433608444148|1.11e-16|
|pos10_mean_diff_V|0.0777569927436|0.0777569927436|1.249e-16|
|zero_mean_diff_V|0.000282741376758|0.000282741376758|0|
|neg20_mean_diff_V|-0.159015417806|-0.159015417806|2.776e-17|
|neg20_static_error_fraction|0.00615363870982|0.00615363870982|1.735e-16|
|neg20_cm_error_V|0.00759460527083|0.00759460527083|0|
|neg20_power_W|0.000296926551537|0.000296926551537|2.168e-19|
|neg20_settle_s|3.48780894509e-08|3.48780894509e-08|0|
|neg20_ripple_V|0.000429324415723|0.000429324415723|2.776e-17|
|transfer_positive_gain|8.2933074407|8.2933074407|1.776e-15|
|transfer_bipolar_gain|7.99263712393|7.99263712393|2.665e-15|
|transfer_zero_residual_V|0.000282741376758|0.000282741376758|0|
