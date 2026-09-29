from audit29_common import *
import importlib.util,math
CASE=ROOT/'cases/30-gilbert-mixer'

def db(a,b=1):return 20*math.log10(max(a,1e-30)/max(b,1e-30))
def spectrum(d,start,stop):
    n=2048;phase=np.arange(n)/n;tt=start+phase*(stop-start);basis=np.exp(-2j*np.pi*np.arange(61)[:,None]*phase[None,:])
    return {key:2*np.abs(basis@np.interp(tt,d['time'],d[p]-d[q]))/n for key,p,q in [('out','ifoutp','ifoutn'),('rf','rfp','rfn'),('lo','lop','lon')]}

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];rows=[];raw={}
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('original30',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    for key,path in r['groups'].items():
        rd=ROOT/path;d=data(rd,'tran.tran');net=(rd/'inputs/bench.scs').read_text();assert net.count('resistor r=50')==4 and net.count('capacitor c=200f')==2 and 'IREF (vdd iref) isource dc=50u' in net
        if key.startswith('rf'):
            rf=float(key[2:5])*1e9;lo=rf-2e8;imb=key.endswith('imb');sp=spectrum(d,5e-9,15e-9);at=lambda kind,hz:float(sp[kind][round(hz/1e8)]);t=d['time'];a=np.searchsorted(t,5e-9,'right');b=np.searchsorted(t,15e-9,'left');tt=np.r_[5e-9,t[a:b],15e-9]
            def avg(y):
                v=np.interp(tt,t,y);return float(np.dot(np.diff(tt),(v[1:]+v[:-1])/2)/(tt[-1]-tt[0]))
            amp=at('out',2e8);low=float(sp['out'][1]);high=float(max(sp['out'][3:31]));cm=avg((d['ifoutp']+d['ifoutn'])/2)
            out=dict(conversion_gain_db=db(amp,at('rf',rf)),lo_if_isolation_db=db(at('out',lo),at('lo',lo)),rf_if_feedthrough_db=db(at('out',rf),at('rf',rf)),lo_rf_isolation_db=db(at('rf',lo),at('lo',lo)),output_dc_balance_v=abs(avg(d['ifoutp']-d['ifoutn'])),output_common_mode_v=cm,output_headroom_to_vdd_v=1.8-cm,power_w=avg(-d['vdd']*d['VDD:p']),if_amp_v=amp,spur_low_v=low,spur_high_v=high,spur_dbc=db(max(low,high),amp))
            old=next(x for x in r['values']['rf'] if x['RF_Hz']==rf and x['imbalance']==imb)
            for k,v in out.items():
                if k in ['lo_if_isolation_db','rf_if_feedthrough_db','lo_rf_isolation_db']:compare(checks,key+'_'+k+'_linear',10**(old[k]/20),10**(v/20),atol=1e-12)
                else:compare(checks,key+'_'+k,old[k],v,atol=1e-12)
            point=up.RfPoint(key,'tt',1.8,27,rf_ghz=rf/1e9,rf_imbalance=.02 if imb else 0,lo_imbalance=.02 if imb else 0,lo_phase_error=2 if imb else 0,robust_isolation=imb);rows.append(dict(name=key,point=point,**out))
        else:
            sp=spectrum(d,10e-9,30e-9);at=lambda kind,hz:float(sp[kind][round(hz/50e6)]);out=dict(fund1=at('out',200e6),fund2=at('out',250e6),im3lo=at('out',150e6),im3hi=at('out',300e6),input1=at('rf',2.4e9),input2=at('rf',2.45e9),gain_dB=db(at('out',200e6),at('rf',2.4e9)));raw[key]=out
            for k,v in out.items():compare(checks,key+'_'+k,r['values']['linearity_raw'][key][k],v,atol=1e-12)
    lin=dict(name='TT1.8V27C')
    for key,prefix in [('two_low','low'),('two_high','high')]:
        for k,target in dict(fund1='fundamental_one_v',fund2='fundamental_two_v',im3lo='im3_lower_v',im3hi='im3_upper_v',input1='input_one_v',input2='input_two_v').items():lin[prefix+'_'+target]=raw[key][k]
    lin.update(small_conversion_gain_db=raw['small']['gain_dB'],large_conversion_gain_db=raw['large']['gain_dB'])
    a,b=raw['two_low'],raw['two_high'];fund=lambda q:(q['fund1']+q['fund2'])/2;inp=lambda q:(q['input1']+q['input2'])/2;im=lambda q:max(q['im3lo'],q['im3hi']);step=db(inp(b),inp(a));out=dict(IIP3_dBm=min(db(inp(q))+db(fund(q),im(q))/2 for q in [a,b])+10*math.log10(5),fundamental_slope=db(fund(b),fund(a))/step,IM3_slope=db(im(b),im(a))/step,tone_gain_difference_dB=max(abs(db(q['fund1'],q['fund2'])) for q in [a,b]),compression_dB=raw['small']['gain_dB']-raw['large']['gain_dB'])
    for k,v in out.items():compare(checks,k,r['values']['linearity'][k],v,atol=1e-10)
    up.RF_POINTS=tuple(x['point'] for x in rows);up.LINEARITY_POINTS=(up.LinearityPoint('TT1.8V27C','tt',1.8,27,41001),);oc=up.evaluate(rows,[lin]);assert len(oc)==7 and all(x[1] for x in oc),oc
    finish(CASE,30,checks,[dict(name=n,passed=bool(ok),detail=msg) for n,ok,msg in oc],'Independent directcomplexDFT2048samples (notFFT), piecewiseintegration, RF/IF/LOphysicalpeakratiosandtwo-tone/compression recomputed. SevenunmodifiedupstreamchecksprojectedtosixRFandoneTTlinearitypoint; deepnullscomparedinlinearunits.',dict(independent_rf=[{k:v for k,v in x.items() if k!='point'} for x in rows],independent_linearity=lin,derived_linearity=out,comparison_note='DeepisolationdirectDFTvsFFT absolutelinearratiotolerance1e-12; numericalrununcertainty2e-5, notabsoluteRFchipisolationprediction.'))

if __name__=='__main__':main()
