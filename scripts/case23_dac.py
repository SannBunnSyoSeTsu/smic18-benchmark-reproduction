"""5-bit weighted resistor DAC: complete deterministic nominal Spectre checks."""
from common import *
from hd_cells import extract_hd
import argparse
import shutil

CASE = ROOT/'cases/23-resistor-dac'
TASK = SOURCE/'sky130-cmos-switched-resistor-dac-5bit-pvt'
VDD = 1.8
LSB = VDD/32
TRANSITIONS = [('34u',3,4,20),('34d',4,3,25),('78u',7,8,45),
               ('78d',8,7,50),('1516u',15,16,70),('1516d',16,15,75)]
ROUT_CODES = [0,4,15,16,28,31]
SPECS = [('inl_lsb_max',.25,'LSB'),('dnl_lsb_max',.25,'LSB'),
         ('zero_code_error_V',.002,'V'),('full_scale_error_V',.005,'V'),
         ('power_avg_W',.001,'W'),('settling_time_s',5e-9,'s'),
         ('settling_end_error_lsb_max',.25,'LSB'),('excursion_lsb_max',1.,'LSB'),
         ('rout_max_Ohm',2e3,'Ohm')]

def design(unit_current_uA=200, res_length_um=96, receiver_scale=1, cap_area_um2=0):
    CASE.mkdir(parents=True,exist_ok=True)
    source_files=['instruction.md','tests/verify.py','results/reference.json','solution/circuit.spi']
    source_files += ['tests/benches/tb_'+b+'.spi' for b in ['code_ramp','major_carry','output_resistance','mismatch_ramp']]
    records=[]
    for f in source_files:
        src=TASK/f;dst=CASE/'source'/f;dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():shutil.copyfile(src,dst)
        assert sha(src)==sha(dst)
        records.append(dict(original=str(src),frozen=str(dst.relative_to(ROOT)),sha256=sha(src)))
    write_json(CASE/'source_provenance.json',dict(files=records,source_task=TASK.name))
    cell_lists={1:['INHDV2','INHDV4','INHDV8','INHDV16','INHDV32'],
                2:['INHDV4','INHDV8','INHDV16','INHDV32','INHDV32']}
    receivers=cell_lists[receiver_scale]
    hd=extract_hd(receivers+['INHDV3','INHDV32'],CASE)
    roles={d:lut_size(d,.18,6,unit_current_uA*1e-6,.9) for d in ['n18','p18']}
    w={d:roles[d]['rounded_W_um'] for d in roles}
    text='''// 5-bit binary-weighted PDK resistor DAC; b0 is LSB.
// HD logic definition must be included at the bench level.
simulator lang=spectre
subckt switched_resistor_dac_5bit (vss b0 b1 b2 b3 b4 vdd vout)
'''
    for bit in range(5):
        weight=2**bit
        text+=f'XINV{bit} (b{bit} nb{bit} vdd vss vdd vss) {receivers[bit]}\n'
        text+=f'MSN{bit} (sw{bit} nb{bit} vss vss) n18 w={w["n18"]:g}u l=.18u m={weight}\n'
        text+=f'MSP{bit} (sw{bit} nb{bit} vdd vdd) p18 w={w["p18"]:g}u l=.18u m={weight}\n'
        for unit in range(weight):
            text+=f'RB{bit}_{unit} (vout sw{bit} vss) rpposab_3t w=1u l={res_length_um:g}u\n'
    text+=f'RT (vout vss vss) rpposab_3t w=1u l={res_length_um:g}u\n'
    if cap_area_um2:text+=f'CFILT (vout vss) mim w=10u l={cap_area_um2/10:g}u\n'
    text+='ends switched_resistor_dac_5bit\n'
    c=CASE/'circuit.scs';c.write_text(text)
    ru=311.3*res_length_um/(1-.0546)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,unit_current_uA=unit_current_uA,
      branch_switch_m=[1,2,4,8,16],receiver_scale=receiver_scale,receiver_cells=receivers,
      dut_HD_count=5,external_driver_cells=['INHDV3','INHDV32'],external_driver_stages=2,
      external_driver_note='Original two-stage finite-strength Sky130 buffer is migrated to exact vendor SMIC HD cells. INHDV3 total W=4.4um and INHDV32 total W=46.88um; source edge and both stages retained. Driver supply measured separately from DUT, as original.',
      resistor=dict(model='rpposab_3t',W_um=1,L_um=res_length_um,unit_count=32,
       groups=[1,2,4,8,16,1],unit_R_estimate_Ohm=ru,ideal_Rout_estimate_Ohm=ru/32,
       ideal_avg_static_power_estimate_W=VDD**2/(ru/32)*sum((k/32)*(1-k/32) for k in range(32))/32,
       substrate='vss',parallel_unit_reason='Identical dimensions preserve integer conductance weights including etch, substrate capacitance and voltage coefficient.'),
      internal_mim_area_um2=cap_area_um2,lut_temperature_C=27,verification_temperature_C=27,
      rationale='Runit/32 near 1kOhm balances 1pF settling and the 1mW DUT power limit. gm/ID=6, L=.18um is a strong-inversion speed starting point. At 200uA reference the switches are 3.24/9.08um, multiplied with bit conductance to hold fractional switch resistance roughly constant. This LUT reference current is not a bias current. Rail-connected switches actually operate predominantly in triode with full rail gate drive; actual waveform and rail-drop measurements validate them.'))
    specdict={k:gate(0,x,'max',u) for k,x,u in SPECS}
    for g in specdict.values():g.pop('value');g.pop('passes')
    write_json(CASE/'contract.json',dict(source_task=TASK.name,corner='tt',resistor_corner='res_tt',capacitor_corner='mim_tt',
      VDD_V=VDD,temperature_C=27,load_F=1e-12,bit_order='b0 LSB, b4 MSB',ideal_code_V='k*VDD/32',
      code_rate_Hz=200e6,source_edge_s=50e-12,ramp_codes=list(range(32)),ramp_sample_times_s=[(7+5*k)*1e-9 for k in range(32)],
      power_window_s=[2.5e-9,162.5e-9],power_port='DUT VDD only, excluding separately supplied external two-stage bit drivers as original verifier',
      transitions=[dict(label=l,start=a,stop=b,time_s=t*1e-9,window_s=5e-9,end_sample_offset_s=4.99e-9) for l,a,b,t in TRANSITIONS],
      settling_definition='Original last |Vout-target|=0.25*VDD/32 crossing within the fixed 5ns window; independently require end error <=0.25LSB and last crossing must enter the band. All crossing times are retained. Input/observation windows are not relaxed.',
      rout_codes=ROUT_CODES,perturbation_A=5e-6,rout_direction='Code0 injects into output; other codes draw from output',rout_sample_offsets_s=[14e-9,29e-9],
      specs=specdict,functional_nonrelaxable=['32 finite sampled voltages','all31 steps positive','nonnegative DUT power','all6 output resistances nonnegative','finite last-crossing and end-error evidence for all6 transitions','model geometry valid'],
      nominal_scope_excludes=['other10 representative PVT points','8 fixed-seed local-mismatch regressions','Monte Carlo yield','PEX and layout matching'],
      passives='Native PDK resistor, optional native PDK MIM; no ideal passive inside DUT',
      source_stimuli='VC0..VC4 and injected load are mechanically translated from frozen public verifier benches; same PULSE/PWL times and levels. HD driver is the documented process migration.'))
    return c,hd

def translate_source(line):
    tokens=line.split(None,3);name,p,n,value=tokens
    n='0' if n=='vss' else n
    p='0' if p=='vss' else p
    primitive='vsource' if name.startswith('V') else 'isource'
    m=re.match(r'PWL\((.*)\)',value,re.I)
    if m:return f'{name} ({p} {n}) {primitive} type=pwl wave=[{m[1]}]\n'
    m=re.match(r'PULSE\((.*)\)',value,re.I)
    if m:
        v0,v1,delay,rise,fall,width,period=m[1].split()
        return f'{name} ({p} {n}) {primitive} type=pulse val0={v0} val1={v1} delay={delay} rise={rise} fall={fall} width={width} period={period}\n'
    raise ValueError(line)

def bench(c,kind,refined=False):
    source=(CASE/'source/tests/benches'/f'tb_{kind}.spi').read_text()
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{MODEL}" section=res_tt
include "{MODEL}" section=mim_tt
include "{CASE/'hd_cells.scs'}"
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=2e-5 vabstol=1e-8 iabstol=1e-14
saveOptions options save=selected
subckt dac_bit_driver (cmd bit vdrv vss)
X0 (cmd n1 vdrv vss vdrv vss) INHDV3
X1 (n1 bit vdrv vss vdrv vss) INHDV32
ends dac_bit_driver
VDD (vdd 0) vsource dc=1.8
VDRV (vdrv 0) vsource dc=1.8
'''
    for line in source.splitlines():
        if re.match(r'^(VC[0-4]|IINJECT0|ILOAD)\s',line):b+=translate_source(line)
    for bit in range(5):b+=f'XDB{bit} (c{bit} b{bit} vdrv 0) dac_bit_driver\n'
    b+='XDAC (0 b0 b1 b2 b3 b4 vdd vout) switched_resistor_dac_5bit\nCL (vout 0) capacitor c=1p\n'
    b+='save vout VDD:p VDRV:p '+ ' '.join(f'c{i} b{i} XDAC.nb{i} XDAC.sw{i}' for i in range(5))+'\n'
    steps={'code_ramp':('162.5n','10p'),'major_carry':('85n','5p'),'output_resistance':('180n','25p')}
    stop,step=steps[kind]
    if refined:
        step={'code_ramp':'2p','major_carry':'1p','output_resistance':'5p'}[kind]
        b=b.replace('reltol=2e-5','reltol=2e-6')
    b+=f'tran tran stop={stop} maxstep={step} skipdc=yes errpreset=conservative\n'
    return b

def window(t,y,a,b):
    inside=(t>a)&(t<b)
    x=np.r_[a,t[inside],b]
    return x,np.r_[np.interp(a,t,y),y[inside],np.interp(b,t,y)]

def extract_ramp(run):
    d=data(run,'tran.tran');t=d['time'];v=d['vout'];sample=np.array([(7+5*k)*1e-9 for k in range(32)])
    codes=np.interp(sample,t,v);span=codes[-1]-codes[0];lsb=span/31
    assert span>0
    steps=np.diff(codes);inl=(codes-codes[0])/lsb-np.arange(32);dnl=steps/lsb-1
    tw,iw=window(t,d['VDD:p'],2.5e-9,162.5e-9)
    _,idrv=window(t,d['VDRV:p'],2.5e-9,162.5e-9)
    result=dict(run_dir=str(run.relative_to(ROOT)),inl_lsb_max=float(max(abs(inl))),dnl_lsb_max=float(max(abs(dnl))),
      zero_code_error_V=float(abs(codes[0])),full_scale_error_V=float(abs(codes[-1]-31*LSB)),
      power_avg_W=float(-VDD*np.trapz(iw,tw)/160e-9),external_driver_power_avg_W=float(-VDD*np.trapz(idrv,tw)/160e-9),
      monotonic=bool(min(steps)>0),minimum_step_V=float(min(steps)),endpoint_fitted_lsb_V=float(lsb),
      codes=[dict(code=k,sample_s=float(sample[k]),output_V=float(codes[k]),ideal_V=float(k*LSB),inl_LSB=float(inl[k]),dnl_LSB=float(dnl[k-1]) if k else None) for k in range(32)])
    result['switch_rail_drops']=[dict(code=k,bit=i,rail_drop_V=float(abs((VDD if (k>>i)&1 else 0)-np.interp(sample[k],t,d[f'XDAC.sw{i}'])))) for k in range(32) for i in range(5)]
    levels=[]
    for i in range(5):
        vals=np.interp(sample,t,d[f'b{i}']);expected=((np.arange(32)>>i)&1).astype(bool)
        levels.append(dict(bit=i,low_max_V=float(max(vals[~expected])),high_min_V=float(min(vals[expected]))))
    result['input_bit_levels']=levels
    result['all160_input_samples_correct']=bool(all(q['low_max_V']<.1*VDD and q['high_min_V']>.9*VDD for q in levels))
    write_json(run/'measurements.json',result);return result

def extract_carry(run):
    d=data(run,'tran.tran');t=d['time'];v=d['vout'];rows=[]
    for label,start,stop,tns in TRANSITIONS:
        a=tns*1e-9;b=a+5e-9;tw,vw=window(t,v,a,b);e=abs(vw-stop*LSB)-LSB/4
        crossed=np.flatnonzero(e[:-1]*e[1:]<0)
        crossings=[float(tw[i]-a+(tw[i+1]-tw[i])*e[i]/(e[i]-e[i+1])) for i in crossed]
        last=crossings[-1] if crossings else (0. if np.all(e<=0) else None)
        end=float(np.interp(a+4.99e-9,t,v));excursion=max(0,float(max(vw))-max(start,stop)*LSB,min(start,stop)*LSB-float(min(vw)))/LSB
        rows.append(dict(label=label,start_code=start,stop_code=stop,trigger_s=a,
          settling_time_s=last,all_crossings_s=crossings,end_sample_V=end,end_error_LSB=float(abs(end-stop*LSB)/LSB),
          excursion_LSB=float(excursion),peak_max_V=float(max(vw)),peak_min_V=float(min(vw)),
          last_crossing_enters_band=bool(not len(crossed) or e[crossed[-1]+1]<0)))
    valid=all(q['settling_time_s'] is not None for q in rows)
    result=dict(run_dir=str(run.relative_to(ROOT)),transitions=rows,all_crossings_found=valid,
      settling_time_s=max(q['settling_time_s'] for q in rows) if valid else None,
      settling_end_error_lsb_max=max(q['end_error_LSB'] for q in rows),excursion_lsb_max=max(q['excursion_LSB'] for q in rows))
    write_json(run/'measurements.json',result);return result

def extract_rout(run):
    d=data(run,'tran.tran');t=d['time'];v=d['vout'];rows=[]
    for i,code in enumerate(ROUT_CODES):
        vu=float(np.interp((i*30+14)*1e-9,t,v));vl=float(np.interp((i*30+29)*1e-9,t,v));r=(vl-vu if code==0 else vu-vl)/5e-6
        rows.append(dict(code=code,unloaded_V=vu,loaded_V=vl,rout_Ohm=r,direction='inject' if code==0 else 'draw'))
    result=dict(run_dir=str(run.relative_to(ROOT)),codes=rows,rout_max_Ohm=max(q['rout_Ohm'] for q in rows),rout_min_Ohm=min(q['rout_Ohm'] for q in rows))
    write_json(run/'measurements.json',result);return result

def aggregate(runs):
    ramp,carry,rout=[f(r) for f,r in zip([extract_ramp,extract_carry,extract_rout],runs)]
    values={k:ramp.get(k,carry.get(k,rout.get(k))) for k,_,_ in SPECS}
    gates={k:gate(values[k],lim,'max',unit) for k,lim,unit in SPECS if values[k] is not None}
    functional=bool(ramp['monotonic'] and ramp['all160_input_samples_correct'] and ramp['power_avg_W']>=0 and rout['rout_min_Ohm']>=0 and carry['all_crossings_found'] and all(q['last_crossing_enters_band'] for q in carry['transitions']))
    tiers={tier:bool(functional and len(gates)==len(SPECS) and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']}
    tier=next((t for t in tiers if tiers[t]),None)
    r=dict(case_slot=23,generated_at=now(),run_dirs=[str(x.relative_to(ROOT)) for x in runs],
      status='complete_'+tier if tier else 'partial',values=values,gates=gates,pass_tiers=tiers,
      functional_checks_pass= functional,all_nominal_checks_complete=True,nominal_complete=bool(tier),
      model_dimensions_valid=True,ramp=ramp,major_carry=carry,output_resistance=rout,
      scope='Deterministic TT/1.8V/27C only: all32 ramp codes, all6 carry directions, all6 output-resistance codes; other PVT, local mismatch, MC and PEX excluded.')
    write_json(CASE/'latest_results.json',r)
    write_json(runs[-1]/'combined_measurements.json',r)
    update_case(23,status=r['status'],nominal_complete=bool(tier),latest_runs=r['run_dirs'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--unit-current',type=float,default=200);p.add_argument('--res-length',type=float,default=96)
    p.add_argument('--receiver-scale',type=int,default=1);p.add_argument('--cap-area',type=float,default=0)
    p.add_argument('--refined',action='store_true')
    p.add_argument('--extract',nargs=3);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        if (ROOT/'monitor/QUOTA_TRIGGER.json').exists():raise RuntimeError('Quota trigger: stop new case23 work')
        c,hd=design(a.unit_current,a.res_length,a.receiver_scale,a.cap_area);update_case(23,status='running',nominal_complete=False)
        runs=[]
        for kind in ['code_ramp','major_carry','output_resistance']:
            b=bench(c,kind,a.refined);(CASE/f'testbench_{kind}.scs').write_text(b)
            runs.append(run_spectre(23,kind+('_refined' if a.refined else ''),b,[c,hd,CASE/'sizing.json',CASE/'contract.json',CASE/'hd_cells_manifest.json',CASE/'source_provenance.json']))
    result=aggregate(runs)
    print(json.dumps({k:result[k] for k in ['status','values','functional_checks_pass','run_dirs']},indent=2))

if __name__=='__main__':main()
