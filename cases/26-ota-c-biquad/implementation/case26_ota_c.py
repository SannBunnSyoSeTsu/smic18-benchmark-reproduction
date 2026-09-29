"""Source-degenerated fully differential OTA-C biquad, two CMFB loops."""
from batch29 import *
import argparse
CASE=ROOT/'cases/26-ota-c-biquad';TASK=SOURCE/'sky130-fully-differential-ota-c-biquad-pvt'

def design(rdeg=19100,rq=8000,c1=8,c2=4,current=20,input_gmid=22,bpratio=1.5):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C completeAC/noise/threeamplitude-frequencyTHD/CMstep. Other24ACnoise PVT and2dynamicstressconditions excluded.',VDD_V=1.8,temperature_C=27,bias_A=20e-6,VCM_V=.9,probe_load_each_F=250e-15,ac_Hz=[1e3,1e8],fit_Hz=[1e3,8e6],original_ac_dec=100,noise_Hz=[1e3,4e6],thd=dict(stop_s=30e-6,cycles=2,N=256,harmonics=[2,3,4,5],cases=[[200e3,.6],[200e3,.9],[2e6,.9]]),cm_step=dict(start_s=5e-6,end_s=5.05e-6,low_V=.85,high_V=.95,band_V=.01,late_s=12e-6,stop_s=20e-6),limits=dict(f0_Hz=[1.8e6,2.2e6],Q=[.65,.75],passgain_dB=[-1,1],fit_rms_dB=.5,stop20M_dB=35,bp_peak_Hz=[1.7e6,2.3e6],bp_peak_dB=[-8,-5],bp_1k_rejection_dB=18,bp_200k_20M_rejection_dB=15,cm_error_V=.01,power_W=500e-6,noise_Vrms=500e-6,thd_dB=[-45,-30,-45],fundamental_gain_min=[.85,.8,.5],bp_f0_thd_dB=-45,bp_f0_gain_min=.3,cm_settle_s=1e-6),allowed_DUT='nativeMOS andpositiveidealR/C allowed; no behavioral orcontrolledsources',gmID='initialtableindices; dynamicgm/ID differsunderlargeinput; allsourcebodyeffectsretained'))
    roles=dict(bias=lut_size('n18',1,18,20e-6,.45),input=lut_size('n18',.36,input_gmid,current*1e-6,.45),load=lut_size('p18',1,14,current*1e-6,.9),cm_input=lut_size('n18',.36,20,current*.5e-6,.45),cm_load=lut_size('p18',1,14,current*.5e-6,.9));w={k:q['rounded_W_um'] for k,q in roles.items()};m=current/20
    text='simulator lang=spectre\n'
    for name,hasload,pmult,deg in [('gmc_core',True,1,rdeg),('gmc_core_bp',True,bpratio,rdeg),('gmc_sink',False,0,rq)]:
        ports='vss vdd vbn vctrl inp inn outp outn' if hasload else 'vss vbn inp inn outp outn';text+=f'''subckt {name} ({ports})
MTA (ta vbn vss vss) n18 w={w['bias']}u l=1u m={m:g}
MTB (tb vbn vss vss) n18 w={w['bias']}u l=1u m={m:g}
RDEG (ta tb) resistor r={deg:g}
MA (outn inp ta vss) n18 w={w['input']}u l=.36u
MB (outp inn tb vss) n18 w={w['input']}u l=.36u
'''
        if hasload:text+=f'''MLA (outn vctrl vdd vdd) p18 w={w['load']}u l=1u m={pmult:g}
MLB (outp vctrl vdd vdd) p18 w={w['load']}u l=1u m={pmult:g}
'''
        text+=f'ends {name}\n'
    text+=f'''subckt cmfb_amp (vss vdd vbn vocm vsense vctrl)
MCTA (cta vbn vss vss) n18 w={w['bias']}u l=1u m={m/2:g}
MCTB (ctb vbn vss vss) n18 w={w['bias']}u l=1u m={m/2:g}
RCM (cta ctb) resistor r=5k
MC1 (cd vsense cta vss) n18 w={w['cm_input']}u l=.36u
MC2 (vctrl vocm ctb vss) n18 w={w['cm_input']}u l=.36u
MCL1 (cd cd vdd vdd) p18 w={w['cm_load']}u l=1u
MCL2 (vctrl vctrl vdd vdd) p18 w={w['cm_load']}u l=1u
CCM (vctrl vdd) capacitor c=.3p
ends cmfb_amp
subckt fd_ota_c_biquad (vss iref vdd vinp vinn vocm vbpp vbpn voutp voutn)
MREF (iref iref vss vss) n18 w={w['bias']}u l=1u
XGIN (vss vdd iref vc1 vinp vinn vbpp vbpn) gmc_core_bp
XGF (vss vdd iref vc2 vbpp vbpn voutp voutn) gmc_core
XGB (vss vdd iref vc1 voutp voutn vbpn vbpp) gmc_core_bp
XGQ (vss iref vbpp vbpn vbpn vbpp) gmc_sink
RS1A (vbpp sense1) resistor r=1Meg
RS1B (vbpn sense1) resistor r=1Meg
XCM1 (vss vdd iref vocm sense1 vc1) cmfb_amp
RS2A (voutp sense2) resistor r=1Meg
RS2B (voutn sense2) resistor r=1Meg
XCM2 (vss vdd iref vocm sense2 vc2) cmfb_amp
C1P (vbpp vss) capacitor c={c1:g}p
C1N (vbpn vss) capacitor c={c1:g}p
C2P (voutp vss) capacitor c={c2:g}p
C2N (voutn vss) capacitor c={c2:g}p
ends fd_ota_c_biquad
'''
    save_design(CASE,text,roles,dict(rdeg=rdeg,rq=rq,c1=c1,c2=c2,current=current,input_gmid=input_gmid,bpratio=bpratio),'Threepositivefullydifferential source-degeneratedsignalGms andonecrosseddampingGm. Shared20uA currentreference, separateCMFBperstate. BPPMOSloadm1.5suppliesthreesinkbanks. Regularn18 replacesoriginalLVTusinggmID22current-densityselection andexplicitbodyeffect, notmodelalias.')

def bench(kind,step=2e-9,reltol=1e-6,dec=100,noise_dec=80):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=20u
VOCM (vocm 0) vsource '''+('type=pwl wave=[0 .85 5u .85 5.05u .95 20u .95]' if kind=='cmstep' else 'dc=.9')+f'''
X (0 iref vdd vinp vinn vocm vbpp vbpn voutp voutn) fd_ota_c_biquad
CLP (voutp 0) capacitor c=250f
CLN (voutn 0) capacitor c=250f
CBP (vbpp 0) capacitor c=250f
CBN (vbpn 0) capacitor c=250f
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-9 iabstol=1e-14
saveOptions options save=selected
save vdd iref vinp vinn vocm voutp voutn vbpp vbpn VDD:p X.vc1 X.vc2 X.sense1 X.sense2
'''
    for n,phase in [('VINP',0),('VINN',180)]:
        spec=f'dc=.9 mag=.5 phase={phase}'
        if kind in ['thd','thd2','thd_f0']:
            amp=.15 if kind=='thd' else .225;freq=2e6 if kind=='thd_f0' else 200e3;spec=f'dc=.9 type=sine ampl={amp:g} freq={freq:g} sinephase={phase}'
        b+=f'{n} ({n.lower()} 0) vsource {spec}\n'
    if kind=='ac':
        for inst,devs in [('MREF',[]),('XGIN',['MTA','MTB','MA','MB','MLA','MLB']),('XGF',['MTA','MA','MLA']),('XCM1',['MCTA','MC1','MCL1','MC2','MCL2']),('XCM2',['MCTA','MC1','MCL1','MC2','MCL2'])]:
            for dev in devs or ['']:b+='save '+' '.join(f'X.{inst}{"."+dev if dev else ""}:{k}' for k in ['ids','gm','gmbs','vgs','vds','vdsat'])+'\n'
        b+=f'dcOp dc\nac ac start=1k stop=100M dec={dec}\n'
    elif kind=='noise':b+=f'noise (voutp voutn) noise iprobe=VINP start=1k stop=4M dec={noise_dec}\n'
    else:b+=f'tran tran stop={"20u" if kind=="cmstep" else "30u"} maxstep={step:g} method=gear2only errpreset=conservative\n'
    return b

def harmonic(d,f,amp,which='lp'):
    t=d['time'];y=d['voutp']-d['voutn'] if which=='lp' else d['vbpp']-d['vbpn'];grid=t[-1]-2/f+np.arange(256)*2/f/256;sp=np.fft.rfft(np.interp(grid,t,y));sig=abs(sp[2]);harm=np.sqrt(sum(abs(sp[2*k])**2 for k in range(2,6)))
    return dict(output_amplitude_V=float(2*sig/256),fundamental_gain=float(2*sig/256/(amp/2)),thd_dB=float(20*np.log10(max(harm,1e-12)/max(sig,1e-12))))

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());a=data(ROOT/groups['ac'],'ac.ac');op=dc(ROOT/groups['ac']);f=a['freq'];lp=abs(a['voutp']-a['voutn']);bp=abs(a['vbpp']-a['vbpn']);sel=f<=8e6;x=(f[sel]/2e6)**2;c0,c1,c2=np.linalg.lstsq(np.column_stack([np.ones(len(x)),x,x*x]),1/lp[sel]**2,rcond=None)[0];gain=1/np.sqrt(c0);f0=2e6*(c0/c2)**.25;Q=1/np.sqrt(c1/c2/(f0/2e6)**2+2);fitted=gain/np.sqrt((1-(f[sel]/f0)**2)**2+(f[sel]/f0/Q)**2);ff=np.flatnonzero((f>2e5)&(f<2e7));peakidx=ff[np.argmax(bp[ff])];nearest=lambda hz:int(np.argmin(abs(f-hz)))
    ac=dict(f0_Hz=float(f0),Q=float(Q),passgain_dB=float(20*np.log10(gain)),fit_error_dB=float(np.sqrt(np.mean((20*np.log10(lp[sel]/fitted))**2))),atten20M_dB=float(-20*np.log10(lp[nearest(20e6)]/gain)),bp_peak_Hz=float(f[peakidx]),bp_peak_dB=float(20*np.log10(bp[peakidx])),bp_1k_dB=float(20*np.log10(bp[peakidx]/bp[nearest(1e3)])),bp_200k_dB=float(20*np.log10(bp[peakidx]/bp[nearest(200e3)])),bp_20M_dB=float(20*np.log10(bp[peakidx]/bp[nearest(20e6)])),cm_error_V=max(abs((op[p]+op[n])/2-.9) for p,n in [('voutp','voutn'),('vbpp','vbpn')]),power_W=-1.8*op['VDD:p'])
    vals={'ac':ac};g={};ok=ac['power_W']>=0
    for k,center,tol in [('f0_Hz',2e6,.2e6),('Q',.7,.05),('bp_peak_Hz',2e6,.3e6)]:g[k+'_error']=gate(abs(ac[k]-center),tol,'max','Hz/ratio')
    for k,limit,sense in [('passgain_dB',-1,'min'),('passgain_dB',1,'max'),('fit_error_dB',.5,'max'),('atten20M_dB',35,'min'),('bp_peak_dB',-8,'min'),('bp_peak_dB',-5,'max'),('bp_1k_dB',18,'min'),('bp_200k_dB',15,'min'),('bp_20M_dB',15,'min'),('cm_error_V',.01,'max'),('power_W',500e-6,'max')]:g[k+'_'+sense]=gate(ac[k],limit,sense,'dB/V/W',kind='amplitude_db' if k.endswith('_dB') and k!='fit_error_dB' else 'linear')
    n=data(ROOT/groups['noise'],'noise.noise',required=['out']);psd=abs(n['out'])**2;vn=float(np.sqrt(np.trapz(psd,n['freq'])));vals['noise_Vrms']=vn;g['noise_Vrms']=gate(vn,500e-6,'max','Vrms')
    for kind,freq,vpp,lim,m in [('thd',200e3,.6,-45,.85),('thd2',200e3,.9,-30,.8),('thd_f0',2e6,.9,-45,.5)]:
        d=data(ROOT/groups[kind],'tran.tran');q=harmonic(d,freq,vpp);vals[kind]=q;g[kind+'_thd_dB']=gate(q['thd_dB'],lim,'max','dB',kind='amplitude_db');g[kind+'_gain']=gate(q['fundamental_gain'],m,'min','V/V')
        if kind=='thd_f0':
            z=harmonic(d,freq,vpp,'bp');vals['thd_f0_bp']=z;g['thd_f0_bp_thd_dB']=gate(z['thd_dB'],-45,'max','dB',kind='amplitude_db');g['thd_f0_bp_gain']=gate(z['fundamental_gain'],.3,'min','V/V')
    d=data(ROOT/groups['cmstep'],'tran.tran');t=d['time'];cm=[]
    for p,n in [('voutp','voutn'),('vbpp','vbpn')]:
        y=(d[p]+d[n])/2;bad=(t>5.05e-6)&(abs(y-.95)>.01);cm.append(dict(initial_error_V=abs(float(np.interp(4.85e-6,t,y))-.85),settle_s=float(max(t[bad])-5.05e-6) if any(bad) else 0,late_excursion_V=float(max(abs(y[t>=12e-6]-.95)))))
    vals['cmstep']={k:max(x[k] for x in cm) for k in cm[0]}
    for k,lim in [('initial_error_V',.01),('settle_s',1e-6),('late_excursion_V',.01)]:g['cm_'+k]=gate(vals['cmstep'][k],lim,'max','V/s',relax=k=='settle_s')
    bad={k:[w for w in json.loads((ROOT/v/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in w] for k,v in groups.items()};ok &= not any(bad.values())
    return result(CASE,26,vals,g,groups,ok,operating_point=op,disallowed_warnings=bad)

def run(step=2e-9,reltol=1e-6,dec=100,noise_dec=80):
    simulate_groups(26,CASE,{k:bench(k,step,reltol,dec,noise_dec) for k in ['ac','noise','thd','thd2','thd_f0','cmstep']});return extract()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k,d in [('rdeg',19100),('rq',8000),('c1',8),('c2',4),('current',20),('input-gmid',22),('bpratio',1.5)]:p.add_argument('--'+k,type=float,default=d)
    a=p.parse_args();design(**vars(a));update_case(26,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));run()
