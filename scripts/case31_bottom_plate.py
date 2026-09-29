"""Differential bottom-plate sampling, real HD clock buffers and gm/ID TGs."""
from common import *
from hd_cells import extract_hd
from case16_miller import prefix
import argparse
import importlib.util
import shutil

CASE=ROOT/'cases/31-bottom-plate'
TASK=SOURCE/'sky130-bottom-plate-sampler-pvt'

def design(input_uA=400,common_uA=50,cap_pF=1,delay_fF=20,cell='INHDV4',last_cell='INHDV8',topology='bootstrap',boot_uA=100,boot_pF=1,unprotected=False):
    CASE.mkdir(parents=True,exist_ok=True);hd=extract_hd([cell,last_cell],CASE)
    roles={}
    for role,current in [('input',input_uA),('common',common_uA)]:
        for device in (['n18','p18'] if topology=='tg' else ['n18']):roles[role+'_'+device]=lut_size(device,.18,8,current*1e-6,.9)
    if topology=='bootstrap':
        for device in ['n18','p18']:roles['boot_'+device]=lut_size(device,.18,8,boot_uA*1e-6,.9)
        roles['top_equalizer_n18']=lut_size('n18',.18,8,600e-6,.9)
    def tg(name,drain,source,en,enb,role):
        return ''.join(f'M{name}{dev[0].upper()} ({drain} {gate} {source} {body}) {dev} w={roles[role+"_"+dev]["rounded_W_um"]:g}u l=.18u\n' for dev,gate,body in [('n18',en,'vss'),('p18',enb,'vdd')])
    c=CASE/'circuit.scs';b='// Sample capacitor bottom plates disconnect before signal-input switches.\nsimulator lang=spectre\n'
    if topology=='bootstrap':
        wn=roles['boot_n18']['rounded_W_um'];wp=roles['boot_p18']['rounded_W_um']
        b+=f'''subckt boot_drv (VIN CLK VDD VSS VG)
XCLKN (CLK CLKN VDD VSS VDD VSS) {cell}
XCLKP (CLKN CLKP VDD VSS VDD VSS) {cell}
CBOOT (CBT CBB) capacitor c={boot_pF:g}p
MDCHG (CBB CLKN VSS VSS) n18 w={wn:g}u l=.18u
MPCHG (CG CLKP VDD VDD) p18 w={wp:g}u l=.18u
MLIM (VDD VG CBT CBT) p18 w={wp:g}u l=.18u
MPRE (VDD CLK {'VG' if unprotected else 'PRE'} VSS) n18 w={wn:g}u l=.18u m=2
MGTRK (CG CLKP CBB VSS) n18 w={wn:g}u l=.18u m=2
MBPP (VG CG CBT CBT) p18 w={wp:g}u l=.18u
MPVIN (CBB VG VIN VSS) n18 w={wn:g}u l=.18u m=2
MCASC (VG VDD CLKP VSS) n18 w={wn:g}u l=.18u m=2
ends boot_drv
'''
        if not unprotected:b=b.replace('ends boot_drv','MPRGUARD (VG VDD PRE VSS) n18 w='+f'{wn:g}u l=.18u m=2\nends boot_drv')
    b+=f'''
subckt bottom_plate_sampler (vinp vinn clk vcm vdd vss vsp vsn vtopp vtopn)
XCLK0 (clk earlyb vdd vss vdd vss) {cell}
XCLK1 (earlyb early vdd vss vdd vss) {cell}
XCLK2 (early lateb vdd vss vdd vss) {cell}
XCLK3 (lateb late vdd vss vdd vss) {last_cell}
CDELAY (lateb vss) capacitor c={delay_fF:g}f
'''
    if topology=='bootstrap':
        for side in ['p','n']:b+=f'XB{side.upper()} (vin{side} late vdd vss vg{side}) boot_drv\n'
        b+='XBC (vcm early vdd vss vgc) boot_drv\n'
    for side in ['p','n']:
        if topology=='tg':
            b+=tg('I'+side.upper(),'vs'+side,'vin'+side,'late','lateb','input')
            b+=tg('C'+side.upper(),'vtop'+side,'vcm','early','earlyb','common')
        else:
            b+=f'MI{side.upper()} (vs{side} vg{side} vin{side} vss) n18 w={roles["input_n18"]["rounded_W_um"]:g}u l=.18u\n'
            b+=f'MC{side.upper()} (vtop{side} vgc vcm vss) n18 w={roles["common_n18"]["rounded_W_um"]:g}u l=.18u\n'
        b+=f'C{side.upper()} (vs{side} vtop{side}) capacitor c={cap_pF:g}p\n'
    if topology=='bootstrap':b+=f'MTS (vtopp vgc vtopn vss) n18 w={roles["top_equalizer_n18"]["rounded_W_um"]:g}u l=.18u\n'
    c.write_text(b+'ends bottom_plate_sampler\n')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,topology=topology,precharge_guard=not unprotected,bootstrap_pF=boot_pF if topology=='bootstrap' else None,capacitor_each_pF=cap_pF,delay_cap_fF=delay_fF,clock_cells=[cell,cell,cell,last_cell],rationale='Each sample capacitor common-mode plate disconnects before its input plate. Bootstrap follows sourceVIN and keeps main VGS nearVDD. A VDD-gated cascode shields the precharge switch from boosted gate voltage when CLK falls; guard uses same gmID-selected boot_n unit m2. Original HD clock cells retain vendor transistor sizes; steering analog switches operate in triode.'))
    hashes={}
    for file in ['instruction.md','solution/circuit.spi','tests/verify.py','tests/utils.py','tests/benches/tb_static.spi','tests/benches/tb_hold.spi','tests/benches/tb_fft.spi']:
        src=TASK/file;dst=CASE/'source'/file;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);hashes[file]=sha(src)
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_hashes=hashes,corner='tt',VDD_V=1.8,temperature_C=27,clock_Hz=100e6,clock_delay_s=2e-9,clock_edge_s=50e-12,clock_high_plateau_s=5e-9,clock_source_Ohm=50,common_mode_V=.9,static_differential_V=[.8,-.8],acquisition_sample_s=29e-9,acquisition_error_max_V=.005,hold_reversal_s=[8e-9,8.1e-9],hold_samples_s=[7.8e-9,11.5e-9,19.5e-9],hold_error_max_V=.005,input_sine_Hz=5e6,input_sine_differential_Vpp=1.6,held_samples=80,held_sample_s='(9+10*cycle)ns, cycle8..87',fundamental_bin=4,SFDR_min_dB=80,spur_bins='1..39 excluding4; no window or Nyquist bin, per frozen verifier',gain_error_max_fraction=.005,stored_common_mode_max_V=.025,power_window_s=[80e-9,880e-9],total_source_power_max_W=.6e-3,power_sources=['VDD','VCM','VINP','VINN','VCLK_before_50Ohm'],power_definition='Sum max(0,time-mean(-Vsource*Isource)) separately across all5 sources over800ns',legal_DUT_leaves='n18/p18 MOS, unmodified HD MOS cells, positive finite capacitors',scope_excludes=['remaining8 representative FFT PVT rows','ss/ff hold rows','noise/SNDR/THD/ENOB not graded','mismatch/PEX']))
    contract=json.loads((CASE/'contract.json').read_text())
    contract['additional_voltage_guard']=dict(max_abs_VGS_VGD_VDS_V=1.98,relaxable=False,scope='All four transient DUT copies, all analog and HD MOS terminals',basis='Engineering screen at original maximum supply 1.8*1.10; not a foundry oxide/lifetime rating')
    write_json(CASE/'contract.json',contract)
    return c,hd

def wave_clock(stop):
    points=[(0,0)]
    for j in range(int(stop/10e-9)+1):
        start=2e-9+j*10e-9
        for when,value in [(start,0),(start+50e-12,1.8),(start+5.05e-9,1.8),(start+5.1e-9,0)]:
            if when<=stop:points.append((when,value))
    if points[-1][0]<stop:points.append((stop,points[-1][1]))
    return ' '.join(f'{tm:.13g} {val:g}' for tm,val in points)

def instance(tag,kind,stop):
    def n(name):return name+tag
    b=f'''VDD{tag} ({n('vdd')} 0) vsource dc=1.8
VCM{tag} ({n('vcm')} 0) vsource dc=.9
VCLK{tag} ({n('clk_src')} 0) vsource type=pwl wave=[{wave_clock(stop)}]
RCLK{tag} ({n('clk_src')} {n('clk')}) resistor r=50
'''
    for side,sign in [('p',1),('n',-1)]:
        if kind=='sine':spec=f'type=sine dc=.9 ampl={sign*.4:g} freq=5M'
        elif kind=='hold':spec=f'type=pwl wave=[0 {.9+sign*.4:g} 8n {.9+sign*.4:g} 8.1n {.9-sign*.4:g} 30n {.9-sign*.4:g}]'
        else:spec=f'dc={.9+sign*(.4 if kind=="positive" else -.4):g}'
        b+=f'VIN{side.upper()}{tag} ({n("vin"+side)} 0) vsource {spec}\n'
    pins=[n(x) for x in ['vinp','vinn','clk','vcm','vdd']]+['0']+[n(x) for x in ['vsp','vsn','vtopp','vtopn']]
    b+='X'+tag+' ('+' '.join(pins)+') bottom_plate_sampler\n'
    b+='save '+' '.join(n(x) for x in ['vinp','vinn','clk','clk_src','vcm','vsp','vsn','vtopp','vtopn'])+'\n'
    b+='save '+' '.join(f'{src}{tag}:p' for src in ['VDD','VCM','VINP','VINN','VCLK'])+'\n'
    b+='save '+' '.join(f'X{tag}.{x}' for x in ['early','earlyb','late','lateb'])+'\n'
    if json.loads((CASE/'sizing.json').read_text())['topology']=='bootstrap':
        b+='save '+' '.join(f'X{tag}.{x}' for x in ['vgp','vgn','vgc'])+'\n'
        for inst in ['XBP','XBN','XBC']:b+='save '+' '.join(f'X{tag}.{inst}.{x}' for x in ['CBT','CBB','CG','CLKP','CLKN'])+'\n'
        if json.loads((CASE/'sizing.json').read_text()).get('precharge_guard'):
            b+='save '+' '.join(f'X{tag}.{inst}.PRE' for inst in ['XBP','XBN','XBC'])+'\n'
    return b

def benches(c,maxstep_ps=10,reltol=1e-5):
    head=prefix(c).replace('reltol=1e-6','reltol='+str(reltol)).replace('iabstol=1e-15','iabstol=1e-12')+f'include "{CASE/"hd_cells.scs"}"\n'
    short=head+''.join(instance(tag,kind,30e-9) for tag,kind in [('P','positive'),('N','negative'),('H','hold')])+f'tran tran stop=30n maxstep={maxstep_ps:g}p errpreset=conservative\n'
    sine=head+instance('S','sine',900e-9)+f'tran tran stop=900n maxstep={maxstep_ps:g}p errpreset=conservative\n'
    return short,sine

def verifier():
    sys.path.insert(0,str(CASE/'source/tests'))
    spec=importlib.util.spec_from_file_location('case31_frozen_verifier',CASE/'source/tests/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

def terminal_extrema(a,tag,sizing):
    """Gate-to-either-channel-terminal and D/S checks, not absolute boosted Vg."""
    t=a['time'];zero=np.zeros_like(t);supply=zero+1.8
    def node(n):return a[f'X{tag}.'+n]
    rows=[]
    def add(name,d,g,s):
        rows.append(dict(device=tag+'.'+name,max_abs_vgs_V=float(max(abs(g-s))),max_abs_vgd_V=float(max(abs(g-d))),max_abs_vds_V=float(max(abs(d-s)))))
    def inv(name,inp,out):
        add(name+'.nMOS',out,inp,zero);add(name+'.pMOS',out,inp,supply)
    for i,(inp,out) in enumerate([(a['clk'+tag],node('earlyb')),(node('earlyb'),node('early')),(node('early'),node('lateb')),(node('lateb'),node('late'))]):inv('XCLK'+str(i),inp,out)
    if sizing['topology']=='bootstrap':
        for inst,side in [('XBP','p'),('XBN','n'),('XBC','c')]:
            inp=a['vin'+side+tag] if side!='c' else a['vcm'+tag]
            q={n:node(inst+'.'+n) for n in ['CBT','CBB','CG','CLKP','CLKN']}
            q.update(VIN=inp,VG=node('vg'+side),VDD=supply,VSS=zero,CLK=node('late' if side!='c' else 'early'))
            if sizing.get('precharge_guard'):q['PRE']=node(inst+'.PRE')
            inv(inst+'.XCLKN',q['CLK'],q['CLKN']);inv(inst+'.XCLKP',q['CLKN'],q['CLKP'])
            devices=[('MDCHG',['CBB','CLKN','VSS']),('MPCHG',['CG','CLKP','VDD']),('MLIM',['VDD','VG','CBT']),('MPRE',['VDD','CLK','PRE' if sizing.get('precharge_guard') else 'VG']),('MGTRK',['CG','CLKP','CBB']),('MBPP',['VG','CG','CBT']),('MPVIN',['CBB','VG','VIN']),('MCASC',['VG','VDD','CLKP'])]
            if sizing.get('precharge_guard'):devices.append(('MPRGUARD',['VG','VDD','PRE']))
            for name,terminals in devices:add(inst+'.'+name,*(q[n] for n in terminals))
        for side in ['p','n']:
            add('MI'+side,a['vs'+side+tag],node('vg'+side),a['vin'+side+tag])
            add('MC'+side,a['vtop'+side+tag],node('vgc'),a['vcm'+tag])
        add('MTS',a['vtopp'+tag],node('vgc'),a['vtopn'+tag])
    else:
        for side in ['p','n']:
            for kind,dd,ss,clock in [('I','vs'+side,'vin'+side,'late'),('C','vtop'+side,'vcm','early')]:
                for typ,ctrl in [('N',clock),('P',clock+'b')]:add('M'+kind+side+typ,a[dd+tag],node(ctrl),a[ss+tag])
    return rows

def extract(runs):
    short=data(runs[0],'tran.tran');sine=data(runs[1],'tran.tran');v=verifier()
    def stored(q,tag):return q['vsp'+tag]-q['vtopp'+tag]-q['vsn'+tag]+q['vtopn'+tag]
    yP=stored(short,'P');yN=stored(short,'N');yH=stored(short,'H');t=short['time']
    values=dict(positive_acquisition_error_V=abs(float(np.interp(29e-9,t,yP))-.8),negative_acquisition_error_V=abs(float(np.interp(29e-9,t,yN))+.8))
    vals=[float(np.interp(when,t,yH)) for when in [7.8e-9,11.5e-9,19.5e-9]]
    values.update(hold_positive_capture_error_V=abs(vals[0]-.8),hold_isolation_shift_V=abs(vals[1]-vals[0]),negative_reacquisition_error_V=abs(vals[2]+.8))
    vectors={'time':sine['time'].tolist()}
    for name in ['vsp','vsn','vtopp','vtopn','clk_src','vcm','vinp','vinn']:vectors['v('+name+')']=sine[name+'S'].tolist()
    for name in ['vdd','vcm','vinp','vinn','vclk']:vectors['i('+name+')']=sine[name.upper()+'S:p'].tolist()
    values.update(v.analyze_fft(vectors,1.8))
    times=np.array([(9+10*i)*1e-9 for i in range(8,88)])
    ss=np.array([v.stored(vectors,when) for when in times]);z=np.fft.fft(ss[:,0]);amp=abs(z)/40
    gates={}
    for key in ['positive_acquisition_error_V','negative_acquisition_error_V','hold_positive_capture_error_V','hold_isolation_shift_V','negative_reacquisition_error_V']:gates[key]=gate(values[key],.005,'max','V')
    gates['sfdr_db']=gate(values['sfdr_db'],80,'min','dB','amplitude_db')
    for key,lim,unit in [('gain_error',.005,'fraction'),('stored_common_mode_error_v',.025,'V'),('total_source_power_w',.6e-3,'W')]:gates[key]=gate(values[key],lim,'max',unit)
    sizing=json.loads((runs[0]/'inputs/sizing.json').read_text())
    extrema=[]
    for tag in ['P','N','H']:extrema+=terminal_extrema(short,tag,sizing)
    extrema+=terminal_extrema(sine,'S',sizing)
    values['max_gate_terminal_voltage_V']=max(max(q['max_abs_vgs_V'],q['max_abs_vgd_V']) for q in extrema)
    values['max_drain_source_voltage_V']=max(q['max_abs_vds_V'] for q in extrema)
    for key in ['max_gate_terminal_voltage_V','max_drain_source_voltage_V']:gates[key]=gate(values[key],1.98,'max','V',relax=False)
    tiers={tier:all(g['passes'][tier] for g in gates.values()) for tier in ['original','10pct','15pct']};tier=next((k for k in tiers if tiers[k]),None)
    r=dict(case_slot=31,generated_at=now(),run_dirs=[str(rd.relative_to(ROOT)) for rd in runs],status='complete_'+tier if tier else 'partial',values=values,gates=gates,pass_tiers=tiers,all_nominal_checks_complete=True,model_dimensions_valid=True,terminal_extrema=extrema,voltage_guard_note='Additional engineering guard1.98V=1.8V*1.10 (also original maximum supply); nonrelaxable. These terminal checks are not foundry lifetime/oxide-reliability signoff.',hold_observations_V=vals,samples=dict(time_s=times.tolist(),differential_V=ss[:,0].tolist(),common_mode_V=ss[:,1].tolist(),spectrum_amplitude_V=amp.tolist()),measurement_engine='Frozen upstream analyze_fft and stored functions on actual Spectre vectors; acquisition/hold use identical interpolation times.',scope='TT/1.8V/27C only; +/-0.8V acquisition, hold reversal and reacquisition,80 coherent5MHz sine samples,all5source power. OtherPVT and mismatch excluded.')
    write_json(runs[-1]/'measurements.json',r);write_json(CASE/'latest_results.json',r)
    update_case(31,status=r['status'],nominal_complete=bool(tier),latest_run=r['run_dirs'][-1],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser()
    for name,default in [('input_uA',400),('common_uA',50),('cap_pF',1),('delay_fF',20),('maxstep_ps',5),('boot_uA',100),('boot_pF',1)]:p.add_argument('--'+name.replace('_','-'),type=float,default=default)
    p.add_argument('--topology',choices=['tg','bootstrap'],default='bootstrap')
    p.add_argument('--reltol',type=float,default=2e-6)
    p.add_argument('--unprotected',action='store_true')
    p.add_argument('--cell',default='INHDV4');p.add_argument('--last-cell',default='INHDV8');p.add_argument('--extract',nargs=2);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        params=vars(a).copy();params.pop('extract');step=params.pop('maxstep_ps');rtol=params.pop('reltol');c,hd=design(**params);update_case(31,status='running',nominal_complete=False)
        deps=[c,hd,CASE/'sizing.json',CASE/'contract.json',CASE/'hd_cells_manifest.json',Path(__file__).resolve()]
        runs=[]
        for label,b in zip(['acquisition_hold','fft'],benches(c,step,rtol)):
            (CASE/f'bench_{label}.scs').write_text(b);runs.append(run_spectre(31,label,b,deps))
    r=extract(runs);print(json.dumps(dict(status=r['status'],values=r['values'],failed=[k for k,v in r['gates'].items() if not v['passes']['15pct']]),indent=2))

if __name__=='__main__':main()
