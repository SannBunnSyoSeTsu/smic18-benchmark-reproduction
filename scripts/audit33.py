"""Independent original-window, derivative, AC and noise checks for task33."""
from common import *
import importlib.util
import audit_schematic_independent as drawing

CASE=ROOT/'cases/33-sampling-ota-gain1'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];assert r['all_nominal_checks_complete'] and r['nonrelaxable_guards_pass']
    groups={k:ROOT/p for k,p in r['groups'].items()};out={};checks=[]
    d=data(groups['loop'],'ac.ac');o=dc(groups['loop']);f=d['freq'];h=d['voutp']-d['voutn'];loop=h/2;db=20*np.log10(abs(loop));ph=np.unwrap(np.angle(loop))*180/np.pi
    crossing=[i for i in range(len(f)-1) if db[i]>=0>db[i+1]];assert len(crossing)==1;i=crossing[0];ratio=db[i]/(db[i]-db[i+1]);assert max(db[i+1:])<0
    out.update(loop_ugb_hz=float(f[i]*(f[i+1]/f[i])**ratio),phase_margin_deg=float(180+ph[i]+ratio*(ph[i+1]-ph[i])),low_frequency_loop_gain_db=float(db[0]),closed_loop_differential_gain_db=float(20*np.log10(abs(h[0]/(1+h[0]/2)))),power_w=-1.8*o['VDD:p'],output_common_mode_error_v=abs((o['voutp']+o['voutn'])/2-.9))
    d=data(groups['settling'],'tran.tran');t=d['time'];y=d['voutp']-d['voutn'];stim=[]
    for key,time,target in [('rise_dynamic',65e-9,-.9),('fall_dynamic',145e-9,0),('high_static',104e-9,-.9),('low_static',169e-9,0)]:out[key+'_output_v']=float(np.interp(time,t,y));out[key+'_error_fraction']=abs(out[key+'_output_v']-target)/.9
    for name,start,stop,target in [('rise',25e-9,104e-9,-.9),('fall',105e-9,170e-9,0)]:
        mask=(t>=start)&(t<=stop);tt=t[mask];ee=abs(y[mask]-target)-.9e-3;cross=[]
        for j in range(len(tt)-1):
            if ee[j]*ee[j+1]<=0 and ee[j]!=ee[j+1]:cross.append(float(tt[j]-ee[j]*(tt[j+1]-tt[j])/(ee[j+1]-ee[j])))
        assert cross and abs(np.interp(stop,t,y)-target)<=.9e-3;out[name+'_settling_time_s']=cross[-1]-start
    assert abs(np.interp(20e-9,t,d['srcp'])-.9)<1e-12 and abs(np.interp(30e-9,t,d['srcp'])-.45)<1e-12 and abs(np.interp(30e-9,t,d['srcn'])-1.35)<1e-12
    assert abs(np.interp(110e-9,t,d['srcp'])-.9)<1e-12
    stim.append(dict(test='settling',initial_sources_V=[.9,.9],active_sources_V=[.45,1.35],passed=True))
    d=data(groups['ranges'],'swing.dc');x=d['vin_diff'];y=d['voutp']-d['voutn'];g=[]
    for j in range(len(x)):
        lo=max(0,j-1);hi=min(len(x)-1,j+1);g.append((y[hi]-y[lo])/(x[hi]-x[lo]))
    db=20*np.log10(g);lim=max(db)-3;cross=[]
    for j in range(len(x)-1):
        if (db[j]-lim)*(db[j+1]-lim)<0:cross.append(float(y[j]+(lim-db[j])*(y[j+1]-y[j])/(db[j+1]-db[j])))
    assert len(x)==81 and len(cross)==2;out.update(output_range_min_v=cross[0],output_range_max_v=cross[1],output_range_v=cross[1]-cross[0],open_loop_gain_peak_db=float(max(db)))
    d=data(groups['noise'],'noise.noise',required=['out']);f=d['freq'];n=abs(d['out']);assert abs(f[0]-10)<1e-9 and abs(f[-1]-1e10)<1
    out['output_noise_vrms']=float(np.sqrt(sum((f[j+1]-f[j])*(n[j+1]**2+n[j]**2)/2 for j in range(len(f)-1))))
    assert r['noise_quadrature']['relative_difference']<.001
    d=data(groups['cmfb'],'tran.tran');t=d['time'];cm=(d['voutp']+d['voutn'])/2;err=abs(cm-(d['routp']+d['routn'])/2);m=(t>=20e-9)&(t<=45e-9)
    out.update(cmfb_static_error_v=float(abs(np.interp(15e-9,t,cm)-.9)),cmfb_max_deviation_v=float(max(err[m])),cmfb_residual_20ns_v=float(np.interp(60.2e-9,t,err)),cmfb_residual_100ns_v=float(np.interp(140.2e-9,t,err)))
    for node in ['VSENSEP:p','VSENSEN:p']:
        assert abs(np.interp(30e-9,t,d[node])-50e-6)<1e-13 and abs(np.interp(15e-9,t,d[node]))<1e-13 and abs(np.interp(45e-9,t,d[node]))<1e-13
    stim.append(dict(test='CMFB',per_output_pulse_A=50e-6,reference='undisturbed identical instance',passed=True))
    for key,value in out.items():
        diff=abs(value-v[key]);assert diff<=max(1e-12,abs(value)*1e-7),(key,value,v[key]);checks.append(dict(metric=key,report=v[key],independent=float(value),absolute_difference=diff,passed=True))
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('sampling_upstream',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    # Characterization-only scalars retain original names; scored scalars use independent values.
    row={'name':'SMIC18TT1.8V27C','point':up.NOMINAL,**v,**out};ok,msg=up.nominal_functional(row,row)
    comparisons=[dict(name='original_nominal_functional',passed=ok,detail=msg)]
    for key,lim,ismin,metrics in [('output_noise_vrms',300e-6,False,up.NOISE_METRICS),('cmfb_max_deviation_v',.15,False,up.CMFB_METRICS),('cmfb_residual_20ns_v',.05,False,up.CMFB_METRICS),('cmfb_residual_100ns_v',.02,False,up.CMFB_METRICS),('power_w',.005,False,up.LOOP_METRICS)]:
        name,passed,detail=up.limit_check(key,[row],1,metrics,key,lim,ismin,1,'SI');comparisons.append(dict(name=name,passed=passed,detail=detail))
    comparisons.append(dict(name='original_3dB_range',passed=out['output_range_v']>=up.OUTPUT_RANGE_V,detail=f"{out['output_range_v']:.12g}V >= {up.OUTPUT_RANGE_V:g}V"))
    assert ok and r['pass_tiers'][r['status'].removeprefix('complete_')]
    source=json.loads((CASE/'source_provenance.json').read_text())
    for rel,h in source['files'].items():assert sha(CASE/'source'/rel)==h==sha(Path(source['task'])/rel)
    models=model_provenance();assert models==json.loads((ROOT/'environment.json').read_text())['model_file_hashes'];logs=[]
    conf=json.loads((CASE/'numerical_confirmation.json').read_text());assert conf['passed'] and conf['circuit_sha256']==r['circuit_sha256']
    for key,run in list(groups.items())+[('range_resolution',ROOT/conf['diagnostic_run'])]:
        m=json.loads((run/'run.json').read_text());assert m['status']=='completed' and m['models']==models and m['model_dimensions_valid'] and m['temperature_C']==27
        assert sha(ROOT/m['netlist'])==m['netlist_sha256']
        for src,q in m['dependencies'].items():
            assert sha(ROOT/q['snapshot'])==q['sha256']
            if src.endswith('circuit.scs'):assert q['sha256']==sha(CASE/'circuit.scs')==r['circuit_sha256']
            if src.endswith('contract.json'):assert q['sha256']==sha(CASE/'contract.json')==r['contract_sha256']
        log='\n'.join(p.read_text(errors='replace') for p in (run/'output').glob('*.log'));assert re.search(r'spectre completes with 0 errors',log) and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',log)
        assert not m['warnings'],m['warnings'];logs.append(dict(group=key,run=str(run.relative_to(ROOT)),real_error_free=True,warnings=m['warnings'],bridge_errors=m['errors']))
    for q in json.loads((CASE/'sizing.json').read_text())['roles'].values():assert sha(q['lut_path'])==q['lut_sha256']==sha(CASE/'lut'/Path(q['lut_path']).name)
    sc=drawing.audit_slot(33);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    a=dict(generated_at=now(),status='passed',circuit_sha256=r['circuit_sha256'],results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),measurement_cross_checks=checks,original_nominal_checks=comparisons,original_model_hashes_unchanged=True,source_snapshot_hashes_verified=True,lut_hashes_unchanged=True,run_provenance=logs,stimulus_checks=stim,numerical_confirmation=conf,schematic_instances=sc['source_definition_count'],schematic_terminals=sc['source_terminal_count'],pdf_review_pending=True,full_upstream_signoff=False,mismatch_samples_executed=0,method='Independent scalar interpolation, last crossing,81point central differences and noise quadrature; unchanged upstream nominal_functional and limit_check with explicit nominal expected count1. No claim of30point PVT or20sample mismatch completion.')
    write_json(CASE/'verification_audit.json',a);note='# 第33项独立复核\n\n'+a['method']+'\n\n|指标|报告|独立值|绝对差|\n|---|---:|---:|---:|\n'
    for q in checks:note+=f"|{q['metric']}|{q['report']:.12g}|{q['independent']:.12g}|{q['absolute_difference']:.3g}|\n"
    (CASE/'measurement-review.md').write_text(note);print(json.dumps(dict(status='passed',measurement_checks=len(checks),instances=sc['source_definition_count'],terminals=sc['source_terminal_count'],original_checks=comparisons),ensure_ascii=False))

if __name__=='__main__':main()
