"""Size a SMIC18 5T OTA from target-PDK LUT and run the complete nominal contract."""
from __future__ import annotations
import argparse
import json
import numpy as np
from common import *

CASE=ROOT/'cases/44-ota5'

def design(gmid=18.0,branch_uA=90.0,pl=0.36,pgmid=6.0,nl=1.0):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={
      'input':lut_size('n18',nl,gmid,branch_uA*1e-6),
      'load':lut_size('p18',pl,pgmid,branch_uA*1e-6,vds=0.9),
      'tail':lut_size('n18',1.0,10,2*branch_uA*1e-6,vds=0.2),
      'reference':lut_size('n18',1.0,10,50e-6,vds=0.2),
    }
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    c=CASE/'circuit.scs'
    c.write_text(f'''// SMIC18MMRF 5T signal core plus bias replica.
// Dimensions are from sizing.json target-PDK gm/ID LUT, not scaled Sky130 widths.
simulator lang=spectre
subckt ota_5t (vss ibias vdd vinn vinp vout)
M1 (nleft vinp tail vss) n18 w={w['input']:.4f}u l={nl}u
M2 (vout vinn tail vss) n18 w={w['input']:.4f}u l={nl}u
M3 (nleft nleft vdd vdd) p18 w={w['load']:.4f}u l={pl}u
M4 (vout nleft vdd vdd) p18 w={w['load']:.4f}u l={pl}u
M5 (tail ibias vss vss) n18 w={w['tail']:.4f}u l=1u
M6 (ibias ibias vss vss) n18 w={w['reference']:.4f}u l=1u
ends ota_5t
''')
    sizing=dict(generated_at=now(),roles=roles,assumptions=['Zero-body-bias LUT gives initial sizing; actual input VSB is checked in the measured operating point.', 'Current mirror has matching L; target tail/reference ratio is set by LUT-derived widths.', 'Input gm is chosen for 1 pF UGB and integrated-noise budget; p-load uses lower gm/ID and shorter L to keep mirror pole fast.'])
    write_json(CASE/'sizing.json',sizing)
    contract=dict(source=str(SOURCE/'sky130-ota-5t-gain40-pm60-noise50uv-pvt'),corner='tt',vdd_V=1.8,temp_C=27,load_F=1e-12,reference_A=50e-6,metrics={'gain_db':['min',40,1000],'ugb_hz':['min',100e6],'phase_margin_deg':['min',60],'power_W':['max',.5e-3],'input_noise_Vrms':['max',50e-6,10,10e6],'cmrr_db':['min',50,1000],'psrr_plus_db':['min',30,1000],'psrr_minus_db':['min',30,1000]},nominal_checks_required=['OP/bias','double-injection Middlebrook gain/UGB/PM','closed-loop input-referred noise','total VDD power including reference','natural-open-loop CMRR','natural-open-loop PSRR+','natural-open-loop PSRR-'],not_in_scope=['other PVT points','Monte Carlo','layout extraction'])
    write_json(CASE/'contract.json',contract)
    return c

def bench(circuit):
    return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{circuit}"
simulatorOptions options temp=27 tnom=27 reltol=2e-5 vabstol=1e-8 iabstol=1e-14 gmin=1e-14
// Power/noise copy, same closed DC unity feedback as upstream.
VDDP (vddp 0) vsource dc=1.8
IBIASP (vddp ibias_p) isource dc=50u
VINP (vinp_p 0) vsource dc=.9 mag=1
VTESTP (vout_p vinn_p) vsource dc=0
XP (0 ibias_p vddp vinn_p vinp_p vout_p) ota_5t
CLP (vout_p 0) capacitor c=1p
// Voltage injection.
VDDV (vddv 0) vsource dc=1.8
IBIASV (vddv ibias_v) isource dc=50u
VINV (vinp_v 0) vsource dc=.9
VXV (mv xv) vsource dc=0
VYV (mv yv) vsource dc=0 mag=1
XV (0 ibias_v vddv xv vinp_v yv) ota_5t
CLV (yv 0) capacitor c=1p
// Current injection.
VDDI (vddi 0) vsource dc=1.8
IBIASI (vddi ibias_i) isource dc=50u
VINI (vinp_i 0) vsource dc=.9
VXI (mi xi) vsource dc=0
VYI (mi yi) vsource dc=0
ITI (0 mi) isource dc=0 mag=1
XI (0 ibias_i vddi xi vinp_i yi) ota_5t
CLI (yi 0) capacitor c=1p
// Natural open-loop differential/common-mode reference, no output clamp.
VDDR (vddr 0) vsource dc=1.8
IBIASDM (vddr ibias_dm) isource dc=50u
VDMP (vinp_dm 0) vsource dc=.9 mag=.5
VDMN (vinn_dm 0) vsource dc=.9 mag=.5 phase=180
XDM (0 ibias_dm vddr vinn_dm vinp_dm vout_dm) ota_5t
CLDM (vout_dm 0) capacitor c=1p
IBIASCM (vddr ibias_cm) isource dc=50u
VCMP (vinp_cm 0) vsource dc=.9 mag=1
VCMN (vinn_cm 0) vsource dc=.9 mag=1
XCM (0 ibias_cm vddr vinn_cm vinp_cm vout_cm) ota_5t
CLCM (vout_cm 0) capacitor c=1p
// Positive rail rejection, inputs fixed relative to ground.
VDDPS (vddps 0) vsource dc=1.8 mag=1
IBIASPS (vddps ibias_ps) isource dc=50u
VPSP (vinp_ps 0) vsource dc=.9
VPSN (vinn_ps 0) vsource dc=.9
XPS (0 ibias_ps vddps vinn_ps vinp_ps vout_ps) ota_5t
CLPS (vout_ps 0) capacitor c=1p
// Negative rail rejection, VDD and inputs fixed to absolute ground.
VSSMS (vssms 0) vsource dc=0 mag=1
VDDMS (vddms 0) vsource dc=1.8
IBIASMS (vddms ibias_ms) isource dc=50u
VMSP (vinp_ms 0) vsource dc=.9
VMSN (vinn_ms 0) vsource dc=.9
XMS (vssms ibias_ms vddms vinn_ms vinp_ms vout_ms) ota_5t
CLMS (vout_ms 0) capacitor c=1p
saveOptions options save=selected
save vout_p vinn_p vinp_p ibias_p XP.tail XP.nleft VDDP:p yv xv yi xi VXI:p VYI:p vout_dm vinp_dm vinn_dm vout_cm vinp_cm vinn_cm vout_ps vout_ms
save XP.M1:ids XP.M1:gm XP.M1:gds XP.M1:vgs XP.M1:vds XP.M1:vbs XP.M1:vdsat XP.M1:cgg XP.M1:region
save XP.M3:ids XP.M3:gm XP.M3:gds XP.M3:vgs XP.M3:vds XP.M3:vdsat XP.M3:region
save XP.M5:ids XP.M5:gm XP.M5:gds XP.M5:vgs XP.M5:vds XP.M5:vdsat XP.M5:region
dcOp dc
ac ac start=10 stop=10G dec=100
noise (vout_p 0) noise iprobe=VINP start=10 stop=10M dec=100
'''

def extract(run):
    a=data(run,'ac.ac');o=dc(run);noise=data(run,'noise.noise',required=('in','out'))
    f=a['freq'];tv=-a['yv']/a['xv'];ti=a['VYI:p']/a['VXI:p']
    loop=(tv*ti-1)/(tv+ti+2)
    lm=loop_metrics(f,loop)
    fn=noise['freq'];ni=noise['in']
    nrms=float(np.sqrt(np.trapz(np.abs(ni)**2,fn)))
    adm=a['vout_dm']/(a['vinp_dm']-a['vinn_dm']);acm=a['vout_cm']/((a['vinp_cm']+a['vinn_cm'])/2)
    ratios={'cmrr_db':adm/acm,'psrr_plus_db':adm/a['vout_ps'],'psrr_minus_db':adm/a['vout_ms']}
    values={**lm,'power_W':abs(1.8*o['VDDP:p']),'input_noise_Vrms':nrms}
    values.update({k:float(at(f,20*np.log10(np.abs(v)),1000)) for k,v in ratios.items()})
    gates={
      'gain_db':gate(values['gain_db'],40,'min','dB','amplitude_db'),
      'ugb_hz':gate(values['ugb_hz'],100e6,'min','Hz'),
      'phase_margin_deg':gate(values['phase_margin_deg'],60,'min','deg','phase_margin'),
      'power_W':gate(values['power_W'],.5e-3,'max','W'),
      'input_noise_Vrms':gate(values['input_noise_Vrms'],50e-6,'max','Vrms'),
      'cmrr_db':gate(values['cmrr_db'],50,'min','dB','amplitude_db'),
      'psrr_plus_db':gate(values['psrr_plus_db'],30,'min','dB','amplitude_db'),
      'psrr_minus_db':gate(values['psrr_minus_db'],30,'min','dB','amplitude_db'),
    }
    op={}
    for m in ['M1','M3','M5']:
        fields={k.split(':')[1]:v for k,v in o.items() if k.startswith('XP.'+m+':')}
        fields.update(gmid=abs(fields['gm']/fields['ids']),gmro=abs(fields['gm']/fields['gds']),headroom_V=abs(fields['vds'])-abs(fields['vdsat']))
        op[m]=fields
    bias_ok=all(v['headroom_V']>0 for v in op.values()) and abs(o['vout_p']-.9)<.03
    tiers={t:bool(bias_ok and all(g['passes'][t] for g in gates.values())) for t in ['original','10pct','15pct']}
    tier=next((t for t in tiers if tiers[t]),None)
    report=dict(generated_at=now(),case_slot=44,run_dir=str(run.relative_to(ROOT)),scope='SMIC18MMRF TT 1.8 V 27 C only',values=values,gates=gates,operating_point=op,dc_node_voltages={k:v for k,v in o.items() if ':' not in k},bias_valid=bias_ok,all_nominal_checks_complete=True,pass_tiers=tiers,status=('complete_'+tier) if tier else 'partial',testbench_translation='Upstream double voltage/current injection and natural open-loop rejection networks preserved in native Spectre; noise in is V/sqrt(Hz), integrated in quadrature from 10 Hz to 10 MHz.')
    write_json(run/'measurements.json',report);write_json(CASE/'latest_results.json',report)
    update_case(44,status=report['status'],nominal_complete=bool(tier),latest_run=str(run.relative_to(ROOT)),report=str((CASE/'latest_results.json').relative_to(ROOT)),sizing=str((CASE/'sizing.json').relative_to(ROOT)))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--gmid',type=float,default=18);p.add_argument('--branch-ua',type=float,default=90);p.add_argument('--pl',type=float,default=.36);p.add_argument('--pgmid',type=float,default=6);p.add_argument('--nl',type=float,default=1);p.add_argument('--extract')
    args=p.parse_args()
    if args.extract:run=ROOT/args.extract
    else:
        c=design(args.gmid,args.branch_ua,args.pl,args.pgmid,args.nl)
        (CASE/'testbench.scs').write_text(bench(c))
        update_case(44,status='running',nominal_complete=False)
        run=run_spectre(44,'ota5',bench(c),[c,CASE/'sizing.json',CASE/'contract.json'])
    print(json.dumps(extract(run),indent=2))

if __name__=='__main__':main()
