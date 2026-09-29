"""SMIC18 fully differential telescopic OTA; nominal external contract only."""
from common import *
import argparse
import importlib.util

CASE = ROOT/'cases/36-telescopic'
TASK = SOURCE/'sky130-telescopic-cascode-ota-pvt-fix'
DEVS = ['MREF','MTAIL','MINP','MINN','MNCP','MNCN','MPCN','MPCP','MPTN','MPTP',
        'MR1','MT1','MPB2','MD1','MDP1','MT4','MPM','MT5','MCMS','MCMR','MCMT','MCML','MCMLO']
OPFIELDS = ['ids','gm','gds','vgs','vds','vdsat','region']

def design(branch=100,cc=.39,rz=3000,ncdrop=.20,pcdrop=.24,input_l=1,cm_current=20,cm_gmid=18,ptop_gmid=12,sense_c=.15,cm_l=1):
    CASE.mkdir(parents=True,exist_ok=True)
    sourcefiles = ['instruction.md','solution/circuit.spi','tests/verify.py'] + ['tests/benches/'+x for x in ['tb_pvt.spi','tb_swing.spi','tb_settling.spi','tb_cm_recovery.spi']]
    sources={}
    for name in sourcefiles:
        src=TASK/name; dest=CASE/'source'/name; dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(src.read_bytes())
        assert sha(src)==sha(dest)
        sources[name]=dict(path=str(src),sha256=sha(src),frozen=str(dest.relative_to(ROOT)))
    roles={
      'input':lut_size('n18',input_l,18,10e-6,.45),
      'n_bias':lut_size('n18',1,14,10e-6,.2),
      'n_cascode':lut_size('n18',.36,18,10e-6,.45),
      'p_cascode':lut_size('p18',.36,14,10e-6,.45),
      'p_top':lut_size('p18',1,ptop_gmid,10e-6,.45),
      'cm_input':lut_size('n18',cm_l,cm_gmid,10e-6,.45),
    }
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    branch_m=branch/10; cm_m=cm_current/20
    c=CASE/'circuit.scs'
    c.write_text(f'''// SMIC18 gm/ID migration of a fully differential telescopic OTA.
// D G S B; all individual W <= 100um, wide devices use m copies.
simulator lang=spectre
subckt telescopic_cascode_ota (vss iref vdd vinn vinp vocm voutn voutp)
MREF (iref iref vss vss) n18 w={w['n_bias']:g}u l=1u m=5
MTAIL (tail iref vss vss) n18 w={w['n_bias']:g}u l=1u m={2*branch_m:g}
MINP (a1 vinp tail vss) n18 w={w['input']:g}u l={input_l:g}u m={branch_m:g}
MINN (a2 vinn tail vss) n18 w={w['input']:g}u l={input_l:g}u m={branch_m:g}
MNCP (voutn vcn a1 vss) n18 w={w['n_cascode']:g}u l=.36u m={branch_m:g}
MNCN (voutp vcn a2 vss) n18 w={w['n_cascode']:g}u l=.36u m={branch_m:g}
MPCN (voutn vbpc pn pn) p18 w={w['p_cascode']:g}u l=.36u m={branch_m:g}
MPCP (voutp vbpc pp pp) p18 w={w['p_cascode']:g}u l=.36u m={branch_m:g}
MPTN (pn vctrl vdd vdd) p18 w={w['p_top']:g}u l=1u m={branch_m:g}
MPTP (pp vctrl vdd vdd) p18 w={w['p_top']:g}u l=1u m={branch_m:g}
MR1 (vdd vocm srep vss) n18 w={w['input']:g}u l={input_l:g}u
MT1 (srep iref vss vss) n18 w={w['n_bias']:g}u l=1u m=2
MPB2 (vcn vbp vdd vdd) p18 w={w['p_top']:g}u l=1u
MD1 (vcn vcn x1 vss) n18 w={w['n_cascode']:g}u l=.36u
RN (x1 srep) resistor r={ncdrop/10e-6:g}
RP (vdd x2) resistor r={pcdrop/10e-6:g}
MDP1 (vbpc vbpc x2 x2) p18 w={w['p_cascode']:g}u l=.36u
MT4 (vbpc iref vss vss) n18 w={w['n_bias']:g}u l=1u
MPM (vbp vbp vdd vdd) p18 w={w['p_top']:g}u l=1u
MT5 (vbp iref vss vss) n18 w={w['n_bias']:g}u l=1u
RSP (voutp vcm_sense) resistor r=4.7M
RSN (voutn vcm_sense) resistor r=4.7M
CSP (voutp vcm_sense) capacitor c={sense_c:g}p
CSN (voutn vcm_sense) capacitor c={sense_c:g}p
MCMS (dg vcm_sense cmt vss) n18 w={w['cm_input']:g}u l={cm_l:g}u m={cm_m:g}
MCMR (vctrl vocm cmt vss) n18 w={w['cm_input']:g}u l={cm_l:g}u m={cm_m:g}
MCMT (cmt iref vss vss) n18 w={w['n_bias']:g}u l=1u m={cm_current/10:g}
MCML (dg dg vdd vdd) p18 w={w['p_top']:g}u l=1u m={cm_m:g}
MCMLO (vctrl dg vdd vdd) p18 w={w['p_top']:g}u l=1u m={cm_m:g}
CCP (vctrl zp) capacitor c={cc:g}p
RZP (zp voutp) resistor r={rz:g}
CCN (vctrl zn) capacitor c={cc:g}p
RZN (zn voutn) resistor r={rz:g}
ends telescopic_cascode_ota
''')
    args=dict(branch=branch,cc=cc,rz=rz,ncdrop=ncdrop,pcdrop=pcdrop,input_l=input_l,cm_current=cm_current,cm_gmid=cm_gmid,ptop_gmid=ptop_gmid,sense_c=sense_c,cm_l=cm_l)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,parameters=args,
      rationale='gm/(2*pi*(2pF+0.15pF+CC)) estimates differential UGB; 100uA at gm/ID18 yields about 113MHz before internal-node poles. Input L=1um preserves gain; .36um cascodes keep internal nodes fast. VOCM replica sets NMOS cascode headroom, PMOS replica sets top-source headroom. RC average senses CM. Mirror-load CM error amplifier drives both top PMOS gates. Each legal base width is replicated with m.',
      skill_assets='/home/IC/.codex/skills/gmoverid/assets/design_gmoverid.py',target_lut_api=str(LUT_ROOT/'gmidsmic.py')))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_files=sources,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=50e-6,input_common_mode_V=.9,output_common_mode_V=.9,load_each_F=2e-12,
       ac=dict(frequency_Hz=[1,1e10],points_per_decade=100,gain_1Hz_min_dB=60,ugb_min_Hz=50e6,phase_margin_min_deg=60,falling_crossings=1,no_recross=True,cm_error_max_V=.005,power_W=[0,.001]),
       range=dict(command_V=[-.45,.45],step_V=.005,points=181,full_command_span_V=.9,tracking_error_max_V=.005,cm_error_max_V=.005),
       settling=dict(command_V=[-.05,.05],edge_start_s=20e-9,edge_end_s=21e-9,end_s=140e-9,band_V=.001,last_entry_max_s=10e-9,final_mean_window_s=10e-9,static_error_max_V=.0001,static_fraction_max=.01),
       cm_recovery=dict(command_V=[.85,.95],edge_start_s=20e-9,edge_end_s=21e-9,end_s=160e-9,band_V=.005,last_entry_max_s=40e-9,final_mean_window_s=20e-9,static_error_max_V=.005),
       relaxation='Positive min *0.9/0.85, max *1.1/1.15; amplitude dB adds 20log10(0.9/0.85), PM min >=45deg. Same stimuli, full 181-point span, error-band definitions, crossing count and finite/nonnegative guards are not relaxed.',
       nominal_only=True,excluded=['remaining 26 PVT points','mismatch/Monte Carlo','noise/CMRR/PSRR','extracted parasitics','passive variation']))
    return c

def prefix(c):
    return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=50u
X (0 iref vdd vinn vinp vocm voutn voutp) telescopic_cascode_ota
CLP (voutp 0) capacitor c=2p
CLN (voutn 0) capacitor c=2p
save voutp voutn VDD:p vocm vinn vinp iref
'''

def acbench(c):
    b=prefix(c)+'''VOCM (vocm 0) vsource dc=.9
VINP (vinp 0) vsource dc=.9 mag=.5
VINN (vinn 0) vsource dc=.9 mag=.5 phase=180
save X.tail X.a1 X.a2 X.pn X.pp X.vcn X.vbpc X.vctrl X.srep X.x1 X.x2 X.vbp X.cmt X.dg X.vcm_sense
'''
    for dev in DEVS:b+='save '+' '.join(f'X.{dev}:{x}' for x in OPFIELDS)+'\n'
    return b+'dcOp dc\nac ac start=1 stop=10G dec=100\n'

def feedback():
    return '''EFB (err err0 voutp voutn) vcvs gain=-1
EINP (vinp vocm err 0) vcvs gain=.5
EINN (vinn vocm err 0) vcvs gain=-.5
save err0 err
'''

def rangebench(c):
    return prefix(c)+'''parameters command=0
VOCM (vocm 0) vsource dc=.9
VERR (err0 0) vsource dc=command
'''+feedback()+'''swing dc param=command start=-.45 stop=.45 step=.005
'''

def settlebench(c):
    return prefix(c)+'''VOCM (vocm 0) vsource dc=.9
VERR (err0 0) vsource type=pwl wave=[0 -.05 20n -.05 21n .05 140n .05]
'''+feedback()+'''tran tran stop=140n maxstep=25p strobeperiod=50p strobeoutput=strobeonly errpreset=conservative
'''

def cmbench(c):
    return prefix(c)+'''VOCM (vocm 0) vsource type=pwl wave=[0 .85 20n .85 21n .95 160n .95]
VINP (vinp 0) vsource dc=.9
VINN (vinn 0) vsource dc=.9
save X.vctrl X.vcm_sense X.vcn X.vbpc
tran tran stop=160n maxstep=25p strobeperiod=50p strobeoutput=strobeonly errpreset=conservative
'''

def cm_stb():
    """Noninvasive zero-volt probe in the sole CM sense feedback connection."""
    c=CASE/'circuit.scs';cp=CASE/'cmprobe.scs'
    text=c.read_text().replace('MCMS (dg vcm_sense cmt vss)', 'PCM (vcm_sense cm_probe) iprobe\nMCMS (dg cm_probe cmt vss)')
    cp.write_text(text)
    b=acbench(cp).replace('ac ac start=1 stop=10G dec=100','cmstb stb start=1 stop=10G dec=100 probe=X.PCM')
    run=run_spectre(36,'cmstb',b,[cp,c,CASE/'sizing.json',CASE/'contract.json'])
    q=data(run,'cmstb.stb');print(str(run));print(list(q));return run,q

def source_verifier():
    spec=importlib.util.spec_from_file_location('case36_frozen_verify',CASE/'source/tests/verify.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def extract(runs):
    a=data(runs[0],'ac.ac');o=dc(runs[0]);v=source_verifier()
    def plot(q,axis,names):
        keys=[axis]+names
        variables=[{'freq':'frequency','time':'time'}.get(k,'v('+k+')') for k in keys]
        return v.Plot('Spectre translated',variables,[list(x) for x in zip(*(q[k].astype(complex) for k in keys))])
    vals=v.ac_metrics(plot(a,'freq',['voutp','voutn']))
    vals.update(output_common_mode_error_v=abs((o['voutp']+o['voutn'])/2-.9),power_w=-1.8*o['VDD:p'])
    op={}
    for dev in DEVS:
        q={k:o[f'X.{dev}:{k}'] for k in OPFIELDS}
        q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']))
        op[dev]=q
    valid=vals['falling_crossing_count']==1 and vals['post_first_crossing_gain_db_max']<0 and vals['power_w']>=0
    gates={}
    for key,lim,sense,unit,kind in [('dc_gain_db',60,'min','dB','amplitude_db'),('ugb_hz',50e6,'min','Hz','linear'),('phase_margin_deg',60,'min','deg','phase_margin'),('output_common_mode_error_v',.005,'max','V','linear'),('power_w',.001,'max','W','linear')]:gates[key]=gate(vals[key],lim,sense,unit,kind)
    if len(runs)==4:
        d=data(runs[1],'swing.dc');s=data(runs[2],'tran.tran');c=data(runs[3],'tran.tran')
        # The original verifier validates every public range command and exact endpoint stimuli.
        rangeplot=v.Plot('range',['v(err0)','v(voutp)','v(voutn)'],[list(x) for x in zip(*(d[k].astype(complex) for k in ['err0','voutp','voutn']))])
        vals.update(v.swing_metrics(rangeplot,.9));vals.update(v.settling_metrics(plot(s,'time',['err0','voutp','voutn'])));vals.update(v.common_mode_recovery_metrics(plot(c,'time',['vocm','voutp','voutn'])))
        for key,lim,unit in [('closed_loop_tracking_error_v_max',.005,'V'),('closed_loop_common_mode_error_v_max',.005,'V'),('settling_time_s',10e-9,'s'),('settling_static_error_v',.0001,'V'),('settling_error_fraction',.01,'fraction'),('cm_recovery_time_s',40e-9,'s'),('cm_recovery_final_error_v',.005,'V')]:
            if np.isfinite(vals[key]):gates[key]=gate(vals[key],lim,'max',unit)
            else:valid=False;vals[key]=None
        valid=bool(valid and vals['range_points']==181 and abs(vals['closed_loop_range_vpp']-.9)<1e-12)
    all_complete=len(runs)==4
    # Source uses strict boundaries for AC, power, and both last-entry times.
    strict=['dc_gain_db','ugb_hz','phase_margin_deg','output_common_mode_error_v','power_w','settling_time_s','cm_recovery_time_s']
    for key in strict:
        if key in gates:
            g=gates[key]
            g['comparison']='>' if g['sense']=='min' else '<'
            g['passes']={t:bool(g['value']>lim if g['sense']=='min' else g['value']<lim) for t,lim in g['limits'].items()}
    tiers={tier:bool(all_complete and valid and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']}
    tier=next((x for x in tiers if tiers[x]),None)
    result=dict(case_slot=36,generated_at=now(),run_dirs=[str(x.relative_to(ROOT)) for x in runs],status='complete_'+tier if tier else 'partial',values=vals,gates=gates,operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},all_nominal_checks_complete=all_complete,pass_tiers=tiers,model_dimensions_valid=True,nonrelaxable_guards_pass=valid,source_verifier_sha256=sha(CASE/'source/tests/verify.py'),measurement_engine='Original frozen verifier receives translated real Spectre PSF vectors; power uses identical -VDD*I(VDD).',scope='SMIC18 tt / 1.8 V / 27 C, FD AC 1Hz-10GHz, full181 DC range, differential last-entry and VOCM recovery; other PVT and mismatch excluded.')
    write_json(runs[0]/'measurements.json',result);write_json(CASE/'latest_results.json',result)
    update_case(36,status=result['status'],nominal_complete=bool(tier),case_dir=str(CASE.relative_to(ROOT)),results=str((CASE/'latest_results.json').relative_to(ROOT)),run_dirs=result['run_dirs'])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['static','full'],default='full')
    for name,default in [('branch',100),('cc',.39),('rz',3000),('ncdrop',.20),('pcdrop',.24),('input_l',1),('cm_current',20),('cm_gmid',18),('ptop_gmid',12),('sense_c',.15),('cm_l',1)]:p.add_argument('--'+name.replace('_','-'),type=float,default=default)
    args=vars(p.parse_args());mode=args.pop('mode')
    update_case(36,status='running',nominal_complete=False)
    c=design(**args);deps=[c,CASE/'sizing.json',CASE/'contract.json',Path(__file__).resolve()]
    runs=[]
    for label,fn in [('ac',acbench)]+([('range',rangebench),('settling',settlebench),('cm_recovery',cmbench)] if mode=='full' else []):
        text=fn(c);(CASE/f'testbench_{label}.scs').write_text(text)
        runs.append(run_spectre(36,label,text,deps))
    result=extract(runs)
    print(json.dumps(dict(status=result['status'],values=result['values'],runs=result['run_dirs'],op_summary={k:{x:result['operating_point'][k][x] for x in ['gmid','headroom_V']} for k in ['MINP','MTAIL','MNCP','MPCN','MPTN','MCMS']}),indent=2))

if __name__=='__main__':main()
