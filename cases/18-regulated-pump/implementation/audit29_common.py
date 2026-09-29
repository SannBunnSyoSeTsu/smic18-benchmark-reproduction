"""Source/model/snapshot/geometry checks shared by this batch's independent audits."""
from common import *
import audit_schematic_independent as drawing

def compare(checks,name,report,independent,rtol=1e-8,atol=1e-15):
    d=abs(report-independent);ok=bool(np.isfinite(independent) and d<=max(atol,abs(independent)*rtol));assert ok,(name,report,independent)
    checks.append(dict(metric=name,report=float(report),independent=float(independent),absolute_difference=float(d),passed=True))

def finish(case,slot,checks,original_checks,method,details=None):
    r=json.loads((case/'latest_results.json').read_text());assert r['status'].startswith('complete_') and r['nonrelaxable_guards_pass']
    model=model_provenance();assert model==json.loads((ROOT/'environment.json').read_text())['model_file_hashes']
    source=json.loads((case/'source_provenance.json').read_text())
    for path,h in source['files'].items():assert sha(case/'source'/path)==h==sha(Path(source['task'])/path)
    for q in json.loads((case/'sizing.json').read_text())['roles'].values():assert sha(q['lut_path'])==q['lut_sha256']==sha(case/'lut'/Path(q['lut_path']).name)
    if (case/'hd_cells_manifest.json').exists():
        hd=json.loads((case/'hd_cells_manifest.json').read_text());assert not hd['sizes_modified'] and not hd['model_names_modified']
        assert sha(hd['source'])==hd['source_sha256'] and sha(case/'hd_cells.scs')==hd['output_sha256']
        vendor=Path(hd['source']).read_text()
        for cell in hd['cells']:
            block=re.search(r'^\.SUBCKT\s+'+re.escape(cell['name'])+r'[^\n]*\n.*?^\.ENDS[^\n]*',vendor,re.M|re.S|re.I)[0]
            assert hashlib.sha256(block.encode()).hexdigest()==cell['original_block_sha256']
    conf=json.loads((case/'numerical_confirmation.json').read_text());assert conf['passed'] and conf['final_groups']==r['groups'] and conf['circuit_sha256']==r['circuit_sha256']
    logs=[]
    for path in sorted(set(r['run_dirs']+list(conf['baseline_groups'].values()))):
        rd=ROOT/path;m=json.loads((rd/'run.json').read_text());assert m['status']=='completed' and m['models']==model and m['model_dimensions_valid']
        assert sha(ROOT/m['netlist'])==m['netlist_sha256'] and sha(rd/'inputs/circuit.scs')==r['circuit_sha256']==sha(case/'circuit.scs')
        assert sha(rd/'inputs/contract.json')==r['contract_sha256']
        for q in m['dependencies'].values():assert sha(ROOT/q['snapshot'])==q['sha256']
        log='\n'.join(p.read_text(errors='replace') for p in (rd/'output').glob('*.log'));assert re.search(r'spectre completes with 0 errors',log) and not re.search(r'(?im)^\s*(ERROR|FATAL)\s*\(',log)
        logs.append(dict(run=path,actual_error_free=True,warnings=m['warnings'],bridge_errors=m['errors']))
    blocks=drawing.parse_source(case/'circuit.scs')
    for block in blocks.values():
        for d in block['instances'].values():
            p=d['parameters'];m=d['model']
            if m in ['n18','p18']:
                assert .19e-6<=drawing.numeric(p['w'])<=100e-6 and .18e-6<=drawing.numeric(p['l'])<=20e-6 and drawing.numeric(p.get('m','1'))>0
            elif m in ['resistor','capacitor']:assert drawing.numeric(p['r' if m=='resistor' else 'c'])>0
    sc=drawing.audit_slot(slot);assert sc['status']=='passed',sc['errors'];write_json(case/'schematic_independent_review.json',sc)
    a=dict(generated_at=now(),status='passed',circuit_sha256=r['circuit_sha256'],results_sha256=sha(case/'latest_results.json'),contract_sha256=r['contract_sha256'],measurement_cross_checks=checks,original_nominal_checks=original_checks,original_model_hashes_unchanged=True,source_snapshot_hashes_verified=True,lut_hashes_unchanged=True,run_provenance=logs,numerical_confirmation=conf,schematic_instances=sc['source_definition_count'],schematic_terminals=sc['source_terminal_count'],pdf_review_pending=True,full_upstream_signoff=False,method=method)
    write_json(case/'verification_audit.json',a)
    if details is not None:write_json(case/'independent_measurement_details.json',details)
    md=f'# 第{slot:02d}项独立复核\n\n{method}\n\n|指标|报告|独立|差异|\n|---|---:|---:|---:|\n'
    for q in checks:md+=f"|{q['metric']}|{q['report']:.12g}|{q['independent']:.12g}|{q['absolute_difference']:.4g}|\n"
    (case/'measurement-review.md').write_text(md)
    print(json.dumps(dict(status='passed',measurements=len(checks),instances=sc['source_definition_count'],terminals=sc['source_terminal_count']),ensure_ascii=False))
    return a
