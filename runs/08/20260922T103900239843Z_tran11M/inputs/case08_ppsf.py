"""Capacitively coupled, bootstrapped push-pull source follower; nominal."""
from common import *
import argparse
import importlib.util
import shutil

CASE=ROOT/'cases/08-ppsf';TASK=SOURCE/'sky130-buf-ppsf-bs-gain1-sfdr90'


def design(mult=6,gmid=18,cap_pF=5,drop=.18,L=.36):
    CASE.mkdir(parents=True,exist_ok=True);sources={}
    for p in [TASK/'instruction.md',TASK/'solution/circuit.spi',TASK/'tests/verify.py',TASK/'tests/utils.py',*sorted((TASK/'tests/benches').glob('*'))]:
        rel=str(p.relative_to(TASK));dest=CASE/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);sources[rel]=sha(p)
    roles={name:lut_size(model,length,gm,20e-6,vds) for name,model,length,gm,vds in [('n_in','n18',L,gmid,.45),('p_in','p18',L,gmid,.45),('n_cas','n18',L,14,.45),('p_cas','p18',L,14,.45),('n_bias','n18',1,14,.45),('p_bias','p18',1,12,.45)]}
    lines=['simulator lang=spectre','subckt buf_ppsf_bs (IREF VCM VDD VIN VIP VON VOP VSS)'];geo=[]
    def mos(name,pins,role,m=1):
        q=roles[role];w=q['rounded_W_um'];assert w<=100
        lines.append(f'{name} ({pins}) {q["model"]} w={w:g}u l={q["L_um"]:g}u m={m:g}');geo.append(dict(name=name,pins=pins.split(),role=role,W_unit_um=w,L_um=q['L_um'],m=m))
    mos('MREF','IREF IREF VSS VSS','n_bias');mos('MBN','pb IREF VSS VSS','n_bias');mos('MBP','pb pb VDD VDD','p_bias')
    for tag in ['1','2']:
        mos('MPBN'+tag,'VBN'+tag+' pb VDD VDD','p_bias');mos('MNBN'+tag,'VBN'+tag+' VBN'+tag+' '+('VCM VCM' if tag=='1' else 'nbs nbs'),'n_in' if tag=='1' else 'n_cas')
        mos('MNBP'+tag,'VBP'+tag+' IREF VSS VSS','n_bias');mos('MPBP'+tag,'VBP'+tag+' VBP'+tag+' '+('VCM VCM' if tag=='1' else 'pbs pbs'),'p_in' if tag=='1' else 'p_cas')
    lines+=['RNB (nbs VCM) resistor r='+str(drop/20e-6),'RPB (VCM pbs) resistor r='+str(drop/20e-6)]
    for side,vin,vout in [('P','VIP','VOP'),('N','VIN','VON')]:
        mos('MIN'+side,f'nd{side} gn{side} {vout} {vout}','n_in',mult);mos('MCN'+side,f'VDD gcn{side} nd{side} nd{side}','n_cas',mult)
        mos('MIP'+side,f'pd{side} gp{side} {vout} {vout}','p_in',mult);mos('MCP'+side,f'VSS gcp{side} pd{side} pd{side}','p_cas',mult)
        for gate,bias,node in [('gn','VBN1',vin),('gp','VBP1',vin),('gcn','VBN2',vout),('gcp','VBP2',vout)]:
            lines+=[f'R{gate}{side} ({bias} {gate}{side}) resistor r=1Meg',f'C{gate}{side} ({gate}{side} {node}) capacitor c={cap_pF:g}p']
    lines.append('ends buf_ppsf_bs');c=CASE/'circuit.scs';c.write_text('\n'.join(lines)+'\n')
    write_json(CASE/'sizing.json',dict(roles=roles,mult=mult,gmid=gmid,cap_pF=cap_pF,drop_V=drop,L_um=L,rationale='20uA replica units derive follower VGS from VCM. Current-derived resistive drops set bootstrapped cascode headroom; 1Meg biases/5pF input/output bootstrap preserve DC isolation. All MOS bodies follow own sources and therefore require isolated wells in future layout.'))
    write_json(CASE/'geometry.json',dict(devices=geo,circuit_sha256=sha(c),all_unit_widths_valid=True))
    write_json(CASE/'contract.json',dict(source_task=TASK.name,source_hashes=sources,corner='tt',VDD_V=1.8,temperature_C=27,reference_A=20e-6,VCM_V=.9,load_each_F=1e-12,ac=dict(start_Hz=1e6,stop_Hz=40e6,dec=100,differential_amplitude_V=.8,gain_min_VV=.99,input_current_gate_A=20e-6,input_current_gate_relaxable=False),power_W_max=.001,power_ports=['VDD','VCM','VIN','VIP'],dynamic=dict(frequency_Hz=[1e6,11e6,41e6],differential_peak_V=.8,input_transient_offset_V=0,input_DC_analysis_offset_V=.9,stop_s=50e-6,window_s=[49e-6,50e-6],uniform_points=1000,sample_step_s=1e-9,SFDR_min_dB=[90,80,70],fundamental_gain_min=.95,full_Nyquist=True,Nyquist_included=True),nominal_only=True,excluded=['otherfourprocesscorners','otherVDD/temperatures','randommismatch','PEX']))
    return c


def bench(c,freq=None):
    b=f'''simulator lang=spectre
include "{MODEL}" section=tt
include "{c}"
simulatorOptions options temp=27 tnom=27 reltol=1e-6 vabstol=1e-9 iabstol=1e-14
VDD (vdd 0) vsource dc=1.8
VCM (vcm 0) vsource dc=.9
IREF (vdd iref) isource dc=20u
X (iref vcm vdd vin vip von vop 0) buf_ppsf_bs
CLP (vop 0) capacitor c=1p
CLN (von 0) capacitor c=1p
save vop von vip vin VDD:p VCM:p VIP:p VIN:p X.VBN1 X.VBN2 X.VBP1 X.VBP2 X.ndP X.pdP
'''
    for name,phase in [('VIP',0),('VIN',180)]:
        b+=f'{name} ({name.lower()} 0) vsource dc=.9 '+(f'type=sine sinedc=0 ampl=.4 freq={freq:g} sinephase={phase}' if freq else f'mag=.4 phase={phase}')+'\n'
    if freq:return b+'tran tran stop=50u maxstep=100p strobeperiod=1n strobeoutput=strobeonly errpreset=conservative\n'
    for q in json.loads((CASE/'geometry.json').read_text())['devices']:b+='save '+' '.join(f'X.{q["name"]}:{k}' for k in ['ids','gm','gds','vds','vdsat','vgs'])+'\n'
    return b+'dcOp dc\nac ac start=1M stop=40M dec=100\n'


def original_verifier():
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('case08_original',CASE/'source/tests/verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v


def extract(runs):
    a=data(runs[0],'ac.ac');o=dc(runs[0]);h=abs(a['vop']-a['von'])/.8
    vals=dict(gain_min_VV=float(min(h)),gain_1MHz_VV=float(h[0]),gain_40MHz_VV=float(h[-1]),input_current_40MHz_A=float(abs(a['VIP:p'][-1]-a['VIN:p'][-1])),power_W=sum(abs(o['VDD:p']*1.8) if p=='VDD' else abs(o[p+':p']*.9) for p in ['VDD','VCM','VIN','VIP']))
    specs=[('gain_min_VV',.99,'min','V/V','linear'),('power_W',.001,'max','W','linear')];op={}
    for q in json.loads((CASE/'geometry.json').read_text())['devices']:
        z={k:o[f'X.{q["name"]}:{k}'] for k in ['ids','gm','gds','vds','vdsat','vgs']};z.update(gmid=abs(z['gm']/z['ids']),headroom_V=abs(z['vds'])-abs(z['vdsat']));op[q['name']]=z
    verifier=original_verifier();detail=[]
    for run,f,lim in zip(runs[1:],[1e6,11e6,41e6],[90,80,70]):
        d=data(run,'tran.tran');path=run/'dynamic.dat';sel=(d['time']>=48.999e-6)&(d['time']<=50e-6)
        with path.open('w') as out:
            for tt,p,n in zip(d['time'][sel],d['vop'][sel],d['von'][sel]):out.write(f'{tt:.12e} {p:.17g} {tt:.12e} {n:.17g}\n')
        gain,sfdr=verifier.dynamic_metrics(path,f);tag=str(int(f/1e6));vals['gain_'+tag+'MHz_VV']=gain;vals['SFDR_'+tag+'MHz_dB']=sfdr
        specs += [('gain_'+tag+'MHz_VV',.95,'min','V/V','linear'),('SFDR_'+tag+'MHz_dB',lim,'min','dB','amplitude_db')];detail.append(dict(frequency_Hz=f,samples=len(d['time']),source_function='dynamic_metrics',data_sha256=sha(path)))
    gates={k:gate(vals[k],lim,sense,unit,kind) for k,lim,sense,unit,kind in specs};gates['input_current_40MHz_A']=gate(vals['input_current_40MHz_A'],20e-6,'max','A',relax=False)
    for key,g in gates.items():g['passes']={tier:g['value']>lim if g['sense']=='min' else g['value']<lim for tier,lim in g['limits'].items()}
    complete=len(runs)==4;tiers={tier:bool(complete and all(g['passes'][tier] for g in gates.values())) for tier in ['original','10pct','15pct']};tier=next((x for x in tiers if tiers[x]),None)
    r=dict(case_slot=8,status='complete_'+tier if tier else 'partial',generated_at=now(),values=vals,gates=gates,pass_tiers=tiers,operating_point=op,dc_nodes={k:z for k,z in o.items() if ':' not in k},all_nominal_checks_complete=complete,model_dimensions_valid=True,measurement_detail=detail,run_dirs=[str(p.relative_to(ROOT)) for p in runs],scope='SMIC18 TT27 at1.8V only; strict nonrelaxable input-current gate; all1–40MHzAC samples and three fullNyquist rectangular spectra when complete.')
    write_json(CASE/'latest_results.json',r);write_json(runs[0]/'measurements.json',r);update_case(8,status=r['status'],nominal_complete=bool(tier),case_dir=str(CASE.relative_to(ROOT)),results=str((CASE/'latest_results.json').relative_to(ROOT)),run_dirs=r['run_dirs']);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true')
    for key,default in [('mult',6),('gmid',18),('cap_pF',5),('drop',.18),('L',.36)]:p.add_argument('--'+key.replace('_','-'),type=float,default=default)
    args=vars(p.parse_args());full=args.pop('full');c=design(**args);update_case(8,status='running',nominal_complete=False);deps=[c,CASE/'sizing.json',CASE/'contract.json',CASE/'geometry.json',Path(__file__).resolve()];runs=[]
    for f in [None]+([1e6,11e6,41e6] if full else []):
        b=bench(c,f);runs.append(run_spectre(8,'ac' if not f else f'tran{int(f/1e6)}M',b,deps))
    r=extract(runs);print(json.dumps(dict(status=r['status'],values=r['values'],op={k:z for k,z in r['operating_point'].items() if k in ['MINP','MIPP','MCNP','MCPP']}),indent=2))

if __name__=='__main__':main()
