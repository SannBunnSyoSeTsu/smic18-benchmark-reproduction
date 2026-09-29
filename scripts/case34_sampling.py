"""SMIC18 deterministic nominal sampling-feedback OTA; original capacitive benches."""
from __future__ import annotations
import argparse,shutil
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *
from case21_highpsrr_bandgap import quota_guard

CASE=ROOT/'cases/34-sampling-ota-gain8';TASK=SOURCE/'sky130-fd-sampling-feedback-ota-gain8-settling10ns-noise1mv-pvt-mc'
GROUPS=['loop','settling','noise','ranges','cmfb','rejection']
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region']

def freeze():
    CASE.mkdir(parents=True,exist_ok=True);files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',TASK/'tests/utils.py',TASK/'environment/starter/testbench/tb_nominal.spi']+sorted((TASK/'tests/benches').glob('*.spi'))
    for src in files:
        dst=CASE/'source'/src.relative_to(TASK);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    write_json(CASE/'source_provenance.json',dict(task=str(TASK),captured_at=now(),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=50e-6,VCM_V=.9,pin_order=['vss','iref','vdd','vinn','vinp','vocm','voutn','voutp'],feedback=dict(Cs_F=1e-12,Cf_F=125e-15,CL_each_F=250e-15,DC_bias_L_H=1e9,beta=.111111111111),loop=dict(start_Hz=10,stop_Hz=1e11,points_per_decade=80,return_ratio='0.111111111111*(voutp-voutn); CL_eff=0.361111111111pF per output',nominal_closed_loop_numerator='A/(1+0.111111111111*A) at10Hz'),settling=dict(step_V=.9,start_s=[25e-9,65e-9],physical_edge_s=50e-12,pulse_plateau_s=40e-9,period_s=100e-9,stop_s=105e-9,tolerance_V=9e-3,windows_s=[[25e-9,64e-9],[65e-9,105e-9]],static_read_s=[64e-9,104e-9],dynamic_read_s=[35e-9,75e-9],target_differential_V=[.9,0]),ranges=dict(input_start_V=-20e-6,input_stop_V=20e-6,input_step_V=.5e-6,definition='Open-loop differential-output span at two local DC gain crossings3dB below peak; not a closed-loop command sweep'),noise=dict(start_Hz=10,stop_Hz=1e10,points_per_decade=80,quantity='differential output Vrms; integrated squared output spectral amplitude, not input noise'),cmfb=dict(sink_each_A=50e-6,pulse_start_s=20e-9,rise_fall_s=100e-12,plateau_s=20e-9,period_s=200e-9,stop_s=150e-9,peak_window_s=[20e-9,45e-9],residual_read_s=[60.2e-9,140.2e-9],reference='separate undisturbed identical DUT'),limits=dict(phase_margin_deg=60,cm_error_V=.025,power_W=.010,static_error_fraction=.01,dynamic_error_fraction=.01,settling_s=10e-9,range_V=1.8,noise_Vrms=1e-3,cmfb_peak_V=.1,cmfb_20ns_V=.005,cmfb_100ns_V=.001),allowed_DUT='native SMIC MOS and idealR/C allowed by original task; no internal sources or behavioral elements',scope='Deterministic matched TT/1.8V/27C nominal only; retain both settling edges, full noise band, open-loop range and common-mode disturbance. Other29PVTpoints, two nonnominal CMFBpoints and20local-mismatch samples excluded, not passed.',mismatch_samples_executed=0,acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env.update(captured_at=now(),models=model_provenance());write_json(CASE/'environment.json',env)

def design(cc=.64,rz=1000,branch=600,input_gmid=10,output=700):
    base=ROOT/'cases/35-fd-miller';old=json.loads((base/'sizing.json').read_text());roles={}
    for name,q in old['roles'].items():
        roles[name]=lut_size(q['model'],q['L_um'],q['gmid'],q['Id_A'],q['lut_metadata']['vds_V'],q['width_ref_um'])
        assert roles[name]['rounded_W_um']==q['rounded_W_um'] and roles[name]['lut_sha256']==q['lut_sha256']
    roles['input']=lut_size('n18',1,input_gmid,10e-6,.9)
    text=(base/'circuit.scs').read_text().replace('fd_two_stage_miller_opamp','sampling_feedback_ota')
    text=re.sub(r'(RZ[PN] \([^\n]+\) resistor r=)[^\n]+',lambda m:m[1]+f'{rz:g}',text)
    text=re.sub(r'(CC[PN] \([^\n]+\) capacitor c=)[^\n]+',lambda m:m[1]+f'{cc:g}p',text)
    for name,m in [('MTAIL',2*branch/10),('MINP',branch/10),('MINN',branch/10),('MSP',(branch+50)/10),('MSN',(branch+50)/10),('MSECONDP',output/10),('MSECONDN',output/10),('MLOADP',output/10),('MLOADN',output/10)]:
        text=re.sub(r'(^'+name+r' [^\n]*\bm=)[^\n]+',lambda q:q[1]+f'{m:g}',text,flags=re.M)
    for name in ['MINP','MINN']:
        text=re.sub(r'(^'+name+r' [^\n]*\bw=)[^\s]+',lambda q:q[1]+f"{roles['input']['rounded_W_um']:g}u",text,flags=re.M)
    (CASE/'circuit.scs').write_text(text)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,parameters={**old['parameters'],'cc':cc,'rz':rz,'branch':branch,'fold':branch+50,'input_gmid':input_gmid,'output':output},circuit_sha256=sha(CASE/'circuit.scs'),starting_topology=dict(path=str(base/'circuit.scs'),sha256=sha(base/'circuit.scs')),rationale='FreshgmID input sizing and increased input current addressbeta1/9 loop speed. Folding sources grow with tail current but preserve50uA cascode/sink branches. SmallerCc, actualCf125fF/CL250fF, output0.9V and10GHz noise band require new task34 simulations; no historical35/33 measurements are scored.'))
    for q in roles.values():(CASE/'lut').mkdir(exist_ok=True);shutil.copy2(q['lut_path'],CASE/'lut'/Path(q['lut_path']).name)

def prefix():
    return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-10 iabstol=1e-15
saveOptions options save=selected
'''

def standard(load_pf=.25):return f'''VSS (vss 0) vsource dc=0
VDD (vdd vss) vsource dc=1.8
IREF (vdd iref) isource dc=50u
VOCM (vocm vss) vsource dc=.9
X (vss iref vdd vinn vinp vocm voutn voutp) sampling_feedback_ota
CLP (voutp vss) capacitor c={load_pf:.12g}p
CLN (voutn vss) capacitor c={load_pf:.12g}p
save vdd vss iref vocm vinp vinn voutp voutn VDD:p
'''

def caps():return '''CSP (srcp vinp) capacitor c=1p
CSN (srcn vinn) capacitor c=1p
CFP (voutn vinp) capacitor c=125f
CFN (voutp vinn) capacitor c=125f
LBP (vocm vinp) inductor l=1G
LBN (vocm vinn) inductor l=1G
save srcp srcn
'''

def bench(group,step_ps=10):
    if group=='rejection':
        b=prefix()
        for label,cm,pa,na in [('C',1,0,0),('P',0,1,0),('N',0,-1,1)]:
            def mag(x):return f'mag={abs(x):g} phase={180 if x<0 else 0}'
            b+=f'''VSS{label} (vss{label} 0) vsource dc=0 {mag(na)}
VDD{label} (vdd{label} vss{label}) vsource dc=1.8 {mag(pa)}
IREF{label} (vdd{label} iref{label}) isource dc=50u
VOCM{label} (vocm{label} vss{label}) vsource dc=.9
VCM{label} (cm{label} 0) vsource dc=0 mag={cm}
ECM{label} (cmref{label} vocm{label} cm{label} 0) vcvs gain=1
EP{label} (vinp{label} cmref{label} voutp{label} voutn{label}) vcvs gain=-.0555555555556
EN{label} (vinn{label} cmref{label} voutp{label} voutn{label}) vcvs gain=.0555555555556
X{label} (vss{label} iref{label} vdd{label} vinn{label} vinp{label} vocm{label} voutn{label} voutp{label}) sampling_feedback_ota
CLP{label} (voutp{label} vss{label}) capacitor c=.361111111111111p
CLN{label} (voutn{label} vss{label}) capacitor c=.361111111111111p
save voutp{label} voutn{label}
'''
        # Spectre rejects equal start/stop; retain exact10Hz sample plus unused11Hz.
        return b+'ac ac start=10 stop=11 lin=2\n'
    b=prefix()+standard(.25+1/9 if group=='loop' else .25)
    if group=='loop':
        b+='VINP (vinp vss) vsource dc=.9 mag=.5\nVINN (vinn vss) vsource dc=.9 mag=.5 phase=180\n'
        for dev in re.findall(r'^(M\w+) ',(CASE/'circuit.scs').read_text(),re.M):b+='save '+' '.join(f'X.{dev}:{k}' for k in OPFIELDS)+'\n'
        b+='save X.tail X.fp X.fn X.stagep X.stagen X.sinkp X.sinkn X.vbp X.vbpout X.vcn X.vpc X.vcmfb X.vcms X.cmt X.cma X.ncb X.pcb\n'
        return b+'dcOp dc\nac ac start=10 stop=100G dec=80\n'
    if group=='ranges':return b+'''parameters vin_diff=0
VID (vid vss) vsource dc=vin_diff
EIP (vinp vocm vid vss) vcvs gain=.5
EIN (vinn vocm vid vss) vcvs gain=-.5
save vid
swing dc param=vin_diff start=-20u stop=20u step=500n
'''
    if group=='noise':return b+'''VNOISE (srcp vss) vsource dc=.9 mag=1
VQUIET (srcn vss) vsource dc=.9
'''+caps()+'noise (voutp voutn) noise iprobe=VNOISE start=10 stop=10G dec=80\n'
    if group=='settling':
        b+='''VSIGP (srcp vss) vsource type=pulse val0=.9 val1=.95625 delay=25n rise=50p fall=50p width=40n period=100n
VSIGN (srcn vss) vsource type=pulse val0=.9 val1=.84375 delay=25n rise=50p fall=50p width=40n period=100n
'''+caps()+'save X.stagep X.stagen X.vcmfb X.vcms\n'
        return b+f'tran tran stop=105n maxstep={step_ps:g}p errpreset=conservative method=gear2only\n'
    assert group=='cmfb'
    return b+f'''VINP (vinp vss) vsource dc=.9
VINN (vinn vss) vsource dc=.9
IREFR (vdd irefr) isource dc=50u
XR (vss irefr vdd vinn vinp vocm routn routp) sampling_feedback_ota
CLRP (routp vss) capacitor c=250f
CLRN (routn vss) capacitor c=250f
VSENSEP (voutp distp) vsource dc=0
VSENSEN (voutn distn) vsource dc=0
IDISTP (distp vss) isource type=pulse val0=0 val1=50u delay=20n rise=100p fall=100p width=20n period=200n
IDISTN (distn vss) isource type=pulse val0=0 val1=50u delay=20n rise=100p fall=100p width=20n period=200n
save routp routn X.vcmfb X.stagep VSENSEP:p VSENSEN:p
tran tran stop=150n maxstep={step_ps:g}p errpreset=conservative method=gear2only
'''

def simulate(groups,step_ps=10):
    cp=CASE/'circuit.scs';runs={}
    if (CASE/'latest_runs.json').exists():
        for k,p in json.loads((CASE/'latest_runs.json').read_text()).items():
            if json.loads((ROOT/p/'run.json').read_text())['dependencies'][str(cp)]['sha256']==sha(cp):runs[k]=p
    for name in groups:
        quota_guard();b=bench(name,step_ps);(CASE/f'testbench_{name}.scs').write_text(b)
        rd=run_spectre(34,name,b,[cp,CASE/'sizing.json',CASE/'contract.json'],timeout=600);runs[name]=str(rd.relative_to(ROOT));write_json(CASE/'latest_runs.json',runs)
    return runs

def last_cross(t,y,start,stop,target,band):
    ix=np.flatnonzero((t>start)&(t<stop));tt=np.r_[start,t[ix],stop];yy=np.interp(tt,t,y);e=abs(yy-target)-band
    hit=np.flatnonzero((e[:-1]*e[1:]<=0)&(e[:-1]!=e[1:]))
    if not len(hit) or e[-1]>0:return None
    i=hit[-1];return float(tt[i]-e[i]*(tt[i+1]-tt[i])/(e[i+1]-e[i])-start)

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());vals={};gates={};extra={};valid=True
    if 'loop' in runs:
        run=ROOT/runs['loop'];o=dc(run);d=data(run,'ac.ac');h=d['voutp']-d['voutn'];loop=.111111111111*h;m=loop_metrics(d['freq'],loop,10);db=20*np.log10(abs(loop));ix=np.flatnonzero(db<0);recross=not len(ix) or bool(np.any(db[ix[0]:]>0));valid=valid and m['falling_crossings']==1 and not recross
        vals.update(output_common_mode_error_v=abs((o['voutp']+o['voutn'])/2-.9),power_w=-1.8*o['VDD:p'],low_frequency_loop_gain_db=m['gain_db'],closed_loop_differential_gain_db=float(20*np.log10(abs(h[0]/(1+loop[0])))),loop_ugb_hz=m['ugb_hz'],phase_margin_deg=m['phase_margin_deg'])
        op={}
        for dev in re.findall(r'^(M\w+) ',(CASE/'circuit.scs').read_text(),re.M):
            q={k:o[f'X.{dev}:{k}'] for k in OPFIELDS};q.update(gmid=abs(q['gm']/q['ids']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[dev]=q
        extra.update(operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},ac_guards=dict(falling_crossings=m['falling_crossings'],recross=recross));valid=valid and vals['power_w']>0 and all(q['headroom_V']>0 for q in op.values())
    if 'settling' in runs:
        d=data(ROOT/runs['settling'],'tran.tran');t=d['time'];y=d['voutp']-d['voutn'];at_time=lambda x:float(np.interp(x,t,y));dy=np.gradient(y,t)
        vals.update(rise_settling_time_s=last_cross(t,y,25e-9,64e-9,.9,9e-3),fall_settling_time_s=last_cross(t,y,65e-9,105e-9,0,9e-3),rise_dynamic_output_v=at_time(35e-9),fall_dynamic_output_v=at_time(75e-9),high_static_output_v=at_time(64e-9),low_static_output_v=at_time(104e-9),rise_slew_rate_v_per_s=float(max(dy[(t>=25e-9)&(t<=35e-9)])),fall_slew_rate_v_per_s=float(min(dy[(t>=65e-9)&(t<=75e-9)])),rise_peak_output_v=float(max(y[(t>=25e-9)&(t<=64e-9)])),fall_min_output_v=float(min(y[(t>=65e-9)&(t<=104e-9)])),max_output_common_mode_error_v=float(max(abs((d['voutp'][(t>=25e-9)&(t<=104e-9)]+d['voutn'][(t>=25e-9)&(t<=104e-9)])/2-.9))))
        for key,source,target in [('rise_dynamic_error_fraction','rise_dynamic_output_v',.9),('fall_dynamic_error_fraction','fall_dynamic_output_v',0),('high_static_error_fraction','high_static_output_v',.9),('low_static_error_fraction','low_static_output_v',0)]:vals[key]=abs(vals[source]-target)/.9
        valid=valid and all(vals[k] is not None for k in ['rise_settling_time_s','fall_settling_time_s'])
    if 'ranges' in runs:
        d=data(ROOT/runs['ranges'],'swing.dc');x=d['vin_diff'];y=d['voutp']-d['voutn'];assert len(x)==81 and np.allclose(x,np.linspace(-20e-6,20e-6,81),rtol=0,atol=1e-13)
        gain=np.gradient(y,x);assert np.all(gain>0);db=20*np.log10(gain);peak=int(np.argmax(db));threshold=db[peak]-3;left=np.flatnonzero((db[:-1]<threshold)&(db[1:]>=threshold));right=np.flatnonzero((db[:-1]>=threshold)&(db[1:]<threshold));assert len(left)==len(right)==1 and left[0]<peak<=right[0]
        def crossing(i):return float(y[i]+(threshold-db[i])*(y[i+1]-y[i])/(db[i+1]-db[i]))
        low,high=crossing(left[0]),crossing(right[0]);vals.update(open_loop_gain_peak_db=float(db[peak]),gain_3db_db=float(threshold),output_range_min_v=low,output_range_max_v=high,output_range_v=high-low);extra['range_derivative']=dict(method='central finite difference, one-sided endpoints; interpolate gain-dB crossings in output coordinates',input_V=x.tolist(),output_V=y.tolist(),gain_db=db.tolist(),crossing_indices=[int(left[0]),int(right[0])])
    if 'noise' in runs:
        d=data(ROOT/runs['noise'],'noise.noise',required=['out']);f=d['freq'];psd=abs(d['out'])**2;assert abs(f[0]-10)<1e-9 and abs(f[-1]-1e10)<1
        vals['output_noise_vrms']=float(np.sqrt(np.trapz(psd,f)));lr=np.log(f[1:]/f[:-1]);alpha=np.log(psd[1:]/psd[:-1])/lr+1;fac=np.where(abs(alpha)<1e-10,lr,np.expm1(alpha*lr)/alpha);quad=float(np.sqrt(np.sum(psd[:-1]*f[:-1]*fac)));extra['noise_quadrature']=dict(powerlaw_Vrms=quad,trapezoid_Vrms=vals['output_noise_vrms'],relative_difference=abs(quad/vals['output_noise_vrms']-1),points=len(f))
    if 'cmfb' in runs:
        d=data(ROOT/runs['cmfb'],'tran.tran');t=d['time'];cm=(d['voutp']+d['voutn'])/2;ref=(d['routp']+d['routn'])/2;dev=abs(cm-ref);ix=np.flatnonzero((t>20e-9)&(t<45e-9));peak=max(np.interp(20e-9,t,dev),np.interp(45e-9,t,dev),max(dev[ix]));vals.update(cmfb_static_error_v=float(abs(np.interp(15e-9,t,cm)-.9)),cmfb_max_deviation_v=float(peak),cmfb_residual_20ns_v=float(np.interp(60.2e-9,t,dev)),cmfb_residual_100ns_v=float(np.interp(140.2e-9,t,dev)))
    if 'rejection' in runs and 'closed_loop_differential_gain_db' in vals:
        d=data(ROOT/runs['rejection'],'ac.ac');extra['matched_rejection']={}
        for label,name in [('C','CMRR'),('P','PSRR_plus'),('N','PSRR_minus')]:
            v0=d['voutp'+label][0]-d['voutn'+label][0];extra['matched_rejection'][name]=dict(feedthrough_abs=float(abs(v0)),nominal_closed_gain_db=vals['closed_loop_differential_gain_db'],ratio_db=float(vals['closed_loop_differential_gain_db']-20*np.log10(abs(v0)))) if abs(v0)>0 else dict(feedthrough_abs=0,ratio_db=None)
        extra['rejection_scope']='Matched symmetric diagnostic only; cancellation-limited. Original20sample mismatch tests excluded, not passed.'
    specs=[('phase_margin_deg',60,'min','deg','phase_margin'),('output_common_mode_error_v',.025,'max','V','linear'),('power_w',.01,'max','W','linear'),('rise_settling_time_s',10e-9,'max','s','linear'),('fall_settling_time_s',10e-9,'max','s','linear'),('rise_dynamic_error_fraction',.01,'max','fraction','linear'),('fall_dynamic_error_fraction',.01,'max','fraction','linear'),('high_static_error_fraction',.01,'max','fraction','linear'),('low_static_error_fraction',.01,'max','fraction','linear'),('output_range_v',1.8,'min','V','linear'),('output_noise_vrms',1e-3,'max','Vrms','linear'),('cmfb_max_deviation_v',.1,'max','V','linear'),('cmfb_residual_20ns_v',.005,'max','V','linear'),('cmfb_residual_100ns_v',.001,'max','V','linear')]
    for key,limit,sense,unit,kind in specs:
        if key in vals and vals[key] is not None:gates[key]=gate(vals[key],limit,sense,unit,kind)
    warnings={k:[w for w in json.loads((ROOT/p/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in w] for k,p in runs.items()};valid=valid and not any(warnings.values());full=set(runs)==set(GROUPS) and len(gates)==len(specs)
    tiers={t:bool(full and valid and all(g['passes'][t] for g in gates.values())) for t in ['original','10pct','15pct']};status=next(('complete_'+t for t,b in tiers.items() if b),'needs_iteration' if full else 'partial')
    report=dict(case_slot=34,generated_at=now(),status=status,values=vals,gates=gates,pass_tiers=tiers,groups=runs,run_dirs=list(runs.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),all_nominal_checks_complete=full,model_dimensions_valid=True,model_operating_range_valid=not any(warnings.values()),disallowed_model_warnings=warnings,nonrelaxable_guards_pass=bool(valid),scope=json.loads((CASE/'contract.json').read_text())['scope'],mismatch_samples_executed=0,**extra)
    write_json(CASE/'latest_results.json',report);print(json.dumps(dict(status=status,values=vals,failed_guards=not valid),indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cc',type=float,default=.64);p.add_argument('--rz',type=float,default=1000);p.add_argument('--branch',type=float,default=600);p.add_argument('--input-gmid',type=float,default=10);p.add_argument('--output',type=float,default=700);p.add_argument('--run',nargs='+',default=GROUPS);p.add_argument('--step-ps',type=float,default=10);p.add_argument('--extract',action='store_true');a=p.parse_args()
    if a.extract:extract();raise SystemExit(0)
    quota_guard()
    if not (CASE/'contract.json').exists():freeze()
    design(a.cc,a.rz,a.branch,a.input_gmid,a.output);update_case(34,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))
    simulate(a.run,a.step_ps);extract()
