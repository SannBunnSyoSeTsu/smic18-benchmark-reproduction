"""Independent original CML waveform semantics and provenance checks."""
from common import *
import importlib.util
import audit_schematic_independent as drawing

CASE=ROOT/'cases/09-cml-divider'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];source=json.loads((CASE/'source_provenance.json').read_text())
    sys.path.insert(0,str(CASE/'source/tests'))
    spec=importlib.util.spec_from_file_location('case09_upstream',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up)
    comparisons=[];uprows=[];stimuli=[]
    for label,q in v['frequencies'].items():
        d=data(ROOT/r['groups'][label],'tran.tran');rows=[list(map(float,row)) for row in zip(d['time'],d['outp'],d['outn'])]
        u=up.divider_metrics(rows,q['frequency_Hz']);assert u['pass'],(label,u)
        for ours,theirs in [('output_swing_Vpp','output_swing_vpp'),('minimum_cycle_swing_Vpp','minimum_cycle_swing_vpp'),('target_tone_Vpp','target_tone_vpp'),('alternating_cycles','alternating_cycles')]:
            diff=abs(q[ours]-u[theirs]);assert diff<1e-9,(label,ours,diff)
            comparisons.append(dict(metric=label+':'+ours,report=q[ours],independent=u[theirs],absolute_difference=diff,passed=True))
        uprows.append(dict(corner='tt',label=label,frequency_hz=q['frequency_Hz'],metrics=u,error=None))
        assert np.max(abs((d['srcp']+d['srcn'])/2-.9))<1e-12
        assert abs(np.ptp(d['srcp']-d['srcn'])-.3)<1e-12
        # Check the physical source trajectory against the published PULSE timing.
        tt=d['time'];per=1/q['frequency_Hz'];phase=np.mod(tt-100e-12,per);expected=np.full(len(tt),.825)
        rising=(tt>=100e-12)&(phase<10e-12);high=(tt>=100e-12)&(phase>=10e-12)&(phase<per/2);fall=(tt>=100e-12)&(phase>=per/2)&(phase<per/2+10e-12)
        expected[rising]=.825+.15*phase[rising]/10e-12;expected[high]=.975;expected[fall]=.975-.15*(phase[fall]-per/2)/10e-12
        err=float(np.max(abs(d['srcp']-expected)));assert err<1e-7,(label,err)
        stimuli.append(dict(label=label,source_waveform_max_error_V=err,source_differential_Vpp=q['source_differential_Vpp'],common_mode_V=.9,cycle_count=40,measured_output_frequency_Hz=q['measured_output_frequency_Hz'],positive_zero_crossings=q['positive_zero_crossings']))
    speed,measurements=up.speed_check(uprows,('tt',));assert speed[1],speed
    op=dc(ROOT/r['groups']['power']);power=-op['vdd']*op['VDD:p'];assert abs(power-v['dc_power_W'])<1e-15 and power<up.POWER_MAX_W
    comparisons.append(dict(metric='quiescent VDD power',report=v['dc_power_W'],independent=power,absolute_difference=abs(power-v['dc_power_W']),passed=True))
    assert abs(op['clkp']-.9)<1e-12 and abs(op['clkn']-.9)<1e-12
    for rel,h in source['files'].items():assert sha(CASE/'source'/rel)==h==sha(Path(source['task'])/rel)
    models=model_provenance();assert models==json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    provenance=[]
    for label,path in r['groups'].items():
        run=ROOT/path;m=json.loads((run/'run.json').read_text());assert m['status']=='completed' and m['model_dimensions_valid'] and m['models']==models
        assert sha(ROOT/m['netlist'])==m['netlist_sha256']
        for src,d in m['dependencies'].items():
            assert sha(ROOT/d['snapshot'])==d['sha256']
            if src.endswith('circuit.scs'):assert d['sha256']==r['circuit_sha256']==sha(CASE/'circuit.scs')
            if src.endswith('contract.json'):assert d['sha256']==sha(CASE/'contract.json')
        logs=list((run/'output').glob('*.log'));log='\n'.join(x.read_text(errors='replace') for x in logs)
        assert 'spectre completes with 0 errors, 0 warnings' in log and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',log)
        if m['errors']:assert m['errors']==['license error'] and 'Periodic Lic check successful' in log
        provenance.append(dict(group=label,run=path,input_hashes_intact=True,models_intact=True,warnings=m['warnings'],bridge_errors=m['errors'],diagnostic_review='Final log has successful license check and0errors/0warnings; Bridge substring false positive retained. Earlier failed PWL deck has realCMI-2204 and is excluded.',logs={str(x.relative_to(ROOT)):sha(x) for x in logs}))
    for z in json.loads((CASE/'sizing.json').read_text())['roles'].values():assert sha(z['lut_path'])==z['lut_sha256']==sha(CASE/'lut'/Path(z['lut_path']).name)
    sc=drawing.audit_slot(9);assert sc['status']=='passed',sc['errors'];write_json(CASE/'schematic_independent_review.json',sc)
    audit=dict(generated_at=now(),status='passed',circuit_sha256=sha(CASE/'circuit.scs'),results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),upstream_verifier_sha256=sha(CASE/'source/tests/verify.py'),measurement_cross_checks=comparisons,upstream_nominal_speed_check=dict(name=speed[0],passed=speed[1],detail=speed[2]),upstream_nominal_power_check=dict(passed=True,value_W=power,strict_max_W=up.POWER_MAX_W),stimulus_checks=stimuli,run_provenance=provenance,source_snapshot_hashes_verified=True,original_model_hashes_unchanged=True,lut_hashes_unchanged=True,all_original_gates_pass=True,all_final_runs_same_circuit=True,schematic_independent_review='cases/09-cml-divider/schematic_independent_review.json',full_upstream_signoff=False,pdf_review_pending=True,method='Current agent independently passed actual Spectre time/outp/outn rows to unchanged upstream divider_metrics and speed_check forTT. Power independently computed from originalVDD port. No other process corners claimed.')
    write_json(CASE/'verification_audit.json',audit)
    note='# 第09项独立测量复核\n\n'+audit['method']+'\n\n|指标|报告|独立结果|绝对差|\n|---|---:|---:|---:|\n'
    for z in comparisons:note+=f"|{z['metric']}|{z['report']:.12g}|{z['independent']:.12g}|{z['absolute_difference']:.3g}|\n"
    note+='\n四频点的40周期符号、逐周期摆幅和时间加权fIN/2投影均沿原定义。输入PWL轨迹对照原PULSE解析式检查一致；输出频率另从正向过零间隔测得，未将命令频率直接当作实测。\n'
    note+=f"\n图纸{sc['source_definition_count']}实例/{sc['source_terminal_count']}端子核对通过；模型、LUT与最终五组电路快照一致。\n";(CASE/'measurement-review.md').write_text(note)
    print(json.dumps(dict(status='passed',measurement_checks=len(comparisons),original_speed_points=4,instances=sc['source_definition_count'],terminals=sc['source_terminal_count'])))

if __name__=='__main__':main()
