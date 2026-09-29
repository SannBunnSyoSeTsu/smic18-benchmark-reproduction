"""SMIC18 project utilities; existing EDA environments are imported, never edited."""
from __future__ import annotations
import datetime as dt
import fcntl
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BRIDGE = WORKSPACE / 'virtuoso-bridge-lite'
LUT_ROOT = WORKSPACE / 'gmoverid_smic18'
SOURCE = WORKSPACE / 'Analog-Circuit-Knowledge-Base/Analog-Design-Bench-V2-Lessons/sources/upstream/tasks'
MODEL = Path('/home/IC/Tech/smic_018mmrf-OA/SMIC_018_MMRF/models/spectre/ms018_v1p7_spe.lib')
SPECTRE = '/opt/eda/cadence/SPECTRE181/bin/spectre'
sys.path[:0] = [str(BRIDGE/'src'), str(LUT_ROOT)]
from virtuoso_bridge.spectre.runner import SpectreSimulator
from virtuoso_bridge.spectre.parsers import parse_spectre_psf_ascii
from gmidsmic import GmIdTable

class _PSFMetadataWarning(logging.Filter):
    def filter(self, record):
        # This bridge version treats nested PROP("units" ...) as a signal.
        # Suppress only that known metadata warning; real traces are validated below.
        return not (record.msg == "PSF ASCII: signal '%s' has %d points, expected %d"
                    and record.args and record.args[0] == 'units')

logging.getLogger('virtuoso_bridge.spectre.parsers').addFilter(_PSFMetadataWarning())

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path, obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def model_provenance():
    found={}
    def read(p):
        p=p.resolve()
        if str(p) in found: return
        found[str(p)]=sha(p)
        for name in re.findall(r'^\s*include\s+"([^"]+)"',p.read_text(errors='replace'),re.M|re.I):
            q=p.parent/name
            if q.is_file():read(q)
    read(MODEL)
    return found

def init_project():
    ids=re.findall(r'^id = "([^"]+)"',(SOURCE/'benchmark.toml').read_text(),re.M)
    path=ROOT/'status.json'
    if not path.exists():
        write_json(path,dict(objective='All 50 designs reproduced in SMIC18MMRF nominal with gm/ID and HD digital cells',started=now(),cases=[dict(slot=i+1,source_task_id=t,status='pending',nominal_complete=False) for i,t in enumerate(ids)]))
    write_json(ROOT/'environment.json',dict(captured_at=now(),process='smic18mmrf',corner='tt',temperature_C=27,nominal_vdd_V=1.8,model_library=str(MODEL),model_file_hashes=model_provenance(),spectre_binary=SPECTRE,python_executable=sys.executable,bridge_source=str(BRIDGE/'src'),lut_root=str(LUT_ROOT),lut_index_sha256=sha(LUT_ROOT/'lut/index.json'),external_model_calls=False))

def update_case(slot, **fields):
    # Independent module workers share this index. Lock the read/modify/write
    # and atomically replace it so readers never see a partially written JSON.
    p=ROOT/'status.json'
    with (ROOT/'.status.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        s=json.loads(p.read_text());row=s['cases'][slot-1]
        if fields.get('status')=='running':
            fields.update(review_pdf_ready=False,pdf_render_review_pending=True)
        row.update(fields);row['updated_at']=now();s['updated_at']=now()
        tmp=ROOT/f'.status.{os.getpid()}.tmp'
        write_json(tmp,s);tmp.replace(p)

def lut_size(device,L,gmid,Id,vds=0.45,width_ref_um=10):
    lutroot=LUT_ROOT/'lut'
    try:t=GmIdTable(device,W=width_ref_um,L=L,vds=vds,corner='tt')
    except KeyError:
        lutroot=ROOT/'lut_supplement'
        t=GmIdTable(device,W=width_ref_um,L=L,vds=vds,corner='tt',lut_root=lutroot)
    r=t.size(gmid=gmid,Id=Id)
    r.update(lut_metadata=t.metadata)
    index=json.loads((lutroot/'index.json').read_text())
    matches=[x for x in index['tables'] if x['device']==device and x['corner']=='tt' and x['width_ref_um']==width_ref_um and x['length_um']==L and x['vds_V']==vds]
    assert len(matches)==1
    p=lutroot/matches[0]['json']
    r.update(lut_path=str(p),lut_sha256=sha(p),rounded_W_um=round(r['W_um']/0.02)*0.02)
    return r

def run_spectre(case_slot, label, text, dependencies=(), timeout=600, temperature_C=27):
    trigger=ROOT/'monitor/QUOTA_TRIGGER.json'
    if trigger.exists():
        raise RuntimeError('Quota handoff trigger exists: do not start a new simulation until it is reviewed')
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'runs'/f'{case_slot:02d}'/(stamp+'_'+label)
    inp=out/'inputs';inp.mkdir(parents=True)
    dep_hashes={}
    for src in dependencies:
        src=Path(src).resolve(); dest=inp/src.name
        dest.write_bytes(src.read_bytes());text=text.replace(str(src),str(dest))
        dep_hashes[str(src)]={'snapshot':str(dest.relative_to(ROOT)),'sha256':sha(dest)}
    net=inp/'bench.scs'; net.write_text(text)
    declared_temp=re.search(r'\bsimulatorOptions\s+options[^\n]*\btemp=([-+0-9.eE]+)',text)
    if declared_temp and float(declared_temp[1])!=float(temperature_C):raise ValueError('Run metadata temperature does not match actual bench')
    meta=dict(started_at=now(),case_slot=case_slot,label=label,netlist=str(net.relative_to(ROOT)),netlist_sha256=sha(net),dependencies=dep_hashes,models=model_provenance(),corner='tt',temperature_C=temperature_C,status='running')
    write_json(out/'run.json',meta)
    simulator=SpectreSimulator.local(spectre_cmd=SPECTRE,work_dir=out/'output',output_format='psfascii',timeout=timeout)
    result=simulator.run_simulation(net,{})
    warnings=[]
    for p in (out/'output').glob('*.log'):
        warnings.extend(l.strip() for l in p.read_text(errors='replace').splitlines() if 'WARNING (' in l)
    invalid_model=any('CMI-2441' in w for w in warnings)
    meta.update(completed_at=now(),status='completed' if result.ok and not invalid_model else 'failed',errors=result.errors,warnings=warnings,model_dimensions_valid=not invalid_model,raw_dir=str((out/'output/bench.raw').relative_to(ROOT)))
    write_json(out/'run.json',meta)
    if not result.ok: raise RuntimeError(f'Spectre failed; retained {out}: {result.errors}')
    if invalid_model:raise RuntimeError('PDK model dimension range exceeded: '+str(out))
    return out

def data(run, analysis, required=()):
    p=Path(run)/'output/bench.raw'/analysis
    if not p.exists() and analysis=='tran.tran':
        p=p.with_name('tran.tran.tran')
    parsed=parse_spectre_psf_ascii(p)
    if not parsed.data: raise RuntimeError('Missing parsed data: '+str(p))
    result={k:np.asarray(v) for k,v in parsed.data.items() if k!='units'}
    axis=next((k for k in ['time','freq'] if k in result),next(iter(result),None))
    if axis:
        n=len(result[axis])
        # Noise files also expose hierarchical source records that the bridge
        # parser leaves as NaN placeholders; validate the requested scalar traces.
        for key in (set(required)|{axis}) if required else result:
            values=result[key]
            if len(values)!=n or not np.all(np.isfinite(values)):
                raise RuntimeError(f'Invalid real PSF trace {key} in {p}')
        if np.any(np.diff(result[axis])<=0):
            raise RuntimeError('Non-increasing PSF sweep: '+str(p))
    return result

def dc(run):
    p=Path(run)/'output/bench.raw/dcOp.dc'
    rows={}
    for line in p.read_text().split('VALUE\n',1)[1].splitlines():
        m=re.match(r'^"([^"]+)"\s+"[^"]*"\s+([-+0-9.eE]+)(?:\s|$)',line)
        if m:rows[m[1]]=float(m[2])
    if not rows:raise RuntimeError('DC scalar parse is empty: '+str(p))
    return rows

def at(f,y,target):
    if target<f[0] or target>f[-1]:raise ValueError('frequency outside data')
    return np.interp(np.log10(target),np.log10(f),y)

def loop_metrics(f, loop, gain_freq=1000):
    mag=20*np.log10(np.abs(loop));phase=np.unwrap(np.angle(loop))*180/np.pi
    indices=np.flatnonzero((mag[:-1]>=0)&(mag[1:]<0))
    if not len(indices):raise ValueError('No falling unity crossing')
    i=indices[0];a=mag[i]/(mag[i]-mag[i+1]);logfu=np.log10(f[i])+a*np.log10(f[i+1]/f[i])
    return dict(gain_db=float(at(f,mag,gain_freq)),ugb_hz=float(10**logfu),phase_margin_deg=float(180+phase[i]+a*(phase[i+1]-phase[i])),falling_crossings=int(len(indices)))

def gate(value,limit,sense,unit,kind='linear',relax=True):
    if not np.isfinite(value):raise ValueError('Nonfinite measured metric')
    limits=[]
    for d in [0,0.10,0.15]:
        if not relax: adjusted=limit
        elif kind=='amplitude_db':adjusted=limit+(20*np.log10(1-d) if sense=='min' else 20*np.log10(1+d))
        elif kind=='phase_margin':adjusted=max(45,limit*(1-d))
        else:adjusted=limit*((1-d) if sense=='min' else (1+d))
        limits.append(float(adjusted))
    passes=[bool(value>=v if sense=='min' else value<=v) for v in limits]
    return dict(value=float(value),unit=unit,sense=sense,limits=dict(zip(['original','10pct','15pct'],limits)),passes=dict(zip(['original','10pct','15pct'],passes)))

if __name__=='__main__':init_project()
