"""Case07 PMOS-pass LDO; full TT27 supply/load and output-network matrix."""
from common import *
import argparse
import importlib.util
import shutil

CASE=ROOT/'cases/07-ldo-ota5';TASK=SOURCE/'sky130-ldo-ota5-robust-pvt-mc'


def design(tail_uA=100,input_gmid=18,mirror_gmid=8,pass_gmid=6,pass_m=30,buffer=False,mirror_L=.36,fvf=False,input_L=1,pinput=False,lag_C_pF=0,lag_R=50000):
    CASE.mkdir(parents=True,exist_ok=True)
    roles=dict(input=lut_size('n18',input_L,input_gmid,tail_uA*.5e-6,.9 if input_L==4 else .45),mirror=lut_size('p18',mirror_L,mirror_gmid,tail_uA*.5e-6,.9 if mirror_L==4 else .45),bias=lut_size('n18',1,14,50e-6,.2),pass_unit=lut_size('p18',.18,pass_gmid,1e-3,.45))
    if buffer or fvf:roles.update(buffer=lut_size('p18',.18,16,30e-6,.9),buffer_bias=lut_size('p18',1,10,10e-6,.45))
    if fvf:roles['buffer_driver']=lut_size('p18',.18,4,30e-6,.9)
    if pinput:
        roles['input']=lut_size('p18',input_L,input_gmid,tail_uA*.5e-6,.9 if input_L==4 else .45)
        roles['mirror']=lut_size('n18',mirror_L,mirror_gmid,tail_uA*.5e-6,.9 if mirror_L==4 else .45)
        roles['ptail']=lut_size('p18',1,16,10e-6,.2)
    c=CASE/'circuit.scs'
    def mos(name,nodes,role,m=1):
        q=roles[role];nunit=int(np.ceil(q['rounded_W_um']/100));return f'{name} ({nodes}) {q["model"]} w={q["rounded_W_um"]/nunit:g}u l={q["L_um"]:g}u m={m*nunit:g}\n'
    b='simulator lang=spectre\nsubckt ldo_ota5 (vin vout vss vref ibias fb gate_drive gate)\n'
    for name,nodes,role,m in [('MINP','nleft fb tail vss','input',1),('MINN','gate_drive vref tail vss','input',1),('MLOAD','nleft nleft vin vin','mirror',1),('MLOUT','gate_drive nleft vin vin','mirror',1),('MTAIL','tail ibias vss vss','bias',tail_uA/50),('MREF','ibias ibias vss vss','bias',1),('MPASS','vout gate vin vin','pass_unit',pass_m)]:b+=mos(name,nodes,role,m)
    if pinput:
        b=b.replace('fb tail vss','fb tail tail').replace('vref tail vss','vref tail tail').replace('nleft vin vin','nleft vss vss')
        b=re.sub(r'^MTAIL .*\n',mos('MTAIL','tail pbias vin vin','ptail',tail_uA/10),b,flags=re.M)
        b+=mos('MPTREF','pbias pbias vin vin','ptail')+mos('MNPT','pbias ibias vss vss','bias',.2)
    if buffer or fvf:
        b=b.replace('MINN (gate_drive','MINN (ampout').replace('MLOUT (gate_drive','MLOUT (ampout')
        if fvf:b+=mos('MSF','pbuf ampout gate_drive gate_drive','buffer')+mos('MBUF','gate_drive pbuf vin vin','buffer_driver')+mos('MNBUF','pbuf ibias vss vss','bias',.6)
        else:b+=mos('MSF','vss ampout gate_drive gate_drive','buffer')+mos('MBUF','gate_drive pbuf vin vin','buffer_bias',3)+mos('MPBUF','pbuf pbuf vin vin','buffer_bias')+mos('MNBUF','pbuf ibias vss vss','bias',.2)
    if lag_C_pF:
        b+=f'RLAG (ampout lag vss) rpposab_3t w=1u l={lag_R*(1-.0546)/311.3:g}u\nCLAG (lag vss) mim w=30u l=30u m={lag_C_pF/(.971e-3*900):g}\n'
    c.write_text(b+'ends ldo_ota5\n')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,tail_uA=tail_uA,pass_m=pass_m,buffer=buffer,fvf=fvf,pinput=pinput,lag_C_pF=lag_C_pF,lag_R_Ohm=lag_R,rationale='5T error amplifier, diode reference and PMOS pass; optional PMOS source follower/FVF isolates the pass gate capacitance. Legal units with m preserve model dimensions. LUT is initial sizing only; actual bias and load-dependent pass region checked.'))
    hashes={}
    for src in [TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',*sorted((TASK/'tests/benches').glob('*.spi'))]:
        name=str(src.relative_to(TASK));dst=CASE/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);hashes[name]=sha(src)
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_hashes=hashes,corner='tt',temperature_C=27,VDD_V=1.8,reference_V=.8,reference_A=50e-6,target_V=1.2,feedback_Ohm=[300e3,600e3],DC_supply_V=[1.62,1.8,1.98],DC_load_A=[.001,.01,.03],loop_nominal_supply_load_points=9,loop_network_extreme_points=8,network_extremes_at_V=1.8,network_cap_F=[.8e-6,1.2e-6],network_ESR_Ohm=[.02,.1],network_extreme_load_A=[.001,.03],nominal_cap_F=1e-6,nominal_ESR_Ohm=.05,dropout_sweep_V=[1.15,1.8,.002],dropout_load_A=.03,dropout_regulation_fraction=.99,loop='-V(gate_drive)/V(gate), differential series injection',loop_freq_Hz=[1,1e8],noise_band_Hz=[10,1e6],noise_load_A=.01,startup='0to1.8V ramp1to21us; Rload120ohm; observe70us',load_step='1to25to1mA,20us and40.2us starts,200ns edges',line_step='1.98to1.62to1.98V,20us and40.2us starts,200ns edges,10mA',settling_band_V=.015,transient_windows_s=[[20e-6,40.2e-6],[40.2e-6,65e-6]],scope_excludes=['otherprocesscorners','temperaturesotherthan27C','SS125networktransients','30process+mismatchruns','PEX']))
    return c


def prefix(c):return f'''simulator lang=spectre
include "{MODEL}" section=tt
include "{MODEL}" section=res_tt
include "{MODEL}" section=mim_tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-14
'''


def fixture(tag,vin=1.8,load=.01,cap=1e-6,esr=.05,kind='dc'):
    n=lambda name:name+tag
    vspec=f'dc={vin:g}'+(' mag=1' if kind=='psrr' else '')
    if kind=='startup':vspec='type=pwl wave=[0 0 1u 0 21u 1.8 70u 1.8]'
    if kind=='line':vspec='type=pwl wave=[0 1.98 20u 1.98 20.2u 1.62 40.2u 1.62 40.4u 1.98 70u 1.98]'
    if kind=='dropout':vspec='dc=supply'
    b=f'VIN{tag} ({n("vin")} 0) vsource {vspec}\nVREF{tag} ({n("vref")} 0) vsource dc=.8\nIBIAS{tag} ({n("vin")} {n("ibias")}) isource dc=50u\n'
    if kind=='startup':b+=f'RLOAD{tag} ({n("vout")} 0) resistor r=120\n'
    else:
        ispec='type=pwl wave=[0 .001 20u .001 20.2u .025 40.2u .025 40.4u .001 70u .001]' if kind=='load' else f'dc={load:g}'
        b+=f'ILOAD{tag} ({n("vout")} 0) isource {ispec}\n'
    b+='X'+tag+' ('+' '.join(n(x) if x!='0' else x for x in ['vin','vout','0','vref','ibias','fb','gate_drive','gate'])+') ldo_ota5\n'
    b+=f'RFBT{tag} ({n("vout")} {n("fb")}) resistor r=300k\nRFBB{tag} ({n("fb")} 0) resistor r=600k\nVLOOP{tag} ({n("gate_drive")} {n("gate")}) vsource dc=0'+(' mag=1' if kind=='loop' else '')+'\n'
    b+=f'RESR{tag} ({n("vout")} {n("vcap")}) resistor r={esr:g}\nCOUT{tag} ({n("vcap")} 0) capacitor c={cap:g}\n'
    b+='save '+' '.join(n(x) for x in ['vin','vout','fb','gate_drive','gate','ibias'])+f' VIN{tag}:p\n'
    return b


def matrixbench(c):
    b=prefix(c);points=[]
    for kind in ['dc','loop','psrr']:
        for iv,vin in enumerate([1.62,1.8,1.98]):
            for il,load in enumerate([.001,.01,.03]):
                tag=f'{kind[0].upper()}{iv}{il}';points.append(dict(kind=kind,tag=tag,vin=vin,load=load,cap=1e-6,esr=.05));b+=fixture(tag,vin,load,kind=kind)
    for ic,cap in enumerate([.8e-6,1.2e-6]):
        for ie,esr in enumerate([.02,.1]):
            for il,load in enumerate([.001,.03]):
                tag=f'E{ic}{ie}{il}';points.append(dict(kind='loop',tag=tag,vin=1.8,load=load,cap=cap,esr=esr));b+=fixture(tag,1.8,load,cap,esr,'loop')
    devices=re.findall(r'^(M\w+) ',c.read_text(),re.M)
    for tag in ['D00','D02','D11']:
        b+='save '+' '.join(f'X{tag}.{name}:{field}' for name in devices for field in ['ids','gm','gds','vds','vdsat','vgs'])+'\n'
        b+='save '+' '.join(f'X{tag}.{name}' for name in ['nleft','tail']+(['ampout','pbuf'] if 'MSF' in devices else []))+'\n'
    write_json(CASE/'matrix_points.json',points);return b+'dcOp dc\nac ac start=1 stop=100M dec=100\n'


def source_verifier():
    spec=importlib.util.spec_from_file_location('case07_verifier',CASE/'source/tests/verify.py');v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v);return v


def rawplot(v,kind,q,tag=''):
    names=['frequency' if 'freq' in q else 'time'];keys=['freq' if 'freq' in q else 'time']
    for key in ['vin','vout','gate_drive','gate']:
        if key+tag in q:names.append('v('+key+')');keys.append(key+tag)
    return v.RawPlot(kind,names,[[complex(x) for x in row] for row in zip(*(q[k] for k in keys))])


def extract_matrix(run):
    v=source_verifier();a=data(run,'ac.ac');op=dc(run);pts=json.loads((run/'inputs/matrix_points.json').read_text());rows=[]
    for pt in pts:
        tag=pt['tag']
        if pt['kind']=='dc':vals=dict(vout_V=op['vout'+tag],output_error_V=abs(op['vout'+tag]-1.2),Iq_A=abs(op['VIN'+tag+':p'])-pt['load'])
        else:vals=v.analyze(pt['kind'],[rawplot(v,pt['kind'],a,tag)],1.2)
        rows.append(dict(**pt,values=vals))
    values=dict(dc_error_V=max(q['values']['output_error_V'] for q in rows if q['kind']=='dc'),Iq_A=max(q['values']['Iq_A'] for q in rows if q['kind']=='dc'),min_Iq_A=min(q['values']['Iq_A'] for q in rows if q['kind']=='dc'))
    for key in ['dc_loop_gain_db','loop_ugb_hz','phase_margin_deg']:values[key]=min(q['values'][key] for q in rows if q['kind']=='loop')
    for key in ['psrr_100hz_db','psrr_1khz_db','psrr_100khz_db','psrr_1mhz_db']:values[key]=min(q['values'][key] for q in rows if q['kind']=='psrr')
    r=dict(case_slot=7,generated_at=now(),run_dirs=[str(run.relative_to(ROOT))],status='partial',values=values,matrix=rows,all_nominal_checks_complete=False)
    write_json(CASE/'latest_results.json',r);write_json(run/'measurements.json',r);update_case(7,status='partial',nominal_complete=False,latest_run=r['run_dirs'][0],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r


def stb_matrix(c):
    pts=[q for q in json.loads((CASE/'matrix_points.json').read_text()) if q['kind']=='loop'];b=prefix(c)
    for q in pts:
        tag=q['tag'];part=fixture(tag,q['vin'],q['load'],q['cap'],q['esr'])
        b+=part.replace(f'VLOOP{tag} (gate_drive{tag} gate{tag}) vsource dc=0',f'PROBE{tag} (gate_drive{tag} gate{tag}) iprobe')
    b+='dcOp dc\n'
    for q in pts:b+=f'stb{q["tag"]} stb start=1 stop=100M dec=100 probe=PROBE{q["tag"]}\n'
    run=run_spectre(7,'stb_matrix',b,[c,CASE/'sizing.json',CASE/'contract.json',CASE/'matrix_points.json',Path(__file__).resolve()]);rows=[]
    for pt in pts:
        a=data(run,'stb'+pt['tag']+'.stb');lm=loop_metrics(a['freq'],-a['loopGain'],1);rows.append(dict(**pt,values=lm))
    result=dict(run_dir=str(run.relative_to(ROOT)),matrix=rows,minimum_phase_margin_deg=min(q['values']['phase_margin_deg'] for q in rows),minimum_ugb_Hz=min(q['values']['ugb_hz'] for q in rows))
    write_json(run/'diagnostics.json',result);write_json(CASE/'stb_diagnostic.json',result);return result


def extra_checks(c):
    deps=[c,CASE/'sizing.json',CASE/'contract.json',Path(__file__).resolve(),CASE/'source/tests/verify.py']
    b=prefix(c)+'parameters supply=1.8\n'+fixture('D',load=.03,kind='dropout')+fixture('N',load=.01)
    b+='dropout dc param=supply start=1.15 stop=1.8 step=.002\nnoise (voutN 0) noise iprobe=VINN start=10 stop=1M dec=100\n'
    (CASE/'bench_extra.scs').write_text(b);static=run_spectre(7,'dropout_noise',b,deps)
    b=prefix(c)
    for kind,tag in [('startup','S'),('load','T'),('line','L')]:b+=fixture(tag,kind=kind)
    b+='tran tran stop=70u maxstep=2n strobeperiod=5n strobeoutput=strobeonly errpreset=conservative\n'
    (CASE/'bench_transient.scs').write_text(b);tr=run_spectre(7,'transient',b,deps)
    return static,tr


def extract_full(matrix,stb,extra):
    v=source_verifier();r=matrix.copy();vals=r['values'].copy();static,tr=extra
    d=data(static,'dropout.dc');n=data(static,'noise.noise',required=('out',));t=data(tr,'tran.tran')
    detail={}
    detail['dropout']=v.analyze('dropout',[rawplot(v,'DC',dict(time=d['supply'],vin=d['vinD'],vout=d['voutD']))],1.2)
    pn=v.RawPlot('Noise Spectral Density',['frequency','onoise_spectrum'],[[complex(f),complex(o)] for f,o in zip(n['freq'],n['out'])])
    detail['noise']=v.analyze('noise',[pn],1.2)
    for kind,tag in [('startup','S'),('load_tran','T'),('line_tran','L')]:detail[kind]=v.analyze(kind,[rawplot(v,'Transient Analysis',t,tag)],1.2,.015)
    vals['dropout_V']=detail['dropout']['dropout_v'];vals['noise_Vrms']=detail['noise']['output_noise_rms_v']
    vals.update(detail['startup'])
    for kind in ['load','line']:
        vals[kind+'_excursion_V']=detail[kind+'_tran']['excursion_v'];vals[kind+'_settling_s']=detail[kind+'_tran']['settling_time_s']
    vals['stb_phase_margin_deg']=stb['minimum_phase_margin_deg'];vals['stb_ugb_Hz']=stb['minimum_ugb_Hz']
    specs=[('dc_error_V',.02,'max','V','linear'),('Iq_A',200e-6,'max','A','linear'),('min_Iq_A',0,'min','A','linear'),('dc_loop_gain_db',40,'min','dB','amplitude_db'),('loop_ugb_hz',50e3,'min','Hz','linear'),('phase_margin_deg',60,'min','deg','phase_margin'),('psrr_100hz_db',40,'min','dB','amplitude_db'),('psrr_1khz_db',40,'min','dB','amplitude_db'),('psrr_100khz_db',20,'min','dB','amplitude_db'),('psrr_1mhz_db',10,'min','dB','amplitude_db'),('dropout_V',.25,'max','V','linear'),('noise_Vrms',150e-6,'max','Vrms','linear'),('startup_t90_s',30e-6,'max','s','linear'),('startup_settling_after_ramp_s',10e-6,'max','s','linear'),('startup_overshoot_v',.05,'max','V','linear'),('load_excursion_V',.02,'max','V','linear'),('line_excursion_V',.02,'max','V','linear'),('load_settling_s',5e-6,'max','s','linear'),('line_settling_s',5e-6,'max','s','linear'),('stb_phase_margin_deg',60,'min','deg','phase_margin'),('stb_ugb_Hz',50e3,'min','Hz','linear')]
    valid=all(np.isfinite(z) for z in vals.values());gates={key:gate(vals[key],limit,sense,unit,kind) for key,limit,sense,unit,kind in specs if np.isfinite(vals[key])}
    tiers={tier:bool(valid and len(gates)==len(specs) and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']};tier=next((x for x in tiers if tiers[x]),None)
    op=dc(ROOT/matrix['run_dirs'][0]);devices=re.findall(r'^(M\w+) ',(CASE/'circuit.scs').read_text(),re.M);ops={}
    for tag in ['D00','D02','D11']:
        ops[tag]={}
        for dev in devices:
            z={field:op.get('X'+tag+'.'+dev+':'+field) for field in ['ids','gm','gds','vds','vdsat','vgs']}
            z.update(gmid=abs(z['gm']/z['ids']),headroom_V=abs(z['vds'])-abs(z['vdsat']));ops[tag][dev]=z
    vals={k:z if np.isfinite(z) else None for k,z in vals.items()}
    r.update(generated_at=now(),status='complete_'+tier if tier else 'partial',values=vals,gates=gates,pass_tiers=tiers,measurement_detail=detail,stb_diagnostic=stb,operating_point=ops,all_nominal_checks_complete=True,model_dimensions_valid=True,nonrelaxable_guards_pass=valid,source_verifier_sha256=sha(CASE/'source/tests/verify.py'),run_dirs=matrix['run_dirs']+[stb['run_dir']]+[str(p.relative_to(ROOT)) for p in extra],scope='SMIC18 TT27 only; full 9 supply/load, 17 loop/output-network, 9 PSRR, 30mA dropout, noise, startup, load and line steps; supplementary true-loop STB. Other process/temperature/mismatch and SS125 output-network transients excluded.')
    write_json(CASE/'latest_results.json',r);write_json(ROOT/matrix['run_dirs'][0]/'measurements.json',r)
    update_case(7,status=r['status'],nominal_complete=bool(tier),case_dir=str(CASE.relative_to(ROOT)),results=str((CASE/'latest_results.json').relative_to(ROOT)),run_dirs=r['run_dirs'])
    return r


def main():
    p=argparse.ArgumentParser()
    for name,default in [('tail_uA',100),('input_gmid',18),('mirror_gmid',8),('pass_gmid',6),('pass_m',30),('mirror_L',.36),('input_L',1),('lag_C_pF',0),('lag_R',50000)]:p.add_argument('--'+name.replace('_','-'),type=float,default=default)
    p.add_argument('--buffer',action='store_true')
    p.add_argument('--fvf',action='store_true')
    p.add_argument('--pinput',action='store_true')
    p.add_argument('--stb',action='store_true');p.add_argument('--full',action='store_true');p.add_argument('--extract');a=p.parse_args()
    if a.extract:run=ROOT/a.extract
    else:
        args=vars(a).copy();args.pop('extract');args.pop('stb');args.pop('full');c=design(**args);b=matrixbench(c);(CASE/'bench_matrix.scs').write_text(b);update_case(7,status='running',nominal_complete=False)
        run=run_spectre(7,'matrix',b,[c,CASE/'sizing.json',CASE/'contract.json',CASE/'matrix_points.json',Path(__file__).resolve()])
    r=extract_matrix(run);print(json.dumps(r['values'],indent=2))
    if a.stb or a.full:
        sd=stb_matrix(CASE/'circuit.scs');print(json.dumps({k:v for k,v in sd.items() if k!='matrix'},indent=2))
    if a.full:
        r=extract_full(r,sd,extra_checks(CASE/'circuit.scs'));print(json.dumps(dict(status=r['status'],values=r['values']),indent=2))

if __name__=='__main__':main()
