"""Native-device two-phase voltage pump with original nominal time windows."""
from __future__ import annotations
import argparse,shutil
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *
from case21_highpsrr_bandgap import quota_guard
from hd_cells import extract_hd

CASE=ROOT/'cases/15-unregulated-pump';TASK=SOURCE/'sky130-unregulated-charge-pump-10mhz-pvt'

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',TASK/'tests/utils.py',TASK/'environment/starter/SKY130_NETLIST_GUIDE.md',*sorted((TASK/'tests/benches').glob('*.spi'))]
    for src in files:
        dst=CASE/'source'/src.relative_to(TASK);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    write_json(CASE/'source_provenance.json',dict(captured_at=now(),task=str(TASK),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='SMIC18 TT/1.8V/40C nominal representative point; independent enabled/disabled benches',VDD_V=1.8,temperature_C=40,pin_order=['AVDD','AVSS','CLK','EN','VOUT'],clock_Hz=1e7,clock_initial_V=1.8,clock_low_V=0,clock_edge_s=1e-12,clock_low_plateau_s=50e-9,clock_period_s=100e-9,clock_and_enable_source_ohm=50,enabled_load_A=50e-6,disabled_load_A=0,external_output_F=1e-9,enabled_stop_s=200e-6,enabled_window_s=[190e-6,200e-6],disabled_stop_s=10e-6,disabled_window_s=[9e-6,10e-6],disabled_enable_from_time_zero=True,disabled_clock_keeps_running=True,output_center_V=2.5,output_error_max_V=.3,ripple_max_V=.005,enabled_current_max_A=200e-6,disabled_current_max_A=100e-9,current_definition='absolute value of time-average VDD sense current, separate runs',allowed_DUT='native SMIC MOS and MIM; exact unmodified HD cells; no ideal R/C or internal sources',terminal_screen_V={'n33':3.63,'nnt33':3.63,'n18':1.98,'p18':1.98},terminal_screen_interpretation='non-relaxable engineering 110percent nominal-terminal screen; not a foundry lifetime signoff rating',exclusions=['other7representative PVT points','full Cartesian PVT','mismatch','efficiency','behavior after200us','layout/PEX'],acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env.update(captured_at=now(),temperature_C=40,models=model_provenance());write_json(CASE/'environment.json',env)

def design(cap_pf=5,gm_id=6,current_uA=250,cell='INHDV16',model='nnt33',length=1,pre_model='nnt33',clamp_uA=0,pre_current_uA=50):
    roles={'transfer':lut_size(model,length,gm_id,current_uA*1e-6,1.8)};q=roles['transfer'];w=q['rounded_W_um'];pre=lut_size('n33',.36,8,250e-6,1.8) if pre_model=='n33' else lut_size('nnt33',1,6,pre_current_uA*1e-6,1.8);roles['precharge']=pre;cl=lut_size('n33',.36,8,clamp_uA*1e-6,1.8) if clamp_uA else None
    if cl:roles['clamp']=cl
    hd=extract_hd(['NAND2HDV1',cell],CASE)
    net=f'''// Native thick-oxide charge transfer and unmodified HD clock logic.
simulator lang=spectre
subckt charge_pump_unregulate (AVDD AVSS CLK EN VOUT)
XEN (CLK EN gated AVDD AVSS AVDD AVSS) NAND2HDV1
XPH0 (gated ph0 AVDD AVSS AVDD AVSS) {cell}
XPH1 (ph0 ph1 AVDD AVSS AVDD AVSS) {cell}
CF0 (p0 ph0) mim w=100u l={cap_pf/.0971:.10g}u
CF1 (p1 ph1) mim w=100u l={cap_pf/.0971:.10g}u
MPRE0 (AVDD p1 p0 AVSS) {pre['model']} w={pre['rounded_W_um']:g}u l={pre['L_um']:g}u
MPRE1 (AVDD p0 p1 AVSS) {pre['model']} w={pre['rounded_W_um']:g}u l={pre['L_um']:g}u
MRECT0 (VOUT p0 p0 AVSS) {model} w={w:g}u l={length:g}u
MRECT1 (VOUT p1 p1 AVSS) {model} w={w:g}u l={length:g}u
ends charge_pump_unregulate
'''
    if cl:
        extra=''.join(f'MCL{k} (p{k} p{k} AVDD AVSS) n33 w={cl["rounded_W_um"]:g}u l=.36u\n' for k in range(2))
        net=net.replace('ends charge_pump_unregulate',extra+'ends charge_pump_unregulate')
    (CASE/'circuit.scs').write_text(net)
    write_json(CASE/'sizing.json',dict(generated_at=now(),parameters=dict(cap_pf=cap_pf,gm_id=gm_id,current_uA=current_uA,cell=cell,model=model,length=length,pre_model=pre_model,clamp_uA=clamp_uA,pre_current_uA=pre_current_uA),roles=roles,physical_capacitance=dict(model='mim',nominal_each_pF=cap_pf,plate_area_um2_total=2*cap_pf/.000971),rationale='Final low-threshold thick-oxide nnt33 uses narrower precharge than rectifier devices to reduce reverse transfer and parasitic loading; gmID lookup at27C gives initial transfer width, actual contract at40C including body effect. Opposite boosted gate precharges each flying node; diode-connected NMOS rectifies to output. Final dynamic current, loss, ripple and terminal ranges are measured. Exact HD NAND/IN cells provide enable gating and complementary bottom-plate clocks.',circuit_sha256=sha(CASE/'circuit.scs')))
    for q in roles.values():
        (CASE/'lut').mkdir(exist_ok=True);shutil.copy2(q['lut_path'],CASE/'lut'/Path(q['lut_path']).name)

def bench(kind,step_ns=1,reltol=1e-5,method='gear2only'):
    enabled=kind=='enabled';stop=200e-6 if enabled else 10e-6
    text='simulator lang=spectre\nglobal 0\n'+''.join(f'include "{MODEL}" section={s}\n' for s in ['tt','mim_tt'])
    text+=f'''include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
VDD (vsrc 0) vsource dc=1.8
VSENSE (vsrc AVDD) vsource dc=0
VCLK (clksrc 0) vsource type=pulse val0=1.8 val1=0 delay=0 rise=1p fall=1p width=50n period=100n
RCLK (clksrc CLK) resistor r=50
VEN (ensrc {'vsrc' if enabled else '0'}) vsource dc=0
REN (ensrc EN) resistor r=50
X (AVDD 0 CLK EN VOUT) charge_pump_unregulate
CLOAD (VOUT 0) capacitor c=1n
'''
    if enabled:text+='ILOAD (VOUT 0) isource dc=50u\n'
    text+=f'''simulatorOptions options temp=40 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14
saveOptions options save=selected
save AVDD VOUT CLK EN clksrc ensrc VDD:p VSENSE:p X.p0 X.p1 X.ph0 X.ph1 X.gated
tran tran stop={stop:g} maxstep={step_ns:g}n errpreset=conservative method={method} {'skipstart=2u skipstop=180u skipcount=100' if enabled else ''}
'''
    return text

def window(d,start,stop):
    t=d['time'];mask=(t>start)&(t<stop);xx=np.r_[start,t[mask],stop]
    return xx,{k:np.r_[np.interp(start,t,a),a[mask],np.interp(stop,t,a)] for k,a in d.items() if k!='time'}

def simulate(kinds,step_ns=1,reltol=1e-5,method='gear2only'):
    cp=CASE/'circuit.scs';runs={}
    if (CASE/'latest_runs.json').exists():
        for k,p in json.loads((CASE/'latest_runs.json').read_text()).items():
            if json.loads((ROOT/p/'run.json').read_text())['dependencies'][str(cp)]['sha256']==sha(cp):runs[k]=p
    for kind in kinds:
        quota_guard();b=bench(kind,step_ns,reltol,method);(CASE/f'testbench_{kind}.scs').write_text(b)
        run=run_spectre(15,kind,b,[cp,CASE/'hd_cells.scs',CASE/'hd_cells_manifest.json',CASE/'contract.json',CASE/'sizing.json'],temperature_C=40,timeout=600)
        runs[kind]=str(run.relative_to(ROOT));write_json(CASE/'latest_runs.json',runs)
    return runs

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());waves={k:data(ROOT/r,'tran.tran') for k,r in runs.items()};assert set(waves)=={'enabled','disabled'}
    te,e=window(waves['enabled'],190e-6,200e-6);td,d=window(waves['disabled'],9e-6,10e-6)
    avg=lambda t,v:float(np.trapz(v,t)/(t[-1]-t[0]))
    v=dict(vout_en_avg=avg(te,e['VOUT']),vout_en_max=float(max(e['VOUT'])),vout_en_min=float(min(e['VOUT'])),i_avdd_en_avg=avg(te,e['VSENSE:p']),i_avdd_pd_avg=avg(td,d['VSENSE:p']))
    v.update(output_error_V=abs(v['vout_en_avg']-2.5),ripple_V=v['vout_en_max']-v['vout_en_min'],enabled_current_A=abs(v['i_avdd_en_avg']),disabled_current_A=abs(v['i_avdd_pd_avg']))
    tl,el=window(waves['enabled'],199.9e-6,200e-6);v['output_last_cycle_mean_V']=avg(tl,el['VOUT'])
    gates={'output_error':gate(v['output_error_V'],.3,'max','V'),'ripple':gate(v['ripple_V'],.005,'max','Vpp'),'enabled_current':gate(v['enabled_current_A'],200e-6,'max','A'),'disabled_current':gate(v['disabled_current_A'],100e-9,'max','A')}
    terminal={}
    for kind,wave in waves.items():
        get=lambda n:np.zeros(len(wave['time'])) if n=='AVSS' else wave.get(n,wave.get('X.'+n))
        rows=[]
        for name,nodes,model in re.findall(r'^(M\w+)\s+\(([^)]+)\)\s+(\w+)',(CASE/'circuit.scs').read_text(),re.M):
            dv,gv,sv,bv=map(get,nodes.split());peaks={label:float(np.max(abs(a-b))) for label,a,b in [('VGS',gv,sv),('VGD',gv,dv),('VDS',dv,sv),('VGB',gv,bv),('VDB',dv,bv),('VSB',sv,bv)]};rows.append(dict(name=name,model=model,peaks_V=peaks))
        terminal[kind]=rows
    valid=all(max(x['peaks_V'].values())<=3.63 for rows in terminal.values() for x in rows)
    model_warnings={k:[w for w in json.loads((ROOT/p/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in w] for k,p in runs.items()}
    model_valid=not any(model_warnings.values())
    tiers={tier:all(g['passes'][tier] for g in gates.values()) and valid and model_valid for tier in ['original','10pct','15pct']};status=next(('complete_'+k for k,b in tiers.items() if b),'needs_iteration')
    r=dict(case_slot=15,generated_at=now(),status=status,values=v,gates=gates,pass_tiers=tiers,groups=runs,run_dirs=list(runs.values()),terminal_voltages=terminal,terminal_screen_valid=valid,circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),all_nominal_checks_complete=True,model_dimensions_valid=True,model_operating_range_valid=model_valid,disallowed_model_warnings=model_warnings,scope=json.loads((CASE/'contract.json').read_text())['scope'])
    write_json(CASE/'latest_results.json',r);print(json.dumps(dict(status=status,values=v,terminal_screen_valid=valid,terminal_max_V=max(max(x['peaks_V'].values()) for rows in terminal.values() for x in rows)),indent=2));return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cap-pf',type=float,default=5);p.add_argument('--gm-id',type=float,default=6);p.add_argument('--current-uA',type=float,default=250);p.add_argument('--cell',default='INHDV16');p.add_argument('--model',default='nnt33');p.add_argument('--length',type=float,default=1);p.add_argument('--pre-model',default='nnt33');p.add_argument('--clamp-uA',type=float,default=0);p.add_argument('--pre-current-uA',type=float,default=50);p.add_argument('--step-ns',type=float,default=1);p.add_argument('--reltol',type=float,default=1e-5);p.add_argument('--method',default='gear2only');p.add_argument('--run',nargs='+',default=['enabled','disabled']);p.add_argument('--extract',action='store_true');a=p.parse_args()
    if a.extract:extract();raise SystemExit(0)
    quota_guard()
    if not (CASE/'contract.json').exists():freeze()
    design(a.cap_pf,a.gm_id,a.current_uA,a.cell,a.model,a.length,a.pre_model,a.clamp_uA,a.pre_current_uA);update_case(15,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))
    runs=simulate(a.run,a.step_ns,a.reltol,a.method)
    if set(runs)=={'enabled','disabled'}:extract()
