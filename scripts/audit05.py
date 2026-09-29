from audit29_common import *
import importlib.util
CASE=ROOT/'cases/05-bootstrap-driver'

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];independent={};edge_records={}
    for label,path in r['groups'].items():
        d=data(ROOT/path,'tran.tran');t=d['time'];a,z=.5e-6,1e-6;tt=np.r_[a,t[(t>a)&(t<z)],z];v={k:np.interp(tt,t,value) for k,value in d.items()};gs=v['hi_g']-v['vsw'];on=(v['vsw']>.9).astype(float)
        integrate=lambda x:float(np.sum(np.diff(tt)*(x[:-1]+x[1:])*.5))
        def crossing(x,sign):
            result=[]
            for i in range(len(tt)-1):
                if (sign>0 and x[i]<=.9<x[i+1]) or (sign<0 and x[i]>=.9>x[i+1]):result.append(float(tt[i]+(.9-x[i])*(tt[i+1]-tt[i])/(x[i+1]-x[i])))
            return result
        hr,hf,lr,lf=crossing(gs,1),crossing(gs,-1),crossing(v['lo_g'],1),crossing(v['lo_g'],-1)
        assert all(len(x)==5 for x in [hr,hf,lr,lf]);hl=[b-a for a,b in zip(hf,lr)];lh=[b-a for a,b in zip(lf,hr)];assert min(hl+lh)>0
        q=dict(VGS_avg_V=integrate(gs*on)/integrate(on),power_W=abs(1.8*integrate(v['VDDDUT:p'])/(z-a)),VGS_peak_V=float(np.max(gs)),HS_peak_A=float(np.max(np.abs(v['VHS:p']))),VBST_cap_peak_V=float(np.max(v['vbst']-v['vlx'])),GN2_peak_V=float(np.max(v['lo_g'])),VBST_peak_V=float(np.max(v['vbst'])),dead_HL_s=lr[1]-hf[1],dead_LH_s=hr[1]-lf[1],dead_all_min_s=min(hl+lh),dead_all_max_s=max(hl+lh),high_fraction=integrate(on)/(z-a))
        for key,value in q.items():compare(checks,label+'_'+key,r['values'][label][key],value)
        independent[label]=q;edge_records[label]=dict(HS_rise_s=hr,HS_fall_s=hf,LS_rise_s=lr,LS_fall_s=lf,source_rule='FALL=2 to RISE=2 in the unchanged0.5–1us window; matched-index events, no nearest-edge substitution.')
        net=(ROOT/path/'inputs/bench.scs').read_text();assert 'MHS (vdd_hs hi_g vsw ext_vlx2) n18 w=50u l=.18u m=450' in net and 'MLS (vsw lo_g 0 0) n18 w=50u l=.18u m=450' in net and net.count('inductor l=2n')==2 and net.count('inductor l=.3n')==2 and 'resistor r=3.6' in net
    # Independent recursive expansion includes exact vendor MOS geometry,
    # both delay-chain occurrences, each floating buffer and the MOS capacitor.
    blocks=drawing.parse_source(CASE/'circuit.scs');blocks.update(drawing.parse_source(CASE/'hd_cells.scs'));area_rows=[]
    def expand(name,path=''):
        for n,d in blocks[name]['instances'].items():
            p=d['parameters'];model=d['model'];full=path+n
            if model in blocks:expand(model,full+'/')
            else:
                assert model in ['n18','p18','n33','p33','mim'],model
                wl=drawing.numeric(p['w'])*drawing.numeric(p['l'])*drawing.numeric(p.get('m','1'))*1e12;area_rows.append(dict(instance=full,model=model,area_um2=wl))
    expand('bootstrap_driver');total=sum(x['area_um2'] for x in area_rows);compare(checks,'expanded_WLm_area_um2',r['area_um2'],total);assert total<=35000
    vals=list(independent.values());low=lambda k:min(x[k] for x in vals);high=lambda k:max(x[k] for x in vals)
    original=[('deadtime_3to7ns',min(low('dead_HL_s'),low('dead_LH_s'))>=3e-9 and max(high('dead_HL_s'),high('dead_LH_s'))<=7e-9),('power_below3p5mW',high('power_W')<.0035),('mean_VGS_min1p65V',low('VGS_avg_V')>=1.65),('mean_VGS_max1p85V',high('VGS_avg_V')<=1.85),('VGS_peak_below2p15V',high('VGS_peak_V')<2.15),('HS_peak_below0p8A',high('HS_peak_A')<.8),('1p8V_node_peaks',high('VBST_cap_peak_V')<2.15 and high('GN2_peak_V')<2.15),('source_VBST_below5p65V',high('VBST_peak_V')<5.65)]
    tier=r['status'].removeprefix('complete_');f={'original':0,'10pct':.1,'15pct':.15}[tier]
    assert low('VGS_avg_V')>=1.65*(1-f) and high('VGS_avg_V')<=1.85*(1+f) and high('power_W')<.0035*(1+f)
    assert min(low('dead_HL_s'),low('dead_LH_s'))>=3e-9*(1-f) and max(high('dead_HL_s'),high('dead_LH_s'))<=7e-9*(1+f)
    assert all(p for _,p in original[3:]) and high('VBST_peak_V')<3.63
    return finish(CASE,5,checks,[dict(name=n,passed=bool(p)) for n,p in original],'Independent trapezoid sums, explicit second-fall/second-rise times, five-edge count per polarity and peak searches on actual traces. Original eight electrical inequalities recorded truthfully for three nominal PWM widths. Independent full DUT hierarchy/HD WLm area expansion; model/source hashes and numerical confirmation checked. Peak guards and native3.63V absolute-node screen never relaxed; no lifetime or PVT signoff.',dict(independent_values=independent,edges=edge_records,independent_area_um2=total,area_leaves=area_rows,selected_tier=tier))

if __name__=='__main__':main()
