from case38_capless_ldo import *

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    bounds={k:(.01 if 'dB' in k else 1e-8 if k.endswith('_A') else .0002) for k in base['values']['line_points'][0] if k not in ['supply_V','vref_current_A']}
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(step_max_s=20e-9,start_max_s=200e-9,reltol=1e-6,dc_step_A=.0002,ac_dec=40),refined=dict(step_max_s=10e-9,start_max_s=100e-9,reltol=1e-7,dc_step_A=.0001,ac_dec=160),bounds=bounds,startup_voltage_difference_max_V=.0002))
    write_json(CASE/'numerical_baseline.json',base);fine=run(step=10e-9,reltol=1e-7,dc_step=.0001,dec=160);rows=[]
    for b,f in zip(base['values']['line_points'],fine['values']['line_points']):
        assert b['supply_V']==f['supply_V']
        for k,limit in bounds.items():
            d=abs(f[k]-b[k]);rows.append(dict(metric=f"{b['supply_V']}V_{k}",baseline=b[k],refined=f[k],absolute_difference=d,maximum_difference=limit,passed=bool(d<=limit)))
    for k,b in base['values']['startup'].items():
        f=fine['values']['startup'][k];d=abs(f-b);rows.append(dict(metric='startup_'+k,baseline=b,refined=f,absolute_difference=d,maximum_difference=.0002,passed=bool(d<=.0002)))
    ok=all(q['passed'] for q in rows) and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,rows
    print('case38 numerical confirmation passed')

if __name__=='__main__':main()
