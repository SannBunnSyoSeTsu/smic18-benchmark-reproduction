"""Native-passive SMIC18 LNA, original forward/reverse50ohm benches."""
from __future__ import annotations
import argparse,shutil
import common
common.SPECTRE='/home/IC/.local/bin/spectre-wsl'
from common import *
from case21_highpsrr_bandgap import quota_guard
CASE=ROOT/'cases/43-inductive-lna';TASK=SOURCE/'sky130-inductive-lna-2p4ghz-gain12-nf2-pvt'
RFLIB=MODEL.parent/'ms018_rf_v1p5_spe.lib';RFIND=MODEL.parent/'ms018_rf_v1p5_spri_ind_spe.ckt'
RFMIM=MODEL.parent/'ms018_rf_v1p5_mim_spe.ckt';RF_FILES=[RFLIB,RFIND,RFMIM]
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region','cgs','cgd']
MOS=['MREF','MNSINK','MPDIO','MPMIR','MCBOT','MCTOP','MIN','MCAS']

def freeze():
    CASE.mkdir(parents=True,exist_ok=True)
    files=[p for p in TASK.rglob('*') if p.is_file() and p.suffix in ['.md','.py','.spi'] and ('tests' in p.parts or 'starter' in p.parts or p==TASK/'instruction.md' or p==TASK/'solution/circuit.spi')]
    for p in files:
        dst=CASE/'source'/p.relative_to(TASK);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    write_json(CASE/'source_provenance.json',dict(task=str(TASK),captured_at=now(),files={str(p.relative_to(TASK)):sha(p) for p in files}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,scope='SMIC18TT1.8V27C nominal. Other26PVT points and public0C diagnostic excluded.',VDD_V=1.8,temperature_C=27,reference_A=50e-6,pin_order=['vss','iref','vdd','rfin','rfout'],external_ports_ohm=50,band_Hz=[2.35e9,2.45e9],band_points=101,stability_Hz=[.1e9,10e9],stability_points_per_decade=200,original_limits=dict(transducer_gain_db_min=12,gain_ripple_db=1.5,s11_db_max=-10,s22_db_max=-10,noise_figure_db=2,reverse_isolation_db_max=-30,stability_k_min=1.2,stability_delta_max=1,power_w=.01,iref_voltage_v=.4,iref_headroom_v=.1),noise='Original noiseless external output50ohm, noisy input50ohm; NF=20log10(max(input_referred_density)/sqrt(4kT50)); all DUTnoise enabled',nonrelaxable=['finite all101bandpoints and401stabilitypoints','K>1 and absDelta<1 strict','bias voltage >=.4V and VDD-iref>=.1V','native physical devices and unmodified models'],relaxation='Transducer gain, ripple and NF are power-ratio dB:10log10(.9/.85 minimum or1.1/1.15 maximum). S11/S22/S12 amplitude dB:20log10(1.1/1.15). K and power linear; stable K>1,Delta<1 and bias compliance never relaxed.',allowed_DUT='native n18/p18 and rpposab_3t, ind_rf, mim1_rf only. No user idealR/C/L or switches. Existing PDKspiral r60um/n3.5 assembled in series/parallel with original fullsubcircuits; mutual coupling not included.'))
    env=json.loads((ROOT/'cases/11-bandgap/environment.json').read_text());env.update(captured_at=now(),models=model_provenance(),rf_model_files={str(p):sha(p) for p in RF_FILES});write_json(CASE/'environment.json',env)

def design(current_ma=3,gmid=14,cas_gmid=10,lg_series=3,ls_parallel=6,ld_series=2,cout_pf=.655,cmatch_pf=1.5874,cin_pf=5.4,damp_l_um=0):
    roles=dict(input=lut_size('n18',.18,gmid,50e-6,.9),cascode=lut_size('n18',.18,cas_gmid,50e-6,.9),pmirror=lut_size('p18',.36,14,50e-6,.9))
    q=roles['input'];c=roles['cascode'];p=roles['pmirror'];m=current_ma*20;rep=m/10
    text=f'''simulator lang=spectre
subckt inductive_lna (vss iref vdd rfin rfout)
MREF (iref iref vss vss) n18 w={q['rounded_W_um']:g}u l=.18u
MNSINK (pgate iref vss vss) n18 w={q['rounded_W_um']:g}u l=.18u m={rep:g}
MPDIO (pgate pgate vdd vdd) p18 w={p['rounded_W_um']:g}u l=.36u m={rep:g}
MPMIR (vcas pgate vdd vdd) p18 w={p['rounded_W_um']:g}u l=.36u m={rep:g}
MCBOT (vbias vbias vss vss) n18 w={c['rounded_W_um']:g}u l=.18u m={rep:g}
MCTOP (vcas vcas vbias vss) n18 w={c['rounded_W_um']:g}u l=.18u m={rep:g}
MIN (nx ng ns vss) n18 w={q['rounded_W_um']:g}u l=.18u m={m:g}
MCAS (nd vcas nx vss) n18 w={c['rounded_W_um']:g}u l=.18u m={m:g}
RBIAS (iref ng vss) rpposab_3t w=1u l=150u
'''
    caps=dict(CIN=('rfin','nin',cin_pf),CBN=('iref','vss',5.4),CBC=('vcas','vss',3.6),COUT=('nd','rfout',cout_pf),CMATCH=('rfout','vss',cmatch_pf))
    for name,(a,b,total) in caps.items():
        count=int(np.ceil(total/.9));area=total*1000/count
        for j in range(count):text+=f'X{name}{j} ({a} {b}) mim1_rf wr=30u lr={area/30:.12g}u\n'
    for name,start,end,count in [('LG','nin','ng',lg_series),('LD','vdd','nd',ld_series)]:
        for j in range(count):
            a=start if j==0 else f'{name.lower()}{j}';b=end if j==count-1 else f'{name.lower()}{j+1}'
            text+=f'X{name}{j} ({a} {b}) ind_rf r=60u n=3.5\n'
    for j in range(ls_parallel):text+=f'XLS{j} (ns vss) ind_rf r=60u n=3.5\n'
    if damp_l_um:text+=f'RDAMP (nd vdd vss) rpposab_3t w=1u l={damp_l_um:g}u\n'
    text+='ends inductive_lna\n';(CASE/'circuit.scs').write_text(text)
    inductance=(-1.7271-.3612*3.5+.2907*3.5**2+.03256*60+.000171*60**2)*1e-9
    resistance=-1.1605+.66174*3.5+.07719*3.5**2+.02008*60+.00011029*60**2
    write_json(CASE/'sizing.json',dict(generated_at=now(),parameters=dict(current_ma=current_ma,gmid=gmid,cas_gmid=cas_gmid,lg_series=lg_series,ls_parallel=ls_parallel,ld_series=ld_series,cout_pf=cout_pf,cmatch_pf=cmatch_pf,cin_pf=cin_pf,damp_l_um=damp_l_um),roles=roles,circuit_sha256=sha(CASE/'circuit.scs'),native_spiral=dict(radius_um=60,turns=3.5,width_um=8,spacing_um=1.5,unit_series_L_H=inductance,unit_series_R_ohm=resistance,gate_series=lg_series,source_parallel=ls_parallel,drain_series=ld_series),native_mim=dict(unit_max_area_um2=900,width_um=30,capacitors={k:dict(nodes=[a,b],target_pF=x,instances=int(np.ceil(x/.9))) for k,(a,b,x) in caps.items()}),rf_model_files={str(p):sha(p) for p in RF_FILES},rationale='InputgmID sets gm/noise/capacitance; sourceL targets gmLs/Cgs near50ohm, gateL resonatesCgs. Cascode and replica stack isolateoutput and preserveheadroom; outputcapacitive transformation matches finiteQdrainload to50ohm. All spirals use documented original r60/n3.5 geometry; no modified equivalent devices.'))
    (CASE/'lut').mkdir(exist_ok=True)
    for q in roles.values():shutil.copy2(q['lut_path'],CASE/'lut'/Path(q['lut_path']).name)

def bench(band_points=101,stability_dec=200,reltol=1e-6):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{MODEL}" section=res_tt
include "{RFLIB}" section=mim_tt
include "{RFIND}"
include "{CASE/'circuit.scs'}"
simulator lang=spectre
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-9 iabstol=1e-14
saveOptions options save=selected
VDDF (vddf 0) vsource dc=1.8
IREFF (vddf ireff) isource dc=50u
VSF (srcf 0) vsource dc=0 mag=1
RSF (srcf rfinf) resistor r=50
RLF (rfoutf 0) resistor r=50 isnoisy=no
XF (0 ireff vddf rfinf rfoutf) inductive_lna
VDDR (vddr 0) vsource dc=1.8
IREFR (vddr irefr) isource dc=50u
VSR (srcr 0) vsource dc=0 mag=1
RSR (srcr rfoutr) resistor r=50
RINR (rfinr 0) resistor r=50
XR (0 irefr vddr rfinr rfoutr) inductive_lna
save vddf ireff rfinf rfoutf rfinr rfoutr VDDF:p XF.ng XF.ns XF.nx XF.nd XF.vcas XF.vbias XF.pgate
'''
    for dev in MOS:b+='save '+' '.join(f'XF.{dev}:{k}' for k in OPFIELDS)+'\n'
    # Spectre lin counts intervals; source ngspice lin counts sampled points.
    return b+f'dcOp dc\nband ac start=2.35G stop=2.45G lin={band_points-1}\nwide ac start=100M stop=10G dec={stability_dec}\nnoise (rfoutf 0) noise iprobe=VSF start=2.35G stop=2.45G lin={band_points-1}\n'

def simulate(band_points=101,stability_dec=200,reltol=1e-6):
    quota_guard();b=bench(band_points,stability_dec,reltol);(CASE/'testbench_rf.scs').write_text(b);rd=run_spectre(43,'rf',b,[CASE/'circuit.scs',CASE/'sizing.json',CASE/'contract.json'],timeout=600)
    write_json(CASE/'latest_runs.json',dict(rf=str(rd.relative_to(ROOT))));return rd

def sp(d):
    return 2*d['rfinf']-1,2*d['rfoutf'],2*d['rfoutr']-1,2*d['rfinr']

def db_gate(value,limit,sense,unit='dB',power=False):
    g=gate(value,limit,sense,unit,kind='amplitude_db')
    if power:
        for tier,loss in [('original',0),('10pct',.1),('15pct',.15)]:
            bound=limit+10*np.log10(1-loss if sense=='min' else 1+loss);g['limits'][tier]=float(bound);g['passes'][tier]=bool(value>=bound if sense=='min' else value<=bound)
    return g

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());rd=ROOT/runs['rf'];m=json.loads((rd/'run.json').read_text());assert m['status']=='completed' and not m['warnings'] and m['model_dimensions_valid'];assert sha(rd/'inputs/circuit.scs')==sha(CASE/'circuit.scs')
    d=data(rd,'band.ac');s11,s21,s22,s12=sp(d);db=lambda z:20*np.log10(abs(z));gain=db(s21);v=dict(transducer_gain_db_min=float(min(gain)),transducer_gain_db_max=float(max(gain)),gain_ripple_db=float(np.ptp(gain)),s11_db_max=float(max(db(s11))),s22_db_max=float(max(db(s22))),reverse_isolation_db_max=float(max(db(s12))))
    w=data(rd,'wide.ac');a,b,c,e=sp(w);delta=a*c-e*b;k=(1-abs(a)**2-abs(c)**2+abs(delta)**2)/(2*abs(e*b));v.update(stability_k_min=float(min(k)),stability_delta_max=float(max(abs(delta))))
    no=data(rd,'noise.noise',required=['in','out']);source=np.sqrt(4*1.380649e-23*300.15*50);density=float(max(abs(no['in'])));v.update(noise_figure_db=float(20*np.log10(density/source)),input_noise_density_max_vrthz=density)
    o=dc(rd);v.update(power_w=-o['vddf']*o['VDDF:p'],iref_voltage_v=o['ireff'],iref_headroom_v=o['vddf']-o['ireff'])
    g={}
    for key,limit,sense,power in [('transducer_gain_db_min',12,'min',True),('gain_ripple_db',1.5,'max',True),('s11_db_max',-10,'max',False),('s22_db_max',-10,'max',False),('noise_figure_db',2,'max',True),('reverse_isolation_db_max',-30,'max',False)]:g[key]=db_gate(v[key],limit,sense,power=power)
    for key,limit,sense,unit,relax in [('stability_k_min',1.2,'min','ratio',True),('stability_delta_max',1,'max','ratio',False),('power_w',.01,'max','W',True),('iref_voltage_v',.4,'min','V',False),('iref_headroom_v',.1,'min','V',False)]:g[key]=gate(v[key],limit,sense,unit,relax=relax)
    g['stability_delta_max']['passes']={t:bool(v['stability_delta_max']<1) for t in ['original','10pct','15pct']}
    valid=bool(np.all(np.isfinite(k)) and v['stability_k_min']>1 and v['stability_delta_max']<1 and v['power_w']>0 and v['iref_voltage_v']>=.4 and v['iref_headroom_v']>=.1)
    assert len(d['freq'])>=101 and len(w['freq'])>=401 and len(no['freq'])==len(d['freq'])
    tiers={t:bool(valid and all(q['passes'][t] for q in g.values())) for t in ['original','10pct','15pct']};status=next(('complete_'+t for t,x in tiers.items() if x),'needs_iteration');op={}
    for dev in MOS:
        q={k:o[f'XF.{dev}:{k}'] for k in OPFIELDS};q.update(gmid=abs(q['gm']/q['ids']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[dev]=q
    r=dict(case_slot=43,generated_at=now(),status=status,values=v,gates=g,pass_tiers=tiers,groups=runs,run_dirs=list(runs.values()),circuit_sha256=sha(CASE/'circuit.scs'),contract_sha256=sha(CASE/'contract.json'),all_nominal_checks_complete=True,model_dimensions_valid=True,nonrelaxable_guards_pass=valid,scope=json.loads((CASE/'contract.json').read_text())['scope'],operating_point=op,dc_nodes={k:y for k,y in o.items() if ':' not in k},measurement_points=dict(band=len(d['freq']),stability=len(w['freq']),noise=len(no['freq'])),worst_frequency_Hz=dict(K=float(w['freq'][np.argmin(k)]),delta=float(w['freq'][np.argmax(abs(delta))]),NF=float(no['freq'][np.argmax(abs(no['in']))])),rf_model_hashes={str(p):sha(p) for p in RF_FILES})
    write_json(CASE/'latest_results.json',r);print(json.dumps(dict(status=status,values=v,failed=[k for k,q in g.items() if not q['passes']['15pct']],functional=valid),indent=2));return r

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key,default in [('current-ma',3),('gmid',14),('cas-gmid',10),('cout-pf',.655),('cmatch-pf',1.5874),('cin-pf',5.4),('damp-l-um',0)]:p.add_argument('--'+key,type=float,default=default)
    for key,default in [('lg-series',3),('ls-parallel',6),('ld-series',2)]:p.add_argument('--'+key,type=int,default=default)
    p.add_argument('--extract',action='store_true');a=p.parse_args();quota_guard()
    if a.extract:extract();raise SystemExit(0)
    if not (CASE/'contract.json').exists():freeze()
    design(**{k:v for k,v in vars(a).items() if k!='extract'});update_case(43,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));simulate();extract()
