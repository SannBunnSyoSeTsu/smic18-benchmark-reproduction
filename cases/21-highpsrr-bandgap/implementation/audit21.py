"""Independent case21 source-metric and schematic audit; no simulation."""
from common import *
import importlib.util
import math
from scipy.integrate import trapezoid
import audit_schematic_independent as drawing

CASE=ROOT/'cases/21-highpsrr-bandgap'

def main():
    report=json.loads((CASE/'latest_results.json').read_text());v=report['values'];groups=report['groups']
    sys.path.insert(0,str(CASE/'source/tests'))
    spec=importlib.util.spec_from_file_location('case21_upstream',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    td=data(ROOT/groups['static'],'temperature.dc');ac=data(ROOT/groups['ac'],'ac.ac');tr=data(ROOT/groups['startup'],'tran.tran')
    assert np.array_equal(td['temp'],np.arange(-40,86))
    times=tr['time'];mask=(times>=90e-6-1e-14)&(times<=100e-6+1e-14)
    tt=times[mask];yy=tr['VBG'][mask]
    assert abs(tt[0]-90e-6)<1e-13 and abs(tt[-1]-100e-6)<1e-13
    assert abs(tr['VBG'][0])<1e-12 and abs(tr['AVDD'][0])<1e-12
    row=dict(point=up.NOMINAL,name=up.point_name(up.NOMINAL),vbg_dc=float(td['VBG'][np.where(td['temp']==27)[0][0]]),vbg_temp_max=float(max(td['VBG'])),vbg_temp_min=float(min(td['VBG'])),vbg_temp_avg=float(trapezoid(td['VBG'],td['temp'])/(td['temp'][-1]-td['temp'][0])),vbg_tran_final=float(trapezoid(yy,tt)/(tt[-1]-tt[0])))
    for freq,key in [(.01,'supply_gain_0p01hz_db'),(1e6,'supply_gain_1mhz_db')]:
        ix=np.argmin(abs(ac['freq']-freq));assert np.isclose(ac['freq'][ix],freq,rtol=1e-10)
        row[key]=20*math.log10(abs(complex(ac['VBG'][ix])))
    official=up.checks([row],{up.NOMINAL});assert all(x[1] for x in official),official
    comparisons=[]
    for ours,key,tol in [('vref_V','vbg_dc',1e-12),('temp_min_V','vbg_temp_min',1e-12),('temp_max_V','vbg_temp_max',1e-12),('temp_average_V','vbg_temp_avg',1e-12),('tempco_ppm_C','drift_ppm',1e-9),('supply_gain_low_dB','supply_gain_0p01hz_db',1e-9),('supply_gain_1MHz_dB','supply_gain_1mhz_db',1e-9),('startup_average_V','vbg_tran_final',1e-10),('startup_error_fraction','startup_error',1e-10)]:
        delta=abs(v[ours]-row[key]);assert math.isfinite(delta) and delta<=tol,(ours,delta)
        comparisons.append(dict(metric=ours,report=v[ours],independent=row[key],absolute_difference=delta,tolerance=tol,passed=True))
    source=json.loads((CASE/'source_provenance.json').read_text())
    for rel,h in source['files'].items():assert sha(CASE/'source'/rel)==h==sha(Path(source['task'])/rel)
    models=model_provenance();original=json.loads((ROOT/'environment.json').read_text())['model_file_hashes'];assert models==original
    runs=[]
    for name,path in groups.items():
        run=ROOT/path;m=json.loads((run/'run.json').read_text());assert m['status']=='completed' and m['model_dimensions_valid']
        assert m['models']==models and sha(ROOT/m['netlist'])==m['netlist_sha256']
        for src,d in m['dependencies'].items():
            assert sha(ROOT/d['snapshot'])==d['sha256']
            if src.endswith('circuit.scs'):assert d['sha256']==sha(CASE/'circuit.scs')
            if src.endswith('contract.json'):assert d['sha256']==sha(CASE/'contract.json')
        logs=list((run/'output').glob('*.log'));log='\n'.join(p.read_text(errors='replace') for p in logs)
        assert 'spectre completes with 0 errors, 0 warnings' in log
        assert not re.search(r'(?im)^\s*(?:ERROR|FATAL)\s*\(',log)
        if m['errors']:assert m['errors']==['license error'] and 'Periodic Lic check successful' in log
        runs.append(dict(group=name,run=path,inputs_and_models_intact=True,errors=m['errors'],warnings=m['warnings'],diagnostic_review='Known Bridge substring false positive: successful licensing and 0 errors/0 warnings in original Spectre logs; original metadata preserved.',logs={str(p.relative_to(ROOT)):sha(p) for p in logs}))
    sizing=json.loads((CASE/'sizing.json').read_text())
    for z in sizing['roles'].values():assert sha(z['lut_path'])==z['lut_sha256']==sha(CASE/'lut'/Path(z['lut_path']).name)
    drawing.PRIMITIVE_PORTS['npn18a4']=('C','B','E','SUB');drawing.PRIMITIVE_KINDS['npn18a4']='BJT'
    sc=drawing.audit_slot(21);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    audit=dict(generated_at=now(),status='passed',circuit_sha256=sha(CASE/'circuit.scs'),results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),upstream_verifier_sha256=sha(CASE/'source/tests/verify.py'),measurement_cross_checks=comparisons,upstream_nominal_checks=[dict(name=x[0],passed=x[1],detail=x[2]) for x in official],all_original_gates_pass=True,all_final_runs_same_circuit=True,source_snapshot_hashes_verified=True,source_snapshot_count=len(source['files']),original_model_hashes_unchanged=True,lut_hashes_unchanged=True,run_provenance=runs,schematic_independent_review='cases/21-highpsrr-bandgap/schematic_independent_review.json',full_upstream_signoff=False,pdf_review_pending=True,method='Current agent independently re-integrated actual Spectre trajectories and passed the resulting metrics to the unchanged upstream checks(rows,{NOMINAL}); no other3PVT points simulated or claimed.')
    write_json(CASE/'verification_audit.json',audit)
    note='# 第21项独立测量复核\n\n'+audit['method']+'\n\n|指标|报告|独立结果|绝对差|\n|---|---:|---:|---:|\n'
    for x in comparisons:note+=f"|{x['metric']}|{x['report']:.12g}|{x['independent']:.12g}|{x['absolute_difference']:.3g}|\n"
    note+='\n原上游五项nominal检查均通过；温度平均值采用梯形积分除以125°C。启动按90–100µs时间平均与独立27°C DC值比较；不使用瞬态自己的尾值作目标。\n'
    note+=f"\n图纸独立复核{sc['source_definition_count']}实例、{sc['source_terminal_count']}端子，错误0；源文件、PDK、LUT及三组最终输入哈希一致。\n"
    (CASE/'measurement-review.md').write_text(note)
    print(json.dumps(dict(status='passed',independent_metrics=len(comparisons),upstream_nominal_checks=len(official),instances=sc['source_definition_count'],terminals=sc['source_terminal_count'])))

if __name__=='__main__':main()
