from case40_delta_sigma import *
import shutil

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    limits=dict(dc=1/256,gain=.005,sndr8_dB=.75,sndr16_dB=.75,sndr32_dB=.75,shaping_dB=.75,density=1/512,transitions=.008,invalid=0,state_peak_V=.005,source_mean_power_W=75e-6,time_weighted_power_W=10e-6,DC_error=1/256,coefficient_real=.002,coefficient_imag=.002,polarity_amplitude_ratio=.005,polarity_phase_error_deg=.3,osr_improvement_dB=1.)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=1e-9,global_reltol=1e-5,effective_conservative_reltol=1e-6),refined=dict(maxstep_s=.5e-9,global_reltol=1e-6,effective_conservative_reltol=1e-7),absolute_difference_limits=limits,bitstream_difference_fraction_max=.02,rationale='SC loop finite512-bit spectrum may move with individual decisions; require stable original pass,sub-dB spectra,half-percent gain,onecode density and2%bitstream bound. Original sample-mean current depends on adaptive step distribution; physical time-weighted current held to10uW.'))
    write_json(CASE/'numerical_baseline.json',base);shutil.copy2(CASE/'conversion_records.json',CASE/'baseline_conversion_records.json');fine=run(.5e-9,1e-6);rows=[]
    for kind,vals in base['values'].items():
        for k,bv in vals.items():
            fv=fine['values'][kind][k];delta=abs(fv-bv);rows.append(dict(metric=kind+'_'+k,baseline=bv,refined=fv,absolute_difference=delta,maximum_difference=limits[k],passed=delta<=limits[k]))
    bc=json.loads((CASE/'baseline_conversion_records.json').read_text());fc=json.loads((CASE/'conversion_records.json').read_text());diff={k:sum(a!=b for a,b in zip(bc[k]['codes'],fc[k]['codes']))/512 for k in bc};ok=all(x['passed'] for x in rows) and max(diff.values())<=.02 and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,bitstream_changed_fraction=diff,passed=ok));assert ok,[x for x in rows if not x['passed']]
if __name__=='__main__':main()
