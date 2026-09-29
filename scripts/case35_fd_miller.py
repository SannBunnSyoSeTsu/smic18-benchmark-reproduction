"""Nominal SMIC18 fully differential folded-input two-stage Miller op amp."""
from common import *
import argparse
import importlib.util

CASE=ROOT/'cases/35-fd-miller'
TASK=SOURCE/'sky130-fd-two-stage-miller-opamp-gain60-pm60-noise50uv-pvt'
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region']

def design(branch=100,fold=150,output=700,cc=2,rz=400,cm_branch=50,cm_ratio=2,ncdrop=.28,pcdrop=.4,cm_gmid=14):
    CASE.mkdir(parents=True,exist_ok=True)
    sources={}
    for name in ['instruction.md','solution/circuit.spi','tests/verify.py','tests/utils.py']+['tests/benches/'+x for x in ['tb_op_ac.spi','tb_noise.spi','tb_swing.spi','tb_settling.spi','tb_cm_recovery.spi','tb_mc.spi']]:
        src=TASK/name;dest=CASE/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(src.read_bytes())
        assert sha(src)==sha(dest);sources[name]=dict(path=str(src),sha256=sha(src),frozen=str(dest.relative_to(ROOT)))
    roles={'input':lut_size('n18',1,18,10e-6,.9),'n_bias':lut_size('n18',1,14,10e-6,.2),'p_bias':lut_size('p18',1,10,10e-6,.45),
       'n_cascode':lut_size('n18',.36,14,10e-6,.45),'p_cascode':lut_size('p18',.36,14,10e-6,.45),
       'second':lut_size('n18',.36,6,10e-6,.9),'output_load':lut_size('p18',.36,8,10e-6,.9),'cm_input':lut_size('n18',.36,cm_gmid,10e-6,.45)}
    w={k:q['rounded_W_um'] for k,q in roles.items()};fi=(fold-branch)/10
    c=CASE/'circuit.scs';c.write_text(f'''// Fully differential folded-cascode first stage and symmetric second stage.
// D G S B. Legal unit widths use m replication; no internal sources.
simulator lang=spectre
subckt fd_two_stage_miller_opamp (vss iref vdd vinn vinp vocm voutn voutp)
MREF (iref iref vss vss) n18 w={w['n_bias']:g}u l=1u m=5
MBN (vbp iref vss vss) n18 w={w['n_bias']:g}u l=1u
MBP (vbp vbp vdd vdd) p18 w={w['p_bias']:g}u l=1u
MOBN (vbpout iref vss vss) n18 w={w['n_bias']:g}u l=1u
MOBP (vbpout vbpout vdd vdd) p18 w={w['output_load']:g}u l=.36u
MNCB (vcn vbp vdd vdd) p18 w={w['p_bias']:g}u l=1u
MDN (vcn vcn ncb vss) n18 w={w['n_cascode']:g}u l=.36u
RNB (ncb vss) resistor r={ncdrop/10e-6:g}
RPC (vdd pcb) resistor r={pcdrop/10e-6:g}
MDP (vpc vpc pcb pcb) p18 w={w['p_cascode']:g}u l=.36u
MPCB (vpc iref vss vss) n18 w={w['n_bias']:g}u l=1u
MTAIL (tail iref vss vss) n18 w={w['n_bias']:g}u l=1u m={2*branch/10:g}
MINP (fp vinp tail vss) n18 w={w['input']:g}u l=1u m={branch/10:g}
MINN (fn vinn tail vss) n18 w={w['input']:g}u l=1u m={branch/10:g}
MSP (fp vbp vdd vdd) p18 w={w['p_bias']:g}u l=1u m={fold/10:g}
MSN (fn vbp vdd vdd) p18 w={w['p_bias']:g}u l=1u m={fold/10:g}
MPCP (stagep vpc fp fp) p18 w={w['p_cascode']:g}u l=.36u m={fi:g}
MPCN (stagen vpc fn fn) p18 w={w['p_cascode']:g}u l=.36u m={fi:g}
MNCP (stagep vcn sinkp vss) n18 w={w['n_cascode']:g}u l=.36u m={fi:g}
MNCN (stagen vcn sinkn vss) n18 w={w['n_cascode']:g}u l=.36u m={fi:g}
MSINKP (sinkp vcmfb vss vss) n18 w={w['n_bias']:g}u l=1u m={fi:g}
MSINKN (sinkn vcmfb vss vss) n18 w={w['n_bias']:g}u l=1u m={fi:g}
MSECONDP (voutp stagep vss vss) n18 w={w['second']:g}u l=.36u m={output/10:g}
MSECONDN (voutn stagen vss vss) n18 w={w['second']:g}u l=.36u m={output/10:g}
MLOADP (voutp vbpout vdd vdd) p18 w={w['output_load']:g}u l=.36u m={output/10:g}
MLOADN (voutn vbpout vdd vdd) p18 w={w['output_load']:g}u l=.36u m={output/10:g}
RZP (stagep zp) resistor r={rz:g}
CCP (zp voutp) capacitor c={cc:g}p
RZN (stagen zn) resistor r={rz:g}
CCN (zn voutn) capacitor c={cc:g}p
RCMP (voutp vcms) resistor r=100k
RCMN (voutn vcms) resistor r=100k
CCMP (voutp vcms) capacitor c=100f
CCMN (voutn vcms) capacitor c=100f
MCMT (cmt iref vss vss) n18 w={w['n_bias']:g}u l=1u m={2*cm_branch/10:g}
MCMREF (cma vocm cmt vss) n18 w={w['cm_input']:g}u l=.36u m={cm_branch/10:g}
MCMSENSE (vcmfb vcms cmt vss) n18 w={w['cm_input']:g}u l=.36u m={cm_branch/10:g}
MCMD (cma cma vdd vdd) p18 w={w['p_bias']:g}u l=1u m={cm_branch/10:g}
MCMM (vcmfb cma vdd vdd) p18 w={w['p_bias']:g}u l=1u m={cm_branch*cm_ratio/10:g}
MCMND (vcmfb vcmfb vss vss) n18 w={w['n_bias']:g}u l=1u m={cm_branch*(cm_ratio-1)/10:g}
ends fd_two_stage_miller_opamp
''')
    geom=[]
    for line in c.read_text().splitlines():
        m=re.match(r'(M\w+) \((.*?)\) (n18|p18) w=([.\d]+)u l=([.\d]+)u(?: m=([.\d]+))?',line)
        if m:
            name,pins,model,ww,ll,mult=m.groups();ww=float(ww);mult=float(mult or 1)
            geom.append(dict(name=name,pins=pins.split(),model=model,W_unit_um=ww,L_um=float(ll),m=mult,W_total_um=ww*mult))
    assert len(geom)==30 and all(x['W_unit_um']<=100 and x['m']>0 for x in geom)
    write_json(CASE/'geometry.json',dict(circuit_sha256=sha(c),devices=geom,all_unit_widths_valid=True,HD_logic='none'))
    args=dict(branch=branch,fold=fold,output=output,cc=cc,rz=rz,cm_branch=cm_branch,cm_ratio=cm_ratio,ncdrop=ncdrop,pcdrop=pcdrop,cm_gmid=cm_gmid)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,parameters=args,rationale='Folded first-stage target gm1=1.8mS and Cc=2pF predict UGB143MHz. .36um second stage gm/ID6 at700uA gives gm2=4.2mS; series400ohm exceeds1/gm2 to remove the RHP Miller zero. Shared10uA unit mirrors keep width legal. CM amplifier mirror surplus current biases a diode NMOS for finite low output impedance, then controls first-stage sinks.'))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_files=sources,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=50e-6,VCM_V=.9,load_each_F=1e-12,
       ac=dict(start_Hz=10,stop_Hz=1e10,dec=100,gain_10Hz_min_dB=60,ugb_min_Hz=100e6,pm_min_deg=60,output_cm_error_max_V=.015,output_balance_error_max_V=.0001,power_max_W=.005),
       noise=dict(topology='unity differential feedback; differential output; source input referred',start_Hz=10,stop_Hz=15e6,max_Vrms=50e-6),
       range=dict(command_min_V=-.8,command_max_V=.8,step_V=.005,points=321,valid_tracking_band_V=.005,min_valid_span_Vpp=.8,require_contiguous_valid_interval=True),
       settling=dict(command_V=[-.2,.2],edge_start_s=20e-9,edge_end_s=21e-9,stop_s=320e-9,band_V=.002,time_origin_s=20e-9,max_s=15e-9,final_error_fraction_max=.01,fraction_denominator_V=.2,definition='last tolerance crossing interpolation minus20ns; final instantaneous output at320ns'),
       cm_recovery=dict(command_V=[.85,.95],edge_start_s=20e-9,edge_end_s=21e-9,stop_s=1e-6,band_V=.015,time_origin_s=20e-9,max_s=100e-9,final_error_max_V=.01),
       rejection=dict(original='20 fixed seeds41000..41019 at nominal local mismatch;10Hz CMRR>=50dB and PSRR both rails>=40dB;1MHz characterization',this_scope='matched nominal four excitations only, characterized and explicitly excluded from random mismatch pass claim',CMRR_min_dB=50,PSRR_min_dB=40,seed_samples_executed=0),
       nominal_only=True,exclusions=['other26 primary PVT points','two nonnominal dynamic representative points','20 fixed seed mismatch samples','post-layout/passive variation'],relaxation='project acceptance-policy; original measurement bands and stimuli retained'))
    return c

def prefix(c):return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=50u
X (0 iref vdd vinn vinp vocm voutn voutp) fd_two_stage_miller_opamp
CLP (voutp 0) capacitor c=1p
CLN (voutn 0) capacitor c=1p
save voutp voutn vinp vinn vocm iref VDD:p
'''

def acbench(c):
    b=prefix(c)+'''VOCM (vocm 0) vsource dc=.9
VINP (vinp 0) vsource dc=.9 mag=.5
VINN (vinn 0) vsource dc=.9 mag=.5 phase=180
save X.tail X.fp X.fn X.stagep X.stagen X.sinkp X.sinkn X.vbp X.vbpout X.vpc X.vcn X.vcmfb X.vcms X.cmt X.cma X.ncb X.pcb
'''
    for q in json.loads((CASE/'geometry.json').read_text())['devices']:
        b+='save '+' '.join('X.'+q['name']+':'+k for k in OPFIELDS)+'\n'
    return b+'dcOp dc\nac ac start=10 stop=10G dec=100\n'

def feedback():return '''EFB (err src voutp voutn) vcvs gain=-1
EINP (vinp vocm err 0) vcvs gain=.5
EINN (vinn vocm err 0) vcvs gain=-.5
save src err
'''

def noisebench(c):return prefix(c)+'''VOCM (vocm 0) vsource dc=.9
VNOISE (src 0) vsource dc=0 mag=1
'''+feedback()+'''noise (voutp voutn) noise iprobe=VNOISE start=10 stop=15M dec=100
'''

def rangebench(c):return prefix(c)+'''parameters command=0
VOCM (vocm 0) vsource dc=.9
VCMD (src 0) vsource dc=command
'''+feedback()+'''swing dc param=command start=-.8 stop=.8 step=.005
'''

def settlebench(c):return prefix(c)+'''VOCM (vocm 0) vsource dc=.9
VCMD (src 0) vsource type=pwl wave=[0 -.2 20n -.2 21n .2 320n .2]
'''+feedback()+'''tran tran stop=320n maxstep=25p strobeperiod=50p strobeoutput=strobeonly errpreset=conservative
'''

def cmbench(c):return prefix(c)+'''VOCM (vocm 0) vsource type=pwl wave=[0 .85 20n .85 21n .95 1u .95]
VINP (vinp 0) vsource dc=.9
VINN (vinn 0) vsource dc=.9
save X.vcmfb X.vcms X.stagep
tran tran stop=1u maxstep=50p strobeperiod=100p strobeoutput=strobeonly errpreset=conservative
'''

def rejectionbench(c):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
'''
    for name,pa,na,vda,vsa in [('D',.5,-.5,0,0),('C',1,1,0,0),('P',0,0,1,0),('N',0,0,-1,1)]:
        def acmag(v):return f'mag={abs(v):g} phase={180 if v<0 else 0}'
        b+=f'''VSS{name} (vss{name} 0) vsource dc=0 {acmag(vsa)}
VDD{name} (vdd{name} vss{name}) vsource dc=1.8 {acmag(vda)}
IREF{name} (vdd{name} iref{name}) isource dc=50u
VOCM{name} (vocm{name} vss{name}) vsource dc=.9
VIP{name} (vinp{name} vss{name}) vsource dc=.9 {acmag(pa)}
VIN{name} (vinn{name} vss{name}) vsource dc=.9 {acmag(na)}
X{name} (vss{name} iref{name} vdd{name} vinn{name} vinp{name} vocm{name} voutn{name} voutp{name}) fd_two_stage_miller_opamp
CLP{name} (voutp{name} vss{name}) capacitor c=1p
CLN{name} (voutn{name} vss{name}) capacitor c=1p
save voutp{name} voutn{name} vdd{name} vss{name}
'''
    return b+'ac ac start=10 stop=10M dec=100\n'

def last_cross(t,y,target,band,origin):
    e=abs(y-target)-band;inds=np.flatnonzero((e[:-1]*e[1:]<=0)&(e[:-1]!=e[1:])&(t[1:]>=origin))
    if not len(inds) or e[-1]>0:return None
    k=inds[-1];tc=t[k]-e[k]*(t[k+1]-t[k])/(e[k+1]-e[k]);return float(max(0,tc-origin))

def cm_stb():
    c=CASE/'circuit.scs';cp=CASE/'cmprobe.scs';cp.write_text(c.read_text().replace('MCMSENSE (vcmfb vcms cmt vss)','PCM (vcms cm_probe) iprobe\nMCMSENSE (vcmfb cm_probe cmt vss)'))
    b=acbench(cp).replace('ac ac start=10 stop=10G dec=100','cmstb stb start=1 stop=10G dec=100 probe=X.PCM')
    rd=run_spectre(35,'cmstb',b,[c,cp,CASE/'sizing.json',CASE/'contract.json']);d=data(rd,'cmstb.stb');m=loop_metrics(d['freq'],-d['loopGain'],1)
    log=(rd/'output/bench.log').read_text();native=re.search(r'Phase margin = ([0-9.]+) Deg',log)
    m.update(run_dir=str(rd.relative_to(ROOT)),native_PM_deg=float(native[1]) if native else None,passes=bool(m['phase_margin_deg']>=45 and m['falling_crossings']==1),definition='-Spectre loopGain; zero-volt iprobe in CM sense-to-gate connection; minimum45deg diagnostic')
    if native:assert abs(m['native_PM_deg']-m['phase_margin_deg'])<.02
    write_json(rd/'measurements.json',m);return m

def original_scalar_checks(values):
    """Compare translated scalar values with the frozen verifier's threshold function."""
    def loadmodule(name,path):
        spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
    old=sys.modules.get('utils');sys.modules['utils']=loadmodule('case35_original_utils',CASE/'source/tests/utils.py')
    try:v=loadmodule('case35_original_verify',CASE/'source/tests/verify.py')
    finally:
        if old is None:sys.modules.pop('utils',None)
        else:sys.modules['utils']=old
    mapped=dict(name='smic18_tt_1.8V_27C',dc_gain_db=values['gain_db'],ugb_hz=values['ugb_hz'],phase_margin_deg=values['phase_margin_deg'],output_common_mode_error_v=values['cm_error_V'],output_balance_error_v=values['balance_error_V'],power_w=values['power_W'])
    ok,msg=v.nominal_functional(mapped);result={'nominal_OP_AC':dict(passed=ok,message=msg)}
    checks=[('input_noise_Vrms',50e-6,False),('range_Vpp',.8,True),('range_tracking_error_V',.005,False),('settling_s',15e-9,False),('settling_error_fraction',.01,False),('cm_recovery_s',100e-9,False),('cm_final_error_V',.01,False)]
    for key,lim,ismin in checks:
        if key in values and values[key] is not None:
            _,ok,msg=v.threshold([{'name':'smic18_nominal',key:values[key]}],1,(key,key,lim,ismin,1,'SI'))
            result[key]=dict(passed=ok,message=msg)
    return result

def extract(runs):
    o=dc(runs['ac']);a=data(runs['ac'],'ac.ac');h=a['voutp']-a['voutn'];lm=loop_metrics(a['freq'],h,10)
    vals=dict(gain_db=lm['gain_db'],ugb_hz=lm['ugb_hz'],phase_margin_deg=lm['phase_margin_deg'],cm_error_V=abs((o['voutp']+o['voutn'])/2-.9),balance_error_V=abs(o['voutp']-o['voutn']),power_W=-1.8*o['VDD:p'])
    db=20*np.log10(abs(h));below=np.flatnonzero(db<0);recross=bool(not len(below) or np.any(db[below[0]:]>=0))
    gates={}
    specs=[('gain_db',60,'min','dB','amplitude_db'),('ugb_hz',100e6,'min','Hz','linear'),('phase_margin_deg',60,'min','deg','phase_margin'),('cm_error_V',.015,'max','V','linear'),('balance_error_V',.0001,'max','V','linear'),('power_W',.005,'max','W','linear')]
    op={}
    for q0 in json.loads((CASE/'geometry.json').read_text())['devices']:
        name=q0['name'];q={k:o['X.'+name+':'+k] for k in OPFIELDS};q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[name]=q
    valid=vals['power_W']>0 and lm['falling_crossings']==1 and not recross
    extra={}
    if 'noise' in runs:
        n=data(runs['noise'],'noise.noise',required=('in','out'))
        assert abs(n['freq'][0]-10)<1e-9 and abs(n['freq'][-1]-15e6)<1
        psd=abs(n['in'])**2;nf=n['freq'];vals['input_noise_Vrms']=float(np.sqrt(np.trapz(psd,nf)))
        lr=np.log(nf[1:]/nf[:-1]);exponent=np.log(psd[1:]/psd[:-1])/lr+1
        integral=np.where(abs(exponent)<1e-10,lr,np.expm1(exponent*lr)/exponent)
        powerlaw=float(np.sqrt(np.sum(psd[:-1]*nf[:-1]*integral)))
        extra['noise_quadrature']=dict(primary='trapezoid of squared input spectral amplitude over linear frequency',powerlaw_PSD_interpolation_Vrms=powerlaw,relative_difference=abs(vals['input_noise_Vrms']/powerlaw-1),points=len(nf),start_Hz=float(nf[0]),stop_Hz=float(nf[-1]))
        specs.append(('input_noise_Vrms',50e-6,'max','Vrms','linear'))
    if 'range' in runs:
        d=data(runs['range'],'swing.dc');cmd=d['src'];y=d['voutp']-d['voutn'];err=abs(y-cmd);ok=err<=.005
        assert len(cmd)==321 and np.allclose(cmd,np.linspace(-.8,.8,321),atol=1e-9,rtol=0)
        inds=np.flatnonzero(ok);contiguous=bool(len(inds) and len(inds)==inds[-1]-inds[0]+1)
        vals.update(range_Vpp=float(cmd[inds[-1]]-cmd[inds[0]]) if len(inds) else 0,range_tracking_error_V=float(max(err[ok])) if len(inds) else float(max(err)))
        extra['range']=dict(points=321,valid_points=int(sum(ok)),valid_command_min_V=float(cmd[inds[0]]) if len(inds) else None,valid_command_max_V=float(cmd[inds[-1]]) if len(inds) else None,contiguous=contiguous,max_CM_error_V=float(max(abs((d['voutp']+d['voutn'])/2-.9))))
        valid=valid and contiguous;specs.extend([('range_Vpp',.8,'min','Vpp','linear'),('range_tracking_error_V',.005,'max','V','linear')])
    if 'settling' in runs:
        d=data(runs['settling'],'tran.tran');y=d['voutp']-d['voutn'];vals['settling_s']=last_cross(d['time'],y,.2,.002,20e-9);vals['settling_error_fraction']=float(abs(y[-1]-.2)/.2)
        specs.extend([('settling_s',15e-9,'max','s','linear'),('settling_error_fraction',.01,'max','fraction','linear')]);valid=valid and vals['settling_s'] is not None
    if 'cm' in runs:
        d=data(runs['cm'],'tran.tran');y=(d['voutp']+d['voutn'])/2;vals['cm_recovery_s']=last_cross(d['time'],y,.95,.015,20e-9);vals['cm_final_error_V']=float(abs(y[-1]-.95))
        specs.extend([('cm_recovery_s',100e-9,'max','s','linear'),('cm_final_error_V',.01,'max','V','linear')]);valid=valid and vals['cm_recovery_s'] is not None
    if 'rejection' in runs:
        d=data(runs['rejection'],'ac.ac');dm=d['voutpD']-d['voutnD'];extra['matched_rejection']={}
        for k,suffix,lim in [('CMRR','C',50),('PSRR_plus','P',40),('PSRR_minus','N',40)]:
            z=d['voutp'+suffix]-d['voutn'+suffix];out={}
            for f in [10,1e6]:
                ad=complex(at(d['freq'],dm,f));az=complex(at(d['freq'],z,f));leg=max(abs(complex(at(d['freq'],d['voutp'+suffix],f))),abs(complex(at(d['freq'],d['voutn'+suffix],f))))
                out[str(f)]=dict(differential_signal_gain=abs(ad),disturbance_to_differential_gain=abs(az),rejection_db=float(20*np.log10(abs(ad)/abs(az))) if abs(az)>0 else None,numerical_cancellation_limited=True,matched_symmetry_limited=True,relative_leg_residual=float(abs(az)/max(leg,1e-20)))
            out.update(original_mismatch_limit_dB=lim,scope='Matched nominal characterization only; not a20-sample mismatch pass')
            extra['matched_rejection'][k]=out
    for key,lim,sense,unit,kind in specs:
        if vals[key] is not None:gates[key]=gate(vals[key],lim,sense,unit,kind)
    complete=set(runs)=={'ac','noise','range','settling','cm','rejection'}
    tiers={t:bool(complete and valid and all(q['passes'][t] for q in gates.values())) for t in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    r=dict(case_slot=35,generated_at=now(),run_dirs=[str(rd.relative_to(ROOT)) for rd in runs.values()],runs_by_analysis={k:str(rd.relative_to(ROOT)) for k,rd in runs.items()},status='complete_'+tier if tier else 'partial',values=vals,gates=gates,operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},ac_guards=dict(falling_crossings=lm['falling_crossings'],recross=recross),pass_tiers=tiers,all_nominal_checks_complete=complete,model_dimensions_valid=True,nonrelaxable_guards_pass=bool(valid),nominal_OP_all_30_saturation=all(q['headroom_V']>0 for q in op.values()),source_scalar_crosscheck=original_scalar_checks(vals),source_verifier_sha256=sha(CASE/'source/tests/verify.py'),mismatch_samples_executed=0,scope='Matched deterministic nominal only. The original20-seed mismatch rejection requirement is excluded, not passed.',**extra)
    write_json(runs['ac']/'measurements.json',r);write_json(CASE/'latest_results.json',r);update_case(35,status=r['status'],nominal_complete=bool(tier),case_dir=str(CASE.relative_to(ROOT)),results=str((CASE/'latest_results.json').relative_to(ROOT)),run_dirs=r['run_dirs'])
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['static','full'],default='full')
    for name,default in [('branch',100),('fold',150),('output',700),('cc',2),('rz',400),('cm_branch',50),('cm_ratio',2),('ncdrop',.28),('pcdrop',.4),('cm_gmid',14)]:p.add_argument('--'+name.replace('_','-'),type=float,default=default)
    args=vars(p.parse_args());mode=args.pop('mode');update_case(35,status='running',nominal_complete=False)
    c=design(**args);deps=[c,CASE/'sizing.json',CASE/'contract.json',Path(__file__).resolve()]
    jobs=[('ac',acbench)]+([('noise',noisebench),('range',rangebench),('settling',settlebench),('cm',cmbench),('rejection',rejectionbench)] if mode=='full' else [])
    runs={}
    for name,fn in jobs:
        text=fn(c);(CASE/f'testbench_{name}.scs').write_text(text);runs[name]=run_spectre(35,name,text,deps)
    r=extract(runs)
    print(json.dumps(dict(status=r['status'],values=r['values'],op_summary={k:{n:r['operating_point'][k][n] for n in ['gmid','headroom_V']} for k in ['MINP','MPCP','MNCP','MSINKP','MSECONDP','MLOADP','MCMSENSE']}),indent=2))
    if r['status'].startswith('complete'):
        r['cm_loop_diagnostic']=cm_stb()
        if not r['cm_loop_diagnostic']['passes']:
            r['status']='partial';r['pass_tiers']={t:False for t in r['pass_tiers']};update_case(35,status='partial',nominal_complete=False)
        write_json(CASE/'latest_results.json',r);write_json(runs['ac']/'measurements.json',r)
        print(json.dumps(r['cm_loop_diagnostic'],indent=2))

if __name__=='__main__':main()
