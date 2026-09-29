"""Independently compare schematic manifests with frozen Spectre source.

Read-only for all case/PDK/design files.  No drawing or simulator modules are
imported.  Only this review's JSON and Markdown report files are written.
"""
from __future__ import annotations
import collections
import datetime
import hashlib
import json
import math
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SLOTS=(2,3,4,7,8,10,12,13,14,16,20,22,23,24,29,31,35,36,37,41,44,45,47,49,50)
MOS_MODELS={'n18','p18'}
PRIMITIVE_PORTS={
    'n18':('D','G','S','B'),'p18':('D','G','S','B'),
    'resistor':('1','2'),'capacitor':('1','2'),
    'rpposab_3t':('1','2','B'),'mim':('1','2'),
    'mim1_rf':('1','2'),'ind_rf':('1','2'),
    'pvar18w10l1_ckt_rf':('1','2'),
}
PRIMITIVE_KINDS={'n18':'MOS','p18':'MOS','resistor':'R','capacitor':'C',
    'rpposab_3t':'R','mim':'C','mim1_rf':'C','ind_rf':'L','pvar18w10l1_ckt_rf':'VAR'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numeric(value):
    # An independent unit parser; literal parameters are compared separately.
    found=re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([A-Za-z]*)',value)
    if not found:raise ValueError(f'Unrecognized numeric parameter: {value}')
    scale={'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'K':1e3,'Meg':1e6,'meg':1e6,'M':1e6,'G':1e9}
    return float(found[1])*scale[found[2]]


def parse_source(path):
    """Tokenize complete subcircuit bodies without the renderer's parser."""
    blocks={};current=None
    for line_no,original in enumerate(path.read_text().splitlines(),1):
        line=original.partition('//')[0].strip()
        if not line or line.startswith('simulator '):continue
        if line.startswith('ends '):
            assert current is not None and line.split()==['ends',current],(path,line_no,line)
            current=None;continue
        assert '(' in line and ')' in line,(path,line_no,'Unsupported source syntax',line)
        before,sep,tail=line.partition('(');inside,sep,after=tail.partition(')')
        assert sep and '(' not in inside and ')' not in after,(path,line_no,line)
        head=before.split();nodes=inside.split();rest=after.split()
        if head[0]=='subckt':
            assert len(head)==2 and not rest and current is None,(path,line_no,line)
            current=head[1];assert current not in blocks,(path,'Duplicate subckt',current)
            assert len(nodes)==len(set(nodes)),(path,current,'Duplicate formal ports')
            blocks[current]={'ports':nodes,'instances':{}};continue
        assert current is not None and len(head)==1 and rest,(path,line_no,line)
        name=head[0];model=rest[0];params={}
        for token in rest[1:]:
            key,eq,value=token.partition('=')
            assert eq and key and value and key not in params,(path,line_no,token)
            params[key]=value
        assert name not in blocks[current]['instances'],(path,current,'Duplicate instance',name)
        blocks[current]['instances'][name]={'name':name,'model':model,'node_order':nodes,
            'parameters':params,'line_number':line_no}
    assert current is None and blocks,(path,'Unclosed or missing subckt')
    return blocks


def decorate(blocks,hd):
    for block in blocks.values():
        for device in block['instances'].values():
            model=device['model']
            if model in PRIMITIVE_PORTS:ports=PRIMITIVE_PORTS[model];kind=PRIMITIVE_KINDS[model]
            elif model in blocks:ports=blocks[model]['ports'];kind='SUBCKT'
            elif model in hd:ports=hd[model]['ports'];kind='HD'
            else:raise ValueError('Unknown model: '+model)
            assert len(ports)==len(device['node_order']),(device['name'],model,'Terminal count')
            device['pins']={ports[k]:node for k,node in enumerate(device['node_order'])}
            device['kind']=kind


def equivalent(source,record,where,errors):
    for field in ('name','kind','model','parameters','pins'):
        if record.get(field)!=source[field]:errors.append({'where':where,'field':field,'source':source[field],'schematic':record.get(field)})


def expand_design(blocks,top):
    leaves={};boundaries=[]
    def enter(block,scope,bindings,ancestors):
        assert block not in ancestors,('Recursive hierarchy',block)
        def node(net):return bindings[net] if net in bindings else net if not scope or net=='0' else scope+'/'+net
        for name,d in blocks[block]['instances'].items():
            path=scope+'/'+name if scope else name
            pins={pin:node(net) for pin,net in d['pins'].items()}
            if d['kind']=='SUBCKT':
                boundaries.append({'path':path,'definition':d['model'],'port_bindings':pins})
                enter(d['model'],path,pins,ancestors+(block,))
            else:leaves[path]={k:d[k] for k in ('name','kind','model','parameters')}|{'pins':pins,'definition':block+'/'+name,'path':path}
    enter(top,'',{p:p for p in blocks[top]['ports']},())
    return leaves,boundaries


def close(a,b):return abs(a-b)<1e-8


def on_segment(point,a,b):
    x,y=point
    return ((close(a[0],b[0]) and close(x,a[0]) and min(a[1],b[1])-1e-8<=y<=max(a[1],b[1])+1e-8)
        or (close(a[1],b[1]) and close(y,a[1]) and min(a[0],b[0])-1e-8<=x<=max(a[0],b[0])+1e-8))


def segment_contact(a,b,c,d):
    if any(on_segment(p,c,d) for p in (a,b)) or any(on_segment(p,a,b) for p in (c,d)):return True
    a_vertical=close(a[0],b[0]);c_vertical=close(c[0],d[0])
    if a_vertical==c_vertical:return False
    point=(a[0],c[1]) if a_vertical else (c[0],a[1])
    return on_segment(point,a,b) and on_segment(point,c,d)


def independently_trace(manifest,errors):
    """Build our own per-net conductor graph, ignoring stored audit booleans."""
    checked=0;by_sheet={s['index']:s for s in manifest['sheets']}
    for index,sheet in by_sheet.items():
        segments=[]
        for wire in sheet['wires']:
            for a,b in zip(wire['points'],wire['points'][1:]):
                if a==b:continue
                if not (close(a[0],b[0]) or close(a[1],b[1])):
                    errors.append({'sheet':index,'reason':'Non-orthogonal wire','net':wire['net']})
                segments.append((wire['net'],a,b))
        parent=list(range(len(segments)))
        def find(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for i,(net,a,b) in enumerate(segments):
            for j,(other,c,d) in enumerate(segments[:i]):
                if net==other and segment_contact(a,b,c,d):parent[find(i)]=find(j)
        named={}
        for label in sheet['net_labels']:
            for i,(net,a,b) in enumerate(segments):
                if net==label['net'] and on_segment(label['point'],a,b):named.setdefault(net,set()).add(find(i))
        for qualified,instance in manifest['instances'].items():
            if instance['sheet']!=index:continue
            for pin,point in instance['rendered_pins'].items():
                expected=instance['pins'][pin];valid=[];wrong=[]
                for i,(net,a,b) in enumerate(segments):
                    if on_segment(point,a,b):
                        if net==expected:valid.append(i)
                        else:wrong.append(net)
                if wrong:errors.append({'where':qualified+'.'+pin,'reason':'Rendered pin touches another net','source':expected,'other':sorted(set(wrong))})
                if not any(find(i) in named.get(expected,set()) for i in valid):
                    errors.append({'where':qualified+'.'+pin,'reason':'No drawn conductor path to matching label','net':expected})
                checked+=1
    return checked


def audit_slot(slot):
    paths=list((ROOT/'cases').glob(f'{slot:02d}-*'));assert len(paths)==1,(slot,paths)
    case=paths[0];netlist=case/'circuit.scs';hdfile=case/'hd_cells.scs';conn=case/'schematic/connectivity.json'
    out={'slot':slot,'case':str(case.relative_to(ROOT)),'circuit_sha256':sha(netlist),'hd_cells_sha256':sha(hdfile) if hdfile.exists() else None}
    blocks=parse_source(netlist);hd=parse_source(hdfile) if hdfile.exists() else {};decorate(blocks,hd)
    if hd:decorate(hd,{})
    referenced={d['model'] for b in blocks.values() for d in b['instances'].values() if d['kind']=='SUBCKT'}
    tops=set(blocks)-referenced;assert len(tops)==1,(slot,tops)
    top=tops.pop();leaves,boundaries=expand_design(blocks,top)
    out.update(top=top,source_definition_count=sum(len(b['instances']) for b in blocks.values()),
               source_terminal_count=sum(len(d['pins']) for b in blocks.values() for d in b['instances'].values()),
               source_expanded_leaf_count=len(leaves),hierarchy_boundaries=boundaries)
    if not conn.exists():return out|{'status':'pending','reason':'connectivity.json not yet generated'}
    errors=[];manifest=json.loads(conn.read_text());out['connectivity_sha256']=sha(conn)
    if manifest.get('circuit_sha256')!=out['circuit_sha256']:errors.append({'reason':'Manifest source SHA does not match current circuit'})
    if manifest.get('top')!=top:errors.append({'reason':'Top subckt mismatch','source':top,'schematic':manifest.get('top')})
    source_ports={name:block['ports'] for name,block in blocks.items()}
    if manifest.get('subcircuit_ports')!=source_ports:errors.append({'reason':'Subcircuit formal-port order mismatch','source':source_ports,'schematic':manifest.get('subcircuit_ports')})
    expected={block+'/'+name:d for block,b in blocks.items() for name,d in b['instances'].items()}
    drawn=manifest['instances']
    if set(expected)!=set(drawn):errors.append({'reason':'Definition coverage mismatch','missing':sorted(set(expected)-set(drawn)),'extra':sorted(set(drawn)-set(expected))})
    expected_nets=collections.defaultdict(list);mos=[];res3=[];hdpins=[]
    for qualified,d in expected.items():
        block,name=qualified.split('/',1)
        if qualified not in drawn:continue
        r=drawn[qualified];equivalent(d,r,qualified,errors)
        if r.get('block')!=block:errors.append({'where':qualified,'reason':'Incorrect local scope'})
        if set(r.get('rendered_pins',{}))!=set(d['pins']):errors.append({'where':qualified,'reason':'Missing/extra rendered terminal'})
        for pin,net in d['pins'].items():expected_nets[block+'/'+net].append((qualified,pin))
        if d['kind']=='MOS':
            # D/G/S/B come from fixed simulator terminal order, not names/prefixes.
            mos.append({'instance':qualified,'D_G_S_B':d['node_order']})
            for key,value in {'W_unit_um':numeric(d['parameters']['w'])*1e6,'L_um':numeric(d['parameters']['l'])*1e6,'m':numeric(d['parameters'].get('m','1'))}.items():
                if not isinstance(r.get(key),(int,float)) or not math.isclose(r[key],value,rel_tol=1e-10,abs_tol=1e-10):errors.append({'where':qualified,'field':key,'source':value,'schematic':r.get(key)})
        elif d['model']=='rpposab_3t':res3.append({'instance':qualified,'terminal_1_2_B':d['node_order']})
        elif d['kind']=='HD':
            hdpins.append({'instance':qualified,'model':d['model'],'formal_order':hd[d['model']]['ports'],'all_connections':d['pins'],
                'supply_and_well_connections':{p:n for p,n in d['pins'].items() if p in ('VDD','VSS','VNW','VPW','AVDD','AVSS')}})
            for pin in ('VDD','VSS','VNW','VPW'):
                if pin not in d['pins'] or pin not in r['rendered_pins']:errors.append({'where':qualified,'reason':'HD supply/well terminal omitted','pin':pin})
    actual_nets={net:[(d['instance'],d['pin']) for d in members] for net,members in manifest['nets'].items()}
    if set(actual_nets)!=set(expected_nets):errors.append({'reason':'Net-index keys mismatch'})
    for net,members in expected_nets.items():
        if collections.Counter(actual_nets.get(net,[]))!=collections.Counter(members):errors.append({'reason':'Net-index terminal membership mismatch','net':net,'source':members,'schematic':actual_nets.get(net)})
    flat=manifest.get('expanded_leaf_instances',{})
    if set(flat)!=set(leaves):errors.append({'reason':'Expanded leaf paths mismatch','missing':sorted(set(leaves)-set(flat)),'extra':sorted(set(flat)-set(leaves))})
    for path,d in leaves.items():
        if path not in flat:continue
        equivalent(d,flat[path],'expanded:'+path,errors)
        for field in ('path','definition'):
            if flat[path].get(field)!=d[field]:errors.append({'where':'expanded:'+path,'field':field,'source':d[field],'schematic':flat[path].get(field)})
    trace_count=independently_trace(manifest,errors)
    if trace_count!=out['source_terminal_count']:errors.append({'reason':'Drawn terminal total mismatch','drawn':trace_count,'source':out['source_terminal_count']})
    for file,initial in [(netlist,out['circuit_sha256']),(conn,out['connectivity_sha256'])]+([(hdfile,out['hd_cells_sha256'])] if hdfile.exists() else []):
        if sha(file)!=initial:errors.append({'reason':'Input changed during review','file':str(file.relative_to(ROOT))})
    out.update(status='failed' if errors else 'passed',errors=errors,
        schematic_definition_count=len(drawn),schematic_expanded_leaf_count=len(flat),independently_traced_terminals=trace_count,
        expanded_leaf_counts_by_kind=dict(collections.Counter(d['kind'] for d in leaves.values())),
        MOS_terminal_order_checks=mos,PDK_three_terminal_resistor_checks=res3,HD_port_checks=hdpins,
        parameters_compared='Exact parameter-key/value dictionaries, plus independently converted MOS W/L/m labels',
        scoped_net_count=len(expected_nets),hd_models_declared={n:b['ports'] for n,b in hd.items()},
        HD_internal_MOS_counts={n:sum(d['kind']=='MOS' for d in b['instances'].values()) for n,b in hd.items()},
        checks={'definitions_and_model_names':not errors,'all_parameter_dicts':not errors,'all_terminal_networks_and_order':not errors,
            'MOS_D_G_S_B_order':not errors,'resistor_third_terminal':not errors,'HD_formal_supply_and_well_pins':not errors,
            'hierarchy_expansion':not errors,'net_index_membership':not errors,'drawn_path_to_matching_net_label':not errors})
    return out


def main():
    cases=[]
    for slot in SLOTS:
        try:result=audit_slot(slot)
        except Exception as exc:result={'slot':slot,'status':'failed','errors':[{'reason':type(exc).__name__+': '+str(exc)}]}
        cases.append(result);print(f'{slot:02d}: {result["status"]}',flush=True)
    failures=[c['slot'] for c in cases if c['status']=='failed'];pending=[c['slot'] for c in cases if c['status']=='pending']
    report={'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'failed' if failures else 'pending' if pending else 'passed',
        'scope':'25 retrospective schematic additions; original case 25 reference drawing is outside this retrofit review.',
        'review_script':'scripts/audit_schematic_independent.py','review_script_sha256':sha(__file__),
        'independence':'Only Python standard library. The drawing parser, renderer, existing audit flags and routed-pin pass booleans are not imported or used as evidence.',
        'method':['Independently tokenize every circuit.scs and hd_cells.scs subcircuit/instance statement.',
                  'Fix analog primitive port order from Spectre model conventions; derive local and HD formal order from source declarations.',
                  'Compare every model, literal parameter dictionary, pin network, rendered terminal key, MOS size label and scoped net-index membership.',
                  'Independently recurse local analog hierarchy and compare every expanded leaf path and mapped network.',
                  'Independently traverse recorded orthogonal wire segments to a matching local net label for every rendered terminal.'],
        'limitations':'Static source-to-manifest correspondence only. HD cells remain allowed vendor leaf symbols. Multiplicity m remains a labeled parameter, not repeated symbols. Does not replace visual review, physical LVS or electrical performance verification.',
        'expected_case_count':len(SLOTS),'passed_case_count':sum(c['status']=='passed' for c in cases),'failed_slots':failures,'pending_slots':pending,
        'totals':{'definitions':sum(c.get('source_definition_count',0) for c in cases),'terminals':sum(c.get('source_terminal_count',0) for c in cases),
                  'expanded_leaf_instances':sum(c.get('source_expanded_leaf_count',0) for c in cases),
                  'independently_traced_terminals':sum(c.get('independently_traced_terminals',0) for c in cases)},'cases':cases}
    dest=ROOT/'reports/schematic-independent-review.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    rows=['# 图纸独立静态复核','',f'结论：**{report["status"]}**；{report["passed_case_count"]}/{len(SLOTS)} 项通过。',
        '', '本次覆盖既有 25 项报告补图，不含作为范例的第 25 项原图。自行读取并解析每份 `circuit.scs` 和 `hd_cells.scs`，未调用绘图解析器或采用已有审计的通过标志。',
        '', '逐实例核对型号、全部原始参数、MOS 的 D/G/S/B、三端电阻的 B 端、HD 声明端序及全部供电/井端，并独立展开模拟子电路。另根据记录的实际导线重建连通分量，逐端追踪至对应网络标签。',
        '', '| 案例 | 结果 | 器件定义 | 端子 | 展开叶实例 |','|---|---|---:|---:|---:|']
    for c in cases:rows.append(f'| {c["slot"]:02d} | {c["status"]} | {c.get("source_definition_count","—")} | {c.get("source_terminal_count","—")} | {c.get("source_expanded_leaf_count","—")} |')
    rows+=['', '20、22、31 的每个层次实例均按各自形式端口重新绑定；内部节点分别置于实例路径作用域，未将不同子电路的同名内部网络合并。完整绑定表、逐 MOS/三端电阻/HD 端口清单及文件 SHA-256 见同名 JSON。']
    if pending:rows+=['', '待补齐图纸：'+', '.join(f'{s:02d}' for s in pending)+'。']
    if failures:rows+=['', '发现缺陷：'+', '.join(f'{s:02d}' for s in failures)+'；具体差异见 JSON errors。']
    rows+=['','此审查仅确认图纸清单与既有网表对应；HD 按允许的原厂叶单元核对，m 作为尺寸标注保留。没有运行仿真、修改电路或重做性能判定。','']
    (ROOT/'reports/schematic-independent-review.md').write_text('\n'.join(rows))
    print(json.dumps({k:report[k] for k in ('status','passed_case_count','failed_slots','pending_slots','totals')},ensure_ascii=False))


if __name__=='__main__':main()
