"""Fixed raw-grid convergence bounds for PRBS7 and sensitivity."""
from case32_tx import *

def main():
    quota_guard();base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_');write_json(CASE/'numerical_baseline.json',base)
    limits=dict(prbs_eye_height_v=.0005,sens_swing_v=.0005,prbs_jitter_pp_s=.05e-12,prbs_jitter_rms_s=.05e-12,prbs_dcd_s=.05e-12,prbs_rise_time_s=.05e-12,prbs_fall_time_s=.05e-12,sens_rise_time_s=.05e-12,sens_fall_time_s=.05e-12,time_weighted_power_w=.05e-3)
    write_json(CASE/'numerical_plan.json',dict(declared_at=now(),circuit_sha256=base['circuit_sha256'],max_absolute_differences=limits,baseline=dict(maxstep_s=.2e-12,reltol=1e-6),refined=dict(maxstep_s=.1e-12,reltol=1e-7)))
    simulate(['prbs7','sensitivity'],.1,1e-7);r=extract();checks={}
    for key,tol in limits.items():
        a,b=base['values'][key],r['values'][key];checks[key]=dict(baseline=a,refined=b,absolute_difference=abs(a-b),maximum_difference=tol,passed=abs(a-b)<=tol)
    z=dict(generated_at=now(),circuit_sha256=r['circuit_sha256'],baseline_groups=base['groups'],final_groups=r['groups'],metrics=checks,baseline_tier=base['status'],refined_tier=r['status'],passed=all(q['passed'] for q in checks.values()) and base['status']==r['status'] and r['nonrelaxable_guards_pass'])
    write_json(CASE/'numerical_confirmation.json',z);print(json.dumps(dict(passed=z['passed'],metrics=checks),indent=2));assert z['passed']

if __name__=='__main__':main()
