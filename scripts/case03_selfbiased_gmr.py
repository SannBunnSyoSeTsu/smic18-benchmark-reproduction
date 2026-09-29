"""Self-biased beta-multiplier GM-R, independent case03 nominal implementation."""
from common import *
import case04_gmr as base
import argparse
CASE=ROOT/'cases/03-selfbiased-gmr'
DEVS=['MINP','MTAIL','MB1','MB2','MP1','MP2','MST']

def design(rb=3000,rs=500,rl=1770,core=20,branch=250,gmid=16):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={'n_unit':lut_size('n18',.36,gmid,core*1e-6,.45),'p_mirror':lut_size('p18',1,10,core*1e-6,.9),'reference':lut_size('n18',1,12,50e-6,.45),'startup':lut_size('n18',4,8.55815194812451,3.7547949603946485e-7,1.35,.24)}
    w={k:v['rounded_W_um'] for k,v in roles.items()};c=CASE/'circuit.scs'
    c.write_text(f'''// Beta-biased source-degenerated GM-R; VCM is a compatibility port.
simulator lang=spectre
subckt gmr_degen (IREF VCM VDD VIN VIP VON VOP VSS)
MREF (IREF IREF VSS VSS) n18 w={w['reference']:g}u l=1u
MST (nc IREF VSS VSS) n18 w={w['startup']:g}u l=4u
MB1 (nb nb VSS VSS) n18 w={w['n_unit']:g}u l=.36u
MB2 (nc nb rb2 VSS) n18 w={w['n_unit']:g}u l=.36u m=4
RB (rb2 VSS) resistor r={rb:g}
MP1 (nb nc VDD VDD) p18 w={w['p_mirror']:g}u l=1u
MP2 (nc nc VDD VDD) p18 w={w['p_mirror']:g}u l=1u
MTAIL (tail nb VSS VSS) n18 w={w['n_unit']:g}u l=.36u m={2*branch/core:g}
MINN (VON VIN sn VSS) n18 w={w['n_unit']:g}u l=.36u m={branch/core:g}
MINP (VOP VIP sp VSS) n18 w={w['n_unit']:g}u l=.36u m={branch/core:g}
RSN (sn tail) resistor r={rs:g}
RSP (sp tail) resistor r={rs:g}
RLN (VDD VON) resistor r={rl:g}
RLP (VDD VOP) resistor r={rl:g}
ends gmr_degen
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,core_target_uA=core,branch_target_uA=branch,n_beta_m=4,n_tail_m=2*branch/core,n_input_m=branch/core,rb_Ohm=rb,rs_Ohm=rs,rl_Ohm=rl,rationale='The input and beta master share unit current density. Beta RB sets gm while source degeneration reduces signal nonlinearity. All devices remain below100um unit width; no capacitors or sources in DUT. PVT gain stability remains outside nominal-only validation.'))
    write_json(CASE/'contract.json',dict(source_task='sky130-gmr-degen-amp-constant-gm-pvt',corner='tt',temperature_C=27,VDD_V=1.8,VCM_V=.9,load_each_F=1e-12,IREF_A=50e-6,gain_target=2,gain_error_max=.02,gain_frequency_Hz=1e6,bandwidth_min_Hz=60e6,power_max_W=.0015,power_ports=['VDD','VCM','VIN','VIP'],SDR_min_dB=60,sine_Hz=3e6,differential_peak_V=.1,fundamental_gain_range=[1.9,2.1],fit_window_s=[.5e-6,1.5e-6],legal_DUT_leaves='MOS and positive resistors; no intentional capacitors',nominal_scope_excludes=['remaining14 process-temperature points','supplyvariation','mismatch','PEX']))
    return c

def bench(c):
    b=base.bench(c)
    for dev in DEVS[2:]:b+='save '+' '.join(f'XDUT.{dev}:{x}' for x in ['ids','gm','gds','vgs','vds','vdsat','region'])+'\n'
    return b+'save XDUT.nb XDUT.nc XDUT.rb2\n'

def main():
    p=argparse.ArgumentParser()
    for n,v in [('rb',3000),('rs',500),('rl',1770),('core',20),('branch',250),('gmid',16)]:p.add_argument('--'+n,type=float,default=v)
    p.add_argument('--extract');a=p.parse_args()
    if a.extract:run=ROOT/a.extract
    else:
        c=design(a.rb,a.rs,a.rl,a.core,a.branch,a.gmid);b=bench(c);(CASE/'testbench.scs').write_text(b);update_case(3,status='running',nominal_complete=False);run=run_spectre(3,'gmr',b,[c,CASE/'sizing.json',CASE/'contract.json'])
    r=base.extract(run,slot=3,case=CASE,bandwidth_min=60e6,power_max=.0015,op_devices=DEVS);print(json.dumps({k:r[k] for k in ['status','values','operating_point','dc_nodes']},indent=2))
if __name__=='__main__':main()
