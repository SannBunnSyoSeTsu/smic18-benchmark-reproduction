"""Differential 4-bit flash converter at the original 50 MS/s conditions."""
from batch29 import *
from hd_cells import extract_hd
CASE=ROOT/'cases/27-flash-adc4bit';TASK=SOURCE/'sky130-flash-adc-4bit-50msps'

def design(comp_scale=1,mix_R=200e3,ladder_R=100,hold_pF=20,sample_scale=1):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C complete original nominal 16-code transfer, 90-point linearity and 32-point coherent dynamic records.',VDD_V=1.8,temperature_C=27,clock=dict(period_s=20e-9,delay_s=1e-12,rise_fall_s=20e-12,width_s=9.96e-9,source_ohm=50),output_load_F=10e-15,sample_offset_s=9e-9,transfer_first_sample_s=69e-9,transfer_codes=list(range(16)),linearity=dict(samples=90,first_sample_s=9e-9,ramp_diff_V=[-1.7,1.7],duration_s=1.8e-6),dynamic=dict(N=32,tone_bin=5,frequency_Hz=7.8125e6,first_sample_s=69e-9,amplitude_per_leg_V=.85,common_V=.9,phase_deg=0,stop_s=720e-9),power_window_s=[60e-9,720e-9],power_definition='Net delivered VDD and VREFP power; clock delivery diagnostic only. Original excludes input-driver energy.',sndr_min_dB=22,sfdr_min_dB=26,power_max_W=.005,inl_dnl_max_LSB=.5,fft='Original bins1..15 excluding DC and tone; Nyquist excluded by source contract.',nonrelaxable='Transfer all16codes correct; ramp all16monotonic with exactly15adjacenttransitions; finite rail-valid sampled outputs.',allowed='NativeMOS,positiveidealR/C,exactHDlogic; nobehavioralDUT',unmodeled=['mismatch','device noise','metastability statistics','PEX','PVT']))
    roles=dict(input=lut_size('n18',.18,14,100e-6),tail=lut_size('n18',.18,8,300e-6),latch_n=lut_size('n18',.18,10,100e-6),latch_p=lut_size('p18',.18,10,50e-6),sample_n=lut_size('n18',.18,8,2e-3),sample_p=lut_size('p18',.18,8,2e-3))
    w={k:q['rounded_W_um']*(sample_scale if k.startswith('sample') else comp_scale) for k,q in roles.items()}
    extract_hd(['INHDV1','INHDV16','NAND2HDV1','XOR2HDV1'],CASE)
    t=f'''simulator lang=spectre
subckt fa_comp (clk vinp vinn outp outn vdd vss)
MTAIL (tail clk vss vss) n18 w={w['tail']:g}u l=.18u
MIN1 (dx vinp tail vss) n18 w={w['input']:g}u l=.18u
MIN2 (dy vinn tail vss) n18 w={w['input']:g}u l=.18u
MNL1 (outn outp dx vss) n18 w={w['latch_n']:g}u l=.18u
MNL2 (outp outn dy vss) n18 w={w['latch_n']:g}u l=.18u
MPL1 (outn outp vdd vdd) p18 w={w['latch_p']:g}u l=.18u
MPL2 (outp outn vdd vdd) p18 w={w['latch_p']:g}u l=.18u
MPC1 (outn clk vdd vdd) p18 w={w['latch_p']:g}u l=.18u
MPC2 (outp clk vdd vdd) p18 w={w['latch_p']:g}u l=.18u
MPC3 (dx clk vdd vdd) p18 w={w['latch_p']:g}u l=.18u
MPC4 (dy clk vdd vdd) p18 w={w['latch_p']:g}u l=.18u
ends fa_comp
subckt fa_sr (sn rn q qb vdd vss)
XG1 (sn qb q vdd vss vdd vss) NAND2HDV1
XG2 (rn q qb vdd vss vdd vss) NAND2HDV1
ends fa_sr
subckt fa_sample (a b en enb vdd vss)
MN (a en b vss) n18 w={w['sample_n']/4:g}u l=.18u m=4
MP (a enb b vdd) p18 w={w['sample_p']/4:g}u l=.18u m=4
ends fa_sample
subckt flash_adc_4bit (clk dout3 dout2 dout1 dout0 vss vdd vinn vinp vrefn vrefp)
XCLK (clk clks vdd vss vdd vss) INHDV16
XSP (vinp vhp clks clk vdd vss) fa_sample
XSN (vinn vhn clks clk vdd vss) fa_sample
CHP (vhp s8) capacitor c={hold_pF:g}p
CHN (vhn s8) capacitor c={hold_pF:g}p
'''
    nodes=['vrefn']+[f's{i}' for i in range(1,16)]+['vrefp']
    for i in range(16):t+=f'RL{i+1} ({nodes[i+1]} {nodes[i]}) resistor r={ladder_R:g}\n'
    for i in range(1,16):
        for pol,src,ref in [('p','vhp',16-i),('n','vhn',i)]:t+=f'R{i}{pol}A ({src} v{pol}{i}) resistor r={mix_R:g}\nR{i}{pol}B (s{ref} v{pol}{i}) resistor r={mix_R:g}\n'
        t+=f'XC{i} (clk vp{i} vn{i} cp{i} cn{i} vdd vss) fa_comp\nXS{i} (cn{i} cp{i} q{i} qb{i} vdd vss) fa_sr\n'
    # Balanced parity trees: bit j is XOR of all thermometer entries at 2^j multiples.
    for bit in range(4):
        ns=[f'q{i}' for i in range(2**bit,16,2**bit)];level=0
        while len(ns)>1:
            nxt=[]
            for i in range(0,len(ns),2):
                if i+1==len(ns):nxt.append(ns[i]);continue
                z=f'b{bit}l{level}n{i//2}';t+=f'XE{bit}_{level}_{i} ({ns[i]} {ns[i+1]} {z} vdd vss vdd vss) XOR2HDV1\n';nxt.append(z)
            ns=nxt;level+=1
        t+=f'XB{bit}a ({ns[0]} outb{bit} vdd vss vdd vss) INHDV1\nXB{bit}b (outb{bit} dout{bit} vdd vss vdd vss) INHDV1\n'
    t+='ends flash_adc_4bit\n'
    save_design(CASE,t,roles,dict(comp_scale=comp_scale,mix_R=mix_R,ladder_R=ladder_R,hold_pF=hold_pF,sample_scale=sample_scale),'Native gmID StrongARM bank; complementary transmission-gate shared differential track/hold; resistive summing pairs compare differential held input to antisymmetric ladder thresholds. Exact native HD SR cells store decisions and balanced XOR thermometer parity trees encode binary output.')
    update_case(27,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))

def bench(kind,step=100e-12,reltol=1e-5):
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{CASE/'hd_cells.scs'}"
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
VREFP (vrefp 0) vsource dc=1.8
VCM (vcm 0) vsource dc=.9
VCLK (clk_src 0) vsource type=pulse val0=0 val1=1.8 delay=1p rise=20p fall=20p width=9.96n period=20n
RCLK (clk_src clk) resistor r=50
X (clk d3 d2 d1 d0 0 vdd vinn vinp 0 vrefp) flash_adc_4bit
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14 gmin=1e-15
saveOptions options save=selected
save d0 d1 d2 d3 vinp vinn clk_src clk VDD:p VREFP:p VCLK:p X.vhp X.vhn
'''
    for i in range(4):b+=f'C{i} (d{i} 0) capacitor c=10f\n'
    if kind=='transfer':
        pts=[(0,.05625)]
        for i in range(1,16):pts += [(55+20*i,.05625+.1125*(i-1)),(55.1+20*i,.05625+.1125*i)]
        pts.append((400,1.74375));stop=400e-9
    elif kind=='linearity':pts=[(0,.05),(1800,1.75)];stop=1800e-9
    else:
        b+='VINP (vinp vcm) vsource dc=0 type=sine ampl=.85 freq=7.8125M\nVINN (vinn vcm) vsource dc=0 type=sine ampl=.85 freq=7.8125M sinephase=180\n';stop=720e-9;pts=None
    if pts:
        for pol in ['p','n']:b+=f'VIN{pol.upper()} (vin{pol} 0) vsource type=pwl wave=['+' '.join(f'{x:g}n {(v if pol=="p" else 1.8-v):.12g}' for x,v in pts)+']\n'
    return b+f'tran tran stop={stop:g} maxstep={step:g} method=gear2only errpreset=conservative\n'

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());values={};records={};g={};ok=True
    for k,path in runs.items():
        d=data(ROOT/path,'tran.tran');t=d['time'];times=((9+20*np.arange(90)) if k=='linearity' else (69+20*np.arange(16 if k=='transfer' else 32)))*1e-9
        v=np.array([np.interp(times,t,d[f'd{i}']) for i in range(4)]);codes=2**np.arange(4)@(v>.9);invalid=int(np.sum((v>.36)&(v<1.44)));ok &= invalid==0;q=dict(invalid_levels=invalid);r=dict(times_s=times.tolist(),codes=codes.tolist())
        if k=='transfer':q.update(code_errors=int(np.sum(codes!=np.arange(16))),missing_codes=16-len(set(codes)));ok &= q['code_errors']==q['missing_codes']==0
        elif k=='linearity':
            inp=np.interp(times,t,d['vinp']-d['vinn']);changes=np.flatnonzero(np.diff(codes)!=0);before=codes[changes];after=codes[changes+1];threshold=(inp[changes]+inp[changes+1])/2;valid=bool(np.array_equal(before,np.arange(15)) and np.array_equal(after,np.arange(1,16)) and len(set(codes))==16);ok &= valid
            q.update(linearity_valid=valid,transition_count=len(changes),missing_codes=16-len(set(codes)),monotonic=bool(np.all(np.diff(codes)>=0)))
            if valid:
                lsb=(threshold[-1]-threshold[0])/14;q['inl_LSB']=float(max(abs(threshold-threshold[0]-np.arange(15)*lsb))/lsb);q['dnl_LSB']=float(max(abs(np.diff(threshold)/lsb-1)))
                for key in ['inl_LSB','dnl_LSB']:g[key]=gate(q[key],.5,'max','LSB')
            r.update(input_diff_V=inp.tolist(),thresholds_V=threshold.tolist())
        else:
            p=abs(np.fft.rfft(codes-np.mean(codes)))**2;signal=p[5];noise=sum(p[1:16])-signal;spur=max([p[i] for i in range(1,16) if i!=5]);q.update(sndr_dB=float(10*np.log10(signal/noise)),sfdr_dB=float(10*np.log10(signal/spur)))
            a,z=60e-9,720e-9;tt=np.r_[a,t[(t>a)&(t<z)],z];avg=lambda v:float(np.trapz(np.interp(tt,t,v),tt)/(z-a))
            q['power_W']=avg(-1.8*(d['VDD:p']+d['VREFP:p']));q['clock_power_W']=avg(-d['clk_src']*d['VCLK:p']);ok &= q['power_W']>=0;r['spectrum_power']=p.tolist()
            for key,limit in [('sndr_dB',22),('sfdr_dB',26)]:g[key]=gate(q[key],limit,'min','dB',kind='amplitude_db')
            g['power']=gate(q['power_W'],.005,'max','W')
        values[k]=q;records[k]=r
    write_json(CASE/'conversion_records.json',records)
    warnings={k:[x for x in json.loads((ROOT/v/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in x] for k,v in runs.items()};ok &= not any(warnings.values())
    return result(CASE,27,values,g,runs,ok,disallowed_warnings=warnings,conversion_records_sha256=sha(CASE/'conversion_records.json'))

def run(step=100e-12,reltol=1e-5):
    simulate_groups(27,CASE,{k:bench(k,step,reltol) for k in ['transfer','linearity','dynamic']});return extract()

if __name__=='__main__':design();run()
