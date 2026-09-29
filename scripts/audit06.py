from audit29_common import *
CASE=ROOT/'cases/06-ring-amplifier'

def clipped(t,v,start,stop):
    pts=[(start,float(np.interp(start,t,v)))]+[(float(x),float(y)) for x,y in zip(t,v) if start<x<stop]+[(stop,float(np.interp(stop,t,v)))];return pts

def mean(t,v,start,stop):
    p=clipped(t,v,start,stop);return sum((x1-x0)*(y0+y1)/2 for (x0,y0),(x1,y1) in zip(p,p[1:]))/(stop-start)

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];ind={}
    for name,path in r['groups'].items():
        rd=ROOT/path;d=data(rd,'tran.tran');t=d['time'];diff=d['voutp']-d['voutn'];avg=mean(t,diff,1.4e-6,1.45e-6);q=dict(mean_diff_V=avg)
        if name in ['pos20','neg20']:
            tar=.16 if name=='pos20' else -.16;er=np.abs(diff-tar)-.016;events=[]
            for i in range(len(t)-1):
                if t[i]>=1.05e-6 and t[i+1]<1.499e-6 and er[i]>0>=er[i+1]:events.append(float(t[i]+(t[i+1]-t[i])*er[i]/(er[i]-er[i+1])-1.05e-6))
            assert events
            q.update(static_error_fraction=abs(avg-tar)/.16,cm_error_V=abs((mean(t,d['voutp'],1.4e-6,1.45e-6)+mean(t,d['voutn'],1.4e-6,1.45e-6))/2-.9),power_W=abs(1.8*mean(t,d['VDD:p'],1.2e-6,1.45e-6)),settle_s=events[-1],ripple_V=max(abs(float(diff[i])-avg) for i,x in enumerate(t) if 1.4e-6<=x<=1.45e-6))
        ind[name]=q
        for key,val in q.items():compare(checks,name+'_'+key,r['values'][name][key],val,atol=2e-15)
        net=(rd/'inputs/bench.scs').read_text();assert net.count('capacitor c=10p')==2 and net.count(') SW_RESET')==7 and 'model SW_RESET relay ropen=1e12 rclosed=100 vth=.25 trans=1u hysteresis=.1' in net and 'isource dc=25u' in net and 'skipdc=yes' in net and 'cmin=1f' in net
        assert not re.search(r'(?m)^ic\s',net)
    ind['transfer']=dict(positive_gain=(ind['pos20']['mean_diff_V']-ind['pos10']['mean_diff_V'])/.01,bipolar_gain=(ind['pos20']['mean_diff_V']-ind['neg20']['mean_diff_V'])/.04,zero_residual_V=abs(ind['zero']['mean_diff_V']))
    for k,v in ind['transfer'].items():compare(checks,'transfer_'+k,r['values']['transfer'][k],v)
    q=ind['transfer'];oc=[dict(name='gain_transfer',passed=7.2<=q['positive_gain']<=8.8 and 7.2<=q['bipolar_gain']<=8.8),dict(name='gain_zero_input',passed=q['zero_residual_V']<=.005)]
    for key,lim in [('static_error_fraction',.01),('cm_error_V',.05),('power_W',400e-6),('settle_s',50e-9),('ripple_V',.005)]:oc.append(dict(name=key,passed=max(ind[k][key] for k in ['pos20','neg20'])<=lim))
    assert all(q['passed'] for q in oc)
    finish(CASE,6,checks,oc,'Independent explicit boundary interpolation and scalar trapezoid sums recompute the original external-port means, last commanded-band entry, ripple and supply power. Both gain slopes and seven published original electrical checks are evaluated independently; no design extractor is imported. Native model-based relay vth=.25/hysteresis=.1 implements original switching memory with 1uV transition regularization and unchanged 0.5V reference; vt1/vt2 alone would not implement hysteresis.',dict(independent_values=ind,zero_state='No imposed capacitor/node voltage; existing skipdc and 1fF shunt preserved.',startup='Two actual native NMOS bias-gated input startup paths are part of DUT and schematic, not hidden bench initialization.'))

if __name__=='__main__':main()
