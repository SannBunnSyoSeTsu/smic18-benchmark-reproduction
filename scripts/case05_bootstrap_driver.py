"""Native half-bridge gate driver; package, large external NMOS and load fixed."""
from batch29 import *
from hd_cells import extract_hd
CASE=ROOT/'cases/05-bootstrap-driver';TASK=SOURCE/'sky130-bootstrap-driver-pt'

def design(delay_fF=100,cboot_pF=620,chip_mim_m=20,drive_parallel=32,charge_scale=1,follow_scale=None,reset_scale=1,moscap_m=0,trackcap_m=0,trackp_scale=0):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C all original20/50/80ns PWM widths; fixed two external50um*m450 NMOS,3.6ohm load and package/wire parasitics. OriginalFS/SF and80/125C not claimed.',VDD_V=1.8,temperature_C=27,PWM=dict(period_s=100e-9,rise_fall_s=3e-9,width_s=[20e-9,50e-9,80e-9],source_ohm=50),external_power_NMOS=dict(model='n18',W_um=50,L_um=.18,m=450,HS_body='external capacitor bottom ext_vlx2',migration='Native minimum length .18um; same50um finger width and450parallel count.'),load_ohm=3.6,supply_package=dict(L_H=.3e-9,R_ohm=.003),bootstrap_wire_each=dict(L_H=2e-9,R_ohm=.005),offchip_cap_max_F=100e-9,window_s=[.5e-6,1e-6],deadtime_range_s=[3e-9,7e-9],power_strict_max_W=.0035,VGS_mean_range_V=[1.65,1.85],VGS_strict_peak_V=2.15,HS_strict_peak_A=.8,VBST_minus_VLX_strict_peak_V=2.15,GN2_strict_peak_V=2.15,source_VBST_strict_peak_V=5.65,native33_VBST_screen_V=3.63,area_max_um2=35000,power_definition='abs(1.8*time-weighted mean current of zero-voltVDDDUT probe), includes bootstrap charge; external bridge current separately sensed byVHS.',allowed='Native MOS,MIM and unmodifiedHD; no ideal DUT capacitors/resistors/sources.',nonrelaxable='Gate and bootstrap voltage peaks,current shoot-through,positive nonoverlap,actual high-side drive;3.63V33device screening is not foundry reliability signoff.',unmodeled=['PVT','mismatch','PEX','reliability lifetime']))
    roles=dict(hv_n=lut_size('n33',.36,10,10e-6,1.8),hv_p=lut_size('p33',.36,10,1e-6,1.8),charge_n=lut_size('n33',.36,5,.05,1.8),charge_p=lut_size('p33',.36,5,.05,1.8),reset_n=lut_size('n18',.18,8,.1),mirror_n=lut_size('n18',.18,10,10e-6))
    extract_hd(['INHDV1','INHDV4','INHDV16','INHDV32','NAND2HDV1','NOR2HDV1'],CASE)
    lines=['simulator lang=spectre'];mapping={}
    def add(s):lines.extend(s.strip().splitlines())
    def hd(name,nodes,model):add(f'X{name} ({nodes}) {model}')
    def mos(name,nodes,role,scale=1):
        q=roles[role];W=q['rounded_W_um']*scale;parallel=int(np.ceil(W/90));mapping[name]=dict(role=role,total_W_um=W,parallel=parallel);add(f'M{name} ({nodes}) {q["model"]} w={W/parallel:.10g}u l={q["L_um"]:g}u m={parallel}')
    add('subckt inv (in out vdd vss)\nXG (in out vdd vss vdd vss) INHDV1\nends inv\nsubckt nand (a b q vdd vss)\nXG (a b q vdd vss vdd vss) NAND2HDV1\nends nand\nsubckt delay_chain (in out vdd vss)')
    for i in range(8):
        a='in' if i==0 else f'd{i-1}';z='out' if i==7 else f'd{i}';hd('D'+str(i),f'{a} {z} vdd vss vdd vss','INHDV1');add(f'CD{i} ({z} vss) mim w=10u l={delay_fF/10:g}u')
    add('ends delay_chain\nsubckt non_overlap (clk p1 p2 vdd vss)\nXI5 (net03 p2 vdd vss) inv\nXI0 (clk net5 vdd vss) inv\nXI3 (p1 clk net4 vdd vss) nand\nXI1 (net5 net03 net6 vdd vss) nand\nXI4 (net4 net03 vdd vss) delay_chain\nXI2 (net6 p1 vdd vss) delay_chain\nends non_overlap')
    for name,counts in [('buffer',[1,max(1,drive_parallel//16),max(1,drive_parallel//4),drive_parallel]),('buffers',[1,1,1,2])]:
        add(f'subckt {name} (in out vdd vss)')
        for st,num in enumerate(counts):
            a='in' if st==0 else f'b{st-1}';z='out' if st==3 else f'b{st}';model=('INHDV16' if st==0 else 'INHDV32') if name=='buffer' else ['INHDV1','INHDV4','INHDV16','INHDV32'][st]
            for i in range(num):hd(f'B{st}_{i}',f'{a} {z} vdd vss vdd vss',model)
        add('ends '+name)
    src=(TASK/'solution/circuit.spi').read_text();core=src[src.index('.subckt lvl3'):];block=None
    for raw in core.splitlines():
        z=raw.split()
        if not z or z[0].startswith('*'):continue
        if z[0].lower()=='.subckt':block=z[1];add('subckt '+block+' ('+' '.join(z[2:])+')');continue
        if z[0].lower()=='.ends':add('ends '+z[1]);continue
        if z[0]=='XC0':
            add(f'CBST (VBST VLX) mim w=30u l=30u m={chip_mim_m}')
            if moscap_m:add(f'MBSTCAP (VLX VBST VLX VLX) n18 w=80u l=9.6u m={moscap_m}')
            if trackcap_m:add(f'MTRACKCAP (VLX VSW VLX VLX) n18 w=80u l=9.6u m={trackcap_m}')
            if trackp_scale:mos('TRACKP','VSW VSS VLX VLX','charge_p',trackp_scale)
            continue
        if block=='lvl3' and z[0] in ['XNM0','XPM2']:
            if z[0]=='XNM0':hd('COREINV','in net1 vdd1 vss vdd1 vss','INHDV1')
            continue
        if block=='bootstrap_driver' and z[0] in ['XLVL2','XINV4','XINV5','XPM1','XPM0','XNM0']:continue
        if block=='bootstrap_driver' and z[0]=='XBUFF7':
            add('XBUFF7 (net028 net16 VDD VSS) buffers\nXCHARGE_LS (net02 CHUP VDD VBST VSS) lvl3')
            mos('CHN','charge_inv CHUP VLX VLX','hv_n');mos('CHP','charge_inv CHUP VBST VBST','hv_p')
            add('XINVCH (charge_inv charge_noninv VBST VLX) inv\nXBUFFCH (charge_noninv charge_gate VBST VLX) buffers');continue
        if block=='bootstrap_driver' and z[0]=='XPM2':z[2]='charge_gate'
        if z[0].startswith(('XNM','XPM')):
            par=dict(re.findall(r'(w|l|m)=([.\d]+)',raw));W=float(par['w']);mul=float(par.get('m',1));pol='n' if z[0].startswith('XNM') else 'p';role='hv_'+pol;scale=W*mul/(.75 if pol=='n' else .5)
            if block=='bootstrap_driver' and z[0] in ['XNM2','XPM2']:role='charge_'+pol;scale=(follow_scale if pol=='n' and follow_scale is not None else charge_scale)
            elif block=='bootstrap_driver' and z[0]=='XNM1':role='reset_n';scale=reset_scale
            elif 'nfet_01v8' in raw:role='mirror_n';scale=W*mul/.42
            mos(block+'_'+z[0][1:],' '.join(z[1:5]),role,scale)
        elif z[0].startswith('X'):add(z[0]+' ('+' '.join(z[1:-1])+') '+z[-1])
        else:raise ValueError(raw)
    save_design(CASE,'\n'.join(lines)+'\n',roles,dict(delay_fF=delay_fF,cboot_pF=cboot_pF,chip_mim_m=chip_mim_m,drive_parallel=drive_parallel,charge_scale=charge_scale,instance_roles=mapping),'Source floating-bootstrap topology retained with native3.3V-class thick-oxide devices for level translation and recharge paths. LUT sizing atgmID10 for level shift,5 for strong recharge and8 for bottom reset. Digital nonoverlap and four-stage buffers use unmodifiedHD; parallel complete cells provide drive. Bootstrap recharge is explicitly interlocked with the low-side command: an addedHVlevel shifter holds the chargingPMOS off during HS conduction/deadtime; the bottom reset is driven by the low-side command throughHD buffers. Source feedback level-down latch is removed. This avoids discharging the floating storage intoVDD before the lower plate resets. MIMdelay cells and bootstrap storage use native mim. Extra3.3V-class terminal screening required; no5Vdevice claim.')
    sizing=json.loads((CASE/'sizing.json').read_text());sizing['parameters'].update(follow_scale=follow_scale,reset_scale=reset_scale,moscap_m=moscap_m,trackcap_m=trackcap_m,trackp_scale=trackp_scale,moscap_geometry_note='Native MOS used as two-terminal storage: D/S/B=VLX,G=VBST or VSW,W80um,L9.6um. Geometry is area/capacitance sizing, not an amplifier gmID operating point. Model nonlinearity retained.');write_json(CASE/'sizing.json',sizing)
    update_case(5,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))

def bench(pw,step=.1e-9,reltol=1e-5):
    par=json.loads((CASE/'sizing.json').read_text())['parameters'];return f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{MODEL}" section=mim_tt
include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
VDDDUT (vdd_dut vdd) vsource dc=0
VHS (vdd_hs vdd) vsource dc=0
VIN (src 0) vsource type=pulse val0=0 val1=1.8 delay=0 rise=3n fall=3n width={pw}n period=100n
RIN (src inp) resistor r=50
LVDD (vdd_dut vdd_pkg) inductor l=.3n
RVDD (vdd_pkg vdd_core) resistor r=.003
LVSS (0 vss_pkg) inductor l=.3n
RVSS (vss_pkg vss_core) resistor r=.003
X (hi_g lo_g inp vbst vdd_core vlx vss_core vsw) bootstrap_driver
L0 (vbst net9) inductor l=2n
RL0 (net9 net9b) resistor r=.005
L1 (vlx ext_vlx) inductor l=2n
RL1 (ext_vlx ext_vlx2) resistor r=.005
C0 (net9b ext_vlx2) capacitor c={par['cboot_pF']:g}p
MHS (vdd_hs hi_g vsw ext_vlx2) n18 w=50u l=.18u m=450
MLS (vsw lo_g 0 0) n18 w=50u l=.18u m=450
RLOAD (vsw 0) resistor r=3.6
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-7 iabstol=1e-12 gmin=1e-15
saveOptions options save=selected
save hi_g lo_g vbst vlx vsw inp vdd_core vss_core VDDDUT:p VHS:p X.net16 X.P1UP X.p1_int X.net028 X.charge_gate X.CHUP X.net02
tran tran stop=1u maxstep={step:g} method=traponly errpreset=conservative
'''

def metrics(d):
    t=d['time'];a,z=.5e-6,1e-6;tt=np.r_[a,t[(t>a)&(t<z)],z];v={k:np.interp(tt,t,x) for k,x in d.items()};gs=v['hi_g']-v['vsw'];mask=(v['vsw']>.9).astype(float);avg=lambda x:float(np.trapz(x,tt)/(z-a))
    def edges(x,rise):
        e=x-.9;ix=np.flatnonzero(((e[:-1]<=0)&(e[1:]>0)) if rise else ((e[:-1]>=0)&(e[1:]<0)));return [float(tt[i]-e[i]*(tt[i+1]-tt[i])/(e[i+1]-e[i])) for i in ix]
    def delay(falls,rises):return [min(y for y in rises if y>x)-x for x in falls if any(y>x for y in rises)]
    hl=delay(edges(gs,False),edges(v['lo_g'],True));lh=delay(edges(v['lo_g'],False),edges(gs,True));both=hl+lh
    q=dict(VGS_avg_V=float(np.trapz(gs*mask,tt)/max(np.trapz(mask,tt),1e-30)),power_W=abs(1.8*avg(v['VDDDUT:p'])),VGS_peak_V=float(max(gs)),HS_peak_A=float(max(abs(v['VHS:p']))),VBST_cap_peak_V=float(max(v['vbst']-v['vlx'])),GN2_peak_V=float(max(v['lo_g'])),VBST_peak_V=float(max(v['vbst'])),dead_HL_s=hl[1] if len(hl)>1 else None,dead_LH_s=lh[1] if len(lh)>1 else None,dead_all_min_s=min(both) if both else None,dead_all_max_s=max(both) if both else None,high_fraction=avg(mask))
    return q,dict(dead_HL_s=hl,dead_LH_s=lh)

def probe(pw=50):
    rd=run_spectre(5,'probe_'+str(pw),bench(pw),[CASE/x for x in ['circuit.scs','sizing.json','contract.json','hd_cells.scs','hd_cells_manifest.json']],timeout=1800);q,rec=metrics(data(rd,'tran.tran'));write_json(CASE/'probe_results.json',dict(run=str(rd.relative_to(ROOT)),values=q,records=rec));print(json.dumps(q,indent=2),flush=True)

def area():
    from schematic_common import read_case
    from audit_schematic_independent import parse_source,numeric
    hd=parse_source(CASE/'hd_cells.scs');design=read_case(5);rows=[]
    for path,q in design['flat_instances'].items():
        devices=hd[q['model']]['instances'].values() if q['kind']=='HD' else [q]
        value=sum(numeric(d['parameters']['w'])*numeric(d['parameters']['l'])*numeric(d['parameters'].get('m','1'))*1e12 for d in devices)
        rows.append(dict(instance=path,kind=q['kind'],model=q['model'],area_um2=value))
    report=dict(method='Expanded DUT sum(W*L*m) for nativeMOS/MOSCAP/MIM and every unchangedHD MOS; repeated subcircuits counted per occurrence; fixed external powerMOS and external capacitor excluded.',total_um2=sum(x['area_um2'] for x in rows),instances=rows)
    write_json(CASE/'area_audit.json',report);return report['total_um2']

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());values={};records={};gates={};guards=set(runs)=={'pw20','pw50','pw80'}
    for label,path in runs.items():
        d=data(ROOT/path,'tran.tran');q,rec=metrics(d);values[label]=q;records[label]=rec
        for key,lo,hi in [('VGS_avg_V',1.65,1.85),('dead_HL_s',3e-9,7e-9),('dead_LH_s',3e-9,7e-9)]:
            gates[label+'_'+key+'_min']=gate(q[key],lo,'min','V' if key.startswith('VGS') else 's');gates[label+'_'+key+'_max']=gate(q[key],hi,'max','V' if key.startswith('VGS') else 's')
        gates[label+'_power']=strict(gate(q['power_W'],.0035,'max','W'))
        peak_ok=all(q[k]<lim for k,lim in [('VGS_peak_V',2.15),('HS_peak_A',.8),('VBST_cap_peak_V',2.15),('GN2_peak_V',2.15),('VBST_peak_V',3.63)])
        # Exactly five complete transitions of each kind in the fixed five
        # cycle record; an extra crossing cannot be hidden by edge pairing.
        t=d['time'];mask=(t>=.5e-6)&(t<=1e-6);gs=(d['hi_g']-d['vsw'])[mask];lo=d['lo_g'][mask]
        counts={name:int(np.sum((a[:-1]<=.9)&(a[1:]>.9))) if rising else int(np.sum((a[:-1]>=.9)&(a[1:]<.9))) for name,a,rising in [('HS_rise',gs,True),('HS_fall',gs,False),('LS_rise',lo,True),('LS_fall',lo,False)]}
        rec['edge_counts']=counts;rec['peak_guards_pass']=peak_ok;guards &= peak_ok and all(x==5 for x in counts.values()) and len(rec['dead_HL_s'])==5 and len(rec['dead_LH_s'])==5 and q['dead_all_min_s']>0 and q['high_fraction']>.05
    a=area();guards &= a<=35000 and json.loads((CASE/'sizing.json').read_text())['parameters']['cboot_pF']<=100000
    write_json(CASE/'switching_records.json',records);return result(CASE,5,values,gates,runs,guards,area_um2=a,switching_records_sha256=sha(CASE/'switching_records.json'))

def run(step=.1e-9,reltol=1e-5):
    simulate_groups(5,CASE,{f'pw{pw}':bench(pw,step,reltol) for pw in [20,50,80]});return extract()

def final_design():
    design(delay_fF=110,cboot_pF=200,chip_mim_m=1,drive_parallel=8,charge_scale=.1,follow_scale=.4,reset_scale=.07,moscap_m=34,trackp_scale=2)

if __name__=='__main__':final_design();run()
