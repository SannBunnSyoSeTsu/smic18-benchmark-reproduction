"""SMIC18 gain-boosted folded-cascode plus cascoded output stage, nominal only."""
from common import *
import argparse
import importlib.util

CASE=ROOT/'cases/50-gainboosted-folded'
TASK=SOURCE/'sky130-folded-cascode-ota-gain130-pm60-noise50uv-pvt'
OPFIELDS=['ids','gm','gds','vgs','vds','vdsat','region']

def design(branch=150,fold=250,output=900,cc=1.3,rz=1000,pcap=3,ncap=9,fold_ratio=1,pdrop=.35,ndrop=.25,rin=50,paux=20,naux=80):
    CASE.mkdir(parents=True,exist_ok=True);sources={}
    filenames=['instruction.md','solution/circuit.spi','tests/verify.py','tests/utils.py','tests/reviewer_local_loops.py']+['tests/benches/'+x for x in ['tb_op_ac.spi','tb_noise.spi','tb_closed_loop_range.spi','tb_settling.spi']]+['tests/reviewer_benches/tb_'+x+'.spi' for x in ['gpc','gnc']]
    for name in filenames:
        src=TASK/name;dest=CASE/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes(src.read_bytes())
        assert sha(src)==sha(dest);sources[name]=dict(path=str(src),sha256=sha(src),frozen=str(dest.relative_to(ROOT)))
    roles={key:lut_size(dev,L,gmid,10e-6,vds) for key,dev,L,gmid,vds in [
        ('input','n18',.5,18,.9),('n_bias','n18',1,14,.2),('p_bias','p18',1,12,.45),
        ('n_cascode_diode','n18',.36,12,.45),('n_cascode_boosted','n18',.36,18,.45),('p_cascode','p18',.36,14,.45),
        ('second','n18',.18,8,.9),('out_cascode','n18',.18,18,.45),('output_load','p18',.36,8,.9),
        ('aux_pinput','p18',.36,14,.45),('aux_nload','n18',1,14,.45),('level_shift','n18',.36,8,.9)]}
    rows=[];lines=['// Gain-boosted folded first stage and cascoded common-source output.','// D G S B; legal base widths from SMIC18 gm/ID, m scales current.','simulator lang=spectre','subckt folded_cascode_ota (vss iref vdd vinn vinp vout)']
    def mos(name,nodes,role,m=1):
        q=roles[role];w=q['rounded_W_um'];L=q['L_um'];assert 0<w<=100 and m>0
        lines.append(f'{name} ({nodes}) {q["model"]} w={w:g}u l={L:g}u m={m:g}')
        rows.append(dict(name=name,pins=nodes.split(),model=q['model'],role=role,W_unit_um=w,L_um=L,m=m,W_total_um=w*m,unit_width_valid=True))
    def cap(name,a,b,c):lines.append(f'{name} ({a} {b}) capacitor c={c:g}p')
    def res(name,a,b,value):lines.append(f'{name} ({a} {b}) resistor r={value:g}')
    mos('MREF','iref iref vss vss','n_bias',5)
    mos('MTAIL','tail iref vss vss','n_bias',2*branch/10)
    mos('MNBP','vbp iref vss vss','n_bias');mos('MPBP','vbp vbp vdd vdd','p_bias')
    mos('MNPC','vpc iref vss vss','n_bias');res('RPC','vdd','pcbs',pdrop/10e-6);mos('MPPC','vpc vpc pcbs vdd','p_cascode')
    mos('MPB2','ncb vbp vdd vdd','p_bias');mos('MNCB','ncb ncb ncbs vss','n_cascode_diode');res('RNCB','ncbs','vss',ndrop/10e-6)
    mos('MNRBI','nref iref vss vss','n_bias');mos('MNRS','vdd ncb nref vss','n_cascode_diode')
    mos('MPRBI','pref vbp vdd vdd','p_bias');mos('MPRS','vss vpc pref vdd','p_cascode')
    mos('MINP','p1 vinn sinp vss','input',branch/10);mos('MINN','p2 vinp sinn vss','input',branch/10)
    res('RINP','sinp','tail',rin);res('RINN','sinn','tail',rin)
    mos('MFP','p1 vbp vdd vdd','p_bias',fold/10);mos('MFN','p2 vbp vdd vdd','p_bias',fold*fold_ratio/10)
    folded=(fold-branch)/10
    mos('MFCP','mirror vpc p1 vdd','p_cascode',folded);mos('MFCN','nfirst gpc p2 vdd','p_cascode',folded)
    mos('MMD','mirror ncb n1 vss','n_cascode_diode',folded);mos('MMO','nfirst gnc n2 vss','n_cascode_boosted',folded)
    mos('MCD','n1 mirror vss vss','n_bias',folded);mos('MCO','n2 mirror vss vss','n_bias',folded)
    mos('MHSI','hs iref vss vss','n_bias');mos('MHSF','vdd p2 hs vss','level_shift')
    mos('MHRI','hr iref vss vss','n_bias');mos('MHRF','vdd pref hr vss','level_shift')
    mos('MPT','apt vbp vdd vdd','p_bias',2*paux/10)
    mos('MPA','pgd hr apt vdd','aux_pinput',paux/10);mos('MPB','gpc hs apt vdd','aux_pinput',paux/10)
    mos('MPMA','pgd pgd vss vss','aux_nload',paux/10);mos('MPMB','gpc pgd vss vss','aux_nload',paux/10)
    mos('MNT','ant vbp vdd vdd','p_bias',2*naux/10)
    mos('MNA','ngd nref ant vdd','aux_pinput',naux/10);mos('MNB','gnc n2 ant vdd','aux_pinput',naux/10)
    mos('MNMA','ngd ngd vss vss','aux_nload',naux/10);mos('MNMB','gnc ngd vss vss','aux_nload',naux/10)
    cap('CGPC','gpc','vdd',pcap);cap('CGNC','gnc','vss',ncap)
    mos('MOBN','obias iref vss vss','n_bias');mos('MOBP','obias obias vdd vdd','output_load')
    mos('MOUT','nout nfirst vss vss','second',output/10);mos('MOUTC','vout ncb nout vss','out_cascode',output/10)
    mos('MLOAD','vout obias vdd vdd','output_load',output/10)
    cap('CCOMP','vout','comp',cc);res('RCOMP','comp','nfirst',rz);lines.append('ends folded_cascode_ota')
    c=CASE/'circuit.scs';c.write_text('\n'.join(lines)+'\n')
    write_json(CASE/'geometry.json',dict(circuit_sha256=sha(c),devices=rows,all_unit_widths_valid=True,HD_logic='none',interpretation='MOS primitive D G S B; every legal W is an unchanged model-unit width; m sets multiplicity. PMOS bulk atVDD.'))
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,parameters=dict(branch=branch,fold=fold,output=output,cc=cc,rz=rz,pcap=pcap,ncap=ncap,fold_ratio=fold_ratio,pdrop=pdrop,ndrop=ndrop,rin=rin,paux=paux,naux=naux),rationale='L=.5um input gm/ID18,150uA/side gives2.7mS; degeneration50ohm reduces effective gm toabout2.38mS. Cc1.5pF gives initial~252MHz. Folded branches100uA, local p/n boosters hold high/low cascode sources to current-derived replicas. Slow3pF/9pF booster outputs preserve low-frequency gain while avoiding main UGB. Output900uA gm/ID8 drives1pF; .18um cascode enhances gain. Current-derived references replace extreme-size source bias devices; everyMOS has a recorded target-LUT role.',skill_assets='/home/IC/.codex/skills/gmoverid/assets/design_gmoverid.py',target_lut_api=str(LUT_ROOT/'gmidsmic.py')))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_files=sources,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=50e-6,VCM_V=.9,load_F=1e-12,
      ac=dict(frequency_Hz=[10,1e11],points_per_decade=100,return_ratio='-Vout/Vinn with series AC1 at Vout->Vinn',gain_10Hz_min_dB=130,ugb_min_Hz=200e6,phase_margin_min_deg=60,falling_crossings=1,no_later_recross=True,output_error_max_V=.0008,power_W=[0,.0054]),
      noise=dict(connection='unity feedback, VIN input referred',frequency_Hz=[10,1e7],max_Vrms=50e-6),
      range=dict(command_V=[.3,1.5],step_V=.01,points=121,fixed_eligibility_error_V=.02,min_contiguous_span_V=.92,boundary_interpolation='only adjacent qualified/unqualified samples'),
      settling=dict(command_V=[.85,.95,.85],rise_edge_s=[20e-9,21e-9],fall_edge_s=[121e-9,122e-9],reference_s=[20.5e-9,121.5e-9],window_end_s=[119.5e-9,240e-9],final_mean_window_s=[[114.5e-9,119.5e-9],[235e-9,240e-9]],fixed_band_V=.0007,last_entry='first sample after which all remaining samples in that direction window satisfy fixed band',each_time_max_s=10e-9,each_static_max_V=.0007,static_error_fraction_max=.007,step_V=.1),
      local_loop_diagnostic=dict(scope='both cascode-gate boosters, main unity feedback intact',min_PM_deg=45,strictly_diagnostic=True),
      nominal_only=True,excluded=['other26 OP/AC and noise PVT points','two nonnominal range points','two nonnominal settling points','mismatch/MC/CMRR/PSRR not in original task','layout parasitics/passive variation'],relaxation='Project acceptance-policy; preserve full stimulus, loads, frequency/observation windows, last-entry predicate, fixed range/settling error windows and exactlyone falling crossing. Positive min*0.9/0.85,max*1.1/1.15; amplitude dB20log10(.9/.85); PM>=45deg.'))
    return c

def prefix(c):return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-7 vabstol=1e-10 iabstol=1e-16
saveOptions options save=selected
VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=50u
X (0 iref vdd vinn vinp vout) folded_cascode_ota
CL (vout 0) capacitor c=1p
save vout vinn vinp VDD:p iref
'''

def acbench(c):
    b=prefix(c)+'''VIN (vinp 0) vsource dc=.9
VTEST (vout vinn) vsource dc=0 mag=1
save X.tail X.vbp X.vpc X.pcbs X.ncbs X.ncb X.nref X.pref X.p1 X.p2 X.mirror X.nfirst X.n1 X.n2 X.hs X.hr X.apt X.pgd X.gpc X.ant X.ngd X.gnc X.obias X.nout X.sinp X.sinn
'''
    for d in json.loads((CASE/'geometry.json').read_text())['devices']:b+='save '+' '.join(f'X.{d["name"]}:{f}' for f in OPFIELDS)+'\n'
    return b+'dcOp dc\nac ac start=10 stop=100G dec=100\n'

def noisebench(c):return prefix(c)+'''VIN (vinp 0) vsource dc=.9 mag=1
VFB (vout vinn) vsource dc=0
noise (vout 0) noise start=10 stop=10M dec=100 iprobe=VIN
'''

def rangebench(c):return prefix(c)+'''parameters command=.9
VIN (vinp 0) vsource dc=command
VFB (vout vinn) vsource dc=0
swing dc param=command start=.3 stop=1.5 step=.01
'''

def settlebench(c):return prefix(c)+'''VIN (vinp 0) vsource type=pwl wave=[0 .85 20n .85 21n .95 121n .95 122n .85 240n .85]
VFB (vout vinn) vsource dc=0
save X.gpc X.gnc X.p2 X.n2 X.nfirst
tran tran stop=240n maxstep=25p strobeperiod=50p strobeoutput=strobeonly errpreset=conservative
'''

def source_verifier():
    spec=importlib.util.spec_from_file_location('case50_frozen_verify',CASE/'source/tests/verify.py');v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v);return v

def extract(runs):
    v=source_verifier();rmap={k:Path(p) for k,p in runs.items()};a=data(rmap['op_ac'],'ac.ac');o=dc(rmap['op_ac'])
    def plot(q,axis,names,title):
        keys=([axis] if axis else [])+names;variables=[{'freq':'frequency','time':'time','VDD:p':'i(vdd)'}.get(k,'v('+k+')') for k in keys]
        return v.Plot(title,variables,[list(x) for x in zip(*(np.atleast_1d(q[k]).astype(complex) for k in keys))])
    groups={'op_ac':{**v.ac_metrics(plot(a,'freq',['vout','vinn'],'AC Analysis')),**v.op_metrics(plot(o,None,['vout','VDD:p'],'Operating Point'),1.8)}}
    vals=dict(groups['op_ac']);detail={};op={}
    for dev in json.loads((CASE/'geometry.json').read_text())['devices']:
        name=dev['name'];q={f:o[f'X.{name}:{f}'] for f in OPFIELDS};q.update(gmid=abs(q['gm']/q['ids']),gmro=abs(q['gm']/q['gds']),headroom_V=abs(q['vds'])-abs(q['vdsat']));op[name]=q
    valid=bool(vals['falling_crossing_count']==1 and vals['post_first_crossing_gain_db_max']<0 and vals['power_w']>=0)
    if 'noise' in rmap:
        n=data(rmap['noise'],'noise.noise',required=['in','out']);psd=abs(n['in'])**2;f=n['freq'];noise=float(np.sqrt(np.trapz(psd,f)));alpha=np.log(psd[1:]/psd[:-1])/np.log(f[1:]/f[:-1]);exp=alpha+1
        integral=np.where(abs(exp)<1e-10,psd[:-1]*f[:-1]*np.log(f[1:]/f[:-1]),psd[:-1]*f[:-1]*np.expm1(exp*np.log(f[1:]/f[:-1]))/exp)
        nlog=float(np.sqrt(sum(integral)));groups['noise']=dict(input_noise_vrms=noise);detail['noise']=dict(points=len(f),start_Hz=float(f[0]),stop_Hz=float(f[-1]),power_law_integral_Vrms=nlog,integration_relative_difference=abs(noise/nlog-1))
    if 'range' in rmap:groups['range']=v.range_metrics(plot(data(rmap['range'],'swing.dc'),None,['vinp','vout'],'DC transfer characteristic'))
    if 'settling' in rmap:groups['settling']=v.settling_metrics(plot(data(rmap['settling'],'tran.tran'),'time',['vinp','vout'],'Transient Analysis'))
    for q in groups.values():vals.update(q)
    specs=[('dc_gain_db',130,'min','dB','amplitude_db'),('ugb_hz',200e6,'min','Hz','linear'),('phase_margin_deg',60,'min','deg','phase_margin'),('output_common_mode_error_v',.0008,'max','V','linear'),('power_w',.0054,'max','W','linear'),('input_noise_vrms',50e-6,'max','Vrms','linear'),('closed_loop_range_vpp',.92,'min','Vpp','linear'),('closed_loop_tracking_error_v_max',.02,'max','V','linear'),('settling_rise_time_s',10e-9,'max','s','linear'),('settling_fall_time_s',10e-9,'max','s','linear'),('rise_static_error_v',.0007,'max','V','linear'),('fall_static_error_v',.0007,'max','V','linear'),('settling_static_error_fraction',.007,'max','fraction','linear')]
    gates={}
    for key,lim,sense,unit,kind in specs:
        if key not in vals:continue
        if not np.isfinite(vals[key]):valid=False;vals[key]=None;continue
        gates[key]=gate(vals[key],lim,sense,unit,kind)
    complete=set(rmap)==set(v.GROUP_BENCHES);tiers={t:bool(complete and valid and len(gates)==13 and all(x['passes'][t] for x in gates.values())) for t in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    sourcechecks={k:bool(v.case_passes(dict(group=k,**q))) for k,q in groups.items()}
    r=dict(case_slot=50,status='complete_'+tier if tier else 'partial',generated_at=now(),values=vals,gates=gates,pass_tiers=tiers,operating_point=op,dc_nodes={k:x for k,x in o.items() if ':' not in k},measurement_detail=detail,source_group_passes=sourcechecks,nonrelaxable_guards_pass=valid,all_nominal_checks_complete=complete,model_dimensions_valid=True,nominal_OP_all_saturation=all(q['headroom_V']>0 for q in op.values()),run_dirs=[str(p.relative_to(ROOT)) for p in rmap.values()],runs_by_analysis={k:str(p.relative_to(ROOT)) for k,p in rmap.items()},geometry_sha256=sha(CASE/'geometry.json'),source_verifier_sha256=sha(CASE/'source/tests/verify.py'),measurement_engine='Frozen original ac_metrics/op_metrics/range_metrics/settling_metrics/case_passes applied to real PSF. Noise sqrt(integral input-referred PSD) with independent power-law integration crosscheck. No PVT matrix spoofing.',scope='SMIC18 tt1.8V27C; fullfour nominal groups. OtherPVT/MC/parasitics/passive variation excluded.')
    write_json(rmap['op_ac']/'measurements.json',r);write_json(CASE/'latest_results.json',r);update_case(50,status=r['status'],nominal_complete=bool(tier),case_dir=str(CASE.relative_to(ROOT)),results=str((CASE/'latest_results.json').relative_to(ROOT)),run_dirs=r['run_dirs']);return r

def local_loops():
    c=CASE/'circuit.scs';results={}
    for label,name in [('gpc','MFCN'),('gnc','MMO')]:
        q=next(d for d in json.loads((CASE/'geometry.json').read_text())['devices'] if d['name']==name);nodes=' '.join(q['pins']);newnodes=nodes.replace(label,label+'_gate');cp=CASE/(label+'_probe.scs')
        cp.write_text(c.read_text().replace(f'{name} ({nodes})',f'PL ({label} {label}_gate) iprobe\n{name} ({newnodes})'))
        b=acbench(cp).replace('VTEST (vout vinn) vsource dc=0 mag=1','VTEST (vout vinn) vsource dc=0').replace('ac ac start=10 stop=100G dec=100','localstb stb start=1 stop=100G dec=100 probe=X.PL')
        run=run_spectre(50,label+'_stb',b,[cp,c,CASE/'sizing.json',CASE/'contract.json',Path(__file__).resolve()]);d=data(run,'localstb.stb');h=-d['loopGain'];m=loop_metrics(d['freq'],h,1);db=20*np.log10(abs(h));first=np.flatnonzero(db<0)[0]
        m.update(run_dir=str(run.relative_to(ROOT)),post_first_crossing_gain_db_max=float(max(db[first:])),op_output_difference_V=abs(dc(run)['vout']-json.loads((CASE/'latest_results.json').read_text())['dc_nodes']['vout']),probe='X.PL between '+label+' and '+label+'_gate, main unity feedback intact',min_PM_deg=45)
        log=run/'output/bench.log';native=re.search(r'Phase margin = ([0-9.]+) Deg',log.read_text())
        if native:
            m['spectre_native_phase_margin_deg']=float(native[1]);m['native_PM_difference_deg']=abs(float(native[1])-m['phase_margin_deg']);assert m['native_PM_difference_deg']<.02
        m['log_sha256']=sha(log)
        m['passes']=bool(m['phase_margin_deg']>=45 and m['falling_crossings']==1 and m['post_first_crossing_gain_db_max']<0 and m['op_output_difference_V']<1e-7);write_json(run/'measurements.json',m);results[label]=m
    r=json.loads((CASE/'latest_results.json').read_text());r['local_booster_loops']=results
    if not all(x['passes'] for x in results.values()):r['status']='partial';r['pass_tiers']={k:False for k in r['pass_tiers']};update_case(50,status='partial',nominal_complete=False)
    write_json(CASE/'latest_results.json',r);write_json(ROOT/r['run_dirs'][0]/'measurements.json',r);return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['static','full','loops'],default='full')
    for k,d in dict(branch=150,fold=250,output=900,cc=1.3,rz=1000,pcap=3,ncap=9,fold_ratio=1,pdrop=.35,ndrop=.25,rin=50,paux=20,naux=80).items():p.add_argument('--'+k.replace('_','-'),type=float,default=d)
    args=vars(p.parse_args());mode=args.pop('mode')
    if mode=='loops':print(json.dumps(local_loops(),indent=2));return
    update_case(50,status='running',nominal_complete=False);c=design(**args);deps=[c,CASE/'sizing.json',CASE/'contract.json',Path(__file__).resolve()];runs={}
    for label,fn in [('op_ac',acbench)]+([('noise',noisebench),('range',rangebench),('settling',settlebench)] if mode=='full' else []):
        b=fn(c);(CASE/f'testbench_{label}.scs').write_text(b);runs[label]=run_spectre(50,label,b,deps)
    r=extract(runs);print(json.dumps(dict(status=r['status'],values=r['values'],nodes=r['dc_nodes'],op_bad={k:v['headroom_V'] for k,v in r['operating_point'].items() if v['headroom_V']<0},runs=r['run_dirs']),indent=2))

if __name__=='__main__':main()
