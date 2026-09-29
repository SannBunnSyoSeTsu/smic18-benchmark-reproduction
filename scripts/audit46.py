from audit29_common import *
import importlib.util
CASE=ROOT/'cases/46-flash-adc3bit'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];rows=[]
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('original46',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    items=[dict(name=k+'_TT1.8V27C',group=k,corner='tt',vdd=1.8,temp_c=27,tone_bin=1 if k=='sine_low' else 7,phase_deg=212 if k=='sine_low' else 279.25) for k in ['transition','ramp','sine_low','sine_high']]
    for item in items:
        k=item['group'];rd=ROOT/r['groups'][k];d=data(rd,'tran.tran');t=d['time']
        if k in ['transition','ramp']:
            names=['time','b2','b1','b0','vin','clk_src','VDD:p','VREFP:p','VREFN:p','VCLK:p'];aliases=['time','v(b2)','v(b1)','v(b0)','v(vin)','v(clk_src)','i(vdd)','i(vrefp)','i(vrefn)','i(vclk_src)'];plot=up.Plot('Transient Analysis',aliases,list(map(list,zip(*(d[n] for n in names)))))
            out=up.transition_metrics(item,[plot]) if k=='transition' else up.static_metrics(item,[plot])
        else:
            measures={}
            for n in range(16):
                end=50e-9+n*20e-9+19e-9;start=end-9.5e-9;lo=np.searchsorted(t,start,'right');hi=np.searchsorted(t,end,'left')
                for bit in range(3):
                    y=d[f'b{bit}'];values=[float(np.interp(start,t,y)),*map(float,y[lo:hi]),float(np.interp(end,t,y))];key=f's{n}_b{bit}';measures[key]=float(np.interp(end,t,y));measures[key+'_min']=min(values);measures[key+'_max']=max(values)
            out=up.sine_metrics(item,measures)
        for name,value in r['values'][k].items():compare(checks,k+'_'+name,float(value),float(out[name]),atol=1e-12 if not name.endswith(('_w','_s','_a')) else 1e-15)
        rows.append(out)
        net=(rd/'inputs/bench.scs').read_text();assert 'resistor r=50' in net and net.count('capacitor c=15f')==3 and 'delay=10n rise=.3n fall=.3n width=9.4n period=20n' in net
        if k.startswith('sine'):assert f'sinephase={item["phase_deg"]:g}' in net
    up.CASES=tuple(items);oc=up.score(rows,[]);assert len(oc)==13 and all(x[1] for x in oc),oc
    records=json.loads((CASE/'conversion_records.json').read_text());assert sha(CASE/'conversion_records.json')==r['conversion_records_sha256']
    definitions=drawing.parse_source(CASE/'circuit.scs');assert len(definitions['fa_comp']['instances'])==11 and len([d for d in definitions['flash_adc_3bit']['instances'].values() if d['model']=='fa_comp'])==7
    finish(CASE,46,checks,[dict(name=n,passed=bool(ok),detail=msg) for n,ok,msg in oc],'Independent original Python analyzer receives actualSpectre traces throughpuredata Plot adapter. Staticramp, last-crossing/missingedge/stableband, signedcore/referencepower, positiveclockpower and originalrecursiveDFT(all16codes) recomputed. Original13checkfunctions at explicitfourTTfunctionalrecords; originalsourceunmodified.',dict(independent_rows=rows,conversion_records=records,projection='TT1.8V27C forramp/transition/bothcoherentsines; nootherPVT ornoise/mismatchclaim'))

if __name__=='__main__':main()
