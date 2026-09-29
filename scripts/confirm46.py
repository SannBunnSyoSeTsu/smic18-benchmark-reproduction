from case46_flash_adc import *
import shutil

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    bounds=dict(clock_to_output_s=.05e-9,core_reference_power_w=2e-6,clock_delivery_power_w=1e-6,clock_peak_current_a=.00005)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=.1e-9,reltol=1e-6),refined=dict(maxstep_s=.05e-9,reltol=1e-7),transition_bounds=bounds,remaining_scalar_difference_max=1e-10,conversion_codes_must_be_identical=True))
    write_json(CASE/'numerical_baseline.json',base);shutil.copy2(CASE/'conversion_records.json',CASE/'baseline_conversion_records.json');fine=run(.05e-9,1e-7);rows=[]
    for kind,b in base['values'].items():
        for k,bv in b.items():
            fv=fine['values'][kind][k];delta=abs(float(bv)-float(fv));limit=bounds[k] if kind=='transition' and k in bounds else 1e-10;rows.append(dict(metric=kind+'_'+k,baseline=bv,refined=fv,absolute_difference=delta,maximum_difference=limit,passed=delta<=limit))
    bc=json.loads((CASE/'baseline_conversion_records.json').read_text());fc=json.loads((CASE/'conversion_records.json').read_text());identical=all(bc[k]['codes']==fc[k]['codes'] for k in bc)
    ok=all(x['passed'] for x in rows) and identical and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,conversion_codes_identical=identical,passed=ok));assert ok,rows

if __name__=='__main__':main()
