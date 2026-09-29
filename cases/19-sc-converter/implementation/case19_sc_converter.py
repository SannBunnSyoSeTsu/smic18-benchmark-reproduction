"""Native switched-capacitor converter and exact HD non-overlap logic."""
from batch29 import *
from hd_cells import extract_hd
import argparse
CASE=ROOT/'cases/19-sc-converter';TASK=SOURCE/'sky130-switched-capacitor-2to1-converter-pvt'

def design(cf=100,co=280,nm=60,pm=24,lowm=64):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C, matched680/6800ohm loads with all original nominal checks. Other44active and2passive corners excluded.',supply_V=1.8,temperature_C=27,loads_ohm=[680,6800],clock=dict(Hz=20e6,delay_s=5e-9,rise_fall_s=.4e-9,width_s=24.6e-9,period_s=50e-9,source_ohm=50),stop_s=.7e-6,window_s=[.3e-6,.7e-6],startup_target_V=.378*1.8,startup_max_s=200e-9,startup_measurement='Last rising crossing of0.378VDD; minimum200ns-to-stop separately fixedabove0.378VDD',cold_start='skipdc=yes: equivalent originaluic, zero storedcapacitor state',heavy_ratio=[.42,.51],light_ratio=[.45,.51],heavy_efficiency_min=.7,light_efficiency_min=.3,efficiency_max_nonrelaxable=1,heavy_ripple_max_V=.08,light_input_power_max_W=500e-6,output_resistance_max_ohm=100,power='mean(-VDD*I(VDD)) plus mean(max(-VCLK*I(VCLK),0)); returnedclockenergy notcredited',allowed_DUT='nativeMOS/MIM and exactHD logic, no idealDUT passives',terminal_limit_V=1.98))
    roles=dict(floating_switch=lut_size('n18',.18,8,50e-6,.45),ground_switch=lut_size('n18',.18,10,50e-6,.45),high_switch=lut_size('p18',.18,8,50e-6,.45));w={k:q['rounded_W_um'] for k,q in roles.items()}
    extract_hd(['INHDV1','INHDV2','INHDV16','NAND2HDV1'],CASE)
    text='simulator lang=spectre\nsubckt sc_2to1_converter (vss vdd clk vout)\n'
    cells=[('RX1','clk ckb','INHDV1'),('RX2','ckb ck','INHDV1'),('NA','ck fb2 n1','NAND2HDV1'),('A1','n1 a1','INHDV1'),('A2','a1 a2','INHDV1'),('A3','a2 s1','INHDV2'),('FB1','s1 fb1','INHDV1'),('NB','ckb fb1 n2','NAND2HDV1'),('B1','n2 b1','INHDV1'),('B2','b1 b2','INHDV1'),('B3','b2 s2','INHDV2'),('FB2','s2 fb2','INHDV1')]
    for branch,series,parallel in [('A','s1','s2'),('B','s2','s1')]:
        cells += [(f'DP{branch}',f'{series} pg{branch}','INHDV16'),(f'DN3{branch}1',f'{series} n3p{branch}','INHDV2'),(f'DN3{branch}2',f'n3p{branch} ng{branch}','INHDV16'),(f'DNP{branch}1',f'{parallel} npp{branch}','INHDV2'),(f'DNP{branch}2',f'npp{branch} npg{branch}','INHDV16')]
    for name,nodes,model in cells:text+=f'X{name} ({nodes} vdd vss vdd vss) {model}\n'
    for b in ['A','B']:
        text+=f'''MP1{b} (ct{b} pg{b} vdd vdd) p18 w={w['high_switch']}u l=.18u m={pm:g}
MN3{b} (cb{b} ng{b} vout vss) n18 w={w['floating_switch']}u l=.18u m={nm:g}
MN2{b} (ct{b} npg{b} vout vss) n18 w={w['floating_switch']}u l=.18u m={nm:g}
MN4{b} (cb{b} npg{b} vss vss) n18 w={w['ground_switch']}u l=.18u m={lowm:g}
CF{b} (ct{b} cb{b}) mim w=100u l=100u m={cf/9.71:.12g}
CBP{b} (cb{b} vss) mim w=20u l={2/.01942:.12g}u
'''
    text+=f'CO (vout vss) mim w=100u l=100u m={co/9.71:.12g}\nends sc_2to1_converter\n'
    save_design(CASE,text,roles,dict(cf=cf,co=co,nm=nm,pm=pm,lowm=lowm),'Two interleaved4-switch2:1 branches. Originalnonoverlap NANDfeedback and driverbranches replaced with exactHD cells. Analogswitch initial W fromgmID8/10 LUT; actualswitch operatesintrioderegion and reverse current, notclaimedconstantgmID. NativeMIMcapacitorsincludephysicalmodel.')

def bench(load,step=.5e-9,reltol=1e-6):
    return 'simulator lang=spectre\nglobal 0\n'+''.join(f'include "{MODEL}" section={s}\n' for s in ['tt','mim_tt'])+f'''include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
VCLK (clk_src 0) vsource type=pulse val0=0 val1=1.8 delay=5n rise=.4n fall=.4n width=24.6n period=50n
RCLK (clk_src clk) resistor r=50
RL (vout 0) resistor r={load:g}
X (0 vdd clk vout) sc_2to1_converter
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14
saveOptions options save=selected
save vdd vout clk clk_src VDD:p VCLK:p X.ckb X.ck X.fb1 X.fb2 X.n1 X.n2 X.s1 X.s2 X.pgA X.pgB X.ngA X.ngB X.npgA X.npgB X.ctA X.ctB X.cbA X.cbB
tran tran stop=.7u maxstep={step:g} skipdc=yes method=gear2only errpreset=conservative
'''

def window(d,a=.3e-6,b=.7e-6):
    t=d['time'];s=(t>a)&(t<b);tt=np.r_[a,t[s],b]
    return tt,{k:np.r_[np.interp(a,t,v),v[s],np.interp(b,t,v)] for k,v in d.items() if k!='time'}

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());rows=[];g={};guards=True;term=[]
    for label,load,lo,eff in [('heavy',680,.42,.7),('light',6800,.45,.3)]:
        d=data(ROOT/groups[label],'tran.tran');t,w=window(d);avg=lambda v:float(np.trapz(v,t)/(t[-1]-t[0]));v=w['vout'];row=dict(load_ohm=load,vout_mean_V=avg(v),vout_min_V=float(min(v)),vout_max_V=float(max(v)),supply_power_W=avg(-w['vdd']*w['VDD:p']),clock_power_W=avg(np.maximum(-w['clk_src']*w['VCLK:p'],0)),load_power_W=avg(v*v/load))
        row.update(conversion_ratio=row['vout_mean_V']/1.8,ripple_V=row['vout_max_V']-row['vout_min_V'],input_power_W=row['supply_power_W']+row['clock_power_W'],load_current_A=row['vout_mean_V']/load);row['efficiency']=row['load_power_W']/row['input_power_W'];rows.append(row)
        for k,limit,sense,relax in [('conversion_ratio',lo,'min',True),('efficiency',eff,'min',True),('conversion_ratio',.51,'max',True),('efficiency',1,'max',False)]:g[label+'_'+k+'_'+sense]=gate(row[k],limit,sense,'ratio',relax=relax)
        guards &= row['supply_power_W']>=0 and row['clock_power_W']>=0 and row['input_power_W']>0 and row['load_power_W']>=0
        if label=='heavy':
            target=.378*1.8;y=d['vout'];tt=d['time'];cross=np.flatnonzero((y[:-1]<target)&(y[1:]>=target));assert len(cross),'No startup crossing';i=cross[-1];startup=float(tt[i]+(tt[i+1]-tt[i])*(target-y[i])/(y[i+1]-y[i]));ht,hw=window(d,200e-9,.7e-6);hold=float(min(hw['vout']));row.update(startup_s=startup,post_startup_min_V=hold)
            g['heavy_ripple_V']=gate(row['ripple_V'],.08,'max','V');g['startup_s']=gate(startup,200e-9,'max','s');g['startup_hold_V']=gate(hold,target,'min','V',relax=False)
        else:g['light_input_power_W']=gate(row['input_power_W'],500e-6,'max','W')
        get=lambda n:np.zeros(len(d['time'])) if n=='vss' else d.get(n,d.get('X.'+n))
        for name,nodes in re.findall(r'^(M\w+)\s+\(([^)]+)\)',(CASE/'circuit.scs').read_text(),re.M):
            z=[get(n) for n in nodes.split()];peaks={k:float(max(abs(z[a]-z[b]))) for k,a,b in [('VGS',1,2),('VGD',1,0),('VDS',0,2),('VGB',1,3),('VDB',0,3),('VSB',2,3)]};term.append(dict(load=label,device=name,peaks_V=peaks));guards &= max(peaks.values())<=1.98
    h,l=rows;rout=(l['vout_mean_V']-h['vout_mean_V'])/(h['load_current_A']-l['load_current_A']);g['output_resistance_ohm']=gate(rout,100,'max','ohm');guards &= rout>=0
    bad={k:[w for w in json.loads((ROOT/v/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in w] for k,v in groups.items()};guards &= not any(bad.values())
    return result(CASE,19,dict(loads=rows,output_resistance_ohm=rout),g,groups,guards,terminal_voltages=term,disallowed_warnings=bad)

def run(step=.5e-9,reltol=1e-6):
    simulate_groups(19,CASE,{label:bench(load,step,reltol) for label,load in [('heavy',680),('light',6800)]});return extract()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k,d in [('cf',100),('co',280),('nm',60),('pm',24),('lowm',64)]:p.add_argument('--'+k,type=float,default=d)
    a=p.parse_args();design(**vars(a));update_case(19,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));run()
