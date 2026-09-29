"""SMIC18 analog CML divide-by2 at all four original frequencies."""
from __future__ import annotations
import argparse
import shutil
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *
from case21_highpsrr_bandgap import quota_guard

CASE=ROOT/'cases/09-cml-divider'
TASK=SOURCE/'sky130-cml-divider-div2-range1gto10g'
FREQ={'1g':1e9,'2g':2e9,'5g':5e9,'10g':10e9}

def mos_devices():return re.findall(r'^(M\w+)\s+\(', (CASE/'circuit.scs').read_text(),re.M)

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',TASK/'tests/utils.py',*sorted((TASK/'tests/benches').glob('*.spi')),TASK/'environment/starter/testbench/README.md']
    for src in files:
        dst=CASE/'source'/src.relative_to(TASK);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    write_json(CASE/'source_provenance.json',dict(captured_at=now(),task=str(TASK),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='SMIC18 TT only; preserve all four frequency points and full40cycle observation',VDD_V=1.8,temperature_C=27,reference_A=150e-6,clock_common_mode_V=.9,input_differential_Vpp=.3,input_source_ohm=50,input_rise_s=10e-12,input_fall_s=10e-12,input_delay_s=100e-12,output_load_F_each=10e-15,frequency_Hz=list(FREQ.values()),startup_s=5e-9,observed_input_cycles=40,minimum_each_cycle_swing_Vpp=.2,target_half_frequency_tone_Vpp=.2,sample_phase_period=.4,sign_threshold_V=.01,required_alternating_cycles=40,dc_power_max_W=.0015,dc_power_comparison='strictly less than; includes150uA reference sourced fromVDD',power_clock_inputs_V=.9,nodeset=dict(outp=1.0,outn=.8,interpretation='released DC operating-point hint, never forced during transient'),allowed_DUT='native SMIC MOS plus finite positive ideal R/C; CML core gm/ID explicitly authorized2026-09-22',relaxation='Only swing, target-tone amplitude and power limits; fixed frequency points and alternating-sign function never relaxed',exclusions=['ff/ss/fs/sf corners','voltage/temperature sweeps','mismatch','PEX','phase noise','external clock-driver energy'],acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env['captured_at']=now();env['models']=model_provenance();write_json(CASE/'environment.json',env)

def design(load_r=1200,tail_m=2.3,ref_gmid=16,clock_gmid=14,data_gmid=8,regen_gmid=8):
    roles={
        'reference':lut_size('n18',.36,ref_gmid,150e-6,.45),
        'clock':lut_size('n18',.18,clock_gmid,150e-6,.45),
        'data':lut_size('n18',.18,data_gmid,150e-6,.45),
        'regeneration':lut_size('n18',.18,regen_gmid,150e-6,.45)}
    w={k:q['rounded_W_um'] for k,q in roles.items()}
    text=f'''// Static master-slave CML; no ideal source inside DUT.
simulator lang=spectre
subckt cml_div2 (vss iref vdd clkn clkp outn outp)
MBIAS (iref iref vss vss) n18 w={w['reference']:g}u l=0.36u
RMP (mp vdd) resistor r={load_r:g}
RMN (mn vdd) resistor r={load_r*1.005:g}
MMDP (mp outn nmd vss) n18 w={w['data']:g}u l=0.18u
MMDN (mn outp nmd vss) n18 w={w['data']:g}u l=0.18u
MMTC (nmd clkp mtail vss) n18 w={w['clock']:g}u l=0.18u
MMRP (mp mn nmr vss) n18 w={w['regeneration']:g}u l=0.18u
MMRN (mn mp nmr vss) n18 w={w['regeneration']:g}u l=0.18u
MMTRC (nmr clkn mtail vss) n18 w={w['clock']:g}u l=0.18u
MMTAIL (mtail iref vss vss) n18 w={w['reference']:g}u l=0.36u m={tail_m:g}
RSP (outp vdd) resistor r={load_r*1.005:g}
RSN (outn vdd) resistor r={load_r:g}
MSDP (outp mp nsd vss) n18 w={w['data']:g}u l=0.18u
MSDN (outn mn nsd vss) n18 w={w['data']:g}u l=0.18u
MSTC (nsd clkn stail vss) n18 w={w['clock']:g}u l=0.18u
MSRP (outp outn nsr vss) n18 w={w['regeneration']:g}u l=0.18u
MSRN (outn outp nsr vss) n18 w={w['regeneration']:g}u l=0.18u
MSTRC (nsr clkp stail vss) n18 w={w['clock']:g}u l=0.18u
MSTAIL (stail iref vss vss) n18 w={w['reference']:g}u l=0.36u m={tail_m:g}
ends cml_div2
'''
    (CASE/'circuit.scs').write_text(text)
    write_json(CASE/'sizing.json',dict(generated_at=now(),parameters=dict(load_r=load_r,tail_m=tail_m,ref_gmid=ref_gmid,clock_gmid=clock_gmid,data_gmid=data_gmid,regen_gmid=regen_gmid),roles=roles,rationale='Two static master/slave latches share one steered tail current each. Short data/regeneration devices use lowergm/ID to reduce output gate loading and improve speed; clock pair uses highergm/ID for150mV differential clock peaks. L0.36um tail/reference preserve low headroom and current replication. Budget includes150uA externally sourced reference; all nominal speed points are retained. Small0.5percent resistor asymmetry and released nodeset select phase, not a forced waveform.',circuit_sha256=sha(CASE/'circuit.scs')))
    for z in roles.values():
        dst=CASE/'lut'/Path(z['lut_path']).name;dst.parent.mkdir(exist_ok=True);shutil.copy2(z['lut_path'],dst)

def clock_wave(freq,stop,positive=True):
    low,high=(.825,.975) if positive else (.975,.825)
    period=int(round(1e15/freq));stop=int(round(stop*1e15));delay=100000;edge=10000;points=[(0,low)]
    for k in range(int(stop/period)+2):
        start=delay+k*period
        for t,v in [(start,low),(start+edge,high),(start+period//2,high),(start+period//2+edge,low)]:
            if t<=stop and t>points[-1][0]:points.append((t,v))
    if points[-1][0]<stop:
        phase=(stop-delay)%period
        val=low if stop<delay or phase>=period/2+edge else high if edge<=phase<=period/2 else low+(high-low)*phase/edge if phase<edge else high+(low-high)*(phase-period/2)/edge
        points.append((stop,val))
    return ' '.join(f'{t}f {v:.14g}' for t,v in points)

def bench(kind):
    text=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=150u
X (0 iref vdd clkn clkp outn outp) cml_div2
CLP (outp 0) capacitor c=10f
CLN (outn 0) capacitor c=10f
simulatorOptions options temp=27 tnom=27 reltol=1e-5 vabstol=1e-8 iabstol=1e-14
saveOptions options save=selected
save vdd iref clkp clkn outp outn VDD:p X.mp X.mn X.nmd X.nmr X.mtail X.nsd X.nsr X.stail
nodeset outp=1.0 outn=0.8
'''
    if kind=='power':
        text+='VCLKP (clkp 0) vsource dc=.9\nVCLKN (clkn 0) vsource dc=.9\n'
        for dev in mos_devices():text+='save '+' '.join(f'X.{dev}:{k}' for k in ['ids','gm','gds','vgs','vds','vbs','vdsat','region'])+'\n'
        text+='dcOp dc\n'
    else:
        freq=FREQ[kind];stop=5e-9+40/freq;step=min(2e-12,1/freq/100)
        text+=f'VCLKP (srcp 0) vsource type=pwl wave=[{clock_wave(freq,stop)}]\nVCLKN (srcn 0) vsource type=pwl wave=[{clock_wave(freq,stop,False)}]\nRCLKP (srcp clkp) resistor r=50\nRCLKN (srcn clkn) resistor r=50\nsave srcp srcn\n'
        text+=f'tran tran stop={stop:.14g} maxstep={step:.14g} strobeperiod={step:.14g} strobeoutput=strobeonly method=gear2only errpreset=conservative\n'
    return text

def metrics(d,freq):
    t=d['time'];v=d['outp']-d['outn'];period=1/freq
    assert len(t)>=1000 and t[-1]>=5e-9+40*period-1e-14
    mask=t>=5e-9;tt=t[mask];vv=v[mask];duration=tt[-1]-tt[0];omega=2*np.pi*(freq/2)
    avg=np.trapz(vv,tt)/duration
    ci=np.trapz(vv*np.cos(omega*tt),tt)-avg*(np.sin(omega*tt[-1])-np.sin(omega*tt[0]))/omega
    si=np.trapz(vv*np.sin(omega*tt),tt)-avg*(-np.cos(omega*tt[-1])+np.cos(omega*tt[0]))/omega
    tone=float(4*np.hypot(ci,si)/duration);swings=[];samples=[]
    for cycle in range(40):
        t0=5e-9+cycle*period;t1=t0+period;cyc=(t>=t0)&(t<=t1);assert np.any(cyc)
        swings.append(float(np.ptp(v[cyc])));samples.append(float(v[np.argmin(abs(t-(5e-9+(cycle+.4)*period)))]))
    signs=np.where(np.asarray(samples)>.01,1,np.where(np.asarray(samples)<-.01,-1,0));transitions=int(np.sum((signs[:-1]!=0)&(signs[1:]!=0)&(signs[:-1]!=signs[1:])))
    ix=np.flatnonzero((vv[:-1]<=0)&(vv[1:]>0));cross=tt[ix]-vv[ix]*(tt[ix+1]-tt[ix])/(vv[ix+1]-vv[ix])
    measured=float(1/np.mean(np.diff(cross))) if len(cross)>1 else None
    return dict(frequency_Hz=freq,target_frequency_Hz=freq/2,measured_output_frequency_Hz=measured,positive_zero_crossings=len(cross),output_swing_Vpp=float(np.ptp(vv)),minimum_cycle_swing_Vpp=min(swings),target_tone_Vpp=tone,alternating_cycles=transitions+1,valid_function=bool(transitions==39),cycle_swings_Vpp=swings,samples_V=samples,sample_signs=signs.tolist(),source_differential_Vpp=float(np.ptp(d['srcp']-d['srcn'])),clock_pin_differential_Vpp=float(np.ptp(d['clkp']-d['clkn'])),saved_points=len(t),observation_start_s=float(tt[0]),stop_s=float(t[-1]))

def simulate(kinds):
    cp=CASE/'circuit.scs';runs={}
    if (CASE/'latest_runs.json').exists():
        for k,v in json.loads((CASE/'latest_runs.json').read_text()).items():
            if json.loads((ROOT/v/'run.json').read_text())['dependencies'][str(cp)]['sha256']==sha(cp):runs[k]=v
    for kind in kinds:
        quota_guard();b=bench(kind);(CASE/f'testbench_{kind}.scs').write_text(b)
        run=run_spectre(9,kind,b,[cp,CASE/'sizing.json',CASE/'contract.json']);runs[kind]=str(run.relative_to(ROOT));write_json(CASE/'latest_runs.json',runs)
        result=metrics(data(run,'tran.tran'),FREQ[kind]) if kind!='power' else {'power_W':-1.8*dc(run)['VDD:p']}
        print(kind,json.dumps({k:v for k,v in result.items() if not isinstance(v,list)}),flush=True)
    return runs

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());assert set(groups)==set(FREQ)|{'power'}
    for path in groups.values():
        m=json.loads((ROOT/path/'run.json').read_text());assert m['status']=='completed' and m['dependencies'][str(CASE/'circuit.scs')]['sha256']==sha(CASE/'circuit.scs')
    results={label:metrics(data(ROOT/groups[label],'tran.tran'),freq) for label,freq in FREQ.items()};o=dc(ROOT/groups['power']);power=-1.8*o['VDD:p'];gates={}
    for name,v in results.items():
        gates[name+'_swing']=gate(v['minimum_cycle_swing_Vpp'],.2,'min','Vpp');gates[name+'_tone']=gate(v['target_tone_Vpp'],.2,'min','Vpp');gates[name+'_cycles']=gate(v['alternating_cycles'],40,'min','cycles',relax=False)
    gates['dc_power']=gate(power,.0015,'max','W');gates['dc_power']['passes']={k:power<lim for k,lim in gates['dc_power']['limits'].items()}
    tiers={tier:all(g['passes'][tier] for g in gates.values()) for tier in ['original','10pct','15pct']};tier=next((k for k,v in tiers.items() if v),None)
    op={}
    for dev in mos_devices():
        z={k.split(':')[1]:v for k,v in o.items() if k.startswith('X.'+dev+':')};z.update(gmid=abs(z['gm']/z['ids']),headroom_V=abs(z['vds'])-abs(z['vdsat']));op[dev]=z
    report=dict(case_slot=9,generated_at=now(),status='complete_'+tier if tier else 'partial',values=dict(dc_power_W=power,frequencies=results),gates=gates,pass_tiers=tiers,groups=groups,run_dirs=list(groups.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},all_nominal_checks_complete=True,model_dimensions_valid=True,scope=json.loads((CASE/'contract.json').read_text())['scope'])
    write_json(CASE/'latest_results.json',report);print(json.dumps(dict(status=report['status'],power_W=power,failed_original=[k for k,g in gates.items() if not g['passes']['original']]),indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--load-r',type=float,default=1200);p.add_argument('--tail-m',type=float,default=2.3);p.add_argument('--ref-gmid',type=float,default=16);p.add_argument('--clock-gmid',type=float,default=14);p.add_argument('--data-gmid',type=float,default=8);p.add_argument('--regen-gmid',type=float,default=8);p.add_argument('--run',nargs='+',default=['1g','2g','5g','10g','power']);p.add_argument('--extract',action='store_true');p.add_argument('--prepare',action='store_true');x=p.parse_args()
    if x.extract:extract();raise SystemExit(0)
    if not (CASE/'contract.json').exists():freeze()
    design(x.load_r,x.tail_m,x.ref_gmid,x.clock_gmid,x.data_gmid,x.regen_gmid)
    if x.prepare:raise SystemExit(0)
    quota_guard();update_case(9,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))
    runs=simulate(x.run)
    if set(runs)==set(FREQ)|{'power'}:extract()
