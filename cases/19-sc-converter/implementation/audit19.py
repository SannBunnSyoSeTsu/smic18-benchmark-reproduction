from audit29_common import *
import importlib.util
CASE=ROOT/'cases/19-sc-converter'

def section(d,a,b):
    t=d['time'];left=np.searchsorted(t,a,'right');right=np.searchsorted(t,b,'left');tt=[a,*t[left:right],b]
    out={k:[float(np.interp(a,t,v)),*map(float,v[left:right]),float(np.interp(b,t,v))] for k,v in d.items() if k!='time'}
    return np.array(tt),{k:np.array(v) for k,v in out.items()}

def mean(t,v):return float(sum((float(v[i])+float(v[i-1]))*(float(t[i])-float(t[i-1]))/2 for i in range(1,len(t)))/(t[-1]-t[0]))

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];rows=[];details=[]
    for label,q in zip(['heavy','light'],r['values']['loads']):
        rd=ROOT/r['groups'][label];d=data(rd,'tran.tran');t,w=section(d,.3e-6,.7e-6);load=q['load_ohm'];v=w['vout'];o=dict(vout_mean_V=mean(t,v),vout_min_V=float(min(v)),vout_max_V=float(max(v)),supply_power_W=mean(t,-w['vdd']*w['VDD:p']),clock_power_W=mean(t,(abs(w['clk_src']*w['VCLK:p'])-w['clk_src']*w['VCLK:p'])/2),load_power_W=mean(t,v**2/load))
        o.update(conversion_ratio=o['vout_mean_V']/1.8,ripple_V=o['vout_max_V']-o['vout_min_V'],input_power_W=o['supply_power_W']+o['clock_power_W'],load_current_A=o['vout_mean_V']/load);o['efficiency']=o['load_power_W']/o['input_power_W']
        if label=='heavy':
            tt=d['time'];y=d['vout'];target=.6804;idx=[i for i in range(1,len(tt)) if y[i-1]<target<=y[i]][-1];o['startup_s']=float(np.interp(target,[y[idx-1],y[idx]],[tt[idx-1],tt[idx]]));_,p=section(d,200e-9,.7e-6);o['post_startup_min_V']=float(min(p['vout']))
        for k,v in o.items():compare(checks,label+'_'+k,q[k],v)
        aliases={'supply_power_W':'vdd_input_power_w','clock_power_W':'clock_input_power_w','vout_mean_V':'vout_mean_v','vout_min_V':'vout_min_v','vout_max_V':'vout_max_v','post_startup_min_V':'post_startup_min_v'}
        rows.append(dict(name='tt/1.80V/+27C',point=('tt',1.8,27),**{aliases.get(k,k.lower()):v for k,v in o.items()}))
        for record in [x for x in r['terminal_voltages'] if x['load']==label]:
            nodes=re.search(r'^'+record['device']+r'\s+\(([^)]+)\)',(CASE/'circuit.scs').read_text(),re.M)[1].split();z=[np.zeros(len(d['time'])) if n=='vss' else d[n] if n in d else d['X.'+n] for n in nodes]
            for k,a,b in [('VGS',1,2),('VGD',1,0),('VDS',0,2),('VGB',1,3),('VDB',0,3),('VSB',2,3)]:
                peak=float(np.max(np.abs(np.subtract(z[a],z[b]))));assert peak<=1.98;compare(checks,label+'_'+record['device']+'_'+k,record['peaks_V'][k],peak)
        net=(rd/'inputs/bench.scs').read_text();assert 'skipdc=yes' in net and 'delay=5n rise=.4n fall=.4n width=24.6n period=50n' in net and f'resistor r={load:g}' in net
        details.append(dict(load=label,window_points=len(t),netlist_checked=True,terminal_limit_V=1.98))
    rout=(rows[1]['vout_mean_v']-rows[0]['vout_mean_v'])/(rows[0]['load_current_a']-rows[1]['load_current_a']);compare(checks,'output_resistance_ohm',r['values']['output_resistance_ohm'],rout)
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('original19',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    up.POINTS=(up.NOMINAL,)
    oc=[*up.heavy_checks([rows[0]],up.POINTS,'nominal').values(),*up.light_checks([rows[1]],up.POINTS,'nominal').values(),up.output_resistance_check([rows[0]],[rows[1]])];assert len(oc)==8 and all(x[1] for x in oc),oc
    finish(CASE,19,checks,[dict(name=n,passed=bool(ok),detail=msg) for n,ok,msg in oc],'Independent per-interval integration including positive-only clock power, last rising crossing plus fixed startup hold, matched-load resistance and all6terminal differences perpowerMOS. Eight original check functions at explicitnominalpoint; no sourceorlimit edits.',details)

if __name__=='__main__':main()
