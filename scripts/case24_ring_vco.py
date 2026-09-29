"""Current-starved five-stage ring: full deterministic nominal VCO contract."""
from common import *
from hd_cells import extract_hd
import argparse
import shutil

CASE=ROOT/'cases/24-ring-vco'
TASK=SOURCE/'sky130-current-starved-ring-vco-pvt'
CONTROLS=[.9,1.,1.1,1.2]
STARTS=np.array([51e-9,1.052e-6,2.053e-6,3.054e-6])
ENDS=STARTS+1e-6
SPECS=[('f_0p9_min_Hz',10e6,'min','Hz'),('f_0p9_max_Hz',25e6,'max','Hz'),
       ('f_1p2_Hz',25e6,'min','Hz'),('tuning_ratio',1.5,'min','ratio'),
       ('kvco_min_Hz_per_V',30e6,'min','Hz/V'),('kvco_linearity_ratio',1.5,'max','ratio'),
       ('frequency_settling_drift',.001,'max','fraction'),('duty_error_from_half',.05,'max','fraction'),
       ('startup_time_s',100e-9,'max','s'),('output_low_fraction',.1,'max','VDD'),
       ('output_high_fraction',.9,'min','VDD'),('power_W',200e-6,'max','W'),
       ('supply_pushing_pct_per_V',100.,'max','%/V')]

def design(resistance=47e3,cap_fF=30,gmid=15,current_uA=10,length=.36,cell='INHDV2'):
    CASE.mkdir(parents=True,exist_ok=True)
    records=[]
    for rel in ['instruction.md','tests/verify.py','results/reference.json','solution/circuit.spi',
                'tests/benches/tb_tune.spi','tests/benches/tb_push.spi']:
        src=TASK/rel;dst=CASE/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():shutil.copyfile(src,dst)
        assert sha(src)==sha(dst)
        records.append(dict(original=str(src),frozen=str(dst.relative_to(ROOT)),sha256=sha(src)))
    write_json(CASE/'source_provenance.json',dict(source_task=TASK.name,files=records))
    hd=extract_hd([cell,'INHDV0','INHDV2'],CASE)
    roles={d:lut_size(d,length,gmid,current_uA*1e-6,.45) for d in ['n18','p18']}
    wn=roles['n18']['rounded_W_um'];wp=roles['p18']['rounded_W_um']
    text=f'''// Five-stage current-starved VCO; original HD cells on virtual rails.
simulator lang=spectre
subckt current_starved_ring_vco (vss vctrl vdd vout)
RDEG (ndeg vss) resistor r={resistance:g}
MVIN (pdio vctrl ndeg vss) n18 w={wn:g}u l={length:g}u
MPDIO (pdio pdio vdd vdd) p18 w={wp:g}u l={length:g}u
MPSRC (ndio pdio vdd vdd) p18 w={wp:g}u l={length:g}u
MNDIO (ndio ndio vss vss) n18 w={wn:g}u l={length:g}u
'''
    for i in range(1,6):
        previous=5 if i==1 else i-1
        text+=f'MPS{i} (s{i}t pdio vdd vdd) p18 w={wp:g}u l={length:g}u\n'
        text+=f'XINV{i} (n{previous} n{i} s{i}t s{i}b vdd vss) {cell}\n'
        text+=f'MNS{i} (s{i}b ndio vss vss) n18 w={wn:g}u l={length:g}u\n'
        text+=f'CS{i} (n{i} vss) capacitor c={cap_fF:g}f\n'
    text+='''XBUF0 (n5 bo1 vdd vss vdd vss) INHDV0
XBUF1 (bo1 vout vdd vss vdd vss) INHDV2
ends current_starved_ring_vco
'''
    c=CASE/'circuit.scs';c.write_text(text)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,reference_current_uA=current_uA,
      initial_gmid=gmid,L_um=length,Rdeg_Ohm=resistance,stage_load_fF=cap_fF,ring_stages=5,
      ring_HD_cell=cell,output_HD_cells=['INHDV0','INHDV2'],HD_count=7,
      digital_analog_boundary='Each ring inverter is an unmodified vendor HD cell. Its supply terminals connect to external analog current-limit devices; well pins stay on the global VDD/VSS. Analog V-to-I and mirror/current-limit MOS use gm/ID LUT sizes. No custom digital MOS.',
      lut_temperature_C=27,verification_temperature_C=27,
      rationale='Source-degenerated NMOS creates a near-linear Vctrl-to-I conversion. PMOS and NMOS mirrors feed both sides of five HD inverter stages. gm/ID15 limits gate overdrive and preserves current-source headroom. 10uA initial current, five30fF loads and1.8V imply f≈I/(5*C*VDD)≈37MHz before parasitics and nonlinear transition effects; low-control current is lower. Source degeneration reduces tuning curvature. Actual transistor currents, period windows and supply pushing verify the design.',
      passives='Ideal internal R and C expressly permitted by the original task; no claim of physical resistor/capacitor area, mismatch or temperature behavior.',
      startup='No forced initial condition, kick, noise source or skipdc: original control step from0V after50ns and physical output-buffer loading start the ring.'))
    specs={k:gate(0,l,s,u) for k,l,s,u in SPECS}
    for v in specs.values():v.pop('value');v.pop('passes')
    write_json(CASE/'contract.json',dict(source_task=TASK.name,corner='tt',VDD_V=1.8,temperature_C=27,load_F=20e-15,
      controls_V=CONTROLS,plateau_starts_s=STARTS.tolist(),plateau_ends_s=ENDS.tolist(),transition_s=1e-9,
      tuning_frequency='5/(rise6-rise1), rising half-supply crossings beginning300ns after each plateau starts',
      settling_drift='abs(fearly-flate)/mean(fearly,flate); 2 periods each beginning300ns after start and300ns before end',
      plateau_containment_nonrelaxable=True,startup='First rising half-supply crossing after51ns minus51ns; no forced IC',
      duty_control_V=1.1,duty_original_verifier='min(abs(firstfall-firstrise),period-abs(firstfall-firstrise))/period; actual high fraction also extracted',
      duty_acceptance='abs(actual high fraction-0.5)<=0.05;10/15% expand halfwidth to0.055/0.0575, center stays0.5',
      swing_windows_s=[[float(a+300e-9),float(b)] for a,b in zip(STARTS,ENDS)],
      power_window_s=[3.754e-6,4.054e-6],power_port='Entire DUT VDD including analog bias, all5 delay stages and both output buffers',
      supply_pushing=dict(controls_V=1.1,temperature_C=27,corner='tt',supplies_V=[1.71,1.89],measurement_start_s=550e-9,periods=5,stop_s=1e-6,formula='abs(fhigh-flow)/mean(fhigh,flow)/0.18*100'),
      specs=specs,nominal_scope_excludes=['other26 tuning PVT combinations','SS/FF supply-pushing tests','phase noise and jitter','mismatch/Monte Carlo','PEX'],
      source='Frozen instruction and formal verifier define the timing. Static supply perturbation is a nominal sensitivity dimension and remains required.'))
    return c,hd

def prefix(c):
    return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'hd_cells.scs'}"
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=2e-5 vabstol=1e-8 iabstol=1e-14
saveOptions options save=selected
'''

def bench(c,kind,step_ps=100):
    b=prefix(c)
    if kind=='tune':
        b+='''VDD (vdd 0) vsource dc=1.8
VCTRL (vctrl 0) vsource type=pwl wave=[0 0 50n 0 51n .9 1.051u .9 1.052u 1 2.052u 1 2.053u 1.1 3.053u 1.1 3.054u 1.2 4.054u 1.2]
XVCO (0 vctrl vdd vout) current_starved_ring_vco
CL (vout 0) capacitor c=20f
save vctrl vout VDD:p XVCO.pdio XVCO.ndio XVCO.ndeg XVCO.bo1
save XVCO.n1 XVCO.n2 XVCO.n3 XVCO.n4 XVCO.n5 XVCO.s1t XVCO.s1b
'''
        for dev in ['MVIN','MPDIO','MNDIO','MPS1','MNS1']:
            b+='save '+' '.join(f'XVCO.{dev}:{x}' for x in ['ids','vgs','vds','gm','gds','vdsat'])+'\n'
        stop='4.054u'
    elif kind=='push':
        b+='VCTRL (vctrl 0) vsource type=pwl wave=[0 0 50n 0 51n 1.1 1u 1.1]\n'
        for suffix,supply in [('LOW',1.71),('HIGH',1.89)]:
            b+=f'VDD{suffix} (vdd{suffix} 0) vsource dc={supply}\nX{suffix} (0 vctrl vdd{suffix} out{suffix}) current_starved_ring_vco\nCL{suffix} (out{suffix} 0) capacitor c=20f\nsave out{suffix} VDD{suffix}:p\n'
        stop='1u'
    else:raise ValueError(kind)
    return b+f'tran tran stop={stop} maxstep={step_ps:g}p errpreset=conservative\n'

def crosses(t,y,level,rising=True):
    index=np.flatnonzero((y[:-1]<level)&(y[1:]>=level) if rising else (y[:-1]>level)&(y[1:]<=level))
    return t[index]+(t[index+1]-t[index])*(level-y[index])/(y[index+1]-y[index])

def window(t,y,a,b):
    mask=(t>a)&(t<b)
    return np.r_[a,t[mask],b],np.r_[np.interp(a,t,y),y[mask],np.interp(b,t,y)]

def average(t,y,a,b):
    tw,vw=window(t,y,a,b)
    return float(np.trapz(vw,tw)/(b-a))

def tune_extract(run):
    d=data(run,'tran.tran');t=d['time'];y=d['vout'];rise=crosses(t,y,.9);fall=crosses(t,y,.9,False)
    rows=[]
    for control,a,b in zip(CONTROLS,STARTS,ENDS):
        early=rise[rise>=a+300e-9][:6];late=rise[rise>=b-300e-9][:3]
        if len(early)<6 or len(late)<3:
            result=dict(run_dir=str(run.relative_to(ROOT)),valid=False,error=f'Missing period edges at control{control}',available_rising_edges=rise.tolist(),plateaus=rows)
            write_json(run/'measurements.json',result);return result
        f=5/(early[5]-early[0]);fe=2/(early[2]-early[0]);fl=2/(late[2]-late[0])
        _,yw=window(t,y,a+300e-9,b)
        rows.append(dict(control_V=control,plateau_start_s=float(a),plateau_end_s=float(b),frequency_Hz=float(f),
          early_frequency_Hz=float(fe),late_frequency_Hz=float(fl),drift=float(abs(fe-fl)/((fe+fl)/2)),
          six_period_edges_s=early.tolist(),late_three_edges_s=late.tolist(),
          period_end_s=float(early[5]),late_end_s=float(late[2]),all_edges_inside_plateau=bool(early[5]<=b and late[2]<=b),
          output_min_V=float(min(yw)),output_max_V=float(max(yw)),
          average_bias_current_A=average(t,d['XVCO.MVIN:ids'],a+300e-9,b),
          average_ndeg_V=average(t,d['XVCO.ndeg'],a+300e-9,b),
          average_VDD_current_A=-average(t,d['VDD:p'],a+300e-9,b)))
    after=rise[rise>=51e-9]
    f=np.array([q['frequency_Hz'] for q in rows]);kvco=np.diff(f)/.1
    duty_edges=rise[rise>=2.353e-6][:2];first_fall=fall[fall>=2.353e-6][0];following_fall=fall[fall>duty_edges[0]][0]
    period=duty_edges[1]-duty_edges[0];gap=abs(first_fall-duty_edges[0]);duty_original=min(gap,period-gap)/period
    high=(following_fall-duty_edges[0])/period
    result=dict(run_dir=str(run.relative_to(ROOT)),valid=True,plateaus=rows,
      f_0p9_min_Hz=float(f[0]),f_0p9_max_Hz=float(f[0]),f_1p2_Hz=float(f[3]),tuning_ratio=float(f[3]/f[0]),
      kvco_Hz_per_V=kvco.tolist(),kvco_min_Hz_per_V=float(min(kvco)),kvco_linearity_ratio=float(max(kvco)/min(kvco)),
      frequency_settling_drift=max(q['drift'] for q in rows),startup_time_s=float(after[0]-51e-9),startup_crossing_s=float(after[0]),
      duty_high_fraction=float(high),duty_verifier_fraction=float(duty_original),duty_error_from_half=float(abs(high-.5)),
      duty_edges_s=dict(rise1=float(duty_edges[0]),rise2=float(duty_edges[1]),firstfall=float(first_fall),followingfall=float(following_fall)),
      output_low_fraction=max(q['output_min_V'] for q in rows)/1.8,output_high_fraction=min(q['output_max_V'] for q in rows)/1.8,
      power_W=-1.8*average(t,d['VDD:p'],3.754e-6,4.054e-6),
      all_windows_valid=all(q['all_edges_inside_plateau'] for q in rows),monotonic=bool(np.all(kvco>0)))
    conditions=[];crosscheck=[]
    for q in rows:
        a=q['plateau_start_s']+300e-9;b=q['plateau_end_s'];idx=(t>=a)&(t<=b)
        rec=dict(control_V=q['control_V'],devices={})
        for dev in ['MVIN','MPDIO','MNDIO']:
            z={key:average(t,d[f'XVCO.{dev}:{key}'],a,b) for key in ['ids','vgs','vds','gm','gds','vdsat']}
            z['gmid']=abs(z['gm']/z['ids'])
            z['min_saturation_headroom_V']=float(min(abs(d[f'XVCO.{dev}:vds'][idx])-abs(d[f'XVCO.{dev}:vdsat'][idx])))
            rec['devices'][dev]=z
        rec['virtual_rails_V']=dict(top_min=float(min(d['XVCO.s1t'][idx])),top_max=float(max(d['XVCO.s1t'][idx])),bottom_min=float(min(d['XVCO.s1b'][idx])),bottom_max=float(max(d['XVCO.s1b'][idx])))
        conditions.append(rec)
        all_edges=rise[(rise>=a)&(rise<=b)];all_f=(len(all_edges)-1)/(all_edges[-1]-all_edges[0])
        crosscheck.append(dict(control_V=q['control_V'],complete_stable_periods=len(all_edges)-1,contract_five_period_Hz=q['frequency_Hz'],all_complete_stable_periods_Hz=float(all_f),relative_difference=float(abs(all_f-q['frequency_Hz'])/q['frequency_Hz'])))
    oc=dict(run_dir=str(run.relative_to(ROOT)),method='Time-weighted averages over each stable plateau; headroom is minimum sampled |VDS|-|VDSAT|. These are periodic circuit conditions, not standalone DC OP.',plateaus=conditions)
    xc=dict(method='Independent averaging over all complete stable-window periods; no extra simulation and no changed acceptance windows.',run_dir=str(run.relative_to(ROOT)),checks=crosscheck,max_relative_difference=max(q['relative_difference'] for q in crosscheck),note='Nearzero drift is deterministic periodic model agreement, not physical jitter/phase-noise performance.')
    for name,record in [('operating_conditions.json',oc),('frequency_crosscheck.json',xc)]:
        write_json(run/name,record);write_json(CASE/name,record)
    write_json(run/'measurements.json',result);return result

def push_extract(run):
    d=data(run,'tran.tran');t=d['time'];rows=[]
    for suffix,vdd in [('LOW',1.71),('HIGH',1.89)]:
        rising=crosses(t,d['out'+suffix],vdd/2);edges=rising[rising>=550e-9][:6]
        if len(edges)<6:
            result=dict(run_dir=str(run.relative_to(ROOT)),valid=False,error=f'Missing6 edges at VDD{vdd}',supplies=rows)
            write_json(run/'measurements.json',result);return result
        rows.append(dict(VDD_V=vdd,frequency_Hz=float(5/(edges[-1]-edges[0])),edges_s=edges.tolist(),all_edges_in_window=bool(edges[-1]<=1e-6)))
    fl,fh=[q['frequency_Hz'] for q in rows];push=abs(fh-fl)/((fl+fh)/2)/.18*100
    result=dict(run_dir=str(run.relative_to(ROOT)),valid=True,supplies=rows,supply_pushing_pct_per_V=push,all_windows_valid=all(q['all_edges_in_window'] for q in rows))
    write_json(run/'measurements.json',result);return result

def aggregate(runs):
    tune=tune_extract(runs[0]);push=push_extract(runs[1]);values={k:tune.get(k,push.get(k)) for k,_,_,_ in SPECS}
    gates={k:gate(values[k],lim,sense,unit) for k,lim,sense,unit in SPECS if values[k] is not None}
    functional=bool(tune.get('valid') and push.get('valid') and tune.get('monotonic') and tune.get('all_windows_valid') and push.get('all_windows_valid') and tune.get('power_W',-1)>=0)
    tiers={tier:bool(functional and len(gates)==len(SPECS) and all(q['passes'][tier] for q in gates.values())) for tier in ['original','10pct','15pct']}
    tier=next((t for t in tiers if tiers[t]),None)
    r=dict(case_slot=24,generated_at=now(),run_dirs=[str(x.relative_to(ROOT)) for x in runs],status='complete_'+tier if tier else 'partial',
      nominal_complete=bool(tier),values=values,gates=gates,pass_tiers=tiers,functional_checks_pass=functional,all_nominal_checks_complete=bool(tune.get('valid') and push.get('valid')),
      model_dimensions_valid=True,tuning=tune,pushing=push,scope='TT/1.8V/27C4 control plateaus and TT/27C1.71/1.89V pushing pair. Other PVT, mismatch, noise/jitter and PEX excluded.')
    write_json(CASE/'latest_results.json',r);write_json(runs[-1]/'combined_measurements.json',r)
    update_case(24,status=r['status'],nominal_complete=bool(tier),latest_runs=r['run_dirs'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--resistance',type=float,default=47e3);p.add_argument('--cap',type=float,default=30)
    p.add_argument('--gmid',type=float,default=15);p.add_argument('--current',type=float,default=10);p.add_argument('--length',type=float,default=.36)
    p.add_argument('--cell',default='INHDV2');p.add_argument('--step',type=float,default=100);p.add_argument('--extract',nargs=2);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        if (ROOT/'monitor/QUOTA_TRIGGER.json').exists():raise RuntimeError('Quota trigger: stop new24 simulations')
        c,hd=design(a.resistance,a.cap,a.gmid,a.current,a.length,a.cell);update_case(24,status='running',nominal_complete=False)
        runs=[]
        for kind in ['tune','push']:
            b=bench(c,kind,a.step);(CASE/f'testbench_{kind}.scs').write_text(b)
            runs.append(run_spectre(24,kind,b,[c,hd,CASE/'sizing.json',CASE/'contract.json',CASE/'hd_cells_manifest.json',CASE/'source_provenance.json']))
    r=aggregate(runs);print(json.dumps({k:r[k] for k in ['status','values','functional_checks_pass','run_dirs']},indent=2))

if __name__=='__main__':main()
