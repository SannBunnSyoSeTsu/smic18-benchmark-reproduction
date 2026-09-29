"""Native FCT residue amplifier with fixed external SC/hold fixtures."""
from batch29 import *
from hd_cells import extract_hd
CASE=ROOT/'cases/28-fct-amplifier';TASK=SOURCE/'sky130-fct-residue-amplifier-900msps'
PERIOD=1/900e6

def design(input_scale=1,output_n_scale=1,output_p_scale=1,reservoir_pF=2,clock_drive=16,output_switch_scale=1):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C both original10mV/bin5 and20mV/bin3 records at900MS/s; fixed400fF flying capacitors,50fF output hold loads and original startup/timing.',VDD_V=1.8,temperature_C=27,fs_Hz=900e6,input_diff_peak_V=[.01,.02],tone_bins=[5,3],N=32,warmup_cycles=64,period_s=PERIOD,held_offset_s=.88e-9,track_offset_s=.78e-9,input_cm_V=1.,output_precharge_V=.9,bias_A=50e-6,fixture_flying_F=400e-15,output_load_F=50e-15,fixture_switch=dict(Ron_ohm=.1,series_ohm=1,Roff_ohm=1e12,Vt_V=.9,Vh_V=.0005,transition_regularization_V=1e-6,terminal_cap_F=100e-18),fixture_clock_migration='Fixed vendor BUFHDV16 maps the external two-inverter clock-buffer function; fixed before DUT tuning, same stimuli. Not exact Sky130 transistor delay.',startup_only_precharge_s=1e-9,power_window_s=[64*PERIOD,96*PERIOD],power_definition='Signed net DUT VDD+VCM+SAM+TRANSFER+IBIAS port energy; fixture power separate and excluded as original.',gain_range=[5.5,6.5],sfdr_min_dB=60,output_cm_range_V=[.3,1.2],output_range_V=[.2,1.6],hold_movement_max=.015,power_max_W=.005,allowed='NativeMOS, positiveideal capacitors, exact vendorHD digital. Ideal switches only in source-owned fixture.',unmodeled=['PVT','noise','mismatch','PEX']))
    roles=dict(nbias=lut_size('n18',.18,16,50e-6),pbias=lut_size('p18',.18,12,50e-6),ninput=lut_size('n18',.18,12,50e-6),pinput=lut_size('p18',.18,12,50e-6),nswitch=lut_size('n18',.18,8,200e-6),pswitch=lut_size('p18',.18,8,75e-6))
    extract_hd([f'BUFHDV{clock_drive}',f'INHDV{clock_drive}','BUFHDV16'],CASE)
    src=(TASK/'solution/circuit.spi').read_text().split('.subckt test_fct',1)[1];src='.subckt test_fct'+src
    lines=['simulator lang=spectre'];mapping={}
    for raw in src.splitlines():
        z=raw.split()
        if not z or z[0].startswith('*'):continue
        if z[0].lower()=='.subckt':lines.append('subckt '+z[1]+' ('+' '.join(z[2:])+')')
        elif z[0].lower()=='.ends':lines.append('ends '+z[1])
        elif z[0].startswith('X_CLOCK'):
            model=f'BUFHDV{clock_drive}' if z[-1]=='fct_clock_buffer' else f'INHDV{clock_drive}';lines.append(z[0]+' ('+' '.join(z[1:5]+z[3:5])+') '+model)
        elif z[0][0]=='X':
            name=z[0];pol='n' if name.startswith('XN') else 'p';par=dict(re.findall(r'(w|l|m|nf)=([.\d]+)',raw));W=float(par['w']);mult=float(par.get('m',1));scale=1
            if '_BIAS' in name or (pol=='n' and name=='XN_RESERVOIR_06'):
                role=pol+'bias';scale=W/(7.2 if pol=='n' else 11)
            elif W in [3.3,8.0625]:role=pol+'input';scale=mult*(input_scale if mult>1 else 1)
            elif W in [6.3,33]:role=pol+'bias';scale=W/(7.2 if pol=='n' else 11)*(output_n_scale if pol=='n' else output_p_scale)
            elif pol=='p' and name=='XP_INPUT_09':role='pbias';scale=1
            else:role=pol+'switch';scale=W/6*(output_switch_scale if '_OUTPUT_' in name else 1)
            q=roles[role];width=q['rounded_W_um']*scale;pm=int(np.ceil(width/90));mapping[name]=dict(role=role,total_W_um=width,parallel=pm)
            lines.append('M'+name[1:]+' ('+' '.join(z[1:5])+f') {q["model"]} w={width/pm:.10g}u l=.18u m={pm}')
        elif z[0][0]=='C':
            val=f'{reservoir_pF:g}p' if z[0] in ['C_RESERVOIR_01','C_RESERVOIR_03'] else z[3];lines.append(z[0]+' ('+' '.join(z[1:3])+f') capacitor c={val}')
        else:raise ValueError(raw)
    save_design(CASE,'\n'.join(lines)+'\n',roles,dict(input_scale=input_scale,output_n_scale=output_n_scale,output_p_scale=output_p_scale,reservoir_pF=reservoir_pF,clock_drive=clock_drive,instance_roles=mapping),'Original FCT signal topology and reservoir,reset,bias capacitor connections retained. Native gmID roles set bias,input and switch widths with source current/finger ratios; output-pull balance remains an explicit design parameter. All12 digital clock cells mapped to unmodifiedHD. Fixture remains fixed outsideDUT.')
    sizing=json.loads((CASE/'sizing.json').read_text());sizing['parameters']['output_switch_scale']=output_switch_scale;write_json(CASE/'sizing.json',sizing)
    update_case(28,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))

def fixture():
    src=(TASK/'tests/benches/fct_fixture.spi').read_text().split('.subckt fct_fixture_sc',1)[1]
    lines=['model FCT_SW relay rclosed=.1 ropen=1e12 vth=.9 trans=1u hysteresis=.0005','subckt fct_fixture_switch (a b vss ctrl)','R1 (b switch_series) resistor r=1','S1 (switch_series a ctrl vss) FCT_SW','CA (a vss) capacitor c=100a','CB (b vss) capacitor c=100a','ends fct_fixture_switch','subckt fct_fixture_sc'+src.splitlines()[0].replace(' sam',' (sam')+')']
    for raw in src.splitlines()[1:]:
        z=raw.split()
        if not z or z[0].startswith('*'):continue
        if z[0].lower()=='.ends':lines.append('ends '+z[1])
        elif z[0][0]=='C':lines.append(z[0]+' ('+' '.join(z[1:3])+') capacitor c=400f')
        elif z[0]=='XTRANSFER_COMPLEMENT_BUFFER':lines.append(z[0]+' ('+' '.join(z[1:5]+z[3:5])+') BUFHDV16')
        else:lines.append(z[0]+' ('+' '.join(z[1:-1])+') '+z[-1])
    return '\n'.join(lines)+'\n'

def bench(kind,step=10e-12,reltol=1e-5,vabstol=1e-6,iabstol=1e-12):
    amp,tone=(.01,5) if kind=='10mv' else (.02,3)
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
'''+fixture()+f'''VDD (vdd 0) vsource dc=1.8
VFIXTURE (fixture_vdd 0) vsource dc=1.8
VICM_FIXTURE (vcm_fixture 0) vsource dc=1
VICM_DUT (vcm 0) vsource dc=1
VOCM (vocm 0) vsource dc=.9
VINP (vinp vcm_fixture) vsource type=sine dc=0 ampl={amp/2:g} freq={tone*900e6/32:g} sinephase=90
VINN (vinn vcm_fixture) vsource type=sine dc=0 ampl={amp/2:g} freq={tone*900e6/32:g} sinephase=-90
IREF (0 iref) isource dc=50u
XSC (sam_fixture init_precharge transfer_fixture vcm_fixture vinp vinn cinn cinp fixture_vdd 0) fct_fixture_sc
XDUT (cinn cinp coutn coutp iref sam transfer vcm vdd vdd 0 0) test_fct
CLOADP (voutp vcm_fixture) capacitor c=50f
CLOADN (voutn vcm_fixture) capacitor c=50f
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol={vabstol:g} iabstol={iabstol:g} gmin=1e-15 max_minstep_nonconv=10000 max_approach_minstep=10000
saveOptions options save=selected
save vinp vinn cinn cinp coutn coutp voutp voutn sam transfer iref VDD:p VICM_DUT:p VSAM_DUT:p VTRANSFER_DUT:p XDUT.bias_n_cascode XDUT.bias_p_cascode XDUT.reservoir_hi_p XDUT.reservoir_lo_p
'''
    for name,node,delay,rise,width,period in [('SAM_FIXTURE','sam_fixture',PERIOD-.1e-9,10e-12,PERIOD-.8e-9,PERIOD),('TRANSFER_FIXTURE','transfer_fixture',PERIOD-.8e-9,10e-12,.5e-9,PERIOD),('SAM_DUT','sam',PERIOD-.1e-9,10e-12,PERIOD-.8e-9,PERIOD),('TRANSFER_DUT','transfer',PERIOD-.8e-9,10e-12,.5e-9,PERIOD),('SAMPLE_OUT','sample_out',PERIOD-1.03e-9,20e-12,.72e-9,PERIOD),('INIT_PRECHARGE','init_precharge',0,10e-12,1e-9,1e-6)]:b+=f'V{name} ({node} 0) vsource type=pulse val0=0 val1=1.8 delay={delay:.14g} rise={rise:g} fall={rise:g} width={width:.14g} period={period:.14g}\n'
    for name,a,z,g in [('PREN','vocm','voutn','sam_fixture'),('PREP','vocm','voutp','sam_fixture'),('INITN','vocm','voutn','init_precharge'),('INITP','vocm','voutp','init_precharge'),('SAMN','coutn','voutn','sample_out'),('SAMP','coutp','voutp','sample_out')]:b+=f'X{name} ({a} {z} 0 {g}) fct_fixture_switch\n'
    times=sorted([(64+j)*PERIOD+off for j in range(32) for off in [.78e-9,.88e-9]])
    strobe=' '.join(f'{x:.17g}' for x in times)
    return b+f'tran tran stop={97*PERIOD:.14g} maxstep={step:g} method=gear2only errpreset=conservative strobetimes=[{strobe}] strobeoutput=all\n'

def metrics(d,kind):
    amp,tone=(.01,5) if kind=='10mv' else (.02,3);t=d['time'];held=(64+np.arange(32))*PERIOD+.88e-9;early=held-.1e-9;p=np.interp(held,t,d['voutp']);n=np.interp(held,t,d['voutn']);dif=p-n;track=np.interp(early,t,d['voutp']-d['voutn']);sp=abs(np.fft.rfft(dif-np.mean(dif)));spur=max(x for k,x in enumerate(sp) if k not in [0,tone]);a,z=64*PERIOD,96*PERIOD;tt=np.r_[a,t[(t>a)&(t<z)],z]
    comps={'VDD':-1.8*d['VDD:p'],'VCM':-d['VICM_DUT:p'],'SAM':-d['sam']*d['VSAM_DUT:p'],'TRANSFER':-d['transfer']*d['VTRANSFER_DUT:p'],'IBIAS':d['iref']*50e-6};powers={k:float(np.trapz(np.interp(tt,t,v),tt)/(z-a)) for k,v in comps.items()}
    q=dict(gain_vv=float(2*sp[tone]/32/amp),sfdr_db=float(20*np.log10(sp[tone]/max(spur,1e-30))),cm_mean_v=float(np.mean((p+n)/2)),output_min_v=float(min(p.min(),n.min())),output_max_v=float(max(p.max(),n.max())),hold_movement_ratio=float(np.sqrt(np.sum((track-dif)**2)/np.sum(dif**2))),power_w=sum(powers.values()))
    rec=dict(sample_times_s=held.tolist(),outp=p.tolist(),outn=n.tolist(),track_diff_V=track.tolist(),spectrum=sp.tolist(),power_components_W=powers);return q,rec

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());vs={};recs={};gs={};ok=len(runs)==2
    for k,path in runs.items():
        q,recs[k]=metrics(data(ROOT/path,'tran.tran'),k);vs[k]=q;ok &= q['power_w']>=0
        for key,lim,sense,unit in [('gain_vv',5.5,'min','V/V'),('gain_vv',6.5,'max','V/V'),('sfdr_db',60,'min','dB'),('cm_mean_v',.3,'min','V'),('cm_mean_v',1.2,'max','V'),('output_min_v',.2,'min','V'),('output_max_v',1.6,'max','V'),('hold_movement_ratio',.015,'max','ratio'),('power_w',.005,'max','W')]:gs[k+'_'+key+'_'+sense]=gate(q[key],lim,sense,unit,kind='amplitude_db' if unit=='dB' else 'linear')
    write_json(CASE/'sample_records.json',recs);return result(CASE,28,vs,gs,runs,ok,sample_records_sha256=sha(CASE/'sample_records.json'))

def run(step=10e-12,reltol=1e-5,vabstol=1e-6,iabstol=1e-12):simulate_groups(28,CASE,{k:bench(k,step,reltol,vabstol,iabstol) for k in ['10mv','20mv']});return extract()
def probe():
    rd=run_spectre(28,'probe_10mv',bench('10mv'),[CASE/x for x in ['circuit.scs','sizing.json','contract.json','hd_cells.scs','hd_cells_manifest.json']],timeout=1800);q,rec=metrics(data(rd,'tran.tran'),'10mv');write_json(CASE/'probe_results.json',dict(run=str(rd.relative_to(ROOT)),values=q,records=rec));print(json.dumps(q,indent=2),flush=True)
def final_design():
    design(input_scale=.3,output_n_scale=2.3,output_p_scale=1.23,reservoir_pF=4,clock_drive=12,output_switch_scale=.6)

if __name__=='__main__':final_design();run()
