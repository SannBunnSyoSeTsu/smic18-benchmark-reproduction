"""SMIC18 high-PSRR bandgap, independently verified with the case21 contract."""
from __future__ import annotations
import argparse
import shutil
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *

CASE=ROOT/'cases/21-highpsrr-bandgap'
TASK=SOURCE/'sky130-high-psrr-bandgap-reference-pvt'
MONITOR=ROOT/'monitor/weekly-20260926-continue'
MOS=['MP0','MP1','MP2','MNB','MTAIL','MINA','MINB','MPD','MPM','MPST','MNST','MSTART']

def mos_devices():
    return re.findall(r'^(M\w+)\s+\(', (CASE/'circuit.scs').read_text(),re.M)

def quota_guard():
    if (MONITOR/'TRIGGER.json').exists():raise RuntimeError('User quota stop triggered: '+(MONITOR/'TRIGGER.json').read_text())
    state=json.loads((MONITOR/'STATE.json').read_text())
    assert state['status']=='ok' and state['windowDurationMins']==10080
    age=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(state['observedAt'])).total_seconds()
    assert age<120 and state['remainingPercent']>=5,('Quota sample stale or below threshold',age,state)

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',TASK/'tests/utils.py',TASK/'environment/starter/SKY130_NETLIST_GUIDE.md',*sorted((TASK/'tests/benches').glob('*.spi'))]
    for src in files:
        dst=CASE/'source'/src.relative_to(TASK);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    write_json(CASE/'source_provenance.json',dict(captured_at=now(),task=str(TASK),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='SMIC18 TT nominal representative point; retain full1C-step temperature characterization at1.8V',VDD_V=1.8,temperature_C=27,load_F=1e-12,sections=['tt','bjt_tt','res_tt','mim_tt'],pin_order=['AVDD','AVSS','VBG','SUB'],reference_center_V=1.2,reference_error_max_V=.15,temperature_sweep=dict(start_C=-40,stop_C=85,step_C=1,mean='trapezoidal temperature average, matching original .measure dc AVG'),tempco_max_ppm_C=50,ac=dict(start_Hz=.01,stop_Hz=1e8,points_per_decade=40,excitation_V=1,low_frequency_Hz=.01,nominal_low_gain_max_dB=-60,one_MHz_gain_max_dB=-30),startup=dict(ramp_s=1e-6,stop_s=100e-6,average_window_s=[90e-6,100e-6],error_max_fraction=.01,target='independent DC at27C from the temperature sweep',initial_supply_V=0),power_limit_W=None,allowed_DUT='native SMIC MOS, BJT and physical passives only; no ideal source or ideal R/C',exclusions=['other3representative PVT points','full Cartesian PVT','mismatch','noise','layout/PEX','loaded/buffered reference'],acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env['captured_at']=now();env['models']=model_provenance()
    write_json(CASE/'environment.json',env)

def design(rref=73.3,cc=.5,cout=60,filter_c=20,filter_r=30,core_l=4,amp_l=4,cascode=1,self_bias=1):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={
      'mirror':lut_size('p18',core_l,15,5e-6,.9),
      'input':lut_size('n18',amp_l,22,4e-6,.9 if amp_l==4 else .45),
      'load':lut_size('p18',amp_l,16,4e-6,.9 if amp_l==4 else .45),
      'bias':lut_size('n18',4,12,3e-6,.9),
      'startup_p':lut_size('p18',1,12,2e-6,.9),
      'startup_n':lut_size('n18',1,12,2e-6,.9)}
    if cascode:
        roles['cascode']=lut_size('p18',1,15,10e-6,.9)
        roles['cascode_bias']=lut_size('p18',1,5,3e-6,.9)
    if self_bias:
        assert cascode
        roles['amp_bias_mirror']=lut_size('p18',core_l,15,3e-6,.9)
        roles['amp_bias_cascode']=lut_size('p18',1,15,3e-6,.9)
    w={k:z['rounded_W_um'] for k,z in roles.items()}
    core_nodes=['pc0','pc1','pc2'] if cascode else ['va','vb','vcore']
    text=f'''// Long-channel closed-loop bandgap plus physical RC output isolation.
simulator lang=spectre
subckt bandgap (AVDD AVSS VBG SUB)
MP0 ({core_nodes[0]} pctrl AVDD AVDD) p18 w={w['mirror']}u l={core_l}u m=2
MP1 ({core_nodes[1]} pctrl AVDD AVDD) p18 w={w['mirror']}u l={core_l}u m=2
MP2 ({core_nodes[2]} pctrl AVDD AVDD) p18 w={w['mirror']}u l={core_l}u m=4
Q0 (va va AVSS SUB) npn18a4 area=1
RPTAT (vb n1 SUB) rpposab_3t w=1u l=16.5u
Q1 (n1 n1 AVSS SUB) npn18a4 area=8
RREF (vcore vctat SUB) rpposab_3t w=1u l={rref}u
QREF (vctat vctat AVSS SUB) npn18a4 area=2
CCORE (vcore AVSS) mim w=100u l={cout/.0971:.8g}u
RFILT (vcore VBG SUB) rpposab_3t w=1u l={filter_r}u
CFILT (VBG AVSS) mim w=100u l={filter_c/.0971:.8g}u
'''
    if cascode:
        for i,(node,m) in enumerate([('va',1),('vb',1),('vcore',2)]):
            text+=f'MPC{i} ({node} cbias pc{i} AVDD) p18 w={w["cascode"]}u l=1u m={m}\n'
        text+=f'MPCB (cbias cbias AVDD AVDD) p18 w={w["cascode_bias"]}u l=1u\n'
        for i in range(5):
            a='cbias' if i==0 else f'rcb{i}';b='AVSS' if i==4 else f'rcb{i+1}'
            text+=f'RCB{i} ({a} {b} SUB) rpposab_3t w=1u l=200u\n'
    if self_bias:
        text+=f'MPA (namp pctrl AVDD AVDD) p18 w={w["amp_bias_mirror"]}u l={core_l}u\n'
        text+=f'MPCA (nbias cbias namp AVDD) p18 w={w["amp_bias_cascode"]}u l=1u\n'
    else:
        for i in range(8):
            a='AVDD' if i==0 else f'rb{i}';b='nbias' if i==7 else f'rb{i+1}'
            text+=f'RB{i} ({a} {b} SUB) rpposab_3t w=1u l=162.5u\n'
    text+=f'''MNB (nbias nbias AVSS AVSS) n18 w={w['bias']}u l=4u
MTAIL (tail nbias AVSS AVSS) n18 w={w['bias']}u l=4u m=3
MINA (pctrl va tail AVSS) n18 w={w['input']}u l={amp_l}u
MINB (nout vb tail AVSS) n18 w={w['input']}u l={amp_l}u
MPD (nout nout AVDD AVDD) p18 w={w['load']}u l={amp_l}u
MPM (pctrl nout AVDD AVDD) p18 w={w['load']}u l={amp_l}u
CCOMP (pctrl AVSS) mim w=50u l={cc/.04855:.8g}u
MPST (st vcore AVDD AVDD) p18 w={w['startup_p']}u l=1u
MNST (st vcore AVSS AVSS) n18 w={w['startup_n']}u l=1u
MSTART (pctrl st AVSS AVSS) n18 w={w['startup_n']}u l=1u
ends bandgap
'''
    path=CASE/'circuit.scs';path.write_text(text)
    write_json(CASE/'sizing.json',dict(generated_at=now(),parameters=dict(rref=rref,cc=cc,cout=cout,filter_c=filter_c,filter_r=filter_r,core_l=core_l,amp_l=amp_l,cascode=cascode,self_bias=self_bias),roles=roles,bjt=dict(model='npn18a4',unit_emitter_area_um2=4,area_ratios=[1,8,2]),rationale='Increase mirror output resistance and error-amplifier gain with L4um devices; split mirror into5uA units to remain below100um width. PMOS cascodes equalize mirror drain voltages; a strong-inversion diode plus native-poly current path provides the cascode gate bias, including body effect in finalOP. Error-amplifier current is mirrored from the PTAT core instead of directly biased by the supply. Independent startup removes the zero-current equilibrium. Native poly/MIM output RC attenuates MHz feedthrough. Keep1pF external load and original100us startup contract. Actual body effect, headroom and supply gain require measured OP/AC/tran.',circuit_sha256=sha(path)))
    for z in roles.values():
        dst=CASE/'lut'/Path(z['lut_path']).name;dst.parent.mkdir(exist_ok=True);shutil.copy2(z['lut_path'],dst)

def bench(kind):
    supply='dc=1.8 mag=1' if kind!='startup' else 'type=pwl wave=[0 0 1u 1.8 100u 1.8]'
    text='simulator lang=spectre\nglobal 0\n'+''.join(f'include "{MODEL}" section={s}\n' for s in ['tt','bjt_tt','res_tt','mim_tt'])
    text+=f'''include "{CASE/'circuit.scs'}"
VDD (AVDD 0) vsource {supply}
X (AVDD 0 VBG 0) bandgap
CLOAD (VBG 0) capacitor c=1p
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
save AVDD VBG VDD:p X.vcore X.va X.vb X.n1 X.vctat X.pctrl X.nout X.tail X.nbias X.st
'''
    if 'MPC0 ' in (CASE/'circuit.scs').read_text():text+='save X.pc0 X.pc1 X.pc2 X.cbias\n'
    if 'MPA ' in (CASE/'circuit.scs').read_text():text+='save X.namp\n'
    if kind=='static':
        for dev in mos_devices():text+='save '+' '.join(f'X.{dev}:{k}' for k in ['ids','gm','gds','vgs','vds','vbs','vdsat','region'])+'\n'
        text+='dcOp dc\ntemperature dc param=temp start=-40 stop=85 step=1\n'
    elif kind=='ac':text+='dcOp dc\nac ac start=0.01 stop=100M dec=40\n'
    elif kind=='startup':text+='tran tran stop=100u maxstep=10n strobeperiod=10n strobeoutput=strobeonly method=gear2only errpreset=conservative\n'
    else:raise ValueError(kind)
    return text

def simulate(kinds):
    runs={};cp=CASE/'circuit.scs'
    if (CASE/'latest_runs.json').exists():
        for k,v in json.loads((CASE/'latest_runs.json').read_text()).items():
            if json.loads((ROOT/v/'run.json').read_text())['dependencies'][str(cp)]['sha256']==sha(cp):runs[k]=v
    for kind in kinds:
        quota_guard();b=bench(kind);(CASE/f'testbench_{kind}.scs').write_text(b)
        runs[kind]=str(run_spectre(21,kind,b,[cp,CASE/'sizing.json',CASE/'contract.json']).relative_to(ROOT))
        write_json(CASE/'latest_runs.json',runs);print(kind,runs[kind],flush=True)
    return runs

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());assert set(groups)=={'static','ac','startup'}
    runs={k:ROOT/v for k,v in groups.items()}
    for run in runs.values():
        m=json.loads((run/'run.json').read_text());assert m['status']=='completed' and m['dependencies'][str(CASE/'circuit.scs')]['sha256']==sha(CASE/'circuit.scs')
    o=dc(runs['static']);t=data(runs['static'],'temperature.dc');a=data(runs['ac'],'ac.ac');s=data(runs['startup'],'tran.tran')
    assert np.allclose(t['temp'],np.arange(-40,86)) and len(t['temp'])==126
    avg=float(np.trapz(t['VBG'],t['temp'])/125);dc_ref=float(t['VBG'][67])
    assert abs(dc_ref-o['VBG'])<1e-7
    ti=s['time'];v=s['VBG'];mask=(ti>90e-6)&(ti<100e-6)
    tx=np.r_[90e-6,ti[mask],100e-6];vx=np.r_[np.interp(90e-6,ti,v),v[mask],np.interp(100e-6,ti,v)]
    final=float(np.trapz(vx,tx)/10e-6)
    gain=20*np.log10(abs(a['VBG']))
    values=dict(vref_V=dc_ref,temp_min_V=float(min(t['VBG'])),temp_max_V=float(max(t['VBG'])),temp_average_V=avg,tempco_ppm_C=float(np.ptp(t['VBG'])/avg/125*1e6),supply_gain_low_dB=float(at(a['freq'],gain,.01)),supply_gain_1MHz_dB=float(at(a['freq'],gain,1e6)),startup_average_V=final,startup_error_fraction=abs(final-dc_ref)/abs(dc_ref),startup_initial_V=float(v[0]),startup_peak_V=float(max(v)),nominal_power_W=-1.8*o['VDD:p'],maximum_temperature_power_W=float(max(-1.8*t['VDD:p'])),temperature_points=126)
    gates=dict(reference_error_V=gate(abs(dc_ref-1.2),.15,'max','V'),tempco_ppm_C=gate(values['tempco_ppm_C'],50,'max','ppm/C'),supply_gain_low_dB=gate(values['supply_gain_low_dB'],-60,'max','dB',kind='amplitude_db'),supply_gain_1MHz_dB=gate(values['supply_gain_1MHz_dB'],-30,'max','dB',kind='amplitude_db'),startup_error_fraction=gate(values['startup_error_fraction'],.01,'max','fraction'))
    tiers={tier:all(g['passes'][tier] for g in gates.values()) for tier in ['original','10pct','15pct']};tier=next((k for k,v in tiers.items() if v),None)
    op={}
    for dev in mos_devices():
        z={k.split(':')[1]:v for k,v in o.items() if k.startswith('X.'+dev+':')};z.update(gmid=abs(z['gm']/z['ids']),gmro=abs(z['gm']/z['gds']),headroom_V=abs(z['vds'])-abs(z['vdsat']));op[dev]=z
    result=dict(case_slot=21,generated_at=now(),status='complete_'+tier if tier else 'partial',values=values,gates=gates,pass_tiers=tiers,groups=groups,run_dirs=list(groups.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},all_nominal_checks_complete=True,model_dimensions_valid=True,scope=json.loads((CASE/'contract.json').read_text())['scope'])
    write_json(CASE/'latest_results.json',result);print(json.dumps(dict(status=result['status'],values=values,failed_original=[k for k,g in gates.items() if not g['passes']['original']]),indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rref',type=float,default=73.3);p.add_argument('--cc',type=float,default=.5);p.add_argument('--cout',type=float,default=60);p.add_argument('--filter-c',type=float,default=20);p.add_argument('--filter-r',type=float,default=30);p.add_argument('--core-l',type=float,default=4);p.add_argument('--amp-l',type=float,default=4);p.add_argument('--cascode',type=int,choices=[0,1],default=1);p.add_argument('--self-bias',type=int,choices=[0,1],default=1);p.add_argument('--run',nargs='+',default=['static','ac','startup']);p.add_argument('--extract',action='store_true');p.add_argument('--prepare',action='store_true');x=p.parse_args()
    if x.extract:extract();raise SystemExit(0)
    if not (CASE/'contract.json').exists():freeze()
    design(x.rref,x.cc,x.cout,x.filter_c,x.filter_r,x.core_l,x.amp_l,x.cascode,x.self_bias)
    if x.prepare:raise SystemExit(0)
    quota_guard();update_case(21,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))
    runs=simulate(x.run)
    if set(runs)=={'static','ac','startup'}:extract()
