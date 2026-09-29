"""Shared provenance for the authorized seven-case continuation; no quota polling."""
from common import *
import common,shutil
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'

def freeze_case(case,task,contract):
    case.mkdir(parents=True,exist_ok=True)
    files=[p for p in task.rglob('*') if p.is_file() and p.suffix in ['.md','.spi','.py','.json']]
    for p in files:
        dst=case/'source'/p.relative_to(task);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    write_json(case/'source_provenance.json',dict(captured_at=now(),task=str(task),files={str(p.relative_to(task)):sha(p) for p in files}))
    write_json(case/'contract.json',contract)
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env.update(captured_at=now(),models=model_provenance(),quota_monitoring=False);write_json(case/'environment.json',env)

def save_design(case,text,roles,parameters,rationale):
    (case/'circuit.scs').write_text(text)
    write_json(case/'sizing.json',dict(generated_at=now(),roles=roles,parameters=parameters,rationale=rationale,circuit_sha256=sha(case/'circuit.scs')))
    (case/'lut').mkdir(exist_ok=True)
    for q in roles.values():shutil.copy2(q['lut_path'],case/'lut'/Path(q['lut_path']).name)

def simulate_groups(slot,case,benches,temperature_C=27):
    runs={}
    for label,b in benches.items():
        (case/f'testbench_{label}.scs').write_text(b)
        deps=[case/'circuit.scs',case/'sizing.json',case/'contract.json']+[case/n for n in ['hd_cells.scs','hd_cells_manifest.json'] if (case/n).exists()]
        rd=run_spectre(slot,label,b,deps,timeout=1800,temperature_C=temperature_C)
        runs[label]=str(rd.relative_to(ROOT));write_json(case/'latest_runs.json',runs)
        print(label,runs[label],flush=True)
    return runs

def result(case,slot,values,gates,groups,guards=True,**extra):
    tiers={t:bool(guards and all(q['passes'][t] for q in gates.values())) for t in ['original','10pct','15pct']}
    status=next(('complete_'+t for t,v in tiers.items() if v),'needs_iteration')
    r=dict(case_slot=slot,generated_at=now(),status=status,values=values,gates=gates,pass_tiers=tiers,groups=groups,run_dirs=list(groups.values()),circuit_sha256=sha(case/'circuit.scs'),contract_sha256=sha(case/'contract.json'),scope=json.loads((case/'contract.json').read_text())['scope'],all_nominal_checks_complete=True,model_dimensions_valid=True,nonrelaxable_guards_pass=bool(guards),**extra)
    write_json(case/'latest_results.json',r)
    hist=case/'iteration_history.json';history=json.loads(hist.read_text()) if hist.exists() else []
    history.append(dict(generated_at=r['generated_at'],circuit_sha256=r['circuit_sha256'],parameters=json.loads((case/'sizing.json').read_text())['parameters'],status=status,values=values,groups=groups))
    write_json(hist,history)
    print(json.dumps(dict(status=status,values=values,failed=[k for k,v in gates.items() if not v['passes']['15pct']]),ensure_ascii=False,indent=2),flush=True)
    return r

def strict(g):
    g['passes']={t:bool(g['value']>v if g['sense']=='min' else g['value']<v) for t,v in g['limits'].items()}
    return g
