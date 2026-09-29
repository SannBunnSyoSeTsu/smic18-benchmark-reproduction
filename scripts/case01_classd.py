"""SMIC18 Class-D half bridge: both original TT temperatures and all loads."""
from __future__ import annotations
import argparse,shutil
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *
from hd_cells import extract_hd
from case21_highpsrr_bandgap import quota_guard

CASE=ROOT/'cases/01-class-d';TASK=SOURCE/'sky130-class-d-halfbridge-eff95-tt'
LOADS=[1,2,3,6,8,12,16];TEMPS=[27,125]
POINTS={f't{temp}_r{load}':(temp,load) for temp in TEMPS for load in LOADS}

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',TASK/'tests/utils.py',TASK/'tests/benches/tb_efficiency.spi',TASK/'environment/starter/testbench/tb_class_d_tt_1p80v_27c.spi']
    for src in files:
        dst=CASE/'source'/src.relative_to(TASK);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    write_json(CASE/'source_provenance.json',dict(task=str(TASK),captured_at=now(),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='SMIC18TT only, retain both original27/125C efficiency groups and all7loads (14points)',VDD_V=1.8,temperature_C=27,temperature_points_C=TEMPS,pin_order=['vss','vdd','clk_in','sw'],loads_ohm=LOADS,clock_Hz=5e6,clock_rise_s=2e-9,clock_fall_s=2e-9,clock_high_plateau_s=98e-9,clock_source_ohm=50,external_L_H=3e-6,external_C_F=345e-12,transient_stop_s=20e-6,measurement_window_s=[18e-6,20e-6],maximum_step_s=1e-9,pin_formula='abs(1.8*meanI_VDD)+abs(mean(VSS*I_VSS))+abs(mean(VCLK*I_VCLK)); all time weighted',pout_formula='abs(mean(V_RLnode*I_VMEAS_RL)); independent V_RL^2/R crosscheck',efficiency_min_strict=dict(peak_27=.95,all_27=.85,peak_125=.90,all_125=.80),output_power_min_strict_W=.03,output_power_guard_relaxable=False,sanity='finite P_in>0, P_out>0, eta<=1+1e-6, no relaxed function/polarity/model eligibility',allowed_DUT='native SMIC MOS/MIM and exact vendor HD cells only; no internal sources or ideal passives',scope_excludes=['otherprocesscorners','mismatch','otherloads/frequencies/duty cycles','layout/PEX','lifetime reliability signoff'],acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env.update(captured_at=now(),temperature_points_C=TEMPS,models=model_provenance());write_json(CASE/'environment.json',env)

def drive_role(model):
    p=ROOT/f'lut_supplement/tt/{model}_L180nm_VDS1.800_W50.000.json';j=json.loads(p.read_text());a=j['data'];ix=int(np.argmax(a['vgs_V']));assert abs(a['vgs_V'][ix]-1.8)<1e-10
    q=lut_size(model,.18,a['gmid'][ix],a['id_ref_A'][ix],1.8,width_ref_um=50);assert abs(q['rounded_W_um']-50)<1e-9
    q.update(selection='Full1.8V drive endpoint of actual W50um saturated sweep; Id is characterization current, not the circuit bias current',cgg_full_drive_F=a['cgg_ref_F'][ix]);return q

def cell(name,nodes,kind):return f'{name} ({nodes}) {kind}\n'

def design(p_m=2048,n_m=1024,delay_pf=.1,p_banks=8,n_banks=4,diffusion_um=.3):
    roles={'power_p':drive_role('p18'),'power_n':drive_role('n18')}
    extract_hd(['INHDV1','INHDV4','INHDV8','INHDV32','NAND2HDV1'],CASE)
    text='// Full native power devices and parameter-free exact HD hierarchy.\nsimulator lang=spectre\nsubckt bank4 (I O vdd vss)\n'
    for i in range(4):text+=cell(f'XB{i}','I O vdd vss vdd vss','INHDV32')
    text+='ends bank4\n\nsubckt delay4 (I O vdd vss)\n'
    for i in range(4):
        a='I' if i==0 else f'd{i}';b='O' if i==3 else f'd{i+1}'
        text+=cell(f'XD{i}',f'{a} {b} vdd vss vdd vss','INHDV1')
        text+=f'CD{i} ({b} vss) mim w=10u l={delay_pf/.00971:.10g}u\n'
    text+='ends delay4\n\nsubckt driver_p (I O vdd vss)\n'
    text+=cell('XP0','I a vdd vss vdd vss','INHDV4')+cell('XP1','a b vdd vss vdd vss','INHDV32')
    for i in range(2):text+=cell(f'XP2_{i}','b c vdd vss','bank4')
    for i in range(p_banks):text+=cell(f'XP3_{i}','c O vdd vss','bank4')
    text+='ends driver_p\n\nsubckt driver_n (I O vdd vss)\n'
    text+=cell('XN0','I a vdd vss vdd vss','INHDV8')+cell('XN1','a b vdd vss','bank4')
    for i in range(n_banks):text+=cell(f'XN2_{i}','b O vdd vss','bank4')
    text+='ends driver_n\n\nsubckt half_bridge (vss vdd clk_in sw)\n'
    for name,model,g,s,b,m in [('MP','p18','gp','vdd','vdd',p_m),('MN','n18','gn','vss','vss',n_m)]:
        # Keep each device's physical series resistance above default minr.
        # Splitting parallel groups preserves total geometry and model values.
        count=int(np.ceil(m/512));unit_m=m/count
        for k in range(count):
            text+=f'{name}{k} (sw {g} {s} {b}) {model} w=50u l=.18u m={unit_m:g} ad={50*diffusion_um:g}p as={50*diffusion_um:g}p pd={2*(50+diffusion_um):g}u ps={2*(50+diffusion_um):g}u\n'
    text+=cell('XINV','clk_in clkb vdd vss vdd vss','INHDV1')
    text+=cell('XHP','clk_in noffd poff vdd vss vdd vss','NAND2HDV1')+cell('XLN','clkb poffd noff vdd vss vdd vss','NAND2HDV1')
    text+=cell('XDP','poff poffd vdd vss','delay4')+cell('XDN','noff noffd vdd vss','delay4')
    text+=cell('XBP','poff gp vdd vss','driver_p')+cell('XBN','noff gn vdd vss','driver_n')+'ends half_bridge\n'
    (CASE/'circuit.scs').write_text(text)
    z=dict(generated_at=now(),parameters=dict(p_m=p_m,n_m=n_m,delay_pf=delay_pf,p_banks=p_banks,n_banks=n_banks,diffusion_um=diffusion_um),roles=roles,power_total_width_um=dict(p18=50*p_m,n18=50*n_m),diffusion_assumption='Each50um finger has0.3um source/drain extension; explicit AD/AS and perimeter. Geometry assumption only, no completed layout claim.',digital_policy='EveryHD MOS and model remains unmodified; drive strengths use parallel whole cells in parameter-free bank4. Four-stage P path is noninverting; three-stage N path inverts active-low noff.',rationale='gmID comes from full1.8V drive, with sameW50um characterization. Large m reduces conduction loss but increases gate/diffusion charge. Cross-coupled NAND and native-MIM loaded HD delays provide break-before-make control. Actual efficiency includes all VDD and50ohm clock source power; evaluate full load matrix.',circuit_sha256=sha(CASE/'circuit.scs'))
    write_json(CASE/'sizing.json',z)
    for q in roles.values():(CASE/'lut').mkdir(exist_ok=True);shutil.copy2(q['lut_path'],CASE/'lut'/Path(q['lut_path']).name)

def bench(label,step_ns=1,reltol=1e-5):
    temp,load=POINTS[label]
    text='simulator lang=spectre\nglobal 0\n'+''.join(f'include "{MODEL}" section={s}\n' for s in ['tt','mim_tt'])
    text+=f'''include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
VSS (vss 0) vsource dc=0
VDD (vdd vss) vsource dc=1.8
VCLK (clk_src vss) vsource type=pulse val0=0 val1=1.8 delay=0 rise=2n fall=2n width=98n period=200n
RCLK (clk_src clk_in) resistor r=50
X (vss vdd clk_in sw) half_bridge
L1 (sw lc_node) inductor l=3u
C1 (lc_node rl_node) capacitor c=345p
VMEAS_RL (rl_node rl_meas) vsource dc=0
RL (rl_meas vss) resistor r={load}
simulatorOptions options temp={temp} tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-12
saveOptions options save=selected
save vdd vss clk_src clk_in sw lc_node rl_node rl_meas VDD:p VSS:p VCLK:p VMEAS_RL:p X.gp X.gn X.poff X.noff X.poffd X.noffd
tran tran stop=20u maxstep={step_ns:g}n errpreset=conservative method=traponly
'''
    return text

def simulate(labels,step_ns=1,reltol=1e-5):
    cp=CASE/'circuit.scs';runs={}
    if (CASE/'latest_runs.json').exists():
        for k,p in json.loads((CASE/'latest_runs.json').read_text()).items():
            if json.loads((ROOT/p/'run.json').read_text())['dependencies'][str(cp)]['sha256']==sha(cp):runs[k]=p
    for label in labels:
        quota_guard();b=bench(label,step_ns,reltol);(CASE/f'testbench_{label}.scs').write_text(b)
        run=run_spectre(1,label,b,[cp,CASE/'hd_cells.scs',CASE/'hd_cells_manifest.json',CASE/'contract.json',CASE/'sizing.json'],temperature_C=POINTS[label][0],timeout=600)
        runs[label]=str(run.relative_to(ROOT));write_json(CASE/'latest_runs.json',runs)
    return runs

def measured(run,temp,load):
    d=data(run,'tran.tran');t=d['time'];mask=(t>18e-6)&(t<20e-6);tt=np.r_[18e-6,t[mask],20e-6]
    q={k:np.r_[np.interp(18e-6,t,v),v[mask],np.interp(20e-6,t,v)] for k,v in d.items() if k!='time'}
    avg=lambda a:float(np.trapz(a,tt)/(tt[-1]-tt[0]))
    vdd=abs(avg(1.8*q['VDD:p']));vss=abs(avg(q['vss']*q['VSS:p']));clk=abs(avg(q['clk_src']*q['VCLK:p']));pout=abs(avg(q['rl_node']*q['VMEAS_RL:p']));pin=vdd+vss+clk
    # L, C and VMEAS_RL are strictly in series; their currents are identical.
    vals=dict(temperature_C=temp,load_ohm=load,p_vdd_W=vdd,p_vss_W=vss,p_clk_W=clk,p_in_W=pin,p_out_W=pout,efficiency=pout/pin,p_out_square_W=avg(q['rl_meas']**2/load),window_points=len(tt),SW_min_V=float(min(q['sw'])),SW_max_V=float(max(q['sw'])),gp_min_V=float(min(q['X.gp'])),gp_max_V=float(max(q['X.gp'])),gn_min_V=float(min(q['X.gn'])),gn_max_V=float(max(q['X.gn'])),tank_energy_start_J=float(.5*3e-6*q['VMEAS_RL:p'][0]**2+.5*345e-12*(q['lc_node'][0]-q['rl_node'][0])**2),tank_energy_end_J=float(.5*3e-6*q['VMEAS_RL:p'][-1]**2+.5*345e-12*(q['lc_node'][-1]-q['rl_node'][-1])**2))
    assert pin>0 and pout>0 and 0<vals['efficiency']<=1+1e-6
    vals['tank_energy_rate_W']=(vals['tank_energy_end_J']-vals['tank_energy_start_J'])/2e-6
    return vals

def strict_min(value,limit,unit,relax=True):
    q=gate(value,limit,'min',unit,relax=relax);q['passes']={k:value>v for k,v in q['limits'].items()};q['strict']=True;return q

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());values={k:measured(ROOT/p,*POINTS[k]) for k,p in runs.items()};full=set(runs)==set(POINTS);gates={}
    if full:
        for temp,peak,minv in [(27,.95,.85),(125,.9,.8)]:
            eff=[q['efficiency'] for q in values.values() if q['temperature_C']==temp]
            gates[f'peak_{temp}']=strict_min(max(eff),peak,'ratio');gates[f'all_{temp}']=strict_min(min(eff),minv,'ratio')
        gates['minimum_output_power']=strict_min(min(q['p_out_W'] for q in values.values()),.03,'W',False)
    warnings={k:[w for w in json.loads((ROOT/p/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in w] for k,p in runs.items()};valid=not any(warnings.values())
    tiers={k:full and valid and all(g['passes'][k] for g in gates.values()) for k in ['original','10pct','15pct']};status=next(('complete_'+k for k,b in tiers.items() if b),'needs_iteration' if full else 'partial')
    r=dict(case_slot=1,generated_at=now(),status=status,values=values,gates=gates,pass_tiers=tiers,groups=runs,run_dirs=list(runs.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),all_nominal_checks_complete=full,model_dimensions_valid=True,model_operating_range_valid=valid,disallowed_model_warnings=warnings,scope=json.loads((CASE/'contract.json').read_text())['scope'])
    write_json(CASE/'latest_results.json',r)
    for k,q in values.items():print(k,'Pout_mW',round(q['p_out_W']*1e3,6),'Pin_mW',round(q['p_in_W']*1e3,6),'eff_pct',round(q['efficiency']*100,6),'SWrange',q['SW_min_V'],q['SW_max_V'])
    print('status',status,'model_valid',valid);return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--p-m',type=float,default=2048);p.add_argument('--n-m',type=float,default=1024);p.add_argument('--delay-pf',type=float,default=.1);p.add_argument('--p-banks',type=int,default=8);p.add_argument('--n-banks',type=int,default=4);p.add_argument('--diffusion-um',type=float,default=.3);p.add_argument('--run',nargs='+',default=list(POINTS));p.add_argument('--step-ns',type=float,default=1);p.add_argument('--reltol',type=float,default=1e-5);p.add_argument('--extract',action='store_true');a=p.parse_args()
    if a.extract:extract();raise SystemExit(0)
    quota_guard()
    if not (CASE/'contract.json').exists():freeze()
    design(a.p_m,a.n_m,a.delay_pf,a.p_banks,a.n_banks,a.diffusion_um);update_case(1,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))
    simulate(a.run,a.step_ns,a.reltol);extract()
