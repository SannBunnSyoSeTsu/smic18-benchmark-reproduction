"""Static, netlist-backed schematic drawing shared by the report retrofit.

No simulator or performance extractor is imported.  Symbol placement is
topology-specific; this module provides symbols, routing and coverage checks.
"""
from __future__ import annotations
import collections
import copy
import inspect
import math
import re
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Polygon, Rectangle, PathPatch
from matplotlib.path import Path as MPath
from schematic25 import (Sheet as BaseSheet, sha, now, write, number as base_number,
                         intersections, routed_pin_audit, INK, WIRE, BULK,
                         GREEN, MUTED, ROOT)

def number(s):
    return base_number(re.sub(r'(?i)meg$','M',s))


def case_path(slot):
    matches=list((ROOT/'cases').glob(f'{slot:02d}-*'))
    assert len(matches)==1,(slot,matches)
    return matches[0]


def declarations(path):
    return {m[1]:m[2].split() for m in re.finditer(r'^subckt\s+(\w+)\s+\(([^)]+)\)',path.read_text(),re.M)} if path.exists() else {}


def read_case(slot):
    case=case_path(slot);circuit=case/'circuit.scs';text=circuit.read_text()
    ports=declarations(circuit);hd=declarations(case/'hd_cells.scs')
    blocks={n:dict(ports=p,devices={}) for n,p in ports.items()};active=None
    for raw in text.splitlines():
        line=raw.split('//',1)[0].strip()
        if not line or line.startswith('simulator '):continue
        if line.startswith('subckt '):active=line.split()[1];continue
        if line.startswith('ends '):active=None;continue
        m=re.fullmatch(r'(\w+)\s+\(([^)]+)\)\s+(\w+)(?:\s+(.+))?',line)
        if not m or active is None:raise ValueError('Unparsed electrical line: '+line)
        name,nodes,model,tail=m.groups();nodes=nodes.split()
        params=dict(re.findall(r'(\w+)\s*=\s*([^\s]+)',tail or ''))
        if model in ('n18','p18','n33','p33','nnt33'):kind='MOS';names=['D','G','S','B']
        elif model=='npn18a4':kind='BJT';names=['C','B','E','SUB']
        elif model in ('resistor','rpposab_3t'):kind='R';names=['1','2']+(['B'] if len(nodes)==3 else [])
        elif model in ('capacitor','mim','mim1_rf'):kind='C';names=['1','2']
        elif model in ('ind_rf','inductor'):kind='L';names=['1','2']
        elif model.startswith('pvar'):kind='VAR';names=['1','2']
        elif model in hd:kind='HD';names=hd[model]
        elif model in ports:kind='SUBCKT';names=ports[model]
        else:raise ValueError('Unsupported model: '+line)
        assert len(nodes)==len(names),(name,nodes,names)
        d=dict(name=name,kind=kind,model=model,pins=dict(zip(names,nodes)),parameters=params,source_line=raw)
        if kind=='MOS':
            d.update(W_unit_um=number(params['w'])*1e6,L_um=number(params['l'])*1e6,m=number(params.get('m','1')))
        elif model in ('resistor','capacitor'):d['value_SI']=number(params['r' if kind=='R' else 'c'])
        assert name not in blocks[active]['devices']
        blocks[active]['devices'][name]=d
    referenced={d['model'] for b in blocks.values() for d in b['devices'].values() if d['kind']=='SUBCKT'}
    tops=set(blocks)-referenced;assert len(tops)==1,(slot,tops)
    top=next(iter(tops));flat={}
    def expand(block,prefix,mapping,seen):
        assert block not in seen,'Recursive schematic hierarchy'
        for n,d in blocks[block]['devices'].items():
            q=copy.deepcopy(d);path=prefix+n
            def node(net):return mapping.get(net,prefix+net)
            q['pins']={pin:node(net) for pin,net in d['pins'].items()}
            if d['kind']=='SUBCKT':expand(d['model'],path+'/',q['pins'],seen+[block])
            else:q.update(definition=block+'/'+n,path=path);flat[path]=q
    expand(top,'',{p:p for p in blocks[top]['ports']},[])
    return dict(slot=slot,case=case,subcircuits=blocks,top=top,flat_instances=flat,
                circuit_sha256=sha(circuit),hd_cells_sha256=sha(case/'hd_cells.scs') if hd else None)


def parameter_text(d):
    if d['model']=='inductor':return f"L={number(d['parameters']['l'])*1e12:g} pH"
    out=[]
    for key,value in d['parameters'].items():
        if key in ('w','l','wr','lr','r') and d['model']!='resistor':
            out.append(f'{key}={number(value)*1e6:g}um')
        else:out.append(f'{key}={value}')
    return ' '.join(out)


class Sheet(BaseSheet):
    def tag(self,net,point,body=False,ha='left',dx=.15,dy=.17):
        x,y=point
        self.text(x+dx,y+dy,net,6.35 if body else 7.0,color=BULK if body else GREEN,
                  ha=ha,va='center',weight='normal' if body else 'bold',fontfamily='DejaVu Sans Mono')
        self.labels.append(dict(net=net,point=list(point),text=net,body=body))

    def passive(self,name,x,y,vertical=True,reverse=False):
        d=self.devices[name]
        if d['model'] in ('resistor','capacitor'):return super().passive(name,x,y,vertical,reverse)
        assert d['kind'] in ('R','C','L','VAR') and name not in self.instances
        def tr(u,v):return (x+v,y+u) if vertical else (x+u,y+v)
        ends=[tr(.82,0),tr(-.82,0)]
        if not vertical:ends.reverse()
        if reverse:ends.reverse()
        if d['kind']=='R':
            self.line([tr(-.82,0),tr(-.5,0)]);self.line([tr(.5,0),tr(.82,0)])
            self.line([tr(-.5,-.17),tr(.5,-.17),tr(.5,.17),tr(-.5,.17),tr(-.5,-.17)])
        elif d['kind'] in ('C','VAR'):
            self.line([tr(-.82,0),tr(-.115,0)]);self.line([tr(.115,0),tr(.82,0)])
            for u in [-.115,.115]:self.line([tr(u,-.39),tr(u,.39)],lw=1.0)
            if d['kind']=='VAR':
                self.ax.annotate('',xy=tr(.5,.55),xytext=tr(-.5,-.55),arrowprops=dict(arrowstyle='->',color=INK,lw=.7))
        else:
            self.line([tr(-.82,0),tr(-.6,0)]);self.line([tr(.6,0),tr(.82,0)])
            import numpy as np
            t=np.linspace(0,3*math.pi,120)
            self.line([tr(-.6+1.2*i/119,.32*abs(math.sin(v))) for i,v in enumerate(t)])
        pts=dict(zip(['1','2'],ends))
        label=parameter_text(d)
        if vertical:
            self.text(x+.68,y+.57,name+'  '+d['model'],6.4,weight='bold')
            self.text(x+.68,y-.56,label,5.9)
        else:
            self.text(x,y+.82,name+'  '+d['model'],6.4,ha='center',weight='bold')
            self.text(x,y+.36,label,5.9,ha='center')
        if 'B' in d['pins']:
            bside=1 if vertical else -1
            pts['B']=tr(0,.7*bside)
            self.line([tr(0,.18*bside),pts['B']],color=BULK,lw=.7)
        for pin,pt in pts.items():self.pins[(name,pin)]=dict(point=pt,net=d['pins'][pin],connected=False)
        self.instances[name]=dict(**d,sheet=self.index,origin=[x,y],rendered_pins={k:list(v) for k,v in pts.items()})
        if 'B' in pts:
            end=tr(0,1.15*bside);self.wire(d['pins']['B'],pts['B'],end,body=True)
            self.tag(d['pins']['B'],end,body=True,dy=.01 if vertical else -.2)

    def cell(self,name,x,y):
        d=self.devices[name];assert d['kind'] in ('HD','SUBCKT') and name not in self.instances
        supply={'VDD','AVDD','VPWR','VSS','AVSS','VGND','VNW','VPW'}
        outs=[p for p in d['pins'] if p.upper() in {'ZN','Z','Q','QN','QB','O','Y','VG','VO','OUT','OUTP','OUTN','VOUT','VOUTP','VOUTN'}]
        if d['model']=='cmfb_amp':outs=['vctrl']
        if d['model']=='sar_logic':outs=[p for p in d['pins'] if p=='cmpck' or p.startswith(('dctrl','do'))]
        if d['model']=='sar_cdac':outs=['vtop']
        if d['model']=='sigma_adc':outs=['inp','inn']
        ins=[p for p in d['pins'] if p not in outs and p.upper() not in supply]
        h=max(1.2,.5*(max(len(ins),len(outs))-1)+.65);pts={}
        for names,side in [(ins,-1),(outs,1)]:
            for k,pin in enumerate(names):
                yy=y+(len(names)-1)*.5-k
                pts[pin]=(x+side*2.7,yy)
                self.line([(x+side*1.65,yy),pts[pin]])
                self.text(x+side*1.48,yy+.13,pin,5.8,ha='left' if side<0 else 'right')
        for pin,xx,yy in [('VDD',x-.8,y+h+1),('AVDD',x-.8,y+h+1),('VNW',x+.8,y+h+1),('VSS',x-.8,y-h-1),('AVSS',x-.8,y-h-1),('VPW',x+.8,y-h-1)]:
            actual=next((p for p in d['pins'] if p.upper()==pin),None)
            if actual:
                pts[actual]=(xx,yy);edge=y+(h if yy>y else -h)
                self.line([(xx,edge),(xx,yy)],color=BULK if pin in ('VNW','VPW') else WIRE,lw=.7)
                self.text(xx,edge+(.13 if yy>y else -.3),actual,5.3,ha='center')
        assert set(pts)==set(d['pins']),(name,'unplaced pins',set(d['pins'])-set(pts))
        model=d['model']
        if model.startswith('INHD'):
            self.ax.add_patch(Polygon([(x-1.5,y-1.1),(x-1.5,y+1.1),(x+1.35,y)],closed=True,fill=False,edgecolor=INK,lw=.9))
            self.ax.add_patch(Circle((x+1.5,y),.14,facecolor='white',edgecolor=INK,lw=.8))
        elif model.startswith('NOR'):
            verts=[(x-1.6,y-1.15),(x-.9,y),(x-1.6,y+1.15),(x+.5,y+1.15),(x+1.35,y),(x+.5,y-1.15),(x-1.6,y-1.15)]
            self.ax.add_patch(PathPatch(MPath(verts,[MPath.MOVETO,MPath.CURVE3,MPath.CURVE3,MPath.CURVE3,MPath.CURVE3,MPath.CURVE3,MPath.CURVE3]),fill=False,edgecolor=INK,lw=.9))
            self.ax.add_patch(Circle((x+1.5,y),.14,facecolor='white',edgecolor=INK,lw=.8))
        else:
            self.ax.add_patch(Rectangle((x-1.65,y-h),3.3,2*h,fill=False,edgecolor=INK,lw=.9))
            if d['kind']!='SUBCKT':self.text(x,y,'DFF' if model.startswith('DRN') else model,7,ha='center',va='center')
            if 'CK' in pts:
                yy=pts['CK'][1];self.line([(x-1.65,yy-.15),(x-1.4,yy),(x-1.65,yy+.15)])
        if model.startswith(('INHD','NOR')):
            # A light library-cell boundary carries explicit supply/well pins;
            # the standard logic symbol inside defines the signal function.
            self.ax.add_patch(Rectangle((x-1.65,y-h),3.3,2*h,fill=False,edgecolor='#afbec7',lw=.45,linestyle='--'))
            for pin in ins:
                yy=pts[pin][1]
                if model.startswith('INHD'):edge=x-1.5
                else:
                    t=(yy-y+1.15)/2.3;edge=x-1.6+1.4*t*(1-t)
                self.line([(x-1.65,yy),(edge,yy)])
        self.text(x,y+h+2.5,name+'  '+model,6.5,ha='center',weight='bold')
        for pin,pt in pts.items():self.pins[(name,pin)]=dict(point=pt,net=d['pins'][pin],connected=False)
        self.instances[name]=dict(**d,sheet=self.index,origin=[x,y],rendered_pins={k:list(v) for k,v in pts.items()})

    def finish(self):
        for (name,pin),q in list(self.pins.items()):
            if q['connected'] or self.instances[name]['kind'] not in ('HD','SUBCKT'):continue
            x,y=q['point'];ox,oy=self.instances[name]['origin']
            if abs(x-ox)>2:
                sign=1 if x>ox else -1;end=(x+.6*sign,y)
                self.wire(q['net'],(x,y),end);self.tag(q['net'],end,ha='left' if sign>0 else 'right',dx=.12*sign,dy=0)
            else:
                sign=1 if y>oy else -1;end=(x,y+.5*sign)
                self.wire(q['net'],(x,y),end);self.tag(q['net'],end,dy=.15*sign,dx=.1)
        return super().finish()


def make_case(slot,titles,layout,blocks=None,dpi=125):
    design=read_case(slot);case=design['case'];out=case/'schematic';out.mkdir(exist_ok=True)
    indices=sorted(titles);assert indices==list(range(1,len(indices)+1))
    blocks=blocks or {i:design['top'] for i in indices};assert set(blocks)==set(indices)
    sheets=[]
    def frame(fig,i,box):
        left,bottom,width,height=box;block=blocks[i]
        ax=fig.add_axes([left+width*.015,bottom+height*.115,width*.97,height*.775])
        fig.text(left+width*.035,bottom+height*.96,f'{slot:02d} · {i}/{len(indices)}  {titles[i]}',fontsize=13.5,color=INK,weight='bold',va='top')
        fig.text(left+width*.035,bottom+height*.912,'晶体管／标准单元连接图｜MOS单位 W/L（um），m 为并联倍数｜参数读取最终 circuit.scs',fontsize=7.5,color=MUTED)
        fig.text(left+width*.035,bottom+height*.073,f'子电路：{block}  |  端口：'+', '.join(design['subcircuits'][block]['ports']),fontsize=6.8,color=MUTED)
        fig.text(left+width*.035,bottom+height*.047,'同一子电路内同名网络跨页相连；实心点为连接，交叉无点不连接；紫色为实际体端／井端。',fontsize=7.1,color=MUTED)
        fig.text(left+width*.035,bottom+height*.024,'数字HD保持原厂单元；模拟子电路附展开分图；原厂无源用工艺符号和几何参数。外部测试负载不属于DUT。',fontsize=6.9,color=MUTED)
        z=layout(ax,i,design['subcircuits'][block]['devices']);z.block=block
        return z
    with PdfPages(out/'sheets.pdf',metadata={'Title':f'{slot:02d} 完整晶体管与标准单元图'}) as pdf:
        for i in indices:
            fig=plt.figure(figsize=(11.69,8.27),facecolor='white');sheets.append(frame(fig,i,(0,0,1,1)))
            fig.savefig(out/f'sheet-{i}.svg');fig.savefig(out/f'sheet-{i}.png',dpi=dpi);pdf.savefig(fig);plt.close(fig)
    cols=1 if len(indices)==1 else 2;rows=math.ceil(len(indices)/cols)
    fig=plt.figure(figsize=(11.69*cols,8.27*rows),facecolor='white')
    for k,i in enumerate(indices):frame(fig,i,((k%cols)/cols,1-(k//cols+1)/rows,1/cols,1/rows))
    fig.savefig(out/'full.svg');fig.savefig(out/'full.pdf');fig.savefig(out/'full.png',dpi=90);plt.close(fig)
    rendered={};nets=collections.defaultdict(list);allpaths=[];conflicts=[];crossings=[]
    for block,b in design['subcircuits'].items():
        local=[s for s in sheets if s.block==block]
        names=[n for s in local for n in s.instances]
        assert collections.Counter(names)==collections.Counter(b['devices'].keys()),('Missing/duplicate instances',slot,block,names)
        paths=routed_pin_audit(local);allpaths.extend(dict(q,block=block) for q in paths)
        issue,cross=intersections(local);conflicts+=issue;crossings+=cross
        for s in local:
            for n,d in s.instances.items():
                source=b['devices'][n];assert d['pins']==source['pins'] and d['parameters']==source['parameters']
                qualified=block+'/'+n;rendered[qualified]=dict(d,block=block)
                for pin,net in d['pins'].items():nets[block+'/'+net].append(dict(instance=qualified,pin=pin,sheet=s.index,point=d['rendered_pins'][pin]))
        assert set(nets).issuperset(block+'/'+p for p in b['ports'] if any(p in d['pins'].values() for d in b['devices'].values()))
    assert not conflicts,('Graphical wire conflicts',slot,conflicts)
    expected=sum(len(d['pins']) for b in design['subcircuits'].values() for d in b['devices'].values())
    assert len(allpaths)==expected
    con=dict(generated_at=now(),circuit_sha256=design['circuit_sha256'],top=design['top'],subcircuit_ports={n:b['ports'] for n,b in design['subcircuits'].items()},instances=rendered,expanded_leaf_instances=design['flat_instances'],nets=dict(nets),routed_pin_checks=allpaths,sheets=[dict(index=s.index,block=s.block,title=titles[s.index],wires=s.wires,net_labels=s.labels) for s in sheets],geometric_conflicts=conflicts,unconnected_crossings=crossings,unused_ports={n:[p for p in b['ports'] if not any(p in d['pins'].values() for d in b['devices'].values())] for n,b in design['subcircuits'].items()},convention='Nets are scoped by subcircuit. Identical local labels join across its sheets. Local analog subcircuits have complete definition drawings. HD leaf cells keep all formal supply/well pins. This is static schematic coverage, not layout LVS.')
    write(out/'connectivity.json',con)
    assert sha(case/'circuit.scs')==design['circuit_sha256']
    # Keep the exact drawing sources, including the imported symbol engine,
    # beside the artifacts so later edits cannot orphan a recorded hash.
    for target,source in [('renderer_source.py',Path(__file__)),('symbol_source.py',ROOT/'scripts/schematic25.py'),('layout_source.py',Path(inspect.getfile(layout)))]:
        (out/target).write_bytes(source.read_bytes())
    counts=dict(collections.Counter(d['kind'] for d in rendered.values()));flatcounts=dict(collections.Counter(d['kind'] for d in design['flat_instances'].values()))
    audit=dict(generated_at=now(),status='coverage_passed_visual_pending',circuit_sha256=design['circuit_sha256'],hd_cells_sha256=design['hd_cells_sha256'],renderer_sha256=sha(__file__),layout_file=str(Path(inspect.getfile(layout)).relative_to(ROOT)),layout_sha256=sha(inspect.getfile(layout)),instance_counts=counts,expanded_leaf_instance_counts=flatcounts,total_instances=len(rendered),expanded_leaf_instances=len(design['flat_instances']),total_terminals=expected,all_instances_drawn_exactly_once_per_definition=True,all_terminals_mapped=True,all_body_connections_explicit=True,all_rendered_pins_have_drawn_path_to_correct_net_label=True,all_values_read_from_netlist=True,all_internal_nets_preserved=True,geometric_wire_conflicts=[],sheets=len(sheets),sheet_page_size='A4 landscape',render_review_pending=True,artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(out.iterdir()) if p.is_file()},scope='Documentation-only schematic generation and static connectivity checks. No circuit changes or simulation.')
    write(case/'schematic_audit.json',audit);return audit


def confirm_visual(slot,note='All split sheets and full overview actually viewed; connectivity, symbols, values, body ties and text readability reviewed.'):
    case=case_path(slot);p=case/'schematic_audit.json';a=__import__('json').loads(p.read_text())
    assert sha(case/'circuit.scs')==a['circuit_sha256']
    for path,h in a['artifacts'].items():assert sha(ROOT/path)==h
    a.update(status='passed',render_review_pending=False,all_pages_visually_reviewed=True,visual_reviewed_at=now(),visual_review_note=note)
    write(p,a);return a
