"""Native-device NMOS LDO with two original load points and series loop injection."""
from batch29 import *
import argparse
CASE=ROOT/'cases/17-nmos-ldo';TASK=SOURCE/'sky130-nmos-pass-ldo-0p4v-pvt-mc'
MOS=['MPREF','MPTAIL','MPINR','MPINF','MNDR','MNDF','MNSINK','MNOUT','MPD','MPOUT','MPASS']

def design(cgate=100,cout=20,k=2,tail=80,pass_m=100):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C, both1mA/5mA loads. Other52 PVT/load points and50 mismatch seeds excluded.',VDD_V=1.8,temperature_C=27,loads_A=[.001,.005],vref_V=.4,bias_sink_A=40e-6,external_cap_F=10e-12,ac_Hz=[1,1e9],ac_dec=40,original_limits=dict(output_error_V=.05,iq_max_A=400e-6,phase_margin_deg=45,gain_margin_db=6,psrr_1khz_db=40,headroom_V=.03),nonrelaxable=['finite complete both load cases','nonnegative Iq','all active MOS headroom>30mV','PM>45deg','native devices only'],measurement='Original series return ratio -Vloop_out/Vpass_gate, first falling0dB and -180degree crossings; IQ=-IVDD-ILOAD-40uA. Independent STB added as diagnostic; weaker stability decides acceptance.',acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    roles=dict(pbias=lut_size('p18',1,14,10e-6,.9),input=lut_size('p18',1,18,10e-6,.45),nmirror=lut_size('n18',1,14,10e-6,.9),pmirror=lut_size('p18',1,14,10e-6,.9),pass_unit=lut_size('n18',.18,14,50e-6,.9))
    w={n:q['rounded_W_um'] for n,q in roles.items()};m=tail/20
    text=f'''simulator lang=spectre
subckt nmos_pass_ldo (vdd vout vss vref ibias loop_out pass_gate)
MPREF (ibias ibias vdd vdd) p18 w={w['pbias']}u l=1u m=4
MPTAIL (tail ibias vdd vdd) p18 w={w['pbias']}u l=1u m={tail/10:g}
MPINR (nr vref tail vdd) p18 w={w['input']}u l=1u m={m:g}
MPINF (nf vout tail vdd) p18 w={w['input']}u l=1u m={m:g}
MNDR (nr nr vss vss) n18 w={w['nmirror']}u l=1u m={m:g}
MNDF (nf nf vss vss) n18 w={w['nmirror']}u l=1u m={m:g}
MNSINK (pc nf vss vss) n18 w={w['nmirror']}u l=1u m={m*k:g}
MNOUT (loop_out nr vss vss) n18 w={w['nmirror']}u l=1u m={m*k:g}
MPD (pc pc vdd vdd) p18 w={w['pmirror']}u l=1u m={m*k:g}
MPOUT (loop_out pc vdd vdd) p18 w={w['pmirror']}u l=1u m={m*k:g}
MPASS (vdd pass_gate vout vss) n18 w={w['pass_unit']}u l=.18u m={pass_m:g}
CGATE (loop_out vss) mim w=100u l=100u m={cgate/9.71:.12g}
COUT (vout vss) mim w=100u l=100u m={cout/9.71:.12g}
ends nmos_pass_ldo
'''
    save_design(CASE,text,roles,dict(cgate=cgate,cout=cout,k=k,tail=tail,pass_m=pass_m),'PMOS input handles0.4V commonmode; two current-mirror branches shift output to NMOS gate voltage without violating input headroom. 80uA tail andK2 mirror target240uA IQ. NativeMIM dominantgate compensation; pass sized5mA/gmID14 from50uA legal units.')

def bench(load,mode,dec=40,reltol=1e-6):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{MODEL}" section=mim_tt
include "{CASE/'circuit.scs'}"
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-9 iabstol=1e-14
saveOptions options save=selected
VDD (vdd 0) vsource dc=1.8 mag={1 if mode=='psrr' else 0}
VREF (vref 0) vsource dc=.4
IBIAS (ibias 0) isource dc=40u
ILOAD (vout 0) isource dc={load:g}
CLOAD (vout 0) capacitor c=10p
VLOOP (loop_out probe) vsource dc=0 mag={1 if mode=='loop' else 0}
IP (probe pass_gate) iprobe
X (vdd vout 0 vref ibias loop_out pass_gate) nmos_pass_ldo
save vout vdd vref ibias loop_out pass_gate VDD:p X.tail X.nr X.nf X.pc
'''
    for d in MOS:b+='save '+' '.join(f'X.{d}:{k}' for k in ['ids','gm','gds','vgs','vds','vbs','vdsat','region'])+'\n'
    return b+f'dcOp dc\nac ac start=1 stop=1G dec={dec}\n'+(f'loop stb probe=IP start=1 stop=1G dec={dec}\n' if mode=='loop' else '')

def crossing(x,y,target):
    ix=np.flatnonzero((y[:-1]>=target)&(y[1:]<target));assert len(ix),'Missing required falling crossing'
    i=int(ix[0]);f=(target-y[i])/(y[i+1]-y[i]);return i,float(f),float(x[i]+f*(x[i+1]-x[i]))

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());rows=[];gates={};ops={}
    for ma in [1,5]:
        rd=ROOT/groups[f'loop{ma}'];d=data(rd,'ac.ac');s=data(rd,'loop.stb');p=data(ROOT/groups[f'psrr{ma}'],'ac.ac');o=dc(rd)
        loop=-d['loop_out']/d['pass_gate'];mag=20*np.log10(abs(loop));ph=np.unwrap(np.angle(loop))*180/np.pi
        i,a,fu=crossing(d['freq'],mag,0);pm=180+ph[i]+a*(ph[i+1]-ph[i]);j,b,fp=crossing(d['freq'],ph,-180);gm=-(mag[j]+b*(mag[j+1]-mag[j]))
        # Spectre's stored loopGain is the signed return (DC phase+180deg).
        # Use negative-feedback T=-return for the conventional180+phase margin.
        st=-s['loopGain'];sm=20*np.log10(abs(st));sp=np.unwrap(np.angle(st))*180/np.pi
        si,sa,sfu=crossing(s['freq'],sm,0);spm=180+sp[si]+sa*(sp[si+1]-sp[si]);sj,sb,sfp=crossing(s['freq'],sp,-180);sgm=-(sm[sj]+sb*(sm[sj+1]-sm[sj]))
        op={}
        for dev in MOS:
            q={k:o[f'X.{dev}:{k}'] for k in ['ids','gm','gds','vgs','vds','vbs','vdsat','region']};q.update(gmid=abs(q['gm']/q['ids']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[dev]=q
        ops[str(ma)]=op
        row=dict(load_mA=ma,vout_V=o['vout'],iq_A=-o['VDD:p']-ma*1e-3-40e-6,loop_ugb_Hz=fu,phase_margin_deg=float(pm),gain_margin_db=float(gm),stb_ugb_Hz=sfu,stb_phase_margin_deg=float(spm),stb_gain_margin_db=float(sgm),psrr_1k_dB=float(np.interp(1e3,p['freq'],-20*np.log10(abs(p['vout'])))),min_active_headroom_V=min(q['headroom_V'] for q in op.values() if abs(q['ids'])>=1e-9))
        rows.append(row)
        for key,limit,sense,kind,relax in [('iq_A',400e-6,'max','linear',True),('phase_margin_deg',45,'min','phase_margin',False),('gain_margin_db',6,'min','amplitude_db',True),('stb_phase_margin_deg',45,'min','phase_margin',False),('stb_gain_margin_db',6,'min','amplitude_db',True),('psrr_1k_dB',40,'min','amplitude_db',True),('min_active_headroom_V',.03,'min','linear',False)]:gates[f'{ma}mA_{key}']=strict(gate(row[key],limit,sense,'SI/deg/dB',kind=kind,relax=relax))
        gates[f'{ma}mA_output_error_V']=gate(abs(row['vout_V']-.4),.05,'max','V')
    guards=all(q['iq_A']>=0 and 0<q['vout_V']<1.8 for q in rows)
    return result(CASE,17,dict(load_points=rows),gates,groups,guards,operating_point=ops)

def run(dec=40,reltol=1e-6):
    simulate_groups(17,CASE,{f'{mode}{ma}':bench(ma*1e-3,mode,dec,reltol) for ma in [1,5] for mode in ['loop','psrr']});return extract()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k,d in [('cgate',100),('cout',20),('k',2),('tail',80),('pass-m',100)]:p.add_argument('--'+k,type=float,default=d)
    a=p.parse_args();design(**vars(a));update_case(17,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));run()
