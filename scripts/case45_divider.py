"""HD-cell 1 GHz divide by two, including asynchronous reset contract."""
from common import *
from hd_cells import extract_hd
import argparse

CASE=ROOT/'cases/45-divider'

def design(ff=1,nor=16,rinv=2):
    CASE.mkdir(parents=True,exist_ok=True)
    h=extract_hd([f'DRNQNHDV{ff}',f'NOR2HDV{nor}',f'INHDV{rinv}'],CASE)
    p=CASE/'circuit.scs'
    p.write_text(f'''// Unmodified HD library cells. Internal FF is reset; output NOR adds a fast assertion path.
simulator lang=spectre
subckt divide_by_2 (clk reset vdd vss clkout)
XR (reset rdn vdd vss vdd vss) INHDV{rinv}
XFF (clk qn qn rdn vdd vss vdd vss) DRNQNHDV{ff}
XOUT (qn reset clkout vdd vss vdd vss) NOR2HDV{nor}
ends divide_by_2
''')
    write_json(CASE/'contract.json',dict(source_task='sky130-transistor-divide-by-2',corner='tt',vdd_V=1.8,temperature_C=27,frequency_hz=1e9,load_F=20e-15,source_resistance_ohm=20,clock_rise_fall_s=10e-12,reset_edge_s=5e-12,relaxation={'reset_delay_s':[100e-12,110e-12,115e-12],'clock_delay_s':[400e-12,440e-12,460e-12],'duty_error_fraction':[.01,.011,.0115]},functional_invariants=['Divide ratio exactly 2 within original +/-1%','High >=1.44V, low <=0.36V','Internal reset state cleared','No output rise at asynchronous release before next clock edge']))
    return p,h

def bench(circuit,hd,reset=False):
    wave='0 1.8 .945n 1.8 .95n 0 1.745n 0 1.75n 1.8 2.045n 1.8 2.05n 0 3n 0' if reset else '0 1.8 .945n 1.8 .95n 0 9n 0'
    return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{hd}"
include "{circuit}"
simulatorOptions options temp=27 reltol=1e-5 vabstol=1e-8 iabstol=1e-14 method=gear2only
VDD (vdd 0) vsource dc=1.8
VCLK (clk_src 0) vsource type=pulse val0=0 val1=1.8 delay=.2n rise=10p fall=10p width=.49n period=1n
VRESET (reset_src 0) vsource type=pwl wave=[{wave}]
RCLK (clk_src clk) resistor r=20
RRESET (reset_src reset) resistor r=20
CL (clkout 0) capacitor c=20f
XDUT (clk reset vdd 0 clkout) divide_by_2
saveOptions options save=selected
save clk reset clkout XDUT.qn XDUT.rdn VDD:p
tran tran stop={'3n' if reset else '9n'} maxstep=1p errpreset=conservative
'''

def crossings(t,v,rise=True,start=0,level=.9):
    mask=(v[:-1]<level)&(v[1:]>=level) if rise else (v[:-1]>level)&(v[1:]<=level)
    idx=np.flatnonzero(mask);x=t[idx]+(level-v[idx])/(v[idx+1]-v[idx])*(t[idx+1]-t[idx])
    return x[x>=start]

def window(t,v,lo,hi):
    return np.r_[np.interp(lo,t,v),v[(t>lo)&(t<hi)],np.interp(hi,t,v)]

def extract(r_div,r_rst):
    d=data(r_div,'tran.tran');r=data(r_rst,'tran.tran');t=d['time'];tr=r['time'];v=d['clkout'];vr=r['clkout']
    cr=crossings(t,d['clk'],True,.95e-9);up=crossings(t,v,True,.95e-9);dn=crossings(t,v,False,.95e-9)
    reset_rise=crossings(tr,r['reset'],True,1.7e-9);reset_fall=crossings(tr,vr,False,1.7e-9)
    if len(up)<4 or len(dn)<3 or len(cr)<7 or not len(reset_rise) or not len(reset_fall):
        raise RuntimeError('Missing required clock/output/reset transitions; waveform retained')
    periods=np.diff(up[:4]);high=dn[:3]-up[:3];low=up[1:4]-dn[:3];delays=up[:4]-cr[:7:2]
    values=dict(input_frequency_hz=float(3/(cr[3]-cr[0])),output_frequency_hz=float(3/(up[3]-up[0])),output_periods_s=list(periods),high_duties=list(high/periods),low_duties=list(low/periods),clock_delays_s=list(delays),reset_delay_s=float(reset_fall[0]-reset_rise[0]),pre_assert_V=float(np.interp(1.65e-9,tr,vr)),asserted_max_V=float(np.max(window(tr,vr,1.85e-9,2.04e-9))),release_hold_max_V=float(np.max(window(tr,vr,2.05e-9,2.2e-9))),next_edge_V=float(np.interp(2.7e-9,tr,vr)),low_samples_V=[float(np.interp(x,t,v)) for x in [2.9e-9,4.9e-9]],high_samples_V=[float(np.interp(x,t,v)) for x in [3.9e-9,5.9e-9]])
    function=bool(.99e9<=values['input_frequency_hz']<=1.01e9 and np.all((periods>=1/.505e9)&(periods<=1/.495e9)) and min(values['low_samples_V'])>=-.05 and max(values['low_samples_V'])<=.36 and min(values['high_samples_V'])>=1.44 and values['pre_assert_V']>=1.44 and values['asserted_max_V']<=.36 and values['release_hold_max_V']<=.36 and values['next_edge_V']>=1.44 and min(delays)>=0 and values['reset_delay_s']>=0)
    gates=dict(reset_delay_s=gate(values['reset_delay_s'],100e-12,'max','s'),clock_delay_s=gate(float(max(delays)),400e-12,'max','s'),duty_error=gate(float(max(np.max(abs(high/periods-.5)),np.max(abs(low/periods-.5)))),.01,'max','fraction'))
    passes={tier:bool(function and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']}
    tier=next((x for x in passes if passes[x]),None)
    report=dict(case_slot=45,generated_at=now(),run_dirs=[str(x.relative_to(ROOT)) for x in [r_div,r_rst]],values=values,gates=gates,functional_checks_pass=function,pass_tiers=passes,status='complete_'+tier if tier else 'partial',all_nominal_checks_complete=True,digital_implementation='Unmodified HD standard-cell transistor models; no custom digital gate sizing',scope='TT 1.8V 27C, original 1GHz stimulus and 20fF output load')
    write_json(CASE/'latest_results.json',report)
    for run in [r_div,r_rst]:write_json(run/'measurements.json',report)
    update_case(45,status=report['status'],nominal_complete=bool(tier),report=str((CASE/'latest_results.json').relative_to(ROOT)),latest_runs=report['run_dirs'])
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--ff',type=int,default=1);p.add_argument('--nor',type=int,default=16);p.add_argument('--rinv',type=int,default=2);p.add_argument('--extract',nargs=2)
    a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        c,h=design(a.ff,a.nor,a.rinv);update_case(45,status='running',nominal_complete=False)
        runs=[]
        for reset in [False,True]:
            text=bench(c,h,reset);(CASE/('tb_reset.scs' if reset else 'tb_divide.scs')).write_text(text)
            runs.append(run_spectre(45,'reset' if reset else 'divide',text,[c,h,CASE/'hd_cells_manifest.json',CASE/'contract.json']))
    print(json.dumps(extract(*runs),indent=2))

if __name__=='__main__':main()
