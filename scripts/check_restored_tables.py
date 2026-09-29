"""Compare rendered Markdown cell strings to every recovered PDF table cell."""
from restore_report_markdown import *
from html.parser import HTMLParser
import markdown

class Content(HTMLParser):
    def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.table=[];self.tables.append(self.table)
        elif tag=='tr' and self.table is not None:self.row=[];self.table.append(self.row)
        elif tag in ['th','td'] and self.row is not None:self.cell=''
        elif tag=='br' and self.cell is not None:self.cell+='\n'
    def handle_data(self,s):
        if self.cell is not None:self.cell+=s
    def handle_endtag(self,tag):
        if tag in ['th','td'] and self.cell is not None:self.row.append(self.cell);self.cell=None
        elif tag=='tr':self.row=None
        elif tag=='table':self.table=None

def audit():
    rows=[]
    for case in sorted((ROOT/'cases').iterdir()):
        p=case/'markdown_provenance.json'
        if not p.exists():continue
        r=json.loads(p.read_text());m=case/'review_report.md';assert sha(m)==r['markdown_sha256']
        parser=Content();parser.feed(markdown.markdown(m.read_text(),extensions=['tables','fenced_code']))
        expected=[[t['headers']]+t['rows'] for page in r['pages'] for t in page['tables']]
        issues=[]
        if len(expected)!=len(parser.tables):issues.append('table count')
        for i,(want,got) in enumerate(zip(expected,parser.tables)):
            if want!=got:issues.append(dict(table=i,expected=want,actual=got))
        rows.append(dict(case=case.name,tables=len(expected),cells=sum(len(z) for table in expected for z in table),status='failed' if issues else 'passed',issues=issues))
    result=dict(generated_at=now(),status='passed' if all(x['status']=='passed' for x in rows) else 'failed',reports=len(rows),tables=sum(x['tables'] for x in rows),cells=sum(x['cells'] for x in rows),cases=rows)
    write(ROOT/'reports/markdown-content-audit.json',result);print(json.dumps({k:v for k,v in result.items() if k!='cases'},ensure_ascii=False));print(json.dumps([r for r in rows if r['issues']],ensure_ascii=False));return result
if __name__=='__main__':audit()
