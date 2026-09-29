"""Native-RF-passive2GHz VCO; exact four-plateau nominal and supply-pushing tests."""
from common import *
import argparse
import shutil

CASE=ROOT/'cases/49-lc-vco';TASK=SOURCE/'sky130-lc-vco-2ghz-pvt'
RFDIR=MODEL.parent;RFLIB=RFDIR/'ms018_rf_v1p5_spe.lib'
RFVAR=RFDIR/'ms018_rf_v1p5_var_spe.ckt';RFIND=RFDIR/'ms018_rf_v1p5_spri_ind_spe.ckt'
RF_FILES=[RFLIB,RFVAR,RFIND]+[RFDIR/q for q in sorted(set(re.findall(r'^include "([^"]+)"',RFLIB.read_text(),re.M)))]
WINDOWS=[(20e-9,39e-9),(60e-9,79e-9),(100e-9,119e-9),(140e-9,159e-9)]
CONTROLS=[0,.6,1.2,1.8]


def design(cap_area=600,var_nf=20,feed_m=16,core_gmid=12,bias_gmid=20,ind_r=60,ind_n=3.5,coupling_units=3,var_units=2,varbias_gmid=7.3,pulldown_m=4):
    CASE.mkdir(parents=True,exist_ok=True);records=[]
    files=['instruction.md','tests/verify.py','tests/benches/tb_tune.spi','solution/circuit.spi','results/reference.json',
      'environment/starter/SKY130_NETLIST_GUIDE.md','environment/starter/testbench/tb_tune_tt_1p8v_27c.spi',
      'environment/starter/testbench/tb_supply_pushing_tt_1p62v_27c.spi','environment/starter/testbench/tb_supply_pushing_tt_1p98v_27c.spi',
      'environment/starter/testbench/check_supply_pushing_benches.py']
    for rel in files:
        src=TASK/rel;dst=CASE/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():shutil.copyfile(src,dst)
        assert sha(src)==sha(dst);records.append(dict(original=str(src),frozen=str(dst.relative_to(ROOT)),sha256=sha(src)))
    write_json(CASE/'source_provenance.json',dict(source_task=TASK.name,files=records))
    roles={'negative_resistance':lut_size('n18',.18,core_gmid,feed_m*50e-6/2,.45),'bias_unit':lut_size('p18',.18,bias_gmid,12.5e-6,.45)}
    target_vgs=roles['bias_unit']['Vgs_V'];long_table=GmIdTable('p18',W=10,L=1,vds=.45,corner='tt')
    matched_gmid=float(min(np.linspace(4,20,1601),key=lambda g:abs(long_table.lookup('vgs',float(g))-target_vgs)))
    roles['var_feed']=lut_size('p18',1,matched_gmid,12.5e-6,.45)
    roles['varactor_bias']=lut_size('n18',1,varbias_gmid,50e-6,.45)
    roles.update(reg_input=lut_size('n18',.36,15,25e-6,.45),reg_load=lut_size('p18',1,15,25e-6,.45),
      reg_pullup=lut_size('p18',.18,12,50e-6,.45),reg_pulldown=lut_size('n18',.18,3,40e-6,.45))
    wn=roles['negative_resistance']['rounded_W_um'];wp=roles['bias_unit']['rounded_W_um']
    wb=roles['varactor_bias']['rounded_W_um']
    assert wn<=100 and wp<=100
    text=f'''// Analog differential LC oscillator; no digital logic.
simulator lang=spectre
subckt lc_vco_2ghz (vss iref vctrl vdd outp outn)
MPREFU (pbu pbu vdd vdd) p18 w={wp:g}u l=.18u m=4
MPREFL (iref iref pbu vdd) p18 w={wp:g}u l=.18u m=4
MPFEED (pcas pbu vdd vdd) p18 w={wp:g}u l=.18u m={feed_m*4:g}
MPCAS (tankct iref pcas vdd) p18 w={wp:g}u l=.18u m={feed_m*4:g}
MPVB (vrefvar pbu vdd vdd) p18 w={roles['var_feed']['rounded_W_um']:g}u l=1u m=4
MNB1 (nbmid nbmid vss vss) n18 w={wb:g}u l=1u
MNB2 (vrefvar vrefvar nbmid vss) n18 w={wb:g}u l=1u
MRT (rtail nbmid vss vss) n18 w={wb:g}u l=1u m=2
MRI1 (ra vbias rtail vss) n18 w={roles['reg_input']['rounded_W_um']:g}u l=.36u m=2
MRI2 (rout vrefvar rtail vss) n18 w={roles['reg_input']['rounded_W_um']:g}u l=.36u m=2
MRL1 (ra ra vdd vdd) p18 w={roles['reg_load']['rounded_W_um']:g}u l=1u m=2
MRL2 (rout ra vdd vdd) p18 w={roles['reg_load']['rounded_W_um']:g}u l=1u m=2
MRPU (vbias rout vdd vdd) p18 w={roles['reg_pullup']['rounded_W_um']:g}u l=.18u m=20
MRPD (vbias rout vss vss) n18 w={roles['reg_pulldown']['rounded_W_um']:g}u l=.18u m={pulldown_m:g}
XLP (outp tankct) ind_rf r={ind_r:g}u n={ind_n:g}
XLN (outn tankct) ind_rf r={ind_r:g}u n={ind_n:g}
XCP (outp vss) mim1_rf wr=20u lr={cap_area/20:g}u
XCN (outn vss) mim1_rf wr=20u lr={cap_area/20:g}u
RBP (vbias varp vss) rpposab_3t w=1u l=3u
RBN (vbias varn vss) rpposab_3t w=1u l=3u
RBP2 (vbias varp vss) rpposab_3t w=1u l=3u
RBN2 (vbias varn vss) rpposab_3t w=1u l=3u
MNP (outp outn vss vss) n18 w={wn:g}u l=0.18u
MNN (outn outp vss vss) n18 w={wn:g}u l=0.18u
'''
    for i in range(coupling_units):
        text+=f'XCCP{i} (outp varp) mim1_rf wr=30u lr=30u\nXCCN{i} (outn varn) mim1_rf wr=30u lr=30u\n'
    for i in range(var_units):
        text+=f'XVP{i} (vctrl varp) pvar18w10l1_ckt_rf wr=10u lr=1u nf={var_nf:g}\nXVN{i} (vctrl varn) pvar18w10l1_ckt_rf wr=10u lr=1u nf={var_nf:g}\n'
    text+='ends lc_vco_2ghz\n'
    circuit=CASE/'circuit.scs';circuit.write_text(text)
    L=(-1.7271-.3612*ind_n+.2907*ind_n**2+.03256*ind_r+.000171*ind_r**2)*1e-9
    Rs=-1.1605+.66174*ind_n+.07719*ind_n**2+.02008*ind_r+.00011029*ind_r**2
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,external_reference_A=50e-6,PMOS_reference_unit_A=12.5e-6,PMOS_reference_m=4,feed_m=feed_m,PMOS_feed_m=feed_m*4,target_tank_current_A=feed_m*50e-6,
      bias_topology=f'Two diode-connected PMOS banks feed a{feed_m}x self-biased cascode mirror. The50uA reference input is the only external bias.',
      gmID_rationale=f'n18 L0.18um negative-resistance pair target{core_gmid}V^-1 at{feed_m*25:g}uA/device; fT from actualSMIC LUT. PMOS L0.18um mirror target{bias_gmid}V^-1 reduces bias-node startup capacitance; longL1um var-feed matches its actualLUTVGS. All banks use integer multipliers.',
      regulator=dict(tail_multiplier=2,input_multiplier=2,load_multiplier=2,pullup_multiplier=20,pulldown_multiplier=pulldown_m),
      inductor=dict(model='ind_rf',count=2,radius_um=ind_r,turns=ind_n,metal_width_um=8,spacing_um=1.5,model_series_L_H=L,model_series_R_ohm=Rs,approx_Q_at_2GHz=2*np.pi*2e9*L/Rs),
      fixed_cap=dict(model='mim1_rf',width_um=20,length_um=cap_area/20,area_each_um2=cap_area,nominal_C_F=cap_area*1e-15,count=2),
      coupling_cap=dict(model='mim1_rf',unit_width_um=30,unit_length_um=30,parallel_units_each_side=coupling_units,total_C_each_side_F=coupling_units*.9e-12),
      varactor=dict(model='pvar18w10l1_ckt_rf',width_um=10,length_um=1,fingers=var_nf,parallel_units_each_side=var_units,count=2*var_units,ports='port1=vctrl,port2=varp/varn; DC biased through nativeR,AC coupled by nativeMIM; vendor substrates refer to global0'),
      varactor_bias='MPVB feeds two1umNMOSdiodes creatingvrefvar. A5MOSerroramplifierand analogpush-pull common-source powerstage regulatevbias; thissupplies the real startupcharge ofcouplingcaps. Eachvarnodeconnects throughtwoparallelnativeRPPOSAB W1/L3umunits. AllbiasandregulatorpowerisincludedinVDD.',
      nominal_temperature_C=27,LUT_temperature_C=27,digital_cells=0,
      native_passive_reference='RF readme explicitly givesind_rf r60u n3.5, MOSvaractorwr10u lr1u nf20 andMIM30u×30u examples. PDKcards are frozen unmodified; no userideal tank.',
      model_files={str(p):sha(p) for p in RF_FILES}))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,process='SMIC18MMRF',corner='tt',temperature_C=27,nominal_VDD_V=1.8,pushing_VDD_V=[1.62,1.98],
      reference_sink_A=50e-6,load_each_F=10e-15,controls_V=CONTROLS,control_step_end_s=[0,40e-9,80e-9,120e-9],control_ramp_s=.1e-9,
      measurement_windows_s=WINDOWS,stop_s=160e-9,max_step_s=5e-12,initial_voltages_V=dict(outp=.61,outn=.59),skip_DC=True,
      frequency_definition='19/(crossing20-crossing1), differential rising zero crossings counted from each fixedwindow start; crossing20 must remain insidewindow',
      limits=dict(frequency0_min_Hz=2.08e9,frequency1p8_max_Hz=1.72e9,tuning_ratio_min=1.25,step_drop_min_Hz=8e6,swing_min_Vpp=.3,startup_max_s=14e-9,
        startup_threshold_V=.2,output_min_V=-.05,output_max_VDD=.75,commonmode_min_VDD=.18,commonmode_max_VDD=.48,reference_min_V=.22,reference_headroom_min_V=.9,power_max_W=2.4e-3,pushing_max_pct_per_V=.6),
      power_window_s=[20e-9,159e-9],power_definition='-VDD*timeweighted mean(I(VDD)), includes all3 tuning transitions and reference branch',
      pushing_definition='100*abs(f1.98-f1.62)/mean(f1.98,f1.62)/0.36, each of4 controls,TT27C',
      coverage_2GHz_functional=True,scope_excludes=['remaining26 fullPVT rows','SS/FF and non27C pushing','phase noise/jitter (not an original metric)','mismatch/MonteCarlo','PEX'],
      structure='Sourceverifierimposespublished electrical behavior; fullnativeRFpassives retained here withoutideal tank substitution. No digital logic.'))
    return circuit


def bench(circuit,mode='nominal',step_ps=5):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{MODEL}" section=res_tt
include "{RFLIB}" section=mim_tt
include "{RFVAR}"
include "{RFIND}"
include "{circuit}"
simulator lang=spectre
simulatorOptions options temp=27 tnom=27 reltol=1e-5 vabstol=1e-8 iabstol=1e-14 gmin=1e-12
saveOptions options save=selected
VCTRL (vctrl 0) vsource type=pwl wave=[0 0 39.9n 0 40n 0.6 79.9n 0.6 80n 1.2 119.9n 1.2 120n 1.8 160n 1.8]
save vctrl
'''
    supplies=[('',1.8)] if mode=='nominal' else [('_LOW',1.62),('_HIGH',1.98)]
    for tag,V in supplies:
        b+=f'''VDD{tag} (vdd{tag} 0) vsource dc={V}
IREF{tag} (iref{tag} 0) isource dc=50u
XVCO{tag} (0 iref{tag} vctrl vdd{tag} outp{tag} outn{tag}) lc_vco_2ghz
CLP{tag} (outp{tag} 0) capacitor c=10f
CLN{tag} (outn{tag} 0) capacitor c=10f
ic outp{tag}=0.61 outn{tag}=0.59
save vdd{tag} iref{tag} outp{tag} outn{tag} VDD{tag}:p XVCO{tag}.tankct XVCO{tag}.pbu XVCO{tag}.pcas XVCO{tag}.vbias XVCO{tag}.varp XVCO{tag}.varn XVCO{tag}.vrefvar XVCO{tag}.rout
'''
        if mode=='nominal':
            for dev in ['MPREFU','MPREFL','MPFEED','MPCAS','MNP','MNN','MPVB','MNB1','MNB2','MRT','MRI1','MRI2','MRL1','MRL2','MRPU','MRPD']:
                b+='save '+' '.join(f'XVCO.{dev}:{p}' for p in ['ids','gm','gds','vgs','vds','vdsat'])+'\n'
    return b+f'tran tran stop=160n maxstep={step_ps:g}p skipdc=yes errpreset=conservative method=traponly\n'


def crossings(t,v,level=0):
    i=np.flatnonzero((v[:-1]<level)&(v[1:]>=level));return t[i]+(t[i+1]-t[i])*(level-v[i])/(v[i+1]-v[i])


def window(t,v,a,b):
    i=(t>a)&(t<b);return np.r_[a,t[i],b],np.r_[np.interp(a,t,v),v[i],np.interp(b,t,v)]


def time_mean(t,v,a,b):
    tx,vx=window(t,v,a,b);return float(np.trapz(vx,tx)/(b-a))


def point(d,tag,VDD):
    t=d['time'];vp=d['outp'+tag];vn=d['outn'+tag];vd=vp-vn;cm=(vp+vn)/2;edges=crossings(t,vd);start=crossings(t,abs(vd),.2)
    plateaus=[]
    for control,(a,b) in zip(CONTROLS,WINDOWS):
        ee=edges[(edges>=a)&(edges<=b)];ok=len(ee)>=20
        p=dict(control_V=control,window_s=[a,b],rising_crossing_count=len(ee),selected_crossings_s=ee[:20].tolist(),twentieth_crossing_inside=bool(ok),frequency_Hz=float(19/(ee[19]-ee[0])) if ok else None)
        for name,wave in [('differential',vd),('commonmode',cm),('outp',vp),('outn',vn),('iref',d['iref'+tag])]:
            _,vv=window(t,wave,a,b);p[name+'_min_V']=float(min(vv));p[name+'_max_V']=float(max(vv))
        p['swing_Vpp']=p['differential_max_V']-p['differential_min_V']
        p['power_W']=-VDD*time_mean(t,d['VDD'+tag+':p'],a,b)
        p['all_complete_period_average_Hz']=float((len(ee)-1)/(ee[-1]-ee[0])) if len(ee)>=2 else None
        plateaus.append(p)
    return dict(VDD_V=VDD,plateaus=plateaus,startup_s=float(start[0]) if len(start) else None,oscillation_data_complete=bool(len(start) and all(x['twentieth_crossing_inside'] for x in plateaus)),
      power_W=-VDD*time_mean(t,d['VDD'+tag+':p'],20e-9,159e-9))


def extract(run,mode):
    d=data(run,'tran.tran')
    if mode=='push':
        low=point(d,'_LOW',1.62);high=point(d,'_HIGH',1.98)
        valid=low['oscillation_data_complete'] and high['oscillation_data_complete']
        pushing=[100*abs(h['frequency_Hz']-l['frequency_Hz'])/((h['frequency_Hz']+l['frequency_Hz'])/2)/.36 for l,h in zip(low['plateaus'],high['plateaus'])] if valid else None
        r=dict(run_dir=str(run.relative_to(ROOT)),mode=mode,generated_at=now(),points=[low,high],functional=valid,pushing_pct_per_V=pushing,max_pushing_pct_per_V=max(pushing) if pushing else None)
        write_json(run/'measurements.json',r);write_json(CASE/'pushing_results.json',r)
    else:
        q=point(d,'',1.8);ps=q['plateaus'];valid=q['oscillation_data_complete'];fs=[p['frequency_Hz'] for p in ps]
        vals=dict(swing_min_Vpp=min(p['swing_Vpp'] for p in ps),startup_s=q['startup_s'],output_negative_excursion_V=max(0,-min(min(p['outp_min_V'],p['outn_min_V']) for p in ps)),
          output_high_fraction=max(max(p['outp_max_V'],p['outn_max_V']) for p in ps)/1.8,commonmode_min_fraction=min(p['commonmode_min_V'] for p in ps)/1.8,
          commonmode_max_fraction=max(p['commonmode_max_V'] for p in ps)/1.8,reference_min_V=min(p['iref_min_V'] for p in ps),reference_headroom_V=1.8-max(p['iref_max_V'] for p in ps),power_W=q['power_W'])
        if valid:vals.update(frequency0_Hz=fs[0],frequency1p8_Hz=fs[3],tuning_ratio=fs[0]/fs[3],step_drop_Hz=min(fs[i]-fs[i+1] for i in range(3)))
        limits=[('frequency0_Hz',2.08e9,'min','Hz'),('frequency1p8_Hz',1.72e9,'max','Hz'),('tuning_ratio',1.25,'min','ratio'),('step_drop_Hz',8e6,'min','Hz'),
          ('swing_min_Vpp',.3,'min','Vpp'),('startup_s',14e-9,'max','s'),('output_negative_excursion_V',.05,'max','V'),('output_high_fraction',.75,'max','fraction'),
          ('commonmode_min_fraction',.18,'min','fraction'),('commonmode_max_fraction',.48,'max','fraction'),('reference_min_V',.22,'min','V'),('reference_headroom_V',.9,'min','V'),('power_W',2.4e-3,'max','W')]
        gates={k:gate(vals[k],lim,sense,u) for k,lim,sense,u in limits if vals.get(k) is not None}
        functional=bool(valid and fs[0]>=2e9>=fs[-1] and all(fs[i]>fs[i+1] for i in range(3)))
        r=dict(case_slot=49,generated_at=now(),run_dir=str(run.relative_to(ROOT)),mode=mode,point=q,values=vals,gates=gates,functional=functional,all_measurements_complete=valid)
        ops=[];t=d['time']
        for control,(a,b) in zip(CONTROLS,WINDOWS):
            devices={}
            for dev in ['MPREFU','MPREFL','MPFEED','MPCAS','MNP','MNN','MPVB','MNB1','MNB2','MRT','MRI1','MRI2','MRL1','MRL2','MRPU','MRPD']:
                op={p:time_mean(t,d[f'XVCO.{dev}:{p}'],a,b) for p in ['ids','gm','gds','vgs','vds','vdsat']}
                op['gmid']=abs(op['gm']/op['ids']) if op['ids'] else None
                op['min_saturation_headroom_V']=float(min(window(t,abs(d[f'XVCO.{dev}:vds'])-abs(d[f'XVCO.{dev}:vdsat']),a,b)[1]));devices[dev]=op
            ops.append(dict(control_V=control,devices=devices))
        r['operating_conditions']=ops
        write_json(run/'measurements.json',r);write_json(CASE/'nominal_results.json',r)
    return finalize()


def finalize():
    nominal=json.loads((CASE/'nominal_results.json').read_text()) if (CASE/'nominal_results.json').exists() else None
    if nominal is None:return dict(status='partial',reason='Nominal run missing')
    result=dict(nominal);pushing=None
    if (CASE/'pushing_results.json').exists():
        candidate=json.loads((CASE/'pushing_results.json').read_text());run=ROOT/candidate['run_dir']
        if sha(run/'inputs/circuit.scs')==sha(ROOT/nominal['run_dir']/'inputs/circuit.scs'):pushing=candidate
    gates=dict(nominal['gates']);functional=bool(nominal['functional'] and pushing and pushing['functional'])
    if pushing and pushing['max_pushing_pct_per_V'] is not None:gates['pushing_pct_per_V']=gate(pushing['max_pushing_pct_per_V'],.6,'max','%/V')
    tiers={tier:bool(functional and len(gates)==14 and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']}
    tier=next((k for k in tiers if tiers[k]),None)
    run_paths=[nominal['run_dir']]+([pushing['run_dir']] if pushing else [])
    model_valid=all(json.loads((ROOT/q/'run.json').read_text()).get('model_dimensions_valid',False) for q in run_paths)
    result.update(status='complete_'+tier if tier else 'partial',nominal_complete=bool(tier),all_nominal_checks_complete=bool(functional and len(gates)==14),model_dimensions_valid=model_valid,gates=gates,pass_tiers=tiers,functional_checks_pass=functional,pushing=pushing,
      run_dirs=[nominal['run_dir']]+([pushing['run_dir']] if pushing else []),scope='TT27C nominal1.8V plus original1.62/1.98V pushing endpoints,4controls. OtherPVT/noise/mismatch/PEX excluded.')
    write_json(CASE/'latest_results.json',result)
    update_case(49,status=result['status'],nominal_complete=bool(tier),latest_run=result['run_dirs'][-1],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return result


def characterize_varactor():
    b=f'''simulator lang=spectre
global 0
include "{RFVAR}"
simulator lang=spectre
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
'''
    combos=[]
    for orientation in ['control_gate','output_gate']:
        for bias in [0,.55,1.2]:
            for control in np.linspace(0,1.8,13):
                i=len(combos);out=f'o{i}';ctl=f'c{i}';ports=f'{ctl} {out}' if orientation=='control_gate' else f'{out} {ctl}'
                b+=f'VT{i} ({out} 0) vsource dc={bias:g} mag=1\nVC{i} ({ctl} 0) vsource dc={control:g}\nXV{i} ({ports}) pvar18w10l1_ckt_rf wr=10u lr=1u nf=20\nsave VT{i}:p\n'
                combos.append(dict(orientation=orientation,output_bias_V=bias,control_V=float(control),current_trace=f'VT{i}:p'))
    b+='ac ac start=2G stop=2.001G lin=2\n'
    run=run_spectre(49,'varactor_ac',b,[RFVAR,CASE/'contract.json'])
    d=data(run,'ac.ac')
    for q in combos:
        Y=-d[q['current_trace']][0];q.update(Ceff_F=float(Y.imag/(2*np.pi*d['freq'][0])),conductance_S=float(Y.real))
    r=dict(run_dir=str(run.relative_to(ROOT)),frequency_Hz=float(d['freq'][0]),native_model=str(RFVAR),native_model_sha256=sha(RFVAR),rows=combos)
    write_json(run/'measurements.json',r);write_json(CASE/'varactor_characterization.json',r)
    for orientation in ['control_gate','output_gate']:
        for bias in [0,.55,1.2]:
            vals=[q['Ceff_F']*1e12 for q in combos if q['orientation']==orientation and q['output_bias_V']==bias]
            print(orientation,bias,np.round(vals,4).tolist())
    return r


def characterize_varactor_transient():
    b=f'''simulator lang=spectre
global 0
include "{RFVAR}"
simulator lang=spectre
simulatorOptions options temp=27 tnom=27 reltol=1e-5 vabstol=1e-8 iabstol=1e-14
saveOptions options save=selected
VCTRL (vc 0) vsource type=pwl wave=[0 0 39.9n 0 40n .6 79.9n .6 80n 1.2 119.9n 1.2 120n 1.8 160n 1.8]
'''
    combos=[]
    for bias in [.55,1.2,1.4]:
        for scale in [1,.8,.6]:
            i=len(combos);b+=f'''VT{i} (o{i} 0) vsource type=sine dc={bias:g} ampl=.15 freq=2G
VC{i} (c{i} 0) vsource type=pwl wave=[0 0 39.9n 0 40n {scale*.6:g} 79.9n {scale*.6:g} 80n {scale*1.2:g} 119.9n {scale*1.2:g} 120n {scale*1.8:g} 160n {scale*1.8:g}]
XV{i} (c{i} o{i}) pvar18w10l1_ckt_rf wr=10u lr=1u nf=20
save o{i} VT{i}:p XV{i}.3 XV{i}.4
'''
            combos.append(dict(output_bias_V=bias,control_scale=scale,index=i))
    b+='tran tran stop=160n maxstep=2p skipdc=yes errpreset=conservative method=traponly\n'
    run=run_spectre(49,'varactor_tran',b,[RFVAR,CASE/'contract.json']);d=data(run,'tran.tran');t=d['time']
    for q in combos:
        i=q['index'];q['plateaus']=[]
        for control,(a,z) in zip(CONTROLS,WINDOWS):
            #20ns to39ns is an integer38cycles ofthe2GHz test tone.
            tx,cur=window(t,-d[f'VT{i}:p'],a,z);phase=2*np.pi*2e9*tx
            C=float(2*np.trapz(cur*np.cos(phase),tx)/(z-a)/(.15*2*np.pi*2e9))
            q['plateaus'].append(dict(control_V=control,actual_control_V=control*q['control_scale'],Ceff_F=C,internal3_avg_V=time_mean(t,d[f'XV{i}.3'],a,z)))
        print(q['output_bias_V'],q['control_scale'],[round(p['Ceff_F']*1e12,4) for p in q['plateaus']],[round(p['internal3_avg_V'],4) for p in q['plateaus']])
    r=dict(run_dir=str(run.relative_to(ROOT)),frequency_Hz=2e9,output_amplitude_V=.15,native_model_sha256=sha(RFVAR),rows=combos)
    write_json(run/'measurements.json',r);write_json(CASE/'varactor_transient_characterization.json',r);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['nominal','push'],default='nominal');p.add_argument('--cap-area',type=float,default=600)
    p.add_argument('--var-nf',type=int,default=20);p.add_argument('--feed-m',type=int,default=16);p.add_argument('--core-gmid',type=float,default=12);p.add_argument('--bias-gmid',type=float,default=20)
    p.add_argument('--coupling-units',type=int,default=3);p.add_argument('--var-units',type=int,default=2);p.add_argument('--varbias-gmid',type=float,default=7.3);p.add_argument('--pulldown-m',type=int,default=4)
    p.add_argument('--ind-r',type=float,default=60);p.add_argument('--ind-n',type=float,default=3.5);p.add_argument('--step',type=float,default=5);p.add_argument('--extract');p.add_argument('--characterize-varactor',action='store_true');p.add_argument('--characterize-varactor-tran',action='store_true');a=p.parse_args()
    if a.characterize_varactor:characterize_varactor();return
    if a.characterize_varactor_tran:characterize_varactor_transient();return
    if a.extract:run=ROOT/a.extract
    else:
        if (ROOT/'monitor/QUOTA_TRIGGER.json').exists():raise RuntimeError('Quota trigger: stop new49 simulations')
        if a.mode=='nominal':c=design(a.cap_area,a.var_nf,a.feed_m,a.core_gmid,a.bias_gmid,a.ind_r,a.ind_n,a.coupling_units,a.var_units,a.varbias_gmid,a.pulldown_m)
        else:c=CASE/'circuit.scs'
        b=bench(c,a.mode,a.step);(CASE/f'testbench_{a.mode}.scs').write_text(b);update_case(49,status='running',nominal_complete=False)
        deps=[c,CASE/'sizing.json',CASE/'contract.json',CASE/'source_provenance.json',*RF_FILES]
        run=run_spectre(49,a.mode,b,deps)
        meta=json.loads((run/'run.json').read_text());meta['additional_RF_model_hashes']={str(f):sha(f) for f in RF_FILES};write_json(run/'run.json',meta)
    r=extract(run,a.mode);print(json.dumps({k:r.get(k) for k in ['status','values','pass_tiers','run_dirs']},indent=2))


if __name__=='__main__':main()
