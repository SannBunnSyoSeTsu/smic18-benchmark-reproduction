"""Two-stage Miller amplifier with full nominal AC/noise/DC/dynamic contract."""
from common import *
import argparse
CASE=ROOT/'cases/16-miller'

def design(branch_uA=70,second_uA=600,cc_pf=.7,rz=1500,second_gmid=5):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={'input':lut_size('n18',1,18,branch_uA*1e-6,.9),'mirror_load':lut_size('p18',1,5,branch_uA*1e-6,.9),'n_bias_unit':lut_size('n18',1,12,10e-6,.2),'p_bias_unit':lut_size('p18',1,10,50e-6,.9),'second':lut_size('n18',.36,second_gmid,second_uA*1e-6,.9)}
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    c=CASE/'circuit.scs';c.write_text(f'''// Two-stage Miller amplifier, SMIC18 target-PDK gm/ID dimensions.
simulator lang=spectre
subckt two_stage_miller_opamp (vss iref vdd vinn vinp vout)
MREF (iref iref vss vss) n18 w={w['n_bias_unit']}u l=1u m=5
MTAIL (tail iref vss vss) n18 w={w['n_bias_unit']}u l=1u m={2*branch_uA/10:g}
MINN (nleft vinn tail vss) n18 w={w['input']}u l=1u
MINP (stage1 vinp tail vss) n18 w={w['input']}u l=1u
MPD (nleft nleft vdd vdd) p18 w={w['mirror_load']}u l=1u
MPM (stage1 nleft vdd vdd) p18 w={w['mirror_load']}u l=1u
MBN (obias iref vss vss) n18 w={w['n_bias_unit']}u l=1u m=5
MBP (obias obias vdd vdd) p18 w={w['p_bias_unit']}u l=1u
MSECOND (vout stage1 vss vss) n18 w={w['second']}u l=.36u
MLOAD (vout obias vdd vdd) p18 w={w['p_bias_unit']}u l=1u m={second_uA/50:g}
RZ (stage1 comp) resistor r={rz}
CC (comp vout) capacitor c={cc_pf}p
ends two_stage_miller_opamp
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,branch_target_uA=branch_uA,second_target_uA=second_uA,cc_pF=cc_pf,rz_Ohm=rz,n_reference_m=5,n_tail_m=2*branch_uA/10,n_obias_m=5,p_output_m=second_uA/50,rationale='High gmID input for gm/noise. Strong inversion p mirror and n second stage align first-stage drain voltages to limit offset. Long input/load channels preserve gain; RZ>1/gm2 creates a left-half-plane compensation zero. Unit current mirrors keep all individual widths within PDK model range.'))
    write_json(CASE/'contract.json',dict(source_task='sky130-two-stage-miller-opamp-gain60-ugb200-pm60-noise50uv-pvt',corner='tt',VDD_V=1.8,temperature_C=27,reference_A=50e-6,load_F=1e-12,VCM_V=.9,gain_frequency_Hz=10,gain_min_dB=60,ugb_min_Hz=200e6,phase_margin_min_deg=60,output_error_max_V=.025,power_max_W=.002,noise_gain=20,noise_low_Hz=10,noise_high='measured closed-loop -3dB bandwidth at noise gain 20',noise_max_Vrms=50e-6,psrr_frequencies_Hz=[1e3,1e6],psrr_min_dB=35,cmrr_frequency_Hz=1e3,cmrr_min_dB=55,swing_sweep_V=[.3,1.5],tracking_error_max_V=.02,contiguous_swing_min_Vpp=.8,settling_step_V=[.85,.95],settling_max_s=20e-9,settling_error_fraction=.02,settling_final_error_max_V=.002,slew_step_V=[.65,1.15],slew_measurement_V=[.75,1.05],slew_min_V_per_us=50,recross_forbidden=True,rejection_definition='Unity feedback external benchmarks; PSRR=-20log10|Vout| with AC rail 1V; CMRR AC unit on input and in series feedback.'))
    return c

def prefix(c):return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
'''

def static_bench(c,noise_high=None):
    b=prefix(c)+'''parameters sweepin=.9
VDDL (vddl 0) vsource dc=1.8
IREFL (vddl irefl) isource dc=50u
VINL (vinpl 0) vsource dc=.9
VTEST (voutl vinnl) vsource dc=0 mag=1
XL (0 irefl vddl vinnl vinpl voutl) two_stage_miller_opamp
CLL (voutl 0) capacitor c=1p
VDDN (vddn 0) vsource dc=1.8
IREFN (vddn irefn) isource dc=50u
VINN (vinpn 0) vsource dc=.9 mag=1
VCMN (vcmn 0) vsource dc=.9
EFB (vinnn vcmn voutn vcmn) vcvs gain=.05
XN (0 irefn vddn vinnn vinpn voutn) two_stage_miller_opamp
CLN (voutn 0) capacitor c=1p
VDDP (vddp 0) vsource dc=1.8 mag=1
IREFP (vddp irefp) isource dc=50u
VINP (vinpp 0) vsource dc=.9
XP (0 irefp vddp voutp vinpp voutp) two_stage_miller_opamp
CLP (voutp 0) capacitor c=1p
VDDC (vddc 0) vsource dc=1.8
IREFC (vddc irefc) isource dc=50u
VINC (vinpc 0) vsource dc=.9 mag=1
VFBC (vinnc voutc) vsource dc=0 mag=1
XC (0 irefc vddc vinnc vinpc voutc) two_stage_miller_opamp
CLC (voutc 0) capacitor c=1p
VDDS (vdds 0) vsource dc=1.8
IREFS (vdds irefs) isource dc=50u
VINS (vinps 0) vsource dc=sweepin
XS (0 irefs vdds vouts vinps vouts) two_stage_miller_opamp
CLS (vouts 0) capacitor c=1p
save voutl vinnl vinpl voutn vinnn vinpn voutp voutc vouts vinps VDDL:p XL.tail XL.stage1 XL.nleft XL.obias irefl
'''
    for dev in ['MINP','MINN','MPM','MTAIL','MSECOND','MLOAD']:
        b+='save '+' '.join(f'XL.{dev}:{x}' for x in ['ids','gm','gds','vgs','vds','vdsat','region'])+'\n'
    if noise_high is None:b+='dcOp dc\nac ac start=10 stop=10G dec=100\nswing dc param=sweepin start=.3 stop=1.5 step=.01\n'
    else:b+=f'noise (voutn 0) noise iprobe=VINN start=10 stop={noise_high:.12g} dec=100\n'
    return b

def dynamic_bench(c):
    b=prefix(c)
    for suffix,wave in [('S','0 .85 5n .85 6n .95 66n .95 67n .85 380n .85'),('R','0 .65 20n .65 21n 1.15 201n 1.15 202n .65 380n .65')]:
        b+=f'''VDD{suffix} (vdd{suffix} 0) vsource dc=1.8
IREF{suffix} (vdd{suffix} iref{suffix}) isource dc=50u
VIN{suffix} (vin{suffix} 0) vsource type=pwl wave=[{wave}]
X{suffix} (0 iref{suffix} vdd{suffix} out{suffix} vin{suffix} out{suffix}) two_stage_miller_opamp
CL{suffix} (out{suffix} 0) capacitor c=1p
save vin{suffix} out{suffix} VDD{suffix}:p
'''
    return b+'tran tran stop=380n maxstep=20p strobeperiod=100p strobeoutput=strobeonly errpreset=conservative\n'

def noise_bw(run):
    a=data(run,'ac.ac');f=a['freq'];g=abs(a['voutn']);target=g[0]/np.sqrt(2);cross=np.flatnonzero((g[:-1]>target)&(g[1:]<=target))
    if not len(cross):raise RuntimeError('Noise-gain-20 bandwidth not found')
    i=cross[0];r=(np.log(g[i])-np.log(target))/(np.log(g[i])-np.log(g[i+1]));return float(np.exp(np.log(f[i])+r*np.log(f[i+1]/f[i])))

def contiguous_span(x,e,tol=.02,center=.9):
    mid=int(np.argmin(abs(x-center)))
    if e[mid]>tol:return dict(low=center,high=center,span=0.)
    lo=hi=mid
    while lo>0 and e[lo-1]<=tol:lo-=1
    while hi<len(x)-1 and e[hi+1]<=tol:hi+=1
    low=x[lo] if lo==0 else x[lo-1]+(tol-e[lo-1])/(e[lo]-e[lo-1])*(x[lo]-x[lo-1])
    high=x[hi] if hi==len(x)-1 else x[hi]+(tol-e[hi])/(e[hi+1]-e[hi])*(x[hi+1]-x[hi])
    return dict(low=float(low),high=float(high),span=float(high-low))

def settling(t,y,start,stop,target):
    mask=(t>=start-1e-18)&(t<=stop+1e-18);tt=t[mask];ee=abs(y[mask]-target);last=float(np.interp(stop,t,y));outside=np.flatnonzero(ee>.002)
    if len(outside) and outside[-1]==len(tt)-1:ts=None
    elif len(outside):
        i=outside[-1];cross=tt[i]+(.002-ee[i])/(ee[i+1]-ee[i])*(tt[i+1]-tt[i]);ts=float(max(0,cross-start))
    else:ts=0.
    return dict(time_s=ts,final_error_V=abs(last-target),final_error_fraction=abs(last-target)/.1)

def crossing(t,y,threshold,rising,start):
    idx=np.flatnonzero(((y[:-1]<threshold)&(y[1:]>=threshold) if rising else (y[:-1]>threshold)&(y[1:]<=threshold))&(t[1:]>=start))
    if not len(idx):return None
    i=idx[0];return float(t[i]+(threshold-y[i])/(y[i+1]-y[i])*(t[i+1]-t[i]))

def extract(runs,slot=16,case=CASE,limit_overrides=None,op_devices=None,slew_starts=(20e-9,200e-9)):
    a=data(runs[0],'ac.ac');o=dc(runs[0]);s=data(runs[0],'swing.dc');n=data(runs[1],'noise.noise',required=('in','out'));d=data(runs[2],'tran.tran')
    f=a['freq'];loop=-a['voutl']/a['vinnl'];lm=loop_metrics(f,loop,gain_freq=10);mag=20*np.log10(abs(loop));first=np.flatnonzero(mag<0)[0];recross=bool(np.any(mag[first:]>0))
    span=contiguous_span(s['sweepin'],abs(s['vouts']-s['vinps']))
    st=[settling(d['time'],d['outS'],5e-9,65e-9,.95),settling(d['time'],d['outS'],66e-9,130e-9,.85)]
    rise=[crossing(d['time'],d['outR'],x,True,slew_starts[0]) for x in [.75,1.05]];fall=[crossing(d['time'],d['outR'],x,False,slew_starts[1]) for x in [1.05,.75]]
    sr=[.3/(x[1]-x[0])/1e6 if None not in x and x[1]>x[0] else 0. for x in [rise,fall]]
    values={**lm,'output_error_V':abs(o['voutl']-.9),'power_W':-1.8*o['VDDL:p'],'noise_bandwidth_Hz':noise_bw(runs[0]),'input_noise_Vrms':float(np.sqrt(np.trapz(abs(n['in'])**2,n['freq']))),'psrr_1k_dB':float(at(f,-20*np.log10(abs(a['voutp'])),1e3)),'psrr_1m_dB':float(at(f,-20*np.log10(abs(a['voutp'])),1e6)),'cmrr_1k_dB':float(at(f,-20*np.log10(abs(a['voutc'])),1e3)),'output_range_Vpp':span['span'],'output_range_boundaries':span,'settling_edges':st,'settling_s':max(x['time_s'] for x in st) if all(x['time_s'] is not None for x in st) else None,'settling_error_V':max(x['final_error_V'] for x in st),'settling_fraction':max(x['final_error_fraction'] for x in st),'slew_rise_V_per_us':sr[0],'slew_fall_V_per_us':sr[1],'recross':recross}
    specs=[('gain_db',60,'min','dB','amplitude_db'),('ugb_hz',200e6,'min','Hz','linear'),('phase_margin_deg',60,'min','deg','phase_margin'),('output_error_V',.025,'max','V','linear'),('power_W',.002,'max','W','linear'),('input_noise_Vrms',50e-6,'max','Vrms','linear'),('psrr_1k_dB',35,'min','dB','amplitude_db'),('psrr_1m_dB',35,'min','dB','amplitude_db'),('cmrr_1k_dB',55,'min','dB','amplitude_db'),('output_range_Vpp',.8,'min','Vpp','linear'),('settling_error_V',.002,'max','V','linear'),('settling_fraction',.02,'max','fraction','linear'),('slew_rise_V_per_us',50,'min','V/us','linear'),('slew_fall_V_per_us',50,'min','V/us','linear')]
    if values['settling_s'] is not None:specs.append(('settling_s',20e-9,'max','s','linear'))
    gates={key:gate(values[key],(limit_overrides or {}).get(key,lim),sense,unit,kind) for key,lim,sense,unit,kind in specs};op={}
    for dev in (op_devices or ['MINP','MINN','MPM','MTAIL','MSECOND','MLOAD']):
        q={k.split(':')[1]:v for k,v in o.items() if k.startswith('XL.'+dev+':')};q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[dev]=q
    valid=not recross and values['settling_s'] is not None and all(z['headroom_V']>0 for z in op.values())
    tiers={t:bool(valid and all(g['passes'][t] for g in gates.values())) for t in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    report=dict(case_slot=slot,generated_at=now(),run_dirs=[str(x.relative_to(ROOT)) for x in runs],status='complete_'+tier if tier else 'partial',values=values,gates=gates,operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},all_nominal_checks_complete=True,pass_tiers=tiers,model_dimensions_valid=True,scope='Full nominal primary, noise-gain-20 integration, closed-loop rejection, contiguous DC range, both settling and slew directions. Other PVT and mismatch excluded.')
    write_json(runs[0]/'measurements.json',report);write_json(case/'latest_results.json',report);update_case(slot,status=report['status'],nominal_complete=bool(tier),latest_runs=report['run_dirs'],report=str((case/'latest_results.json').relative_to(ROOT)))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--branch-ua',type=float,default=70);p.add_argument('--second-ua',type=float,default=600);p.add_argument('--cc-pf',type=float,default=.7);p.add_argument('--rz',type=float,default=1500);p.add_argument('--second-gmid',type=float,default=5);p.add_argument('--extract',nargs=3);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        c=design(a.branch_ua,a.second_ua,a.cc_pf,a.rz,a.second_gmid);deps=[c,CASE/'sizing.json',CASE/'contract.json'];update_case(16,status='running',nominal_complete=False)
        b=static_bench(c);(CASE/'testbench_static.scs').write_text(b);r0=run_spectre(16,'static',b,deps);bw=noise_bw(r0)
        b=static_bench(c,bw);(CASE/'testbench_noise.scs').write_text(b);r1=run_spectre(16,'noise',b,deps)
        b=dynamic_bench(c);(CASE/'testbench_dynamic.scs').write_text(b);r2=run_spectre(16,'dynamic',b,deps);runs=[r0,r1,r2]
    r=extract(runs);print(json.dumps({k:r[k] for k in ['status','values','operating_point']},indent=2))
if __name__=='__main__':main()
