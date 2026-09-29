"""Six-bit final SAR run. All independent frozen source chunks run concurrently."""
from sar_final import *
from concurrent.futures import ThreadPoolExecutor,as_completed
BITS=6
SLOT,CASE,TASK=context(BITS)

def final_design():
    design(6,unit_fF=30,dummy_fF=10,sample_scale=1,cmp_scale=.25,delay_fF=10,bootstrap=True)

def run_parallel(step=50e-12,reltol=1e-5,workers=4):
    benches={k+str(c):bench(6,k,step,reltol,c) for k,c in groups(6)}
    deps=[CASE/x for x in ['circuit.scs','sizing.json','contract.json','hd_cells.scs','hd_cells_manifest.json']]
    before={str(p):sha(p) for p in deps};runs={}
    for k,b in benches.items():(CASE/f'testbench_{k}.scs').write_text(b)
    def one(k,b):return run_spectre(42,k,b,deps,timeout=1800)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(one,k,b):k for k,b in benches.items()}
        for f in as_completed(futures):
            k=futures[f];runs[k]=str(f.result().relative_to(ROOT));write_json(CASE/'latest_runs_partial.json',runs);print(k,runs[k],flush=True)
    assert {str(p):sha(p) for p in deps}==before
    runs={k:runs[k] for k in benches};write_json(CASE/'latest_runs.json',runs)
    return extract(6)

if __name__=='__main__':final_design();run_parallel()
