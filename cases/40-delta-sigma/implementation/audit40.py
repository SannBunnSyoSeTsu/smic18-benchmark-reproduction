from audit29_common import *
import importlib.util
CASE=ROOT/'cases/40-delta-sigma'

def original(case,slot):
    sys.path.insert(0,str(case/'source/tests'))
    spec=importlib.util.spec_from_file_location('original40',case/'source/tests/verify.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);sys.path.pop(0)
    return module

def main():
    up=original(CASE,40);r=json.loads((CASE/'latest_results.json').read_text());checks=[];records={}
    for case in up.CASES:
        k=case['name'];d=data(ROOT/r['groups'][k],'tran.tran');t=d['time'];ts=20e-9+np.arange(580)*100e-9
        assert ts[-1]<=t[-1]<ts[-1]+100e-9
        idx=np.searchsorted(t,ts,side='right')-1;aa=d['ctrl_a'][idx];bb=d['ctrl_b'][idx];codes=1.-2.*(aa>.9);valid=np.isfinite(aa)&np.isfinite(bb)&((aa>.9)!=(bb>.9))
        a=up.analyze(codes,valid,case['bin'],2*case['amp']);records[k]=a;q=r['values'][k]
        for key in ('dc','gain','density','transitions','invalid'):compare(checks,k+'_'+key,q[key],a[key])
        for osr in [8,16,32]:compare(checks,k+f'_sndr{osr}_dB',q[f'sndr{osr}_dB'],a['sndr'][osr])
        compare(checks,k+'_shaping_dB',q['shaping_dB'],a['shaping'])
        compare(checks,k+'_state_peak_V',q['state_peak_V'],max(abs(d['intp']-d['intn'])))
        compare(checks,k+'_source_mean_power_W',q['source_mean_power_W'],-1.8*float(np.mean(d['VDD:p'])))
        physical=float(-.9*np.sum((d['VDD:p'][:-1]+d['VDD:p'][1:])*np.diff(t))/(t[-1]-t[0]))
        compare(checks,k+'_time_weighted_power_W',q['time_weighted_power_W'],physical)
        compare(checks,k+'_DC_error',q['DC_error'],abs(a['dc']-2*case['offset']/up.DAC_DIFF))
        net=(ROOT/r['groups'][k]/'inputs/bench.scs').read_text();assert net.count('resistor r=50')==5 and net.count('capacitor c=1p')==2 and 'dc=50u' in net and 'stop=58u' in net
    ratio=records['mid_inv']['coeff']/records['mid_pos']['coeff'];phase=up.angle_error_deg(np.angle(ratio),np.pi);gain=records['nominal']['sndr'][32]-records['nominal']['sndr'][16]
    compare(checks,'polarity_ratio',r['values']['suite']['polarity_amplitude_ratio'],abs(ratio));compare(checks,'polarity_phase_deg',r['values']['suite']['polarity_phase_error_deg'],phase,atol=1e-10);compare(checks,'osr_gain_dB',r['values']['suite']['osr_improvement_dB'],gain)
    # The source gates are embedded in main(): apply those exact inequalities
    # to the independently recomputed original-analyzer outputs.
    stream=lambda a:a['invalid']==0 and .05<a['density']<.95 and a['transitions']>.05
    oc=[('nominal_function',stream(records['nominal']) and .7<=records['nominal']['gain']<=1.35),('stimulus_transfer',all(stream(a) and .7<=a['gain']<=1.35 for a in records.values())),('dc_tracking',max(r['values'][k]['DC_error'] for k in records)<=.035),('polarity_tracking',.8<=abs(ratio)<=1.25 and phase<=15),('bounded_state',max(r['values'][k]['state_peak_V'] for k in records)<2),('noise_shaping',min(a['shaping'] for a in records.values())>=10),('first_order_gain',gain>=6),('power',all(0<=r['values'][k]['source_mean_power_W']<=.002 for k in records)),('sndr_suite',all(a['sndr'][32]>=40 for a in records.values()))]
    assert all(p for n,p in oc),oc
    blocks=drawing.parse_source(CASE/'circuit.scs');assert all(d['model'] in {'n18','p18','resistor','capacitor'}|set(blocks) for b in blocks.values() for d in b['instances'].values())
    return finish(CASE,40,checks,[dict(name=n,passed=bool(p),detail='Original main() inequality, independently recomputed traces.') for n,p in oc],'Unmodified original analyze() receives580 actual in-record decisions, retaining its last512 samples and all originalFFT bins. Original extractor could append a58.02us sample beyond the58us record and clip it; this explicit boundary fix forbids extrapolation and is recorded in the frozen contract. Nine source electrical inequalities are separately applied to independently recomputed quantities. Source arithmetic-current mean and physical time-weighted power are both retained; OTA/comparator fixtures are native transistor migrations.',dict(sample_boundary='Exactly580 samples20ns..57.92us; final5126.82us..57.92us; no58.02us extrapolated sample.',source_gates=[(n,bool(p)) for n,p in oc],all_power_windows_include_startup=True))

if __name__=='__main__':main()
