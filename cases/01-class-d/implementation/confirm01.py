"""Bounded convergence comparison for six edge-stress / efficiency endpoints."""
from case01_classd import *

def main():
    quota_guard();base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    prior=CASE/'numerical_baseline.json'
    if prior.exists():
        old=json.loads(prior.read_text())
        if old['circuit_sha256']==sha(CASE/'circuit.scs'):base=old
    labels=[f't{t}_r{r}' for t in TEMPS for r in [1,3,16]]
    limits={'efficiency':.001,'p_in_W':.2e-3,'p_out_W':.2e-3}
    write_json(CASE/'numerical_baseline.json',base)
    latest=json.loads((CASE/'latest_runs.json').read_text());pending=[]
    for label in labels:
        run=ROOT/latest[label];m=json.loads((run/'run.json').read_text());b=(ROOT/m['netlist']).read_text()
        if latest[label]==base['groups'][label] or 'maxstep=0.5n' not in b or 'reltol=1e-06' not in b:pending.append(label)
    midpoint=CASE/'numerical_midpoint.json'
    if midpoint.exists() and json.loads(midpoint.read_text())['circuit_sha256']==sha(CASE/'circuit.scs'):
        # Resume the finer14point pass without downgrading any finished point.
        ref=json.loads(midpoint.read_text())
    else:simulate(pending,.5,1e-6);ref=extract()
    rows={}
    for label in labels:
        rows[label]={}
        for key,tolerance in limits.items():
            a,b=base['values'][label][key],ref['values'][label][key];diff=abs(a-b)
            rows[label][key]=dict(baseline=a,refined=b,absolute_difference=diff,max_absolute_difference=tolerance,passed=diff<=tolerance)
    z=dict(generated_at=now(),circuit_sha256=ref['circuit_sha256'],reason='SPECTRE-16780 edge-local LTE warnings; cover resonant1ohm, near-peak3ohm and low-power16ohm at both temperatures',labels=labels,baseline_groups=base['groups'],final_groups=ref['groups'],baseline_parameters=dict(maxstep_s=1e-9,reltol=1e-5,method='traponly'),refined_parameters=dict(maxstep_s=.5e-9,reltol=1e-6,method='traponly'),metrics=rows,baseline_tier=base['status'],refined_tier=ref['status'],passed=all(q['passed'] for a in rows.values() for q in a.values()) and base['status']==ref['status'])
    if not z['passed']:
        # A failed convergence check is retained; do not widen its tolerances.
        history=CASE/'iteration_history.json';h=json.loads(history.read_text());h.setdefault('numerical_attempts',[])
        if not any(q.get('final_groups')==z['final_groups'] for q in h['numerical_attempts']):h['numerical_attempts'].append(z)
        write_json(history,h);midpath=CASE/'numerical_midpoint.json'
        if midpath.exists() and json.loads(midpath.read_text())['circuit_sha256']==ref['circuit_sha256']:mid=json.loads(midpath.read_text())
        else:mid=ref;write_json(midpath,mid)
        pending=[];latest=json.loads((CASE/'latest_runs.json').read_text())
        for label in POINTS:
            m=json.loads((ROOT/latest[label]/'run.json').read_text());b=(ROOT/m['netlist']).read_text()
            if 'maxstep=0.25n' not in b or 'reltol=1e-07' not in b:pending.append(label)
        simulate(pending,.25,1e-7);ref=extract();rows={}
        for label in labels:
            rows[label]={}
            for key,tolerance in limits.items():
                a,b=mid['values'][label][key],ref['values'][label][key];diff=abs(a-b)
                rows[label][key]=dict(baseline=a,refined=b,absolute_difference=diff,max_absolute_difference=tolerance,passed=diff<=tolerance)
        z.update(generated_at=now(),reason='First1ns/1e-5 comparison failed fixed bounds; all14points now rerun at0.25ns/1e-7. Six representative points compare against0.5ns/1e-6 without changing bounds.',baseline_groups=mid['groups'],final_groups=ref['groups'],baseline_parameters=dict(maxstep_s=.5e-9,reltol=1e-6,method='traponly'),refined_parameters=dict(maxstep_s=.25e-9,reltol=1e-7,method='traponly'),metrics=rows,baseline_tier=mid['status'],refined_tier=ref['status'],all14_final_use_refined_parameters=True,passed=all(q['passed'] for a in rows.values() for q in a.values()) and mid['status']==ref['status'])
    write_json(CASE/'numerical_confirmation.json',z)
    print(json.dumps(dict(passed=z['passed'],baseline_parameters=z['baseline_parameters'],refined_parameters=z['refined_parameters'],max_efficiency_difference=max(q['efficiency']['absolute_difference'] for q in z['metrics'].values()),max_power_difference_W=max(q[k]['absolute_difference'] for q in z['metrics'].values() for k in ['p_in_W','p_out_W'])),indent=2));assert z['passed']

if __name__=='__main__':main()
