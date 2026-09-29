from case18_regulated_pump import *

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    bounds={k:(.25e-6 if k.endswith('_A') else .001 if k in ['control_avg_V','driver_supply_avg_V'] else 50e-6) for k in base['values']['enabled'][0] if k!='load_uA'}
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=1e-9,reltol=1e-5),refined=dict(maxstep_s=.5e-9,reltol=1e-6),bounds=bounds,disabled_current_difference_A=.05e-9))
    write_json(CASE/'numerical_baseline.json',base);fine=run(.5e-9,1e-6);rows=[]
    for b,f in zip(base['values']['enabled'],fine['values']['enabled']):
        for k,limit in bounds.items():
            delta=abs(b[k]-f[k]);rows.append(dict(metric=f"{b['load_uA']}uA_{k}",baseline=b[k],refined=f[k],absolute_difference=delta,maximum_difference=limit,passed=delta<=limit))
    b=base['values']['disabled_current_A'];f=fine['values']['disabled_current_A'];rows.append(dict(metric='disabled_current_A',baseline=b,refined=f,absolute_difference=abs(f-b),maximum_difference=.05e-9,passed=abs(f-b)<=.05e-9))
    ok=all(x['passed'] for x in rows) and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,rows

if __name__=='__main__':main()
