from case19_sc_converter import *

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    bounds={k:(.001 if k=='efficiency' else .0002 if k.endswith('_V') else .5e-9 if k.endswith('_s') else 2e-6 if k.endswith('_W') else 1e-6 if k.endswith('_A') else .0002) for k in base['values']['loads'][0] if k!='load_ohm'}
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=.5e-9,reltol=1e-6),refined=dict(maxstep_s=.25e-9,reltol=1e-7),bounds=bounds,rout_difference_max_ohm=.1))
    write_json(CASE/'numerical_baseline.json',base);fine=run(.25e-9,1e-7);rows=[]
    for b,f in zip(base['values']['loads'],fine['values']['loads']):
        for k in b:
            if k=='load_ohm':continue
            delta=abs(b[k]-f[k]);limit=bounds[k];rows.append(dict(metric=f"{b['load_ohm']}ohm_{k}",baseline=b[k],refined=f[k],absolute_difference=delta,maximum_difference=limit,passed=delta<=limit))
    b=base['values']['output_resistance_ohm'];f=fine['values']['output_resistance_ohm'];rows.append(dict(metric='output_resistance_ohm',baseline=b,refined=f,absolute_difference=abs(f-b),maximum_difference=.1,passed=abs(f-b)<=.1))
    ok=all(x['passed'] for x in rows) and base['status']==fine['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,rows

if __name__=='__main__':main()
