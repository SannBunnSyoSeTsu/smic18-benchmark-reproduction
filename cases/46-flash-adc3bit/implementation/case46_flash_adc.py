"""Seven StrongARM comparators, exact HD SR/encoder, original nominal stimuli."""
from batch29 import *
from hd_cells import extract_hd
CASE=ROOT/'cases/46-flash-adc3bit';TASK=SOURCE/'sky130-flash-adc-3bit-pvt'
CODES=[0,7,3,5,1,6,2,4,7,0,4,2,6,1,5,3,7,0,2,5,0,7,1,6,3,4]

def design(scale=1,ladder=500,tap=.3):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C: fullspeed ramp,26code transition stress, coherent bins1and7 at original212/279.25degree phases. Sine functional stimuli moved toTTnominal; original four other static/transition PVT andtwo dynamic PVT conditions notclaimed.',VDD_V=1.8,temperature_C=27,references_V=[.6,1.4],LSB_V=.1,clock=dict(Hz=50e6,delay_s=10e-9,rise_fall_s=.3e-9,width_s=9.4e-9,source_ohm=50),output_load_F=15e-15,ideal_input_drive_ohm=0,sample_offset_s=19e-9,stable_window_after_edge_s=[9.5e-9,19e-9],transition_codes=CODES,transition_stop_s=540e-9,ramp_stop_s=2.2e-6,ramp_V=[.55,1.45],ramp_s=[100e-9,2100e-9],sine=dict(Hz=[3.125e6,21.875e6],phase_deg=[212,279.25],offset_V=1,amplitude_V=.39,N=16,first_edge_s=50e-9),dnl_inl_absolute_error_max_LSB=.30,delay_max_s=9.5e-9,core_reference_power_max_W=.001,clock_positive_power_max_W=.00025,power_window_s=[100e-9,500e-9],sndr_min_dB=17,sfdr_min_dB=21,normalized_ENOB_min=2.5,nonrelaxable='allcodes/thresholds,monotonic,correcttransitions,requiredcrossings,valid0.2/0.8VDDlevels,9.5-to19ns stability',allowed='nativeMOS,positiveidealR/C,exactHDcells; no behavioralsources',unmodeled=['device noise','mismatch','metastability statistics','PEX','nonidealreference/inputdrivers']))
    roles=dict(input=lut_size('n18',.18,14,100e-6,.45),tail=lut_size('n18',.18,8,300e-6,.45),latch_n=lut_size('n18',.18,10,100e-6,.45),latch_p=lut_size('p18',.18,10,50e-6,.45),precharge=lut_size('p18',.18,10,50e-6,.45));w={k:round(q['rounded_W_um']*scale,4) for k,q in roles.items()}
    extract_hd(['INHDV1','NAND2HDV1','NAND4HDV1'],CASE)
    txt=f'''simulator lang=spectre
subckt fa_comp (clk vinp vinn outp outn vdd vss)
MTAIL (tail clk vss vss) n18 w={w['tail']}u l=.18u
MIN1 (dx vinp tail vss) n18 w={w['input']}u l=.18u
MIN2 (dy vinn tail vss) n18 w={w['input']}u l=.18u
MNL1 (outn outp dx vss) n18 w={w['latch_n']}u l=.18u
MNL2 (outp outn dy vss) n18 w={w['latch_n']}u l=.18u
MPL1 (outn outp vdd vdd) p18 w={w['latch_p']}u l=.18u
MPL2 (outp outn vdd vdd) p18 w={w['latch_p']}u l=.18u
MPC1 (outn clk vdd vdd) p18 w={w['precharge']}u l=.18u
MPC2 (outp clk vdd vdd) p18 w={w['precharge']}u l=.18u
MPC3 (dx clk vdd vdd) p18 w={w['precharge']}u l=.18u
MPC4 (dy clk vdd vdd) p18 w={w['precharge']}u l=.18u
ends fa_comp
subckt fa_sr (sn rn q qb vdd vss)
XG1 (sn qb q vdd vss vdd vss) NAND2HDV1
XG2 (rn q qb vdd vss vdd vss) NAND2HDV1
ends fa_sr
subckt flash_adc_3bit (vss vdd vrefn vrefp clk vin b2 b1 b0)
'''
    nodes=['vrefn']+[f't{i}' for i in range(1,8)]+['vrefp']
    for i in range(8):txt+=f'RL{i+1} ({nodes[i+1]} {nodes[i]}) resistor r={ladder:g}\n'
    for i in range(1,8):txt+=f'''CT{i} (t{i} vss) capacitor c={tap:g}p
XC{i} (clk vin t{i} cp{i} cn{i} vdd vss) fa_comp
XS{i} (cn{i} cp{i} q{i} qb{i} vdd vss) fa_sr
'''
    cells=[('E1','q2 n2','INHDV1'),('E2','q4 n4','INHDV1'),('E3','q6 n6','INHDV1'),('E4','q7 n7','INHDV1'),('E5','q2 n4 x1','NAND2HDV1'),('E6','n6 x1 b1','NAND2HDV1'),('E7','q5 n6 y1','NAND2HDV1'),('E8','q3 n4 y2','NAND2HDV1'),('E9','q1 n2 y3','NAND2HDV1'),('E10','n7 y1 y2 y3 b0','NAND4HDV1'),('E11','q4 d4','INHDV1'),('E12','d4 b2','INHDV1')]
    for n,p,m in cells:txt+=f'X{n} ({p} vdd vss vdd vss) {m}\n'
    txt+='ends flash_adc_3bit\n'
    save_design(CASE,txt,roles,dict(scale=scale,ladder=ladder,tap=tap),'Sevenidentical dynamicStrongARM analogcomparators sizedusingnativegmIDunitcurrentestimates; actualgmIDtimevarying. NativeHD NANDSRholds decisionsduringreset; staticHDthermometerto3-bitencoding. Ideal8x500ohmladder and0.3pF tapfilters allowedbyoriginalcontract.')

def bench(kind,step=.1e-9,reltol=1e-6):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
VREFP (vrefp 0) vsource dc=1.4
VREFN (vrefn 0) vsource dc=.6
VCLK (clk_src 0) vsource type=pulse val0=0 val1=1.8 delay=10n rise=.3n fall=.3n width=9.4n period=20n
RCLK (clk_src clk) resistor r=50
CB2 (b2 0) capacitor c=15f
CB1 (b1 0) capacitor c=15f
CB0 (b0 0) capacitor c=15f
X (0 vdd vrefn vrefp clk vin b2 b1 b0) flash_adc_3bit
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14 gmin=1e-15
saveOptions options save=selected
save vin vdd clk_src clk b2 b1 b0 VDD:p VREFP:p VREFN:p VCLK:p X.t1 X.t2 X.t3 X.t4 X.t5 X.t6 X.t7
'''
    if kind=='transition':
        pairs=[(0,.65)]
        for i,c in enumerate(CODES[1:],1):pairs += [(20e-9*i,.65+.1*CODES[i-1]),(20e-9*i+.4e-9,.65+.1*c)]
        pairs += [(540e-9,1.05)];stim='type=pwl wave=['+' '.join(f'{t:.12g} {v:.12g}' for t,v in pairs)+']';stop=540e-9
    elif kind=='ramp':stim='type=pwl wave=[0 .55 100n .55 2100n 1.45 2200n 1.45]';stop=2.2e-6
    else:
        f,p=(3.125e6,212) if kind=='sine_low' else (21.875e6,279.25);stim=f'dc=1 type=sine ampl=.39 freq={f:g} sinephase={p:g}';stop=380e-9
    return b+f'VIN (vin 0) vsource {stim}\ntran tran stop={stop:g} maxstep={step:g} method=gear2only errpreset=conservative\n'

def window(t,v,a,b):
    q=(t>a)&(t<b);return np.r_[a,t[q],b],np.r_[np.interp(a,t,v),v[q],np.interp(b,t,v)]

def records(d,edges,expected=None):
    t=d['time'];bits=[d['b2'],d['b1'],d['b0']];v=np.array([np.interp(edges+19e-9,t,b) for b in bits]);high=v>.9;codes=np.array([4,2,1])@high;invalid=int(np.sum((v>.36)&(v<1.44)));violations=0
    for j,e in enumerate(edges):
        code=int(codes[j]) if expected is None else expected[j]
        for k,b in enumerate(bits):
            _,w=window(t,b,e+9.5e-9,e+19e-9);violations+=int(np.sum(w<1.44 if code & (4>>k) else w>.36))
    return codes,invalid,violations

def extract():
    groups=json.loads((CASE/'latest_runs.json').read_text());values={};g={};ok=True;diag={}
    for kind,path in groups.items():
        d=data(ROOT/path,'tran.tran');t=d['time']
        if kind=='ramp':
            edges=np.arange(110,2101,20)*1e-9;c,invalid,viol=records(d,edges);vv=np.interp(edges,t,d['vin']);th=[]
            for code in range(1,8):
                ii=np.flatnonzero((c[:-1]<code)&(c[1:]>=code));assert len(ii)==1,(code,c);j=ii[0];th.append(float((vv[j]+vv[j+1])/2))
            th=np.array(th);fit=th[0]+np.arange(7)*(th[-1]-th[0])/6
            q=dict(dnl_lsb=float(max(abs(np.diff(th)/.1-1))),inl_lsb=float(max(abs(th-fit))/.1),absolute_error_lsb=float(max(abs(th-(.6+.1*np.arange(1,8))))/.1),monotonic=bool(np.all(np.diff(c)>=0)),codes_present=len(set(c)),thresholds_found=len(th),invalid_output_levels=invalid,stable_level_violations=viol)
            diag[kind]=dict(edges_s=edges.tolist(),input_V=vv.tolist(),codes=c.tolist(),thresholds_V=th.tolist());ok &= q['monotonic'] and q['codes_present']==8 and q['thresholds_found']==7
            for k in ['dnl_lsb','inl_lsb','absolute_error_lsb']:g[k]=gate(q[k],.3,'max','LSB')
        elif kind=='transition':
            edges=np.arange(30,511,20)*1e-9;c,invalid,viol=records(d,edges,CODES[1:]);delays=[];missing=0;late=0
            for j,e in enumerate(edges):
                for k in range(3):
                    bit=d[f'b{2-k}'];ix=np.flatnonzero((bit[:-1]-.9)*(bit[1:]-.9)<0);ix=ix[(t[ix]>=e)&(t[ix]<e+19e-9)];events=t[ix]+(.9-bit[ix])*(t[ix+1]-t[ix])/(bit[ix+1]-bit[ix]);missing+=int(bool((CODES[j]^CODES[j+1]) & (4>>k)) and not len(events));delays.extend((events-e).tolist());late+=int(np.sum(events-e>9.5e-9))
            # Preserve original power window selection of existing samples, no artificial boundary insertion.
            sel=(t>=100e-9)&(t<=500e-9);tt=t[sel];p=-(1.8*d['VDD:p']+1.4*d['VREFP:p']+.6*d['VREFN:p']);pc=np.maximum(-d['clk_src']*d['VCLK:p'],0);avg=lambda z:float(np.trapz(z[sel],tt)/(tt[-1]-tt[0]))
            q=dict(transition_errors=int(np.sum(c!=CODES[1:])),missing_expected_transitions=missing,late_transitions=late,invalid_output_levels=invalid,stable_level_violations=viol,clock_to_output_s=max(delays),core_reference_power_w=avg(p),clock_delivery_power_w=avg(pc),clock_peak_current_a=float(max(abs(d['VCLK:p'][sel]))));ok &= q['transition_errors']==missing==late==0 and q['core_reference_power_w']>=0 and q['clock_delivery_power_w']>=0
            diag[kind]=dict(edges_s=edges.tolist(),codes=c.tolist(),expected=CODES[1:],all_crossing_delays_s=delays)
            for k,l in [('clock_to_output_s',9.5e-9),('core_reference_power_w',.001),('clock_delivery_power_w',.00025)]:g[k]=gate(q[k],l,'max','s/W',relax=k!='clock_to_output_s')
        else:
            edges=(50+20*np.arange(16))*1e-9;c,invalid,viol=records(d,edges);spec=np.fft.rfft(c-np.mean(c));power=abs(spec)**2;tone=1 if kind=='sine_low' else 7;sig=power[tone];noise=sum(power[1:8])-sig+.5*power[8];spur=max([power[k] for k in range(1,8) if k!=tone]+[.5*power[8]])
            q=dict(codes_present=len(set(c)),invalid_output_levels=invalid,stable_level_violations=viol,sndr_db=float(10*np.log10(sig/noise)),sfdr_db=float(10*np.log10(sig/spur)),normalized_enob_bits=float((10*np.log10(1024/noise)-1.76)/6.02));diag[kind]=dict(edges_s=edges.tolist(),codes=c.tolist(),spectrum_power=power.tolist(),tone_bin=tone)
            for k,l in [('sndr_db',17),('sfdr_db',21),('normalized_enob_bits',2.5)]:g[kind+'_'+k]=gate(q[k],l,'min','dB/bit',kind='amplitude_db' if k.endswith('_db') else 'linear')
        ok &= invalid==viol==0;values[kind]=q
    bad={k:[w for w in json.loads((ROOT/v/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in w] for k,v in groups.items()};ok &= not any(bad.values())
    write_json(CASE/'conversion_records.json',diag)
    return result(CASE,46,values,g,groups,ok,disallowed_warnings=bad,conversion_records_sha256=sha(CASE/'conversion_records.json'))

def run(step=.1e-9,reltol=1e-6):
    simulate_groups(46,CASE,{k:bench(k,step,reltol) for k in ['transition','ramp','sine_low','sine_high']});return extract()

if __name__=='__main__':
    design();update_case(46,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)));run()
