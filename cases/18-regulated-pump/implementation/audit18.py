from audit29_common import *
import importlib.util,copy
CASE=ROOT/'cases/18-regulated-pump'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];rows=[];terminal=[]
    for q in r['values']['enabled']:
        ua=q['load_uA'];rd=ROOT/r['groups'][f'load{ua}'];d=data(rd,'tran.tran');t=d['time'];sl=slice(np.searchsorted(t,190e-6,'right'),np.searchsorted(t,200e-6,'left'));tt=np.r_[190e-6,t[sl],200e-6]
        def crop(y):return np.r_[float(np.interp(tt[0],t,y)),y[sl],float(np.interp(tt[-1],t,y))]
        def mean(y):return float(np.dot(np.diff(tt),(y[:-1]+y[1:])/2)/(tt[-1]-tt[0]))
        v=crop(d['VOUT']);avg=mean(v);out=dict(vout_avg_V=avg,vout_min_V=float(min(v)),vout_max_V=float(max(v)),enabled_current_A=abs(mean(crop(d['VSENSE:p']))),control_avg_V=mean(crop(d['X.ctrl'])),driver_supply_avg_V=mean(crop(d['X.vclk'])),error_V=abs(avg-2.34),ripple_V=float(np.ptp(v)))
        for k,x in out.items():compare(checks,f'{ua}uA_'+k,q[k],x)
        job=('tt',1.8,40,ua*1e-6);rows.append(dict(job=job,point=job[:3],load=job[-1],name=f'TT40C{ua}uA',avg=avg,max=out['vout_max_V'],min=out['vout_min_V'],current=out['enabled_current_A']))
        for record in [x for x in r['terminal_voltages'] if x['load_uA']==ua]:
            nodes=re.search(r'^'+record['device']+r'\s+\(([^)]+)\)',(CASE/'circuit.scs').read_text(),re.M)[1].split();z=[np.zeros(len(t)) if n=='AVSS' else d[n] if n in d else d['X.'+n] for n in nodes];peaks={k:float(np.max(np.abs(z[a]-z[b]))) for k,a,b in [('VGS',1,2),('VGD',1,0),('VDS',0,2),('VGB',1,3),('VDB',0,3),('VSB',2,3)]};assert max(peaks.values())<=record['limit_V'] and peaks==record['peaks_V'];terminal.append(dict(load_uA=ua,device=record['device'],max_V=max(peaks.values()),limit_V=record['limit_V'],passed=True))
        net=(rd/'inputs/bench.scs').read_text();assert 'temp=40' in net and 'CLOAD (VOUT 0) capacitor c=1n' in net and 'IBIAS (src IBN1U) isource dc=1u' in net and 'skipstart=2u skipstop=180u skipcount=100' in net
    rd=ROOT/r['groups']['disabled'];off=abs(dc(rd)['VSENSE:p']);compare(checks,'disabled_current_A',r['values']['disabled_current_A'],off);job=('tt',1.8,40,None);rows.append(dict(job=job,point=job[:3],load=None,name='TT40Coff',avg=None,min=None,max=None,current=off));net=(rd/'inputs/bench.scs').read_text();assert 'VEN (ensrc 0) vsource dc=0' in net and 'ILOAD' not in net and 'dcOp dc' in net
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('original18',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up);oc=up.checks(copy.deepcopy(rows),{x['job'] for x in rows});assert [n for n,ok,_ in oc if not ok]==['pvt_enabled_current']
    accepted=all(abs(q['avg']-2.34)<=.117*1.1 and q['max']-q['min']<=.005*1.1 and q['current']<=200e-6*1.1 for q in rows[:-1]) and off<=100e-9*1.1;assert accepted and r['status']=='complete_10pct'
    details=dict(original_checks=[dict(name=n,passed=bool(ok),detail=msg) for n,ok,msg in oc],accepted_10pct=True,only_relaxed_metric='50uA enabledAVDDcurrent',terminal_devices=terminal)
    finish(CASE,18,checks,details['original_checks'],'Independent dot-product integration overexact190–200uswithendpoints, separateoffDCandallpowerMOSterminalscreen. Unmodifiedoriginal fourcheckgroups truthfullyreturnthreepass/oneenabledcurrentfail; accepted10% tierverifiedseparately. Biasupstreamofsense excludedexactlyasoriginal.',details)

if __name__=='__main__':main()
