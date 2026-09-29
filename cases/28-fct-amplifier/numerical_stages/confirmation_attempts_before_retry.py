from case28_fct_amplifier import *

def first_confirmation():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    limits=dict(gain_vv=.01,sfdr_db=.5,cm_mean_v=.001,output_min_v=.001,output_max_v=.001,hold_movement_ratio=.0002,power_w=5e-6)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=10e-12,global_reltol=1e-5),refined=dict(maxstep_s=5e-12,global_reltol=1e-6),absolute_difference_limits=limits))
    write_json(CASE/'numerical_baseline.json',base);fine=run(5e-12,1e-6);rows=[]
    for kind,vals in base['values'].items():
        for k,b in vals.items():
            f=fine['values'][kind][k];delta=abs(f-b);rows.append(dict(metric=kind+'_'+k,baseline=b,refined=f,absolute_difference=delta,maximum_difference=limits[k],passed=delta<=limits[k]))
    ok=all(x['passed'] for x in rows) and fine['status']==base['status']
    write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,rows



def tighter_absolute_attempt():
    import shutil
    prior=CASE/'numerical_stages';prior.mkdir(exist_ok=True)
    for name in ['numerical_plan.json','numerical_baseline.json','numerical_confirmation.json']:
        if (CASE/name).exists() and not (prior/('initial_'+name)).exists():shutil.copy2(CASE/name,prior/('initial_'+name))
    limits=dict(gain_vv=.01,sfdr_db=.5,cm_mean_v=.001,output_min_v=.001,output_max_v=.001,hold_movement_ratio=.0002,power_w=5e-6)
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    settings=[dict(maxstep_s=2.5e-12,global_reltol=1e-7,vabstol_V=1e-7,iabstol_A=1e-13),dict(maxstep_s=1.25e-12,global_reltol=1e-8,vabstol_V=1e-8,iabstol_A=1e-14)]
    previous=dict(maxstep_s=5e-12,global_reltol=1e-6,vabstol_V=1e-6,iabstol_A=1e-12)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],initial_baseline=previous,refinement_ladder=settings,absolute_difference_limits=limits,reason='Initial 10ps to5ps check failed the original 0.5dB SFDR difference bound; keep that bound and tighten absolute as well as relative tolerances.'))
    stages=[]
    for index,setting in enumerate(settings):
        write_json(CASE/'numerical_baseline.json',base)
        fine=run(setting['maxstep_s'],setting['global_reltol'],setting['vabstol_V'],setting['iabstol_A']);rows=[]
        for kind,vals in base['values'].items():
            for k,b in vals.items():
                f=fine['values'][kind][k];delta=abs(f-b);rows.append(dict(metric=kind+'_'+k,baseline=b,refined=f,absolute_difference=delta,maximum_difference=limits[k],passed=delta<=limits[k]))
        ok=all(x['passed'] for x in rows) and fine['status']==base['status']
        cf=dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],baseline_settings=previous,refined_settings=setting,metrics=rows,passed=ok)
        write_json(prior/f'refinement_{index+1}.json',cf);stages.append(cf);write_json(CASE/'numerical_confirmation.json',dict(**cf,refinement_stages=stages))
        print('precision stage',index+1,'passed',ok,flush=True)
        if ok:return
        base=fine;previous=setting
    assert False,'SFDR convergence remains unresolved; thresholds unchanged'



def main():
    import shutil
    prior=CASE/'numerical_stages';prior.mkdir(exist_ok=True)
    for name in ['numerical_plan.json','numerical_baseline.json','numerical_confirmation.json']:
        if (CASE/name).exists() and not (prior/('before_strobe_'+name)).exists():shutil.copy2(CASE/name,prior/('before_strobe_'+name))
    limits=dict(gain_vv=.01,sfdr_db=.5,cm_mean_v=.001,output_min_v=.001,output_max_v=.001,hold_movement_ratio=.0002,power_w=5e-6)
    settings=[dict(maxstep_s=2.5e-12,global_reltol=1e-6,vabstol_V=1e-6,iabstol_A=1e-12),dict(maxstep_s=1.25e-12,global_reltol=1e-7,vabstol_V=1e-6,iabstol_A=1e-12)]
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),settings=settings,absolute_difference_limits=limits,reason='Initial interpolated FFT check failed0.5dB convergence; tighter absolute tolerance failed at an ideal relay discontinuity. Force accepted time points at all unchanged held/early readout times using strobetimes and retain all adaptive samples for power. Preserve original difference bounds.'))
    base=run(settings[0]['maxstep_s'],settings[0]['global_reltol'],1e-6,1e-12);write_json(CASE/'numerical_baseline.json',base)
    fine=run(settings[1]['maxstep_s'],settings[1]['global_reltol'],1e-6,1e-12);rows=[]
    for kind,vals in base['values'].items():
        for k,b in vals.items():
            f=fine['values'][kind][k];delta=abs(f-b);rows.append(dict(metric=kind+'_'+k,baseline=b,refined=f,absolute_difference=delta,maximum_difference=limits[k],passed=delta<=limits[k]))
    ok=all(x['passed'] for x in rows) and fine['status']==base['status']
    cf=dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],baseline_settings=settings[0],refined_settings=settings[1],exact_original_readout_strobes=True,metrics=rows,passed=ok)
    write_json(CASE/'numerical_confirmation.json',cf);write_json(prior/'strobe_confirmation.json',cf);assert ok,rows

if __name__=='__main__':main()
