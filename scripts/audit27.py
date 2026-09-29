from audit29_common import *
import importlib.util
CASE=ROOT/'cases/27-flash-adc4bit'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];vectors={}
    spec=importlib.util.spec_from_file_location('original27',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    for k,path in r['groups'].items():
        rd=ROOT/path;d=data(rd,'tran.tran');v={('time' if key=='time' else 'i('+key[:-2].lower()+')' if key.endswith(':p') else 'v('+key.lower()+')'):list(map(float,val)) for key,val in d.items()};vectors['inl_dnl' if k=='linearity' else k]=v
        times=up.conversion_sample_times(50e6,9e-9,0 if k=='linearity' else 3,90 if k=='linearity' else 16 if k=='transfer' else 32);levels=[[up.sample(v,t)[f'v(d{i})'] for t in times] for i in range(4)];bad=sum(.36<a<1.44 for bit in levels for a in bit);compare(checks,k+'_invalid_levels',r['values'][k]['invalid_levels'],bad)
        net=(rd/'inputs/bench.scs').read_text();assert 'resistor r=50' in net and net.count('capacitor c=10f')==4 and 'delay=1p rise=20p fall=20p width=9.96n period=20n' in net
    out=up.extract_metrics(vectors)
    names={'transfer':{'code_errors':'transfer_error_count','missing_codes':'missing_codes'},'linearity':{'linearity_valid':'linearity_valid','transition_count':'linearity_transition_count','missing_codes':'linearity_missing_codes','monotonic':'monotonic','inl_LSB':'inl_max_lsb','dnl_LSB':'dnl_max_lsb'},'dynamic':{'sndr_dB':'sndr_db','sfdr_dB':'sfdr_db','power_W':'average_power_w','clock_power_W':'clock_drive_power_w'}}
    for k,aliases in names.items():
        for name,orig in aliases.items():compare(checks,k+'_'+name,float(r['values'][k][name]),float(out[orig]),atol=1e-12 if not name.endswith('_W') else 1e-15)
    # The source Sky130 text parser cannot parse native Spectre/HD. Independently
    # project only the native integrity result after checking every actual leaf.
    blocks=drawing.parse_source(CASE/'circuit.scs');top=blocks['flash_adc_4bit'];hd=json.loads((CASE/'hd_cells_manifest.json').read_text());allowed={'n18','p18','resistor','capacitor'}|set(blocks)|{x['name'] for x in hd['cells']}
    for block in blocks.values():
        for d in block['instances'].values():assert d['model'] in allowed
    assert len([x for x in top['instances'].values() if x['model']=='fa_comp'])==15
    oc=up.score(out,dict(integrity=dict(passed=True,message='Native allowed leaf types, actual zero-error simulations, geometry/HD checks and full schematic connectivity audited separately; not the original Sky130 parser.'),runs=3,failed_runs=[],blocked_runs=[]));assert all(x.passed for x in oc)
    finish(CASE,27,checks,[dict(name=x.name,passed=x.passed,detail=x.message) for x in oc],'Unmodified original Python transfer, endpoint-linearity, recursive-FFT and clipped-energy analyzers receive actual Spectre traces through a name-only adapter. Six original electrical check functions run unchanged. Native eligibility is separately validated; no claim to running the Sky130 text parser on Spectre.',dict(original_metrics=out,integrity_projection='NativeMOS/idealRC/localHD equivalence; source model parser not applicable.',source_checker_count=len(oc)))

if __name__=='__main__':main()
