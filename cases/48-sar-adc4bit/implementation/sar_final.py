"""Native SMIC18 asynchronous SARs; exact vendor HD sequencing and storage."""
from batch29 import *
from hd_cells import extract_hd

ORDER4=[0,11,4,15,2,9,6,13,1,8,5,14,3,10,7,12]
ALT4=[15,0,8,7,3,12,5,10,1,14,6,9,2,13,4,11]

def context(bits):
    slot=48 if bits==4 else 42
    return slot,ROOT/f'cases/{slot:02d}-sar-adc{bits}bit',SOURCE/f'sky130-sar-adc-{bits}bit-async'

def order(bits,alt=False):
    return (ALT4 if alt else ORDER4) if bits==4 else [((21 if alt else 37)*i+(47 if alt else 11))%64 for i in range(64)]

def design(bits,unit_fF=50,dummy_fF=35,sample_scale=1,cmp_scale=1,delay_fF=70,bootstrap=False):
    slot,case,task=context(bits)
    if not (case/'contract.json').exists():
        freeze_case(case,task,dict(source_task=task.name,scope=f'SMIC18 TT 1.8V 27C; all {2**bits} code centers in both original orders with original post-acquisition decoys; original nominal coherent dynamic records. '+('SS/FF source corners excluded from nominal reproduction.' if bits==4 else 'All source nominal signoff groups retained.'),bits=bits,VDD_V=1.8,temperature_C=27,clock=dict(period_s=10e-9,delay_s=1e-12,rise_fall_s=20e-12,width_s=1.98e-9,source_ohm=50),load_per_output_F=10e-15,input_common_V=.9,input_dynamic_per_leg_amplitude_V=.85,transfer_orders=[order(bits),order(bits,True)],decoy_offsets=[8,5] if bits==4 else [32,17],decoy_start_ns=2.2,decoy_end_ns=2.25,next_input_start_ns=7.5 if bits==4 else 9.25,next_input_end_ns=7.55 if bits==4 else 9.3,decode_offset_ns=14.5 if bits==4 else 9,dynamic_samples=32 if bits==4 else 64,dynamic_bins=[15,13] if bits==4 else [31],dynamic_phases_deg=[0,17] if bits==4 else [0],dynamic_first_decode_ns=44.5 if bits==4 else 29,power_window_ns=[39.5,359.5] if bits==4 else [19.5,179.5],power_definition='Signed net delivered energy summed over VDD,VREFP,VCM,VINP,VINN,VCLKS; no omitted input/clock power.',sndr_min_dB=24 if bits==4 else 35,sndr_strict=bits==4,normalized_enob_min_bits=3.90 if bits==4 else 5.90,power_max_W=.005 if bits==4 else .003,power_strict=bits==6,fft='Rectangular, DC removed; bins 1..N/2-1 except tone plus half Nyquist; P_FS=(N*2^bits/4)^2.',nonrelaxable='Exact sample-hold codes in BOTH orders, all groups finite, digital sample levels outside [0.2VDD,0.8VDD], correct reset and conversion timing.',allowed='Native MOS and positive ideal capacitors; unmodified HD vendor cells for all digital logic.',unmodeled=['device noise','mismatch','PEX','metastability statistics','reference impedance']))
    roles=dict(input=lut_size('n18',.18,14,100e-6),tail=lut_size('n18',.18,8,300e-6),latch_n=lut_size('n18',.18,10,100e-6),latch_p=lut_size('p18',.18,10,50e-6),sample_n=lut_size('n18',.18,8,250e-6),sample_p=lut_size('p18',.18,8,250e-6),dac_n=lut_size('n18',.18,8,25e-6),dac_p=lut_size('p18',.18,8,25e-6))
    if bootstrap:roles.update(boot_n=lut_size('n18',.18,8,200e-6,.9),boot_p=lut_size('p18',.18,8,200e-6,.9))
    w={k:q['rounded_W_um']*(sample_scale if k.startswith('sample') else cmp_scale if k in ['input','tail','latch_n','latch_p'] else 1) for k,q in roles.items()}
    cells=['INHDV1','INHDV4','INHDV8','AND2HDV1','OR2HDV2','DQHDV1','DRNQHDV1']
    if bits==6:cells += ['OR2HDV4','DRNQHDV2']
    extract_hd(cells,case)
    lines=['simulator lang=spectre']
    def add(s):lines.extend(s.strip().splitlines())
    def hd(n,p,m):add(f'X{n} ({p} vdd vss vdd vss) {m}')
    def mos(n,p,role):add(f'M{n} ({p}) {roles[role]["model"]} w={w[role]:.8g}u l=.18u')
    add('subckt sar_cmp (clk outn outp vss vdd vinn vinp)')
    mos('TAIL','tail clk vss vss','tail')
    mos('INP','dx vinp tail vss','input');mos('INN','dy vinn tail vss','input')
    mos('LN','ln lp dx vss','latch_n');mos('LP','lp ln dy vss','latch_n')
    mos('PN','ln lp vdd vdd','latch_p');mos('PP','lp ln vdd vdd','latch_p')
    for n in ['dx','dy','ln','lp']:mos('RST_'+n,f'{n} clk vdd vdd','latch_p')
    hd('ON','ln outp','INHDV4');hd('OP','lp outn','INHDV4')
    add('ends sar_cmp')
    add('subckt sar_sample (clk clkb vin vout vdd vss)')
    if bootstrap:
        add('CBOOT (cbt cbb) capacitor c=1.5p')
        for n,p,role,mul in [('DCHG','cbb clkb vss vss','boot_n',1),('PCHG','cg clk vdd vdd','boot_p',1),('LIM','vdd vg cbt cbt','boot_p',1),('PRE','vdd clk pre vss','boot_n',2),('GTRK','cg clk cbb vss','boot_n',2),('BPP','vg cg cbt cbt','boot_p',1),('PVIN','cbb vg vin vss','boot_n',2),('CASC','vg vdd clk vss','boot_n',2),('GUARD','vg vdd pre vss','boot_n',2)]:add(f'M{n} ({p}) {roles[role]["model"]} w={w[role]:.8g}u l=.18u m={mul}')
        mos('SN','vout vg vin vss','sample_n')
    else:
        mos('SN','vout clk vin vss','sample_n');mos('SP','vout clkb vin vdd','sample_p')
    add('ends sar_sample')
    cp=' '.join(f'dctrl{i}' for i in range(bits-1,0,-1))
    add(f'subckt sar_cdac (clks clkb {cp} vss vdd vin vrefn vrefp vtop)\nXS (clks clkb vin vtop vdd vss) sar_sample\nCD (vtop vss) capacitor c={dummy_fF:g}f')
    for i in range(1,bits):
        mul=2**(i-1)
        add(f'C{i} (vtop bot{i}) capacitor c={unit_fF*mul:g}f')
        for pol in ['n','p']:
            m='n18' if pol=='n' else 'p18';ref='vrefn' if pol=='n' else 'vrefp';bulk='vss' if pol=='n' else 'vdd'
            add(f'M{pol.upper()}{i} (bot{i} dctrl{i} {ref} {bulk}) {m} w={w["dac_"+pol]*mul:.8g}u l=.18u')
    add('ends sar_cdac')
    npins=' '.join(f'dctrln{i}' for i in range(bits-1,0,-1));ppins=npins.replace('dctrln','dctrlp');outs=' '.join(f'do{i}' for i in range(bits-1,-1,-1))
    add(f'subckt sar_logic (clkc cmpck dcmpn dcmpp {npins} {ppins} {outs} vss vdd)')
    hd('GATE','clkc rdyb clk_gate','AND2HDV1');hd('LOOP','nvalid clk_gate loop','AND2HDV1')
    hd('VALID','dcmpp dcmpn valid','OR2HDV4' if bits==6 else 'OR2HDV2');hd('NVALID','valid nvalid','INHDV1')
    hd('RDY','clk0 rdyb','INHDV1')
    hd('DELAY1','loop delay1','INHDV1');add(f'CDEL (delay1 vss) capacitor c={delay_fF:g}f');hd('DELAY2','delay1 cmpck','INHDV8')
    for i in range(bits-1,-1,-1):
        hd(f'SEQ{i}',f'valid '+('vdd' if i==bits-1 else f'clk{i+1}')+f' clk{i} clkc','DRNQHDV2' if bits==6 else 'DRNQHDV1')
        for pol in ['p','n']:
            other='n' if pol=='p' else 'p';d=f'dcmp{other if i==bits-1 else pol}'
            q=f'dctrl{pol}{i}';raw=q+'_raw'
            if i==0:
                hd(f'DEC{pol}{i}',f'clk0 {d} {raw}','DQHDV1');hd(f'LSB{pol}',f'{raw} clk0 {q}','AND2HDV1')
            else:
                hd(f'DEC{pol}{i}',f'clk{i} {d} '+(raw if i==bits-1 else q)+' clkc','DRNQHDV1')
                if i==bits-1:hd(f'MSB{pol}',f'{raw} {q}','INHDV8')
    hd('EOC','clk0 nvalid eoc','AND2HDV1')
    for i in range(bits):hd(f'OUT{i}',f'eoc dctrlp{i} do{i}','DQHDV1')
    add('ends sar_logic')
    topouts=' '.join(f'dout{i}' for i in range(bits-1,-1,-1))
    add(f'subckt sar_adc_{bits}bit_async (clks {topouts} vss vdd vinn vinp vrefn vrefp)')
    hd('CLKC','clks clkc','INHDV8')
    add(f'XCMP (cmpck dcmpn dcmpp vss vdd vresn vresp) sar_cmp\nXDP (clks clkc {ppins} vss vdd vinp vrefn vrefp vresp) sar_cdac\nXDN (clks clkc {npins} vss vdd vinn vrefn vrefp vresn) sar_cdac\nXLOG (clkc cmpck dcmpn dcmpp {npins} {ppins} {topouts} vss vdd) sar_logic\nends sar_adc_{bits}bit_async')
    save_design(case,'\n'.join(lines)+'\n',roles,dict(bits=bits,unit_fF=unit_fF,dummy_fF=dummy_fF,sample_scale=sample_scale,cmp_scale=cmp_scale,delay_fF=delay_fF,bootstrap=bootstrap),'Native gm/ID sets comparator regenerative/input roles and analog sampling/CDAC switch current scales. Dynamic devices do not have a constant gm/ID. Differential top-plate sampling uses '+('a protected native bootstrapped NMOS with1.5pF storage.' if bootstrap else 'native complementary transmission gates.')+' Binary CDAC plus dummy accommodates top-node parasitics. Original VALID-driven two-row controller and EOC register are mapped to unmodified vendor HD cells; explicit capacitor sets asynchronous return delay.')
    update_case(slot,status='running',nominal_complete=False,case_dir=str(case.relative_to(ROOT)))

def bench(bits,kind,step=50e-12,reltol=1e-6,chunk=0,debug=False):
    slot,case,task=context(bits)
    b=f'''simulator lang=spectre
global 0
include "{MODEL}" section=tt
include "{case/'hd_cells.scs'}"
include "{case/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
VREFP (vrefp 0) vsource dc=1.8
VCLKS (clks_src 0) vsource type=pulse val0=0 val1=1.8 delay=1p rise=20p fall=20p width=1.98n period=10n
RCLKS (clks_src clks) resistor r=50
X (clks {' '.join(f'd{i}' for i in range(bits-1,-1,-1))} 0 vdd vinn vinp 0 vrefp) sar_adc_{bits}bit_async
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14 gmin=1e-15
saveOptions options save=selected
save clks_src clks vinp vinn vcm {' '.join(f'd{i}' for i in range(bits))} VDD:p VREFP:p VINP:p VINN:p VCLKS:p
'''
    b+=''.join(f'C{i} (d{i} 0) capacitor c=10f\n' for i in range(bits))
    if debug:b+='save X.cmpck X.dcmpp X.dcmpn X.vresp X.vresn X.clkc X.XLOG.valid X.XLOG.eoc X.XLOG.delay1 '+' '.join(f'X.XLOG.clk{i} X.dctrlp{i} X.dctrln{i}' for i in range(bits))+'\n'
    if kind.startswith('transfer'):
        alt=kind=='transfer_alt';codes=order(bits,alt);offset=([8,5] if bits==4 else [32,17])[int(alt)];start=20 if bits==4 else 10
        prev=None
        if bits==6:
            prev=codes[16*chunk-1] if chunk else None;codes=codes[16*chunk:16*(chunk+1)]
        v=lambda c:(c+.5)/2**bits*1.8
        pts=[(0,v(codes[0] if prev is None else prev))]
        if prev is not None:pts += [(2.2,v(prev)),(2.25,v((prev+offset)%2**bits)),(9.25,v((prev+offset)%2**bits)),(9.3,v(codes[0]))]
        for i,c in enumerate(codes):
            t=start+10*i;decoy=v((c+offset)%2**bits);pts += [(t+2.2,v(c)),(t+2.25,decoy)]
            if i<len(codes)-1:pts += [(t+(7.5 if bits==4 else 9.25),decoy),(t+(7.55 if bits==4 else 9.3),v(codes[i+1]))]
        for pol in ['P','N']:b+=f'VIN{pol} (vin{pol.lower()} 0) vsource type=pwl wave=['+' '.join(f'{t:g}n {(x if pol=="P" else 1.8-x):.12g}' for t,x in pts)+']\n'
        b+='VCM (vcm 0) vsource dc=.9\n';stop=189.5e-9 if bits==4 else 169.5e-9
    else:
        N=32 if bits==4 else 64;tone=(15 if kind=='dynamic' else 13) if bits==4 else 31;freq=100e6*tone/N;phase=(0 if kind=='dynamic' else 17) if bits==4 else (360*tone*16*chunk/N)%360
        b+=f'VCM (vcm 0) vsource dc=.9\nVINP (vinp vcm) vsource dc=0 type=sine ampl=.85 freq={freq:g} sinephase={phase:g}\nVINN (vinn vcm) vsource dc=0 type=sine ampl=.85 freq={freq:g} sinephase={phase+180:g}\nsave VCM:p\n';stop=360e-9 if bits==4 else 179.5e-9
    return b+f'tran tran stop={stop:g} maxstep={step:g} method=gear2only errpreset=conservative\n'

def groups(bits):
    return [(k,0) for k in ['transfer','transfer_alt','dynamic','dynamic_alt']] if bits==4 else [(k,c) for k in ['transfer','transfer_alt','dynamic'] for c in range(4)]

def extract(bits):
    slot,case,task=context(bits);runs=json.loads((case/'latest_runs.json').read_text());values={};gates={};records={};guards=True;all_codes={};powers=[]
    for kind,chunk in groups(bits):
        label=kind if bits==4 else kind+str(chunk);d=data(ROOT/runs[label],'tran.tran');t=d['time'];N=(16 if kind.startswith('transfer') or bits==6 else 32)
        first=(34.5 if kind.startswith('transfer') else 44.5) if bits==4 else (19 if kind.startswith('transfer') else 29)
        times=(first+10*np.arange(N))*1e-9;levels=np.array([np.interp(times,t,d[f'd{i}']) for i in range(bits)]);codes=2**np.arange(bits)@(levels>.9);invalid=int(np.sum((levels>.36)&(levels<1.44)));guards &= invalid==0
        rec=dict(sample_times_s=times.tolist(),codes=codes.tolist(),invalid_levels=invalid,analog_sample_levels_V=levels.tolist());q=dict(invalid_levels=invalid)
        if kind.startswith('transfer'):
            exp=order(bits,kind=='transfer_alt');exp=exp if bits==4 else exp[16*chunk:16*(chunk+1)];q['code_errors']=int(np.sum(codes!=exp));guards &= q['code_errors']==0;rec['expected']=exp
        else:
            a,z=([39.5e-9,359.5e-9] if bits==4 else [19.5e-9,179.5e-9]);mask=(t>a)&(t<z);tt=np.r_[a,t[mask],z]
            source=-1.8*(d['VDD:p']+d['VREFP:p'])-.9*d['VCM:p']-(d['vinp']-.9)*d['VINP:p']-(d['vinn']-.9)*d['VINN:p']-d['clks_src']*d['VCLKS:p']
            q['power_W']=float(np.trapz(np.interp(tt,t,source),tt)/(z-a));guards &= q['power_W']>=0
            all_codes.setdefault(kind,[]).extend(codes.tolist());powers.append(q['power_W'])
        records[label]=rec;values[label]=q
    for kind,c in all_codes.items():
        N=len(c);tone=(15 if kind=='dynamic' else 13) if bits==4 else 31;spec=np.fft.rfft(np.array(c)-np.mean(c));p=abs(spec)**2;sig=p[tone];noise=float(sum(p[1:N//2])-sig+.5*p[N//2]);sndr=float(10*np.log10(sig/noise));enob=float((10*np.log10((N*2**bits/4)**2/noise)-1.76)/6.02)
        values[kind+'_spectrum']=dict(sndr_dB=sndr,normalized_enob_bits=enob,signal_power=float(sig),noise_power=noise,tone_bin=tone);records[kind+'_spectrum']=dict(codes=c,spectrum_power=p.tolist())
        gg=gate(sndr,24 if bits==4 else 35,'min','dB',kind='amplitude_db');gates[kind+'_sndr']=strict(gg) if bits==4 else gg
        gates[kind+'_enob']=strict(gate(enob,3.9 if bits==4 else 5.9,'min','bit'))
    gg=gate(max(powers),.005 if bits==4 else .003,'max','W');gates['power']=strict(gg) if bits==6 else gg
    write_json(case/'conversion_records.json',records)
    warnings={k:[x for x in json.loads((ROOT/v/'run.json').read_text())['warnings'] if 'SPECTRE-16780' not in x] for k,v in runs.items()};guards &= not any(warnings.values())
    return result(case,slot,values,gates,runs,guards,disallowed_warnings=warnings,conversion_records_sha256=sha(case/'conversion_records.json'))

def run(bits,step=50e-12,reltol=1e-6):
    slot,case,_=context(bits);simulate_groups(slot,case,{k if bits==4 else k+str(c):bench(bits,k,step,reltol,c) for k,c in groups(bits)});return extract(bits)

def probe(bits,kind='transfer',chunk=0,reltol=1e-5):
    slot,case,_=context(bits);b=bench(bits,kind,chunk=chunk,debug=True,reltol=reltol);rd=run_spectre(slot,'probe_'+kind,b,[case/x for x in ['circuit.scs','sizing.json','contract.json','hd_cells.scs','hd_cells_manifest.json']],timeout=1800);write_json(case/'probe_run.json',dict(run=str(rd.relative_to(ROOT))))
    d=data(rd,'tran.tran');first=(34.5 if kind.startswith('transfer') else 44.5) if bits==4 else (19 if kind.startswith('transfer') else 29);N=16 if kind.startswith('transfer') or bits==6 else 32;v=np.array([np.interp((first+10*np.arange(N))*1e-9,d['time'],d[f'd{i}']) for i in range(bits)]);print(rd, (2**np.arange(bits)@(v>.9)).tolist(),flush=True);return rd
