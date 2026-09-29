from case26_ota_c import *

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    bounds=dict(f0_Hz=1000,Q=.001,passgain_dB=.01,fit_error_dB=.002,atten20M_dB=.01,bp_peak_Hz=30000,bp_peak_dB=.01,bp_1k_dB=.01,bp_200k_dB=.01,bp_20M_dB=.01,cm_error_V=1e-5,power_W=1e-7,noise_Vrms=1e-6,output_amplitude_V=1e-4,fundamental_gain=.001,thd_dB=.05,initial_error_V=1e-5,settle_s=3e-9,late_excursion_V=1e-5)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=2e-9,reltol=1e-6,ac_dec=100,noise_dec=80),refined=dict(maxstep_s=1e-9,reltol=1e-7,ac_dec=200,noise_dec=160),bounds=bounds,FFT_original_N=256))
    write_json(CASE/'numerical_baseline.json',base);fine=run(1e-9,1e-7,200,160);rows=[]
    for kind,b in base['values'].items():
        for key,bv in (b.items() if isinstance(b,dict) else [(kind,b)]):
            fv=fine['values'][kind][key] if isinstance(b,dict) else fine['values'][kind];delta=abs(fv-bv);lim=bounds[key];rows.append(dict(metric=kind+'_'+key,baseline=bv,refined=fv,absolute_difference=delta,maximum_difference=lim,passed=delta<=lim))
    ok=all(x['passed'] for x in rows) and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,rows

if __name__=='__main__':main()
