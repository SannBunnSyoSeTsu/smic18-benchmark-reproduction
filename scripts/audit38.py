from audit29_common import *
import importlib.util
CASE=ROOT/'cases/38-capless-ldo'

def extrema(t,y,a,b):
    lo=int(np.searchsorted(t,a,side='left'));hi=int(np.searchsorted(t,b,side='right'))
    q=list(y[lo:hi]);q.extend([float(np.interp(a,t,y)),float(np.interp(b,t,y))]);return min(q),max(q)

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];rows=[];psr=[];steps=[]
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('capless_original',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    for q in r['values']['line_points']:
        vin=q['supply_V'];tag=str(vin);d=data(ROOT/r['groups']['dc'+tag],'loads.dc');o=dc(ROOT/r['groups']['dc'+tag]);a=data(ROOT/r['groups']['psr'+tag],'ac.ac');t=data(ROOT/r['groups']['step'+tag],'tran.tran')
        assert len(d['iload'])==201 and np.allclose(d['iload'],np.linspace(0,.02,201),atol=1e-14)
        assert len(a['freq'])==801 and abs(a['freq'][0]-100)<1e-10 and abs(a['freq'][-1]-1e7)<1e-5
        out=dict(dc_min_V=float(np.min(d['vout'])),dc_max_V=float(np.max(d['vout'])),iq_A=abs(o['VSUP:p']),vref_current_A=o['VREF:p'])
        out['dc_error_V']=max(1-out['dc_min_V'],out['dc_max_V']-1)
        for k,f in [('psr1k_dB',1000),('psr100k_dB',100000),('psr1M_dB',1000000)]:
            idx=int(np.argmin(abs(a['freq']-f)));assert abs(a['freq'][idx]/f-1)<1e-12;z=a['vout'][idx];out[k]=-10*np.log10(z.real*z.real+z.imag*z.imag)
        for x,y,low,high in [(20,41,'droop_V','w1max_V'),(60,81,'w2min_V','bump_V'),(41,60,'t1min_V','t1max_V'),(81,100,'t2min_V','t2max_V')]:out[low],out[high]=extrema(t['time'],t['vout'],x*1e-6,y*1e-6)
        out['step_excursion_V']=max(abs(out[k]-1) for k in ['droop_V','w1max_V','bump_V','w2min_V']);out['step_recovery_V']=max(abs(out[k]-1) for k in ['t1min_V','t1max_V','t2min_V','t2max_V'])
        for k,v in out.items():compare(checks,f'{vin}V_{k}',q[k],v)
        rows.append(dict(name=f'TT27C{vin}V',vmin_v=out['dc_min_V'],vmax_v=out['dc_max_V'],iq_ua=out['iq_A']*1e6));psr.append(dict(name=f'TT27C{vin}V',supply=vin,psr1k_db=out['psr1k_dB'],psr100k_db=out['psr100k_dB'],psr1meg_db=out['psr1M_dB']))
        steps.append(dict(name=f'TT27C{vin}V',**{k.lower():out[k] for k in ['droop_V','w1max_V','bump_V','w2min_V','t1min_V','t1max_V','t2min_V','t2max_V']}))
        for kind in ['dc','psr','step']:
            text=(ROOT/r['groups'][kind+tag]/'inputs/bench.scs').read_text();assert f'VSUP (vin 0) vsource dc={vin:g}' in text and 'VREF (vref 0) vsource dc=.4' in text and 'CLOAD' not in text
    d=data(ROOT/r['groups']['start'],'tran.tran');q=r['values']['startup'];lo,hi=extrema(d['time'],d['vout'],200e-6,400e-6);st=dict(peak_V=float(max(d['vout'])),tail_min_V=lo,tail_max_V=hi,tail_error_V=max(abs(lo-1),abs(hi-1)))
    for k,v in st.items():compare(checks,'startup_'+k,q[k],v)
    # Only the expected point collection is projected; original check bodies/limits remain intact.
    up.CORNERS=('tt',);up.POINTS=up.NOMINAL_POINTS;up.MATRIX=2;up.START_POINTS=(('tt',27,1.8),)
    oc=[up.dc_check(rows,2),up.iq_check(rows,2),up.psr_check_1k(psr),up.psr_check_flat(psr,'psr100k_db',20,'psr_100khz','100kHz'),up.psr_check_flat(psr,'psr1meg_db',10,'psr_1mhz','1MHz'),up.step_excursion_check(steps),up.step_recovery_check(steps),up.start_check({'tt27C1.8V':dict(m0_peak_v=st['peak_V'],m0_smin_v=lo,m0_smax_v=hi)})]
    assert len(oc)==8 and all(q[1] for q in oc),oc
    blocks=drawing.parse_source(CASE/'circuit.scs');assert set(blocks)=={'capless_ldo'};assert blocks['capless_ldo']['ports']==['vin','vout','vss','vref'];caps=[]
    for name,d in blocks['capless_ldo']['instances'].items():
        assert d['model'] in ['n18','p18','resistor','capacitor']
        if d['model']=='capacitor':caps.append(dict(name=name,cap_F=drawing.numeric(d['parameters']['c'])*drawing.numeric(d['parameters'].get('m','1'))))
    total=sum(x['cap_F'] for x in caps);assert total<=up.CAP_BUDGET_F and len(caps)==4
    assert blocks['capless_ldo']['instances']['MPASS']['model']=='p18'
    startnet=(ROOT/r['groups']['start']/'inputs/bench.scs').read_text();assert 'RLOAD (vout 0) resistor r=2k' in startnet and '100u 1.8 400u 1.8' in startnet
    finish(CASE,38,checks,[dict(name=n,passed=bool(ok),detail=msg) for n,ok,msg in oc],'Independent searchsorted windows with explicit endpoint interpolation, supply-current decomposition and complex-power PSR. Eight unmodified upstream check functions run against explicit TT27C two-supply subset and one startup; original other28DC/step,8PSR,3startup points excluded. Independent primitive/hierarchy parse enforces PMOSpass and totalC<=1nF.',dict(capacitors=caps,total_cap_F=total,dc_rows=rows,psr_rows=psr,step_rows=steps))

if __name__=='__main__':main()
