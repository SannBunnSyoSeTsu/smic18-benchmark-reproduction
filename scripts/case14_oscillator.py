"""2MHz low-power ring: measured supply ramp, external2uA bias and1pF load."""
from common import *
from hd_cells import extract_hd
import argparse
import shutil

CASE=ROOT/'cases/14-oscillator'
TASK=SOURCE/'sky130-low-power-oscillator-2mhz-pvt'

def design(cap_area_um2=77.5,starve_m=2,first_buffer='INHDVL',output_buffer='INHDV0',unit_current_uA=.5):
    CASE.mkdir(parents=True,exist_ok=True);records=[]
    for rel in ['instruction.md','tests/verify.py','tests/benches/tb_osc.spi','solution/circuit.spi','results/reference.json']:
        src=TASK/rel;dst=CASE/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():shutil.copyfile(src,dst)
        assert sha(src)==sha(dst)
        records.append(dict(original=str(src),frozen=str(dst.relative_to(ROOT)),sha256=sha(src)))
    write_json(CASE/'source_provenance.json',dict(source_task=TASK.name,files=records))
    hd=extract_hd(['INHDVL',first_buffer,output_buffer],CASE)
    roles={d:lut_size(d,1,15,unit_current_uA*1e-6,.45) for d in ['n18','p18']}
    ref_m=2/unit_current_uA
    wn=roles['n18']['rounded_W_um'];wp=roles['p18']['rounded_W_um']
    text=f'''// 2MHz coarse oscillator; all digital stages are unmodified HD cells.
simulator lang=spectre
subckt osc_2m (AVDD AVSS CLKO IBN2U)
MNREF (IBN2U IBN2U AVSS AVSS) n18 w={wn:g}u l=1u m={ref_m:g}
MNBP (VBP IBN2U AVSS AVSS) n18 w={wn:g}u l=1u
MPREF (VBP VBP AVDD AVDD) p18 w={wp:g}u l=1u
'''
    for i in range(1,4):
        prev=3 if i==1 else i-1
        text+=f'MPS{i} (P{i} VBP AVDD AVDD) p18 w={wp:g}u l=1u m={starve_m:g}\n'
        text+=f'XINV{i} (N{prev} N{i} P{i} Q{i} AVDD AVSS) INHDVL\n'
        text+=f'MNS{i} (Q{i} IBN2U AVSS AVSS) n18 w={wn:g}u l=1u m={starve_m:g}\n'
        bottom='AVDD' if i==1 else 'AVSS'
        text+=f'CT{i} (N{i} {bottom}) mim w=10u l={cap_area_um2/10:g}u\n'
    text+=f'XBUF0 (N3 B1 AVDD AVSS AVDD AVSS) {first_buffer}\nXBUF1 (B1 CLKO AVDD AVSS AVDD AVSS) {output_buffer}\nends osc_2m\n'
    c=CASE/'circuit.scs';c.write_text(text)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,reference_unit_current_A=unit_current_uA*1e-6,external_bias_A=2e-6,
      reference_m=ref_m,mirror_transfer_m=1,stage_starve_m=starve_m,stage_count=3,ring_HD='INHDVL',buffer_HD=[first_buffer,output_buffer],HD_count=5,
      cap=dict(model='mim',width_um=10,length_um=cap_area_um2/10,area_um2=cap_area_um2,nominal_C_F=cap_area_um2*.971e-15,connections=['N1-to-AVDD','N2-to-AVSS','N3-to-AVSS']),
      first_order_frequency_Hz=starve_m*unit_current_uA*1e-6/(3*cap_area_um2*.971e-15*1.8),
      rationale=f'{ref_m:g} parallel n18 reference units take the external2uA; one equal unit feeds the PMOS reference, nominal{unit_current_uA:g}uA, to reduce bias overhead. Three pairs of analog current-limit devices, each m={starve_m:g}, feed unchanged HD inverters. gm/ID15 and1um length preserve mirror output resistance. Native MIM capacitance sets coarse2MHz timing. First capacitor toAVDD creates physical asymmetry during the specified1us ramp; no forced IC, hidden current source or ideal passive. Small HD first buffer limits slow-input overlap current; second HD buffer drives1pF.',
      LUT_temperature_C=27,verification_temperature_C=27,digital_analog_boundary='HD supply pins connect to analog limited rails; HD wells remain on global rails. No internal vendor device edits.'))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,corner='tt',capacitor_corner='mim_tt',temperature_C=27,VDD_V=1.8,
      supply_ramp_s=1e-6,external_bias_A=2e-6,bias_connection='From measured AVDD to IBN2U, exactly as original bench, included in VSENSE current',
      load_F=1e-12,stop_s=20e-6,measurement_window_s=[10e-6,20e-6],
      frequency_center_Hz=2e6,frequency_error_max_Hz=200e3,frequency_error_10pct_Hz=220e3,frequency_error_15pct_Hz=230e3,
      frequency_definition='10/(rising edge12 minus rising edge2), after10us, half-supply threshold0.9V',
      swing_center_VDD=1.,swing_error_max_VDD=.05,swing_error_10pct_VDD=.055,swing_error_15pct_VDD=.0575,
      swing_definition='(max(CLKO)-min(CLKO))/VDD over10–20us',power_max_W=20e-6,power_definition='VDD*abs(time-weighted mean current through VSENSE),10–20us, includes external2uA bias and full output driver',
      startup_scope='Supply ramps0→1.8V in1us; must sustain required oscillation by10us. No extra deadline before10us; first full-supply half-threshold crossing is diagnostic only.',
      prohibited_DUT='Ideal R/C, sources, behavioral elements, ideal switches, local models; DUT leaves are nativeMOS, nativeMIM and originalHDMOS',
      nominal_scope_excludes=['other4 disclosed representative PVT points','other ramp profiles','other loads','phase noise/jitter','mismatch/Monte Carlo','PEX']))
    return c,hd

def bench(c,step_ps=300):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{MODEL}" section=mim_tt
include "{CASE/'hd_cells.scs'}"
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=2e-5 vabstol=1e-8 iabstol=1e-14 gmin=1e-12
saveOptions options save=selected
VDD (AVDD_SRC 0) vsource type=pwl wave=[0 0 1u 1.8 20u 1.8]
VSENSE (AVDD_SRC AVDD) vsource dc=0
IBIAS (AVDD IBN2U) isource dc=2u
CLOAD (CLKO 0) capacitor c=1p
XDUT (AVDD 0 CLKO IBN2U) osc_2m
save AVDD CLKO IBN2U XDUT.VBP XDUT.N1 XDUT.N2 XDUT.N3 XDUT.B1 VSENSE:p
save XDUT.P1 XDUT.Q1
'''
    for dev in ['MNREF','MNBP','MPREF']:
        b+='save '+' '.join(f'XDUT.{dev}:{p}' for p in ['ids','gm','gds','vgs','vds','vdsat'])+'\n'
    return b+f'tran tran stop=20u maxstep={step_ps:g}p errpreset=conservative\n'

def cross(t,v,level=.9):
    i=np.flatnonzero((v[:-1]<level)&(v[1:]>=level))
    return t[i]+(t[i+1]-t[i])*(level-v[i])/(v[i+1]-v[i])

def window(t,v,a=10e-6,b=20e-6):
    i=(t>a)&(t<b)
    return np.r_[a,t[i],b],np.r_[np.interp(a,t,v),v[i],np.interp(b,t,v)]

def mean(t,v,a=10e-6,b=20e-6):
    tw,vw=window(t,v,a,b);return float(np.trapz(vw,tw)/(b-a))

def extract(run):
    d=data(run,'tran.tran');t=d['time'];v=d['CLKO'];edges=cross(t,v);stable=edges[(edges>=10e-6)&(edges<=20e-6)]
    tw,vw=window(t,v);isup=mean(t,d['VSENSE:p']);valid=len(stable)>=12
    frequency=float(10/(stable[11]-stable[1])) if valid else None
    ratio=float((max(vw)-min(vw))/1.8);power=1.8*abs(isup)
    vals=dict(frequency_Hz=frequency,frequency_error_Hz=abs(frequency-2e6) if frequency else None,swing_Vpp=float(max(vw)-min(vw)),swing_ratio=ratio,swing_error_ratio=abs(ratio-1),power_W=power)
    gates={}
    for k,lim,u in [('frequency_error_Hz',200e3,'Hz'),('swing_error_ratio',.05,'fraction'),('power_W',20e-6,'W')]:
        if vals[k] is not None:gates[k]=gate(vals[k],lim,'max',u)
    functional=bool(valid and isup>0 and edges[0]<10e-6)
    tiers={tier:bool(functional and len(gates)==3 and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']}
    tier=next((k for k in tiers if tiers[k]),None)
    bias={}
    for dev in ['MNREF','MNBP','MPREF']:
        q={p:mean(t,d[f'XDUT.{dev}:{p}']) for p in ['ids','gm','gds','vgs','vds','vdsat']}
        q['gmid']=abs(q['gm']/q['ids']);ix=(t>=10e-6)&(t<=20e-6)
        q['minimum_saturation_headroom_V']=float(min(abs(d[f'XDUT.{dev}:vds'][ix])-abs(d[f'XDUT.{dev}:vdsat'][ix])))
        bias[dev]=q
    supplywaves= dict(current_avg_A=isup,total_supply_charge_C=isup*10e-6,external_bias_power_W=1.8*2e-6,remaining_DUT_power_W=power-1.8*2e-6,
      theoretical_load_dynamic_power_W=1e-12*1.8**2*frequency if frequency else None,first_half_supply_crossing_s=float(edges[0]) if len(edges) else None,
      output_min_V=float(min(vw)),output_max_V=float(max(vw)),stable_rising_edges_s=stable.tolist(),period_10_s=float(stable[11]-stable[1]) if valid else None,
      frequency_edges_s=stable[1:12].tolist() if valid else [],all_period_average_Hz=float((len(stable)-1)/(stable[-1]-stable[0])) if len(stable)>=2 else None)
    supplywaves['all_periods_relative_frequency_difference']=abs(supplywaves['all_period_average_Hz']/frequency-1) if valid else None
    supplywaves['complete_cycles_in_saved_window']=len(stable)-1
    supplywaves['period_to_period_range_s']=[float(min(np.diff(stable))),float(max(np.diff(stable)))] if len(stable)>=2 else None
    supplywaves['frequency_ten_period_end_inside_window']=bool(valid and stable[11]<=20e-6)
    supplywaves['stage1_virtual_rails_V']={key:[float(min(window(t,d[key])[1])),float(max(window(t,d[key])[1]))] for key in ['XDUT.P1','XDUT.Q1']}
    supplywaves['full_supply_startup_note']='First0.9V crossing occurs during the specified ramp and is diagnostic. Frequency/swing/current are scored exclusively in the10–20us saved interval.'
    r=dict(case_slot=14,generated_at=now(),run_dir=str(run.relative_to(ROOT)),status='complete_'+tier if tier else 'partial',nominal_complete=bool(tier),
      values=vals,gates=gates,pass_tiers=tiers,functional_checks_pass=functional,all_nominal_checks_complete=valid,model_dimensions_valid=True,
      observations=supplywaves,bias_operating_conditions=bias,scope='TT/1.8V/27C, original1us ramp,2uA external bias,1pF load,10–20us measurement window. Other4PVT rows and noise/mismatch/PEX excluded.')
    write_json(run/'measurements.json',r);write_json(CASE/'latest_results.json',r)
    update_case(14,status=r['status'],nominal_complete=bool(tier),latest_run=r['run_dir'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--cap-area',type=float,default=77.5);p.add_argument('--starve-m',type=float,default=2);p.add_argument('--unit-current',type=float,default=.5)
    p.add_argument('--first-buffer',default='INHDVL');p.add_argument('--output-buffer',default='INHDV0');p.add_argument('--step',type=float,default=300);p.add_argument('--extract');a=p.parse_args()
    if a.extract:run=ROOT/a.extract
    else:
        if (ROOT/'monitor/QUOTA_TRIGGER.json').exists():raise RuntimeError('Quota trigger: stop new14 simulations')
        c,hd=design(a.cap_area,a.starve_m,a.first_buffer,a.output_buffer,a.unit_current);b=bench(c,a.step);(CASE/'testbench.scs').write_text(b)
        update_case(14,status='running',nominal_complete=False)
        run=run_spectre(14,'ramp',b,[c,hd,CASE/'sizing.json',CASE/'contract.json',CASE/'hd_cells_manifest.json',CASE/'source_provenance.json'])
    r=extract(run);print(json.dumps({k:r[k] for k in ['status','values','functional_checks_pass','run_dir']},indent=2))

if __name__=='__main__':main()
