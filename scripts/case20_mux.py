"""Three-stage transmission-gate mux with exact HD select inverters."""
from common import *
from hd_cells import extract_hd
from case16_miller import prefix
import argparse
CASE=ROOT/'cases/20-mux'
CMS=[0,.9,1.8]

def design(current=20,length=.36,gmid=10,cell='INHDV0'):
    CASE.mkdir(parents=True,exist_ok=True);hd=extract_hd([cell],CASE)
    roles={'n_switch':lut_size('n18',length,gmid,current*1e-6,.9),'p_switch':lut_size('p18',length,gmid,current*1e-6,.9)}
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    text=f'''// Three binary TG stages; standard-cell select complements.
simulator lang=spectre
subckt tg (VDD VSS EN ENB I O)
MN (O EN I VSS) n18 w={w['n_switch']:g}u l={length:g}u
MP (O ENB I VDD) p18 w={w['p_switch']:g}u l={length:g}u
ends tg
subckt input_mux_8to1 (AVDD AVSS S2 S1 S0 VIN7 VIN6 VIN5 VIN4 VIN3 VIN2 VIN1 VIN0 VO)
'''
    for bit in range(3):text+=f'XINV{bit} (S{bit} SB{bit} AVDD AVSS AVDD AVSS) {cell}\n'
    layer=[f'VIN{i}' for i in range(8)];idx=0
    for bit in range(3):
        nxt=[]
        for j in range(len(layer)//2):
            output='VO' if bit==2 else f'n{bit}_{j}';nxt.append(output)
            for k in range(2):
                en,enb=(f'SB{bit}',f'S{bit}') if k==0 else (f'S{bit}',f'SB{bit}')
                text+=f'XSW{idx} (AVDD AVSS {en} {enb} {layer[2*j+k]} {output}) tg\n';idx+=1
        layer=nxt
    text+='ends input_mux_8to1\n';c=CASE/'circuit.scs';c.write_text(text)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,tg_count=14,series_selected_tg_count=3,standard_cell=cell,standard_cell_count=3,initial_switch_current_A=current*1e-6,initial_gmid=gmid,actual_mode='Transmission gates operate near VDS=0 in triode; saturated gm/ID selects starting geometry only. Actual gds and full external transfers determine Ron/bandwidth/isolation.',lut_temperature_C=27,verification_temperature_C=40))
    write_json(CASE/'contract.json',dict(source_task='sky130-analog-input-mux-8to1-pvt',corner='tt',VDD_V=1.8,temperature_C=40,nominal_temperature_reason='Original task nominal row is TT/1.8V/40C',common_modes_V=CMS,selects=list(range(8)),independently_excited_sources=list(range(8)),selected_states=24,total_transfers=192,source_resistance_Ohm=50,source_resistance_ports='AVDD, all3 selects, all8 analog inputs; AVSS ideal ground per original bench',load_F=1e-12,gain_frequency_Hz=.001,selected_gain_max_abs_dB=.001,unselected_gain_max_dB=-80,crosstalk_frequencies_Hz=[.001,1e6],selected_bandwidth_min_Hz=5e6,bandwidth_ratio=10**(-3/20),supply_current_max_A=5e-6,ac_stop_Hz=1e9,pin_aliases='S2/S1/S0 and VIN7..VIN0 are Spectre-safe aliases of original escaped bus pins, exact original order preserved.',legal_DUT_leaves='PDK MOS only; HD cells expanded to original MOS; no ideal passive or source in DUT',nominal_scope_excludes=['remaining4 representative PVT rows','distortion','noise','switchingtransients','mismatch','PEX']))
    return c,hd

def bench(c):
    b=prefix(c).replace('temp=27','temp=40')+f'include "{CASE / "hd_cells.scs"}"\n'
    for cm,voltage in enumerate(CMS):
        for select in range(8):
            for excite in range(8):
                tag=f'{cm}_{select}_{excite}'
                b+=f'''VDD{tag} (vdsrc{tag} 0) vsource dc=1.8
RVD{tag} (vdsrc{tag} vdd{tag}) resistor r=50
'''
                for bit in range(3):
                    b+=f'VS{bit}_{tag} (ss{bit}_{tag} 0) vsource dc={1.8*((select>>bit)&1):g}\nRS{bit}_{tag} (ss{bit}_{tag} s{bit}_{tag}) resistor r=50\n'
                for i in range(8):
                    b+=f'VI{i}_{tag} (vs{i}_{tag} 0) vsource dc={voltage:g} mag={int(i==excite)}\nRI{i}_{tag} (vs{i}_{tag} vi{i}_{tag}) resistor r=50\n'
                pins=[f'vdd{tag}','0']+[f's{i}_{tag}' for i in [2,1,0]]+[f'vi{i}_{tag}' for i in range(7,-1,-1)]+[f'vo{tag}']
                b+=f'X{tag} ('+' '.join(pins)+') input_mux_8to1\n'+f'CL{tag} (vo{tag} 0) capacitor c=1p\nsave vo{tag} VDD{tag}:p\n'
                if select==0 and excite==0:
                    for sw in [0,8,12]:
                        for m in ['MN','MP']:b+=f'save X{tag}.XSW{sw}.{m}:gds\n'
    return b+'dcOp dc\nac ac start=1m stop=1G dec=60\n'

def extract(run):
    a=data(run,'ac.ac');o=dc(run);f=a['freq'];states=[];transfers=[];ron=[]
    for cm,voltage in enumerate(CMS):
        for select in range(8):
            rows=[];currents=[]
            for excite in range(8):
                tag=f'{cm}_{select}_{excite}';h=abs(a['vo'+tag]);db=20*np.log10(np.maximum(h,1e-300));currents.append(abs(o[f'VDD{tag}:p']))
                q=dict(common_mode_V=voltage,select=select,excited_input=excite,gain_dc_dB=float(at(f,db,.001)),gain_1mhz_dB=float(at(f,db,1e6)))
                if excite==select:
                    target=h[0]*10**(-3/20);ix=np.flatnonzero((h[:-1]>=target)&(h[1:]<target))
                    if not len(ix):raise RuntimeError('Missing first -3dB crossing in original sweep')
                    i=ix[0];alpha=(np.log(h[i])-np.log(target))/(np.log(h[i])-np.log(h[i+1]));q['bandwidth_Hz']=float(np.exp(np.log(f[i])+alpha*np.log(f[i+1]/f[i])))
                rows.append(q);transfers.append(q)
            on=rows[select];off=[q for q in rows if q['excited_input']!=select]
            states.append(dict(common_mode_V=voltage,select=select,selected_gain_dc_dB=on['gain_dc_dB'],selected_gain_1mhz_dB=on['gain_1mhz_dB'],worst_off_dc=max(off,key=lambda q:q['gain_dc_dB']),worst_off_1mhz=max(off,key=lambda q:q['gain_1mhz_dB']),bandwidth_Hz=on['bandwidth_Hz'],supply_current_A=max(currents),dc_copies_current_spread_A=max(currents)-min(currents)))
        gs=[]
        for sw in [0,8,12]:gs.append(sum(o[f'X{cm}_0_0.XSW{sw}.{m}:gds'] for m in ['MN','MP']))
        ron.append(dict(common_mode_V=voltage,stage_Ron_Ohm=[1/g for g in gs],path_Ron_Ohm=sum(1/g for g in gs)))
    values=dict(selected_gain_error_dB=max(abs(q['selected_gain_dc_dB']) for q in states),worst_off_dc_dB=max(q['worst_off_dc']['gain_dc_dB'] for q in states),worst_off_1mhz_dB=max(q['worst_off_1mhz']['gain_1mhz_dB'] for q in states),min_bandwidth_Hz=min(q['bandwidth_Hz'] for q in states),max_supply_current_A=max(q['supply_current_A'] for q in states))
    gates={}
    for k,limit,sense,unit,kind in [('selected_gain_error_dB',.001,'max','dB error','linear'),('worst_off_dc_dB',-80,'max','dB','amplitude_db'),('worst_off_1mhz_dB',-80,'max','dB','amplitude_db'),('min_bandwidth_Hz',5e6,'min','Hz','linear'),('max_supply_current_A',5e-6,'max','A','linear')]:gates[k]=gate(values[k],limit,sense,unit,kind)
    assert len(states)==24 and len(transfers)==192
    tiers={tier:all(g['passes'][tier] for g in gates.values()) for tier in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    r=dict(case_slot=20,generated_at=now(),run_dir=str(run.relative_to(ROOT)),status='complete_'+tier if tier else 'partial',values=values,gates=gates,states=states,transfers=transfers,on_resistance=ron,all_nominal_checks_complete=True,pass_tiers=tiers,model_dimensions_valid=True,scope='TT/1.8V/40C, all3 common modes, all8 selects, all8 independent transfers each. Other4PVT rows not run.')
    write_json(run/'measurements.json',r);write_json(CASE/'latest_results.json',r);update_case(20,status=r['status'],nominal_complete=bool(tier),latest_run=r['run_dir'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--current',type=float,default=20);p.add_argument('--length',type=float,default=.36);p.add_argument('--gmid',type=float,default=10);p.add_argument('--cell',default='INHDV0');p.add_argument('--extract');a=p.parse_args()
    if a.extract:run=ROOT/a.extract
    else:
        c,hd=design(a.current,a.length,a.gmid,a.cell);b=bench(c);(CASE/'testbench.scs').write_text(b);update_case(20,status='running',nominal_complete=False)
        run=run_spectre(20,'matrix',b,[c,hd,CASE/'sizing.json',CASE/'contract.json',CASE/'hd_cells_manifest.json'],temperature_C=40)
    r=extract(run);print(json.dumps({k:r[k] for k in ['status','values','on_resistance']},indent=2))
if __name__=='__main__':main()
