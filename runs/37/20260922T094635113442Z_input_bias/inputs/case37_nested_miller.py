"""SMIC18 three-gain-stage nested Miller amplifier, deterministic nominal only."""
from common import *
import argparse
import importlib.util

CASE=ROOT/'cases/37-nested-miller'
TASK=SOURCE/'sky130-three-stage-nested-miller-ota-pvt'
DEVS=['MREF','MTAIL','MBP1','MPDM','MS2B','MVBN','MI1','MI2','MP1A','MP1B','MA2','MPD2','MPM2','MS2','MA3','ML3']
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region']

def design(branch=1.2,second=2.5,output=105,c1=8,c2=3,rz1=0,rz2=0):
    CASE.mkdir(parents=True,exist_ok=True)
    sources={}
    for name in ['instruction.md','solution/circuit.spi','tests/verify.py','tests/utils.py']+['tests/benches/tb_'+k+'.spi' for k in ['pvt','input_bias','swing','settling','slew']]:
        src=TASK/name;dest=CASE/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(src.read_bytes())
        assert sha(src)==sha(dest)
        sources[name]=dict(path=str(src),sha256=sha(src),frozen=str(dest.relative_to(ROOT)))
    roles={
      'input':lut_size('n18',1,18,branch*1e-6,.45),
      'first_mirror':lut_size('p18',1,8,branch*1e-6,.9),
      'second_n':lut_size('n18',1,8,second*1e-6,.9),
      'second_mirror':lut_size('p18',1,10,second*1e-6,.9),
      'n_bias':lut_size('n18',1,14,5e-6,.2),
      'p_bias':lut_size('p18',1,10,5e-6,.9),
      'output_n':lut_size('n18',.36,14,output*1e-6,.9),
    }
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    c=CASE/'circuit.scs'
    lines=f'''// Three gain stages, outer and inner Miller paths; source topology retained.
// SMIC18 primitive D G S B; m scales identical parallel model units.
simulator lang=spectre
subckt three_stage_nmc_ota (vss iref vdd vinn vinp vout)
MREF (iref iref vss vss) n18 w={w['n_bias']:g}u l=1u
MTAIL (tail iref vss vss) n18 w={w['n_bias']:g}u l=1u m={2*branch/5:g}
MBP1 (pdm iref vss vss) n18 w={w['n_bias']:g}u l=1u
MPDM (pdm pdm vdd vdd) p18 w={w['p_bias']:g}u l=1u
MS2B (vbn pdm vdd vdd) p18 w={w['p_bias']:g}u l=1u
MVBN (vbn vbn vss vss) n18 w={w['n_bias']:g}u l=1u
MI1 (na vinn tail vss) n18 w={w['input']:g}u l=1u
MI2 (n1 vinp tail vss) n18 w={w['input']:g}u l=1u
MP1A (na na vdd vdd) p18 w={w['first_mirror']:g}u l=1u
MP1B (n1 na vdd vdd) p18 w={w['first_mirror']:g}u l=1u
MA2 (nb n1 vss vss) n18 w={w['second_n']:g}u l=1u
MPD2 (nb nb vdd vdd) p18 w={w['second_mirror']:g}u l=1u
MPM2 (n2 nb vdd vdd) p18 w={w['second_mirror']:g}u l=1u m=2
MS2 (n2 vbn vss vss) n18 w={w['n_bias']:g}u l=1u m={2*second/5:g}
MA3 (vout n2 vss vss) n18 w={w['output_n']:g}u l=.36u
ML3 (vout pdm vdd vdd) p18 w={w['p_bias']:g}u l=1u m={output/5:g}
'''
    for label,node,cap,res in [('1','n1',c1,rz1),('2','n2',c2,rz2)]:
        capnode=node if res==0 else 'z'+label
        lines+=f'CM{label} (vout {capnode}) capacitor c={cap:g}p\n'
        if res:lines+=f'RZ{label} ({capnode} {node}) resistor r={res:g}\n'
    c.write_text(lines+'ends three_stage_nmc_ota\n')
    rows=[]
    for line in lines.splitlines():
        m=re.match(r'(M\w+) \((.*?)\) (n18|p18) w=([.\d]+)u l=([.\d]+)u(?: m=([.\d]+))?',line)
        if m:
            name,pins,model,ww,ll,mult=m.groups();ww=float(ww);ll=float(ll);mult=float(mult or 1)
            rows.append(dict(name=name,pins=pins.split(),model=model,W_unit_um=ww,L_um=ll,m=mult,W_total_um=ww*mult,unit_width_valid=ww<=100))
    assert len(rows)==16 and all(x['unit_width_valid'] for x in rows)
    write_json(CASE/'geometry.json',dict(devices=rows,circuit_sha256=sha(c),all_unit_widths_valid=True,interpretation='Primitive D G S B; m scales identical legal model units. Fractional m scales current without changing the unit width. No digital cells.'))
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,parameters=dict(branch=branch,second=second,output=output,c1=c1,c2=c2,rz1=rz1,rz2=rz2),
        rationale='A1 NMOS pair with PMOS mirror; A2 noninverting N common-source plus P mirror; A3 N common-source/P current source. Initial input gm/ID18 and1.2uA per branch gives gm1~21.6uS and gm1/(2pi*8pF)~0.43MHz. A2 gm/ID8 keeps n1 high enough for input-stage headroom. A3 105uA at gm/ID14 gives gm3~1.47mS to drive200pF. C1 spans A2+A3; C2 surrounds A3. All current biases derived from5uA iref. Actual OP handles body effect, mirror VDS differences and narrow-width deviations from10um LUT.',
        skill_assets='/home/IC/.codex/skills/gmoverid/assets/design_gmoverid.py',target_lut_api=str(LUT_ROOT/'gmidsmic.py')))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_files=sources,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=5e-6,load_F=200e-12,input_common_mode_V=.9,output_target_V=.9,
        ac=dict(frequency_Hz=[.01,1e8],points_per_decade=100,return_ratio='-V(vout)/V(vinn) from series AC1 source VTEST(vout,vinn), with unity DC feedback',gain_0p1Hz_min_dB=110,ugb_min_Hz=400e3,phase_margin_min_deg=70,power_W=[0,300e-6],output_error_max_V=.01,drive_FOM_min=300,drive_FOM='UGB(kHz)*200pF/power(uW)'),
        input_bias=dict(connection='Both independent inputs at0.9V, open-loop output with200pF',each_input_abs_current_max_A=100e-9),
        range=dict(command_V=[.1,1.7],step_V=.002,points=801,contiguous_valid_span_min_V=.8,eligibility_tracking_error_max_V=.02),
        settling=dict(command_V=[.4,.9],edge_start_s=2e-6,edge_end_s=2.1e-6,end_s=50e-6,fixed_band_V=.01,first_sample_after_last_exit=True,reference_time_s=2e-6,time_max_s=3e-6,strict_time=True,final_error_fraction_max=.02),
        slew=dict(command_V=[.65,1.15],rise_edge_s=[2e-6,2.1e-6],fall_edge_s=[42.1e-6,42.2e-6],threshold_V=[.75,1.05],fall_search_start_s=42e-6,end_s=82e-6,rise_min_V_per_us=.2,fall_min_V_per_us=.2),
        relaxation='Positive min*0.9/0.85; max*1.1/1.15; amplitude gain dB adds20log10(.9/.85); PM min retains>=45deg. Strict power< and settling< retained. Full stimuli, fixed eligibility/settling windows, finite/positive-power guard, load and source connections unchanged.',
        nominal_only=True,excluded=['other44 original PVT points','local mismatch/Monte Carlo (outside original task too)','extracted parasitics/package/aging','passive variation']))
    return c

def prefix(c):
    return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-15
saveOptions options save=selected
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=5u
X (0 iref vdd vinn vinp vout) three_stage_nmc_ota
CL (vout 0) capacitor c=200p
save vout vinn vinp VDD:p iref
'''

def acbench(c):
    b=prefix(c)+'''VIN (vinp 0) vsource dc=.9
VTEST (vout vinn) vsource dc=0 mag=1
save X.tail X.pdm X.vbn X.na X.n1 X.nb X.n2
'''
    for dev in DEVS:b+='save '+' '.join(f'X.{dev}:{f}' for f in OPFIELDS)+'\n'
    return b+'dcOp dc\nac ac start=.01 stop=100M dec=100\n'

def inputbench(c):
    return prefix(c)+'''VINP (vinp 0) vsource dc=.9
VINN (vinn 0) vsource dc=.9
save VINP:p VINN:p
dcOp dc
'''

def rangebench(c):
    return prefix(c)+'''parameters command=.9
VIN (vinp 0) vsource dc=command
VFB (vout vinn) vsource dc=0
swing dc param=command start=.1 stop=1.7 step=.002
'''

def settlebench(c,step=10e-9):
    return prefix(c)+f'''VIN (vinp 0) vsource type=pwl wave=[0 .4 2u .4 2.1u .9 50u .9]
VFB (vout vinn) vsource dc=0
tran tran stop=50u maxstep={step/2:g} strobeperiod={step:g} strobeoutput=strobeonly errpreset=conservative method=gear2only
'''

def slewbench(c,step=10e-9):
    return prefix(c)+f'''VIN (vinp 0) vsource type=pwl wave=[0 .65 2u .65 2.1u 1.15 42.1u 1.15 42.2u .65 82u .65]
VFB (vout vinn) vsource dc=0
tran tran stop=82u maxstep={step/2:g} strobeperiod={step:g} strobeoutput=strobeonly errpreset=conservative method=gear2only
'''

def source_verifier():
    old=sys.modules.get('utils');u=importlib.util.spec_from_file_location('utils',CASE/'source/tests/utils.py');um=importlib.util.module_from_spec(u);sys.modules['utils']=um;u.loader.exec_module(um)
    spec=importlib.util.spec_from_file_location('case37_frozen_verify',CASE/'source/tests/verify.py');module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    if old is None:sys.modules.pop('utils',None)
    else:sys.modules['utils']=old
    return module

def extract(runs):
    v=source_verifier();rmap={k:Path(x) for k,x in runs.items()};a=data(rmap['pvt'],'ac.ac');o=dc(rmap['pvt'])
    def plot(q,axis,names,title):
        keys=([axis] if axis else [])+names
        variables=[{'freq':'frequency','time':'time','VDD:p':'i(vdd)','VINP:p':'i(vinp)','VINN:p':'i(vinn)'}.get(k,'v('+k+')') for k in keys]
        points=[list(x) for x in zip(*(np.atleast_1d(q[k]).astype(complex) for k in keys))]
        return v.Plot(title,variables,points)
    pvt=v.extract_metrics('pvt',[plot(a,'freq',['vout','vinn'],'AC Analysis'),plot(o,None,['vout','VDD:p'],'Operating Point')],v.NOMINAL)
    vals=dict(pvt);source_rows=[dict(group='pvt',point=v.NOMINAL,**pvt)]
    h=-a['vout']/a['vinn'];loop=loop_metrics(a['freq'],h,.1);db=20*np.log10(abs(h));first=np.flatnonzero(db<0)[0]
    diagnostic=dict(falling_crossings=loop['falling_crossings'],post_first_crossing_max_dB=float(max(db[first:])),gain_crosscheck_difference_dB=abs(loop['gain_db']-pvt['dc_gain_db']),ugb_relative_crosscheck_error=abs(loop['ugb_hz']/pvt['ugb_hz']-1),phase_crosscheck_difference_deg=abs(loop['phase_margin_deg']-pvt['phase_margin_deg']))
    op={}
    for dev in DEVS:
        q={k:o[f'X.{dev}:{k}'] for k in OPFIELDS};q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[dev]=q
    valid=bool(-1.8*o['VDD:p']>0 and diagnostic['falling_crossings']==1 and diagnostic['post_first_crossing_max_dB']<0)
    detail={}
    for group in ['input_bias','swing','settling','slew']:
        if group not in rmap:continue
        if group=='input_bias':plots=[plot(dc(rmap[group]),None,['VINP:p','VINN:p'],'Operating Point')]
        elif group=='swing':
            d=data(rmap[group],'swing.dc');plots=[plot(d,None,['vinp','vout'],'DC transfer characteristic')]
            valid=bool(valid and len(d['vinp'])==801 and np.allclose(d['vinp'],np.linspace(.1,1.7,801),atol=1e-12,rtol=0))
            good=abs(d['vout']-d['vinp'])<=.02;segments=np.split(np.flatnonzero(good),np.flatnonzero(np.diff(np.flatnonzero(good))>1)+1);seg=max(segments,key=len)
            detail['range']=dict(points=len(good),valid_points=int(sum(good)),largest_valid_command_V=[float(d['vinp'][seg[0]]),float(d['vinp'][seg[-1]])],max_error_in_largest_interval_V=float(max(abs(d['vout'][seg]-d['vinp'][seg]))),eligibility_band_V=.02)
        else:
            d=data(rmap[group],'tran.tran');plots=[plot(d,'time',['vinp','vout'],'Transient Analysis')]
            detail[group]=dict(points=len(d['time']),sample_period_s=float(np.median(np.diff(d['time']))),start_s=float(d['time'][0]),end_s=float(d['time'][-1]),final_input_V=float(d['vinp'][-1]),final_output_V=float(d['vout'][-1]))
            end=50e-6 if group=='settling' else 82e-6;valid=bool(valid and abs(d['time'][-1]-end)<1e-14)
        metrics=v.extract_metrics(group,plots,v.NOMINAL);vals.update(metrics);source_rows.append(dict(group=group,point=v.NOMINAL,**metrics))
    specs=[('dc_gain_db',110,'min','dB','amplitude_db'),('ugb_hz',400e3,'min','Hz','linear'),('phase_margin_deg',70,'min','deg','phase_margin'),('drive_fom_khz_pf_per_uw',300,'min','kHz*pF/uW','linear'),('output_common_mode_error_v',.01,'max','V','linear'),('power_w',300e-6,'max','W','linear'),('input_bias_vinp_a',100e-9,'max','A','linear'),('input_bias_vinn_a',100e-9,'max','A','linear'),('closed_loop_range_vpp',.8,'min','Vpp','linear'),('settling_time_s',3e-6,'max','s','linear'),('settling_error_fraction',.02,'max','fraction','linear'),('slew_rise_v_per_us',.2,'min','V/us','linear'),('slew_fall_v_per_us',.2,'min','V/us','linear')]
    gates={}
    for key,limit,sense,unit,kind in specs:
        if key not in vals:continue
        if not np.isfinite(vals[key]):valid=False;vals[key]=None;continue
        g=gate(vals[key],limit,sense,unit,kind)
        g['comparison']='<' if key in ['power_w','settling_time_s'] else '>=' if sense=='min' else '<='
        if g['comparison']=='<':g['passes']={tier:g['value']<lim for tier,lim in g['limits'].items()}
        gates[key]=g
    complete=set(rmap)==set(v.GROUPS);tiers={t:bool(complete and valid and len(gates)==13 and all(g['passes'][t] for g in gates.values())) for t in ['original','10pct','15pct']};tier=next((x for x in tiers if tiers[x]),None)
    functional=v.nominal_functional([x for x in source_rows if x['group'] in ['pvt','settling']],[]) if complete and vals.get('settling_time_s') is not None else None
    result=dict(case_slot=37,generated_at=now(),status='complete_'+tier if tier else 'partial',values=vals,gates=gates,pass_tiers=tiers,operating_point=op,dc_nodes={k:z for k,z in o.items() if ':' not in k},loop_diagnostic=diagnostic,measurement_detail=detail,source_nominal_functional=functional,all_nominal_checks_complete=complete,nonrelaxable_guards_pass=valid,model_dimensions_valid=True,nominal_OP_all_16_saturation=all(x['headroom_V']>0 for x in op.values()),run_dirs=[str(x.relative_to(ROOT)) for x in rmap.values()],runs_by_analysis={k:str(x.relative_to(ROOT)) for k,x in rmap.items()},geometry_sha256=sha(CASE/'geometry.json'),source_verifier_sha256=sha(CASE/'source/tests/verify.py'),measurement_engine='Original frozen verifier extract_metrics receives translated PSF vectors for every group. Original45-point matrix check not invoked or spoofed. Independent AC crosscheck and nonnegative raw power check added.',scope='SMIC18 tt1.8V27C; originalfive measurement groups and fixed200pF load. Other44 PVT points, mismatch, parasitics and passive variation excluded.')
    write_json(rmap['pvt']/'measurements.json',result);write_json(CASE/'latest_results.json',result)
    update_case(37,status=result['status'],nominal_complete=bool(tier),case_dir=str(CASE.relative_to(ROOT)),results=str((CASE/'latest_results.json').relative_to(ROOT)),run_dirs=result['run_dirs'])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['static','full'],default='full')
    for key,value in dict(branch=1.2,second=2.5,output=105,c1=8,c2=3,rz1=0,rz2=0).items():p.add_argument('--'+key,type=float,default=value)
    args=vars(p.parse_args());mode=args.pop('mode');update_case(37,status='running',nominal_complete=False)
    c=design(**args);deps=[c,CASE/'sizing.json',CASE/'contract.json',Path(__file__).resolve()];runs={}
    for group,fn in [('pvt',acbench)]+([('input_bias',inputbench),('swing',rangebench),('settling',settlebench),('slew',slewbench)] if mode=='full' else []):
        text=fn(c);(CASE/f'testbench_{group}.scs').write_text(text);runs[group]=run_spectre(37,group,text,deps)
    r=extract(runs);print(json.dumps(dict(status=r['status'],values=r['values'],loop=r['loop_diagnostic'],op={d:{k:r['operating_point'][d][k] for k in ['gmid','headroom_V','ids']} for d in ['MI1','MTAIL','MA2','MS2','MA3','ML3']},runs=r['run_dirs']),indent=2))

if __name__=='__main__':main()
