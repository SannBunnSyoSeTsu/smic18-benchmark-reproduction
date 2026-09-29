"""Extract requested unmodified HD cells from installed vendor CDL."""
from common import *
CDL=Path('/home/IC/Tech/S180MS/SCC018UG_HD_RVT_V0.3a/SCC018UG_HD_RVT_V0p3a/cdl/scc018ug_hd_rvt.cdl')

def extract_hd(names,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    text=CDL.read_text(errors='strict')
    blocks={m[1]:m[0] for m in re.finditer(r'^\.SUBCKT\s+(\S+)[^\n]*\n.*?^\.ENDS[^\n]*',text,re.M|re.S|re.I)}
    result=['// Exact vendor MOS sizes, mechanical syntax conversion only.','simulator lang=spectre'];manifest=[]
    for name in sorted(set(names)):
        block=blocks[name];lines=block.splitlines();pins=lines[0].split()[2:]
        converted=[];mos=0
        for line in lines:
            t=line.split()
            if not t or t[0].startswith('*'):continue
            if t[0].upper()=='.SUBCKT':converted.append('subckt '+name+' ('+' '.join(pins)+')')
            elif t[0].upper()=='.ENDS':converted.append('ends '+name)
            elif t[0].upper().startswith('M'):
                params=[]
                for item in t[6:]:
                    key,value=item.split('=',1)
                    if key.lower() not in {'w','l','m','ad','as','pd','ps','nrd','nrs','nf','multi','sa','sb','sd'}:raise ValueError(item)
                    params.append(key.lower()+'='+value)
                converted.append(t[0]+' ('+' '.join(t[1:5])+') '+t[5]+' '+' '.join(params));mos+=1
            else:raise ValueError('Unsupported vendor statement: '+line)
        result+=converted+['']
        manifest.append(dict(name=name,pins=pins,mos_count=mos,original_block_sha256=hashlib.sha256(block.encode()).hexdigest(),source_line=text[:text.index(block)].count('\n')+1))
    path=directory/'hd_cells.scs';path.write_text('\n'.join(result)+'\n')
    write_json(directory/'hd_cells_manifest.json',dict(source=str(CDL),source_sha256=sha(CDL),cells=manifest,output_sha256=sha(path),sizes_modified=False,model_names_modified=False))
    return path
