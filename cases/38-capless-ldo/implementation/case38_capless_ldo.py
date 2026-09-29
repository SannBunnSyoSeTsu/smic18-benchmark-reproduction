"""Self-biased PMOS-pass LDO, internal977pF and full original load windows."""
from batch29 import *
import argparse
CASE=ROOT/'cases/38-capless-ldo';TASK=SOURCE/'sky130-capless-ldo-1v0-20ma-pvt'
MOS=['MPA','MPB','MN1','MN2','MPT','MIR','MIF','MNDR','MNDF','MNOUT','MNSINK','MPD','MPOUT','MPASS']

def design(rs=12300,cm=3,rz=2200,cf=10,cout=270,esrc=694,esr=150,pass_m=400,k=3.5,bias=5):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT27C, both1.5V/1.8V functional line conditions: full0..20mA DC,20mA PSR and0.5..20mA loadsteps; startupTT1.8V. Other28DC/step,8PSR,3startup PVTpoints excluded.',VDD_V=1.8,temperature_C=27,supplies_V=[1.5,1.8],vref_V=.4,output_target_V=1,dc_loads_A=[0,.02,.0002],psr_Hz=[1e3,1e5,1e6],psr_limits_dB={'1.5':[30,20,10],'1.8':[35,20,10]},cap_budget_F=1e-9,original_limits=dict(dc_error_V=.03,iq_A=100e-6,step_excursion_V=.15,step_recovery_V=.03,startup_peak_V=1.05,startup_tail_error_V=.02),step_windows_s=[[20e-6,41e-6],[60e-6,81e-6],[41e-6,60e-6],[81e-6,100e-6]],startup=dict(ramp_s=100e-6,stop_s=400e-6,load_ohm=2000,tail_s=[200e-6,400e-6]),nonrelaxable=['finite waveforms','PMOSpass with voltage-modefeedback','internal divider','positive RC','totalC<=1nF','no artificial externaloutputcapacitor'],ideal_passives=['R','C'],current_definition='No-load abs(IVIN), includes divider; idealVREF current explicitly free in original contract.'))
    roles=dict(nbias=lut_size('n18',1,10,bias*1e-6,.9),pbias=lut_size('p18',1,14,bias*1e-6,.9),input=lut_size('p18',.36,18,bias/2*1e-6,.45),nmirror=lut_size('n18',1,14,bias/2*1e-6,.9),pmirror=lut_size('p18',1,14,bias/2*1e-6,.9),pass_unit=lut_size('p18',.36,10,50e-6,.45))
    w={n:q['rounded_W_um'] for n,q in roles.items()}
    text=f'''simulator lang=spectre
subckt capless_ldo (vin vout vss vref)
RSTART (vin nb) resistor r=1Meg
MPA (nb pb vin vin) p18 w={w['pbias']}u l=1u
MPB (pb pb vin vin) p18 w={w['pbias']}u l=1u
MN1 (nb nb vss vss) n18 w={w['nbias']}u l=1u
MN2 (pb nb ns vss) n18 w={w['nbias']}u l=1u m=4
RS (ns vss) resistor r={rs:g}
MPT (tail pb vin vin) p18 w={w['pbias']}u l=1u
MIR (nr vref tail tail) p18 w={w['input']}u l=.36u
MIF (nf fb tail tail) p18 w={w['input']}u l=.36u
MNDR (nr nr vss vss) n18 w={w['nmirror']}u l=1u
MNDF (nf nf vss vss) n18 w={w['nmirror']}u l=1u
MNOUT (gate nf vss vss) n18 w={w['nmirror']}u l=1u m={k:g}
MNSINK (pc nr vss vss) n18 w={w['nmirror']}u l=1u m={k:g}
MPD (pc pc vin vin) p18 w={w['pmirror']}u l=1u m={k:g}
MPOUT (gate pc vin vin) p18 w={w['pmirror']}u l=1u m={k:g}
MPASS (vout gate vin vin) p18 w={w['pass_unit']}u l=.36u m={pass_m:g}
CM (gate cmx) capacitor c={cm:g}p
RZ (cmx vout) resistor r={rz:g}
R1 (vout fb) resistor r=30k
CF (vout fb) capacitor c={cf:g}p
R2 (fb vss) resistor r=20k
RESR (vout vc) resistor r={esr:g}
C1 (vc vss) capacitor c={esrc:g}p
C2 (vout vss) capacitor c={cout:g}p
ends capless_ldo
'''
    assert cm+cf+esrc+cout<=1000
    save_design(CASE,text,roles,dict(rs=rs,cm=cm,rz=rz,cf=cf,cout=cout,esrc=esrc,esr=esr,pass_m=pass_m,k=k,bias=bias,total_cap_pF=cm+cf+esrc+cout),'Beta4 self-bias with persistent1Mohm starter; PMOSinput/bodytail, K3.5 current-mirror OTA controls PMOSpass. Unit50uA pass gmID10 atL.36, parallel legalgeometry. Internal30k/20k divider, MillerRC and splitdampedoutputC retain original977pF abstraction.')

def bench(vin,kind,step=20e-9,reltol=1e-6,dc_step=.0002,dec=40):
    supply=f'dc={vin:g} mag=1'
    if kind=='start':supply='type=pwl wave=[0 0 100u 1.8 400u 1.8]'
    load='dc=0' if kind=='dc' else 'dc=.02'
    if kind=='step':load='type=pwl wave=[0 .0005 20u .0005 21u .02 60u .02 61u .0005 100u .0005]'
    b=f'''simulator lang=spectre
global 0
parameters iload=0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-9 iabstol=1e-14
saveOptions options save=selected
VSUP (vin 0) vsource {supply}
VREF (vref 0) vsource dc=.4
X (vin vout 0 vref) capless_ldo
save vin vout VSUP:p VREF:p X.nb X.pb X.ns X.tail X.nr X.nf X.pc X.gate X.fb X.vc
'''
    b+=('RLOAD (vout 0) resistor r=2k\n' if kind=='start' else f'ILOAD (vout 0) isource '+('dc=iload' if kind=='dc' else load)+'\n')
    for dev in MOS:b+='save '+' '.join(f'X.{dev}:{k}' for k in ['ids','gm','gds','vgs','vds','vdsat','region'])+'\n'
    if kind=='dc':b+=f'dcOp dc\nloads dc param=iload start=0 stop=.02 step={dc_step:g}\n'
    elif kind=='psr':b+=f'dcOp dc\nac ac start=100 stop=10M dec={dec}\n'
    else:b+=f'tran tran stop={"400u" if kind=="start" else "100u"} maxstep={step:g} method=gear2only errpreset=conservative\n'
    return b

def window(t,v,a,b):
    return np.r_[np.interp(a,t,v),v[(t>a)&(t<b)],np.interp(b,t,v)]

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());rows=[];g={};ops={}
    for vin in [1.5,1.8]:
        tag=str(vin);rd=ROOT/runs['dc'+tag];o=dc(rd);d=data(rd,'loads.dc');p=data(ROOT/runs['psr'+tag],'ac.ac');s=data(ROOT/runs['step'+tag],'tran.tran');t=s['time'];v=s['vout']
        a,b,ta,tb=[window(t,v,x*1e-6,y*1e-6) for x,y in [(20,41),(60,81),(41,60),(81,100)]]
        row=dict(supply_V=vin,dc_min_V=float(min(d['vout'])),dc_max_V=float(max(d['vout'])),dc_error_V=float(max(abs(d['vout']-1))),iq_A=abs(o['VSUP:p']),vref_current_A=o['VREF:p'],psr1k_dB=float(np.interp(1e3,p['freq'],-20*np.log10(abs(p['vout'])))),psr100k_dB=float(np.interp(1e5,p['freq'],-20*np.log10(abs(p['vout'])))),psr1M_dB=float(np.interp(1e6,p['freq'],-20*np.log10(abs(p['vout'])))),droop_V=float(min(a)),w1max_V=float(max(a)),bump_V=float(max(b)),w2min_V=float(min(b)),t1min_V=float(min(ta)),t1max_V=float(max(ta)),t2min_V=float(min(tb)),t2max_V=float(max(tb)),step_excursion_V=float(max(abs(np.r_[a,b]-1))),step_recovery_V=float(max(abs(np.r_[ta,tb]-1))))
        rows.append(row)
        for key,lim,kind in [('dc_error_V',.03,'linear'),('iq_A',100e-6,'linear'),('step_excursion_V',.15,'linear'),('step_recovery_V',.03,'linear')]:g[tag+'_'+key]=gate(row[key],lim,'max','V/A',kind=kind)
        for key,lim in [('psr1k_dB',30 if vin==1.5 else 35),('psr100k_dB',20),('psr1M_dB',10)]:g[tag+'_'+key]=gate(row[key],lim,'min','dB',kind='amplitude_db')
        op=dc(ROOT/runs['psr'+tag]);ops[tag]={n:{k:op[f'X.{n}:{k}'] for k in ['ids','gm','gds','vgs','vds','vdsat','region']} for n in MOS}
    st=data(ROOT/runs['start'],'tran.tran');tail=window(st['time'],st['vout'],200e-6,400e-6);start=dict(peak_V=float(max(st['vout'])),tail_min_V=float(min(tail)),tail_max_V=float(max(tail)),tail_error_V=float(max(abs(tail-1))))
    g['startup_peak_excess_V']=gate(max(0,start['peak_V']-1),.05,'max','V');g['startup_tail_error_V']=gate(start['tail_error_V'],.02,'max','V')
    return result(CASE,38,dict(line_points=rows,startup=start),g,runs,True,operating_point=ops)

def run(step=20e-9,reltol=1e-6,dc_step=.0002,dec=40):
    benches={kind+str(v):bench(v,kind,step,reltol,dc_step,dec) for v in [1.5,1.8] for kind in ['dc','psr','step']};benches['start']=bench(1.8,'start',step*10,reltol)
    simulate_groups(38,CASE,benches);return extract()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k,d in [('rs',12300),('cm',3),('rz',2200),('cf',10),('cout',270),('esrc',694),('esr',150),('pass-m',400),('k',3.5),('bias',5)]:p.add_argument('--'+k,type=float,default=d)
    a=p.parse_args();design(**vars(a));update_case(38,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));run()
