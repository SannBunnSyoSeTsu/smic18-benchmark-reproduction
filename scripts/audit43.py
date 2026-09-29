"""Independent traveling-wave/power/noise RF audit and original7 checks."""
from common import *
import importlib.util
import audit_schematic_independent as drawing
CASE=ROOT/'cases/43-inductive-lna'

def waves(d):
    root=np.sqrt(50);forward_i=(1-d['rfinf'])/50;reverse_i=(1-d['rfoutr'])/50
    af=(d['rfinf']+50*forward_i)/(2*root);ar=(d['rfoutr']+50*reverse_i)/(2*root)
    s11=(d['rfinf']-50*forward_i)/(2*root)/af;s22=(d['rfoutr']-50*reverse_i)/(2*root)/ar
    return s11,d['rfoutf']/root/af,s22,d['rfinr']/root/ar

def main():
    r=json.loads((CASE/'latest_results.json').read_text());assert r['status']=='complete_original' and r['nonrelaxable_guards_pass'];v=r['values'];rd=ROOT/r['groups']['rf'];d=data(rd,'band.ac');w=data(rd,'wide.ac');no=data(rd,'noise.noise',required=['in','out']);o=dc(rd)
    assert len(d['freq'])==len(no['freq'])==201 and len(w['freq'])==1601
    assert np.allclose(d['freq'],np.linspace(2.35e9,2.45e9,201),rtol=1e-13)
    assert np.allclose(w['freq'],np.geomspace(.1e9,10e9,1601),rtol=1e-12)
    s11,s21,s22,s12=waves(d);gt=(abs(d['rfoutf'])**2/(2*50))/(1/(8*50));assert np.allclose(gt,abs(s21)**2,rtol=1e-13)
    gain=10*np.log10(gt);decibels=lambda x:20*np.log10(abs(x))
    out=dict(transducer_gain_db_min=float(min(gain)),transducer_gain_db_max=float(max(gain)),gain_ripple_db=float(max(gain)-min(gain)),s11_db_max=float(max(decibels(s11))),s22_db_max=float(max(decibels(s22))),reverse_isolation_db_max=float(max(decibels(s12))))
    a,b,c,e=waves(w);delta=a*c-b*e;k=(1-abs(a)**2-abs(c)**2+abs(delta)**2)/(2*abs(b*e))
    out.update(stability_k_min=float(min(k)),stability_delta_max=float(max(abs(delta))))
    referred=no['out']/abs(d['rfoutf']);rel=float(max(abs(referred-no['in'])/no['in']));assert rel<1e-9
    out.update(input_noise_density_max_vrthz=float(max(referred)),noise_figure_db=float(10*np.log10(max(referred**2)/(4*1.380649e-23*300.15*50))),power_w=float(-o['VDDF:p']*o['vddf']),iref_voltage_v=o['ireff'],iref_headroom_v=o['vddf']-o['ireff'])
    assert min(no['in'])>np.sqrt(4*1.380649e-23*300.15*50) and min(k)>1 and max(abs(delta))<1
    checks=[]
    for key,value in out.items():
        diff=abs(value-v[key]);assert diff<=max(1e-17,abs(value)*1e-9),(key,value,v[key]);checks.append(dict(metric=key,report=v[key],independent=value,absolute_difference=diff,passed=True))
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('lna_original',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    row=dict(point=up.NOMINAL,name='SMIC18 TT1.8V27C',**out);oc=up.rf_checks([row],{up.NOMINAL});assert len(oc)==7 and all(q[1] for q in oc);original=[dict(name=n,passed=bool(ok),detail=msg) for n,ok,msg in oc]
    source=json.loads((CASE/'source_provenance.json').read_text())
    for path,h in source['files'].items():assert sha(CASE/'source'/path)==h==sha(Path(source['task'])/path)
    model=model_provenance();assert model==json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    env=json.loads((CASE/'environment.json').read_text());size=json.loads((CASE/'sizing.json').read_text())
    assert env['rf_model_files']==size['rf_model_files']==r['rf_model_hashes']
    for path,h in size['rf_model_files'].items():assert sha(path)==h
    for q in size['roles'].values():assert sha(q['lut_path'])==q['lut_sha256']==sha(CASE/'lut'/Path(q['lut_path']).name)
    conf=json.loads((CASE/'numerical_confirmation.json').read_text());assert conf['passed'] and conf['final_groups']==r['groups'] and conf['circuit_sha256']==r['circuit_sha256']
    logs=[]
    for label,path in [('final',r['groups']['rf']),('baseline',conf['baseline_groups']['rf'])]:
        p=ROOT/path;m=json.loads((p/'run.json').read_text());assert m['status']=='completed' and not m['warnings'] and m['models']==model and m['temperature_C']==27 and m['model_dimensions_valid'];assert sha(ROOT/m['netlist'])==m['netlist_sha256'];text=(ROOT/m['netlist']).read_text()
        for line in ['VDDF (vddf 0) vsource dc=1.8','IREFF (vddf ireff) isource dc=50u','VSF (srcf 0) vsource dc=0 mag=1','RSF (srcf rfinf) resistor r=50','RLF (rfoutf 0) resistor r=50 isnoisy=no','VSR (srcr 0) vsource dc=0 mag=1','RSR (srcr rfoutr) resistor r=50','RINR (rfinr 0) resistor r=50']:assert line in text,line
        for _,q in m['dependencies'].items():assert sha(ROOT/q['snapshot'])==q['sha256']
        assert sha(p/'inputs/circuit.scs')==sha(CASE/'circuit.scs')==r['circuit_sha256']
        assert sha(p/'inputs/contract.json')==r['contract_sha256']
        assert json.loads((p/'inputs/sizing.json').read_text())['rf_model_files']==size['rf_model_files']
        log='\n'.join(x.read_text(errors='replace') for x in (p/'output').glob('*.log'));assert 'spectre completes with 0 errors, 0 warnings' in log and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',log)
        logs.append(dict(group=label,run=path,actual_error_free=True,warnings=m['warnings'],bridge_errors=m['errors'],fixtures_verified=True))
    blocks=drawing.parse_source(CASE/'circuit.scs');assert set(blocks)=={'inductive_lna'}
    for dev,q in blocks['inductive_lna']['instances'].items():
        m=q['model'];p=q['parameters'];assert m in ['n18','p18','rpposab_3t','mim1_rf','ind_rf']
        if m in ['n18','p18']:
            assert .19e-6<=drawing.numeric(p['w'])<=100e-6 and .18e-6<=drawing.numeric(p['l'])<=20e-6 and drawing.numeric(p.get('m','1'))>0
        elif m=='ind_rf':assert abs(drawing.numeric(p['r'])-60e-6)<1e-15 and drawing.numeric(p['n'])==3.5
        elif m=='mim1_rf':assert abs(drawing.numeric(p['wr'])-30e-6)<1e-15 and 10e-6<=drawing.numeric(p['lr'])<=30.000001e-6
        else:assert drawing.numeric(p['w'])>0 and drawing.numeric(p['l'])>0
    sc=drawing.audit_slot(43);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    details=dict(noise_referral_maximum_relative_difference=rel,forward_available_input_power_W=1/(8*50),traveling_wave_definition='a=(V+50I)/(2sqrt50), b=(V-50I)/(2sqrt50)',noise_definition='OutputnoisePSD divided by loaded source-to-output gain squared then4kT50; no subtracting DUTnoise.',baseline_points=conf['baseline_grid'],final_points=conf['final_grid'])
    write_json(CASE/'independent_measurement_details.json',details)
    audit=dict(generated_at=now(),status='passed',circuit_sha256=r['circuit_sha256'],results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),measurement_cross_checks=checks,original_nominal_checks=original,original_model_hashes_unchanged=True,rf_model_hashes_unchanged=True,source_snapshot_hashes_verified=True,lut_hashes_unchanged=True,run_provenance=logs,numerical_confirmation=conf,schematic_instances=sc['source_definition_count'],schematic_terminals=sc['source_terminal_count'],pdf_review_pending=True,full_upstream_signoff=False,independent_details=details,method='Traveling-wave voltage/current construction and available/loaded power ratio independently reproduce allSparams/gain; outputnoise andACgain independently reconstruct inputreferral/NF; original7checks on explicitnominalpoint only. Finegrid includesalloriginalfrequencies. NativeRFmodel/source/LUT hashes verified; noPDKalteration.')
    write_json(CASE/'verification_audit.json',audit);md='# 第43项独立测量复核\n\n'+audit['method']+'\n\n|测量|报告|独立值|绝对差|\n|---|---:|---:|---:|\n'
    for q in checks:md+=f"|{q['metric']}|{q['report']:.12g}|{q['independent']:.12g}|{q['absolute_difference']:.3g}|\n"
    (CASE/'measurement-review.md').write_text(md);print(json.dumps(dict(status='passed',measurements=len(checks),instances=sc['source_definition_count'],terminals=sc['source_terminal_count'],original_checks=original),ensure_ascii=False))

if __name__=='__main__':main()
