"""Nominal28Gb/s CMLTX preserving original fixtures and raw PWL stimuli."""
from __future__ import annotations
import argparse,shutil,importlib.util
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *
from case21_highpsrr_bandgap import quota_guard
CASE=ROOT/'cases/32-cml-tx';TASK=SOURCE/'sky130-cml-tx-driver-28g-nrz-pvt';GROUPS=['static','ac','prbs7','sensitivity'];UI=1/28e9
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region']

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'environment/starter/circuit.spi']+[p for base in ['tests','environment/starter/testbench'] for p in (TASK/base).rglob('*') if p.is_file() and p.suffix in ['.py','.spi','.csv','.md']]
    for p in files:
        d=CASE/'source'/p.relative_to(TASK);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    write_json(CASE/'source_provenance.json',dict(task=str(TASK),captured_at=now(),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='SMIC18TT/1.8V/27C nominal only. Otherpairedss1.62V-40C andff1.98V125C points excluded, not passed.',VDD_V=1.8,temperature_C=27,reference_A=100e-6,pin_order=['vss','vdd','iref','dinp','dinn','voutp','voutn'],input=dict(common_mode_V=1.17,static_symbols_V=[.15,-.15,0],source_resistance_ohm_each=50,pad_cap_F_each=30e-15,source_edge_20_80_s=5e-12),output=dict(termination_ohm_to_VDD_each=50,load_F_each=100e-15),ac=dict(start_Hz=10e6,stop_Hz=50e9,points_per_decade=50,gain_reference_Hz=100e6,peaking_band_Hz=[100e6,22e9],group_delay_band_Hz=[1e9,14e9],phase='physical phase in radians differentiated versus angular frequency; originalPython parser expects degrees and is supplied explicitdegree data'),prbs7=dict(UI_s=UI,period_bits=127,periods=2,stop_s=9071.4286e-12,maxstep_s=.2e-12,symbol_center='original delay-compensated(n+.5)*UI+mean_zero_crossing_offset',measurement_period=2,power='Original raw-sample mean retained; time-weighted mean independently reported and also required to meet power limit'),sensitivity=dict(UIs=12,warmup_UIs=4,differential_Vpp=.2,stop_s=428.5714e-12),allowed_DUT='native SMIC MOS and positive idealR/C/L as original permits; no sources/behavioral logic/ideal switches; no internal50ohm output termination',nonrelaxable=['correctsign every symbol','all expectedtransitions and edge counts','allscalarsfinite','output rail limits','originalsourcefixtureandstimuli'],acceptance_policy=str(ROOT/'contracts/acceptance-policy.md')))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env.update(captured_at=now(),models=model_provenance());write_json(CASE/'environment.json',env)

def design(tail_ma=20,gmid=3,neutral_ff=15,ind_ph=200,ref_gmid=18,in_ph=200):
    roles=dict(pair=lut_size('n18',.18,gmid,100e-6,.9),reference=lut_size('n18',.36,ref_gmid,100e-6,.45));q=roles['pair'];b=roles['reference'];nodes=['dn','dp'] if ind_ph else ['voutn','voutp']
    text=f'''simulator lang=spectre
subckt tx_driver_28g (vss vdd iref dinp dinn voutp voutn)
MREF (iref iref vss vss) n18 w={b['rounded_W_um']:g}u l=.36u m=1
MTAIL (tail iref vss vss) n18 w={b['rounded_W_um']:g}u l=.36u m={tail_ma*10:g}
MPAIRP ({nodes[0]} dinp tail vss) n18 w={q['rounded_W_um']:g}u l=.18u m={tail_ma*5:g}
MPAIRN ({nodes[1]} dinn tail vss) n18 w={q['rounded_W_um']:g}u l=.18u m={tail_ma*5:g}
'''
    if neutral_ff>0:text+=f'CNEUTP ({nodes[1]} dinp) capacitor c={neutral_ff:g}f\nCNEUTN ({nodes[0]} dinn) capacitor c={neutral_ff:g}f\n'
    if ind_ph>0:text+=f'LP (dp voutp) inductor l={ind_ph:g}p\nLN (dn voutn) inductor l={ind_ph:g}p\n'
    if in_ph>0:
        head,body=text.split('\n',2)[0:2],text.split('\n',2)[2]
        body=re.sub(r'\bdinp\b','gip',body);body=re.sub(r'\bdinn\b','gin',body)
        text='\n'.join(head)+'\n'+body+f'LIP (dinp gip) inductor l={in_ph:g}p\nLIN (dinn gin) inductor l={in_ph:g}p\n'
    text+='ends tx_driver_28g\n';(CASE/'circuit.scs').write_text(text)
    write_json(CASE/'sizing.json',dict(generated_at=now(),parameters=dict(tail_ma=tail_ma,gmid=gmid,neutral_ff=neutral_ff,ind_ph=ind_ph,ref_gmid=ref_gmid,in_ph=in_ph),roles=roles,circuit_sha256=sha(CASE/'circuit.scs'),rationale='Direct differential CMLpair, LUTcurrentdensity andtailcurrent set gm and inputcapacitance underfixed50ohmload. LowerpairgmID reduces requiredwidth at fixedgm but increasescurrent andheadroom needs; tailgmID sets overdrive margin. Crossed drains provide positivepolarity. Opposite-drain capacitors target Cgdneutralization. ExternalRs50/Cpad30f/Cload100f alwaysretained; allowed positiveideal input/outputseriesinductors compensate capacitivepoles. No internal50ohm or predriver.'))
    for q in roles.values():(CASE/'lut').mkdir(exist_ok=True);shutil.copy2(q['lut_path'],CASE/'lut'/Path(q['lut_path']).name)

def fixture(tag='',diff=0,ac=False):
    def n(x):return x+tag
    b=f'''VDD{tag} ({n('vdd')} 0) vsource dc=1.8
IREF{tag} ({n('vdd')} {n('iref')}) isource dc=100u
RQP{tag} ({n('voutp')} {n('vdd')}) resistor r=50
RQN{tag} ({n('voutn')} {n('vdd')}) resistor r=50
CQP{tag} ({n('voutp')} 0) capacitor c=100f
CQN{tag} ({n('voutn')} 0) capacitor c=100f
X{tag} (0 {n('vdd')} {n('iref')} {n('dinp')} {n('dinn')} {n('voutp')} {n('voutn')}) tx_driver_28g
save {n('voutp')} {n('voutn')} {n('dinp')} {n('dinn')} {n('iref')} VDD{tag}:p X{tag}.tail
'''
    if tag:
        b+=f'VP{tag} ({n("dinp")} 0) vsource dc={1.17+diff/2:.12g}\nVN{tag} ({n("dinn")} 0) vsource dc={1.17-diff/2:.12g}\n'
        for dev in ['MREF','MTAIL','MPAIRP','MPAIRN']:b+='save '+' '.join(f'X{tag}.{dev}:{k}' for k in OPFIELDS)+'\n'
    else:
        b+='RSP (srcp dinp) resistor r=50\nRSN (srcn dinn) resistor r=50\nCPADP (dinp 0) capacitor c=30f\nCPADN (dinn 0) capacitor c=30f\nsave srcp srcn\n'
        if ac:b+='VP (srcp 0) vsource dc=1.17 mag=.5\nVN (srcn 0) vsource dc=1.17 mag=.5 phase=180\n'
    return b

def bench(group,step_ps=.2,reltol=1e-6):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-9 iabstol=1e-14
saveOptions options save=selected
'''
    if group=='static':return b+''.join(fixture(tag,d) for tag,d in [('one',.15),('zero',-.15),('off',0)])+'dcOp dc\n'
    b+=fixture(ac=group=='ac')
    if group=='ac':return b+'ac ac start=10M stop=50G dec=50\n'
    source=(CASE/'source/tests/benches'/f'tb_{group}.spi').read_text()
    for leg in ['P','N']:
        wave=re.search(r'^VSRC'+leg+r' src\w 0 PWL\(([^)]+)\)',source,re.M)[1]
        b+=f'V{leg} (src{leg.lower()} 0) vsource type=pwl wave=[{wave}]\n'
    stop=9071.4286e-12 if group=='prbs7' else 428.5714e-12
    return b+f'tran tran stop={stop:.14g} maxstep={step_ps:g}p method=gear2only errpreset=conservative\n'

def simulate(groups,step_ps=.2,reltol=1e-6):
    cp=CASE/'circuit.scs';runs={}
    if (CASE/'latest_runs.json').exists():
        for k,p in json.loads((CASE/'latest_runs.json').read_text()).items():
            if sha(ROOT/p/'inputs/circuit.scs')==sha(cp):runs[k]=p
    for group in groups:
        quota_guard();b=bench(group,step_ps,reltol);(CASE/f'testbench_{group}.scs').write_text(b)
        rd=run_spectre(32,group,b,[cp,CASE/'sizing.json',CASE/'contract.json'],timeout=600);runs[group]=str(rd.relative_to(ROOT));write_json(CASE/'latest_runs.json',runs)
    return runs

def upstream():
    p=CASE/'source/tests';sys.path.insert(0,str(p));spec=importlib.util.spec_from_file_location('tx_original',p/'verify.py');up=importlib.util.module_from_spec(spec);spec.loader.exec_module(up);return up

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());up=upstream();v={};extra={};gates={};valid=True
    for p in runs.values():
        m=json.loads((ROOT/p/'run.json').read_text());assert m['status']=='completed' and not m['warnings'] and m['model_dimensions_valid'];assert sha(ROOT/p/'inputs/circuit.scs')==sha(CASE/'circuit.scs')
    if 'static' in runs:
        o=dc(ROOT/runs['static']);s={}
        for tag,code in [('one','1'),('zero','0')]:
            p,n=o['voutp'+tag],o['voutn'+tag];s.update({f'vp{code}':p,f'vn{code}':n,f'vod{code}':p-n,f'vocm{code}':(p+n)/2,f'idd{code}':-o[f'VDD{tag}:p']})
        s['vodoff']=o['voutpoff']-o['voutnoff'];extra['static']=s;v.update(swing_v=s['vod1']-s['vod0'],vocm_drop_max_v=max(1.8-s['vocm1'],1.8-s['vocm0']),vocm_drop_min_v=min(1.8-s['vocm1'],1.8-s['vocm0']),cm_shift_v=abs(s['vocm1']-s['vocm0']),offset_v=abs(s['vodoff']),idd_imbalance_fraction=abs(s['idd1']-s['idd0'])/((s['idd1']+s['idd0'])/2),static_min_v=min(s[k] for k in ['vp1','vn1','vp0','vn0']),static_max_v=max(s[k] for k in ['vp1','vn1','vp0','vn0']))
        valid &= s['vod1']>0>s['vod0'] and min(s['idd1'],s['idd0'])>0
        op={}
        for tag in ['one','zero','off']:
            op[tag]={}
            for dev in ['MREF','MTAIL','MPAIRP','MPAIRN']:
                q={k:o[f'X{tag}.{dev}:{k}'] for k in OPFIELDS};q.update(gmid=abs(q['gm']/q['ids']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[tag][dev]=q
        extra.update(operating_point=op,dc_nodes={k:y for k,y in o.items() if ':' not in k})
    if 'ac' in runs:
        d=data(ROOT/runs['ac'],'ac.ac');f=d['freq'];h=d['voutp']-d['voutn'];a=abs(h);gain=np.interp(100e6,f,a);limit=gain/np.sqrt(2);ix=np.flatnonzero((f[:-1]>=100e6)&(a[:-1]>=limit)&(a[1:]<limit));bw=50e9
        if len(ix):i=ix[0];bw=f[i]+(limit-a[i])*(f[i+1]-f[i])/(a[i+1]-a[i])
        phase=np.unwrap(np.angle(h));gd=-np.diff(phase)/(2*np.pi*np.diff(f));mid=(f[1:]+f[:-1])/2;mask=(mid>=1e9)&(mid<=14e9)
        v.update(gain_100mhz_v=float(gain),bw_hz=float(bw),peaking_db=float(max(20*np.log10(a[(f>=100e6)&(f<=22e9)]/gain))),group_delay_var_s=float(np.ptp(gd[mask])))
        extra['ac_reduction']=dict(bandwidth_lower_bound=not len(ix),group_delay_frequency_Hz=mid.tolist(),group_delay_s=gd.tolist(),phase_unit='radian',gain_reference='source differential1V; includes50ohm/30fF inputfixture')
    if 'prbs7' in runs:
        s=extra['static'];d=data(ROOT/runs['prbs7'],'tran.tran');t=d['time'];csv=ROOT/runs['prbs7']/'original_interface.csv'
        np.savetxt(csv,np.column_stack([t,d['dinp'],t,d['dinn'],t,d['voutp'],t,d['voutn'],t,-d['VDD:p']]),fmt='%.17g')
        row=up.prbs7_analysis.analyze(csv,CASE/'source/tests/benches/prbs7_bits.csv',s['vod1'],s['vod0'],(s['vocm1']+s['vocm0'])/2,1.8);extra['prbs7']=row
        v.update({'prbs_'+k:float(x) for k,x in row.items()})
        i=-d['VDD:p'];start=127*UI;end=t[-1];m=(t>start)&(t<end);tt=np.r_[start,t[m],end];ii=np.interp(tt,t,i);v['time_weighted_power_w']=float(1.8*np.trapz(ii,tt)/(end-start))
        v['overshoot_fraction']=max(row['overshoot_v'],row['undershoot_v'])/v['swing_v'];bits=np.loadtxt(CASE/'source/tests/benches/prbs7_bits.csv')[:,2].astype(int);edges=[n for n in range(128,254) if bits[n]!=bits[n-1]]
        expected_rise=sum(int(bits[n]) for n in edges);expected_fall=len(edges)-expected_rise
        valid &= row['n_transitions']==len(edges) and row['n_rise']==expected_rise and row['n_fall']==expected_fall and row['sign_errors']==0
        extra['prbs_expected_counts']=dict(transitions=len(edges),rise=expected_rise,fall=expected_fall,center_samples=127)
    if 'sensitivity' in runs:
        d=data(ROOT/runs['sensitivity'],'tran.tran');t=d['time'];csv=ROOT/runs['sensitivity']/'original_interface.csv';np.savetxt(csv,np.column_stack([t,d['voutp'],t,d['voutn']]),fmt='%.17g');row=up.sensitivity_analysis.analyze(csv);extra['sensitivity']=row;v.update({'sens_'+k:float(x) for k,x in row.items()});valid &= row['n_samples']==8 and row['n_rise']==4 and row['n_fall']==4 and row['sign_errors']==0
    specs=[('swing_v',.4,'min','V'),('swing_v',.9,'max','V'),('vocm_drop_min_v',.1,'min','V'),('vocm_drop_max_v',.55,'max','V'),('cm_shift_v',.03,'max','V'),('offset_v',.02,'max','V'),('idd_imbalance_fraction',.1,'max','fraction'),('static_min_v',.2,'min','V'),('static_max_v',1.82,'max','V'),('gain_100mhz_v',1.3,'min','V/V'),('gain_100mhz_v',4,'max','V/V'),('bw_hz',22e9,'min','Hz'),('peaking_db',1.5,'max','dB'),('group_delay_var_s',8e-12,'max','s'),('prbs_eye_height_v',.32,'min','V'),('prbs_rise_time_s',15e-12,'max','s'),('prbs_fall_time_s',15e-12,'max','s'),('overshoot_fraction',.12,'max','fraction'),('prbs_vocm_dev_max_v',.05,'max','V'),('prbs_vmin',.2,'min','V'),('prbs_vmax',1.82,'max','V'),('prbs_jitter_pp_s',5e-12,'max','s'),('prbs_jitter_rms_s',1.5e-12,'max','s'),('prbs_dcd_s',2e-12,'max','s'),('prbs_avg_power_w',.045,'max','W'),('time_weighted_power_w',.045,'max','W'),('sens_swing_v',.25,'min','V'),('sens_rise_time_s',17e-12,'max','s'),('sens_fall_time_s',17e-12,'max','s')]
    for k,l,s,u in specs:
        if k in v:
            finite=bool(np.isfinite(v[k]));gates[k+'_'+s]=gate(v[k] if finite else 0,l,s,u,kind='amplitude_db' if k=='peaking_db' else 'linear',relax=k not in ['static_min_v','static_max_v','prbs_vmin','prbs_vmax'])
            if not finite:
                valid=False;gates[k+'_'+s].update(value=None,passes={t:False for t in ['original','10pct','15pct']},failure='Missing finite measurement; original edge thresholds not crossed')
    full=set(runs)==set(GROUPS) and len(gates)==len(specs);tiers={k:bool(full and valid and all(q['passes'][k] for q in gates.values())) for k in ['original','10pct','15pct']};status=next(('complete_'+k for k,z in tiers.items() if z),'needs_iteration' if full else 'partial')
    report=dict(case_slot=32,generated_at=now(),status=status,values=v,gates=gates,pass_tiers=tiers,groups=runs,run_dirs=list(runs.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),all_nominal_checks_complete=full,model_dimensions_valid=True,nonrelaxable_guards_pass=bool(valid),scope=json.loads((CASE/'contract.json').read_text())['scope'],**extra)
    def clean(x):
        if isinstance(x,dict):return {k:clean(y) for k,y in x.items()}
        if isinstance(x,list):return [clean(y) for y in x]
        if isinstance(x,float) and not np.isfinite(x):return None
        return x
    report=clean(report);write_json(CASE/'latest_results.json',report);print(json.dumps(dict(status=status,values=report['values'],failed_original=[k for k,q in gates.items() if not q['passes']['original']],functional=bool(valid)),indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tail-ma',type=float,default=20);p.add_argument('--gmid',type=float,default=3);p.add_argument('--neutral-ff',type=float,default=15);p.add_argument('--ind-ph',type=float,default=200);p.add_argument('--ref-gmid',type=float,default=18);p.add_argument('--in-ph',type=float,default=200);p.add_argument('--run',nargs='+',default=GROUPS);p.add_argument('--step-ps',type=float,default=.2);p.add_argument('--reltol',type=float,default=1e-6);p.add_argument('--extract',action='store_true');a=p.parse_args();quota_guard()
    if a.extract:extract();raise SystemExit(0)
    if not (CASE/'contract.json').exists():freeze()
    design(a.tail_ma,a.gmid,a.neutral_ff,a.ind_ph,a.ref_gmid,a.in_ph);update_case(32,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));simulate(a.run,a.step_ps,a.reltol);extract()
