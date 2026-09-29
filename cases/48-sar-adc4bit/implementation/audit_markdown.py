"""Audit generated Markdown tables as syntax and rendered HTML, excluding source copies."""
from pathlib import Path
import json,re,hashlib,datetime
from html.parser import HTMLParser
import markdown
ROOT=Path(__file__).resolve().parents[1]
KB=ROOT.parent/'Analog-Circuit-Knowledge-Base/SMIC18-Benchmark-Reproduction'
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables=[];self.current=None;self.row=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.current=[];self.tables.append(self.current)
        elif tag=='tr' and self.current is not None:self.row=0
        elif tag in ('th','td') and self.row is not None:self.row+=1
    def handle_endtag(self,tag):
        if tag=='tr' and self.current is not None:self.current.append(self.row);self.row=None
        elif tag=='table':self.current=None

def inspect(path):
    text=path.read_text();lines=text.splitlines();i=0;fence=False;blocks=[];issues=[]
    cells=lambda s:re.split(r'(?<!\\)\|',s.strip()[1:-1])
    while i<len(lines):
        s=lines[i].strip()
        if s.startswith(('```','~~~')):fence=not fence;i+=1;continue
        if fence or not s.startswith('|'):i+=1;continue
        start=i;rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i]);i+=1
        n=len(cells(rows[0]));separator=len(rows)>1 and all(re.fullmatch(r'\s*:?-{3,}:?\s*',c) for c in cells(rows[1]))
        if not separator:issues.append(dict(line=start+1,error='Pipe rows do not form a contiguous header/separator/body table'));continue
        if start and lines[start-1].strip():issues.append(dict(line=start+1,error='Missing blank line before table'))
        if i<len(lines) and lines[i].strip():issues.append(dict(line=i,error='Missing blank line after table'))
        for offset,row in enumerate(rows):
            if not row.rstrip().endswith('|') or len(cells(row))!=n:issues.append(dict(line=start+offset+1,error='Inconsistent column count or unescaped pipe'))
        blocks.append(dict(line=start+1,columns=n,body_rows=len(rows)-2))
    parser=Tables();parser.feed(markdown.markdown(text,extensions=['tables','fenced_code']))
    if len(parser.tables)!=len(blocks):issues.append(dict(error='Rendered table count differs',expected=len(blocks),actual=len(parser.tables)))
    for k,(rendered,block) in enumerate(zip(parser.tables,blocks)):
        if len(rendered)!=block['body_rows']+1 or any(n!=block['columns'] for n in rendered):issues.append(dict(error='Rendered table shape differs',table=k,actual=rendered,expected=block))
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),tables=blocks,issues=issues)

def main():
    paths=set(ROOT.glob('*.md'))|set((ROOT/'reports').glob('*.md'))|set((ROOT/'cases').rglob('*.md'))|set(KB.rglob('*.md'))
    paths=sorted(p for p in paths if not any(x in p.relative_to(ROOT if p.is_relative_to(ROOT) else KB).parts for x in ['source','implementation']))
    rows=[inspect(p) for p in paths];out=dict(generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Generated project and published knowledge Markdown; original source and implementation snapshots excluded.',files=len(rows),table_count=sum(len(q['tables']) for q in rows),status='passed' if not any(q['issues'] for q in rows) else 'failed',documents=rows)
    (ROOT/'reports/markdown-table-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='documents'},ensure_ascii=False));print(json.dumps([q for q in rows if q['issues']],ensure_ascii=False,indent=2));return out
if __name__=='__main__':main()
