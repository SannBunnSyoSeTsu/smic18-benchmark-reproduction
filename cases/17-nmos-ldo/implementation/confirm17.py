from case17_nmos_ldo import *

def main():
    base=json.loads((CASE/'latest_results.json').read_text());assert base['status']=='complete_original'
    bounds=dict(vout_V=1e-6,iq_A=1e-8,loop_ugb_Hz=6000,phase_margin_deg=.05,gain_margin_db=.05,stb_ugb_Hz=6000,stb_phase_margin_deg=.05,stb_gain_margin_db=.05,psrr_1k_dB=.01,min_active_headroom_V=1e-6)
    write_json(CASE/'numerical_plan.json',dict(created_at=now(),baseline_groups=base['groups'],baseline_dec=40,refined_dec=160,baseline_reltol=1e-6,refined_reltol=1e-7,bounds=bounds,same_circuit_sha256=base['circuit_sha256']))
    write_json(CASE/'numerical_baseline.json',base);fine=run(dec=160,reltol=1e-7);diff=[]
    for b,f in zip(base['values']['load_points'],fine['values']['load_points']):
        assert b['load_mA']==f['load_mA']
        for k,limit in bounds.items():
            d=abs(f[k]-b[k]);diff.append(dict(metric=f"{b['load_mA']}mA_{k}",baseline=b[k],refined=f[k],absolute_difference=d,maximum_difference=limit,passed=bool(d<=limit)))
    ok=all(q['passed'] for q in diff) and fine['status']==base['status']
    write_json(CASE/'numerical_confirmation.json',dict(generated_at=now(),baseline_groups=base['groups'],final_groups=fine['groups'],circuit_sha256=fine['circuit_sha256'],metrics=diff,passed=ok));assert ok,diff
    print('case17 numerical confirmation passed')

if __name__=='__main__':main()
