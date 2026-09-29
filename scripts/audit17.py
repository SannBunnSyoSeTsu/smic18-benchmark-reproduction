from audit29_common import *
import importlib.util
CASE=ROOT/'cases/17-nmos-ldo'

def interpolation(f,y,x,target):
    inds=np.flatnonzero(np.diff((x>=target).astype(int))==-1);assert len(inds)
    j=int(inds[0]);xx=x[j:j+2][::-1]
    return float(np.interp(target,xx,f[j:j+2][::-1])),float(np.interp(target,xx,y[j:j+2][::-1]))

def main():
    r=json.loads((CASE/'latest_results.json').read_text());checks=[];original=[];detail=[]
    sys.path.insert(0,str(CASE/'source/tests'));spec=importlib.util.spec_from_file_location('nmos_original',CASE/'source/tests/verify.py');up=importlib.util.module_from_spec(spec);sys.modules[spec.name]=up;spec.loader.exec_module(up)
    for row in r['values']['load_points']:
        ma=row['load_mA'];rd=ROOT/r['groups'][f'loop{ma}'];o=dc(rd);d=data(rd,'ac.ac');s=data(rd,'loop.stb');p=data(ROOT/r['groups'][f'psrr{ma}'],'ac.ac')
        assert len(d['freq'])==len(p['freq'])==len(s['freq'])==1441 and d['freq'][0]==1 and d['freq'][-1]==1e9
        # Independently use phasor quotient identity, then interpolate reversed two-point arrays.
        ratio=-(d['loop_out']*np.conj(d['pass_gate']))/(abs(d['pass_gate'])**2)
        out=dict(vout_V=o['vout'],iq_A=-(o['VDD:p']+ma*.001+40e-6))
        for name,f,z in [('loop',d['freq'],ratio),('stb',s['freq'],-s['loopGain'])]:
            mag=10*np.log10(z.real**2+z.imag**2);phase=np.unwrap(np.arctan2(z.imag,z.real))*180/np.pi
            fu,ph=interpolation(f,phase,mag,0);fp,gm=interpolation(f,mag,phase,-180)
            out.update({name+'_ugb_Hz':fu,('' if name=='loop' else 'stb_')+'phase_margin_deg':180+ph,('' if name=='loop' else 'stb_')+'gain_margin_db':-gm})
            assert len(np.flatnonzero(np.diff((mag>=0).astype(int))==-1))==1
            assert np.all(mag[f>fu]<0)
        idx=int(np.argmin(abs(p['freq']-1000)));assert abs(p['freq'][idx]-1000)<1e-8
        out['psrr_1k_dB']=-10*np.log10(p['vout'][idx].real**2+p['vout'][idx].imag**2)
        mos=[n for n,q in drawing.parse_source(CASE/'circuit.scs')['nmos_pass_ldo']['instances'].items() if q['model'] in ['n18','p18']]
        margins=[dict(device=n,current_A=o[f'X.{n}:ids'],margin_V=abs(o[f'X.{n}:vds'])-abs(o[f'X.{n}:vdsat'])) for n in mos if abs(o[f'X.{n}:ids'])>=1e-9]
        assert len(margins)==11;out['min_active_headroom_V']=min(q['margin_V'] for q in margins)
        for k,v in out.items():compare(checks,f'{ma}mA_{k}',row[k],v)
        tests=dict(output=up.OUTPUT_MIN_V<=out['vout_V']<=up.OUTPUT_MAX_V,iq=0<=out['iq_A']<up.IQ_MAX_A,stability=out['phase_margin_deg']>up.PHASE_MARGIN_MIN_DEG and out['gain_margin_db']>up.GAIN_MARGIN_MIN_DB,psrr=out['psrr_1k_dB']>up.PSRR_1KHZ_MIN_DB,headroom=out['min_active_headroom_V']>up.HEADROOM_MIN_V)
        for n,ok in tests.items():assert ok;original.append(dict(name=f'{ma}mA_{n}',passed=bool(ok),scope='Original constants/inequalities on explicit TT1.8V27C two-load subset; PVT/MC not claimed.'))
        detail.append(dict(load_mA=ma,active_mos=margins))
        net=(rd/'inputs/bench.scs').read_text()
        for line in [f'ILOAD (vout 0) isource dc={ma*.001:g}','CLOAD (vout 0) capacitor c=10p','IBIAS (ibias 0) isource dc=40u','VREF (vref 0) vsource dc=.4','VLOOP (loop_out probe) vsource dc=0 mag=1']:assert line in net
    finish(CASE,17,checks,original,'Independent complex-quotient identity, array interpolation, PSD PSRR and supply-current decomposition; original constants and strict inequalities applied to both nominal loads. First falling crossings and no unity recrossing verified. Signed Spectre return normalized as T=-loopGain. Full PVT/mismatch explicitly excluded.',dict(loads=detail,original_signoff_expected=54,executed_nominal_points=2,mismatch_samples_executed=0))

if __name__=='__main__':main()
