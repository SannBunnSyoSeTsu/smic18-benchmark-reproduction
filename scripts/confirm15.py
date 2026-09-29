"""Bounded numerical refinement prompted by edge-local LTE warnings."""
from case15_pump import *

def main():
    quota_guard();base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    limits={'vout_en_avg':.5e-3,'ripple_V':.05e-3,'enabled_current_A':.5e-6,'disabled_current_A':.02e-9}
    write_json(CASE/'numerical_baseline.json',base)
    simulate(['enabled','disabled'],.5,1e-6,'gear2only');ref=extract();rows={}
    for key,tolerance in limits.items():
        a,b=base['values'][key],ref['values'][key];diff=abs(a-b);rows[key]=dict(baseline=a,refined=b,absolute_difference=diff,max_absolute_difference=tolerance,passed=diff<=tolerance)
    confirmation=dict(generated_at=now(),circuit_sha256=ref['circuit_sha256'],baseline_run_dirs=base['run_dirs'],refined_run_dirs=ref['run_dirs'],baseline_parameters=dict(maxstep_s=1e-9,reltol=1e-5,method='gear2only'),refined_parameters=dict(maxstep_s=.5e-9,reltol=1e-6,method='gear2only'),metrics=rows,baseline_tier=base['status'],refined_tier=ref['status'],passed=all(q['passed'] for q in rows.values()) and ref['status']==base['status'])
    write_json(CASE/'numerical_confirmation.json',confirmation);print(json.dumps(confirmation,indent=2));assert confirmation['passed']

if __name__=='__main__':main()
