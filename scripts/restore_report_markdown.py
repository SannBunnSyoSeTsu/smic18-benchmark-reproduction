"""Restore editable report text/tables from delivered vector PDFs without rerunning reports.

Poppler preserves Matplotlib table text in cell draw order and exposes its white
header font. Every recovered cell is linked to the PDF XML text indices. Figure-only
assets retain plots/diagrams; exact source netlists remain code, not OCR.
This writes documentation only. Publishing is a separate, audited operation.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, html, json, re, subprocess
import xml.etree.ElementTree as ET
from audit_markdown import inspect

ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def cell(s):return html.escape(s,quote=False).replace('|',r'\|').replace('\n','<br>')
def prose(s):
    # Protect raw comparator signs and identifiers from HTML/emphasis parsing.
    return html.escape(s,quote=False).replace('\\','\\\\').replace('_',r'\_').replace('*',r'\*')
def join_lines(lines):
    result=''
    for s in lines:
        if result and re.search(r'[A-Za-z0-9]$',result) and re.match(r'[A-Za-z0-9]',s):result+=' '
        result+=s
    return result

def pdf_pages(pdf,body_pages):
    raw=subprocess.run(['pdftohtml','-xml','-stdout','-i','-hidden','-f','1','-l',str(body_pages),str(pdf)],capture_output=True,check=True).stdout
    tree=ET.fromstring(raw);fonts={};pages=[]
    for page in tree.findall('page'):
        fonts.update({f.attrib['id']:dict(f.attrib) for f in page.findall('fontspec')})
        texts=[]
        for i,t in enumerate(page.findall('text')):
            q=dict(t.attrib);q.update(fonts[q['font']]);q.update(i=i,text=''.join(t.itertext()))
            for k in ['top','left','width','height','size']:q[k]=float(q[k])
            texts.append(q)
        pages.append(dict(number=int(page.attrib['number']),height=float(page.attrib['height']),width=float(page.attrib['width']),texts=texts))
    return pages

def recover_tables(page):
    ts=page['texts'];used=set();tables=[];i=0
    while i<len(ts):
        if ts[i]['color']!='#ffffff':i+=1;continue
        start=i;heads=[]
        while i<len(ts) and ts[i]['color']=='#ffffff':heads.append(ts[i]);i+=1
        xs=sorted(set(x['left'] for x in heads));assert len(xs)>=2,(page['number'],'ambiguous white heading')
        headers=[join_lines([t['text'] for t in heads if t['left']==x]) for x in xs]
        ids=[t['i'] for t in heads];rows=[];row=['']*len(xs);last=-1;row_ids=[];y=None
        while i<len(ts):
            t=ts[i];col=min(range(len(xs)),key=lambda c:abs(t['left']-xs[c]))
            if t['color']!='#000000' or abs(t['left']-xs[col])>1.5 or t['top']<min(h['top'] for h in heads):break
            if col<last or (col==0 and last==0 and y is not None and t['top']-y>1.8*t['height']):
                assert sum(bool(x) for x in row)>=2,(page['number'],'ambiguous PDF table row',row)
                rows.append(row);ids+=row_ids;row=['']*len(xs);row_ids=[];last=-1
            row[col]+= ('\n' if row[col] else '')+t['text'];row_ids.append(t['i']);last=col;y=t['top'];i+=1
        assert sum(bool(x) for x in row)>=2,(page['number'],'table boundary ambiguous',row)
        rows.append(row);ids+=row_ids;assert not set(ids)&used;used.update(ids)
        tables.append(dict(top=min(t['top'] for t in heads),headers=headers,rows=rows,pdf_text_indices=ids))
    assert all(t['i'] in used for t in ts if t['color']=='#ffffff')
    return tables,used

def recover_page(page):
    ts=page['texts'];tables,used=recover_tables(page);blocks=[];extras=[];groups=[]
    titles=[t for t in ts if t['top']<page['height']*.10 and t['size']>=24]
    title=' '.join(t['text'] for t in sorted(titles,key=lambda t:(t['top'],t['left'])))
    used.update(t['i'] for t in titles)
    for tb in tables:
        lines=['| '+' | '.join(cell(x) for x in tb['headers'])+' |','| '+' | '.join('---' for _ in tb['headers'])+' |']
        lines += ['| '+' | '.join(cell(x) for x in row)+' |' for row in tb['rows']]
        blocks.append((tb['top'],'\n'.join(lines)))
    candidates=[];foot=[]
    for t in ts:
        if t['i'] in used:continue
        if t['top']>page['height']*.94 and (re.search(r'SMIC18.*(?:reproduction|Spectre)',t['text']) or t['text'].strip()==str(page['number'])):foot.append(t['i']);continue
        mono='Mono' in t['family']
        # Figure-level prose uses these text colors; chart annotations remain in
        # the referenced original page and are separately preserved below.
        if mono or t['color'] in ['#172c3d','#506273']:
            candidates.append(dict(t,mono=mono))
        else:extras.append(t)
    for t in sorted(candidates,key=lambda t:(t['top'],t['left'])):
        if groups and groups[-1][-1]['mono']==t['mono'] and abs(groups[-1][-1]['left']-t['left'])<3 and 0<t['top']-groups[-1][-1]['top']<=1.7*t['height']:
            groups[-1].append(t)
        else:groups.append([t])
    for g in groups:
        if g[0]['mono']:text='```text\n'+'\n'.join(x['text'] for x in g)+'\n```'
        else:text=prose(join_lines([x['text'] for x in g]))
        blocks.append((g[0]['top'],text));used.update(t['i'] for t in g)
    used.update(foot);used.update(t['i'] for t in extras)
    assert len(used)==len(ts),(page['number'],'unaccounted PDF text')
    # Axis ticks and legends belong inside the figure, not in report prose.
    return title,'\n\n'.join(x[1] for x in sorted(blocks,key=lambda x:x[0])),dict(page=page['number'],tables=tables,total_pdf_text_fragments=len(ts),accounted_pdf_text_fragments=len(used),plot_text_fragments=len(extras))

def restore(slot,refresh=False):
    """Use the readable report builder instead of embedding complete PDF pages."""
    case=next(p for p in (ROOT/'cases').glob(f'{slot:02d}-*') if p.is_dir())
    md=case/'review_report.md'
    if md.exists() and not refresh:
        return dict(slot=slot,status='existing',path=str(md.relative_to(ROOT)))
    import sys
    sys.path.insert(0,str(ROOT/'tools'))
    from refine_report_markdown import revise
    revise(case)
    return dict(slot=slot,status='refined',path=str(md.relative_to(ROOT)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('slots',nargs='*',type=int);ap.add_argument('--refresh',action='store_true');args=ap.parse_args();rows=[]
    for slot in args.slots or range(1,51):
        row=restore(slot,args.refresh);rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    write(ROOT/'reports/markdown-restoration-progress.json',dict(generated_at=now(),cases=rows))
