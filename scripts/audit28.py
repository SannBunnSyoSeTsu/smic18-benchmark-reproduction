from audit29_common import *
import importlib.util
CASE=ROOT/'cases/28-fct-amplifier'

def main():
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('original_fct',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up);sys.path.pop(0)
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];original_checks=[];independent={};tier=r['status'].removeprefix('complete_');fraction={'original':0,'10pct':.1,'15pct':.15}[tier]
    for kind,path in r['groups'].items():
        d=data(ROOT/path,'tran.tran');t=d['time'];samples={};amp,tone=(.01,5) if kind=='10mv' else (.02,3)
        def at(signal,when):
            i=int(np.searchsorted(t,when));return float(d[signal][i-1]+(when-t[i-1])/(t[i]-t[i-1])*(d[signal][i]-d[signal][i-1]))
        for j in range(32):
            for suffix,off in [('',.88e-9),('_early',.78e-9)]:
                for side in ('p','n'):samples[f'out{side}{suffix}_{j:03d}']=at('vout'+side,(64+j)/900e6+off)
        a,z=64/900e6,96/900e6;tt=np.r_[a,t[(t>a)&(t<z)],z]
        source=-1.8*d['VDD:p']-d['VICM_DUT:p']-d['sam']*d['VSAM_DUT:p']-d['transfer']*d['VTRANSFER_DUT:p']+50e-6*d['iref'];pp=np.interp(tt,t,source)
        samples['power_w']=float(np.sum(np.diff(tt)*(pp[:-1]+pp[1:])/2)/(z-a));q=up.analyze(samples,32,tone,amp);assert q is not None;independent[kind]=q
        for key,value in q.items():compare(checks,kind+'_'+key,r['values'][kind][key],value,rtol=2e-8,atol=1e-10)
        oc={};up.add_metric_checks(oc,[dict(corner='tt',**q)],kind)
        original_checks.extend(dict(name=n,passed=bool(p),detail=detail) for n,p,detail in oc.values())
        for key,lo,hi in [('gain_vv',5.5,6.5),('cm_mean_v',.3,1.2),('output_min_v',.2,float('inf')),('output_max_v',-float('inf'),1.6),('hold_movement_ratio',0,.015),('power_w',0,.005)]:
            assert lo*(1-fraction)<=q[key]<=hi*(1+fraction),(kind,key,q[key],tier)
        assert q['sfdr_db']>=60+20*np.log10(1-fraction)
        net=(ROOT/path/'inputs/bench.scs').read_text();assert 'c=400f' in net and net.count('c=50f')==2 and 'IREF (0 iref) isource dc=50u' in net
    return finish(CASE,28,checks,original_checks,'Original unmodified 32-point direct DFT and analyze() independently applied to separately interpolated held/early samples; five-port signed power independently integrated. Original six checks per amplitude retained with truthful pass/fail; final classification uses the previously established original/10%/15% limits, with no timing, load or stimulus relaxation.',dict(independent_values=independent,selected_tier=tier,original_checks=original_checks))

if __name__=='__main__':main()
