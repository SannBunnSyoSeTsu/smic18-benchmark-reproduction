"""LUT-sized source-degenerated differential amplifier, complete nominal tests."""
from common import *
import argparse
CASE=ROOT/'cases/04-gmr'

def design(gmid=18,branch_uA=250,rs=600,rl=1989):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={'input':lut_size('n18',.36,gmid,branch_uA*1e-6,.9),'tail':lut_size('n18',1,16,2*branch_uA*1e-6,.2),'reference':lut_size('n18',1,16,50e-6,.2)}
    w={k:v['rounded_W_um'] for k,v in roles.items()};tail_m=2*branch_uA/50
    p=CASE/'circuit.scs';p.write_text(f'''// SMIC18 source-degenerated differential amplifier. VCM port is unused.
simulator lang=spectre
subckt gmr_degen (IREF VCM VDD VIN VIP VON VOP VSS)
MREF (IREF IREF VSS VSS) n18 w={w['reference']:.4f}u l=1u
MTAIL (tail IREF VSS VSS) n18 w={w['reference']:.4f}u l=1u m={tail_m:g}
MINN (VON VIN sn VSS) n18 w={w['input']:.4f}u l=.36u
MINP (VOP VIP sp VSS) n18 w={w['input']:.4f}u l=.36u
RSN (sn tail) resistor r={rs}
RSP (sp tail) resistor r={rs}
RLN (VDD VON) resistor r={rl}
RLP (VDD VOP) resistor r={rl}
ends gmr_degen
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,implementation=dict(tail=dict(unit_W_um=w['reference'],multiplicity=tail_m,total_W_um=tail_m*w['reference']),model_max_unit_width_um=100),source_resistance_ohm=rs,load_resistance_ohm=rl,initial_rationale='gm_eff approximately gm/[1+(gm+gmb)*Rs], gain approximately gm_eff*RL; output pole includes 1 pF. High input gm/ID supports VCM headroom; source degeneration consumes Id*Rs headroom. Body effect and finite ro are measured, not omitted from final validation. Tail uses reference-sized units within PDK width range.'))
    write_json(CASE/'contract.json',dict(source_task='sky130-gmr-degenerated-diff-amp-gain2-bw70m-power1p2mw-sdr60',corner='tt',VDD_V=1.8,VCM_V=.9,load_each_F=1e-12,IREF_A=50e-6,ac_gain_at_hz=1e6,ac_gain_target=2,ac_gain_error_max=.02,bw_min_hz=70e6,power_max_W=1.2e-3,SDR_min_dB=60,transient_frequency_hz=3e6,differential_peak_V=.1,fundamental_gain_target=2,fundamental_gain_error_max=.1,fit_window_s=[.5e-6,1.5e-6],error_relaxation='Expand error about fixed gain 2, never change gain target',power_ports=['VDD','VCM','VIN','VIP']))
    return p

def bench(p):
    return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{p}"
simulatorOptions options temp=27 tnom=27 reltol=1e-5 vabstol=1e-9 iabstol=1e-14
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=50u
VCM (vcm 0) vsource dc=.9
VIP (vip 0) vsource dc=.9 mag=.5 type=sine ampl=50m freq=3M
VIN (vin 0) vsource dc=.9 mag=.5 phase=180 type=sine ampl=50m freq=3M sinephase=180
XDUT (iref vcm vdd vin vip von vop 0) gmr_degen
CLP (vop 0) capacitor c=1p
CLN (von 0) capacitor c=1p
saveOptions options save=selected
save vdd vcm vin vip von vop iref XDUT.tail XDUT.sn XDUT.sp VDD:p VCM:p VIN:p VIP:p
save XDUT.MINP:ids XDUT.MINP:gm XDUT.MINP:gmbs XDUT.MINP:gds XDUT.MINP:vgs XDUT.MINP:vds XDUT.MINP:vdsat XDUT.MINP:region
save XDUT.MTAIL:ids XDUT.MTAIL:gm XDUT.MTAIL:vds XDUT.MTAIL:vdsat XDUT.MTAIL:region
dcOp dc
ac ac start=100k stop=11G dec=150
tran tran stop=1.5u maxstep=500p strobeperiod=1n strobeoutput=strobeonly errpreset=conservative
'''

def extract(run,slot=4,case=CASE,bandwidth_min=70e6,power_max=1.2e-3,op_devices=None):
    a=data(run,'ac.ac');o=dc(run);d=data(run,'tran.tran');f=a['freq'];gain=abs(a['vop']-a['von']);g1=float(at(f,gain,1e6));target=g1/np.sqrt(2)
    cross=np.flatnonzero((gain[:-1]>target)&(gain[1:]<=target))
    if len(cross):
        i=cross[0];r=(np.log(gain[i])-np.log(target))/(np.log(gain[i])-np.log(gain[i+1]));bw=float(np.exp(np.log(f[i])+r*np.log(f[i+1]/f[i])))
    elif at(f,gain,10e9)>target:bw=10e9
    else:raise RuntimeError('Missing bandwidth crossing')
    power=sum(abs(o[node]*o[src+':p']) for node,src in [('vdd','VDD'),('vcm','VCM'),('vin','VIN'),('vip','VIP')])
    mask=(d['time']>=.5e-6-1e-15)&(d['time']<=1.5e-6+1e-15);t=d['time'][mask];y=(d['vop']-d['von'])[mask]
    assert len(t)>=100
    b=np.column_stack([np.ones(len(t)),np.sin(2*np.pi*3e6*t),np.cos(2*np.pi*3e6*t)]);coef=np.linalg.lstsq(b,y,rcond=None)[0]
    err=y-b@coef;fund=np.hypot(coef[1],coef[2]);sdr=float(10*np.log10((fund**2/2)/np.mean(err**2)))
    fg=float(fund/.1)
    values=dict(gain_1MHz=g1,bandwidth_Hz=bw,power_W=power,SDR_dB=sdr,fundamental_gain=fg,fit_samples=len(t),fit_offset_V=float(coef[0]),fit_residual_rms_V=float(np.sqrt(np.mean(err**2))))
    gates={'gain_error':gate(abs(g1-2),.02,'max','V/V'),'bandwidth_Hz':gate(bw,bandwidth_min,'min','Hz'),'power_W':gate(power,power_max,'max','W'),'SDR_dB':gate(sdr,60,'min','dB','amplitude_db'),'fundamental_gain_error':gate(abs(fg-2),.1,'max','V/V')}
    op={}
    for m in (op_devices or ['MINP','MTAIL']):
        vals={k.split(':')[1]:v for k,v in o.items() if k.startswith('XDUT.'+m+':')};vals['gmid']=abs(vals['gm']/vals['ids']);vals['headroom_V']=abs(vals['vds'])-abs(vals['vdsat']);op[m]=vals
    bias=all(v['headroom_V']>0 for v in op.values())
    tiers={t:bool(bias and all(g['passes'][t] for g in gates.values())) for t in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    report=dict(case_slot=slot,generated_at=now(),run_dir=str(run.relative_to(ROOT)),values=values,gates=gates,operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},bias_valid=bias,all_nominal_checks_complete=True,pass_tiers=tiers,status='complete_'+tier if tier else 'partial',scope='SMIC18 nominal only; original input/load/power boundary and sine-fit SDR definition')
    write_json(run/'measurements.json',report);write_json(case/'latest_results.json',report);update_case(slot,status=report['status'],nominal_complete=bool(tier),latest_run=report['run_dir'],report=str((case/'latest_results.json').relative_to(ROOT)))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--gmid',type=float,default=18);p.add_argument('--branch-ua',type=float,default=250);p.add_argument('--rs',type=float,default=600);p.add_argument('--rl',type=float,default=1989);p.add_argument('--extract');a=p.parse_args()
    if a.extract:r=ROOT/a.extract
    else:
        c=design(a.gmid,a.branch_ua,a.rs,a.rl);text=bench(c);(CASE/'testbench.scs').write_text(text);update_case(4,status='running',nominal_complete=False)
        r=run_spectre(4,'gmr',text,[c,CASE/'sizing.json',CASE/'contract.json'])
    x=extract(r);print(json.dumps({k:x[k] for k in ['status','values','operating_point','dc_nodes']},indent=2))
if __name__=='__main__':main()
