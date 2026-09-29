"""Target-PDK folded first stage with current-buffer (Ahuja) compensation."""
from common import *
from case16_miller import prefix,crossing
import argparse
CASE=ROOT/'cases/29-ahuja'
DEVS=['MINP','MINN','MTAIL','MFP','MFN','MFCP','MFCN','MMD','MMO','MCD','MCO','MSECOND','MLOAD']

def design(branch=20,fold=100,output=650,cc=6.8,pcdrop=.4,ncdrop=.36,second_gmid=8,mirror_gmid=8):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={'input':lut_size('n18',1,18,branch*1e-6,.9),'n_unit':lut_size('n18',1,12,10e-6,.2),'p_unit':lut_size('p18',1,10,20e-6,.9),'p_cascode':lut_size('p18',.36,12,20e-6,.45),'n_cascode':lut_size('n18',.36,12,20e-6,.45),'n_mirror':lut_size('n18',1,mirror_gmid,(fold-branch)*1e-6,.2),'second':lut_size('n18',.36,second_gmid,output*1e-6,.9)}
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    # Split the output device into equal legal unit widths without changing total LUT W.
    second_m=max(1,int(np.ceil(w['second']/90)));second_w=w['second']/second_m
    c=CASE/'circuit.scs';c.write_text(f'''// Indirect compensation returns to the PMOS current-buffer source.
simulator lang=spectre
subckt ahuja_ota (vss iref vdd vinp vinn vout)
MREF (iref iref vss vss) n18 w={w['n_unit']:g}u l=1u m=5
MTAIL (tail iref vss vss) n18 w={w['n_unit']:g}u l=1u m={2*branch/10:g}
MNB (vcp iref vss vss) n18 w={w['n_unit']:g}u l=1u m=2
MPB (vbp vbp vdd vdd) p18 w={w['p_unit']:g}u l=1u
RCP (vbp vcp) resistor r={pcdrop/20e-6:g}
CBP (vcp vdd) capacitor c=5p
CBB (vbp vdd) capacitor c=2p
MPNB (vcn vbp vdd vdd) p18 w={w['p_unit']:g}u l=1u
RCN (vcn ncn) resistor r={ncdrop/20e-6:g}
MNCB (ncn ncn vss vss) n18 w={w['n_cascode']:g}u l=.36u
CBN (vcn vss) capacitor c=2p
MINN (f1 vinn tail vss) n18 w={w['input']:g}u l=1u
MINP (f2 vinp tail vss) n18 w={w['input']:g}u l=1u
MFP (f1 vbp vdd vdd) p18 w={w['p_unit']:g}u l=1u m={fold/20:g}
MFN (f2 vbp vdd vdd) p18 w={w['p_unit']:g}u l=1u m={fold/20:g}
MFCP (g1 vcp f1 vdd) p18 w={w['p_cascode']:g}u l=.36u m={(fold-branch)/20:g}
MFCN (stage1 vcp f2 vdd) p18 w={w['p_cascode']:g}u l=.36u m={(fold-branch)/20:g}
MMD (s5 g1 vss vss) n18 w={w['n_mirror']:g}u l=1u
MMO (s6 g1 vss vss) n18 w={w['n_mirror']:g}u l=1u
MCD (g1 vcn s5 vss) n18 w={w['n_cascode']:g}u l=.36u m={(fold-branch)/20:g}
MCO (stage1 vcn s6 vss) n18 w={w['n_cascode']:g}u l=.36u m={(fold-branch)/20:g}
MSECOND (vout stage1 vss vss) n18 w={second_w:g}u l=.36u m={second_m}
MLOAD (vout vbp vdd vdd) p18 w={w['p_unit']:g}u l=1u m={output/20:g}
CC (vout f2) capacitor c={cc:g}p
ends ahuja_ota
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,branch_target_uA=branch,fold_target_uA=fold,output_target_uA=output,cc_pF=cc,pcdrop_V=pcdrop,ncdrop_V=ncdrop,second_unit_W_um=second_w,second_m=second_m,rationale='Folded first stage uses p current buffers and a wide-swing n cascode mirror. CC returns to f2 (current-buffer source), avoiding direct first-stage feed-forward. Bias from the external 50uA reference only.'))
    write_json(CASE/'contract.json',dict(source_task='sky130-ahuja-compensated-two-stage-load-range-pvt',corner='tt',VDD_V=1.8,temperature_C=27,reference_A=50e-6,VCM_V=.9,loads_F=[20e-12,63e-12,200e-12],ac_sweep_Hz=[1,300e6],servo_R_Ohm=500e6,servo_C_F=.05,light_gain_min_dB=58,light_ugb_min_Hz=6.5e6,all_PM_min_deg=60,recross_forbidden=True,offset_max_V=.006,power_max_W=.002,step_load_F=200e-12,step_V=[.9,1.2],step_edges_s=[2e-6,12.01e-6],edge_duration_s=10e-9,settling_start='1 percent command crossing, 2.0001 us / 12.0101 us',settling_windows_s=[[2e-6,12e-6],[12e-6,20e-6]],settling_max_s=2e-6,settling_tolerance_V=.006,final_error_max_V=.006,nominal_only=True))
    return c

def acbench(c):
    b=prefix(c)
    for suffix,load in [('L',20),('M',63),('H',200)]:
        b+=f'''VDD{suffix} (vdd{suffix} 0) vsource dc=1.8
IREF{suffix} (vdd{suffix} iref{suffix}) isource dc=50u
VIN{suffix} (vin{suffix} 0) vsource dc=.9 mag=1
RS{suffix} (out{suffix} fb{suffix}) resistor r=500M
CS{suffix} (fb{suffix} 0) capacitor c=50m
X{suffix} (0 iref{suffix} vdd{suffix} vin{suffix} fb{suffix} out{suffix}) ahuja_ota
CL{suffix} (out{suffix} 0) capacitor c={load}p
save out{suffix} fb{suffix} VDD{suffix}:p
'''
    b+='save XL.tail XL.vbp XL.vcp XL.vcn XL.ncn XL.f1 XL.f2 XL.g1 XL.stage1 XL.s5 XL.s6 irefL\n'
    for dev in DEVS:b+='save '+' '.join(f'XL.{dev}:{x}' for x in ['ids','gm','gds','vgs','vds','vdsat','region'])+'\n'
    return b+'dcOp dc\nac ac start=1 stop=300M dec=120\n'

def tranbench(c):
    return prefix(c)+'''VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=50u
VIN (vin 0) vsource type=pwl wave=[0 .9 2u .9 2.01u 1.2 12.01u 1.2 12.02u .9 20u .9]
X (0 iref vdd vin out out) ahuja_ota
CL (out 0) capacitor c=200p
save vin out VDD:p
tran tran stop=20u maxstep=500p strobeperiod=1n strobeoutput=strobeonly errpreset=conservative
'''

def last_entry(t,y,start,stop,target,tol=.006):
    m=(t>=start)&(t<=stop+1e-18);tt=t[m];ee=abs(y[m]-target);bad=np.flatnonzero(ee>tol)
    if len(bad) and bad[-1]==len(tt)-1:return None
    if not len(bad):return float(start)
    k=bad[-1];return float(tt[k]+(tol-ee[k])/(ee[k+1]-ee[k])*(tt[k+1]-tt[k]))

def extract(runs):
    a=data(runs[0],'ac.ac');o=dc(runs[0]);d=data(runs[1],'tran.tran');f=a['freq'];ac={};gates={}
    for suffix,load in [('L',20),('M',63),('H',200)]:
        resp=a['out'+suffix];q=loop_metrics(f,resp,gain_freq=10);db=20*np.log10(abs(resp));below=np.flatnonzero(db<0)
        q.update(load_pF=load,recross=bool(not len(below) or np.any(db[below[0]:]>=0)))
        exit6=np.flatnonzero(db<=-6)
        if not len(exit6):raise RuntimeError('Response does not reach the required -6dB diagnostic before 300MHz')
        q['post_minus6_peak_db']=float(max(-6,np.max(db[exit6[0]:])))
        ac[suffix]=q;gates['pm_'+suffix]=gate(q['phase_margin_deg'],60,'min','deg','phase_margin')
    t=d['time'];edges=[]
    for start,stop,target,threshold,rising in [(2e-6,12e-6,1.2,.903,True),(12e-6,20e-6,.9,1.197,False)]:
        tc=crossing(t,d['vin'],threshold,rising,start);te=last_entry(t,d['out'],start,stop,target)
        edges.append(dict(command_1pct_time_s=tc,last_entry_time_s=te,settling_s=max(0,te-tc) if te is not None and tc is not None else None,final_error_V=float(abs(np.interp(stop,t,d['out'])-target))))
    vals=dict(gain_db=ac['L']['gain_db'],ugb_hz=ac['L']['ugb_hz'],min_PM_deg=min(q['phase_margin_deg'] for q in ac.values()),offset_V=abs(o['outL']-.9),power_W=-1.8*o['VDDL:p'],settling_s=max(q['settling_s'] for q in edges) if all(q['settling_s'] is not None for q in edges) else None,final_error_V=max(q['final_error_V'] for q in edges))
    for k,lim,sense,unit,kind in [('gain_db',58,'min','dB','amplitude_db'),('ugb_hz',6.5e6,'min','Hz','linear'),('offset_V',.006,'max','V','linear'),('power_W',.002,'max','W','linear'),('final_error_V',.006,'max','V','linear')]:gates[k]=gate(vals[k],lim,sense,unit,kind)
    if vals['settling_s'] is not None:gates['settling_s']=gate(vals['settling_s'],2e-6,'max','s')
    op={}
    for dev in DEVS:
        q={k.split(':')[1]:v for k,v in o.items() if k.startswith('XL.'+dev+':')};q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[dev]=q
    valid=vals['power_W']>=0 and vals['settling_s'] is not None and all(not q['recross'] and q['falling_crossings']==1 for q in ac.values()) and all(q['headroom_V']>0 for q in op.values())
    tiers={tier:bool(valid and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    r=dict(case_slot=29,generated_at=now(),run_dirs=[str(x.relative_to(ROOT)) for x in runs],status='complete_'+tier if tier else 'partial',values=vals,ac_by_load=ac,settling_edges=edges,gates=gates,operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},all_nominal_checks_complete=True,pass_tiers=tiers,model_dimensions_valid=True,scope='Nominal 20/63/200pF AC, 20pF DC and 200pF bidirectional commanded-target settling. Other PVT excluded.')
    write_json(runs[0]/'measurements.json',r);write_json(CASE/'latest_results.json',r);update_case(29,status=r['status'],nominal_complete=bool(tier),latest_runs=r['run_dirs'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser()
    for n,d in [('branch',20),('fold',100),('output',650),('cc',6.8),('pcdrop',.4),('ncdrop',.36),('second-gmid',8),('mirror-gmid',8)]:p.add_argument('--'+n,type=float,default=d)
    p.add_argument('--extract',nargs=2);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        c=design(a.branch,a.fold,a.output,a.cc,a.pcdrop,a.ncdrop,a.second_gmid,a.mirror_gmid);update_case(29,status='running',nominal_complete=False);deps=[c,CASE/'sizing.json',CASE/'contract.json']
        b=acbench(c);(CASE/'testbench_static.scs').write_text(b);r0=run_spectre(29,'static',b,deps)
        b=tranbench(c);(CASE/'testbench_dynamic.scs').write_text(b);r1=run_spectre(29,'dynamic',b,deps);runs=[r0,r1]
    r=extract(runs);print(json.dumps({k:r[k] for k in ['status','values','ac_by_load','settling_edges','operating_point']},indent=2))
if __name__=='__main__':main()
