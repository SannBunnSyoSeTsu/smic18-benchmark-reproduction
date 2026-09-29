"""Native n18 double-balanced Gilbert mixer, preserved functional RF conditions."""
from batch29 import *
import argparse
CASE=ROOT/'cases/30-gilbert-mixer';TASK=SOURCE/'sky130-gilbert-cell-mixer-2p4ghz-pvt-mismatch'
MOS=['MREF','MTAILP','MTAILN','MRFP','MRFN','MQ1','MQ2','MQ3','MQ4']

def design(tail_m=6.5,rf_gmid=12,lo_gmid=18,lo_m=6.5,rdeg=650,rl=3300,cout=75):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C: RF2.3/2.4/2.5GHz eachbalanced and2%RF/LOamplitude+2degreeLOimbalance; alloriginal nominaltwo-tone/compression. OtherPVT and10mismatchseeds excluded, nofullupstreamsignoff.',VDD_V=1.8,temperature_C=27,bias_A=50e-6,input_common_V=.9,LO_amplitude_each_V=.35,RF_amplitude_each_V=.02,RF_Hz=[2.3e9,2.4e9,2.5e9],IF_Hz=200e6,source_each_ohm=50,external_load_each_F=200e-15,imbalance=dict(RF=.02,LO=.02,LO_phase_error_deg=2),rf_window_s=[5e-9,15e-9],rf_spur_bands_Hz=[[25e6,175e6],[225e6,3e9]],linearity_window_s=[10e-9,30e-9],two_tone_Hz=[2.4e9,2.45e9],two_tone_amplitudes_each_V=[.01,.02],compression_amplitudes_each_V=[.02,.08],spectrum='Rectangularcoherent2048samplesinoriginalwindow, excludeendpoint; exact100MHzRF/50MHzlinearitybins, nozero-padding/leakagewindow. Report physicaldifferentialpeak amplitudes.',limits=dict(gain_min_dB=3,isolation_max_dB=-45,spur_max_dBc=-30,offset_max_V=.03,cm_min_V=.45,headroom_min_V=.2,power_max_W=.002,IIP3_min_dBm=-4,fundamental_slope=[.8,1.2],IM3_slope=[1.8,4],tone_gain_difference_max_dB=1.5,compression_max_dB=2),allowed_DUT='nativeMOS andpositiveidealR/C; no behavioralorcontrolledsources'))
    roles=dict(bias=lut_size('n18',1,18,50e-6,.45),rf=lut_size('n18',.18,rf_gmid,50e-6,.45),lo=lut_size('n18',.18,lo_gmid,50e-6,.45));w={k:q['rounded_W_um'] for k,q in roles.items()}
    txt=f'''simulator lang=spectre
subckt gilbert_mixer (vss iref vdd lop lon rfp rfn ifoutp ifoutn)
MREF (iref iref vss vss) n18 w={w['bias']}u l=1u
MTAILP (stp iref vss vss) n18 w={w['bias']}u l=1u m={tail_m:g}
MTAILN (stn iref vss vss) n18 w={w['bias']}u l=1u m={tail_m:g}
CBIAS (iref vss) capacitor c=1p
MRFP (drfp rfp stp vss) n18 w={w['rf']}u l=.18u m={tail_m:g}
MRFN (drfn rfn stn vss) n18 w={w['rf']}u l=.18u m={tail_m:g}
RDEG (stp stn) resistor r={rdeg:g}
MQ1 (ifoutp lop drfp vss) n18 w={w['lo']}u l=.18u m={lo_m:g}
MQ2 (ifoutn lon drfp vss) n18 w={w['lo']}u l=.18u m={lo_m:g}
MQ3 (ifoutn lop drfn vss) n18 w={w['lo']}u l=.18u m={lo_m:g}
MQ4 (ifoutp lon drfn vss) n18 w={w['lo']}u l=.18u m={lo_m:g}
RLP (vdd ifoutp) resistor r={rl:g}
RLN (vdd ifoutn) resistor r={rl:g}
COUTP (ifoutp vss) capacitor c={cout:g}f
COUTN (ifoutn vss) capacitor c={cout:g}f
ends gilbert_mixer
'''
    save_design(CASE,txt,roles,dict(tail_m=tail_m,rf_gmid=rf_gmid,lo_gmid=lo_gmid,lo_m=lo_m,rdeg=rdeg,rl=rl,cout=cout),'Twoindependentmirroredtailcurrents andsourcebridgeresistance linearizeRFgm; fourlargehighgmIDn18LOswitches commutatecurrent. ShortRFdevicestradegmID/currentdensityagainststackheadroom. Allregularn18realmodels; noLVTemulation.')

def bench(kind,rf=2.4e9,imb=False,step=3e-12,reltol=1e-6):
    lo=rf-200e6;two=kind in ['two_low','two_high'];amp=.01 if kind=='two_low' else .08 if kind=='large' else .02;delta=.02 if imb else 0;pherr=2 if imb else 0
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=50u
X (0 iref vdd lop lon rfp rfn ifoutp ifoutn) gilbert_mixer
CIFP (ifoutp 0) capacitor c=200f
CIFN (ifoutn 0) capacitor c=200f
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-9 iabstol=1e-14
saveOptions options save=selected
save vdd iref lop lon rfp rfn ifoutp ifoutn VDD:p X.stp X.stn X.drfp X.drfn
'''
    for side,sign,phase in [('P',1,0),('N',-1,180)]:
        n=side.lower();b+=f'VLO{side} (los{n} 0) vsource dc=.9 type=sine ampl={.35*(1+sign*delta/2):.12g} freq={lo:g} sinephase={phase-(pherr if side=="N" else 0):g}\nRLO{side} (los{n} lo{n}) resistor r=50\n'
        if two:b+=f'VRF{side}1 (rf1{n} 0) vsource dc=.9 type=sine ampl={amp:g} freq=2.4G sinephase={phase}\nVRF{side}2 (rfs{n} rf1{n}) vsource dc=0 type=sine ampl={amp:g} freq=2.45G sinephase={phase}\n'
        else:b+=f'VRF{side} (rfs{n} 0) vsource dc=.9 type=sine ampl={amp*(1+sign*delta/2):.12g} freq={rf:g} sinephase={phase}\n'
        b+=f'RRF{side} (rfs{n} rf{n}) resistor r=50\n'
    for n in MOS:b+='save '+' '.join(f'X.{n}:{k}' for k in ['ids','gm','vgs','vds','vdsat'])+'\n'
    return b+f'dcOp dc\ntran tran stop={"15n" if kind=="rf" else "30n"} maxstep={step:g} method=traponly errpreset=conservative\n'

def spectrum(d,start,stop,N=2048):
    grid=start+np.arange(N)*(stop-start)/N;t=d['time'];sp={k:2*np.abs(np.fft.rfft(np.interp(grid,t,d[p]-d[n])))/N for k,p,n in [('out','ifoutp','ifoutn'),('rf','rfp','rfn'),('lo','lop','lon')]};return np.fft.rfftfreq(N,(stop-start)/N),sp

def dbv(a,b=1):return float(20*np.log10(max(float(a),1e-30)/max(float(b),1e-30)))

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());rows=[];g={};ok=True;specs={};lin={}
    for key,path in groups.items():
        d=data(ROOT/path,'tran.tran')
        if key.startswith('rf'):
            rf=float(key[2:5])*1e9;imb=key.endswith('imb');lo=rf-2e8;f,s=spectrum(d,5e-9,15e-9);atv=lambda k,hz:float(s[k][int(round(hz/1e8))]);t=d['time'];mask=(t>5e-9)&(t<15e-9);tt=np.r_[5e-9,t[mask],15e-9];avg=lambda v:float(np.trapz(np.interp(tt,t,v),tt)/(10e-9));outamp=atv('out',2e8);low=float(max(s['out'][(f>=25e6)&(f<=175e6)]));high=float(max(s['out'][(f>=225e6)&(f<=3e9)]));cm=avg((d['ifoutp']+d['ifoutn'])/2)
            q=dict(RF_Hz=rf,imbalance=imb,conversion_gain_db=dbv(outamp,atv('rf',rf)),lo_if_isolation_db=dbv(atv('out',lo),atv('lo',lo)),rf_if_feedthrough_db=dbv(atv('out',rf),atv('rf',rf)),lo_rf_isolation_db=dbv(atv('rf',lo),atv('lo',lo)),output_dc_balance_v=abs(avg(d['ifoutp']-d['ifoutn'])),output_common_mode_v=cm,output_headroom_to_vdd_v=1.8-cm,power_w=avg(-d['vdd']*d['VDD:p']),if_amp_v=outamp,spur_low_v=low,spur_high_v=high,spur_dbc=dbv(max(low,high),outamp));rows.append(q);ok &= q['power_w']>=0
            for k,l,sense in [('conversion_gain_db',3,'min'),('output_dc_balance_v',.03,'max'),('output_common_mode_v',.45,'min'),('output_headroom_to_vdd_v',.2,'min'),('power_w',.002,'max'),('spur_dbc',-30,'max')]+([(k,-45,'max') for k in ['lo_if_isolation_db','rf_if_feedthrough_db','lo_rf_isolation_db']] if imb else []):g[key+'_'+k]=gate(q[k],l,sense,'dB/V/W',kind='amplitude_db' if k.endswith(('db','dbc')) else 'linear')
        else:
            f,s=spectrum(d,10e-9,30e-9);atv=lambda k,hz:float(s[k][int(round(hz/50e6))]);lin[key]=dict(fund1=atv('out',200e6),fund2=atv('out',250e6),im3lo=atv('out',150e6),im3hi=atv('out',300e6),input1=atv('rf',2.4e9),input2=atv('rf',2.45e9),gain_dB=dbv(atv('out',200e6),atv('rf',2.4e9)))
        specs[key]=dict(frequency_Hz=f[:61].tolist(),amplitudes_V={k:v[:61].tolist() for k,v in s.items()})
    a=lin['two_low'];b=lin['two_high'];fund=lambda q:(q['fund1']+q['fund2'])/2;inp=lambda q:(q['input1']+q['input2'])/2;im=lambda q:max(q['im3lo'],q['im3hi']);step=dbv(inp(b),inp(a));linearity=dict(IIP3_dBm=min(dbv(inp(q))+dbv(fund(q),im(q))/2 for q in [a,b])+10*np.log10(5),fundamental_slope=dbv(fund(b),fund(a))/step,IM3_slope=dbv(im(b),im(a))/step,tone_gain_difference_dB=max(abs(dbv(q['fund1'],q['fund2'])) for q in [a,b]),compression_dB=lin['small']['gain_dB']-lin['large']['gain_dB'])
    # dBm is a power unit: relaxing minimum IIP3 means a10%/15% reduction in mW.
    iip=gate(10**(linearity['IIP3_dBm']/10),10**(-4/10),'min','mW');g['IIP3_mW']=iip
    for k,l,sense,relax in [('fundamental_slope',.8,'min',False),('fundamental_slope',1.2,'max',False),('IM3_slope',1.8,'min',False),('IM3_slope',4,'max',False),('tone_gain_difference_dB',1.5,'max',True),('compression_dB',2,'max',True)]:g[k+'_'+sense]=gate(linearity[k],l,sense,'ratio/dB',relax=relax)
    bad={k:[w for w in json.loads((ROOT/v/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in w] for k,v in groups.items()};ok &= not any(bad.values());write_json(CASE/'spectral_records.json',specs)
    return result(CASE,30,dict(rf=rows,linearity=linearity,linearity_raw=lin),g,groups,ok,disallowed_warnings=bad,operating_point=dc(ROOT/groups['small']))

def run(step=3e-12,reltol=1e-6):
    benches={f'rf{rf:.1f}_'+('imb' if imb else 'bal'):bench('rf',rf*1e9,imb,step,reltol) for rf in [2.3,2.4,2.5] for imb in [False,True]};benches.update({k:bench(k,step=step,reltol=reltol) for k in ['two_low','two_high','small','large']});simulate_groups(30,CASE,benches);return extract()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k,d in [('tail-m',6.5),('rf-gmid',12),('lo-gmid',18),('lo-m',6.5),('rdeg',650),('rl',3300),('cout',75)]:p.add_argument('--'+k,type=float,default=d)
    a=p.parse_args();design(**vars(a));update_case(30,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));run()
