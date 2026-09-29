from case30_gilbert import *

def main(reuse=False):
    base=json.loads((CASE/('numerical_baseline.json' if reuse else 'latest_results.json')).read_text());assert base['status']=='complete_original'
    if not reuse:
        write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline=dict(maxstep_s=3e-12,reltol=1e-6),refined=dict(maxstep_s=1.5e-12,reltol=1e-7),limits=dict(gain_difference_dB=.02,spur_difference_dB=.15,isolation_linear_ratio_difference=2e-5,voltage_difference_V=10e-6,power_difference_W=1e-6,IIP3_difference_dBm=.05,slope_difference=.01,tone_or_compression_difference_dB=.02,raw_tone_amplitude_difference_V=10e-6),spectrum_N=2048,isolation_note='Compare linearamplitude ratios, notarbitrarydB errorsnearzero; reporteddeepnullsbelowthisnumericalresolution arenotaccurateisolationpredictions.'))
        write_json(CASE/'numerical_baseline.json',base)
    fine=json.loads((CASE/'latest_results.json').read_text()) if reuse else run(1.5e-12,1e-7);rows=[]
    if reuse:
        assert base['groups']!=fine['groups'] and base['circuit_sha256']==fine['circuit_sha256']
        for path in fine['groups'].values():
            net=(ROOT/path/'inputs/bench.scs').read_text();assert 'maxstep=1.5e-12' in net and 'reltol=1e-07' in net
    def add(name,b,f,limit):
        d=float(abs(f-b));rows.append(dict(metric=name,baseline=float(b),refined=float(f),absolute_difference=d,maximum_difference=limit,passed=bool(d<=limit)))
    for b,f in zip(base['values']['rf'],fine['values']['rf']):
        for k,bv in b.items():
            if k in ['RF_Hz','imbalance']:continue
            fv=f[k];lim=.02 if k=='conversion_gain_db' else .15 if k=='spur_dbc' else 1e-6 if k=='power_w' else 10e-6
            if k in ['lo_if_isolation_db','rf_if_feedthrough_db','lo_rf_isolation_db']:bv=10**(bv/20);fv=10**(fv/20);lim=2e-5
            add(f"{b['RF_Hz']}_{b['imbalance']}_{k}",bv,fv,lim)
    for k,b in base['values']['linearity'].items():add(k,b,fine['values']['linearity'][k],.05 if k=='IIP3_dBm' else .01 if 'slope' in k else .02)
    for kind,b in base['values']['linearity_raw'].items():
        for k,v in b.items():add(kind+'_'+k,v,fine['values']['linearity_raw'][kind][k],.02 if k=='gain_dB' else 10e-6)
    ok=all(q['passed'] for q in rows) and fine['status']==base['status'];write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=rows,passed=ok));assert ok,[x for x in rows if not x['passed']]

if __name__=='__main__':main('--from-existing-final' in sys.argv)
