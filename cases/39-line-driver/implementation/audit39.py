"""Independent nominal line-driver measurements and original checker calls."""
from common import *
import importlib.util
import audit_schematic_independent as drawing
CASE=ROOT/'cases/39-line-driver'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];assert r['all_nominal_checks_complete'] and r['nonrelaxable_guards_pass']
    groups={k:ROOT/p for k,p in r['groups'].items()};out={};checks=[]
    d=data(groups['loop'],'ac.ac');o=dc(groups['loop']);f=d['freq'];ratio=-d['vout']/d['fbv'];db=20*np.log10(abs(ratio));ph=np.unwrap(np.angle(ratio))*180/np.pi
    ixs=[i for i in range(len(f)-1) if db[i]>=0>db[i+1]];assert len(ixs)==1;i=ixs[0];alpha=db[i]/(db[i]-db[i+1]);assert max(db[i+1:])<0
    out.update(loop_gain_10hz_db=float(np.interp(np.log10(10),np.log10(f),db)),ugb_hz=float(f[i]*(f[i+1]/f[i])**alpha),phase_margin_deg=float(180+ph[i]+alpha*(ph[i+1]-ph[i])),output_offset_v=abs(o['vout']-.9),power_w=abs(o['vdd']*o['VDD:p']),quiescent_current_a=abs(o['VDD:p']))
    d=data(groups['swing'],'swing.dc');x=d['vs'];y=d['vout'];goal=1.8-x;err=abs(y-goal);mid=int(np.argmin(abs(goal-.9)));assert err[mid]<=.02 and len(x)==801
    lo=hi=mid
    while lo>0 and err[lo-1]<=.02:lo-=1
    while hi+1<len(x) and err[hi+1]<=.02:hi+=1
    out.update(closed_loop_range_vpp=float(goal[lo]-goal[hi]),range_low_v=float(goal[hi]),range_high_v=float(goal[lo]),max_accepted_tracking_error_v=float(max(err[lo:hi+1])))
    sys.path.insert(0,str(CASE/'source/tests'));sp=importlib.util.spec_from_file_location('line_driver_original',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(sp);sp.loader.exec_module(up)
    d=data(groups['thd'],'tran.tran');t=d['time'];y=d['vout'];assert abs(t[-1]-400e-6)<1e-12
    out.update(up.harmonic_fit(t.tolist(),y.tolist()))
    tt=np.arange(2048)*200e-6/2048+200e-6;ang=2*np.pi*20e3*tt;yy=np.interp(tt,t,y)
    mat=np.column_stack([np.ones(len(tt))]+[fn(k*ang) for k in range(1,10) for fn in [np.sin,np.cos]])
    coef=np.linalg.lstsq(mat,yy,rcond=None)[0];amps=np.hypot(coef[1::2],coef[2::2]);assert abs(amps[0]-out['fundamental_v'])<1e-12 and abs(100*np.linalg.norm(amps[1:])/amps[0]-out['thd_pct'])<1e-10
    current=-d['VDD:p'];peak=max(float(current[j]) for j in range(len(t)) if 200e-6<=t[j]<=400e-6);peak=max(peak,float(np.interp(200e-6,t,current)),float(np.interp(400e-6,t,current)))
    out.update(peak_supply_current_a=peak,drive_ratio=peak/out['quiescent_current_a'])
    assert max(abs(d['vs']-(.9+.6*np.sin(2*np.pi*20e3*t))))<1e-10
    for key,val in out.items():
        difference=abs(val-v[key]);assert difference<=max(1e-12,abs(val)*1e-7),(key,val,v[key]);checks.append(dict(metric=key,report=v[key],independent=float(val),absolute_difference=difference,passed=True))
    row=dict(name='SMIC18 TT1.8V27C',point=up.NOMINAL,**out)
    original={**up.loop_checks([row],1),**up.distortion_check([row],1),**up.drive_check([row],[row],1),**up.swing_check([row],1)}
    original_checks=[dict(name=k,passed=q[1],detail=q[2]) for k,q in original.items()];assert all(q['passed'] for q in original_checks)
    src=json.loads((CASE/'source_provenance.json').read_text())
    for rel,h in src['files'].items():assert sha(CASE/'source'/rel)==h==sha(Path(src['task'])/rel)
    model=model_provenance();assert model==json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    c=json.loads((CASE/'numerical_confirmation.json').read_text());assert c['passed'] and c['final_groups']==r['groups'] and c['circuit_sha256']==r['circuit_sha256'];logs=[]
    for label,p in list(r['groups'].items())+[('baseline_thd',c['baseline_groups']['thd'])]:
        rd=ROOT/p;m=json.loads((rd/'run.json').read_text());assert m['status']=='completed' and not m['warnings'] and m['models']==model and m['temperature_C']==27 and m['model_dimensions_valid']
        assert sha(ROOT/m['netlist'])==m['netlist_sha256'];b=(ROOT/m['netlist']).read_text()
        for required in ['IREF (vdd iref) isource dc=50u','R1 (vs vinn) resistor r=10k','CAC (vout la) capacitor c=1u','RL (la 0) resistor r=300','CL (vout 0) capacitor c=200p']:assert required in b
        for source,q in m['dependencies'].items():
            assert sha(ROOT/q['snapshot'])==q['sha256']
            if source.endswith('circuit.scs'):assert q['sha256']==sha(CASE/'circuit.scs')==r['circuit_sha256']
            if source.endswith('contract.json'):assert q['sha256']==sha(CASE/'contract.json')==r['contract_sha256']
        log='\n'.join(p.read_text(errors='replace') for p in (rd/'output').glob('*.log'));assert re.search(r'spectre completes with 0 errors',log) and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',log)
        logs.append(dict(group=label,run=p,actual_error_free=True,warnings=m['warnings'],bridge_errors=m['errors']))
    for q in json.loads((CASE/'sizing.json').read_text())['roles'].values():assert sha(q['lut_path'])==q['lut_sha256']==sha(CASE/'lut'/Path(q['lut_path']).name)
    blocks=drawing.parse_source(CASE/'circuit.scs');assert set(blocks)=={'low_power_line_driver'}
    for q in blocks['low_power_line_driver']['instances'].values():
        assert q['model'] in ['n18','p18','resistor','capacitor']
        if q['model'] in ['n18','p18']:
            p=q['parameters'];assert .19e-6<=drawing.numeric(p['w'])<=100e-6 and .18e-6<=drawing.numeric(p['l'])<=20e-6 and drawing.numeric(p.get('m','1'))>0
        else:assert drawing.numeric(q['parameters']['r' if q['model']=='resistor' else 'c'])>0
    sc=drawing.audit_slot(39);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    a=dict(generated_at=now(),status='passed',circuit_sha256=r['circuit_sha256'],results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),measurement_cross_checks=checks,original_nominal_checks=original_checks,original_model_hashes_unchanged=True,source_snapshot_hashes_verified=True,lut_hashes_unchanged=True,run_provenance=logs,numerical_confirmation=c,schematic_instances=sc['source_definition_count'],schematic_terminals=sc['source_terminal_count'],pdf_review_pending=True,full_upstream_signoff=False,method='Independent AC crossings and contiguous swing walk; unchanged original harmonic_fit and all8 check functions at explicit expected=1; alternate least-squares harmonic fit. Other44PVTpoints excluded. Native device policy and literal external300ohm/200pF loads verified.')
    write_json(CASE/'verification_audit.json',a);note='# 第39项独立测量复核\n\n'+a['method']+'\n\n|测量|报告|独立值|绝对差|\n|---|---:|---:|---:|\n'
    for q in checks:note+=f"|{q['metric']}|{q['report']:.12g}|{q['independent']:.12g}|{q['absolute_difference']:.3g}|\n"
    (CASE/'measurement-review.md').write_text(note);print(json.dumps(dict(status='passed',measurements=len(checks),instances=sc['source_definition_count'],terminals=sc['source_terminal_count'],original_checks=original_checks),ensure_ascii=False))

if __name__=='__main__':main()
