"""Add a bounded nominal MOS length table, keeping existing LUTs untouched."""
from common import *
from gmidsmic.characterize import OP_FIELDS,normalize
from gmidsmic.lut import monotone_branch
from gmidsmic.common import load_config
import argparse

def characterize(device,L,vds,slot,gmid_min=None,width=10):
    base=ROOT/'lut_supplement';suffix='' if width==10 else f'_W{width:.3f}'
    rel=Path('tt')/f'{device}_L{round(L*1000)}nm_VDS{vds:.3f}{suffix}.json'
    target=base/rel
    if target.exists():
        print('Existing supplemental LUT:',target);return target
    sign='-' if device.startswith('p') else ''
    text=f'''simulator lang=spectre
global 0
parameters VGS=0
include "{MODEL}" section=tt
VG (g 0) vsource dc={sign}VGS
VD (d 0) vsource dc={sign}{vds}
MCHAR (d g 0 0) {device} w={width}u l={L}u
simulatorOptions options temp=27 tnom=27 reltol=1e-5 vabstol=1e-8 iabstol=1e-15 gmin=1e-15
saveOptions options save=selected
save '''+' '.join('MCHAR:'+field for field in OP_FIELDS)+'''
characterize dc param=VGS start=0 stop=1.8 step=.002
'''
    run=run_spectre(slot,f'characterize_{device}_L{L:g}',text)
    d=data(run,'characterize.dc');curve=normalize(d,'MCHAR','VGS',width)
    assert np.allclose(curve['gmoverid_per_V'][curve['id_A']>1e-12],curve['gmoverid_derived_per_V'][curve['id_A']>1e-12],rtol=1e-9)
    cfg=load_config()
    if gmid_min is not None:cfg['lut']['gmid_min_per_V']=gmid_min
    arrays=monotone_branch(curve,cfg)
    metadata=dict(schema_version=1,process_library='smic18mmrf',device=device,polarity='pmos' if device.startswith('p') else 'nmos',corner='tt',temperature_C=27,vdd_V=1.8,body_bias_V=0,width_ref_um=width,length_um=L,vds_V=vds,simulator='Cadence Spectre via existing Virtuoso Bridge',model_library=str(MODEL),sign_convention='positive magnitudes',operating_region='saturation only; monotone gm/ID branch',npoints=len(arrays['gmid']),run_dir=str(run.relative_to(ROOT)),generated_at=now())
    write_json(target,dict(metadata=metadata,data={k:v.tolist() for k,v in arrays.items()}))
    index=json.loads((base/'index.json').read_text()) if (base/'index.json').exists() else dict(schema_version=1,description='Task-scoped supplementary SMIC18 nominal LUTs',tables=[])
    index['tables'].append({**{k:metadata[k] for k in ['device','corner','width_ref_um','length_um','vds_V','npoints']},'json':str(rel)})
    write_json(base/'index.json',index)
    print('Supplement:',target,'points:',metadata['npoints'])
    return target

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--device',default='n18');p.add_argument('--length',type=float,required=True);p.add_argument('--vds',type=float,default=.9);p.add_argument('--slot',type=int,required=True);p.add_argument('--gmid-min',type=float);p.add_argument('--width',type=float,default=10);a=p.parse_args()
    characterize(a.device,a.length,a.vds,a.slot,a.gmid_min,a.width)
