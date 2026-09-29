"""Prespecified RF-grid tightening; final scores use all refined samples."""
from case43_lna import *

def main():
    quota_guard();base=json.loads((CASE/'latest_results.json').read_text());assert base['status'].startswith('complete_')
    assert base['measurement_points']==dict(band=101,stability=401,noise=101)
    write_json(CASE/'numerical_baseline.json',base)
    bounds={k:.05 for k in ['transducer_gain_db_min','transducer_gain_db_max','gain_ripple_db','s11_db_max','s22_db_max','reverse_isolation_db_max']}
    bounds.update(noise_figure_db=.005,stability_k_min=abs(base['values']['stability_k_min'])*.01,stability_delta_max=1e-4,power_w=1e-6,iref_voltage_v=1e-5,iref_headroom_v=1e-5)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline_grid=base['measurement_points'],refined_grid=dict(band=201,stability=1601,noise=201),baseline_reltol=1e-6,refined_reltol=1e-7,fixed_maximum_differences=bounds,note='All original frequencies included in refined grid; samephysicalcircuitandfixtures; originalband/stabilityextentsunchanged. Finegrid usedforfinalconservative extrema.'))
    simulate(201,800,1e-7);fine=extract();diff={}
    for k,bound in bounds.items():
        x=abs(fine['values'][k]-base['values'][k]);diff[k]=dict(baseline=base['values'][k],refined=fine['values'][k],absolute_difference=x,maximum_difference=bound,passed=bool(x<=bound))
    a=ROOT/base['groups']['rf'];b=ROOT/fine['groups']['rf']
    for name in ['band.ac','wide.ac','noise.noise']:
        old=data(a,name,required=['out'] if name=='noise.noise' else []);new=data(b,name,required=['out'] if name=='noise.noise' else []);factor=4 if name=='wide.ac' else 2;assert np.allclose(old['freq'],new['freq'][::factor],rtol=1e-12)
    ok=all(q['passed'] for q in diff.values()) and fine['status']==base['status'] and fine['nonrelaxable_guards_pass']
    write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),circuit_sha256=fine['circuit_sha256'],baseline_groups=base['groups'],final_groups=fine['groups'],baseline_grid=base['measurement_points'],final_grid=fine['measurement_points'],metrics=diff,baseline_tier=base['status'],refined_tier=fine['status'],passed=ok));assert ok
    print('NumericalRF confirmation passed')

if __name__=='__main__':main()
