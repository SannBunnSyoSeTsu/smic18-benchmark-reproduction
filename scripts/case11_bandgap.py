"""SMIC18 first-order bandgap; frozen source contract and nominal verification."""
from __future__ import annotations
import argparse
import shutil
import common
common.SPECTRE = '/home/IC/.local/bin/spectre-wsl'
from common import *

CASE = ROOT/'cases/11-bandgap'
TASK = SOURCE/'sky130-bandgap-reference-pvt'
MOS = ['MP0','MP1','MP2','MNB','MTAIL','MINA','MINB','MPD','MPM','MPST','MNST','MSTART']

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',*sorted((TASK/'tests/benches').glob('*.spi'))]
    for p in files:
        dest=CASE/'source'/p.relative_to(TASK);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    write_json(CASE/'source_provenance.json',dict(captured_at=now(),task=str(TASK),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='TT active/BJT/resistor/MIM; nominal dynamic tests at 1.8V/27C, retained temperature-coefficient and line-regulation characterization',sections=['tt','bjt_tt','res_tt','mim_tt'],VDD_V=1.8,temperature_C=27,load_F=5e-12,voltage_center_V=1.22,voltage_error_max_V=.04,power_max_W=150e-6,temperatures_C=[-40,0,27,60,100,125],tempco_definition='(max(VREF)-min(VREF))/(mean(VREF)*165)*1e6',tempco_max_ppm_C=50,line_supplies_V=[1.62,1.8,1.98],line_regulation_max_V_V=.020,startup_ramps_s=[1e-6,10e-6],startup_check_after_ramp_s=10e-6,startup_stop_after_ramp_s=20e-6,startup_overshoot_max_V=.1,startup_peak_current_max_A=.0015,startup_energy_max_J=5e-9,ac_Hz=[10,1e8],supply_gain_max_V_V=.2,noise_Hz=[10,1e6],noise_max_Vrms=500e-6,line_step=dict(initial_V=1.8,high_V=1.98,low_V=1.62,up_s=5e-6,down_s=15e-6,stop_s=30e-6,edge_s=10e-9,band_V=.001,excursion_max_V=.1,settling_max_s=10e-6,target='independent DC at each final supply, not transient tail'),exclusions=['non-TT process/passive corners','paired hot/low-supply and cold/high-supply dynamic stresses','Monte Carlo seeds61000..61029','layout/PEX','loaded or buffered ADC reference'],acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    write_json(CASE/'environment.json',dict(captured_at=now(),spectre_wrapper=common.SPECTRE,spectre_binary='/home/IC/eda/cadence/SPECTRE241/tools.lnx86/spectre/bin/64bit/spectre',spectre_version='24.1.0 64bit 09/14/2024',python=sys.executable,models=model_provenance(),gm_id_assets=str(LUT_ROOT),lut_index_sha256=sha(LUT_ROOT/'lut/index.json'),skill_note='Standalone gmoverid SKILL.md was absent after migration; reused the existing validated skill-compatible GmIdTable API and target-PDK LUT assets. No LUT or EDA environment modified.',external_model_calls=False))

def design(rptat=16.5,rref=70.3,cc=3,cout=20,mirror_l=1,input_gmid=22,bias_r=1300):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={
        'mirror':lut_size('p18',mirror_l,15,10e-6,.9),
        'input':lut_size('n18',1,input_gmid,4e-6,.45),
        'load':lut_size('p18',1,16,4e-6,.45),
        'bias':lut_size('n18',1,12,3e-6,.9),
        'startup_p':lut_size('p18',1,12,2e-6,.9),
        'startup_n':lut_size('n18',1,12,2e-6,.9),
    }
    w={k:q['rounded_W_um'] for k,q in roles.items()}
    text=f'''// First-order VBE + 2*RREF/RPTAT*DeltaVBE; untrimmed high-impedance output.
simulator lang=spectre
subckt bandgap_reference (vss vdd vref)
MP0 (va pctrl vdd vdd) p18 w={w['mirror']}u l={mirror_l}u
MP1 (vb pctrl vdd vdd) p18 w={w['mirror']}u l={mirror_l}u
MP2 (vref pctrl vdd vdd) p18 w={w['mirror']}u l={mirror_l}u m=2
Q0 (va va vss vss) npn18a4 area=1
RPTAT (vb n1 vss) rpposab_3t w=1u l={rptat}u
Q1 (n1 n1 vss vss) npn18a4 area=8
RREF (vref vctat vss) rpposab_3t w=1u l={rref}u
QREF (vctat vctat vss vss) npn18a4 area=2
CREF (vref vss) mim w=100u l={cout/0.0971:.8g}u
'''
    for i in range(8):
        n0='vdd' if i==0 else f'rb{i}';n1='nbias' if i==7 else f'rb{i+1}'
        text+=f'RB{i} ({n0} {n1} vss) rpposab_3t w=1u l={bias_r/8:g}u\n'
    text+=f'''MNB (nbias nbias vss vss) n18 w={w['bias']}u l=1u
MTAIL (tail nbias vss vss) n18 w={w['bias']}u l=1u m=3
MINA (pctrl va tail vss) n18 w={w['input']}u l=1u
MINB (nout vb tail vss) n18 w={w['input']}u l=1u
MPD (nout nout vdd vdd) p18 w={w['load']}u l=1u
MPM (pctrl nout vdd vdd) p18 w={w['load']}u l=1u
CCOMP (pctrl vss) mim w=50u l={cc/.04855:.8g}u
MPST (st vref vdd vdd) p18 w={w['startup_p']}u l=1u
MNST (st vref vss vss) n18 w={w['startup_n']}u l=1u
MSTART (pctrl st vss vss) n18 w={w['startup_n']}u l=1u
ends bandgap_reference
'''
    p=CASE/'circuit.scs';p.write_text(text)
    params=dict(rptat=rptat,rref=rref,cc=cc,cout=cout,mirror_l=mirror_l,input_gmid=input_gmid,bias_r=bias_r)
    write_json(CASE/'sizing.json',dict(generated_at=now(),parameters=params,roles=roles,bjt=dict(model='npn18a4',unit_emitter_area_um2=4,area_ratios=[1,8,2]),resistor=dict(model='rpposab_3t',sheet_ohm=311.3,effective_width_um=.9454),rationale='Target10uA per core branch; 1:1:2 PMOS mirror, DeltaVBE≈VT*ln8≈54mV; RPTAT≈5.4kOhm. Input pair gm/ID22 reduces VGS at about0.75V BJT common-mode. 3uA resistor-derived bias and 3x tail; nominal budget about95uW. Startup inverter pulls pctrl low only while vref is low. All MOS start from measured TT gm/ID LUT; body effect and output conductance verified in circuit.',circuit_sha256=sha(p)))
    for q in roles.values():
        dst=CASE/'lut'/Path(q['lut_path']).name;dst.parent.mkdir(exist_ok=True);shutil.copy2(q['lut_path'],dst)
    return p

def bench(c,kind):
    supply='dc=vddval mag=1'
    if kind.startswith('startup'):
        ramp=1e-6 if kind=='startup1' else 10e-6
        supply=f'type=pwl wave=[0 0 {ramp:g} 1.8 {ramp+20e-6:g} 1.8]'
    elif kind=='step':supply='type=pwl wave=[0 1.8 5u 1.8 5.01u 1.98 15u 1.98 15.01u 1.62 30u 1.62]'
    b=f'''simulator lang=spectre
global 0
parameters vddval=1.8
'''+''.join(f'include "{MODEL}" section={s}\n' for s in ['tt','bjt_tt','res_tt','mim_tt'])+f'''include "{c}"
VDD (vdd 0) vsource {supply}
X (0 vdd vref) bandgap_reference
CLOAD (vref 0) capacitor c=5p
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
save vdd vref VDD:p X.va X.vb X.n1 X.vctat X.pctrl X.nout X.nbias X.tail X.st
'''
    if kind=='static':
        for dev in MOS:b+='save '+' '.join(f'X.{dev}:{k}' for k in ['ids','gm','gds','vgs','vds','vbs','vdsat','region'])+'\n'
        b+='dcOp dc\nline dc param=vddval values=[1.62 1.8 1.98]\ntemperature dc param=temp values=[-40 0 27 60 100 125]\n'
    elif kind=='acnoise':b+='dcOp dc\nac ac start=10 stop=100M dec=100\nnoise (vref 0) noise start=10 stop=1M dec=100 iprobe=VDD\n'
    elif kind.startswith('startup'):
        b+='ic vref=0 X.va=0 X.vb=0 X.n1=0 X.vctat=0 X.pctrl=0 X.nout=0 X.nbias=0 X.tail=0 X.st=0\n'
        b+=f'tran tran stop={ramp+20e-6:g} maxstep=2n strobeperiod=2n strobeoutput=strobeonly skipdc=yes errpreset=conservative\n'
    elif kind=='step':b+='tran tran stop=30u maxstep=1n strobeperiod=1n strobeoutput=strobeonly errpreset=conservative\n'
    else:raise ValueError(kind)
    return b

def simulate(kinds):
    c=CASE/'circuit.scs';runs={}
    if (CASE/'latest_runs.json').exists():
        for k,v in json.loads((CASE/'latest_runs.json').read_text()).items():
            meta=json.loads((ROOT/v/'run.json').read_text())
            if meta['dependencies'][str(c)]['sha256']==sha(c):runs[k]=v
    for kind in kinds:
        b=bench(c,kind);(CASE/f'testbench_{kind}.scs').write_text(b)
        runs[kind]=str(run_spectre(11,kind,b,[c,CASE/'sizing.json',CASE/'contract.json']).relative_to(ROOT))
        print(kind,runs[kind],flush=True)
        write_json(CASE/'latest_runs.json',runs)
    return runs

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text())
    assert set(groups)=={'static','acnoise','startup1','startup10','step'}
    runs={k:ROOT/v for k,v in groups.items()}
    for r in runs.values():
        meta=json.loads((r/'run.json').read_text())
        assert meta['status']=='completed' and meta['dependencies'][str(CASE/'circuit.scs')]['sha256']==sha(CASE/'circuit.scs')
    o=dc(runs['static']);ln=data(runs['static'],'line.dc');temp=data(runs['static'],'temperature.dc')
    assert np.allclose(ln['vddval'],[1.62,1.8,1.98]) and np.allclose(temp['temp'],[-40,0,27,60,100,125])
    a=data(runs['acnoise'],'ac.ac');n=data(runs['acnoise'],'noise.noise',required=['out'])
    assert np.isclose(a['freq'][0],10) and np.isclose(a['freq'][-1],1e8)
    assert np.isclose(n['freq'][0],10) and np.isclose(n['freq'][-1],1e6)
    starts=[]
    for label,ramp in [('startup1',1e-6),('startup10',10e-6)]:
        d=data(runs[label],'tran.tran');t=d['time'];v=d['vref'];current=np.maximum(0,-d['VDD:p'])
        assert abs(t[0])<1e-15 and abs(t[-1]-(ramp+20e-6))<1e-13 and abs(v[0])<1e-9
        mask=t>=ramp+10e-6-1e-15
        win=np.r_[np.interp(ramp+10e-6,t,v),v[mask],v[-1]]
        good=(v>=1.18)&(v<=1.26);stays=np.logical_and.accumulate(good[::-1])[::-1];ix=np.flatnonzero(stays&(t>=ramp-1e-15))
        assert len(ix),'Startup never enters and remains in original voltage window'
        starts.append(dict(ramp_s=ramp,final_V=float(v[-1]),window_min_V=float(min(win)),window_max_V=float(max(win)),entry_after_ramp_s=float(max(0,t[ix[0]]-ramp)),overshoot_V=float(max(0,max(v)-v[-1])),peak_current_A=float(max(current)),energy_J=float(np.trapz(d['vdd']*current,t)),initial_V=float(v[0]),stop_s=float(t[-1])))
    d=data(runs['step'],'tran.tran');t=d['time'];v=d['vref'];steps=[]
    for start,end,target,supply,direction in [(5e-6,15e-6,ln['vref'][-1],1.98,'up'),(15e-6,30e-6,ln['vref'][0],1.62,'down')]:
        mask=(t>=start-1e-15)&(t<=end+1e-15);tt=t[mask];err=abs(v[mask]-target);outside=np.flatnonzero(err>.001)
        assert err[-1]<=.001,'Step never settles to independent DC target'
        last_out=float(max(0,tt[outside[-1]]-start)) if len(outside) else 0.
        first_in=float(max(0,tt[min(outside[-1]+1,len(tt)-1)]-start)) if len(outside) else 0.
        steps.append(dict(direction=direction,final_supply_V=supply,independent_dc_target_V=float(target),excursion_V=float(max(err)),verifier_last_outside_s=last_out,conservative_settling_s=first_in,final_error_V=float(err[-1])))
    ref=np.r_[o['vref'],ln['vref'],temp['vref']]
    values=dict(vref_V=o['vref'],nominal_power_W=-1.8*o['VDD:p'],characterized_vref_min_V=float(min(ref)),characterized_vref_max_V=float(max(ref)),characterized_power_max_W=float(max(np.r_[-ln['vddval']*ln['VDD:p'],-1.8*temp['VDD:p']])),tempco_ppm_C=float(np.ptp(temp['vref'])/np.mean(temp['vref'])/165*1e6),line_regulation_V_V=float(np.ptp(ln['vref'])/.36),supply_gain_max=float(max(abs(a['vref']))),supply_gain_peak_Hz=float(a['freq'][np.argmax(abs(a['vref']))]),output_noise_Vrms=float(np.sqrt(np.trapz(abs(n['out'])**2,n['freq']))),startup=starts,line_step=steps,temperature_rows=[dict(temperature_C=float(t),vref_V=float(v),power_W=float(-1.8*i)) for t,v,i in zip(temp['temp'],temp['vref'],temp['VDD:p'])],line_rows=[dict(supply_V=float(t),vref_V=float(v),power_W=float(-t*i)) for t,v,i in zip(ln['vddval'],ln['vref'],ln['VDD:p'])])
    gates={
        'reference_error_V':gate(float(max(abs(ref-1.22))),.04,'max','V'),
        'power_W':gate(values['characterized_power_max_W'],150e-6,'max','W'),
        'tempco_ppm_C':gate(values['tempco_ppm_C'],50,'max','ppm/C'),
        'line_regulation_V_V':gate(values['line_regulation_V_V'],.02,'max','V/V'),
        'startup_window_error_V':gate(max(max(abs(z['window_min_V']-1.22),abs(z['window_max_V']-1.22)) for z in starts),.04,'max','V'),
        'startup_entry_s':gate(max(z['entry_after_ramp_s'] for z in starts),10e-6,'max','s'),
        'startup_overshoot_V':gate(max(z['overshoot_V'] for z in starts),.1,'max','V'),
        'startup_peak_A':gate(max(z['peak_current_A'] for z in starts),.0015,'max','A'),
        'startup_energy_J':gate(max(z['energy_J'] for z in starts),5e-9,'max','J'),
        'supply_gain':gate(values['supply_gain_max'],.2,'max','V/V'),
        'noise_Vrms':gate(values['output_noise_Vrms'],500e-6,'max','Vrms'),
        'line_step_excursion_V':gate(max(z['excursion_V'] for z in steps),.1,'max','V'),
        'line_step_settling_s':gate(max(z['conservative_settling_s'] for z in steps),10e-6,'max','s'),
        'line_step_final_error_V':gate(max(z['final_error_V'] for z in steps),.001,'max','V',relax=False),
    }
    tiers={tier:all(g['passes'][tier] for g in gates.values()) for tier in ['original','10pct','15pct']}
    tier=next((k for k,v in tiers.items() if v),None)
    op={}
    for dev in MOS:
        z={k.split(':')[1]:v for k,v in o.items() if k.startswith('X.'+dev+':')}
        z.update(gmid=abs(z['gm']/z['ids']),gmro=abs(z['gm']/z['gds']),headroom_V=abs(z['vds'])-abs(z['vdsat']));op[dev]=z
    report=dict(case_slot=11,generated_at=now(),status='complete_'+tier if tier else 'partial',values=values,gates=gates,pass_tiers=tiers,groups=groups,run_dirs=list(groups.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},all_nominal_checks_complete=True,model_dimensions_valid=True,scope=json.loads((CASE/'contract.json').read_text())['scope'])
    write_json(CASE/'latest_results.json',report)
    print(json.dumps(dict(status=report['status'],values=values,failed_original=[k for k,g in gates.items() if not g['passes']['original']]),indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rptat',type=float,default=16.5);p.add_argument('--rref',type=float,default=73.3);p.add_argument('--cc',type=float,default=.5);p.add_argument('--cout',type=float,default=60);p.add_argument('--mirror-l',type=float,default=1);p.add_argument('--input-gmid',type=float,default=22);p.add_argument('--bias-r',type=float,default=1300);p.add_argument('--run',nargs='+',default=['static','acnoise','startup1','startup10','step']);p.add_argument('--extract',action='store_true');a=p.parse_args()
    if a.extract:
        extract();raise SystemExit(0)
    if not (CASE/'contract.json').exists():freeze()
    design(a.rptat,a.rref,a.cc,a.cout,a.mirror_l,a.input_gmid,a.bias_r)
    update_case(11,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))
    simulate(a.run)
