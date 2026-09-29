"""Independent reductions, original nominal checks, fixtures and provenance."""
from common import *
import importlib.util
import audit_schematic_independent as drawing
CASE=ROOT/'cases/32-cml-tx';UI=1/28e9

def crossings(t,y,level):
    k=np.flatnonzero((y[:-1]-level)*(y[1:]-level)<0)
    return t[k]+(level-y[k])*(t[k+1]-t[k])/(y[k+1]-y[k])

def nearest(xs,guess,window):
    k=np.argmin(abs(xs-guess));x=xs[k];assert abs(x-guess)<=window
    return x

def transient(d,bits,static=None):
    t=d['time'];y=d['voutp']-d['voutn'];zero=crossings(t,y,0)
    seq=np.arange(128,254) if static else np.arange(1,12)
    edges=seq[bits[seq]!=bits[seq-1]]
    picked=np.array([nearest(zero,n*UI,.9*UI) for n in edges])
    assert len(np.unique(picked))==len(edges),'No reused crossings'
    errors=picked-edges*UI;delay=float(np.mean(errors))
    assert 0<delay<UI/2,'No half-UI alias in final design'
    centers=np.arange(127,254) if static else np.arange(4,12)
    ct=(centers+.5)*UI+delay;assert ct[-1]<=t[-1]
    samples=np.interp(ct,t,y);ones=samples[bits[centers]==1];zeros=samples[bits[centers]==0]
    sign=int(np.sum(samples*(2*bits[centers]-1)<=0));assert sign==0
    hi,lo=(static['vod1'],static['vod0']) if static else (np.mean(ones),np.mean(zeros))
    low=crossings(t,y,lo+.2*(hi-lo));high=crossings(t,y,lo+.8*(hi-lo))
    rf={'rise':[],'fall':[]};rf_edges=edges if static else centers
    for n in rf_edges:
        a=nearest(low,n*UI+delay,.6*UI);b=nearest(high,n*UI+delay,.6*UI)
        sign_edge=1 if bits[n] else -1;dt=(b-a)*sign_edge;assert dt>0
        rf['rise' if bits[n] else 'fall'].append(float(dt))
    q=dict(sign_errors=sign,rise_time_s=max(rf['rise']),fall_time_s=max(rf['fall']),n_rise=len(rf['rise']),n_fall=len(rf['fall']))
    details=dict(mean_delay_s=delay,edge_indices=edges.tolist(),edge_errors_s=errors.tolist(),sample_indices=centers.tolist(),sample_times_s=ct.tolist(),sample_values_V=samples.tolist(),samples=len(centers),unique_crossings=True)
    if not static:q.update(n_samples=len(centers),swing_v=float(min(ones)-max(zeros)));return q,details
    sel=t>=127*UI;p=d['voutp'][sel];n=d['voutn'][sel];vod=y[sel]
    q.update(n_transitions=len(edges),eye_height_v=float(min(ones)-max(zeros)),overshoot_v=max(0,float(max(vod)-hi)),undershoot_v=max(0,float(lo-min(vod))),vocm_dev_max_v=float(max(abs((p+n)/2-(static['vocm1']+static['vocm0'])/2))),vmin=float(min(min(p),min(n))),vmax=float(max(max(p),max(n))),jitter_pp_s=float(np.ptp(errors)),jitter_rms_s=float(np.std(errors)),dcd_s=float(abs(np.mean(errors[bits[edges]==1])-np.mean(errors[bits[edges]==0]))),avg_power_w=float(np.mean(-d['VDD:p'][sel])*1.8))
    tt=np.r_[127*UI,t[t>127*UI]];ii=np.interp(tt,t,-d['VDD:p'])
    details['time_weighted_power_W']=float(np.sum(np.diff(tt)*(ii[1:]+ii[:-1])/2)*1.8/(tt[-1]-tt[0]))
    assert len(edges)==63 and len(centers)==127 and (q['n_rise'],q['n_fall'])==(31,32)
    return q,details

def main():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];assert r['all_nominal_checks_complete'] and r['nonrelaxable_guards_pass'];runs={k:ROOT/p for k,p in r['groups'].items()}
    sys.path.insert(0,str(CASE/'source/tests'));sp=importlib.util.spec_from_file_location('tx_verify_frozen',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(sp);sp.loader.exec_module(up)
    o=dc(runs['static']);s={}
    for tag,bit in [('one','1'),('zero','0')]:
        p,n=o['voutp'+tag],o['voutn'+tag];s.update({f'vp{bit}':p,f'vn{bit}':n,f'vod{bit}':p-n,f'vocm{bit}':(p+n)/2,f'idd{bit}':-o[f'VDD{tag}:p']})
    s['vodoff']=o['voutpoff']-o['voutnoff'];assert s['vod1']>0>s['vod0']
    out=dict(swing_v=s['vod1']-s['vod0'],vocm_drop_max_v=max(1.8-s['vocm1'],1.8-s['vocm0']),vocm_drop_min_v=min(1.8-s['vocm1'],1.8-s['vocm0']),cm_shift_v=abs(s['vocm1']-s['vocm0']),offset_v=abs(s['vodoff']),idd_imbalance_fraction=abs(s['idd1']-s['idd0'])/((s['idd1']+s['idd0'])/2),static_min_v=min(s[k] for k in ['vp1','vn1','vp0','vn0']),static_max_v=max(s[k] for k in ['vp1','vn1','vp0','vn0']))
    d=data(runs['ac'],'ac.ac');f=d['freq'];h=d['voutp']-d['voutn'];mag=abs(h);phase=np.angle(h)
    assert abs(f[0]-10e6)<1 and abs(f[-1]-50e9)<1
    def csv(name,values):
        p=runs['ac']/name;np.savetxt(p,np.column_stack([f,np.zeros((len(f),3)),values]),fmt='%.17g');return p
    mag_csv=csv('original_ac_mag.csv',mag);phase_csv=csv('original_ac_phase_DEGREES.csv',phase*180/np.pi)
    ac=up.ac_analysis.analyze(mag_csv,phase_csv);out.update(ac)
    physical=-np.diff(np.unwrap(phase))/(2*np.pi*np.diff(f));mid=(f[1:]+f[:-1])/2
    independent_gd=float(np.ptp(physical[(mid>=1e9)&(mid<=14e9)]));assert abs(independent_gd-ac['group_delay_var_s'])<1e-22
    raw_rad=up.ac_analysis.analyze(mag_csv,csv('diagnostic_phase_RADIANS_not_acceptance.csv',phase))
    bits=np.loadtxt(CASE/'source/tests/benches/prbs7_bits.csv')[:,2].astype(int)
    prbs,pdetail=transient(data(runs['prbs7'],'tran.tran'),bits,s)
    sens,sdetail=transient(data(runs['sensitivity'],'tran.tran'),np.arange(12)%2)
    assert (sens['n_samples'],sens['n_rise'],sens['n_fall'])==(8,4,4)
    out.update({'prbs_'+k:float(x) for k,x in prbs.items()});out.update({'sens_'+k:float(x) for k,x in sens.items()});out.update(time_weighted_power_w=pdetail['time_weighted_power_W'],overshoot_fraction=max(prbs['overshoot_v'],prbs['undershoot_v'])/out['swing_v'])
    checks=[]
    for key,val in out.items():
        difference=abs(val-v[key]);tol=1e-22 if key.endswith('_s') else 1e-12;assert difference<=max(tol,abs(val)*1e-8),(key,val,v[key],difference)
        checks.append(dict(metric=key,report=v[key],independent=val,absolute_difference=difference,passed=True))
    original=up.static_checks({'tt':s})+up.ac_checks({'tt':ac})+up.prbs7_checks({'tt':prbs},{'tt':s})[0]+up.sensitivity_checks({'tt':sens})
    original=[dict(name=k,passed=bool(ok),detail=msg) for k,ok,msg in original];assert len(original)==23
    assert {q['name'] for q in original if not q['passed']}=={'bandwidth_22ghz','sensitivity_swing'}
    assert r['pass_tiers']==dict(original=False,**{'10pct':True,'15pct':True})
    src=json.loads((CASE/'source_provenance.json').read_text())
    for rel,hx in src['files'].items():assert sha(CASE/'source'/rel)==hx==sha(Path(src['task'])/rel)
    model=model_provenance();assert model==json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    conf=json.loads((CASE/'numerical_confirmation.json').read_text());assert conf['passed'] and conf['final_groups']==r['groups'] and conf['circuit_sha256']==r['circuit_sha256'];logs=[]
    for label,path in list(r['groups'].items())+[(f'baseline_{k}',conf['baseline_groups'][k]) for k in ['prbs7','sensitivity']]:
        rd=ROOT/path;m=json.loads((rd/'run.json').read_text());assert m['status']=='completed' and not m['warnings'] and m['models']==model and m['temperature_C']==27 and m['model_dimensions_valid']
        assert sha(ROOT/m['netlist'])==m['netlist_sha256'];b=(ROOT/m['netlist']).read_text();group=label.removeprefix('baseline_')
        tags=['one','zero','off'] if group=='static' else ['']
        for tag in tags:
            for line in [f'VDD{tag} (vdd{tag} 0) vsource dc=1.8',f'IREF{tag} (vdd{tag} iref{tag}) isource dc=100u',f'RQP{tag} (voutp{tag} vdd{tag}) resistor r=50',f'RQN{tag} (voutn{tag} vdd{tag}) resistor r=50',f'CQP{tag} (voutp{tag} 0) capacitor c=100f',f'CQN{tag} (voutn{tag} 0) capacitor c=100f']:assert line in b,line
        if group!='static':
            for line in ['RSP (srcp dinp) resistor r=50','RSN (srcn dinn) resistor r=50','CPADP (dinp 0) capacitor c=30f','CPADN (dinn 0) capacitor c=30f']:assert line in b
        if group in ['prbs7','sensitivity']:
            source=(CASE/'source/tests/benches'/f'tb_{group}.spi').read_text()
            for leg in ['P','N']:
                original_pwl=re.search(r'^VSRC'+leg+r' src\w 0 PWL\(([^)]+)\)',source,re.M)[1]
                assert f'V{leg} (src{leg.lower()} 0) vsource type=pwl wave=[{original_pwl}]' in b
            assert ('maxstep=0.2p' if label.startswith('baseline_') else 'maxstep=0.1p') in b
        for source,q in m['dependencies'].items():
            assert sha(ROOT/q['snapshot'])==q['sha256']
            if source.endswith('circuit.scs'):assert q['sha256']==sha(CASE/'circuit.scs')==r['circuit_sha256']
            if source.endswith('contract.json'):assert q['sha256']==sha(CASE/'contract.json')==r['contract_sha256']
        log='\n'.join(p.read_text(errors='replace') for p in (rd/'output').glob('*.log'));assert re.search(r'spectre completes with 0 errors',log) and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',log)
        logs.append(dict(group=label,run=path,actual_error_free=True,warnings=m['warnings'],bridge_errors=m['errors'],fixture_verified=True,stimulus_PWL_identical=group in ['prbs7','sensitivity']))
    for q in json.loads((CASE/'sizing.json').read_text())['roles'].values():assert sha(q['lut_path'])==q['lut_sha256']==sha(CASE/'lut'/Path(q['lut_path']).name)
    blocks=drawing.parse_source(CASE/'circuit.scs');assert set(blocks)=={'tx_driver_28g'}
    for q in blocks['tx_driver_28g']['instances'].values():
        assert q['model'] in ['n18','capacitor','inductor'];p=q['parameters']
        if q['model']=='n18':assert .19e-6<=drawing.numeric(p['w'])<=100e-6 and .18e-6<=drawing.numeric(p['l'])<=20e-6 and drawing.numeric(p.get('m','1'))>0
        else:assert drawing.numeric(p['c' if q['model']=='capacitor' else 'l'])>0
    sc=drawing.audit_slot(32);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    detail=dict(prbs7=pdetail,sensitivity=sdetail,ac_phase_units=dict(acceptance='Degrees exported explicitly for original analyzer; physical radian differentiation independently agrees',physical_group_delay_variation_s=independent_gd,incorrect_radian_as_degree_diagnostic_s=raw_rad['group_delay_var_s']))
    write_json(CASE/'independent_measurement_details.json',detail)
    a=dict(generated_at=now(),status='passed',circuit_sha256=r['circuit_sha256'],results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),measurement_cross_checks=checks,original_nominal_checks=original,original_model_hashes_unchanged=True,source_snapshot_hashes_verified=True,lut_hashes_unchanged=True,run_provenance=logs,numerical_confirmation=conf,schematic_instances=sc['source_definition_count'],schematic_terminals=sc['source_terminal_count'],pdf_review_pending=True,full_upstream_signoff=False,method='Independent vectorized crossing, eye, edges, jitter, static and time-weighted power reductions; all23 frozen original checks at explicit TT only. Full exact PWL fixtures retained; unique crossings and strict counts/signs additionally required. AC parser supplied degrees; physical radian derivative cross-check. Other2pairedPVTpoints excluded.',independent_details=detail)
    write_json(CASE/'verification_audit.json',a);note='# 第32项独立测量复核\n\n'+a['method']+'\n\n|测量|报告|独立值|绝对差|\n|---|---:|---:|---:|\n'
    for q in checks:note+=f"|{q['metric']}|{q['report']:.12g}|{q['independent']:.12g}|{q['absolute_difference']:.3g}|\n"
    (CASE/'measurement-review.md').write_text(note);print(json.dumps(dict(status='passed',measurements=len(checks),instances=sc['source_definition_count'],terminals=sc['source_terminal_count'],original_checks=original,delays_ps={k:detail[k]['mean_delay_s']*1e12 for k in ['prbs7','sensitivity']}),ensure_ascii=False))

if __name__=='__main__':main()
