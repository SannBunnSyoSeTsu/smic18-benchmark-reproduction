"""Independent original recursive-FFT/decoder audit of actual SAR traces."""
from audit29_common import *
import importlib.util

def original(case,slot):
    sys.path.insert(0,str(case/'source/tests'))
    spec=importlib.util.spec_from_file_location(f'original_{slot}',case/'source/tests/verify.py')
    up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    sys.path.pop(0);return up

def main(bits):
    slot=48 if bits==4 else 42;case=ROOT/f'cases/{slot}-sar-adc{bits}bit';up=original(case,slot)
    r=json.loads((case/'latest_results.json').read_text());checks=[];rows=[];powers=[]
    for label,path in r['groups'].items():
        kind=label if bits==4 else label[:-1];chunk=0 if bits==4 else int(label[-1]);d=data(ROOT/path,'tran.tran');t=d['time']
        N=16 if kind.startswith('transfer') or bits==6 else 32
        start=(34.5 if kind.startswith('transfer') else 44.5) if bits==4 else (19 if kind.startswith('transfer') else 29)
        vals={};invalid=0
        for j in range(N):
            when=(start+10*j)*1e-9;idx=int(np.searchsorted(t,when));a,b=t[idx-1],t[idx]
            for bit in range(bits):
                v=d[f'd{bit}'][idx-1]+(when-a)/(b-a)*(d[f'd{bit}'][idx]-d[f'd{bit}'][idx-1]);vals[f's{j}_d{bit}']=float(v);invalid+=.36<v<1.44
        codes=up.decode_codes(vals,N,1.8);row=dict(bench=kind,chunk=chunk,name=label,codes=codes)
        compare(checks,label+'_invalid_levels',r['values'][label]['invalid_levels'],invalid)
        if kind.startswith('transfer'):
            expected=list(up.EXPECTED_CODES if kind=='transfer' else up.ALT_EXPECTED_CODES)
            if bits==6:expected=expected[16*chunk:16*(chunk+1)]
            compare(checks,label+'_code_errors',r['values'][label]['code_errors'],sum(a!=b for a,b in zip(expected,codes)))
        else:
            left,right=([39.5e-9,359.5e-9] if bits==4 else [19.5e-9,179.5e-9])
            source=-1.8*(d['VDD:p']+d['VREFP:p'])-.9*d['VCM:p']-(d['vinp']-.9)*d['VINP:p']-(d['vinn']-.9)*d['VINN:p']-d['clks_src']*d['VCLKS:p']
            tt=np.r_[left,t[(t>left)&(t<right)],right];pp=np.interp(tt,t,source)
            power=float(np.sum((pp[:-1]+pp[1:])*.5*np.diff(tt))/(right-left));powers.append(power);row['average_power_w']=power
            compare(checks,label+'_power_W',r['values'][label]['power_W'],power)
        net=(ROOT/path/'inputs/bench.scs').read_text();assert 'resistor r=50' in net and net.count('capacitor c=10f')==bits and 'delay=1p rise=20p fall=20p width=1.98n period=10n' in net
        rows.append(row)
    if bits==6:
        logical=[up.aggregate_chunks(rows,k,31) for k in ('transfer','transfer_alt','dynamic')]
    else:
        logical=rows
        for row in logical:
            if not row['bench'].startswith('dynamic'):continue
            c=row['codes'];N=len(c);tone=15 if row['bench']=='dynamic' else 13
            spectrum=up.fft([v-sum(c)/N for v in c]);signal=abs(spectrum[tone])**2
            noise=sum(abs(spectrum[k])**2 for k in range(1,N//2))-signal+.5*abs(spectrum[N//2])**2
            row['sndr_db']=up.ratio_db(signal,noise);row['normalized_enob_bits']=(row['sndr_db']+up.ratio_db((N*2**bits/4)**2,signal)-1.76)/6.02
    for row in logical:
        if not row['bench'].startswith('dynamic'):continue
        q=r['values'][row['bench']+'_spectrum']
        compare(checks,row['bench']+'_sndr_dB',q['sndr_dB'],row['sndr_db'],atol=1e-10)
        compare(checks,row['bench']+'_normalized_enob_bits',q['normalized_enob_bits'],row['normalized_enob_bits'],atol=1e-10)
    compare(checks,'maximum_record_power_W',r['gates']['power']['value'],max(powers))
    oc=[up.transfer_check([x for x in logical if x['bench'].startswith('transfer')])]+up.dynamic_checks([x for x in logical if x['bench'].startswith('dynamic')],2 if bits==4 else 1)
    assert all(x[1] for x in oc),oc
    blocks=drawing.parse_source(case/'circuit.scs');hd=json.loads((case/'hd_cells_manifest.json').read_text());allowed={'n18','p18','capacitor'}|set(blocks)|{x['name'] for x in hd['cells']}
    assert all(d['model'] in allowed for b in blocks.values() for d in b['instances'].values())
    return finish(case,slot,checks,[dict(name=n,passed=bool(p),detail=d) for n,p,d in oc],'Actual traces independently interpolated at the original fixed conversion times; original unmodified decoder, recursiveFFT and four electrical checks retained. Signed six-source clipped energy independently integrated. '+('Original chunk aggregator averages four powers; additionally every individual chunk must satisfy the same maximum power limit.' if bits==6 else 'Original TT main and alternate dynamic records retained; SS/FF source corners outside nominal scope.'),dict(original_nominal_rows=logical,all_record_rows=rows,source_power_rule='four-chunk mean plus stricter maximum' if bits==6 else 'worst of both TT dynamic records'))
