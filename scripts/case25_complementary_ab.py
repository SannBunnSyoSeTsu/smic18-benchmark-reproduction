"""SMIC18 complementary-input folded-cascode floating-bias Class-AB op amp."""
from common import *
import argparse

CASE=ROOT/'cases/25-complementary-ab'
TASK=SOURCE/'sky130-complementary-folded-cascode-ab-opamp-pvt'
SUB='complementary_folded_cascode_ab_opamp'
CMS=[.1,.2,.9,1.6,1.7]
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat']

def design(tail=40,fold=40,out=200,cc=12,rz=1000,cgate=.5,ingmid=22,inL=1,abgmid=14,abL=1,rsn=500,rsp=300,cmcap=4,cmres=15000,nshift=.23,pshift=.23,steerN=.62,steerP=.62):
    CASE.mkdir(parents=True,exist_ok=True)
    sources={}
    for name in ['instruction.md','solution/circuit.spi','tests/verify.py','tests/utils.py']+[str(x.relative_to(TASK)) for x in (TASK/'tests/benches').glob('*.spi')]:
        src=TASK/name;dst=CASE/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():dst.write_bytes(src.read_bytes())
        assert sha(src)==sha(dst);sources[name]=dict(path=str(src),sha256=sha(src),frozen=str(dst.relative_to(ROOT)))
    roles={
      'nbias':lut_size('n18',4,14,5e-6,.9),'pbias':lut_size('p18',4,14,5e-6,.9),
      'nin':lut_size('n18',inL,ingmid,5e-6,.45),'pin':lut_size('p18',inL,ingmid,5e-6,.45),
      'nswitch':lut_size('n18',inL,ingmid,5e-6,.45),'pswitch':lut_size('p18',inL,ingmid,5e-6,.45),
      'ncas':lut_size('n18',1,14,10e-6,.45),'pcas':lut_size('p18',1,14,10e-6,.45),
      'pmirror':lut_size('p18',4,10,10e-6,.9),
      'nab':lut_size('n18',abL,abgmid,10e-6,.9 if abL==4 else .45),'pab':lut_size('p18',abL,abgmid,10e-6,.9 if abL==4 else .45),
      'nout':lut_size('n18',1,14,10e-6,.45),'pout':lut_size('p18',1,14,10e-6,.45),
      'nref':lut_size('n18',1,10,10e-6,.45),'pref':lut_size('p18',1,10,10e-6,.45)}
    # The steering reference is a MOS diode plus a positive source resistor.
    nrefR=max(0,(steerN-roles['nref']['Vgs_V'])/10e-6)
    prefR=max(0,(steerP-roles['pref']['Vgs_V'])/10e-6)
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    lines=['// SMIC18 TT: complementary input, constant-sum tail steering, folded summing, floating Class-AB.', 'simulator lang=spectre',f'subckt {SUB} (vss iref vdd vinn vinp vout)']
    devs=[]
    def M(name,nodes,role,m=1):
        r=roles[role];model=r['model'];L=r['L_um'];W=r['rounded_W_um']
        assert .19<=W<=100 and m>0
        lines.append(f'{name} ({nodes}) {model} w={W:g}u l={L:g}u m={m:g}')
        devs.append(dict(name=name,pins=nodes.split(),model=model,W_unit_um=W,L_um=L,m=m,W_total_um=W*m,role=role))
    def R(name,nodes,value):lines.append(f'{name} ({nodes}) resistor r={value:g}')
    def C(name,nodes,pF):lines.append(f'{name} ({nodes}) capacitor c={pF:g}p')
    M('MREF','iref iref vss vss','nbias',4)
    M('MBN','vbp iref vss vss','nbias',2);M('MBP','vbp vbp vdd vdd','pbias',2)
    M('MNCB','vcn vbp vdd vdd','pbias',2);M('MND','vcn vcn ncb vss','ncas');R('RNC','ncb vss',nshift/10e-6)
    M('MPCB','vcp iref vss vss','nbias',2);M('MPD','vcp vcp pcb vdd','pcas');R('RPC','vdd pcb',pshift/10e-6)
    M('MNRB','vrefn vbp vdd vdd','pbias',2);M('MNREF','vrefn vrefn nrefsrc vss','nref');R('RNR','nrefsrc vss',max(nrefR,.001))
    M('MPRB','vrefp iref vss vss','nbias',2);M('MPREF','vrefp vrefp prefsrc vdd','pref');R('RPR','vdd prefsrc',max(prefR,.001))
    M('MNT','ntail iref vss vss','nbias',tail/5);M('MPT','ptail vbp vdd vdd','pbias',tail/5)
    M('MNINN','fp1 vinn ntn vss','nin',tail/10);M('MNINP','fp2 vinp ntp vss','nin',tail/10)
    R('RINN','ntn ntail',rsn);R('RINP','ntp ntail',rsn)
    M('MPINN','fn1 vinn ptn ptail','pin',tail/10);M('MPINP','fn2 vinp ptp ptail','pin',tail/10)
    R('RIPN','ptail ptn',rsp);R('RIPP','ptail ptp',rsp)
    M('MNSW','swnd vrefn ntail vss','nswitch',tail/5)
    M('MPSD','swnd swnd vdd vdd','pbias',tail/5);M('MPSM','ptail swnd vdd vdd','pbias',tail/5)
    M('MPSW','swpd vrefp ptail ptail','pswitch',tail/5)
    M('MNSD','swpd swpd vss vss','nbias',tail/5);M('MNSM','ntail swpd vss vss','nbias',tail/5)
    M('MFBASE','vbsink vbp vdd vdd','pbias',(fold+tail/2)/5)
    M('MFADD','vbsink swnd vdd vdd','pbias',tail/10);M('MFSUB','vbsink swpd vss vss','nbias',tail/10)
    M('MFREF','vbsink vbsink vss vss','nbias',(fold+tail/2)/5)
    M('MFS1','fn1 vbsink vss vss','nbias',(fold+tail/2)/5);M('MFS2','fn2 vbsink vss vss','nbias',(fold+tail/2)/5)
    M('MNC1','ml vcn fn1 vss','ncas',fold/10);M('MNC2','gn vcn fn2 vss','ncas',fold/10)
    M('MPM1','fp1 ml vdd vdd','pmirror',(fold+tail/2)/10);M('MPM2','fp2 ml vdd vdd','pmirror',(fold+tail/2)/10)
    M('MPC1','ml vcp fp1 vdd','pcas',fold/10);M('MPC2','gp vcp fp2 vdd','pcas',fold/10)
    M('MABN','gp vabn gn vss','nab',fold/20);M('MABP','gn vabp gp vdd','pab',fold/20)
    M('MABNS','vabn vbp vdd vdd','pbias',2);M('MABNU','vabn vabn xn vss','nab');M('MABNL','xn xn vss vss','nout')
    M('MABPS','vabp iref vss vss','nbias',2);M('MABPU','vabp vabp yp vdd','pab');M('MABPL','yp yp vdd vdd','pout')
    M('MOUTN','vout gn vss vss','nout',out/10);M('MOUTP','vout gp vdd vdd','pout',out/10)
    C('CGN','gn vss',cgate);C('CGP','gp vdd',cgate)
    R('RCM1','vinn cmin',cmres);R('RCM2','vinp cmip',cmres);C('CCM1','cmin ntail',cmcap);C('CCM2','cmip ntail',cmcap)
    C('CCP','vout zp',cc);R('RZP','zp fp2',rz);C('CCN','vout zn',cc);R('RZN','zn fn2',rz)
    lines.append(f'ends {SUB}');c=CASE/'circuit.scs';c.write_text('\n'.join(lines)+'\n')
    write_json(CASE/'geometry.json',dict(circuit_sha256=sha(c),devices=devs,all_unit_widths_valid=True,HD_logic='none: continuously biased analog signal and bias paths'))
    params={k:v for k,v in locals().items() if k in ['tail','fold','out','cc','rz','cgate','ingmid','inL','abgmid','abL','rsn','rsp','cmcap','cmres','nshift','pshift','steerN','steerP']}
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,parameters=params,rationale='Complementary pairs each40uA tail, gm/ID22 initial; 1:1 tail transfer keeps sum80uA. Fold sink60uA+0.5SN-0.5SP gives constant40uA cascode/AB current. Matched floating-device and upper bias-stack current densities, lower stack matches output devices. Output200uA initial; source-degeneration and symmetric folded-node seriesRC compensation. All MOS sizes are target-PDK LUT values with legal unit widths.'))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_files=sources,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=20e-6,load_F=4e-12,closed_loop_load_ohm=10000,nominal_only=True,
      ac=dict(common_modes_V=CMS,output_DC_V=.9,load_return_ohm=1e12,core_gain_min_dB=90,edge_gain_min_dB=80,ugb_min_Hz=1e6,core_PM_min_deg=60,edge_PM_min_deg=55,ugb_max_min_max=2,frequency_Hz=[1,1e9],source_dec=20,implementation_dec=100),
      tracking=dict(sweep_V=[0,1.8],step_V=.005,core_V=[.2,1.6],core_error_max_V=.005,band_V=[.1,1.7],band_error_max_V=.02,icmr_fixed_error_V=.02,min_span_V=1.5,max_rail_headroom_V=.1,power_max_W=.0015),
      step=dict(command_V=[.2,1.6],edges_s=[1e-6,1.01e-6,3e-6,3.01e-6],stop_s=5e-6,threshold_V=[.48,1.32],min_slew_V_per_us=2,tail_windows_s=[[2.9e-6,3e-6],[4.9e-6,5e-6]],tail_error_max_V=.005),
      noise=dict(common_mode_V=.9,band_Hz=[10,1e6],max_Vrms=70e-6,source_topology='DC LFB closes; AC CFB grounds negative input; use input-referred noise with original4pF//10kohm load'),
      rejection=dict(common_mode_V=.9,CMRR_min_dB={'1kHz':70,'1MHz':55},PSRR_min_dB={'10Hz':45,'1MHz':10},source_return_ohm=100e6),
      thd=dict(frequency_Hz=1000,amplitude_Vpk=.4,offset_V=.9,stop_s=.005,Fourier_final_period_s=[.004,.005],residual_window_s=[.0035,.005],THD_max_percent=.01,residual_max_fraction=.005),
      exclusions=['other24PVT points','two nonnominal representative rejection/distortion points','three tt_mm seed offsets','PEX/passive/mismatch yield'],relaxation='project acceptance-policy; all stimuli and functional dimensions fixed'))
    return c

def header(c):return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
'''

def acbench(c):
    b=header(c)
    for i,cm in enumerate(CMS):
        b+=f'''VDD{i} (vdd{i} 0) vsource dc=1.8
IR{i} (vdd{i} iref{i}) isource dc=20u
VIN{i} (vinp{i} 0) vsource dc={cm:g}
LFB{i} (out{i} fb{i}) inductor l=1e15
SHIFT{i} (vinn{i} fb{i}) vsource dc={cm-.9:g}
CFB{i} (vinn{i} vac{i}) capacitor c=1e6
VAC{i} (vac{i} 0) vsource dc=0 mag=1
VMID{i} (mid{i} 0) vsource dc=.9
RDC{i} (out{i} mid{i}) resistor r=1e12
CL{i} (out{i} 0) capacitor c=4p
X{i} (0 iref{i} vdd{i} vinn{i} vinp{i} out{i}) {SUB}
save out{i} vinn{i} vinp{i} VDD{i}:p
'''
        for n in ['iref','vbp','vcn','vcp','vrefn','vrefp','ntail','ptail','swnd','swpd','fp1','fp2','fn1','fn2','ml','gn','gp','vabn','vabp','xn','yp','vbsink']:
            if n=='iref':b+=f'save iref{i}\n'
            else:b+=f'save X{i}.{n}\n'
        for q in json.loads((CASE/'geometry.json').read_text())['devices']:b+='save '+' '.join(f'X{i}.{q["name"]}:{p}' for p in OPFIELDS)+'\n'
    return b+'dcOp dc\nac ac start=1 stop=1G dec=100\n'

def loaded(c):return header(c)+f'''VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=20u
VMID (mid 0) vsource dc=.9
RL (vout mid) resistor r=10k
CL (vout 0) capacitor c=4p
X (0 iref vdd vinn vinp vout) {SUB}
save vinp vinn vout VDD:p X.gn X.gp X.ntail X.ptail
'''

def trackbench(c):return loaded(c)+'''parameters command=.9
VIN (vinp 0) vsource dc=command
RFB (vout vinn) resistor r=.001
dcOp dc
track dc param=command start=0 stop=1.8 step=.005
'''

def noisebench(c):return loaded(c)+'''VIN (vinp 0) vsource dc=.9 mag=1
LFB (vout vinn) inductor l=1e15
CFB (vinn vac) capacitor c=1e6
VAC (vac 0) vsource dc=0
noise (vout 0) noise iprobe=VIN start=10 stop=1M dec=100
'''

def stepbench(c):return loaded(c)+'''VIN (vinp 0) vsource type=pwl wave=[0 .2 1u .2 1.01u 1.6 3u 1.6 3.01u .2 5u .2]
RFB (vout vinn) resistor r=.001
save X.MOUTN:ids X.MOUTP:ids
tran tran stop=5u maxstep=.5n strobeperiod=1n strobeoutput=strobeonly errpreset=conservative
'''

def thdbench(c):return loaded(c)+'''VIN (vinp 0) vsource type=sine dc=.9 ampl=.4 freq=1k
RFB (vout vinn) resistor r=.001
tran tran stop=5m maxstep=50n strobeperiod=250n strobeoutput=strobeonly errpreset=conservative
'''

def rejectbench(c):
    b=header(c)
    for tag,pa,na,va in [('D',.5,-.5,0),('C',1,1,0),('P',0,0,1)]:
        b+=f'''VDD{tag} (vdd{tag} 0) vsource dc=1.8 mag={va:g}
IR{tag} (vdd{tag} iref{tag}) isource dc=20u
VP{tag} (vp{tag} 0) vsource dc=.9 mag={abs(pa):g}
VN{tag} (vn{tag} 0) vsource dc=.9 mag={abs(na):g} phase={180 if na<0 else 0}
X{tag} (0 iref{tag} vdd{tag} vn{tag} vp{tag} out{tag}) {SUB}
LF{tag} (out{tag} vn{tag}) inductor l=1e15
RB{tag} (out{tag} 0) resistor r=100M
CL{tag} (out{tag} 0) capacitor c=4p
save out{tag} vp{tag} vn{tag}
'''
    return b+'ac ac start=10 stop=100M dec=100\n'

def verify_stb():
    """Direct level-shifted feedback; original AC4pF/1Tohm load, five VCMs."""
    c=CASE/'circuit.scs';b=acbench(c)
    for i in range(5):
        b=b.replace(f'LFB{i} (out{i} fb{i}) inductor l=1e15',f'PLOOP{i} (out{i} fb{i}) iprobe')
        b=b.replace(f'CFB{i} (vinn{i} vac{i}) capacitor c=1e6\n','').replace(f'VAC{i} (vac{i} 0) vsource dc=0 mag=1\n','')
    b=b.replace('ac ac start=1 stop=1G dec=100\n',''.join(f'stb{i} stb start=1 stop=1G dec=100 probe=PLOOP{i}\n' for i in range(5)))
    rd=run_spectre(25,'stb',b,[c,CASE/'sizing.json',CASE/'geometry.json',CASE/'contract.json',Path(__file__)])
    rows=[]
    for i,cm in enumerate(CMS):
        d=data(rd,f'stb{i}.stb');h=-d['loopGain'];m=loop_metrics(d['freq'],h,10);db=20*np.log10(abs(h));ii=np.flatnonzero(db<0)
        m.update(cm_V=cm,recross=bool(not len(ii) or np.any(db[ii[0]:]>=0)));rows.append(m)
    r=dict(run_dir=str(rd.relative_to(ROOT)),rows=rows,all_pass_45deg=all(x['phase_margin_deg']>=45 and x['falling_crossings']==1 and not x['recross'] for x in rows),definition='Native Spectre STB probe in closed direct level-shifted unity feedback; original4pF and1Tohm ACload; no ACgrounding capacitor or infinite inductor.')
    write_json(rd/'measurements.json',r);write_json(CASE/'stb_diagnostic.json',r);print(json.dumps(r,indent=2));return r

def win(t,y,a,b):
    mask=(t>a)&(t<b);return np.r_[a,t[mask],b],np.r_[np.interp(a,t,y),y[mask],np.interp(b,t,y)]

def cross(t,y,v,start,rising=True):
    ix=np.flatnonzero((t[:-1]>=start)&((y[:-1]<v)&(y[1:]>=v) if rising else (y[:-1]>v)&(y[1:]<=v)))
    if not len(ix):return None
    k=ix[0];return float(t[k]+(v-y[k])/(y[k+1]-y[k])*(t[k+1]-t[k]))

def extract(runs):
    vals={};gates={};extra={};valid=True
    def g(k,v,lim,sense,unit,kind='linear',relax=True):vals[k]=float(v);gates[k]=gate(v,lim,sense,unit,kind,relax)
    if 'ac' in runs:
        d=data(runs['ac'],'ac.ac');o=dc(runs['ac']);rows=[]
        for i,cm in enumerate(CMS):
            h=-d[f'out{i}']/d[f'vinn{i}'];m=loop_metrics(d['freq'],h,10);db=20*np.log10(abs(h));ix=np.flatnonzero(db<0);recross=bool(not len(ix) or np.any(db[ix[0]:]>=0));edge=i in [0,4]
            g(f'gain_{i}_dB',m['gain_db'],80 if edge else 90,'min','dB','amplitude_db');g(f'ugb_{i}_Hz',m['ugb_hz'],1e6,'min','Hz');g(f'pm_{i}_deg',m['phase_margin_deg'],55 if edge else 60,'min','deg','phase_margin')
            power=-1.8*o[f'VDD{i}:p'];g(f'ac_power_{i}_W',power,.0015,'max','W');valid &= power>0 and m['falling_crossings']==1 and not recross
            op={}
            for q in json.loads((CASE/'geometry.json').read_text())['devices']:
                name=q['name'];q1={k:o[f'X{i}.{name}:{k}'] for k in OPFIELDS};q1.update(gmid=abs(q1['gm']/q1['ids']) if q1['ids'] else None,headroom_V=abs(q1['vds'])-abs(q1['vdsat']));op[name]=q1
            rows.append(dict(cm_V=cm,output_DC_V=o[f'out{i}'],input_offset_V=o[f'vinn{i}']-cm,metrics=m,power_W=power,recross=recross,operating_points=op,nodes={k:v for k,v in o.items() if k.startswith(f'X{i}.') and ':' not in k}))
        u=[r['metrics']['ugb_hz'] for r in rows];g('ugb_ratio',max(u)/min(u),2,'max','ratio');extra['ac_rows']=rows
    if 'track' in runs:
        d=data(runs['track'],'track.dc');x=d['vinp'];y=d['vout'];e=abs(y-x)
        for label,lo,hi,lim in [('core',.2,1.6,.005),('band',.1,1.7,.02)]:g('tracking_'+label+'_error_V',max(e[(x>=lo-1e-9)&(x<=hi+1e-9)]),lim,'max','V')
        g('tracking_power_W',max(-1.8*d['VDD:p']),.0015,'max','W');valid &= min(-1.8*d['VDD:p'])>=0
        # Fixed20mV ICMR eligibility; crossing interpolation, no relaxed redefinition.
        ok=e<=.02;ii=np.flatnonzero(ok);lo=x[ii[0]];hi=x[ii[-1]];last=min(ii[-1],len(x)-2)
        if ii[0]>0:
            j=ii[0]-1;lo=x[j]+(.02-e[j])*(x[j+1]-x[j])/(e[j+1]-e[j])
        if ii[-1]<len(x)-1:
            j=ii[-1];hi=x[j]+(.02-e[j])*(x[j+1]-x[j])/(e[j+1]-e[j])
        else:hi=1.795 # Match published endpoint scope.
        valid &= bool(np.all(ok[ii[0]:last+1]))
        g('icmr_low_headroom_V',lo,.1,'max','V');g('icmr_high_headroom_V',1.8-hi,.1,'max','V');g('icmr_span_V',hi-lo,1.5,'min','V')
        vals['matched_offset_V']=float(np.interp(.9,x,y)-.9);extra['track_points']=len(x)
    if 'noise' in runs:
        d=data(runs['noise'],'noise.noise',required=('in','out'));g('noise_Vrms',np.sqrt(np.trapz(abs(d['in'])**2,d['freq'])),70e-6,'max','Vrms')
    if 'reject' in runs:
        d=data(runs['reject'],'ac.ac');f=d['freq'];cm=20*np.log10(abs(d['outD']/d['outC']));ps=20*np.log10(abs(d['outD']/d['outP']))
        for k,v,lim in [('CMRR_1k_dB',at(f,cm,1e3),70),('CMRR_1M_dB',at(f,cm,1e6),55),('PSRR_10Hz_dB',at(f,ps,10),45),('PSRR_1M_dB',at(f,ps,1e6),10)]:g(k,v,lim,'min','dB','amplitude_db')
    if 'step' in runs:
        d=data(runs['step'],'tran.tran');t=d['time'];y=d['vout'];r20=cross(t,y,.48,1e-6);r80=cross(t,y,1.32,1e-6);f80=cross(t,y,1.32,3e-6,False);f20=cross(t,y,.48,3e-6,False)
        if None in [r20,r80,f80,f20]:valid=False;extra['step_missing_crossing']=True
        else:g('slew_up_Vus',.84/(r80-r20)/1e6,2,'min','V/us');g('slew_down_Vus',.84/(f20-f80)/1e6,2,'min','V/us')
        er=max(max(abs(win(t,y,2.9e-6,3e-6)[1]-1.6)),max(abs(win(t,y,4.9e-6,5e-6)[1]-.2)));g('settle_tail_error_V',er,.005,'max','V')
        extra['output_drive_peak_A']={k:float(max(abs(d[k]))) for k in ['X.MOUTN:ids','X.MOUTP:ids']}
    if 'thd' in runs:
        d=data(runs['thd'],'tran.tran');t=d['time'];y=d['vout'];tt=np.arange(4000)*250e-9+.004;yy=np.interp(tt,t,y);ang=2*np.pi*1000*(tt-.004)
        mat=np.column_stack([np.ones(len(tt))]+[fun(k*ang) for k in range(1,10) for fun in [np.sin,np.cos]])
        coef=np.linalg.lstsq(mat,yy,rcond=None)[0];amps=np.hypot(coef[1::2],coef[2::2]);thd=100*np.linalg.norm(amps[1:])/amps[0]
        g('THD_percent',thd,.01,'max','%');g('THD_residual_fraction',max(win(t,abs(y-d['vinp']),.0035,.005)[1])/.4,.005,'max','fraction')
        extra['fourier']=dict(window_s=[.004,.005],samples=4000,harmonic_amplitudes_V=amps.tolist(),fundamental_gain=amps[0]/.4,definition='DC plus harmonics1..9 least-squares on coherent final1ms; THDpercent100sqrt(sum(h2..h9^2))/h1')
    complete=set(runs)=={'ac','track','noise','reject','step','thd'}
    diagnostic_runs=[]
    if (CASE/'stb_diagnostic.json').exists():
        stb=json.loads((CASE/'stb_diagnostic.json').read_text());rd=ROOT/stb['run_dir']
        if sha(rd/'inputs/circuit.scs')==sha(CASE/'circuit.scs'):
            extra['native_stb']=stb;diagnostic_runs.append(stb['run_dir'])
            assert stb['all_pass_45deg']
    allruns=[str(x.relative_to(ROOT)) for x in runs.values()]+diagnostic_runs
    metas=[json.loads((ROOT/x/'run.json').read_text()) for x in allruns]
    model_valid=all(x['model_dimensions_valid'] for x in metas)
    same_circuit=all(sha(ROOT/x/'inputs/circuit.scs')==sha(CASE/'circuit.scs') for x in allruns)
    valid &= model_valid and same_circuit and all(x['status']=='completed' for x in metas)
    tiers={k:bool(complete and valid and all(q['passes'][k] for q in gates.values())) for k in ['original','10pct','15pct']};tier=next((k for k,v in tiers.items() if v),None)
    result=dict(case_slot=25,generated_at=now(),status='complete_'+tier if tier else 'partial',nominal_complete=bool(tier),all_nominal_checks_complete=complete,functional_checks_pass=bool(valid),model_dimensions_valid=model_valid,all_runs_same_circuit=same_circuit,values=vals,gates=gates,pass_tiers=tiers,run_dirs=allruns,groups={k:str(x.relative_to(ROOT)) for k,x in runs.items()},extraction_script_sha256=sha(__file__),**extra)
    write_json(CASE/'latest_results.json',result);update_case(25,status=result['status'],nominal_complete=bool(tier),report=str((CASE/'latest_results.json').relative_to(ROOT)),case_dir=str(CASE.relative_to(ROOT)))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('--reuse',action='store_true');p.add_argument('--groups',default='ac,track');p.add_argument('--extract',action='store_true');p.add_argument('--stb',action='store_true')
    for n,v in dict(tail=40,fold=40,out=200,cc=12,rz=1000,cgate=.5,ingmid=22,inL=1,abgmid=14,abL=1,rsn=500,rsp=300,cmcap=4,cmres=15000,nshift=.23,pshift=.23,steerN=.62,steerP=.62).items():p.add_argument('--'+n,type=float,default=v)
    a=p.parse_args();cache=CASE/'working_runs.json'
    if a.stb:verify_stb();return
    if a.extract:runs={k:ROOT/v for k,v in json.loads(cache.read_text()).items()}
    else:
        opts=vars(a).copy();[opts.pop(k) for k in ['full','reuse','groups','extract','stb']]
        c=CASE/'circuit.scs' if a.reuse else design(**opts);runs={}
        if a.reuse and cache.exists():
            for k,v in json.loads(cache.read_text()).items():
                rd=ROOT/v
                if sha(rd/'inputs/circuit.scs')==sha(c):runs[k]=rd
        names=['ac','track','noise','reject','step','thd'] if a.full else a.groups.split(',')
        funcs=dict(ac=acbench,track=trackbench,noise=noisebench,reject=rejectbench,step=stepbench,thd=thdbench)
        update_case(25,status='running',nominal_complete=False)
        for name in names:
            b=funcs[name](c);(CASE/f'testbench_{name}.scs').write_text(b)
            runs[name]=run_spectre(25,name,b,[c,CASE/'sizing.json',CASE/'geometry.json',CASE/'contract.json'],timeout=1200)
            write_json(cache,{k:str(v.relative_to(ROOT)) for k,v in runs.items()})
    r=extract(runs);print(json.dumps({k:r[k] for k in ['status','values','pass_tiers']},indent=2))

if __name__=='__main__':main()
