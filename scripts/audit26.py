from audit29_common import *
import importlib.util,tempfile
CASE=ROOT/'cases/26-ota-c-biquad'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];rows=[]
    spec=importlib.util.spec_from_file_location('original26',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    def plot(name,d,names,aliases):return up.Plot(name,aliases,[list(x) for x in zip(*(d[n] for n in names))])
    for k,path in r['groups'].items():
        item=dict(group=k,corner='tt',vdd=1.8,temp_c=27);rd=ROOT/path
        if k=='ac':
            d=data(rd,'ac.ac');op=dc(rd);names=['voutp','voutn','vbpp','vbpn','VDD:p'];aliases=['v(voutp)','v(voutn)','v(vbpp)','v(vbpn)','i(vdd)'];p=plot('Operating Point',{n:[op[n]] for n in names},names,aliases);a=plot('AC Analysis',d,['freq',*names[:4]],['frequency',*aliases[:4]]);out=up.analyze_ac(item,[p,a],up.SPEC['operating'])
            mapping=dict(f0_Hz='f0_hz',Q='q',passgain_dB='passband_gain_db',fit_error_dB='fit_error_db_rms',atten20M_dB='attenuation_20mhz_db',bp_peak_Hz='bp_peak_frequency_hz',bp_peak_dB='bp_peak_gain_db',bp_1k_dB='bp_low_frequency_attenuation_db',bp_200k_dB='bp_low_attenuation_db',bp_20M_dB='bp_high_attenuation_db',cm_error_V='output_cm_error_v',power_W='power_w')
        elif k=='noise':
            d=data(rd,'noise.noise',required=['out']);psd=np.abs(d['out'])**2;vn=float(np.sqrt(np.dot(np.diff(d['freq']),(psd[:-1]+psd[1:])/2)));out=up.analyze_noise(item,[up.Plot('Integrated Noise',['onoise_total'],[[vn]])]);compare(checks,'noise_Vrms',r['values']['noise_Vrms'],vn);mapping={}
        else:
            d=data(rd,'tran.tran');names=['time','voutp','voutn','vbpp','vbpn'];p=plot('Transient Analysis',d,names,['time',*[f'v({n})' for n in names[1:]]]);out=(up.analyze_cmstep if k=='cmstep' else up.analyze_thd)(item,[p],up.SPEC['operating'])
            if k=='cmstep':mapping=dict(initial_error_V='cm_initial_error_v',settle_s='cm_settle_time_s',late_excursion_V='cm_late_excursion_v')
            else:
                mapping=dict(output_amplitude_V='output_amplitude_v',fundamental_gain='fundamental_gain',thd_dB='thd_db')
                if k=='thd_f0':
                    for key,target in mapping.items():compare(checks,'thd_f0_bp_'+key,r['values']['thd_f0_bp'][key],out['bandpass_'+target])
                    mapping={key:'lowpass_'+target for key,target in mapping.items()}
        for key,target in mapping.items():compare(checks,k+'_'+key,r['values'][k][key],out[target],atol=1e-12)
        rows.append(out);net=(rd/'inputs/bench.scs').read_text();assert net.count('capacitor c=250f')==4 and 'temp=27' in net and 'dc=20u' in net
    up.SPEC['pvt']['corners']=['tt'];up.SPEC['pvt']['operating_points']=[dict(supply_v=1.8,temperature_c=27)];up.SPEC['secondary']['points']=[dict(corner='tt',supply_v=1.8,temperature_c=27)]
    with tempfile.TemporaryDirectory(prefix='audit26-') as p:
        p=Path(p);write_json(p/'rows.json',rows);write_json(p/'run.json',dict(failed_runs=[]));args=[]
        for key,name in [('input','rows'),('run-summary','run'),('summary','summary'),('report','report'),('reward','reward')]:args+=['--'+key,str(p/(name+'.json'))]
        assert up.score_results(args)==0;oc=json.loads((p/'report.json').read_text())['results'];assert oc['summary']['tests']==16 and oc['summary']['failed']==0
    finish(CASE,26,checks,[dict(name=x['name'],passed=x['status']=='passed',detail=x['message']) for x in oc['tests']],'Original unmodifiedAC Gauss-eliminationfit, directDFTTHDandCMstepanalyzers onactualSpectre traces; independentlyintegratednoisePSD. SixTTfunctionalrecords projectedonlyinmemory; all16originalcheckbodies/limitsunchanged.',dict(independent_rows=rows,original_score=oc,noise_adapter='Spectreoutputdensity squared; independentpiecewiselinearPSD integration providedtooriginalintegrated-noisePlot'))

if __name__=='__main__':main()
