"""Independent full14point power integration and unchanged upstream E1-E5."""
from common import *
import importlib.util
import audit_schematic_independent as drawing

CASE=ROOT/'cases/01-class-d'

def independent_measure(d,load):
    t=d['time'];ix=np.flatnonzero((t>18e-6)&(t<20e-6));tt=np.r_[18e-6,t[ix],20e-6]
    q={k:np.r_[np.interp(18e-6,t,a),a[ix],np.interp(20e-6,t,a)] for k,a in d.items() if k!='time'}
    def mean(a):return sum(float(tt[k+1]-tt[k])*float(a[k+1]+a[k])/2 for k in range(len(tt)-1))/2e-6
    vdd=abs(1.8*mean(q['VDD:p']));vss=abs(mean(q['vss']*q['VSS:p']));clk=abs(mean(q['clk_src']*q['VCLK:p']));pin=vdd+vss+clk;pout=abs(mean(q['rl_node']*q['VMEAS_RL:p']))
    return dict(p_vdd_W=vdd,p_vss_W=vss,p_clk_W=clk,p_in_W=pin,p_out_W=pout,efficiency=pout/pin,p_out_square_W=mean(q['rl_meas']**2/load))

def main():
    r=json.loads((CASE/'latest_results.json').read_text());assert r['all_nominal_checks_complete'] and r['model_operating_range_valid']
    tier=r['status'].removeprefix('complete_');assert r['pass_tiers'][tier]
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('classd_upstream',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    checks=[];raw={};stimulus=[];logs=[];models=model_provenance()
    assert models==json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    for i,(temp,load) in enumerate((t,l) for t in [27,125] for l in [1,2,3,6,8,12,16]):
        key=f't{temp}_r{load}';run=ROOT/r['groups'][key];d=data(run,'tran.tran');a=independent_measure(d,load);v=r['values'][key]
        for metric,value in a.items():
            diff=abs(value-v[metric]);assert diff<max(1e-13,abs(value)*1e-8)
            checks.append(dict(point=key,metric=metric,independent=value,report=v[metric],absolute_difference=diff,passed=True))
        assert abs(a['p_out_W']-a['p_out_square_W'])<1e-10 and 0<a['efficiency']<=1+1e-6
        for suffix,name in [('p_in','p_in_W'),('p_out','p_out_W'),('efficiency','efficiency')]:raw[f'm{i}_{suffix}']=a[name]
        t=d['time'];u=d['clk_src'];m=t>=18e-6;t=t[m];u=u[m];ix=np.flatnonzero((u[:-1]<.9)&(u[1:]>=.9));edge=t[ix]+(.9-u[ix])*(t[ix+1]-t[ix])/(u[ix+1]-u[ix]);assert len(edge)==10 and np.max(abs(np.diff(edge)-200e-9))<1e-11
        assert abs(np.max(u)-1.8)<1e-12 and abs(np.min(u))<1e-12
        stimulus.append(dict(point=key,rising_edges=len(edge),period_s=float(np.mean(np.diff(edge))),passed=True))
        meta=json.loads((run/'run.json').read_text());assert meta['status']=='completed' and meta['model_dimensions_valid'] and meta['models']==models and meta['temperature_C']==temp
        assert sha(ROOT/meta['netlist'])==meta['netlist_sha256'];text=(ROOT/meta['netlist']).read_text()
        for expected in [f'temp={temp} ',f'RL (rl_meas vss) resistor r={load}\n','L1 (sw lc_node) inductor l=3u','C1 (lc_node rl_node) capacitor c=345p','RCLK (clk_src clk_in) resistor r=50','rise=2n fall=2n width=98n period=200n','stop=20u'] :assert expected in text,expected
        for src,q in meta['dependencies'].items():
            assert sha(ROOT/q['snapshot'])==q['sha256']
            if src.endswith('circuit.scs'):assert q['sha256']==r['circuit_sha256']==sha(CASE/'circuit.scs')
            if src.endswith('contract.json'):assert q['sha256']==r['contract_sha256']==sha(CASE/'contract.json')
        log='\n'.join(p.read_text(errors='replace') for p in (run/'output').glob('*.log'))
        assert re.search(r'spectre completes with 0 errors',log) and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',log)
        assert all('SPECTRE-16780' in w for w in meta['warnings']),meta['warnings']
        logs.append(dict(point=key,run=r['groups'][key],real_error_free=True,warnings=meta['warnings'],bridge_errors=meta['errors']))
    upstream={};up.run_efficiency=lambda:raw
    def finish(c,n,p):upstream.update(checks=[dict(name=k,passed=b,detail=s) for k,b,s in c],analysis_points=n,original_driver_process_count=p)
    up.finish=finish;assert up.sanity_error(raw) is None;up.main();assert upstream['analysis_points']==14 and len(upstream['checks'])==5
    if tier=='original':assert all(q['passed'] for q in upstream['checks'])
    source=json.loads((CASE/'source_provenance.json').read_text())
    for rel,h in source['files'].items():assert sha(CASE/'source'/rel)==h==sha(Path(source['task'])/rel)
    hd=json.loads((CASE/'hd_cells_manifest.json').read_text());assert not hd['sizes_modified'] and not hd['model_names_modified'];assert sha(hd['source'])==hd['source_sha256'] and sha(CASE/'hd_cells.scs')==hd['output_sha256']
    for q in json.loads((CASE/'sizing.json').read_text())['roles'].values():assert sha(q['lut_path'])==q['lut_sha256']==sha(CASE/'lut'/Path(q['lut_path']).name)
    conf=json.loads((CASE/'numerical_confirmation.json').read_text());assert conf['passed'] and conf['circuit_sha256']==r['circuit_sha256'] and conf['final_groups']==r['groups']
    sc=drawing.audit_slot(1);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    a=dict(generated_at=now(),status='passed',circuit_sha256=r['circuit_sha256'],results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),measurement_cross_checks=checks,original_verifier=upstream,original_model_hashes_unchanged=True,source_snapshot_hashes_verified=True,lut_hashes_unchanged=True,hd_original_geometry_verified=True,run_provenance=logs,stimulus_checks=stimulus,numerical_confirmation=conf,schematic_instances=sc['source_definition_count'],schematic_terminals=sc['source_terminal_count'],pdf_review_pending=True,full_upstream_signoff=False,scope='Complete original TT electrical matrix at27/125C,7loads; SMIC model migration, not Sky130 signoff',method='Scalar time-weighted trapezoid integration of all14 raw PSF windows; original unmodified verifier consumes independently reconstructed m0..m13 measurements.')
    write_json(CASE/'verification_audit.json',a)
    note='# 第01项独立功率复核\n\n'+a['method']+'\n\n|点|指标|报告|独立值|绝对差|\n|---|---|---:|---:|---:|\n'
    for q in checks:note+=f"|{q['point']}|{q['metric']}|{q['report']:.12g}|{q['independent']:.12g}|{q['absolute_difference']:.3g}|\n"
    (CASE/'measurement-review.md').write_text(note);print(json.dumps(dict(status='passed',points=14,measurement_checks=len(checks),original_checks=upstream['checks'],instances=sc['source_definition_count'],terminals=sc['source_terminal_count'])))

if __name__=='__main__':main()
