from case42_sar_adc6bit import *
import shutil

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=50e-12,global_reltol=1e-5,effective_conservative_reltol=1e-6),refined=dict(maxstep_s=25e-12,global_reltol=1e-6,effective_conservative_reltol=1e-7),power_difference_max_W=5e-6,other_scalar_difference_max=1e-8,conversion_codes_must_be_identical=True));write_json(CASE/'numerical_baseline.json',base);shutil.copy2(CASE/'conversion_records.json',CASE/'baseline_conversion_records.json');fine=run_parallel(25e-12,1e-6);rows=[]
    for kind,vals in base['values'].items():
        for k,bv in vals.items():
            fv=fine['values'][kind][k];delta=abs(float(fv)-float(bv));limit=5e-6 if k=='power_W' else 1e-8;rows.append(dict(metric=kind+'_'+k,baseline=bv,refined=fv,absolute_difference=delta,maximum_difference=limit,passed=delta<=limit))
    bc=json.loads((CASE/'baseline_conversion_records.json').read_text());fc=json.loads((CASE/'conversion_records.json').read_text());same=all(bc[k]['codes']==fc[k]['codes'] for k in bc);ok=all(x['passed'] for x in rows) and same and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,conversion_codes_identical=same,passed=ok));assert ok,rows
if __name__=='__main__':main()
