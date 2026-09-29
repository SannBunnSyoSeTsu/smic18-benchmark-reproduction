"""Independent time-window integration and original nominal pump verifier."""
from common import *
import importlib.util
import audit_schematic_independent as drawing

CASE=ROOT/'cases/15-unregulated-pump'

def independent_window(d,name,start,stop):
    t=d['time'];a=d[name];pairs=[(float(start),float(np.interp(start,t,a)))]
    pairs.extend((float(x),float(y)) for x,y in zip(t,a) if start<x<stop)
    pairs.append((float(stop),float(np.interp(stop,t,a))))
    area=sum((b[0]-a[0])*(a[1]+b[1])/2 for a,b in zip(pairs,pairs[1:]))
    return dict(avg=area/(stop-start),minimum=min(y for x,y in pairs),maximum=max(y for x,y in pairs),points=len(pairs))

def main():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];source=json.loads((CASE/'source_provenance.json').read_text())
    waves={k:data(ROOT/p,'tran.tran') for k,p in r['groups'].items()}
    results={};checks=[]
    for key,group,node,field,start,stop in [('vout_en_avg','enabled','VOUT','avg',190e-6,200e-6),('vout_en_max','enabled','VOUT','maximum',190e-6,200e-6),('vout_en_min','enabled','VOUT','minimum',190e-6,200e-6),('i_avdd_en_avg','enabled','VSENSE:p','avg',190e-6,200e-6),('i_avdd_pd_avg','disabled','VSENSE:p','avg',9e-6,10e-6)]:
        q=independent_window(waves[group],node,start,stop);answer=q[field];assert abs(answer-v[key])<max(1e-14,abs(answer)*1e-9)
        checks.append(dict(metric=key,report=v[key],independent=answer,absolute_difference=abs(answer-v[key]),points=q['points'],passed=True));results[key]=answer
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('pump_upstream',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    upchecks=up.checks([dict(point=up.NOMINAL,name='SMIC18TT/1.8V/40C',**results)],{up.NOMINAL})
    tier=r['status'].removeprefix('complete_');assert r['pass_tiers'][tier] and r['terminal_screen_valid']
    if tier=='original':assert all(x[1] for x in upchecks)
    assert r['model_operating_range_valid']
    stimulus_checks=[]
    for group,d in waves.items():
        assert np.max(abs(d['ensrc']-(1.8 if group=='enabled' else 0)))<1e-12
        assert abs(np.ptp(d['clksrc'])-1.8)<1e-12
        start=190e-6 if group=='enabled' else 9e-6;t=d['time'];u=d['clksrc'];mask=t>=start;t=t[mask];u=u[mask]
        ix=np.flatnonzero((u[:-1]<.9)&(u[1:]>=.9));edges=t[ix]+(.9-u[ix])*(t[ix+1]-t[ix])/(u[ix+1]-u[ix])
        assert len(edges)>=9 and np.max(abs(np.diff(edges)-100e-9))<1e-11
        stimulus_checks.append(dict(group=group,clock_still_running=True,period_s=float(np.mean(np.diff(edges))),observed_rising_edges=len(edges),enable_source_V=1.8 if group=='enabled' else 0))
    for rel,h in source['files'].items():assert sha(CASE/'source'/rel)==h==sha(Path(source['task'])/rel)
    models=model_provenance();assert models==json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    hd=json.loads((CASE/'hd_cells_manifest.json').read_text());assert not hd['sizes_modified'] and not hd['model_names_modified'];assert sha(hd['source'])==hd['source_sha256'] and sha(CASE/'hd_cells.scs')==hd['output_sha256']
    logs=[]
    for group,p in r['groups'].items():
        run=ROOT/p;m=json.loads((run/'run.json').read_text());assert m['status']=='completed' and m['model_dimensions_valid'] and m['models']==models and m['temperature_C']==40
        assert sha(ROOT/m['netlist'])==m['netlist_sha256']
        for src,q in m['dependencies'].items():
            assert sha(ROOT/q['snapshot'])==q['sha256']
            if src.endswith('circuit.scs'):assert q['sha256']==sha(CASE/'circuit.scs')==r['circuit_sha256']
            if src.endswith('contract.json'):assert q['sha256']==sha(CASE/'contract.json')==r['contract_sha256']
        rawlog='\n'.join(x.read_text(errors='replace') for x in (run/'output').glob('*.log'))
        assert re.search(r'spectre completes with 0 errors',rawlog) and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',rawlog)
        assert all('SPECTRE-16780' in x for x in m['warnings']),m['warnings']
        logs.append(dict(group=group,run=p,warnings=m['warnings'],bridge_errors=m['errors'],real_error_free=True))
    for q in json.loads((CASE/'sizing.json').read_text())['roles'].values():assert sha(q['lut_path'])==q['lut_sha256']==sha(CASE/'lut'/Path(q['lut_path']).name)
    confirmation=json.loads((CASE/'numerical_confirmation.json').read_text());assert confirmation['passed'] and confirmation['circuit_sha256']==r['circuit_sha256']
    assert confirmation['refined_run_dirs']==r['run_dirs']
    sc=drawing.audit_slot(15);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    a=dict(generated_at=now(),status='passed',circuit_sha256=r['circuit_sha256'],results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),measurement_cross_checks=checks,original_nominal_checks=[dict(name=x[0],passed=x[1],detail=x[2]) for x in upchecks],original_model_hashes_unchanged=True,source_snapshot_hashes_verified=True,lut_hashes_unchanged=True,hd_original_geometry_verified=True,run_provenance=logs,numerical_confirmation=confirmation,schematic_instances=sc['source_definition_count'],schematic_terminals=sc['source_terminal_count'],pdf_review_pending=True,full_upstream_signoff=False,method='Independently integrate raw Spectre windows with scalar trapezoid sums and original verifier checks atTT40C. Other seven representative points excluded.')
    a['stimulus_checks']=stimulus_checks
    write_json(CASE/'verification_audit.json',a)
    note='# 第15项独立复核\n\n'+a['method']+'\n\n|指标|报告|独立值|绝对差|\n|---|---:|---:|---:|\n'
    for q in checks:note+=f"|{q['metric']}|{q['report']:.12g}|{q['independent']:.12g}|{q['absolute_difference']:.3g}|\n"
    note+='\n原始判据和完整数值收敛记录见verification_audit.json。图纸含所有模拟MOS/MIM和原厂HD单元的供电及井端。\n';(CASE/'measurement-review.md').write_text(note)
    print(json.dumps(dict(status='passed',measurement_checks=len(checks),instances=sc['source_definition_count'],terminals=sc['source_terminal_count'])))

if __name__=='__main__':main()
