"""Beta-multiplier-biased resistor-load differential amplifier, nominal only."""
from common import *
from case16_miller import prefix
import argparse
CASE=ROOT/'cases/13-constant-gm'
DEVS=['MREF','MST','MB1','MB2','MP1','MP2','MTAIL','MINP','MINN']

def design(rb=1450,rl=5600,gmid=14,current=45):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={'n_master_input':lut_size('n18',1,gmid,current*1e-6,.45),'p_mirror':lut_size('p18',1,10,current*1e-6,.9),'reference':lut_size('n18',1,12,50e-6,.45)}
    tab=json.loads((ROOT/'lut_supplement/tt/n18_L4000nm_VDS1.350_W0.240.json').read_text())['data'];order=np.argsort(tab['vgs_V']);vg=roles['reference']['Vgs_V']
    def query(key):return float(np.interp(vg,np.asarray(tab['vgs_V'])[order],np.asarray(tab[key])[order]))
    roles['startup']=lut_size('n18',4,query('gmid'),query('id_ref_A'),1.35,.24)
    roles['startup']['selection']='Width-specific LUT selected at VGS predicted by the reference diode LUT; initial Wref10 gmID12 estimate overpredicted gmID and underpredicted startup current.'
    w={k:v['rounded_W_um'] for k,v in roles.items()};c=CASE/'circuit.scs'
    c.write_text(f'''// Self-biased beta multiplier, density-matched input pair and resistor loads.
simulator lang=spectre
subckt cgm_amp (vss iref vdd vinp vinn voutp voutn)
MREF (iref iref vss vss) n18 w={w['reference']:g}u l=1u
MST (nc iref vss vss) n18 w={w['startup']:g}u l=4u
MB1 (nb nb vss vss) n18 w={w['n_master_input']:g}u l=1u
MB2 (nc nb rb2 vss) n18 w={w['n_master_input']:g}u l=1u m=4
RB (rb2 vss) resistor r={rb:g}
MP1 (nb nc vdd vdd) p18 w={w['p_mirror']:g}u l=1u
MP2 (nc nc vdd vdd) p18 w={w['p_mirror']:g}u l=1u
MTAIL (tail nb vss vss) n18 w={w['n_master_input']:g}u l=1u m=2
MINP (voutn vinp tail vss) n18 w={w['n_master_input']:g}u l=1u
MINN (voutp vinn tail vss) n18 w={w['n_master_input']:g}u l=1u
RLP (vdd voutp) resistor r={rl:g}
RLN (vdd voutn) resistor r={rl:g}
ends cgm_amp
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,rb_Ohm=rb,rl_Ohm=rl,branch_target_uA=current,n_beta_ratio=4,n_tail_m=2,rationale='Beta multiplier sets nonzero gm using RB and 4:1 n sizing; input unit is the master unit. gm*RL targets3.5, RL*I targets250mV load drop. The square-law gm≈1/RB is only an initial estimate because body effect and moderate inversion matter. A weak IREF-controlled n18 pulls the p mirror diode low to start the loop and remains on.'))
    write_json(CASE/'contract.json',dict(source_task='sky130-constant-gm-stable-gain-amplifier-pvt',corner='tt',VDD_V=1.8,temperature_C=27,VCM_V=.95,reference_A=50e-6,load_each_F=.5e-12,gain_frequency_Hz=1e6,gain_range=[3,4],bandwidth_min_Hz=30e6,bandwidth_reference='gain at1MHz / sqrt(2)',load_drop_range_V=[.15,.4],imbalance_max_V=.01,linearity_grid_V=[-.06,.06,.002],linearity_comparison_V=[-.06,-.03,.03,.06],central_gain_V=[-.002,.002],gain_error_max=.08,power_max_W=500e-6,cold_start='skipdc=yes, all nodes initialized to zero',vdd_vcm_ramp_s=[.1e-6,1.1e-6],iref_ramp_s=[1.2e-6,1.22e-6],differential_step_V=.02,differential_step_ramp_s=[10e-6,10.02e-6],startup_zero_window_s=[8e-6,9e-6],startup_step_window_s=[14e-6,15e-6],nominal_scope_excludes=['PVT max/min gain ratio','other26 corners','statistical mismatch']))
    return c

def bench(c,start=False):
    b=prefix(c)
    if start:
        b+='''VDD (vdd 0) vsource type=pwl wave=[0 0 .1u 0 1.1u 1.8 20u 1.8]
IREF (vdd iref) isource type=pwl wave=[0 0 1.2u 0 1.22u 50u 20u 50u]
VCM (cma 0) vsource type=pwl wave=[0 0 .1u 0 1.1u .95 20u .95]
VD (vd 0) vsource type=pwl wave=[0 0 10u 0 10.02u .02 20u .02]
'''
    else:b+='''parameters vdtest=0
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=50u
VCM (cma 0) vsource dc=.95
VD (vd 0) vsource dc=vdtest mag=1
'''
    b+='''EINP (vinp cma vd 0) vcvs gain=.5
EINN (vinn cma vd 0) vcvs gain=-.5
X (0 iref vdd vinp vinn voutp voutn) cgm_amp
CLP (voutp 0) capacitor c=500f
CLN (voutn 0) capacitor c=500f
save vdd iref cma vd vinp vinn voutp voutn VDD:p X.nb X.nc X.rb2 X.tail
'''
    if start:
        b+='ic vdd=0 iref=0 cma=0 vd=0 vinp=0 vinn=0 voutp=0 voutn=0 X.nb=0 X.nc=0 X.rb2=0 X.tail=0\ntran tran stop=20u maxstep=2n strobeperiod=2n strobeoutput=strobeonly skipdc=yes errpreset=conservative\n'
    else:
        for dev in DEVS:b+='save '+' '.join(f'X.{dev}:{x}' for x in ['ids','gm','gmbs','gds','vgs','vds','vdsat','region'])+'\n'
        b+='dcOp dc\nac ac start=10k stop=2G dec=100\nlinearity dc param=vdtest start=-.06 stop=.06 step=.002\n'
    return b

def window_mean(t,y,lo,hi):
    keep=(t>lo)&(t<hi);tt=np.r_[lo,t[keep],hi];yy=np.r_[np.interp(lo,t,y),y[keep],np.interp(hi,t,y)]
    return float(np.trapz(yy,tt)/(hi-lo))

def extract(runs):
    o=dc(runs[0]);a=data(runs[0],'ac.ac');l=data(runs[0],'linearity.dc');d=data(runs[1],'tran.tran')
    f=a['freq'];gain=abs(a['voutp']-a['voutn']);g1=float(at(f,gain,1e6));target=g1/np.sqrt(2);ix=np.flatnonzero((gain[:-1]>target)&(gain[1:]<=target))
    if not len(ix):raise RuntimeError('No -3dB crossing in full AC sweep')
    i=ix[0];bw=float(10**(np.log10(f[i])+(target-gain[i])/(gain[i+1]-gain[i])*np.log10(f[i+1]/f[i])))
    x=l['vdtest'];y=l['voutp']-l['voutn'];assert len(x)==61 and np.allclose(x,np.linspace(-.06,.06,61))
    gc=float((np.interp(.002,x,y)-np.interp(-.002,x,y))/.004);gains=[float((np.interp(v,x,y)-np.interp(0,x,y))/v) for v in [-.06,-.03,.03,.06]]
    t=d['time'];diff=d['voutp']-d['voutn'];cm=(d['voutp']+d['voutn'])/2
    st=dict(zero_imbalance_V=abs(window_mean(t,diff,8e-6,9e-6)),step_gain=window_mean(t,diff,14e-6,15e-6)/.02,zero_load_drop_V=1.8-window_mean(t,cm,8e-6,9e-6),step_load_drop_V=1.8-window_mean(t,cm,14e-6,15e-6),initial_max_node_V=float(max(abs(d[k][0]) for k in ['vdd','iref','cma','vd','vinp','vinn','voutp','voutn','X.nb','X.nc','X.rb2','X.tail'])))
    v=dict(gain_1mhz=g1,bandwidth_Hz=bw,gain_1ghz=float(at(f,gain,1e9)),load_drop_V=1.8-(o['voutp']+o['voutn'])/2,imbalance_V=abs(o['voutp']-o['voutn']),power_W=-1.8*o['VDD:p'],central_gain=gc,linearity_error=max(abs(g/gc-1) for g in gains),linearity_gains=gains,startup=st)
    gates=dict(gain_window=gate(abs(g1-3.5),.5,'max','V/V'),bandwidth=gate(bw,30e6,'min','Hz'),load_drop_window=gate(abs(v['load_drop_V']-.275),.125,'max','V'),imbalance=gate(v['imbalance_V'],.01,'max','V'),power=gate(v['power_W'],500e-6,'max','W'),linearity=gate(v['linearity_error'],.08,'max','fraction'),startup_imbalance=gate(st['zero_imbalance_V'],.01,'max','V'),startup_gain_window=gate(abs(st['step_gain']-3.5),.5,'max','V/V'),startup_zero_drop_window=gate(abs(st['zero_load_drop_V']-.275),.125,'max','V'),startup_step_drop_window=gate(abs(st['step_load_drop_V']-.275),.125,'max','V'))
    op={}
    for dev in DEVS:
        q={k.split(':')[1]:z for k,z in o.items() if k.startswith('X.'+dev+':')};q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[dev]=q
    valid=st['initial_max_node_V']<1e-12 and v['power_W']>=0 and all(q['headroom_V']>0 for q in op.values())
    tiers={tier:bool(valid and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']};tier=next((q for q in tiers if tiers[q]),None)
    r=dict(case_slot=13,generated_at=now(),run_dirs=[str(x.relative_to(ROOT)) for x in runs],status='complete_'+tier if tier else 'partial',values=v,gates=gates,operating_point=op,dc_nodes={k:z for k,z in o.items() if ':' not in k},all_nominal_checks_complete=True,pass_tiers=tiers,model_dimensions_valid=True,scope='Nominal AC/DC/linearity and explicit zero-state cold startup. PVT max/min gain ratio intentionally not claimed from one point.')
    write_json(runs[0]/'measurements.json',r);write_json(CASE/'latest_results.json',r);update_case(13,status=r['status'],nominal_complete=bool(tier),latest_runs=r['run_dirs'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--rb',type=float,default=1450);p.add_argument('--rl',type=float,default=5600);p.add_argument('--gmid',type=float,default=14);p.add_argument('--current',type=float,default=45);p.add_argument('--extract',nargs=2);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        c=design(a.rb,a.rl,a.gmid,a.current);update_case(13,status='running',nominal_complete=False);runs=[]
        for label,start in [('static',False),('startup',True)]:
            b=bench(c,start);(CASE/f'testbench_{label}.scs').write_text(b);runs.append(run_spectre(13,label,b,[c,CASE/'sizing.json',CASE/'contract.json']))
    r=extract(runs);print(json.dumps({k:r[k] for k in ['status','values','operating_point']},indent=2))
if __name__=='__main__':main()
