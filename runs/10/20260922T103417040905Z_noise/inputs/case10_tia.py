"""SMIC18 two-stage resistor-feedback analog-inverter TIA, nominal only."""
from common import *
import argparse
import importlib.util

CASE=ROOT/'cases/10-tia'
TASK=SOURCE/'sky130-tia-zt8k-bw750m-noise5p-sfdr70-power5m-pt'
DEVS=['MN1','MP1','MN2','MP2','MREF']
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region']

def design(first=900,second=800,rf1=5550,rin2=5500,rf2=13200,pscale=1):
    CASE.mkdir(parents=True,exist_ok=True);sources={}
    for name in ['instruction.md','solution/circuit.spi','tests/verify.py','tests/utils.py']+['tests/benches/'+x for x in ['tb_ac_power.spi','tb_noise.spi','tb_sfdr.spi']]:
        src=TASK/name;dest=CASE/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(src.read_bytes())
        assert sha(src)==sha(dest);sources[name]=dict(path=str(src),sha256=sha(src),frozen=str(dest.relative_to(ROOT)))
    roles={'n_amp':lut_size('n18',.18,3.4,100e-6,.9),'p_amp':lut_size('p18',.18,3.9,100e-6,.9),'reference':lut_size('n18',1,14,20e-6,.45)}
    w={k:q['rounded_W_um'] for k,q in roles.items()};c=CASE/'circuit.scs'
    c.write_text(f'''// Analog inverters in two resistor-feedback gain stages, not digital gates.
// D G S B; legal gm/ID model-unit widths, all capacitors are in the bench.
simulator lang=spectre
subckt tia (iref in vcm vdd vout vss)
MN1 (n1 in vss vss) n18 w={w['n_amp']:g}u l=.18u m={first/100:g}
MP1 (n1 in vdd vdd) p18 w={w['p_amp']:g}u l=.18u m={first*pscale/100:g}
RF1 (n1 in) resistor r={rf1:g}
RB (in vcm) resistor r=1M
MN2 (vout nbuf vss vss) n18 w={w['n_amp']:g}u l=.18u m={second/100:g}
MP2 (vout nbuf vdd vdd) p18 w={w['p_amp']:g}u l=.18u m={second*pscale/100:g}
RIN2 (n1 nbuf) resistor r={rin2:g}
RFB2 (vout nbuf) resistor r={rf2:g}
MREF (iref iref vss vss) n18 w={w['reference']:g}u l=1u
ends tia
''')
    rows=[]
    for line in c.read_text().splitlines():
        m=re.match(r'(M\w+) \((.*?)\) (n18|p18) w=([.\d]+)u l=([.\d]+)u(?: m=([.\d]+))?',line)
        if m:
            name,pins,model,ww,ll,mult=m.groups();ww=float(ww);mm=float(mult or 1);rows.append(dict(name=name,pins=pins.split(),model=model,W_unit_um=ww,L_um=float(ll),m=mm,W_total_um=ww*mm,unit_width_valid=ww<=100))
    assert len(rows)==5 and all(x['unit_width_valid'] for x in rows)
    write_json(CASE/'geometry.json',dict(circuit_sha256=sha(c),devices=rows,all_unit_widths_valid=True,digital_logic='none; CMOS inverters are continuously biased analog gain stages'))
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,parameters=dict(first=first,second=second,rf1=rf1,rin2=rin2,rf2=rf2,pscale=pscale),rationale='Two self-biased analog inverter stages split transimpedance and voltage gain. Target VGS around0.9V from n gm/ID3.4 and p3.9; both conduct simultaneously.100uA base units replicated to900/800uA initially. Ideal lowfrequency ZT=RF1*(RFB2/RIN2)=13.32kohm, with finite loopgain/loading losses. The first input sees0.3pF, second output0.2pF. The20uA reference is terminated by an n18 diode as in source; inverter biases arise from resistive feedback, not this reference.',skill_assets='/home/IC/.codex/skills/gmoverid/assets/design_gmoverid.py',target_lut_api=str(LUT_ROOT/'gmidsmic.py')))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_files=sources,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=20e-6,VCM_V=.9,input_cap_F=.3e-12,output_cap_F=.2e-12,DUT_elements='target MOS and finite positive resistors only',
      ac=dict(frequency_Hz=[1e6,10.1e9],points_per_decade=100,zt_at1MHz_min_ohm=8000,bandwidth_min_Hz=750e6,bandwidth_definition='first upper falling crossing of |ZT(1MHz)|/sqrt(2); report lower bound10GHz only if no crossing and response at10GHz still above threshold',power_max_W=.005,power_definition='abs(VDD*I(VDD))+abs(VCM*I(VCM)); IREF drawn fromVDD already'),
      noise=dict(band_Hz=[10e6,500e6],max_density_A_per_sqrtHz=5e-12,integrated_max_Arms=.1e-6,maximum_at_every_saved_frequency=True),
      sfdr=dict(input_sine_Hz=100e6,input_peak_A=10e-6,public_diagnostic_peak_A=5e-6,official_peak_used_A=10e-6,stop_s=170e-9,final_cycles=16,period_s=10e-9,samples_per_cycle=1024,FFT_samples=16384,window_s=[10e-9,170e-9],SFDR_min_dBc=70,large_signal_ZT_min_ohm=8000,definition='Frozen sfdr_metrics: uniform np.interp resample,remove mean,2|rFFT|/N; bin16 fundamental; largest remaining nonDC line anywhere; fundamental_amplitude/10uA'),
      nominal_only=True,excluded=['other14 process/temperature points','supply-voltage variation','extra photodiode capacitance','extracted parasitics/statistical mismatch'],relaxation='All original comparisons are strict. Positive min*0.9/0.85,max*1.1/1.15; SFDR is amplitude fundamental/spur ratio and dB limits add20log10(.9/.85). Original load/stimulus/noise/FFT windows unchanged.'))
    return c

def prefix(c):return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-7 vabstol=1e-10 iabstol=1e-16
saveOptions options save=selected
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=20u
VCM (vcm 0) vsource dc=.9
X (iref in vcm vdd vout 0) tia
CIN (in 0) capacitor c=.3p
CL (vout 0) capacitor c=.2p
save vout in vcm VDD:p VCM:p iref X.n1 X.nbuf
'''

def acbench(c):
    b=prefix(c)+'IIN (in 0) isource dc=0 mag=1\n'
    for name in DEVS:b+='save '+' '.join(f'X.{name}:{f}' for f in OPFIELDS)+'\n'
    return b+'dcOp dc\nac ac start=1M stop=10.1G dec=100\n'

def noisebench(c):return prefix(c)+'''IIN (in 0) isource dc=0
noise (vout 0) noise start=10M stop=500M dec=100 iprobe=IIN
'''

def sfdrbench(c):return prefix(c)+'''IIN (in 0) isource type=sine dc=0 ampl=10u freq=100M
save IIN:p
tran tran stop=170n maxstep=5p strobeperiod=9.765625p strobeoutput=strobeonly errpreset=conservative
'''

def source_verifier():
    old=sys.modules.get('utils');sp=importlib.util.spec_from_file_location('utils',CASE/'source/tests/utils.py');u=importlib.util.module_from_spec(sp);sys.modules['utils']=u;sp.loader.exec_module(u)
    sp=importlib.util.spec_from_file_location('case10_frozen_verify',CASE/'source/tests/verify.py');v=importlib.util.module_from_spec(sp);sys.modules[sp.name]=v;sp.loader.exec_module(v)
    if old is None:sys.modules.pop('utils',None)
    else:sys.modules['utils']=old
    return v

def extract(runs):
    v=source_verifier();rp={k:Path(x) for k,x in runs.items()};a=data(rp['ac'],'ac.ac');o=dc(rp['ac']);f=a['freq'];mag=abs(a['vout']);zt=float(mag[0]);threshold=zt/np.sqrt(2);ids=np.flatnonzero((mag[:-1]>=threshold)&(mag[1:]<threshold));z10=float(np.interp(1e10,f,mag));lowerbound=False
    if len(ids):i=ids[0];weight=(threshold-mag[i])/(mag[i+1]-mag[i]);bw=float(f[i]+weight*(f[i+1]-f[i]));bwlog=float(np.exp(np.log(f[i])+weight*np.log(f[i+1]/f[i])))
    elif z10>=threshold:bw=bwlog=1e10;lowerbound=True
    else:raise ValueError('No bandwidth crossing and10GHz response is belowthreshold')
    vals=dict(zt_1m_ohm=zt,zt_10g_ohm=z10,bandwidth_hz=bw,power_w=abs(1.8*o['VDD:p'])+abs(.9*o['VCM:p']))
    detail=dict(ac=dict(bandwidth_is_lower_bound=lowerbound,bandwidth_logfrequency_crosscheck_Hz=bwlog,relative_interpolation_difference=abs(bw/bwlog-1),VDD_power_W=abs(1.8*o['VDD:p']),VCM_power_W=abs(.9*o['VCM:p'])))
    op={}
    for name in DEVS:
        q={k:o[f'X.{name}:{k}'] for k in OPFIELDS};q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[name]=q
    sourcechecks=v.ac_checks([dict(point=v.NOMINAL,name=v.point_name(v.NOMINAL),**vals)],{v.NOMINAL})
    if 'noise' in rp:
        q=data(rp['noise'],'noise.noise',required=['in','out']);ff=q['freq'];psd=abs(q['in'])**2;integral=float(np.sqrt(np.trapz(psd,ff)));alpha=np.log(psd[1:]/psd[:-1])/np.log(ff[1:]/ff[:-1]);exponent=alpha+1;powerlaw=psd[:-1]*ff[:-1]*np.expm1(exponent*np.log(ff[1:]/ff[:-1]))/exponent;ni=float(np.sqrt(sum(powerlaw)))
        vals.update(noise_density_a_per_rt_hz=float(max(abs(q['in']))),integrated_noise_a_rms=integral);detail['noise']=dict(points=len(ff),band_Hz=[float(ff[0]),float(ff[-1])],worst_frequency_Hz=float(ff[np.argmax(abs(q['in']))]),power_law_integral_Arms=ni,relative_integration_difference=abs(integral/ni-1))
        sourcechecks+=v.noise_checks([dict(point=v.NOMINAL,name=v.point_name(v.NOMINAL),**vals)],{v.NOMINAL})
    if 'sfdr' in rp:
        q=data(rp['sfdr'],'tran.tran');sf=rp['sfdr']/'sfdr_psf.dat';np.savetxt(sf,np.column_stack([q['time'],q['vout']]),fmt='%.17e');z,sfr,spur=v.sfdr_metrics(sf);vals.update(large_signal_zt_ohm=z,sfdr_db=sfr,largest_spur_hz=spur)
        stop=q['time'][-1];start=stop-160e-9;mask=(q['time']>=start)&(q['time']<stop);ut=start+np.arange(16384)*160e-9/16384;uy=np.interp(ut,q['time'][mask],q['vout'][mask]);uy-=np.mean(uy);sp=2*abs(np.fft.rfft(uy))/16384;sp[0]=0;fund=float(sp[16]);spur_amp=sp.copy();spur_amp[16]=0;assert abs(20*np.log10(fund/max(spur_amp))-sfr)<1e-10
        np.savetxt(rp['sfdr']/'spectrum.csv',np.column_stack([np.fft.rfftfreq(16384,160e-9/16384),sp]),delimiter=',',header='frequency_Hz,amplitude_V',comments='')
        detail['sfdr']=dict(frozen_function='sfdr_metrics',translated_waveform=str(sf.relative_to(ROOT)),translated_waveform_sha256=sha(sf),FFT_samples=16384,cycles=16,window_s=[float(start),float(stop)],sample_interval_s=160e-9/16384,fundamental_amplitude_V=fund,largest_spur_amplitude_V=float(max(spur_amp)),spectrum=str((rp['sfdr']/'spectrum.csv').relative_to(ROOT)))
        sourcechecks.append(v.sfdr_check([dict(point=v.NOMINAL,name=v.point_name(v.NOMINAL),**vals)],{v.NOMINAL}))
    specs=[('zt_1m_ohm',8000,'min','ohm','linear'),('bandwidth_hz',750e6,'min','Hz','linear'),('power_w',.005,'max','W','linear'),('noise_density_a_per_rt_hz',5e-12,'max','A/sqrtHz','linear'),('integrated_noise_a_rms',.1e-6,'max','Arms','linear'),('large_signal_zt_ohm',8000,'min','ohm','linear'),('sfdr_db',70,'min','dBc','amplitude_db')]
    gates={}
    for key,lim,sense,unit,kind in specs:
        if key not in vals:continue
        q=gate(vals[key],lim,sense,unit,kind);q['comparison']='>' if sense=='min' else '<';q['passes']={t:bool(q['value']>z if sense=='min' else q['value']<z) for t,z in q['limits'].items()};gates[key]=q
    complete=set(rp)=={'ac','noise','sfdr'};valid=bool(all(np.isfinite(x) for x in vals.values()) and vals['power_w']>0);tiers={t:bool(complete and valid and len(gates)==7 and all(q['passes'][t] for q in gates.values())) for t in ['original','10pct','15pct']};tier=next((x for x in tiers if tiers[x]),None)
    r=dict(case_slot=10,generated_at=now(),status='complete_'+tier if tier else 'partial',values=vals,gates=gates,pass_tiers=tiers,measurement_detail=detail,source_nominal_checks=sourcechecks,operating_point=op,dc_nodes={k:x for k,x in o.items() if ':' not in k},all_nominal_checks_complete=complete,nonrelaxable_guards_pass=valid,nominal_OP_all_5_saturation=all(q['headroom_V']>0 for q in op.values()),model_dimensions_valid=True,run_dirs=[str(x.relative_to(ROOT)) for x in rp.values()],runs_by_analysis={k:str(x.relative_to(ROOT)) for k,x in rp.items()},geometry_sha256=sha(CASE/'geometry.json'),source_verifier_sha256=sha(CASE/'source/tests/verify.py'),measurement_engine='Frozen sfdr_metrics and original nominal ac_checks/noise_checks/sfdr_check. AC crossing linear interpolation as bench.meas with log-frequency crosscheck; noise direct spectral maximum and PSD integration over fixed10..500MHz.',scope='tt1.8V27C,originalAC/noise/official10uA SFDR; other14 process/temperature points,extra photodiodeC,voltagevariation,parasitics,mismatch excluded.')
    write_json(CASE/'latest_results.json',r);write_json(rp['ac']/'measurements.json',r);update_case(10,status=r['status'],nominal_complete=bool(tier),case_dir=str(CASE.relative_to(ROOT)),results=str((CASE/'latest_results.json').relative_to(ROOT)),run_dirs=r['run_dirs']);return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['static','full'],default='full')
    for k,d in dict(first=900,second=800,rf1=5550,rin2=5500,rf2=13200,pscale=1).items():p.add_argument('--'+k,type=float,default=d)
    args=vars(p.parse_args());mode=args.pop('mode');update_case(10,status='running',nominal_complete=False);c=design(**args);deps=[c,CASE/'sizing.json',CASE/'contract.json',Path(__file__).resolve()];runs={}
    for k,fn in [('ac',acbench)]+([('noise',noisebench),('sfdr',sfdrbench)] if mode=='full' else []):
        b=fn(c);(CASE/f'testbench_{k}.scs').write_text(b);runs[k]=run_spectre(10,k,b,deps)
    r=extract(runs);print(json.dumps(dict(status=r['status'],values=r['values'],nodes=r['dc_nodes'],OP=r['operating_point'],runs=r['run_dirs']),indent=2))

if __name__=='__main__':main()
