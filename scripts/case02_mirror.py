"""Nominal four-code programmable current sink with all external checks."""
from common import *
from hd_cells import extract_hd
import argparse
CASE=ROOT/'cases/02-mirror'
WEIGHTS=[(16,4),(12,8),(8,12),(4,16)]
STIMULI={'nom':(50,50),'icup':(55,50),'icdn':(45,50),'ptup':(50,55),'ptdn':(50,45)}

def design(rtop=210000,rbot=50000):
    CASE.mkdir(parents=True,exist_ok=True)
    roles={'reference':lut_size('n18',1,16,50e-6,.2),
           'cascode':lut_size('n18',.36,18,1e-3,.2),
           'cascode_bias':lut_size('n18',.36,18,5e-6,.2),
           'selector':lut_size('n18',.18,8,1e-3,.2)}
    w={k:v['rounded_W_um'] for k,v in roles.items()}
    hd=extract_hd(['INHDV0','NOR2HDV0'],CASE)
    lines=['// Analog devices from target SMIC18 gm/ID LUT; exact HD decode cells.',
      'simulator lang=spectre','subckt programmable_current_mirror (vss vdd icc_ref iptat_ref ratio_b0 ratio_b1 iout)',
      f'MICC (icc_ref icc_ref vss vss) n18 w={w["reference"]}u l=1u',
      f'MPTAT (iptat_ref iptat_ref vss vss) n18 w={w["reference"]}u l=1u',
      'XNB0 (ratio_b0 nb0 vdd vss vdd vss) INHDV0',
      'XNB1 (ratio_b1 nb1 vdd vss vdd vss) INHDV0']
    controls=[('ratio_b0','ratio_b1'),('nb0','ratio_b1'),('ratio_b0','nb1'),('nb0','nb1')]
    for code,((ic,pt),(b0,b1)) in enumerate(zip(WEIGHTS,controls)):
        lines += [f'XSEL{code} ({b0} {b1} sel{code} vdd vss vdd vss) NOR2HDV0',
          f'MIC{code} (pre{code} icc_ref vss vss) n18 w={w["reference"]:.6f}u l=1u m={ic}',
          f'MPT{code} (pre{code} iptat_ref vss vss) n18 w={w["reference"]:.6f}u l=1u m={pt}',
          f'MSW{code} (isum sel{code} pre{code} vss) n18 w={w["selector"]}u l=.18u']
    lines += [f'MCASC (iout vcb isum vss) n18 w={w["cascode_bias"]}u l=.36u m=200',
      f'MBC (vcb vcb vb vss) n18 w={w["cascode_bias"]}u l=.36u',
      f'RTOP (vdd vcb) resistor r={rtop}',f'RBOT (vb vss) resistor r={rbot}',
      'ends programmable_current_mirror']
    p=CASE/'circuit.scs';p.write_text('\n'.join(lines)+'\n')
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,weight_pairs=WEIGHTS,rtop_ohm=rtop,rbot_ohm=rbot,implementation=dict(mirror_unit_W_um=w['reference'],mirror_multiplicities=WEIGHTS,cascode_unit_W_um=w['cascode_bias'],cascode_multiplicity=200,model_max_unit_width_um=100),
      rationale='Same-unit mirrors and shared wide-swing cascode; integer m values preserve reference W/L and keep unit dimensions in model range. Cascode diode replica at 5uA with source resistor targets low internal drain voltage. Selector gm/ID point supplies an initial width; selected switches intentionally operate in triode, with actual Ron reported. HD decoder is unmodified vendor CDL.'))
    write_json(CASE/'contract.json',dict(source_task='sky130-programmable-icc-iptat-current-mirror-pvt',corner='tt',VDD_V=1.8,temperature_C=27,weights=WEIGHTS,reference_currents_A=[50e-6,50e-6],weight_perturbation_A=5e-6,output_voltage_nominal_V=.9,output_voltage_range_V=[.45,1.6],compliance_uniform_points=41,rout_difference_V=[.895,.905],reference_pin_range_V=[.2,1.1],reference_pin_limits_relaxed=False,auxiliary_supply_excludes='both forced input references and forced output current',limits=dict(output_error=.08,weight_error=.1,ratio_error=.1,reference_isolation_perturbation_V=.025,reference_isolation_code_V=.05,auxiliary_current_A=100e-6,digital_current_A=1e-6,compliance_error=.03,rout_Ohm=100e3)))
    return p,hd

def bench(p,hd):
    lines=['simulator lang=spectre','global 0','parameters vtest=.9',f'include "{MODEL}" section=tt',f'include "{hd}"',f'include "{p}"',
       'simulatorOptions options temp=27 tnom=27 reltol=1e-7 vabstol=1e-10 iabstol=1e-15','saveOptions options save=selected']
    for code in range(4):
        for stim,(ic,pt) in STIMULI.items():
            n=f'c{code}_{stim}'
            lines += [f'VS_{n} (vdd_{n} 0) vsource dc=1.8',
              f'IC_{n} (vdd_{n} icc_{n}) isource dc={ic}u',f'IP_{n} (vdd_{n} iptat_{n}) isource dc={pt}u',
              f'VB0_{n} (b0_{n} 0) vsource dc={1.8*(code&1)}',f'VB1_{n} (b1_{n} 0) vsource dc={1.8*((code>>1)&1)}',
              f'VO_{n} (out_{n} 0) vsource dc='+('vtest' if stim=='nom' else '.9'),
              f'X{n} (0 vdd_{n} icc_{n} iptat_{n} b0_{n} b1_{n} out_{n}) programmable_current_mirror',
              f'save icc_{n} iptat_{n} VO_{n}:p VS_{n}:p VB0_{n}:p VB1_{n}:p']
        for dev in ['MICC',f'MIC{code}',f'MPT{code}','MCASC',f'MSW{code}','MBC']:
            lines.append(f'save Xc{code}_nom.{dev}:ids Xc{code}_nom.{dev}:gm Xc{code}_nom.{dev}:gds Xc{code}_nom.{dev}:vgs Xc{code}_nom.{dev}:vds Xc{code}_nom.{dev}:vdsat Xc{code}_nom.{dev}:region')
        lines.append(f'save Xc{code}_nom.vcb Xc{code}_nom.vb Xc{code}_nom.isum Xc{code}_nom.pre{code}')
    lines+=['dcOp dc','compliance dc param=vtest start=.45 stop=1.6 step=.02875','rout dc param=vtest start=.89 stop=.91 step=.005']
    return '\n'.join(lines)+'\n'

def extract(run):
    o=dc(run);cs=data(run,'compliance.dc');rt=data(run,'rout.dc')
    vf=cs['vtest'];vr=rt['vtest'];assert len(vf)==41 and np.allclose(vf,np.linspace(.45,1.6,41),rtol=0,atol=1e-12)
    points=[];op={}
    for code,(wtic,wtpt) in enumerate(WEIGHTS):
        curr=lambda stim:-o[f'VO_c{code}_{stim}:p']
        vic=lambda stim:o[f'icc_c{code}_{stim}'];vpt=lambda stim:o[f'iptat_c{code}_{stim}']
        acc=(curr('icup')-curr('icdn'))/10e-6;aptat=(curr('ptup')-curr('ptdn'))/10e-6
        iout=curr('nom');i_sweep=-cs[f'VO_c{code}_nom:p'];i_fine=-rt[f'VO_c{code}_nom:p']
        rout=.01/(np.interp(.905,vr,i_fine)-np.interp(.895,vr,i_fine))
        points.append(dict(code=f'{code:02b}',iout_A=iout,acc=acc,aptat=aptat,ratio=acc/aptat,output_error=abs(iout/.001-1),weight_error=max(abs(acc/wtic-1),abs(aptat/wtpt-1)),ratio_error=abs((acc/aptat)/(wtic/wtpt)-1),reference_min_V=min([vic(s) for s in STIMULI]+[vpt(s) for s in STIMULI]),reference_max_V=max([vic(s) for s in STIMULI]+[vpt(s) for s in STIMULI]),vic_nom_V=vic('nom'),vpt_nom_V=vpt('nom'),isolation_perturbation_V=max(abs(vpt('icup')-vpt('nom')),abs(vpt('icdn')-vpt('nom')),abs(vic('ptup')-vic('nom')),abs(vic('ptdn')-vic('nom'))),auxiliary_current_A=abs(-o[f'VS_c{code}_nom:p']-100e-6),digital_current_A=max(abs(o[f'VB0_c{code}_nom:p']),abs(o[f'VB1_c{code}_nom:p'])),compliance_error=float(max(abs(i_sweep/iout-1))),rout_Ohm=float(rout),minimum_output_A=min([curr(s) for s in STIMULI]+list(i_sweep))))
        op[str(code)]={}
        for dev in ['MICC',f'MIC{code}',f'MPT{code}','MCASC',f'MSW{code}','MBC']:
            vals={k.split(':')[1]:v for k,v in o.items() if k.startswith(f'Xc{code}_nom.{dev}:')}
            vals['gmid']=abs(vals['gm']/vals['ids']);vals['headroom_V']=abs(vals['vds'])-abs(vals['vdsat'])
            if dev.startswith('MSW'):vals['Ron_Ohm']=abs(vals['vds']/vals['ids'])
            op[str(code)][dev]=vals
    vicmean=np.mean([p['vic_nom_V'] for p in points]);vptmean=np.mean([p['vpt_nom_V'] for p in points])
    for p in points:p['isolation_code_V']=max(abs(p['vic_nom_V']-vicmean),abs(p['vpt_nom_V']-vptmean))
    definitions=[('output_error',.08,'max','fraction'),('weight_error',.1,'max','fraction'),('ratio_error',.1,'max','fraction'),('isolation_perturbation_V',.025,'max','V'),('isolation_code_V',.05,'max','V'),('auxiliary_current_A',100e-6,'max','A'),('digital_current_A',1e-6,'max','A'),('compliance_error',.03,'max','fraction'),('rout_Ohm',100e3,'min','ohm')]
    gates={};values={}
    for name,limit,sense,unit in definitions:
        worst=(max if sense=='max' else min)(points,key=lambda p:p[name]);values[name]=worst[name];g=gate(worst[name],limit,sense,unit);g['worst_code']=worst['code'];gates[name]=g
    headroom=all(p['reference_min_V']>=.2 and p['reference_max_V']<=1.1 for p in points);positive=all(p['minimum_output_A']>0 for p in points)
    logic=all(o[f'Xc{i}_nom.pre{i}']>0 for i in range(4))
    tiers={t:bool(headroom and positive and logic and all(g['passes'][t] for g in gates.values())) for t in ['original','10pct','15pct']};tier=next((t for t in tiers if tiers[t]),None)
    report=dict(case_slot=2,generated_at=now(),run_dir=str(run.relative_to(ROOT)),status='complete_'+tier if tier else 'partial',values=values,gates=gates,points=points,operating_point=op,dc_nodes={k:v for k,v in o.items() if ':' not in k},reference_headroom_valid=headroom,output_positive=positive,all_nominal_checks_complete=True,pass_tiers=tiers,scope='All four static codes, all +/-5uA reference perturbations, full 41-point output range; SMIC18 tt 27C 1.8V only')
    write_json(run/'measurements.json',report);write_json(CASE/'latest_results.json',report);update_case(2,status=report['status'],nominal_complete=bool(tier),latest_run=report['run_dir'],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--rtop',type=float,default=210000);p.add_argument('--rbot',type=float,default=50000);p.add_argument('--extract');a=p.parse_args()
    if a.extract:run=ROOT/a.extract
    else:
        c,h=design(a.rtop,a.rbot);b=bench(c,h);(CASE/'testbench.scs').write_text(b);update_case(2,status='running',nominal_complete=False)
        run=run_spectre(2,'mirror',b,[c,h,CASE/'hd_cells_manifest.json',CASE/'sizing.json',CASE/'contract.json'])
    r=extract(run);print(json.dumps({k:r[k] for k in ['status','values','points']},indent=2))
if __name__=='__main__':main()
