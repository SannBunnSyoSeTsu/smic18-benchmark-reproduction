"""Three-stage auto-zeroed ring amplifier, unchanged four-point SC fixture."""
from batch29 import *
CASE=ROOT/'cases/06-ring-amplifier';TASK=SOURCE/'sky130-ring-amp-3stage-gain8-400uw'

def design(input_scale=1,load_scale=1,tail_scale=.7,output_scale=1,feedback_fF=100):
    if not (CASE/'contract.json').exists():
        freeze_case(CASE,TASK,dict(source_task=TASK.name,scope='SMIC18 TT1.8V27C, all four original independent SC records +20,+10,0,-20mV with fixed 25uA sink, 10pF/side output load and bench-owned reset switches.',VDD_V=1.8,temperature_C=27,bias_sink_A=25e-6,input_cm_V=.9,output_cm_V=.9,input_diff_V=[.02,.01,0,-.02],period_s=500e-9,reset_duration_s=50e-9,input_edge_s=20e-12,output_load_per_side_F=10e-12,reset_switch=dict(Ron_ohm=100,Roff_ohm=1e12,threshold_V=.25,hysteresis_V=.1,transition_width_V=1e-6,reference_V=.5),stop_s=1.5e-6,output_mean_window_s=[1.4e-6,1.45e-6],power_window_s=[1.2e-6,1.45e-6],settling_start_s=1.05e-6,settling_band_fraction=.1,target_gain=8,gain_tolerance=.8,zero_max_V=.005,static_error_max_fraction=.01,output_cm_error_max_V=.05,power_max_W=400e-6,settle_max_s=50e-9,ripple_max_V=.005,nonrelaxable='Four transfer records required, both polarity targets and zero-input recovery; finite transient and actual settling-band entry.',allowed='NativeMOS plus positiveidealRCL; fixture-owned idealreset switches.',unmodeled=['PVT','mismatch','device noise','PEX']))
    roles=dict(input=lut_size('n18',.36,18,25e-6),nbias=lut_size('n18',.36,10,25e-6),pbias=lut_size('p18',.36,12,25e-6),ncas=lut_size('n18',.18,16,10e-6),pcas=lut_size('p18',.18,16,5e-6),nout=lut_size('n18',1,8,5e-6),pout=lut_size('p18',1,8,5e-6))
    roles['startup']=lut_size('n18',1,8,5e-6*.5/roles['nout']['W_um'])
    source=(TASK/'solution/circuit.spi').read_text();lines=['simulator lang=spectre'];mapping={}
    for raw in source.splitlines():
        z=raw.split()
        if not z or z[0].startswith('*'):continue
        if z[0].lower()=='.subckt':lines.append('subckt '+z[1]+' ('+' '.join(z[2:])+')')
        elif z[0].lower()=='.ends':
            lines.extend(['MSTARTP (vinp ibias vip vss) n18 w=.5u l=1u','MSTARTN (vinn ibias vin vss) n18 w=.5u l=1u','ends '+z[1]])
        elif z[0][0]=='X':
            n=z[0];pol='n' if n.startswith('XNM') else 'p';params=dict(re.findall(r'(w|l|nf)\s*=\s*([.\d]+)',raw));L=float(params['l']);W=float(params['w']);scale=1
            if n in ['XNM9','XPM7']:role=pol+'cas';scale=1
            elif n in ['XNM0','XNM1']:role='input';scale=input_scale
            elif L==.8:role=pol+'out';scale=output_scale
            elif L==.2:role=pol+'cas';scale=W/(20 if pol=='p' else 20)
            else:
                role=pol+'bias';scale=W/(20 if pol=='p' else 5)
                if n in ['XPM0','XPM3']:scale*=load_scale
                if n in ['XNM3','XNM14']:scale*=tail_scale
            q=roles[role];width=q['rounded_W_um']*scale;mapping[n]=dict(role=role,multiplier=scale,W_um=width,L_um=q['L_um'])
            lines.append('M'+n[1:]+' ('+' '.join(z[1:5])+f') {q["model"]} w={width:.8g}u l={q["L_um"]:g}u')
        elif z[0][0] in ['R','C','L']:
            model={'R':'resistor','C':'capacitor','L':'inductor'}[z[0][0]];val=f'{feedback_fF:g}f' if z[0] in ['C6','C7'] else z[3];lines.append(z[0]+' ('+' '.join(z[1:3])+f') {model} {z[0][0].lower()}={val}')
        else:raise ValueError(raw)
    for name in ['MSTARTP','MSTARTN']:mapping[name]=dict(role='startup',multiplier=1,W_um=.5,L_um=1)
    save_design(CASE,'\n'.join(lines)+'\n',roles,dict(input_scale=input_scale,load_scale=load_scale,tail_scale=tail_scale,output_scale=output_scale,feedback_fF=feedback_fF,instance_roles=mapping),'Source three-stage SC/ring signal topology and all reset terminals retained. Native LUT roles choose .18/.36/1um lengths with explicit instance ratios. Input and feedback capacitors set closed-loop gain; auto-zero stores second-stage gate biases; long-channel output devices reduce quiescent current. Matched cascode sizing restores differential symmetry. Two weak, bias-gated NMOS startup paths charge initially unpowered AC-coupled inputs during the unchanged zero-state transient; their conductance naturally falls as the inputs rise. No forced initial voltage or added ideal fixture source. Dynamic gmID is not constant.')
    update_case(6,status='running',nominal_complete=False,case_dir=str(CASE.relative_to(ROOT)))

def bench(diff,step=.25e-9,reltol=1e-6):
    b=f'''simulator lang=spectre
global 0
model SW_RESET relay ropen=1e12 rclosed=100 vth=.25 trans=1u hysteresis=.1
include "{MODEL}" section=tt
include "{CASE/'circuit.scs'}"
VDD (vdd 0) vsource dc=1.8
VCM (vcm 0) vsource dc=.9
V05 (v05 0) vsource dc=.5
IBIAS (ibias 0) isource dc=25u
VRST (rst 0) vsource type=pulse val0=1 val1=0 delay=50n rise=20p fall=20p width=450n period=500n
VINP (vinp 0) vsource type=pulse val0=.9 val1={.9+diff/2:.12g} delay=50n rise=20p fall=20p width=450n period=500n
VINN (vinn 0) vsource type=pulse val0=.9 val1={.9-diff/2:.12g} delay=50n rise=20p fall=20p width=450n period=500n
X (0 vdd vinp vinn voutp voutn ibias bn1 net4 net5 net7 net11 net13) ring_amp8
CLP (voutp 0) capacitor c=10p
CLN (voutn 0) capacitor c=10p
simulatorOptions options temp=27 tnom=27 reltol={reltol:g} vabstol=1e-8 iabstol=1e-14 gmin=1e-15 cmin=1f
saveOptions options save=selected
save vinp vinn voutp voutn rst ibias bn1 net4 net5 net7 net11 net13 VDD:p X.vop1 X.von1 X.vgp3 X.vgn3 X.net8 X.net10
'''
    for i,(p,n) in enumerate([('voutn','vcm'),('voutp','vcm'),('net4','bn1'),('net13','bn1'),('ibias','net11'),('net7','bn1'),('ibias','net5')]):b+=f'S{i} ({p} {n} rst v05) SW_RESET\n'
    return b+f'tran tran stop=1.5u maxstep={step:g} skipdc=yes method=gear2only errpreset=conservative\n'

def extract():
    runs=json.loads((CASE/'latest_runs.json').read_text());vals={};g={};ok=True
    for name,path in runs.items():
        diff={'pos20':.02,'pos10':.01,'zero':0,'neg20':-.02}[name];d=data(ROOT/path,'tran.tran');t=d['time'];vd=d['voutp']-d['voutn']
        def avg(v,a,z):
            tt=np.r_[a,t[(t>a)&(t<z)],z];return float(np.trapz(np.interp(tt,t,v),tt)/(z-a))
        mean=avg(vd,1.4e-6,1.45e-6);q=dict(mean_diff_V=mean)
        if abs(diff)==.02:
            tar=diff*8;er=abs(vd-tar)-abs(tar)*.1;inds=np.flatnonzero((er[:-1]>0)&(er[1:]<=0)&(t[:-1]>=1.05e-6)&(t[1:]<1.499e-6));settle=None
            if len(inds):i=inds[-1];settle=float(t[i]-er[i]*(t[i+1]-t[i])/(er[i+1]-er[i])-1.05e-6)
            ok &= settle is not None and np.interp(1.45e-6,t,er)<0
            sel=(t>=1.4e-6)&(t<=1.45e-6);q.update(static_error_fraction=abs(mean-tar)/abs(tar),cm_error_V=abs(avg((d['voutp']+d['voutn'])/2,1.4e-6,1.45e-6)-.9),power_W=abs(avg(1.8*d['VDD:p'],1.2e-6,1.45e-6)),settle_s=settle,ripple_V=float(max(abs(vd[sel]-mean))))
            for key,lim,unit in [('static_error_fraction',.01,'fraction'),('cm_error_V',.05,'V'),('power_W',400e-6,'W'),('settle_s',50e-9,'s'),('ripple_V',.005,'V')]:
                if q[key] is not None:g[name+'_'+key]=gate(q[key],lim,'max',unit)
        vals[name]=q
    if len(vals)==4:
        gp=(vals['pos20']['mean_diff_V']-vals['pos10']['mean_diff_V'])/.01;gb=(vals['pos20']['mean_diff_V']-vals['neg20']['mean_diff_V'])/.04;vals['transfer']=dict(positive_gain=gp,bipolar_gain=gb,zero_residual_V=abs(vals['zero']['mean_diff_V']))
        g['gain_positive_error']=gate(abs(gp-8),.8,'max','V/V');g['gain_bipolar_error']=gate(abs(gb-8),.8,'max','V/V');g['zero_residual']=gate(vals['transfer']['zero_residual_V'],.005,'max','V')
    else:ok=False
    return result(CASE,6,vals,g,runs,ok)

def run(step=.25e-9,reltol=1e-6):
    simulate_groups(6,CASE,{k:bench(d,step,reltol) for k,d in [('pos20',.02),('pos10',.01),('zero',0),('neg20',-.02)]});return extract()

if __name__=='__main__':design();run()
