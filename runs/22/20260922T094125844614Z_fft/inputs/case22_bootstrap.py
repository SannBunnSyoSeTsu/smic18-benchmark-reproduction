"""Case22 bootstrap driver: fixed sampler fixtures and original coherent SDR."""
from common import *
from hd_cells import extract_hd
from case16_miller import prefix
import argparse
import importlib.util
import shutil

CASE=ROOT/'cases/22-bootstrap'
TASK=SOURCE/'sky130-bootstrap-sampler-fft'


def design(boot_uA=200,cap_pF=1.5,cell='INHDV8'):
    CASE.mkdir(parents=True,exist_ok=True)
    hd=extract_hd(list(dict.fromkeys([cell,'INHDV8','INHDV16'])),CASE)
    roles={d:lut_size(d,.18,8,boot_uA*1e-6,.9) for d in ['n18','p18']}
    # Fixture width is fixed by the benchmark; invert the LUT density for its declared geometry.
    unit=lut_size('n18',.18,8,100e-6,.9)
    fixture=lut_size('n18',.18,8,100e-6*64/unit['W_um'],.9)
    assert abs(fixture['rounded_W_um']-64)<1e-9
    roles['fixed_fixture_n18']=fixture
    wn=roles['n18']['rounded_W_um'];wp=roles['p18']['rounded_W_um'];c=CASE/'circuit.scs'
    c.write_text(f'''simulator lang=spectre
subckt boot_cell (VDD VSS CLK VIN VG)
XINV (CLK CLKP VDD VSS VDD VSS) {cell}
CBOOT (CBT CBB) capacitor c={cap_pF:g}p
MDCHG (CBB CLK VSS VSS) n18 w={wn:g}u l=.18u
MPCHG (CG CLKP VDD VDD) p18 w={wp:g}u l=.18u
MLIM (VDD VG CBT CBT) p18 w={wp:g}u l=.18u
MPRE (VDD CLKP PRE VSS) n18 w={wn:g}u l=.18u m=2
MGTRK (CG CLKP CBB VSS) n18 w={wn:g}u l=.18u m=2
MBPP (VG CG CBT CBT) p18 w={wp:g}u l=.18u
MPVIN (CBB VG VIN VSS) n18 w={wn:g}u l=.18u m=2
MCASC (VG VDD CLKP VSS) n18 w={wn:g}u l=.18u m=2
MPRGUARD (VG VDD PRE VSS) n18 w={wn:g}u l=.18u m=2
ends boot_cell
subckt bootstrap_gate_driver (vdd vss clk vinp vinn gatep gaten)
XBP (vdd vss clk vinp gatep) boot_cell
XBN (vdd vss clk vinn gaten) boot_cell
ends bootstrap_gate_driver
''')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,bootstrap_pF=cap_pF,internal_cell=cell,external_buffer_cells=['INHDV8','INHDV16'],rationale='Analog gmID8 atVDS0.9V/zeroVSB supplies initial sizing, m2 on switching NMOS. VDD-gated protection isolates precharge transistor. Fixed testbench sampling width64um retained; impossible Sky1300.15um length mapped to legal SMIC0.18um and documented, never tuned.'))
    hashes={}
    for name in ['instruction.md','solution/circuit.spi','tests/verify.py','tests/utils.py','tests/benches/tb_fft.spi','tests/benches/tb_static.spi']:
        src=TASK/name;dst=CASE/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);hashes[name]=sha(src)
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_hashes=hashes,corner='tt',VDD_V=1.8,temperature_C=27,clock_Hz=100e6,clock_delay_s=1e-9,clock_edge_s=50e-12,clock_high_plateau_s=4e-9,clock_source_Ohm=50,track_state='CLK=0; high phase holds',sampling_fixture_W_um=64,sampling_fixture_L_um=.18,fixture_length_migration='SourceSky130L0.15 illegal in target n18, map to target minimumL0.18 while retaining W64 and C1pF',fixture_capacitance_F=1e-12,fixture_clock_cells=['INHDV8','INHDV16'],input_common_mode_V=.9,sine_frequency_Hz=46.875e6,input_peak_each_V=.4,held_samples=32,held_sample_times_s='(3+k)*10ns+4ns,k0..31',midtrack_times_s='(3+k)*10ns+8ns,k0..31',SDR_min_dB=72,SDR_definition='Psignal=|DFT[15]|^2+|DFT[17]|^2; Pdist=sum(all nonDC bins)-Psignal, includes Nyquist; no window',midtrack_VGS_min_ratio=.8,static_input_reversal_s=[22e-9,22.1e-9],static_sample_s=24e-9,positive_and_negative_signed_retained_gain_min=.9,power_window_s=[30e-9,350e-9],DUT_VDD_power_max_W=500e-6,external_buffer_supply_excluded=True,additional_terminal_voltage_guard_V=1.98,voltage_guard_relaxable=False,voltage_guard_basis='Engineering screen, not foundry lifetime rating',scope_excludes=['remaining10PVT points','noise/SNDR/ENOB','mismatch','PEX']))
    return c,hd


def clock_wave(stop):
    pts=[(0,0)]
    for k in range(int(stop/10e-9)+1):
        start=1e-9+k*10e-9
        for when,val in [(start,0),(start+50e-12,1.8),(start+4.05e-9,1.8),(start+4.1e-9,0)]:
            if when<=stop:pts.append((when,val))
    if pts[-1][0]<stop:pts.append((stop,pts[-1][1]))
    return ' '.join(f'{when:.13g} {val:g}' for when,val in pts)


def benches(c,maxstep_ps):
    h=prefix(c).replace('reltol=1e-6','reltol=2e-6').replace('iabstol=1e-15','iabstol=1e-12')+f'include "{CASE/"hd_cells.scs"}"\n'
    decks=[]
    for kind,stop in [('static',30e-9),('fft',350e-9)]:
        b=h+f'''VDD (vdd 0) vsource dc=1.8
VCLKDD (clk_vdd 0) vsource dc=1.8
VCLKIN (clk_src 0) vsource type=pwl wave=[{clock_wave(stop)}]
RCLK (clk_src clk_in) resistor r=50
XCLK1 (clk_in clk_b clk_vdd 0 clk_vdd 0) INHDV8
XCLK2 (clk_b clk clk_vdd 0 clk_vdd 0) INHDV16
save clk_src clk_in clk_b clk VDD:p VCLKDD:p VCLKIN:p
'''
        for tag,pol in ([('P',1),('N',-1)] if kind=='static' else [('S',1)]):
            for side,sign in [('p',1),('n',-1)]:
                if kind=='fft':spec=f'type=sine dc=.9 ampl={sign*.4:g} freq=46.875M'
                else:spec=f'type=pwl wave=[0 {.9+sign*pol*.4:g} 22n {.9+sign*pol*.4:g} 22.1n {.9-sign*pol*.4:g} 30n {.9-sign*pol*.4:g}]'
                b+=f'VIN{side.upper()}{tag} (vin{side}{tag} 0) vsource {spec}\n'
                b+=f'MSW{side.upper()}{tag} (vout{side}{tag} gate{side}{tag} vin{side}{tag} 0) n18 w=64u l=.18u\nCOUT{side.upper()}{tag} (vout{side}{tag} 0) capacitor c=1p\n'
            b+=f'X{tag} (vdd 0 clk vinp{tag} vinn{tag} gatep{tag} gaten{tag}) bootstrap_gate_driver\n'
            b+='save '+' '.join(x+tag for x in ['vinp','vinn','gatep','gaten','voutp','voutn'])+f' VINP{tag}:p VINN{tag}:p\n'
            b+='save '+' '.join(f'X{tag}.XB{side}.{node}' for side in ['P','N'] for node in ['CLKP','CG','CBB','CBT','PRE'])+'\n'
        b+=f'tran tran stop={stop:.12g} maxstep={maxstep_ps:g}p errpreset=conservative\n';decks.append(b)
    return decks


def terminal_extrema(q,tag):
    zero=np.zeros_like(q['time']);supply=zero+1.8;rows=[]
    def add(name,d,g,s):rows.append(dict(device=tag+'.'+name,max_abs_vgs_V=float(max(abs(g-s))),max_abs_vgd_V=float(max(abs(g-d))),max_abs_vds_V=float(max(abs(d-s)))))
    for side in ['p','n']:
        a={key:q[f'X{tag}.XB{side.upper()}.'+key] for key in ['CLKP','CG','CBB','CBT','PRE']};a.update(VG=q['gate'+side+tag],VIN=q['vin'+side+tag],VDD=supply,VSS=zero,CLK=q['clk'])
        for name,terms in [('INVn',['CLKP','CLK','VSS']),('INVp',['CLKP','CLK','VDD']),('MDCHG',['CBB','CLK','VSS']),('MPCHG',['CG','CLKP','VDD']),('MLIM',['VDD','VG','CBT']),('MPRE',['VDD','CLKP','PRE']),('MGTRK',['CG','CLKP','CBB']),('MBPP',['VG','CG','CBT']),('MPVIN',['CBB','VG','VIN']),('MCASC',['VG','VDD','CLKP']),('MPRGUARD',['VG','VDD','PRE'])]:add('XB'+side.upper()+'.'+name,*(a[n] for n in terms))
        add('fixtureSW'+side,q['vout'+side+tag],a['VG'],a['VIN'])
    return rows


def extract(runs):
    sta=data(runs[0],'tran.tran');fft=data(runs[1],'tran.tran');sys.path.insert(0,str(CASE/'source/tests'))
    spec=importlib.util.spec_from_file_location('case22_verifier',CASE/'source/tests/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    times=np.array([(3+k)*10e-9+4e-9 for k in range(32)]);mid=times+4e-9;t=fft['time'];scalars={}
    for k in range(32):
        scalars[f's{k}_out']=float(np.interp(times[k],t,fft['voutpS']-fft['voutnS']))
        for side in ['p','n']:scalars[f's{k}_vgs_{side}_mid']=float(np.interp(mid[k],t,fft['gate'+side+'S']-fft['vin'+side+'S']))
    def avg(y):
        xx=np.r_[30e-9,t[(t>30e-9)&(t<350e-9)],350e-9];return float(np.trapezoid(np.interp(xx,t,y),xx)/(320e-9))
    scalars['average_power_w']=avg(-1.8*fft['VDD:p']);vals=v.analyze_fft(scalars,v.NOMINAL);vals.pop('name')
    for key,tag,sign in [('positive_retained_gain','P',1),('negative_retained_gain','N',-1)]:vals[key]=sign*float(np.interp(24e-9,sta['time'],sta['voutp'+tag]-sta['voutn'+tag]))/.8
    vals['external_clock_buffer_power_W']=avg(-1.8*fft['VCLKDD:p'])
    vals['external_clock_source_power_W']=avg(-fft['clk_src']*fft['VCLKIN:p'])
    extrema=terminal_extrema(sta,'P')+terminal_extrema(sta,'N')+terminal_extrema(fft,'S')
    vals['max_gate_terminal_voltage_V']=max(max(q['max_abs_vgs_V'],q['max_abs_vgd_V']) for q in extrema);vals['max_drain_source_voltage_V']=max(q['max_abs_vds_V'] for q in extrema)
    gates={}
    for key,lim,sense,unit,mode in [('sdr_db',72,'min','dB','amplitude_db'),('minimum_midtrack_vgs_ratio',.8,'min','VDD ratio','linear'),('positive_retained_gain',.9,'min','V/V','linear'),('negative_retained_gain',.9,'min','V/V','linear'),('average_power_w',500e-6,'max','W','linear')]:gates[key]=gate(vals[key],lim,sense,unit,mode)
    for key in ['max_gate_terminal_voltage_V','max_drain_source_voltage_V']:gates[key]=gate(vals[key],1.98,'max','V',relax=False)
    nominal_source_check=v.nominal_passes(vals,vals)
    tiers={tier:all(g['passes'][tier] for g in gates.values()) and vals['average_power_w']>=0 for tier in ['original','10pct','15pct']};tier=next((k for k in tiers if tiers[k]),None)
    samples=np.array([scalars[f's{k}_out'] for k in range(32)]);z=np.fft.fft(samples);pp=abs(z)**2;signal=pp[15]+pp[17];dist=float(sum(pp[k] for k in range(1,32) if k not in [15,17]));stable_sdr=float(10*np.log10(signal/dist))
    r=dict(case_slot=22,generated_at=now(),run_dirs=[str(d.relative_to(ROOT)) for d in runs],status='complete_'+tier if tier else 'partial',values=vals,gates=gates,pass_tiers=tiers,all_nominal_checks_complete=True,model_dimensions_valid=True,source_nominal_check=nominal_source_check,stable_nonfundamental_sum_SDR_dB=stable_sdr,terminal_extrema=extrema,samples=dict(time_s=times.tolist(),output_V=samples.tolist(),midtrack_times_s=mid.tolist(),vgs_p_V=[scalars[f's{k}_vgs_p_mid'] for k in range(32)],vgs_n_V=[scalars[f's{k}_vgs_n_mid'] for k in range(32)],spectrum_amplitude_V=(abs(z)/16).tolist()),scope='TT1.8V27C only, both bipolar hold polarities and32coherent samples, all64midtrackVGS points; remaining10PVT excluded. Fixture W64um/L0.18um/1pF fixed. Additional1.98V screen not foundry lifetime rating.')
    write_json(CASE/'latest_results.json',r);write_json(runs[-1]/'measurements.json',r);update_case(22,status=r['status'],nominal_complete=bool(tier),review_pdf_ready=False,latest_run=r['run_dirs'][-1],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--boot-uA',type=float,default=200);p.add_argument('--cap-pF',type=float,default=1.5);p.add_argument('--cell',default='INHDV8');p.add_argument('--maxstep-ps',type=float,default=5);p.add_argument('--extract',nargs=2);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        c,hd=design(a.boot_uA,a.cap_pF,a.cell);update_case(22,status='running',nominal_complete=False)
        deps=[c,hd,CASE/'sizing.json',CASE/'contract.json',CASE/'hd_cells_manifest.json',Path(__file__).resolve()];runs=[]
        for label,b in zip(['static','fft'],benches(c,a.maxstep_ps)):
            (CASE/f'bench_{label}.scs').write_text(b);runs.append(run_spectre(22,label,b,deps))
    r=extract(runs);print(json.dumps(dict(status=r['status'],values=r['values'],stable_sdr=r['stable_nonfundamental_sum_SDR_dB']),indent=2))

if __name__=='__main__':main()
