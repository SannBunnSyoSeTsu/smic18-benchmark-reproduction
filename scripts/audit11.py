"""Read frozen PSF/source, cross-check with upstream measurement functions."""
from common import *
import importlib.util
import math
import audit_schematic_independent as drawing

CASE=ROOT/'cases/11-bandgap'

def main():
    report=json.loads((CASE/'latest_results.json').read_text());values=report['values'];groups=report['groups']
    spec=importlib.util.spec_from_file_location('case11_original_verifier',CASE/'source/tests/verify.py')
    upstream=importlib.util.module_from_spec(spec);sys.modules[spec.name]=upstream;spec.loader.exec_module(upstream)
    checks=[]
    def compare(name,a,b,tol=1e-12):
        diff=abs(float(a)-float(b));assert math.isfinite(diff) and diff<=tol,(name,a,b,diff,tol)
        checks.append(dict(name=name,report=float(a),independent=float(b),absolute_difference=diff,tolerance=tol,passed=True))
    def upstream_result(group,label,ramp=None):
        run=ROOT/groups[label]
        if group in ('startup','line_step'):
            d=data(run,'tran.tran');plot_name='Transient Analysis';names=['time','v(vref)','v(vdd)','i(vdd)'];vectors=[d[k] for k in ['time','vref','vdd','VDD:p']]
        elif group=='ac':
            d=data(run,'ac.ac');plot_name='AC Analysis';names=['frequency','v(vref)'];vectors=[d['freq'],d['vref']]
        else:
            d=data(run,'noise.noise',required=['out']);plot_name='Noise Spectral Density Curves';names=['frequency','onoise_spectrum'];vectors=[d['freq'],d['out']]
        plot=upstream.Plot(plot_name,names,[[complex(x) for x in row] for row in zip(*vectors)])
        upstream.parse_raw=lambda path:[plot]
        case=dict(group=group,corner='tt',temp_c=27,vdd=1.8)
        if ramp is not None:case['ramp_s']=ramp
        targets={('tt',27,z['supply_V']):z['vref_V'] for z in values['line_rows']}
        return upstream.analyze(case,Path('in-memory-format-adapter'),upstream.SPEC,targets)
    for label,ramp,ours in zip(['startup1','startup10'],[1e-6,10e-6],values['startup']):
        src=upstream_result('startup',label,ramp)
        for key,other in [('window_min_V','startup_window_v_min'),('window_max_V','startup_window_v_max'),('final_V','startup_final_v'),('overshoot_V','startup_overshoot_v'),('peak_current_A','startup_peak_supply_current_a'),('energy_J','startup_energy_j')]:compare(label+':'+key,ours[key],src[other])
    compare('AC maximum',values['supply_gain_max'],upstream_result('ac','acnoise')['supply_gain_max'])
    compare('Output noise integral',values['output_noise_Vrms'],upstream_result('noise','acnoise')['integrated_noise_v'])
    src=upstream_result('line_step','step')
    for ours,z in zip(values['line_step'],src['line_step_details']):
        compare('step '+ours['direction']+' peak',ours['excursion_V'],z['excursion_v'])
        compare('step '+ours['direction']+' last outside',ours['verifier_last_outside_s'],z['settling_time_s'],2.1e-9)
        assert ours['conservative_settling_s']+1e-15>=z['settling_time_s']
    vs=[z['vref_V'] for z in values['temperature_rows']]
    compare('temperature coefficient',values['tempco_ppm_C'],(max(vs)-min(vs))/(sum(vs)/len(vs)*165)*1e6)
    vs=[z['vref_V'] for z in values['line_rows']]
    compare('line regulation',values['line_regulation_V_V'],(max(vs)-min(vs))/.36)
    provenance=[]
    current_models=model_provenance();old_models=json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    assert all(current_models[p]==h for p,h in old_models.items()),'Model changed since previous reproduction'
    for label,path in groups.items():
        run=ROOT/path;meta=json.loads((run/'run.json').read_text())
        assert meta['status']=='completed' and meta['model_dimensions_valid']
        logs=list((run/'output').glob('*.log'));assert logs
        log='\n'.join(p.read_text(errors='replace') for p in logs)
        assert re.search(r'spectre completes with 0 errors, 0 warnings',log)
        assert not re.search(r'(?im)^\s*(?:ERROR|FATAL)\s*\(',log)
        false_positive=None
        if meta['errors']:
            assert meta['errors']==['license error'] and 'Periodic Lic check successful' in log
            false_positive='Bridge runner.py combines any occurrence of license with any occurrence of error, including the final 0 errors message. Raw Spectre reports successful licensing and zero errors/warnings; completed data and inputs independently verified. Original metadata preserved.'
        assert sha(ROOT/meta['netlist'])==meta['netlist_sha256']
        assert meta['models']==current_models
        for src,dep in meta['dependencies'].items():
            assert sha(ROOT/dep['snapshot'])==dep['sha256']
            if src.endswith('circuit.scs'):assert dep['sha256']==sha(CASE/'circuit.scs')
            if src.endswith('contract.json'):assert dep['sha256']==sha(CASE/'contract.json')
        provenance.append(dict(label=label,run=path,warnings=meta['warnings'],inputs_intact=True,models_intact=True,bridge_diagnostic=meta['errors'],diagnostic_review=false_positive,log_files={str(p.relative_to(ROOT)):sha(p) for p in logs}))
    for z in json.loads((CASE/'sizing.json').read_text())['roles'].values():assert sha(z['lut_path'])==z['lut_sha256']
    drawing.PRIMITIVE_PORTS['npn18a4']=('C','B','E','SUB');drawing.PRIMITIVE_KINDS['npn18a4']='BJT'
    schematic=drawing.audit_slot(11);assert schematic['status']=='passed',schematic['errors']
    write_json(CASE/'schematic_independent_review.json',schematic)
    audit=dict(generated_at=now(),status='passed',circuit_sha256=sha(CASE/'circuit.scs'),results_sha256=sha(CASE/'latest_results.json'),contract_sha256=sha(CASE/'contract.json'),upstream_verifier_sha256=sha(CASE/'source/tests/verify.py'),measurement_cross_checks=checks,schematic_independent_review=str((CASE/'schematic_independent_review.json').relative_to(ROOT)),run_provenance=provenance,all_final_runs_same_circuit=True,original_model_hashes_unchanged=True,lut_hashes_unchanged=True,all_original_gates_pass=all(g['passes']['original'] for g in report['gates'].values()),full_upstream_signoff=False,pdf_review_pending=True,method='Current agent independent calculation pass. Actual Spectre waveforms adapted in memory to the original verifier Plot interface; upstream analyze executes unchanged. Original full-PVT score function was not invoked.')
    write_json(CASE/'verification_audit.json',audit)
    text='# 第11项独立测量复核\n\n'+audit['method']+'\n\n|检查|报告|独立结果|绝对差|\n|---|---:|---:|---:|\n'
    for z in checks:text+=f"|{z['name']}|{z['report']:.12g}|{z['independent']:.12g}|{z['absolute_difference']:.3g}|\n"
    text+=f"\n原始波形、输入网表、合同、PDK与LUT哈希检查通过。图纸独立核对{schematic['source_definition_count']}个实例、{schematic['source_terminal_count']}个端子，错误0。未执行全PVT/MC评分。\n"
    (CASE/'measurement-review.md').write_text(text)
    print(json.dumps(dict(status='passed',measurement_checks=len(checks),schematic_instances=schematic['source_definition_count'],schematic_terminals=schematic['source_terminal_count']),ensure_ascii=False))

if __name__=='__main__':main()
