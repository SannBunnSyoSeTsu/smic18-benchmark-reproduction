"""Replica-biased PLL charge pump: nominal DC and full pulse contract."""
from common import *
from hd_cells import extract_hd
from case16_miller import prefix
import argparse

CASE=ROOT/'cases/47-charge-pump'
OP_DEVICES=['MN0','MN2','MPCB','MP2X','MNCB','MP0','MPC0','MNC1','MN1','MPM','MPC','MSUP','MSDU','MNWU','MNM','MNC','MSDN','MSDD','MNWD']

def design(ncb_gmid=4.5,pcb_gmid=4.5,n_ratio=4,p_ratio=10,psw_uA=50,nsw_uA=50,up_cell='INHDV8',upd_cell='INHDV2',dn_cell='INHDV4',cnode_fF=30):
    CASE.mkdir(parents=True,exist_ok=True)
    hd=extract_hd([up_cell,upd_cell,dn_cell],CASE)
    roles={
        'n_mirror_unit':lut_size('n18',4,12,12.5e-6,.9),
        'p_mirror_unit':lut_size('p18',4,12,5e-6,.9),
        'n_cascode_unit':lut_size('n18',1,16,12.5e-6,.45),
        'p_cascode_unit':lut_size('p18',1,16,12.5e-6,.45),
        'n_cascode_bias':lut_size('n18',4,ncb_gmid,12.5e-6,.9),
        'p_cascode_bias':lut_size('p18',4,pcb_gmid,12.5e-6,.9),
        'n_switch':lut_size('n18',.18,8,nsw_uA*1e-6,.9),
        'p_switch':lut_size('p18',.18,8,psw_uA*1e-6,.9),
        'up_dummy_diode':lut_size('n18',1,3.5,50e-6,.9),
        'dn_dummy_follower':lut_size('n18',1,5,50e-6,.9),
    }
    def m(name,nodes,role,mult=1):
        q=roles[role]
        return f"{name} ({nodes}) {q['model']} w={q['rounded_W_um']:g}u l={q['L_um']:g}u m={mult:g}\n"
    b='// Current steering charge pump; only PDK MOS and bias capacitors in DUT.\nsimulator lang=spectre\nsubckt pll_charge_pump (vss iref up dn vdd vout)\n'
    for args in [
        ('MN0','iref iref vss vss','n_mirror_unit',2),
        ('MN2','vbpc iref vss vss','n_mirror_unit',1),
        ('MPCB','vbpc vbpc vdd vdd','p_cascode_bias',1),
        ('MP2X','vbnc vbpc vdd vdd','p_cascode_bias',1),
        ('MNCB','vbnc vbnc vss vss','n_cascode_bias',1),
        ('MP0','n1a vbp vdd vdd','p_mirror_unit',2.5),
        ('MPC0','vbp vbpc n1a vdd','p_cascode_unit',1),
        ('MNC1','vbp vbnc n1b vss','n_cascode_unit',1),
        ('MN1','n1b iref vss vss','n_mirror_unit',1),
        ('MPM','na vbp vdd vdd','p_mirror_unit',p_ratio),
        ('MPC','nc vbpc na vdd','p_cascode_unit',p_ratio/2.5),
        ('MSUP','vout upb nc vdd','p_switch',1),
        ('MSDU','wu upd nc vdd','p_switch',1),
        ('MNWU','wu wu vss vss','up_dummy_diode',1),
        ('MNM','ne iref vss vss','n_mirror_unit',n_ratio),
        ('MNC','nd vbnc ne vss','n_cascode_unit',n_ratio),
        ('MSDN','vout dn nd vss','n_switch',1),
        ('MSDD','wd dnb nd vss','n_switch',1),
        ('MNWD','vdd vdd wd vss','dn_dummy_follower',1),
    ]:b+=m(*args)
    b+=f'''XUP (up upb vdd vss vdd vss) {up_cell}
XUPD (upb upd vdd vss vdd vss) {upd_cell}
XDN (dn dnb vdd vss vdd vss) {dn_cell}
CBP (vbp vdd) capacitor c=1p
CBPC (vbpc vdd) capacitor c=1p
CBNC (vbnc vss) capacitor c=1p
CIR (iref vss) capacitor c=.8p
CWU (wu vss) capacitor c=.4p
CWD (wd vdd) capacitor c=.4p
CNC (nc vss) capacitor c={cnode_fF:g}f
CND (nd vss) capacitor c={cnode_fF:g}f
ends pll_charge_pump
'''
    c=CASE/'circuit.scs';c.write_text(b)
    write_json(CASE/'sizing.json',dict(generated_at=now(),roles=roles,unit_multipliers=dict(MN0=2,MN2=1,MN1=1,MNM=n_ratio,MP0=2.5,MPM=p_ratio,MPC=p_ratio/2.5,MNC=n_ratio),hd_cells=[up_cell,upd_cell,dn_cell],cnode_fF=cnode_fF,rationale='Long-channel unit current mirrors and matched cascode replica; continuously biased branches steer into dummy loads while inactive. gmID defines analog initial dimensions; steering switches actually work in triode. HD control cells retain exact vendor MOS sizes.'))
    source=SOURCE/'sky130-pll-charge-pump-pvt'
    write_json(CASE/'contract.json',dict(source_task=source.name,source_hashes={str(p.relative_to(source)):sha(p) for p in [source/'instruction.md',source/'tests/verify.py',source/'tests/benches/tb_dc.spi',source/'tests/benches/tb_pulse.spi',source/'solution/circuit.spi']},corner='tt',VDD_V=1.8,temperature_C=27,reference_A=25e-6,nominal_current_A=50e-6,dc_output_sweep_V=[.3,1.35,.025],compliance_V=[.45,1.15],matching_voltages_V=[.45,.9,1.15],dc_accuracy_error_max_fraction=.05,flatness_max_fraction=.01,mismatch_max_fraction=.02,off_current_max_A=1e-9,both_current_max_A=1e-6,pulse_output_V=.9,control_rise_fall_s=200e-12,wide_pulse_error_max_fraction=.05,narrow_pulse_error_max_fraction=.25,overlap_charge_max_C=20e-15,turn_on_max_s=.5e-9,turn_off_max_s=.05e-9,power_max_W=500e-6,charge_windows_ns=dict(up10=[15,45],up1=[55,75],dn10=[95,125],dn1=[135,155],both=[175,205]),charge_reference='Q10 normalized to same-branch DC(.9V)*10ns; Q1 to measured same-branch Q10/10',turn_on_reference='First rising 90% of 25-30ns / 105-110ns plateau, measured from START of 200ps input rise (20ns/100ns)',turn_off_reference='First falling 5% after 30ns/110ns; max(crossing minus END of 200ps input fall,0)',power_reference='Time-average -1.8*I(VDD) over0-220ns including IREF and all permanently biased branches',legal_DUT_leaves='PDK MOS and ideal capacitors only; no ideal R or internal sources',scope_excludes=['26 other PVT DC rows','ss/ff transient rows','tt_mm seeds31001-31020','PEX']))
    return c,hd

def header(c):return prefix(c)+f'include "{CASE/"hd_cells.scs"}"\n'

def dc_bench(c):
    b=header(c)+'parameters sweepout=.9\n'
    for tag,up,dn in [('U',1.8,0),('D',0,1.8),('O',0,0),('B',1.8,1.8)]:
        b+=f'''VDD{tag} (vdd{tag} 0) vsource dc=1.8
IREF{tag} (vdd{tag} iref{tag}) isource dc=25u
VUP{tag} (up{tag} 0) vsource dc={up}
VDN{tag} (dn{tag} 0) vsource dc={dn}
VOUT{tag} (vout{tag} 0) vsource dc=sweepout
X{tag} (0 iref{tag} up{tag} dn{tag} vdd{tag} vout{tag}) pll_charge_pump
save vout{tag} VOUT{tag}:p VDD{tag}:p
'''
    for tag in ['U','D','O']:
        b+='save '+' '.join(f'X{tag}.{n}' for n in ['na','nc','ne','nd','n1a','n1b','vbp','vbpc','vbnc','wu','wd'])+'\n'
        for dev in OP_DEVICES:
            b+='save '+' '.join(f'X{tag}.{dev}:{x}' for x in ['ids','gm','gds','vgs','vds','vdsat','region'])+'\n'
    return b+'dcOp dc\ncompliance dc param=sweepout start=.3 stop=1.35 step=.025\n'

def pulse_bench(c):
    return header(c)+'''VDD (vdd 0) vsource dc=1.8
IREF (vdd iref) isource dc=25u
VUP (up 0) vsource type=pwl wave=[0 0 20n 0 20.2n 1.8 30n 1.8 30.2n 0 60n 0 60.2n 1.8 61n 1.8 61.2n 0 180n 0 180.2n 1.8 190n 1.8 190.2n 0 220n 0]
VDN (dn 0) vsource type=pwl wave=[0 0 100n 0 100.2n 1.8 110n 1.8 110.2n 0 140n 0 140.2n 1.8 141n 1.8 141.2n 0 180n 0 180.2n 1.8 190n 1.8 190.2n 0 220n 0]
VOUT (vout 0) vsource dc=.9
XCP (0 iref up dn vdd vout) pll_charge_pump
save up dn vout VOUT:p VDD:p XCP.upb XCP.upd XCP.dnb XCP.nc XCP.nd XCP.wu XCP.wd XCP.vbp XCP.vbpc XCP.vbnc
tran tran stop=220n maxstep=2p strobeperiod=2p errpreset=conservative
'''

def integral(t,y,start,stop):
    mask=(t>start)&(t<stop);ts=np.r_[start,t[mask],stop];ys=np.r_[np.interp(start,t,y),y[mask],np.interp(stop,t,y)]
    return float(np.trapz(ys,ts))

def crossing(t,y,level,start,stop,rise):
    ix=np.flatnonzero((t[:-1]>=start-1e-18)&(t[1:]<=stop)&((y[:-1]<level)&(y[1:]>=level) if rise else (y[:-1]>level)&(y[1:]<=level)))
    if not len(ix):raise RuntimeError(f'Missing required {"rising" if rise else "falling"} crossing {level} in {start}..{stop}')
    i=ix[0];return float(t[i]+(level-y[i])/(y[i+1]-y[i])*(t[i+1]-t[i]))

def extract(runs):
    d=data(runs[0],'compliance.dc');o=dc(runs[0]);t=data(runs[1],'tran.tran');x=d['sweepout'];mask=(x>=.45-1e-10)&(x<=1.15+1e-10)
    assert len(x)==43 and np.count_nonzero(mask)==29
    u=d['VOUTU:p'];dn=-d['VOUTD:p'];curves={};v={}
    for name,y in [('up',u),('dn',dn)]:
        yy=y[mask];avg=integral(x,y,.45,1.15)/.7
        v[name+'_current_min_A']=float(min(yy));v[name+'_current_max_A']=float(max(yy));v[name+'_current_mid_A']=float(np.interp(.9,x,y))
        v[name+'_accuracy_error_fraction']=float(max(abs(yy/50e-6-1)))
        v[name+'_flatness_fraction']=float(np.ptp(yy)/avg)
        curves[name]=y.tolist()
    v['matching_error_fraction']=max(abs(float(np.interp(z,x,u-dn)))/50e-6 for z in [.45,.9,1.15])
    v['all_compliance_matching_error_fraction']=float(max(abs(u[mask]-dn[mask]))/50e-6)
    v['off_current_max_A']=float(max(abs(d['VOUTO:p'])))
    v['both_current_max_A']=float(max(abs(d['VOUTB:p'][mask])))
    tt=t['time'];ii=t['VOUT:p'];edges={}
    for branch,sign,start in [('up',1,20e-9),('dn',-1,100e-9)]:
        y=sign*ii;plateau=integral(tt,y,start+5e-9,start+10e-9)/5e-9
        q10=integral(tt,y,start-5e-9,start+25e-9)
        q1=integral(tt,y,start+35e-9,start+55e-9)
        on=crossing(tt,y,.9*plateau,start,start+5e-9,True)
        off=crossing(tt,y,.05*plateau,start+10e-9,start+25e-9,False)
        v[f'q_{branch}10_C']=q10;v[f'q_{branch}1_C']=q1
        v[f'{branch}_wide_charge_error_fraction']=abs(q10/(v[branch+'_current_mid_A']*10e-9)-1)
        v[f'{branch}_narrow_charge_error_fraction']=abs(q1/(q10/10)-1)
        v[f'{branch}_turn_on_s']=on-start
        v[f'{branch}_turn_off_s']=max(off-(start+10.2e-9),0)
        edges[branch]=dict(plateau_A=plateau,on_90pct_crossing_s=on,off_5pct_crossing_s=off,turn_on_reference_s=start,turn_off_reference_s=start+10.2e-9)
    v['overlap_charge_C']=abs(integral(tt,ii,175e-9,205e-9))
    overlap=(tt>=175e-9)&(tt<=205e-9)
    v['overlap_absolute_current_integral_C']=integral(tt,abs(ii),175e-9,205e-9)
    v['overlap_min_current_A']=float(min(ii[overlap]));v['overlap_max_current_A']=float(max(ii[overlap]))
    v['pulse_min_current_A']=float(min(ii));v['pulse_max_current_A']=float(max(ii))
    v['power_W']=integral(tt,-1.8*t['VDD:p'],0,220e-9)/220e-9
    gates={}
    for branch in ['up','dn']:
        for suffix,limit,unit in [('accuracy_error_fraction',.05,'fraction of50uA'),('flatness_fraction',.01,'fraction of own mean'),('wide_charge_error_fraction',.05,'fraction'),('narrow_charge_error_fraction',.25,'fraction'),('turn_on_s',.5e-9,'s'),('turn_off_s',.05e-9,'s')]:
            key=branch+'_'+suffix;gates[key]=gate(v[key],limit,'max',unit)
    for key,limit,unit in [('matching_error_fraction',.02,'fraction of50uA'),('off_current_max_A',1e-9,'A'),('both_current_max_A',1e-6,'A'),('overlap_charge_C',20e-15,'C'),('power_W',500e-6,'W')]:gates[key]=gate(v[key],limit,'max',unit)
    tiers={tier:all(q['passes'][tier] for q in gates.values()) for tier in ['original','10pct','15pct']};tier=next((k for k in tiers if tiers[k]),None)
    ops={}
    for tag in ['U','D','O']:
        for name in OP_DEVICES:
            q={key:o[f'X{tag}.{name}:{key}'] for key in ['ids','gm','gds','vgs','vds','vdsat','region']}
            q['gm_id']=abs(q['gm']/q['ids']) if abs(q['ids'])>1e-14 else None
            q['saturation_margin_V']=abs(q['vds'])-abs(q['vdsat'])
            ops[tag+'.'+name]=q
    compliance_margins={}
    for tag,devices in [('U',['MPM','MPC']),('D',['MNM','MNC'])]:
        for dev in devices:
            margin=abs(d[f'X{tag}.{dev}:vds'])-abs(d[f'X{tag}.{dev}:vdsat'])
            j=np.flatnonzero(mask)[np.argmin(margin[mask])]
            compliance_margins[tag+'.'+dev]=dict(min_saturation_margin_V=float(margin[j]),output_V=float(x[j]))
    r=dict(case_slot=47,generated_at=now(),run_dirs=[str(rd.relative_to(ROOT)) for rd in runs],status='complete_'+tier if tier else 'partial',values=v,gates=gates,pass_tiers=tiers,all_nominal_checks_complete=True,model_dimensions_valid=True,operating_points=ops,compliance_saturation_margins=compliance_margins,edge_definitions=edges,dc_curves=dict(output_V=x.tolist(),up_A=u.tolist(),dn_A=dn.tolist(),off_A=d['VOUTO:p'].tolist(),both_A=d['VOUTB:p'].tolist()),scope='TT/1.8V/27C. Four DC states on43points; both wide/narrow pulses and overlap; mismatch seeds and other PVT not run.')
    write_json(runs[-1]/'measurements.json',r);write_json(CASE/'latest_results.json',r)
    update_case(47,status=r['status'],nominal_complete=bool(tier),latest_run=r['run_dirs'][-1],report=str((CASE/'latest_results.json').relative_to(ROOT)))
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ncb-gmid',type=float,default=4.5);p.add_argument('--pcb-gmid',type=float,default=4.5)
    p.add_argument('--n-ratio',type=float,default=4);p.add_argument('--p-ratio',type=float,default=10)
    p.add_argument('--psw-uA',type=float,default=50);p.add_argument('--nsw-uA',type=float,default=50)
    p.add_argument('--up-cell',default='INHDV8');p.add_argument('--upd-cell',default='INHDV2');p.add_argument('--dn-cell',default='INHDV4');p.add_argument('--cnode-fF',type=float,default=30)
    p.add_argument('--extract',nargs=2);a=p.parse_args()
    if a.extract:runs=[ROOT/x for x in a.extract]
    else:
        params=vars(a).copy();params.pop('extract');c,hd=design(**params)
        update_case(47,status='running',nominal_complete=False)
        deps=[c,hd,CASE/'sizing.json',CASE/'contract.json',CASE/'hd_cells_manifest.json']
        runs=[]
        for label,maker in [('dc',dc_bench),('pulse',pulse_bench)]:
            b=maker(c);(CASE/f'bench_{label}.scs').write_text(b);runs.append(run_spectre(47,label,b,deps))
    r=extract(runs);print(json.dumps(dict(status=r['status'],values=r['values'],failed=[k for k,v in r['gates'].items() if not v['passes']['15pct']]),indent=2))

if __name__=='__main__':main()
