"""Native-passive regulated doubler, exact HD logic and original three-load nominal."""
from batch29 import *
from hd_cells import extract_hd
import argparse
CASE=ROOT/'cases/18-regulated-pump';TASK=SOURCE/'sky130-regulated-charge-pump-10mhz-pvt'
MOS=['MREF','MTAIL','MREFIN','MFBIN','MPD','MPM','MOFFN','MOFFP','MOFFCTRL','MENREF','MENFB','MCTRL','MPRE0','MPRE1','MRECT0','MRECT1']

def design(cap=7.5,comp=80,control_m=4,pre_uA=50,rect_uA=250,divider=6,zero_segments=3):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V40C, all three enabled loads1/25/50uA and independent disabled DC. Other5enabled and4disabled PVT points excluded.',VDD_V=1.8,temperature_C=40,enabled_loads_A=[1e-6,25e-6,50e-6],output_target_V=2.34,output_error_V=.117,ripple_max_V=.005,enabled_current_max_A=200e-6,disabled_current_max_A=100e-9,clock=dict(Hz=1e7,rise_fall_s=1e-9,low_plateau_s=49e-9,period_s=100e-9,initial_V=1.8),source_ohm=50,bias_A=1e-6,output_cap_F=1e-9,stop_s=200e-6,window_s=[190e-6,200e-6],disabled='Independent DC withCLK=0,EN=0,no load; separate supplysense. Bias current upstream ofAVDDsense, excluded bysourcecontract.',allowed_DUT='NativeMOS/MIM/polyresistors and exactHDcells; no idealuserpassives/sources.',terminal_screen_V={'n18':1.98,'p18':1.98,'nnt33':3.63},terminal_screen_scope='Engineering screening on saved samples, not foundry lifetime or exhaustiveintermediate-timebound; middletime outputdecimated only, integration windowfull.'))
        env=json.loads((CASE/'environment.json').read_text());env['temperature_C']=40;write_json(CASE/'environment.json',env)
    roles=dict(bias=lut_size('n18',1,14,1e-6,.45),input=lut_size('n18',.36,22,.5e-6,.45),pload=lut_size('p18',1,14,.5e-6,.9),enable_n=lut_size('n18',.18,10,10e-6,.9),enable_p=lut_size('p18',.18,10,10e-6,.9),control=lut_size('p18',.36,12,50e-6,.45),precharge=lut_size('nnt33',1,6,pre_uA*1e-6,1.8),rectifier=lut_size('nnt33',1,6,rect_uA*1e-6,1.8))
    w={k:q['rounded_W_um'] for k,q in roles.items()};extract_hd(['NAND2HDV1','INHDV1','INHDV16'],CASE)
    text=f'''simulator lang=spectre
subckt charge_pump_regulated (AVDD AVSS CLK EN IBN1U VOUT)
XENB (EN ENB AVDD AVSS AVDD AVSS) INHDV1
XNAND (CLK EN gated AVDD AVSS AVDD AVSS) NAND2HDV1
XPH0 (gated ph0 AVDD AVSS AVDD AVSS) INHDV16
XPH1 (ph0 ph1 AVDD AVSS AVDD AVSS) INHDV16
XDR0 (ph0 bot0 vclk AVSS AVDD AVSS) INHDV16
XDR1 (ph1 bot1 vclk AVSS AVDD AVSS) INHDV16
MREF (IBN1U IBN1U AVSS AVSS) n18 w={w['bias']}u l=1u
MTAIL (tail IBN1U AVSS AVSS) n18 w={w['bias']}u l=1u
MREFIN (ctrl vnr tail AVSS) n18 w={w['input']}u l=.36u
MFBIN (pd vfb tail AVSS) n18 w={w['input']}u l=.36u
MPD (pd pd AVDD AVDD) p18 w={w['pload']}u l=1u
MPM (ctrl pd AVDD AVDD) p18 w={w['pload']}u l=1u
MOFFN (IBN1U ENB AVSS AVSS) n18 w={w['enable_n']}u l=.18u
MOFFP (pd EN AVDD AVDD) p18 w={w['enable_p']}u l=.18u
MOFFCTRL (ctrl EN AVDD AVDD) p18 w={w['enable_p']}u l=.18u
MENREF (enr EN AVSS AVSS) n18 w={w['enable_n']}u l=.18u
MENFB (enf EN AVSS AVSS) n18 w={w['enable_n']}u l=.18u
MCTRL (vclk ctrl AVDD AVDD) p18 w={w['control']}u l=.36u m={control_m:g}
MPRE0 (AVDD p1 p0 AVSS) nnt33 w={w['precharge']}u l=1u
MPRE1 (AVDD p0 p1 AVSS) nnt33 w={w['precharge']}u l=1u
MRECT0 (VOUT p0 p0 AVSS) nnt33 w={w['rectifier']}u l=1u
MRECT1 (VOUT p1 p1 AVSS) nnt33 w={w['rectifier']}u l=1u
CF0 (p0 bot0) mim w=100u l={cap/.0971:.12g}u
CF1 (p1 bot1) mim w=100u l={cap/.0971:.12g}u
CC (cz AVDD) mim w=100u l=100u m={comp/9.71:.12g}
CN (vnr AVSS) mim w=20u l={1/.01942:.12g}u
CP (vfb AVSS) mim w=20u l={1/.01942:.12g}u
'''
    for i in range(zero_segments):
        a='ctrl' if i==0 else f'rz{i}';b='cz' if i==zero_segments-1 else f'rz{i+1}'
        text+=f'RZ{i} ({a} {b} AVSS) rpposab_3t w=1u l=240u\n'
    # Matched unitpoly geometry: 1:1 reference,1.6:1 output divider. Allhighvoltageoutside amp.
    for name,start,end,count,unit in [('RN0','AVDD','vnr',divider,150),('RN1','vnr','enr',divider,150),('RP0','VOUT','vfb',divider,240),('RP1','vfb','enf',divider,150)]:
        for i in range(count):
            a=start if i==0 else name+str(i);b=end if i==count-1 else name+str(i+1)
            text+=f'{name}_{i} ({a} {b} AVSS) rpposab_3t w=1u l={unit}u\n'
    text+='ends charge_pump_regulated\n'
    save_design(CASE,text,roles,dict(cap=cap,comp=comp,control_m=control_m,pre_uA=pre_uA,rect_uA=rect_uA,divider=divider,zero_segments=zero_segments),'Two nnt33 flyingcapacitor phases use exactHD drivers supplied byanalog PMOS amplitude regulator. NMOS5TOTA compareshalfVDD withVOUT/2.6; nativepolydividers turnoff withEN. A nativepoly seriesR with80pF compensation introduces a stabilizing zero. Powergate andbiasclamps ensure staticdisabledcurrent. Input/rectifier initial sizes frommeasuredgmIDtables; time-dependentbodyeffectverifiedbyactualtransients.')

def bench(load,step=1e-9,reltol=1e-5):
    enabled=load is not None
    b='simulator lang=spectre\nglobal 0\n'+''.join(f'include "{MODEL}" section={s}\n' for s in ['tt','mim_tt','res_tt'])+f'''include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
VDD (src 0) vsource dc=1.8
VSENSE (src AVDD) vsource dc=0
IBIAS (src IBN1U) isource dc=1u
VEN (ensrc 0) vsource dc={1.8 if enabled else 0}
REN (ensrc EN) resistor r=50
VCLK (clksrc 0) vsource '''+('type=pulse val0=1.8 val1=0 delay=0 rise=1n fall=1n width=49n period=100n' if enabled else 'dc=0')+f'''
RCLK (clksrc CLK) resistor r=50
CLOAD (VOUT 0) capacitor c=1n
X (AVDD 0 CLK EN IBN1U VOUT) charge_pump_regulated
simulatorOptions options temp=40 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14
saveOptions options save=selected
save AVDD VOUT CLK EN IBN1U VSENSE:p VDD:p clksrc ensrc X.ENB X.gated X.ph0 X.ph1 X.bot0 X.bot1 X.p0 X.p1 X.vclk X.ctrl X.tail X.pd X.vnr X.vfb X.enr X.enf
'''
    if enabled:b+=f'ILOAD (VOUT 0) isource dc={load:g}\ntran tran stop=200u maxstep={step:g} method=gear2only errpreset=conservative skipstart=2u skipstop=180u skipcount=100\n'
    else:b+='dcOp dc\n'
    return b

def sample_window(d):
    t=d['time'];a=190e-6;b=200e-6;sel=(t>a)&(t<b);tt=np.r_[a,t[sel],b]
    return tt,{k:np.r_[np.interp(a,t,v),v[sel],np.interp(b,t,v)] for k,v in d.items() if k!='time'}

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());rows=[];g={};terminal=[];allowed=True
    for ua in [1,25,50]:
        label=f'load{ua}';rd=ROOT/groups[label];d=data(rd,'tran.tran');t,w=sample_window(d);avg=lambda x:float(np.trapz(x,t)/(t[-1]-t[0]))
        row=dict(load_uA=ua,vout_avg_V=avg(w['VOUT']),vout_min_V=float(min(w['VOUT'])),vout_max_V=float(max(w['VOUT'])),enabled_current_A=abs(avg(w['VSENSE:p'])),control_avg_V=avg(w['X.ctrl']),driver_supply_avg_V=avg(w['X.vclk']))
        row.update(error_V=abs(row['vout_avg_V']-2.34),ripple_V=row['vout_max_V']-row['vout_min_V']);rows.append(row)
        for key,lim in [('error_V',.117),('ripple_V',.005),('enabled_current_A',200e-6)]:g[f'{ua}uA_{key}']=gate(row[key],lim,'max','V/A')
        get=lambda n:np.zeros(len(d['time'])) if n=='AVSS' else d.get(n,d.get('X.'+n))
        for name,nodes,model in re.findall(r'^(M\w+)\s+\(([^)]+)\)\s+(\w+)',(CASE/'circuit.scs').read_text(),re.M):
            v=[get(n) for n in nodes.split()];peaks={k:float(max(abs(v[a]-v[b]))) for k,a,b in [('VGS',1,2),('VGD',1,0),('VDS',0,2),('VGB',1,3),('VDB',0,3),('VSB',2,3)]};lim=3.63 if model=='nnt33' else 1.98;allowed &= max(peaks.values())<=lim;terminal.append(dict(load_uA=ua,device=name,model=model,peaks_V=peaks,limit_V=lim))
    o=dc(ROOT/groups['disabled']);off=abs(o['VSENSE:p']);g['disabled_current_A']=gate(off,100e-9,'max','A')
    warnings={k:json.loads((ROOT/v/'run.json').read_text())['warnings'] for k,v in groups.items()};bad={k:[v for v in w if 'SPECTRE-16780' not in v] for k,w in warnings.items()};allowed &= not any(bad.values())
    return result(CASE,18,dict(enabled=rows,disabled_current_A=off),g,groups,allowed,terminal_voltages=terminal,disallowed_model_warnings=bad)

def run(step=1e-9,reltol=1e-5):
    simulate_groups(18,CASE,{**{f'load{ua}':bench(ua*1e-6,step,reltol) for ua in [1,25,50]},'disabled':bench(None,step,reltol)},temperature_C=40);return extract()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k,d in [('cap',7.5),('comp',80),('control-m',4),('pre-uA',50),('rect-uA',250)]:p.add_argument('--'+k,type=float,default=d)
    p.add_argument('--divider',type=int,default=6);p.add_argument('--zero-segments',type=int,default=3);a=p.parse_args();design(**vars(a));update_case(18,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));run()
