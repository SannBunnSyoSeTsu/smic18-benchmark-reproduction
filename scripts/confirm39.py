"""Predeclared step/tolerance confirmation of nominal distortion and current."""
from case39_line_driver import *

def main():
    quota_guard();base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    old=CASE/'numerical_baseline.json'
    if old.exists():
        z=json.loads(old.read_text())
        if z['circuit_sha256']==sha(CASE/'circuit.scs'):base=z
    write_json(old,base)
    limits=dict(thd_pct=.005,fundamental_v=.0001,peak_supply_current_a=1e-6)
    write_json(CASE/'numerical_plan.json',dict(circuit_sha256=base['circuit_sha256'],limits=limits,baseline_maxstep_s=100e-9,refined_maxstep_s=50e-9,baseline_reltol=1e-6,refined_reltol=1e-7,declared_at=now()))
    simulate(['thd'],50,1e-7);r=extract();checks={}
    for k,tol in limits.items():
        x,y=base['values'][k],r['values'][k];checks[k]=dict(baseline=x,refined=y,absolute_difference=abs(x-y),maximum_difference=tol,passed=abs(x-y)<=tol)
    z=dict(generated_at=now(),circuit_sha256=r['circuit_sha256'],baseline_groups=base['groups'],final_groups=r['groups'],metrics=checks,baseline_tier=base['status'],refined_tier=r['status'],passed=all(q['passed'] for q in checks.values()) and base['status']==r['status'])
    write_json(CASE/'numerical_confirmation.json',z);print(json.dumps(z,indent=2));assert z['passed']

if __name__=='__main__':main()
