"""Strict FCT confirmation; only solver recovery attempt count is increased."""
from case28_fct_amplifier import *
from concurrent.futures import ThreadPoolExecutor,as_completed
import shutil

BASE=dict(maxstep_s=2.5e-12,global_reltol=1e-7,vabstol_V=1e-8,iabstol_A=1e-12)
FINE=dict(maxstep_s=1.25e-12,global_reltol=1e-8,vabstol_V=1e-8,iabstol_A=1e-12)
LIMITS=dict(gain_vv=.01,sfdr_db=.5,cm_mean_v=.001,output_min_v=.001,output_max_v=.001,hold_movement_ratio=.0002,power_w=5e-6)

def main(reuse_baseline20=None,reuse_baseline10=None):
    archive=CASE/'numerical_stages';archive.mkdir(exist_ok=True)
    for name in ['numerical_plan.json','numerical_baseline.json','numerical_confirmation.json']:
        if (CASE/name).exists() and not (archive/('before_retry_'+name)).exists():shutil.copy2(CASE/name,archive/('before_retry_'+name))
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline=BASE,refined=FINE,absolute_difference_limits=LIMITS,recovery=dict(max_minstep_nonconv=10000,max_approach_minstep=10000),exact_original_readout_strobes=True,reason='Retain all original confirmation bounds, including0.5dB SFDR. The ideal-relay discontinuities exceed the default recovery-count limit at strict tolerances. Keep10nV absolute voltage tolerance in both runs;1nV attempts were stopped before the measurement window due to impractical relay recovery cost. Increase allowed recovery attempts; do not change circuit, relay, stimulus, thresholds, minstep or tolerance bounds. All actual solver warnings retained.'))
    deps=[CASE/x for x in ['circuit.scs','sizing.json','contract.json','hd_cells.scs','hd_cells_manifest.json']];hashes={str(p):sha(p) for p in deps};paths={'baseline':{},'refined':{}}
    if reuse_baseline20:paths['baseline']['20mv']=reuse_baseline20
    if reuse_baseline10:paths['baseline']['10mv']=reuse_baseline10
    jobs=[(level,kind,setting) for level,setting in [('baseline',BASE),('refined',FINE)] for kind in ['10mv','20mv'] if kind not in paths[level]]
    def one(level,kind,setting):
        b=bench(kind,setting['maxstep_s'],setting['global_reltol'],setting['vabstol_V'],setting['iabstol_A'])
        return str(run_spectre(28,'precision_'+level+'_'+kind,b,deps,timeout=1800).relative_to(ROOT))
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(one,*job):job[:2] for job in jobs}
        for f in as_completed(futures):
            level,kind=futures[f];paths[level][kind]=f.result();print(level,kind,paths[level][kind],flush=True);write_json(CASE/'precision_runs_partial.json',paths)
    assert {str(p):sha(p) for p in deps}==hashes
    for level in paths:paths[level]={k:paths[level][k] for k in ['10mv','20mv']}
    for group in paths.values():
        for path in group.values():assert json.loads((ROOT/path/'run.json').read_text())['status']=='completed'
    for level,setting in [('baseline',BASE),('refined',FINE)]:
        for kind in ['10mv','20mv']:
            (CASE/f'testbench_{level}_{kind}.scs').write_text(bench(kind,setting['maxstep_s'],setting['global_reltol'],setting['vabstol_V'],setting['iabstol_A']))
    write_json(CASE/'latest_runs.json',paths['baseline']);base=extract();write_json(CASE/'numerical_baseline.json',base)
    write_json(CASE/'latest_runs.json',paths['refined']);fine=extract();rows=[]
    for kind,vals in base['values'].items():
        for key,b in vals.items():
            f=fine['values'][kind][key];delta=abs(f-b);rows.append(dict(metric=kind+'_'+key,baseline=b,refined=f,absolute_difference=delta,maximum_difference=LIMITS[key],passed=delta<=LIMITS[key]))
    ok=all(x['passed'] for x in rows) and fine['status']==base['status']
    cf=dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],baseline_settings=BASE,refined_settings=FINE,exact_original_readout_strobes=True,metrics=rows,passed=ok)
    write_json(CASE/'numerical_confirmation.json',cf);write_json(archive/'retry_confirmation.json',cf);assert ok,rows

if __name__=='__main__':main()
