"""Self-biased beta multiplier with PDK resistor and two cold-start ramps."""
from common import *
import argparse
CASE=ROOT/'cases/12-beta'

def design(res_length=36,core_gmid=7):
    CASE.mkdir(parents=True,exist_ok=True)
    pu=json.loads((ROOT/'lut_supplement/tt/p18_L4000nm_VDS1.800_W0.240.json').read_text())['data']
    pu_gmid=pu['gmid'][int(np.argmin(abs(np.asarray(pu['vgs_V'])-1.8)))]
    roles={'n_unit':lut_size('n18',4,core_gmid,10e-6,.9),'p_mirror':lut_size('p18',1,10,10e-6,.9),'startup_pullup':lut_size('p18',4,pu_gmid,3e-6,1.8,.24),'startup_detect':lut_size('n18',1,12,5e-6,.9),'startup_inject':lut_size('n18',4,7,1e-6,.9)}
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    p=CASE/'circuit.scs';p.write_text(f'''// Self-biased beta multiplier; native SMIC resistor, no external bias.
simulator lang=spectre
subckt beta_multiplier_reference (vss vdd vref iout)
MP1 (na na vdd vdd) p18 w={w['p_mirror']}u l=1u
MP2 (vref na vdd vdd) p18 w={w['p_mirror']}u l=1u
MN1 (vref vref vss vss) n18 w={w['n_unit']}u l=4u
MN2 (na vref nr vss) n18 w={w['n_unit']}u l=4u m=4
MOUT (iout vref vss vss) n18 w={w['n_unit']}u l=4u m=4
RGM (nr vss vss) rpposab_3t w=1u l={res_length}u
MPUP (nx vss vdd vdd) p18 w={w['startup_pullup']}u l=4u
MDET (nx vref vss vss) n18 w={w['startup_detect']}u l=1u
MSTART (na nx vss vss) n18 w={w['startup_inject']}u l=4u
ends beta_multiplier_reference
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,n_ratio=4,output_ratio=4,resistor=dict(model='rpposab_3t',W_um=1,L_um=res_length,nominal_sheet_ohm=311.3,nominal_R_estimate_Ohm=311.3*res_length/.9454,substrate_connection='vss'),startup='Weak long-channel PMOS pulls nx up while vref is low; MSTART pulls na down to start PMOS mirror. MDET clamps nx after vref rises. Injection self-disables; weak pullup draws a small persistent current included in power. Pullup sizing uses width-specific .24um LUT at VSG=1.8V, gm/ID about1.278; no moderate-inversion extrapolation.',rationale='10uA core branches plus 40uA output budget about 72uW before startup. n18 L4 reduces output conductance over 0.4-1.6V. gmID7 targets Vref about .657V. Ratio4 and approximately12k source resistance set nonzero current with body effect.'))
    write_json(CASE/'contract.json',dict(source_task='sky130-beta-multiplier-reference-pvt-mc',corner='tt',resistor_corner='res_tt',VDD_V=1.8,temperature_C=27,output_voltage_nominal_V=.9,output_current_target_A=40e-6,nominal_current_error_max_A=5e-6,vref_target_V=.675,vref_error_max_V=.075,power_max_W=100e-6,power_definition='max(0,-1.8*I(VDD)) + .9*Iout',compliance_range_V=[.4,1.6],compliance_points=121,flatness_definition='(max(I)-min(I))/mean(I)',flatness_max=.08,startup_ramps_s=[1e-6,10e-6],startup_observation_after_ramp_s=10e-6,startup_final_average_window_s=1e-6,startup_current_target_A=40e-6,startup_current_error_max_A=20e-6,startup_settling_max_s=10e-6,startup_overshoot_max=1.5,startup_peak_supply_current_max_A=100e-6,startup_positive_vdd_energy_max_J=1e-9,nominal_scope_excludes=['remaining 26 PVT combinations','stressed paired startup corners','Monte Carlo/mismatch'],passives='Native PDK resistor model, no ideal resistor substituted'))
    return p

def bench(c,ramp=None):
    supply='dc=1.8' if ramp is None else f'type=pwl wave=[0 0 {ramp} 1.8 {ramp+10e-6} 1.8]'
    b=f'''simulator lang=spectre
global 0
parameters vtest=.9
include "{MODEL}" section=tt
include "{MODEL}" section=res_tt
include "{c}"
VDD (vdd 0) vsource {supply}
VOUT (iout 0) vsource dc=vtest
XDUT (0 vdd vref iout) beta_multiplier_reference
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
save vdd vref iout XDUT.na XDUT.nr XDUT.nx VDD:p VOUT:p
'''
    for dev in ['MP1','MP2','MN1','MN2','MOUT','MPUP','MDET','MSTART']:
        b+='save '+' '.join(f'XDUT.{dev}:{q}' for q in ['ids','gm','gds','vgs','vds','vdsat','region'])+'\n'
    if ramp is None:b+='dcOp dc\ncompliance dc param=vtest start=.4 stop=1.6 step=.01\n'
    else:b+=f'tran tran stop={ramp+10e-6:.12g} maxstep=2n strobeperiod=5n strobeoutput=strobeonly errpreset=conservative\n'
    return b

def startup(run,ramp):
    d=data(run,'tran.tran');t=d['time'];curr=-d['VOUT:p'];ref=d['vref'];isup=np.maximum(0,-d['VDD:p']);final=float(np.mean(curr[t>=t[-1]-1e-6-1e-15]));tol=.1*abs(final)
    good=np.abs(curr-final)<=tol;stays=np.logical_and.accumulate(good[::-1])[::-1];indices=np.flatnonzero((t>=ramp-1e-15)&stays)
    settling=float(max(0,t[indices[0]]-ramp)) if len(indices) else None
    return dict(ramp_s=ramp,final_current_A=final,final_vref_V=float(ref[-1]),settling_s=settling,overshoot_ratio=float(np.max(curr)/final) if final>0 else None,peak_supply_current_A=float(max(isup)),positive_vdd_energy_J=float(np.trapz(d['vdd']*isup,t)),initial_vdd_V=float(d['vdd'][0]),initial_vref_V=float(ref[0]),observed_stop_s=float(t[-1]))

def extract(runs):
    o=dc(runs[0]);c=data(runs[0],'compliance.dc');curr=-c['VOUT:p'];assert len(curr)==121 and np.allclose(c['vtest'],np.linspace(.4,1.6,121))
    io=-o['VOUT:p'];power=max(0,-1.8*o['VDD:p'])+.9*io;flat=float((max(curr)-min(curr))/np.mean(curr))
    starts=[startup(r,ramp) for r,ramp in zip(runs[1:],[1e-6,10e-6])]
    gates=dict(current_error_A=gate(abs(io-40e-6),5e-6,'max','A'),vref_error_V=gate(abs(o['vref']-.675),.075,'max','V'),power_W=gate(power,100e-6,'max','W'),compliance_flatness=gate(flat,.08,'max','fraction'))
    valid_start=all(s['settling_s'] is not None and s['overshoot_ratio'] is not None and s['final_current_A']>0 for s in starts)
    if valid_start:
        for name,metric,limit,unit in [('startup_current_error_A','final_current_A',20e-6,'A'),('startup_vref_error_V','final_vref_V',.075,'V'),('startup_settling_s','settling_s',10e-6,'s'),('startup_overshoot','overshoot_ratio',1.5,'ratio'),('startup_peak_current_A','peak_supply_current_A',100e-6,'A'),('startup_energy_J','positive_vdd_energy_J',1e-9,'J')]:
            vals=[abs(s[metric]-40e-6) if metric=='final_current_A' else abs(s[metric]-.675) if metric=='final_vref_V' else s[metric] for s in starts];gates[name]=gate(max(vals),limit,'max',unit)
    op={}
    for dev in ['MP1','MP2','MN1','MN2','MOUT','MPUP','MDET','MSTART']:
        q={k.split(':')[1]:v for k,v in o.items() if k.startswith('XDUT.'+dev+':')};q['gmid']=abs(q['gm']/q['ids']);q['headroom_V']=abs(q['vds'])-abs(q['vdsat']);op[dev]=q
    tiers={t:bool(valid_start and io>0 and all(g['passes'][t] for g in gates.values())) for t in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    values=dict(output_current_A=io,vref_V=o['vref'],power_W=power,compliance_flatness=flat,compliance_min_A=float(min(curr)),compliance_max_A=float(max(curr)),core_resistance_Ohm=o['XDUT.nr']/op['MN2']['ids'],startup=starts)
    report=dict(case_slot=12,generated_at=now(),run_dirs=[str(r.relative_to(ROOT)) for r in runs],status='complete_'+tier if tier else 'partial',values=values,gates=gates,operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},all_nominal_checks_complete=valid_start,pass_tiers=tiers,model_dimensions_valid=True,scope='SMIC18 tt/res_tt 27C 1.8V; nominal current, 121-point output compliance, power including output, cold-start 1us and 10us ramps')
    write_json(runs[0]/'measurements.json',report);write_json(CASE/'latest_results.json',report);update_case(12,status=report['status'],nominal_complete=bool(tier),latest_runs=report['run_dirs'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--res-length',type=float,default=36);p.add_argument('--gmid',type=float,default=7);p.add_argument('--extract',nargs=3);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        c=design(a.res_length,a.gmid);update_case(12,status='running',nominal_complete=False);runs=[]
        for label,ramp in [('dc',None),('startup_1us',1e-6),('startup_10us',10e-6)]:
            b=bench(c,ramp);(CASE/f'testbench_{label}.scs').write_text(b);runs.append(run_spectre(12,label,b,[c,CASE/'sizing.json',CASE/'contract.json']))
    r=extract(runs);print(json.dumps({k:r[k] for k in ['status','values','operating_point']},indent=2))
if __name__=='__main__':main()
