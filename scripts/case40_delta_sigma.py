"""First-order SC delta-sigma loop with explicitly migrated transistor fixtures."""
from batch29 import *
CASE=ROOT/'cases/40-delta-sigma';TASK=SOURCE/'sky130-delta-sigma-adc-1bit-first-order-osr32-sndr40'
CASES={'nominal':(.24,4,45,.02),'mid_pos':(.22,2,45,.02),'mid_inv':(.22,2,225,-.02)}

def design(switch_scale=1,ci_fF=450,hold_fF=300):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C all three original coherent records at10MHz, OSR32,N512. Original external transistor OTA and comparator are explicitly migrated fixtures; source-owned load, current, reset and comparator offset are retained.',VDD_V=1.8,temperature_C=27,clock=dict(period_s=100e-9,rise_fall_s=5e-9,width_s=34e-9,phi2_delay_s=50e-9,comparator_first_delay_s=100e-9,source_ohm=50),input_cm_V=.9,output_cm_V=.9,reference_V=[.5,1.3],bias_reference_A=50e-6,fixture_output_load_F=1e-12,fixture_input_bias_ohm=5e6,comparator_offset_diff_V=.001,stop_s=58e-6,N=512,sample_offset_s=20e-9,records={k:dict(per_leg_amp_V=v[0],tone_bin=v[1],phase_deg=v[2],per_leg_offset_V=v[3]) for k,v in CASES.items()},sndr_min_dB=40,osr32_minus16_min_dB=6,shaping_min_dB=10,AC_gain_range=[.70,1.35],DC_error_max=.035,polarity_amplitude_ratio=[.8,1.25],polarity_phase_error_max_deg=15,state_diff_peak_max_V=2,power_max_W=.002,power_definition='Original extractor arithmetic sample mean of VDD current retained as a separately labeled source metric; physical time-weighted delivered VDD power also required <=2mW. Includes OTA/comparator and50uA reference powered fromVDD, excludes ideal clocks/inputs/reference sources as source contract.',nonrelaxable='Complementary finite decisions, 0.05<density<0.95, transitions>0.05, correct AC/DC/polarity transfer and bounded state; no FFT bin deletion beyond DC/tone.',allowed='NativeMOS positiveR/C only within DUT; all fixture devices explicit.',unmodeled=['noise','mismatch','PVT','PEX','decimationfilter']))
    roles=dict(switch=lut_size('n18',.18,14,100e-6),hold_n=lut_size('n18',.18,8,75e-6),hold_p=lut_size('p18',.18,8,75e-6),ota_ref=lut_size('n18',1,10,50e-6),ota_input=lut_size('n18',1,14,275e-6),ota_load=lut_size('p18',1,10,275e-6),cm_input=lut_size('n18',.36,14,12.5e-6),cm_load=lut_size('p18',1,10,12.5e-6),cmp_input=lut_size('n18',.18,14,100e-6),cmp_tail=lut_size('n18',.18,8,300e-6),cmp_p=lut_size('p18',.18,10,50e-6))
    roles['switch_p']=lut_size('p18',.18,8,50e-6)
    lines=['simulator lang=spectre']
    def add(x):lines.extend(x.strip().splitlines())
    def mos(name,pins,role,mul=1):
        q=roles[role];total=q['rounded_W_um']*mul;parallel=int(np.ceil(total/90));add(f'M{name} ({pins}) {q["model"]} w={total/parallel:.10g}u l={q["L_um"]:g}u m={parallel}')
    # Native fixture topology and bias ratios fixed independently of DUT tuning.
    add('subckt ds_ota (vss iref vdd vinn vinp vocm voutn voutp)')
    mos('REF','iref iref vss vss','ota_ref');mos('TAIL','tail iref vss vss','ota_ref',11)
    mos('INP','voutn vinp tail vss','ota_input');mos('INN','voutp vinn tail vss','ota_input')
    mos('LP','voutp vcmfb vdd vdd','ota_load');mos('LN','voutn vcmfb vdd vdd','ota_load')
    add('RAVP (voutp sense) resistor r=1Meg\nRAVN (voutn sense) resistor r=1Meg\nCAVP (voutp sense) capacitor c=400f\nCAVN (voutn sense) capacitor c=400f')
    mos('CTAIL','ctail iref vss vss','ota_ref',.5);mos('CSENSE','cmirror sense ctail vss','cm_input');mos('CREF','vcmfb vocm ctail vss','cm_input');mos('CLE','cmirror cmirror vdd vdd','cm_load');mos('CLR','vcmfb vcmfb vdd vdd','cm_load');add('ends ds_ota')
    add('subckt ds_comparator (voutp voutn vinp vinn clk vdd vss)')
    mos('RSTP','voutp clk vdd vdd','cmp_p');mos('RSTN','voutn clk vdd vdd','cmp_p');mos('TAIL','tail clk vss vss','cmp_tail');mos('INP','voutp vinp tail vss','cmp_input');mos('INN','voutn vinn tail vss','cmp_input');mos('LP','voutp voutn vdd vdd','cmp_p');mos('LN','voutn voutp vdd vdd','cmp_p');add('CLP (voutp vss) capacitor c=200f\nCLN (voutn vss) capacitor c=200f\nends ds_comparator')
    add('subckt sigma_adc (vss vdd vip vin vp vn vcm ctrl_a ctrl_b c1a c1b c2a c2b intp intn inp inn)\nCSP (cspt cspb) capacitor c=200f\nCSN (csnt csnb) capacitor c=200f')
    add(f'CIP (inp intp) capacitor c={ci_fF:g}f\nCIN (inn intn) capacitor c={ci_fF:g}f')
    for pol in ['a','b']:
        mos('HN'+pol,f'hold_{pol} c1a ctrl_{pol} vss','hold_n');mos('HP'+pol,f'hold_{pol} c1b ctrl_{pol} vdd','hold_p');add(f'CH{pol} (hold_{pol} vss) capacitor c={hold_fF:g}f\nRH{pol} (hold_{pol} vss) resistor r=100G')
    for n,pins in [('DPH','dac_p hold_a vp vn'),('DPL','dac_p hold_b vn vn'),('DNH','dac_n hold_a vn vn'),('DNL','dac_n hold_b vp vn'),('S1','cspt c1a vip vn'),('S2','cspb c1a vcm vn'),('S3','csnt c1a vin vn'),('S4','csnb c1a vcm vn'),('I1','cspt c2a inp vn'),('I2','cspb c2a dac_p vn'),('I3','csnt c2a inn vn'),('I4','csnb c2a dac_n vn')]:
        mos(n,pins,'switch',switch_scale);d,g,s,b=pins.split();ng={'hold_a':'hold_b','hold_b':'hold_a','c1a':'c1b','c2a':'c2b'}[g];mos(n+'P',f'{d} {ng} {s} vdd','switch_p',switch_scale)
    for node in ['dac_p','dac_n','cspt','cspb','csnt','csnb']:add(f'R_{node} ({node} vcm) resistor r=100G')
    add('ends sigma_adc\nsubckt sigma_system (vss vdd vip vin vp vn vcm ctrl_a ctrl_b c1a c1b c2a c2b intp intn inp inn iref vocm sa_inp sa_inn cmpclk)\nXADC (vss vdd vip vin vp vn vcm ctrl_a ctrl_b c1a c1b c2a c2b intp intn inp inn) sigma_adc\nXOTA (vss iref vdd inn inp vocm intp intn) ds_ota\nXSA (ctrl_b ctrl_a sa_inp sa_inn cmpclk vdd vss) ds_comparator\nends sigma_system')
    save_design(CASE,'\n'.join(lines)+'\n',roles,dict(switch_scale=switch_scale,ci_fF=ci_fF,hold_fF=hold_fF,fixture_native_sizes_fixed=True),'DUT preserves source switched-cap topology, held decisions and200fF input caps. Complementary native PMOS paths parallel DAC/sample/transfer NMOS for reference linearity; decision storage capacitance is an explicit DUT parameter. Native gmID roles migrate the fixed OTA/StrongARM transistor fixtures with unchanged topology and reference-current ratios; fixture definitions are explicitly separated from sigma_adc and wrapped only for complete schematic coverage. Native wide devices split into identical parallel fingers. Native dimensions are design migration, not unchanged Sky130 geometry.')
    update_case(40,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))

def bench(kind,step=1e-9,reltol=1e-5):
    amp,bin,phase,off=CASES[kind];freq=bin*10e6/512
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
VCM (vcm 0) vsource dc=.9
VVP (vp 0) vsource dc=1.3
VVN (vn 0) vsource dc=.5
VOCM (vocm 0) vsource dc=.9
IREF (vdd iref) isource dc=50u
VINP (vip vcm) vsource dc={off:g} type=sine ampl={amp:g} freq={freq:g} sinephase={phase:g}
VINN (vin vcm) vsource dc={-off:g} type=sine ampl={amp:g} freq={freq:g} sinephase={phase+180:g}
VOSP (sa_inp intp) vsource dc=.5m
VOSN (sa_inn intn) vsource dc=-.5m
X (0 vdd vip vin vp vn vcm ctrl_a ctrl_b c1a c1b c2a c2b intp intn inp inn iref vocm sa_inp sa_inn cmpclk) sigma_system
RBIP (inp vcm) resistor r=5Meg
RBIN (inn vcm) resistor r=5Meg
CLP (intp 0) capacitor c=1p
CLN (intn 0) capacitor c=1p
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14 gmin=1e-15 cmin=1f
saveOptions options save=selected
save ctrl_a ctrl_b intp intn inp inn vip vin VDD:p X.XOTA.vcmfb X.XADC.hold_a X.XADC.hold_b X.XADC.dac_p X.XADC.dac_n X.XADC.cspt X.XADC.cspb c1a c2a
'''
    for node,delay,reverse in [('c1a',0,False),('c1b',0,True),('c2a',50,False),('c2b',50,True),('cmpclk',100,False)]:b+=f'V{node} ({node}_src 0) vsource type=pulse val0={1.8 if reverse else 0} val1={0 if reverse else 1.8} delay={delay}n rise=5n fall=5n width=34n period=100n\nR{node} ({node}_src {node}) resistor r=50\n'
    return b+f'tran tran stop=58u maxstep={step:g} skipdc=yes method=gear2only errpreset=conservative\n'

def metrics(d,kind):
    amp,bin,phase,off=CASES[kind];t=d['time'];ts=np.arange(580)*1e-7+20e-9;assert ts[-1]<=t[-1];idx=np.searchsorted(t,ts,side='right')-1;aa=d['ctrl_a'][idx];bb=d['ctrl_b'][idx];code=1-2*(aa>.9).astype(int);c=code[-512:];valid=((aa>.9)!=(bb>.9))[-512:];coef=np.fft.fft(c-np.mean(c))/512;mag=abs(coef);sndr={}
    for osr in [8,16,32]:sndr[osr]=float(10*np.log10(mag[bin]**2/sum(mag[k]**2 for k in range(1,512//(2*osr)+1) if k!=bin)))
    q=dict(dc=float(np.mean(c)),gain=float(.8*2*mag[bin]/(2*amp)),sndr8_dB=sndr[8],sndr16_dB=sndr[16],sndr32_dB=sndr[32],shaping_dB=float(10*np.log10(np.mean(mag[9:256]**2)/np.mean([mag[k]**2 for k in range(1,9) if k!=bin]))),density=float(np.mean(c>0)),transitions=float(np.mean(c[1:]!=c[:-1])),invalid=int(np.sum(~valid)),state_peak_V=float(max(abs(d['intp']-d['intn']))),source_mean_power_W=float(-1.8*np.mean(d['VDD:p'])),time_weighted_power_W=float(-1.8*np.trapz(d['VDD:p'],t)/(t[-1]-t[0])),DC_error=abs(float(np.mean(c))-2*off/.8),coefficient_real=float(coef[bin].real),coefficient_imag=float(coef[bin].imag))
    rec=dict(codes=c.tolist(),sample_times_s=ts[-512:].tolist(),spectrum_power=(mag**2).tolist());return q,rec

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());vs={};records={};g={};ok=True
    for k,path in runs.items():
        q,records[k]=metrics(data(ROOT/path,'tran.tran'),k);vs[k]=q;ok &= q['invalid']==0 and .05<q['density']<.95 and q['transitions']>.05 and .7<=q['gain']<=1.35 and q['DC_error']<=.035 and q['state_peak_V']<2 and min(q['source_mean_power_W'],q['time_weighted_power_W'])>=0
        for key,lim,sense,unit in [('sndr32_dB',40,'min','dB'),('shaping_dB',10,'min','dB'),('source_mean_power_W',.002,'max','W'),('time_weighted_power_W',.002,'max','W')]:g[k+'_'+key]=gate(q[key],lim,sense,unit,kind='amplitude_db' if unit=='dB' else 'linear')
    if len(vs)==3:
        c=lambda k:complex(vs[k]['coefficient_real'],vs[k]['coefficient_imag']);ratio=abs(c('mid_inv'))/abs(c('mid_pos'));phase=float(abs(np.angle(c('mid_inv')/c('mid_pos')/(-1))*180/np.pi));gain=vs['nominal']['sndr32_dB']-vs['nominal']['sndr16_dB'];vs['suite']=dict(polarity_amplitude_ratio=ratio,polarity_phase_error_deg=phase,osr_improvement_dB=gain);ok &= .8<=ratio<=1.25 and phase<=15;g['first_order_gain']=gate(gain,6,'min','dB',kind='amplitude_db')
    else:ok=False
    write_json(CASE/'conversion_records.json',records);return result(CASE,40,vs,g,runs,ok,conversion_records_sha256=sha(CASE/'conversion_records.json'))

def run(step=1e-9,reltol=1e-5):
    simulate_groups(40,CASE,{k:bench(k,step,reltol) for k in CASES});return extract()

def probe():
    rd=run_spectre(40,'probe_nominal',bench('nominal'),[CASE/x for x in ['circuit.scs','contract.json','sizing.json']],timeout=1800);q,rec=metrics(data(rd,'tran.tran'),'nominal');write_json(CASE/'probe_results.json',dict(run=str(rd.relative_to(ROOT)),values=q,records=rec));print(json.dumps(q,indent=2),flush=True)

if __name__=='__main__':design();run()
