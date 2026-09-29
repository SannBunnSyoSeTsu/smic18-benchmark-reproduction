"""Low-power PMOS-output Miller amplifier with cascoded first-stage load."""
from common import *
import case16_miller as base
import argparse
CASE=ROOT/'cases/41-lowpower-miller'
LIMITS=dict(gain_db=70,ugb_hz=20e6,power_W=600e-6,psrr_1k_dB=65,psrr_1m_dB=20,cmrr_1k_dB=60,settling_s=30e-9,slew_rise_V_per_us=10,slew_fall_V_per_us=10)

def design(branch_uA=30,output_uA=140,cc_pf=2,rz=700,rb=22000,pgmid=10):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={'input':lut_size('n18',1,18,branch_uA*1e-6,.9),'n_bias_unit':lut_size('n18',1,12,10e-6,.2),'p_unit':lut_size('p18',.36,pgmid,10e-6,.45)}
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    c=CASE/'circuit.scs';c.write_text(f'''// Wide-swing cascoded input load and complementary output stage.
simulator lang=spectre
subckt two_stage_miller_opamp (vss iref vdd vinn vinp vout)
MREF (iref iref vss vss) n18 w={w['n_bias_unit']}u l=1u m=5
MTAIL (tail iref vss vss) n18 w={w['n_bias_unit']}u l=1u m={2*branch_uA/10:g}
MLOAD (vout iref vss vss) n18 w={w['n_bias_unit']}u l=1u m={output_uA/10:g}
MCBN (vbp iref vss vss) n18 w={w['n_bias_unit']}u l=1u
RB (vdd nrb) resistor r={rb}
MPCB (vbp vbp nrb vdd) p18 w={w['p_unit']}u l=.36u
MINN (nleft vinn tail vss) n18 w={w['input']}u l=1u
MINP (stage1 vinp tail vss) n18 w={w['input']}u l=1u
MPD (nc3 nleft vdd vdd) p18 w={w['p_unit']}u l=.36u m={branch_uA/10:g}
MPM (nc4 nleft vdd vdd) p18 w={w['p_unit']}u l=.36u m={branch_uA/10:g}
MCD (nleft vbp nc3 vdd) p18 w={w['p_unit']}u l=.36u m={branch_uA/10:g}
MCM (stage1 vbp nc4 vdd) p18 w={w['p_unit']}u l=.36u m={branch_uA/10:g}
MSECOND (vout stage1 vdd vdd) p18 w={w['p_unit']}u l=.36u m={output_uA/10:g}
RZ (stage1 comp) resistor r={rz}
CC (comp vout) capacitor c={cc_pf}p
ends two_stage_miller_opamp
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,branch_target_uA=branch_uA,output_target_uA=output_uA,cc_pF=cc_pf,rz_Ohm=rz,rb_Ohm=rb,n_reference_m=5,n_tail_m=2*branch_uA/10,n_output_m=output_uA/10,p_mirror_m=branch_uA/10,p_cascode_m=branch_uA/10,p_output_m=output_uA/10,rationale='Cascoded p mirror raises first-stage resistance and reduces supply feedthrough. PMOS second stage uses same unit current density as p mirror to align input drain voltages. Source-degenerated diode biases wide-swing cascodes with matching body bias. All currents derive from 50uA reference.'))
    contract=dict(source_task='sky130-two-stage-miller-opamp-gain70-ugb20-pm60-noise50uv-pvt',corner='tt',VDD_V=1.8,temperature_C=27,load_F=2e-12,reference_A=50e-6,VCM_V=.9,limits=LIMITS,phase_margin_min_deg=60,output_error_max_V=.025,input_noise_max_Vrms=50e-6,noise_gain=20,noise_frequency_range='10Hz to measured gain-20 closed-loop -3dB bandwidth',tracking_error_max_V=.02,contiguous_swing_min_Vpp=.8,swing_sweep_V=[.3,1.5],settling_step_V=[.85,.95],settling_windows_s=[[5e-9,65e-9],[66e-9,130e-9]],settling_final_error_max_V=.002,settling_fraction_max=.02,slew_input_V=[.65,1.15],slew_start_s=[10e-9,71e-9],slew_measurement_V=[.75,1.05],recross_forbidden=True,nominal_only=True)
    write_json(CASE/'contract.json',contract);return c

def static_bench(c,noise_high=None):
    b=base.static_bench(c,noise_high).replace('capacitor c=1p','capacitor c=2p')
    extra=''
    for dev in ['MCD','MCM','MPCB']:
        extra+='save '+' '.join(f'XL.{dev}:{x}' for x in ['ids','gm','gds','vgs','vds','vdsat','region'])+'\n'
    extra+='save XL.vbp XL.nrb XL.nc3 XL.nc4\n'
    # base saves obias for case16; this circuit uses vbp instead.
    return b.replace('XL.obias','XL.vbp')+extra

def dynamic_bench(c):
    b=base.dynamic_bench(c).replace('capacitor c=1p','capacitor c=2p')
    b=b.replace('0 .65 20n .65 21n 1.15 201n 1.15 202n .65 380n .65','0 .65 10n .65 11n 1.15 71n 1.15 72n .65 130n .65')
    return b.replace('380n','130n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--branch-ua',type=float,default=30);p.add_argument('--output-ua',type=float,default=140);p.add_argument('--cc-pf',type=float,default=2);p.add_argument('--rz',type=float,default=700);p.add_argument('--rb',type=float,default=22000);p.add_argument('--pgmid',type=float,default=10);p.add_argument('--extract',nargs=3);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        c=design(a.branch_ua,a.output_ua,a.cc_pf,a.rz,a.rb,a.pgmid);deps=[c,CASE/'sizing.json',CASE/'contract.json'];update_case(41,status='running',nominal_complete=False)
        b=static_bench(c);(CASE/'testbench_static.scs').write_text(b);r0=run_spectre(41,'static',b,deps);bw=base.noise_bw(r0)
        b=static_bench(c,bw);(CASE/'testbench_noise.scs').write_text(b);r1=run_spectre(41,'noise',b,deps)
        b=dynamic_bench(c);(CASE/'testbench_dynamic.scs').write_text(b);r2=run_spectre(41,'dynamic',b,deps);runs=[r0,r1,r2]
    r=base.extract(runs,slot=41,case=CASE,limit_overrides=LIMITS,op_devices=['MINP','MINN','MPM','MTAIL','MSECOND','MLOAD','MCD','MCM','MPCB'],slew_starts=(10e-9,70e-9))
    print(json.dumps({k:r[k] for k in ['status','values','operating_point']},indent=2))
if __name__=='__main__':main()
