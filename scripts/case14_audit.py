"""Reproducible provenance and contract audit; finalizes only after visual review."""
from common import *
import argparse
import subprocess

CASE=ROOT/'cases/14-oscillator'


def audit(visual_review=False):
    result=json.loads((CASE/'latest_results.json').read_text())
    sizing=json.loads((CASE/'sizing.json').read_text())
    contract=json.loads((CASE/'contract.json').read_text())
    manifest=json.loads((CASE/'hd_cells_manifest.json').read_text())
    provenance=json.loads((CASE/'pdf_provenance.json').read_text())
    assert result['nominal_complete'] and result['status']=='complete_original'
    assert result['functional_checks_pass'] and result['all_nominal_checks_complete']
    assert len(result['gates'])==3 and all(g['passes']['original'] for g in result['gates'].values())
    v=result['values'];o=result['observations']
    assert 1.8e6<=v['frequency_Hz']<=2.2e6 and .95<=v['swing_ratio']<=1.05 and v['power_W']<=20e-6
    assert len(o['frequency_edges_s'])==11 and all(10e-6<=x<=20e-6 for x in o['frequency_edges_s'])
    assert o['frequency_ten_period_end_inside_window'] and o['current_avg_A']>0
    assert o['all_periods_relative_frequency_difference']<1e-6
    assert contract['temperature_C']==27 and contract['VDD_V']==1.8
    assert contract['supply_ramp_s']==1e-6 and contract['external_bias_A']==2e-6 and contract['load_F']==1e-12
    assert contract['measurement_window_s']==[10e-6,20e-6] and contract['stop_s']==20e-6
    assert contract['frequency_center_Hz']==2e6 and contract['frequency_error_max_Hz']==200e3
    assert contract['swing_center_VDD']==1 and contract['swing_error_max_VDD']==.05

    for f in json.loads((CASE/'source_provenance.json').read_text())['files']:
        assert sha(f['original'])==f['sha256']==sha(ROOT/f['frozen'])
    for role in sizing['roles'].values():
        assert sha(role['lut_path'])==role['lut_sha256']
        assert role['lut_metadata']['temperature_C']==27 and role['gmid']==15
        assert role['rounded_W_um']<=100 and role['L_um']==1
    assert all(x['minimum_saturation_headroom_V']>0 for x in result['bias_operating_conditions'].values())

    # Compare each vendor MOS connection, model and original parameter string.
    vendor=Path(manifest['source']).read_text();hd=(CASE/'hd_cells.scs').read_text()
    assert sha(manifest['source'])==manifest['source_sha256'] and sha(CASE/'hd_cells.scs')==manifest['output_sha256']
    assert not manifest['sizes_modified'] and not manifest['model_names_modified']
    for cell in manifest['cells']:
        name=cell['name'];block=re.search(r'^\.SUBCKT\s+'+name+r'\s[^\n]*\n.*?^\.ENDS[^\n]*',vendor,re.M|re.S|re.I)[0]
        assert hashlib.sha256(block.encode()).hexdigest()==cell['original_block_sha256']
        converted=re.search(r'^subckt '+name+r' \([^\n]*\n.*?^ends '+name+r'\b',hd,re.M|re.S)[0]
        source_mos=[line.split() for line in block.splitlines() if line.upper().startswith('M')]
        actual_mos=[line.replace('(','').replace(')','').split() for line in converted.splitlines() if line.upper().startswith('M')]
        assert len(source_mos)==len(actual_mos)==cell['mos_count']
        for a,b in zip(source_mos,actual_mos):
            assert a[:6]==b[:6]
            assert {x.split('=')[0].lower():x.split('=')[1] for x in a[6:]}=={x.split('=')[0].lower():x.split('=')[1] for x in b[6:]}

    circuit=(CASE/'circuit.scs').read_text();assert 'subckt osc_2m (AVDD AVSS CLKO IBN2U)' in circuit
    assert not re.search(r'(?i)\b(include|vsource|isource|bsource|resistor|capacitor|switch|model)\b',circuit)
    mos=re.findall(r'^M\S+\s+\([^\n]+\)\s+(n18|p18)\s+w=([0-9.]+)u\s+l=([0-9.]+)u(?:\s+m=([0-9.]+))?$',circuit,re.M)
    assert len(mos)==9 and all(float(x[1])<=100 and float(x[2])==1 for x in mos)
    assert len(re.findall(r'^X\S+\s+',circuit,re.M))==5
    assert len(re.findall(r'^CT\d+ .* mim w=10u l=7.75u$',circuit,re.M))==3
    for i in range(1,4):
        prev=3 if i==1 else i-1
        assert f'XINV{i} (N{prev} N{i} P{i} Q{i} AVDD AVSS) INHDVL' in circuit
    assert 'CT1 (N1 AVDD)' in circuit and 'CT2 (N2 AVSS)' in circuit and 'CT3 (N3 AVSS)' in circuit

    runs=[]
    for run in sorted((ROOT/'runs/14').glob('*_ramp')):
        m=json.loads((run/'run.json').read_text());assert m['status']=='completed' and m['model_dimensions_valid'] and m['temperature_C']==27
        assert sha(ROOT/m['netlist'])==m['netlist_sha256']
        for dep in m['dependencies'].values():assert sha(ROOT/dep['snapshot'])==dep['sha256']
        for filename,digest in m['models'].items():assert sha(filename)==digest
        bench=(ROOT/m['netlist']).read_text();incs=re.findall(r'^include "([^"]+)"',bench,re.M)
        assert len(incs)==4 and all(Path(q).is_file() for q in incs)
        assert all(q==str(MODEL) or str(run/'inputs') in q for q in incs)
        assert 'section=tt' in bench and 'section=mim_tt' in bench
        assert 'wave=[0 0 1u 1.8 20u 1.8]' in bench and 'IBIAS (AVDD IBN2U) isource dc=2u' in bench
        assert 'CLOAD (CLKO 0) capacitor c=1p' in bench and 'VSENSE (AVDD_SRC AVDD) vsource dc=0' in bench
        assert 'tran tran stop=20u maxstep=300p' in bench and not re.search(r'\b(ic|skipdc|nodeset)=',bench)
        raw=run/'output/bench.raw/tran.tran.tran';assert raw.stat().st_size>0
        runs.append(dict(path=str(run.relative_to(ROOT)),raw=str(raw.relative_to(ROOT)),raw_bytes=raw.stat().st_size,
          hashes_match=True,model_dimensions_valid=True,include_closure_complete=True,warnings=m['warnings'],status=json.loads((run/'measurements.json').read_text())['status']))
    assert len(runs)==3
    final=ROOT/result['run_dir']
    for filename in ['circuit.scs','hd_cells.scs','sizing.json','contract.json','hd_cells_manifest.json','source_provenance.json']:
        assert sha(CASE/filename)==sha(final/'inputs'/filename)
    d=data(final,'tran.tran');t=d['time'];ix=(t>=10e-6)&(t<=20e-6)
    assert t[0]==0 and abs(t[-1]-20e-6)<1e-15
    virtual_diff=float(np.min(d['XDUT.P1'][ix]-d['XDUT.Q1'][ix]));assert virtual_diff>0

    pdf=ROOT/provenance['pdf'];assert sha(pdf)==provenance['sha256']
    assert sha(CASE/'latest_results.json')==provenance['results_sha256'] and sha(CASE/'circuit.scs')==provenance['circuit_sha256']
    info=subprocess.run(['pdfinfo',str(pdf)],check=True,text=True,capture_output=True).stdout
    assert re.search(r'^Pages:\s+6$',info,re.M)
    text=subprocess.run(['pdftotext',str(pdf),'-'],check=True,text=True,capture_output=True).stdout
    assert text.index('本模块利用')<text.index('结论')
    pages=[]
    for i in range(1,7):
        p=ROOT/f'reports/14-review-page-{i}.png';assert p.is_file() and p.stat().st_size>0
        pages.append(dict(page=i,path=str(p.relative_to(ROOT)),sha256=sha(p)))
    assert visual_review,'Finalization requires actual manual inspection of all six rendered pages.'
    report=dict(generated_at=now(),case_slot=14,status='passed',result_sha256=sha(CASE/'latest_results.json'),circuit_sha256=sha(CASE/'circuit.scs'),
      pdf_sha256=sha(pdf),pdf_pages=6,pdf_intro_before_verdict=True,all_final_pages_visually_reviewed=True,rendered_pages=pages,
      full_nominal_coverage=dict(PVT_points_in_scope=1,PVT_points_disclosed=5,supply_ramp_us=1,external_bias_uA=2,load_pF=1,startup_by_us=10,
        measurement_interval_us=[10,20],frequency_periods=10,selected_edge_count=11,frequency_window_complete=True,frequency_bounds=2,swing_bounds=2,power_bound=1),
      source_hashes_match=True,LUT_hashes_match=True,HD_sizes_models_and_connections_original=True,HD_virtual_supply_and_global_wells_confirmed=True,
      stage1_minimum_virtual_rail_difference_V=virtual_diff,DUT_native_passives_only=True,bias_positive_saturation_headroom=True,runs=runs,
      scope_exclusions=contract['nominal_scope_excludes'],knowledge_path=str((CASE/'knowledge.md').relative_to(ROOT)),knowledge_sha256=sha(CASE/'knowledge.md'))
    write_json(CASE/'verification_audit.json',report)
    provenance.update(render_review_pending=False,visually_reviewed_at=now(),all_pages_reviewed=True,rendered_pages=pages)
    write_json(CASE/'pdf_provenance.json',provenance)
    update_case(14,status='complete_original',nominal_complete=True,review_pdf=str(pdf.relative_to(ROOT)),review_pdf_ready=True,pdf_render_review_pending=False,
      knowledge_draft=str((CASE/'knowledge.md').relative_to(ROOT)),verification_audit=str((CASE/'verification_audit.json').relative_to(ROOT)))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--visual-review-complete',action='store_true');a=p.parse_args()
    print(json.dumps(audit(a.visual_review_complete),indent=2,ensure_ascii=False))
