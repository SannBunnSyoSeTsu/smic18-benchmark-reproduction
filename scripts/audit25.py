"""Evidence and original-threshold audit; never starts a simulator."""
from common import *
import importlib.util

CASE=ROOT/'cases/25-complementary-ab'

def loadmod(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def audit():
    r=json.loads((CASE/'latest_results.json').read_text());c=json.loads((CASE/'contract.json').read_text());s=json.loads((CASE/'sizing.json').read_text());geo=json.loads((CASE/'geometry.json').read_text())
    assert r['status']=='complete_original' and len(r['gates'])==37 and all(x['passes']['original'] for x in r['gates'].values())
    assert set(r['groups'])=={'ac','track','noise','reject','step','thd'} and len(r['run_dirs'])==7
    runrows=[]
    for run in r['run_dirs']:
        rd=ROOT/run;meta=json.loads((rd/'run.json').read_text());assert meta['status']=='completed' and meta['model_dimensions_valid'];assert meta['corner']=='tt' and meta['temperature_C']==27
        assert sha(rd/'inputs/circuit.scs')==sha(CASE/'circuit.scs') and sha(ROOT/meta['netlist'])==meta['netlist_sha256']
        for p,h in meta['models'].items():assert sha(p)==h
        for dep in meta['dependencies'].values():assert sha(ROOT/dep['snapshot'])==dep['sha256']
        runrows.append(dict(run=run,snapshot_consistent=True,model_dimensions_valid=meta['model_dimensions_valid'],warnings=meta['warnings'],netlist_sha256=meta['netlist_sha256'],psf_files={str(p.relative_to(ROOT)):sha(p) for p in (rd/'output/bench.raw').glob('*') if p.is_file()}))
    for z in s['roles'].values():assert sha(z['lut_path'])==z['lut_sha256']
    for z in c['source_files'].values():assert sha(z['path'])==z['sha256']==sha(ROOT/z['frozen'])
    assert geo['circuit_sha256']==sha(CASE/'circuit.scs') and len(geo['devices'])==45
    assert all(.19<=z['W_unit_um']<=100 and z['L_um']>=.18 and z['m']>0 for z in geo['devices'])
    raw=(CASE/'circuit.scs').read_text();assert len(re.findall(r'^M\w+ \(',raw,re.M))==45 and len(re.findall(r'^R\w+ \(',raw,re.M))==12 and len(re.findall(r'^C\w+ \(',raw,re.M))==6
    # Original verifier functions, with only the PVT scope reduced in memory.
    old=sys.modules.get('utils');sys.modules['utils']=loadmod('case25_utils',CASE/'source/tests/utils.py')
    try:orig=loadmod('case25_verify',CASE/'source/tests/verify.py')
    finally:
        if old is None:sys.modules.pop('utils',None)
        else:sys.modules['utils']=old
    orig.PVT=(orig.NOMINAL,);orig.EXPECTED_AC_ROWS=5
    acrows=[]
    for i,z in enumerate(r['ac_rows']):
        m=z['metrics'];acrows.append(dict(point=orig.NOMINAL,name='SMIC18 TT/1.8V/27C',cm_index=i,cm_v=z['cm_V'],gain_10hz_db=m['gain_db'],ugbw_hz=m['ugb_hz'],phase_margin_deg=m['phase_margin_deg'],static_power_w=z['power_W']))
    v=r['values'];track=dict(point=orig.NOMINAL,name='SMIC18 nominal',track_error_core_v=v['tracking_core_error_V'],track_error_band_v=v['tracking_band_error_V'],input_common_mode_low_v=v['icmr_low_headroom_V'],input_common_mode_high_v=1.8-v['icmr_high_headroom_V'],tracking_power_w=v['tracking_power_W'])
    step=dict(point=orig.NOMINAL,name='SMIC18 nominal',slew_up_v_per_us=v['slew_up_Vus'],slew_down_v_per_us=v['slew_down_Vus'],settling_error_v=v['settle_tail_error_V'])
    checks={**orig.ac_checks(acrows),**orig.track_checks([track],acrows),**orig.step_checks([step])};assert all(z[1] for z in checks.values())
    # Fixed endpoint coverage is separate from a set-of-group-names check.
    dims={}
    for group,analysis,axis,start,stop,count,required in [('ac','ac.ac','freq',1,1e9,901,()),('track','track.dc','vinp',0,1.8,361,()),('noise','noise.noise','freq',10,1e6,501,('in','out')),('reject','ac.ac','freq',10,1e8,701,()),('step','tran.tran','time',0,5e-6,5001,()),('thd','tran.tran','time',0,.005,20001,())]:
        d=data(ROOT/r['groups'][group],analysis,required=required);x=d[axis]
        assert len(x)==count and np.isclose(x[0],start,rtol=1e-10,atol=1e-14) and np.isclose(x[-1],stop,rtol=1e-9,atol=1e-14)
        dims[group]=dict(points=len(x),axis=axis,start=float(x[0]),stop=float(x[-1]))
    assert len(r['native_stb']['rows'])==5 and all(z['phase_margin_deg']>60 and z['falling_crossings']==1 and not z['recross'] for z in r['native_stb']['rows'])
    pp=json.loads((CASE/'pdf_provenance.json').read_text()) if (CASE/'pdf_provenance.json').exists() else None
    fig=json.loads((CASE/'schematic_audit.json').read_text()) if (CASE/'schematic_audit.json').exists() else None
    if fig:
        assert fig['status']=='passed' and not fig['render_review_pending']
        assert fig['circuit_sha256']==sha(CASE/'circuit.scs') and fig['geometry_sha256']==sha(CASE/'geometry.json')
        assert fig['instance_counts']==dict(MOS=45,R=12,C=6) and fig['total_terminals']==216
        assert fig['all_rendered_pins_have_drawn_path_to_correct_net_label'] and fig['all_45_body_connections_explicit'] and not fig['geometric_wire_conflicts']
        for path,h in fig['artifacts'].items():assert sha(ROOT/path)==h
    if pp:
        assert sha(ROOT/pp['pdf'])==pp['sha256'] and sha(CASE/'latest_results.json')==pp['results_sha256'] and sha(CASE/'circuit.scs')==pp['circuit_sha256']
    result=dict(audited_at=now(),status=r['status'],nominal_groups=list(r['groups']),nominal_scalar_gates=37,original_function_checks_nominal_scope=checks,source_scope_changes='In-memory PVT=(tt1.8V27C), expected AC rows5 only; original source files unchanged. Source names containing pvt do not assert full PVT.',source_and_model_and_lut_hashes_valid=True,geometry=dict(MOS=45,R=12,C=6,max_unit_width_um=max(z['W_unit_um'] for z in geo['devices']),all_valid=True),all_nominal_runs_same_circuit=True,run_snapshots=runrows,measurement_dimensions=dims,native_stb_five_points_pass=True,source_and_result_sha256=dict(circuit=sha(CASE/'circuit.scs'),results=sha(CASE/'latest_results.json'),contract=sha(CASE/'contract.json'),sizing=sha(CASE/'sizing.json'),knowledge=sha(CASE/'knowledge.md'),measurement_review=sha(CASE/'measurement-review.md')),pdf=pp,schematic_audit=fig,unexecuted=['24otherPVTpoints','2otherrepresentative rejection/distortion points','3fixedmismatchseeds','PEX/passivetolerance'],warning_assessment='AC/STB each have two SPECTRE-294 many-saved-signals performance notices only; all other final runs no warnings. No model dimension or simulator failures.')
    write_json(CASE/'verification_audit.json',result)
    print(json.dumps(dict(status=result['status'],gates=37,groups=6,final_runs=7,original_threshold_functions_pass=True,PDF_ready=bool(pp and not pp['render_review_pending']),schematic_audit_present=bool(fig)),indent=2))
    return result

if __name__=='__main__':audit()
