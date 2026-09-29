"""Native SMIC18 line driver; preserve original300ohm/200pF capacitive load."""
from __future__ import annotations
import argparse,shutil
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *
from case21_highpsrr_bandgap import quota_guard
CASE=ROOT/'cases/39-line-driver'
TASK=SOURCE/'sky130-low-power-line-driver-pvt'
SUB='low_power_line_driver'
GROUPS=['loop','swing','thd']
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region']
SPECS=[('loop_gain_10hz_db',40,'min','dB','amplitude_db'),('ugb_hz',.5e6,'min','Hz','linear'),('phase_margin_deg',60,'min','deg','phase_margin'),('output_offset_v',.020,'max','V','linear'),('power_w',400e-6,'max','W','linear'),('thd_pct',3,'max','%','linear'),('fundamental_v',.55,'min','V','linear'),('peak_supply_current_a',.002,'min','A','linear'),('drive_ratio',10,'min','ratio','linear'),('closed_loop_range_vpp',1.5,'min','Vpp','linear')]

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',TASK/'tests/utils.py',TASK/'environment/starter/circuit.spi']+sorted((TASK/'tests/benches').glob('*.spi'))+sorted((TASK/'environment/starter/testbench').glob('*'))
    for src in files:
        dst=CASE/'source'/src.relative_to(TASK);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    write_json(CASE/'source_provenance.json',dict(task=str(TASK),captured_at=now(),files={str(x.relative_to(TASK)):sha(x) for x in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='Matched SMIC18 TT/1.8V/27C nominal only; remaining44PVTpoints excluded, not passed.',VDD_V=1.8,temperature_C=27,reference_A=50e-6,reference_V=.9,pin_order=['vss','iref','vdd','vinn','vinp','vout'],feedback_ohm=[10000,10000],load=dict(coupling_F=1e-6,line_ohm=300,output_F=200e-12),loop=dict(frequency_Hz=[1,1e9],points_per_decade=60,probe='seriesVTEST fbv-vout DC0 AC1',return_ratio='-V(vout)/V(fbv)'),thd=dict(input_offset_V=.9,input_amplitude_V=.6,frequency_Hz=20e3,stop_s=400e-6,window_s=[200e-6,400e-6],samples=2048,harmonics=list(range(1,10)),sample_endpoint=False,peak_current='max(-I_VDD) over200..400us',drive_ratio='peak_VDD_current / (quiescent_VDD_power/1.8)'),swing=dict(input_start_V=.1,input_stop_V=1.7,input_step_V=.002,desired='1.8-input',tracking_tolerance_V=.02,range='contiguous commanded span around0.9V; nearest failing point each side bounds segment; discrete accepted endpoints, no interpolation'),limits={k:dict(value=l,sense=s,unit=u) for k,l,s,u,_ in SPECS},allowed_DUT='native n18/p18 and positive idealR/C; no sources/behavioral elements',acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env.update(captured_at=now(),models=model_provenance());write_json(CASE/'environment.json',env)

def design(cc=6,rz=1000,out=70,tail=20,outgmid=22):
    roles=dict(nbias=lut_size('n18',1,14,5e-6,.45),pbias=lut_size('p18',1,14,5e-6,.45),input=lut_size('n18',1,18,10e-6,.45),nab=lut_size('n18',.36,14,5e-6,.45),pab=lut_size('p18',.36,14,5e-6,.45),nout=lut_size('n18',.36,outgmid,5e-6,.45),pout=lut_size('p18',.36,outgmid,5e-6,.45))
    text=['simulator lang=spectre',f'subckt {SUB} (vss iref vdd vinn vinp vout)'];devs=[]
    def M(name,nodes,role,m=1):
        q=roles[role];w=q['rounded_W_um'];l=q['L_um'];assert .19<=w<=100 and m>0
        text.append(f'{name} ({nodes}) {q["model"]} w={w:g}u l={l:g}u m={m:g}')
        devs.append(dict(name=name,pins=nodes.split(),role=role,model=q['model'],W_unit_um=w,L_um=l,m=m))
    M('MREF','iref iref vss vss','nbias',10)
    M('MTAIL','tail iref vss vss','nbias',tail/5)
    M('MBN','pb iref vss vss','nbias',2);M('MBP','pb pb vdd vdd','pbias',2)
    M('MABNS','vbn pb vdd vdd','pbias');M('MABNU','vbn vbn xn vss','nab');M('MABNL','xn xn vss vss','nout')
    M('MABPS','vbp iref vss vss','nbias');M('MABPU','vbp vbp yp vdd','pab');M('MABPL','yp yp vdd vdd','pout')
    M('MINP','x3 vinp tail vss','input',tail/20);M('MINN','x5 vinn tail vss','input',tail/20)
    for name,nodes in [('MP3','x3 x3 vdd vdd'),('MP4','x4 x3 vdd vdd'),('MP5','x5 x5 vdd vdd'),('MP6','gp x5 vdd vdd')]:M(name,nodes,'pbias',tail/10)
    M('MN7','x4 x4 vss vss','nbias',tail/10);M('MN8','gn x4 vss vss','nbias',tail/10)
    M('MCN','gp vbn gn vss','nab',tail/20);M('MCP','gn vbp gp vdd','pab',tail/20)
    M('MOUTP','vout gp vdd vdd','pout',out/5);M('MOUTN','vout gn vss vss','nout',out/5)
    text+=['RBAT (gp gn) resistor r=2M',f'CCP (vout zp) capacitor c={cc:g}p',f'RZP (zp gp) resistor r={rz:g}',f'CCN (vout zn) capacitor c={cc:g}p',f'RZN (zn gn) resistor r={rz:g}',f'ends {SUB}']
    cp=CASE/'circuit.scs';cp.write_text('\n'.join(text)+'\n')
    write_json(CASE/'geometry.json',dict(circuit_sha256=sha(cp),devices=devs,all_unit_widths_valid=True))
    write_json(CASE/'sizing.json',dict(generated_at=now(),parameters=dict(cc=cc,rz=rz,out=out,tail=tail,outgmid=outgmid),roles=roles,circuit_sha256=sha(cp),rationale='Fresh native gm/ID units. Input tail20uA and mirror copies feed floating complementary control. Both upper AB-bias stacks match floating device current density; lower stack transistors share output geometry, scaled output70uA initial target. Actual body effect/mirror error/output current require OP confirmation. Positive idealR/C permitted. No HD logic.'))
    for q in roles.values():(CASE/'lut').mkdir(exist_ok=True);shutil.copy2(q['lut_path'],CASE/'lut'/Path(q['lut_path']).name)

def bench(group,step_ns=100,reltol=1e-6):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-10 iabstol=1e-15
saveOptions options save=selected
VDD (vdd vss) vsource dc=1.8
IREF (vdd iref) isource dc=50u
VINP (vinp vss) vsource dc=.9
R1 (vs vinn) resistor r=10k
X (vss iref vdd vinn vinp vout) {SUB}
CAC (vout la) capacitor c=1u
RL (la vss) resistor r=300
CL (vout vss) capacitor c=200p
save vs vinn vinp vout la vdd VDD:p X.gp X.gn X.tail X.pb X.vbn X.vbp X.xn X.yp
'''
    if group=='loop':
        b+='VS (vs vss) vsource dc=.9\nR2 (vinn fbv) resistor r=10k\nVTEST (fbv vout) vsource dc=0 mag=1\nsave fbv\n'
        for dev in json.loads((CASE/'geometry.json').read_text())['devices']:b+='save '+' '.join(f'X.{dev["name"]}:{k}' for k in OPFIELDS)+'\n'
        b+='dcOp dc\nac ac start=1 stop=1G dec=60\n'
    else:
        b+='R2 (vinn vout) resistor r=10k\n'
        if group=='swing':b+='parameters command=.9\nVS (vs vss) vsource dc=command\nswing dc param=command start=.1 stop=1.7 step=.002\n'
        elif group=='thd':b+=f'''VS (vs vss) vsource dc=.9 type=sine ampl=.6 freq=20k
save X.MOUTN:ids X.MOUTP:ids
tran tran stop=400u maxstep={step_ns:g}n method=gear2only errpreset=conservative
'''
        else:raise ValueError(group)
    # Ground the ideal0V return directly. Equivalent external connection avoids
    # an unnecessary branch unknown carrying cancellation current of1uF CAC.
    return re.sub(r'\bvss\b','0',b)

def simulate(groups,step_ns=100,reltol=1e-6):
    cp=CASE/'circuit.scs';runs={}
    if (CASE/'latest_runs.json').exists():
        for k,p in json.loads((CASE/'latest_runs.json').read_text()).items():
            if sha(ROOT/p/'inputs/circuit.scs')==sha(cp):runs[k]=p
    for g in groups:
        quota_guard();b=bench(g,step_ns,reltol);(CASE/f'testbench_{g}.scs').write_text(b)
        rd=run_spectre(39,g,b,[cp,CASE/'sizing.json',CASE/'geometry.json',CASE/'contract.json'],timeout=600)
        runs[g]=str(rd.relative_to(ROOT));write_json(CASE/'latest_runs.json',runs)
    return runs

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());v={};extra={};valid=True
    for p in runs.values():
        assert sha(ROOT/p/'inputs/circuit.scs')==sha(CASE/'circuit.scs')
        m=json.loads((ROOT/p/'run.json').read_text());assert m['status']=='completed' and m['model_dimensions_valid']
        assert not m['warnings'],m['warnings']
    if 'loop' in runs:
        o=dc(ROOT/runs['loop']);d=data(ROOT/runs['loop'],'ac.ac');h=-d['vout']/d['fbv'];q=loop_metrics(d['freq'],h,10);db=20*np.log10(abs(h));below=np.flatnonzero(db<0);recross=not len(below) or bool(np.any(db[below[0]:]>0))
        v.update(loop_gain_10hz_db=q['gain_db'],ugb_hz=q['ugb_hz'],phase_margin_deg=q['phase_margin_deg'],output_offset_v=abs(o['vout']-.9),output_dc_v=o['vout'],power_w=abs(1.8*o['VDD:p']),quiescent_current_a=abs(o['VDD:p']))
        valid &= q['falling_crossings']==1 and not recross and v['power_w']>0
        op={}
        for dev in json.loads((CASE/'geometry.json').read_text())['devices']:
            n=dev['name'];z={k:o[f'X.{n}:{k}'] for k in OPFIELDS};z.update(gmid=abs(z['gm']/z['ids']),headroom_V=abs(z['vds'])-abs(z['vdsat']));op[n]=z
        extra.update(operating_point=op,dc_nodes={k:y for k,y in o.items() if ':' not in k},ac_guards=dict(falling_crossings=q['falling_crossings'],recross=recross))
    if 'swing' in runs:
        d=data(ROOT/runs['swing'],'swing.dc');x=d['vs'];y=d['vout'];assert len(x)==801 and np.allclose(x,np.linspace(.1,1.7,801),rtol=0,atol=1e-12)
        desired=1.8-x;error=abs(y-desired);ok=error<=.02;badhi=desired[(~ok)&(desired>.9)];badlo=desired[(~ok)&(desired<.9)]
        hi=min(badhi) if len(badhi) else 1e6;lo=max(badlo) if len(badlo) else -1e6
        seg=ok&(desired<hi)&(desired>lo);assert np.any(seg)
        v['closed_loop_range_vpp']=float(np.ptp(desired[seg]));v['range_low_v']=float(min(desired[seg]));v['range_high_v']=float(max(desired[seg]));v['max_accepted_tracking_error_v']=float(max(error[seg]))
        valid &= bool(ok[int(np.argmin(abs(desired-.9)))]) and bool(np.all(ok[np.flatnonzero(seg)[0]:np.flatnonzero(seg)[-1]+1]))
        extra['swing_definition']=dict(points=len(x),tracking_tolerance_V=.02,input_V=x.tolist(),desired_V=desired.tolist(),output_V=y.tolist(),accepted=seg.tolist())
    if 'thd' in runs:
        d=data(ROOT/runs['thd'],'tran.tran');t=d['time'];assert t[0]==0 and abs(t[-1]-400e-6)<1e-12
        tt=200e-6+np.arange(2048)*(200e-6/2048);yy=np.interp(tt,t,d['vout']);yy-=np.mean(yy);phase=2*np.pi*4*np.arange(2048)/2048
        amps=[float(np.hypot(2*np.mean(yy*np.cos(k*phase)),2*np.mean(yy*np.sin(k*phase)))) for k in range(1,10)]
        currents=-d['VDD:p'];mask=(t>=200e-6)&(t<=400e-6);peak=max(max(currents[mask]),np.interp(200e-6,t,currents),np.interp(400e-6,t,currents))
        v.update(fundamental_v=amps[0],thd_pct=float(100*np.linalg.norm(amps[1:])/amps[0]),peak_supply_current_a=float(peak))
        if 'quiescent_current_a' in v:v['drive_ratio']=float(peak/v['quiescent_current_a'])
        extra['fourier']=dict(harmonic_amplitudes_V=amps,samples=2048,cycles=4,window_s=[200e-6,400e-6],endpoint=False,algorithm='exact original coherent cosine/sine projection on interpolated uniform grid')
        valid &= amps[0]>0 and peak>0
    gates={k:gate(v[k],l,s,u,kind) for k,l,s,u,kind in SPECS if k in v};full=set(runs)==set(GROUPS) and len(gates)==len(SPECS)
    tiers={k:bool(full and valid and all(q['passes'][k] for q in gates.values())) for k in ['original','10pct','15pct']};status=next(('complete_'+k for k,z in tiers.items() if z),'needs_iteration' if full else 'partial')
    r=dict(case_slot=39,generated_at=now(),status=status,values=v,gates=gates,pass_tiers=tiers,groups=runs,run_dirs=list(runs.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),all_nominal_checks_complete=full,model_dimensions_valid=True,nonrelaxable_guards_pass=bool(valid),scope=json.loads((CASE/'contract.json').read_text())['scope'],**extra)
    write_json(CASE/'latest_results.json',r);print(json.dumps(dict(status=status,values=v,failed_original=[k for k,q in gates.items() if not q['passes']['original']]),indent=2));return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cc',type=float,default=6);p.add_argument('--rz',type=float,default=1000);p.add_argument('--out',type=float,default=70);p.add_argument('--tail',type=float,default=20);p.add_argument('--outgmid',type=float,default=22);p.add_argument('--run',nargs='+',default=GROUPS);p.add_argument('--step-ns',type=float,default=100);p.add_argument('--reltol',type=float,default=1e-6);p.add_argument('--extract',action='store_true');a=p.parse_args()
    quota_guard()
    if a.extract:extract();raise SystemExit(0)
    if not (CASE/'contract.json').exists():freeze()
    design(a.cc,a.rz,a.out,a.tail,a.outgmid);update_case(39,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));simulate(a.run,a.step_ns,a.reltol);extract()
