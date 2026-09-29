from case06_ring_amp import *

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    limits=dict(mean_diff_V=5e-5,static_error_fraction=4e-4,cm_error_V=5e-5,power_W=1e-6,settle_s=.2e-9,ripple_V=5e-5,positive_gain=.01,bipolar_gain=.003,zero_residual_V=5e-5)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=.25e-9,reltol=1e-6),refined=dict(maxstep_s=.125e-9,reltol=1e-7),absolute_difference_limits=limits));write_json(CASE/'numerical_baseline.json',base)
    fine=run(.125e-9,1e-7);rows=[]
    for kind,vs in base['values'].items():
        for k,bv in vs.items():
            fv=fine['values'][kind][k];delta=abs(bv-fv);rows.append(dict(metric=kind+'_'+k,baseline=bv,refined=fv,absolute_difference=delta,maximum_difference=limits[k],passed=delta<=limits[k]))
    ok=all(x['passed'] for x in rows) and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,rows

if __name__=='__main__':main()
