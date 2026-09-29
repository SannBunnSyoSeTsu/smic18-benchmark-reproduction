# 第27项独立复核

Unmodified original Python transfer, endpoint-linearity, recursive-FFT and clipped-energy analyzers receive actual Spectre traces through a name-only adapter. Six original electrical check functions run unchanged. Native eligibility is separately validated; no claim to running the Sky130 text parser on Spectre.

|指标|报告|独立|差异|
|---|---:|---:|---:|
|transfer_invalid_levels|0|0|0|
|linearity_invalid_levels|0|0|0|
|dynamic_invalid_levels|0|0|0|
|transfer_code_errors|0|0|0|
|transfer_missing_codes|0|0|0|
|linearity_linearity_valid|1|1|0|
|linearity_transition_count|15|15|0|
|linearity_missing_codes|0|0|0|
|linearity_monotonic|1|1|0|
|linearity_inl_LSB|0.0843373493976|0.0843373493976|4.857e-16|
|linearity_dnl_LSB|0.156626506024|0.156626506024|1.11e-16|
|dynamic_sndr_dB|26.2773330001|26.2773330001|3.553e-15|
|dynamic_sfdr_dB|29.5313667894|29.5313667894|3.553e-15|
|dynamic_power_W|0.00242198825887|0.00242198825887|8.413e-17|
|dynamic_clock_power_W|0.000217053067308|0.000217053067308|2.819e-18|
