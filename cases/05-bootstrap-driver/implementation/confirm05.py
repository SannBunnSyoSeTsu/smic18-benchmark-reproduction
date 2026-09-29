from case05_bootstrap_driver import *

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    limits={k:(20e-12 if k.startswith('dead_') else 5e-6 if k=='power_W' else .005 if k=='HS_peak_A' else .002 if k in ('VGS_avg_V','high_fraction') else .005) for k in base['values']['pw20']}
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=100e-12,global_reltol=1e-5),refined=dict(maxstep_s=50e-12,global_reltol=1e-6),absolute_difference_limits=limits,method='traponly retained; waveform comparison must bound peak, timing, power and average differences.'))
    write_json(CASE/'numerical_baseline.json',base);fine=run(50e-12,1e-6);rows=[]
    for label,vals in base['values'].items():
        for key,b in vals.items():
            f=fine['values'][label][key];delta=abs(f-b);rows.append(dict(metric=label+'_'+key,baseline=b,refined=f,absolute_difference=delta,maximum_difference=limits[key],passed=delta<=limits[key]))
    ok=all(x['passed'] for x in rows) and fine['status']==base['status']
    write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,rows

if __name__=='__main__':main()
