"""Publish complete editable reports and architecture diagrams; retain all electrical evidence."""
from common import *
from publish_knowledge import KB,NAMES,index
from system_diagrams import DIAGRAMS
from audit_markdown import inspect
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import markdown,shutil

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if (tag,key) in [('a','href'),('img','src')]:self.links.append(value)

def check_links(path):
    parser=Links();parser.feed(markdown.markdown(path.read_text(),extensions=['tables','fenced_code']));count=0
    for target in parser.links:
        u=urlsplit(target)
        if u.scheme or not u.path:continue
        q=Path(unquote(u.path));q=q if q.is_absolute() else path.parent/q
        assert q.exists(),(str(path),target);count+=1
    return count

def main():
    state=json.loads((ROOT/'status.json').read_text());rows=state['cases'];assert len(rows)==50 and all(x['nominal_complete'] and x['review_pdf_ready'] for x in rows)
    content=json.loads((ROOT/'reports/markdown-content-audit.json').read_text());assert content['status']=='passed' and content['reports']==43
    mm=json.loads((ROOT/'reports/mermaid-syntax-audit.json').read_text());assert mm['status']=='passed' and mm['diagrams']==len(DIAGRAMS)
    render=json.loads((ROOT/'reports/mermaid-render-audit.json').read_text())
    visual=json.loads((ROOT/'reports/mermaid-visual-review.json').read_text());assert visual['status']=='passed' and visual['all_diagrams_actually_viewed']
    assert len(render['cases'])==len(visual['cases'])==len(DIAGRAMS)
    parsed={r['case']:r for r in mm['cases']};viewed={r['case']:r for r in visual['cases']}
    for r in render['cases']:
        c=ROOT/'cases'/r['case'];assert parsed[c.name]['mermaid_sha256']==r['mermaid_sha256']==viewed[c.name]['mermaid_sha256']
        for name,key in [('system_block_diagram.mmd','mermaid_sha256'),('markdown_assets/system-block.svg','svg_sha256'),('markdown_assets/system-block.png','png_sha256')]:
            assert sha(c/name)==r[key]==viewed[c.name][key],(c.name,name)
    backup=ROOT/'reports/markdown-completion-before-publication';backup.mkdir(exist_ok=True);receipts=[]
    for row in rows:
        slot=row['slot'];slug=NAMES[slot][0];case=ROOT/'cases'/slug;ev=KB/'evidence'/slug;note=KB/'cases'/f'{slug}.md';md=case/'review_report.md';assert md.is_file() and not inspect(md)['issues']
        pp=json.loads((case/'pdf_provenance.json').read_text());assert not pp['render_review_pending']
        protected={name:sha(ev/name) for name in ['circuit.scs','contract.json','latest_results.json','pdf_provenance.json','review.pdf']}
        assert protected['review.pdf']==sha(ROOT/pp['pdf'])==pp['sha256']
        assert protected['circuit.scs']==sha(case/'circuit.scs') and protected['latest_results.json']==sha(case/'latest_results.json')
        b=backup/slug;b.mkdir(exist_ok=True)
        for src,destname in [(note,'knowledge-note.md'),(ev/'review_report.md','review_report.md'),(ev/'delivery_audit.json','delivery_audit.json')]:
            if src.exists() and not (b/destname).exists():shutil.copy2(src,b/destname)
        assets=['review_report.md']+[name for name in ['markdown_provenance.json','system_block_diagram.mmd'] if (case/name).exists()]
        if (case/'markdown_assets').exists():assets += [str(p.relative_to(case)) for p in (case/'markdown_assets').rglob('*') if p.is_file()]
        for name in assets:
            target=ev/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(case/name,target)
        text=re.sub(r'<!-- REPORT-MARKDOWN -->.*?<!-- END-REPORT-MARKDOWN -->\n*','',note.read_text(),flags=re.S)
        e=f'../evidence/{slug}/';block='<!-- REPORT-MARKDOWN -->\n## 可编辑报告与系统结构\n\n'+f'[完整报告MD]({e}review_report.md) · [对应PDF]({e}review.pdf)'
        if slot in DIAGRAMS:
            q=DIAGRAMS[slot];assert q['mermaid']==(case/'system_block_diagram.mmd').read_text()
            assert ('```mermaid\n'+q['mermaid']+'```') in md.read_text()
            block+=f' · [Mermaid源文件]({e}system_block_diagram.mmd) · [框图SVG]({e}markdown_assets/system-block.svg)\n\n'+q['note']+'\n\n实线为信号或能量通路，虚线为时钟、控制或偏置。\n\n```mermaid\n'+q['mermaid']+'```'
        block+='\n<!-- END-REPORT-MARKDOWN -->\n\n';pos=text.find('\n## ')
        if pos<0:text+='\n\n'+block
        else:text=text[:pos+1]+block+text[pos+1:]
        note.write_text(text)
        count=check_links(md)+check_links(ev/'review_report.md')+check_links(note)
        assert not inspect(note)['issues']
        assert {n:sha(ev/n) for n in protected}==protected
        hashes={name:sha(ev/name) for name in assets};assert all(sha(case/name)==h for name,h in hashes.items())
        record=dict(published_at=now(),slot=slot,status='passed',report_markdown_sha256=sha(md),restored_from_pdf=(case/'markdown_provenance.json').exists(),system_mermaid=slot in DIAGRAMS,artifacts=hashes,protected_evidence_unchanged=protected,knowledge_note_sha256=sha(note),links_verified=count)
        write_json(case/'markdown_delivery.json',record);shutil.copy2(case/'markdown_delivery.json',ev/'markdown_delivery.json')
        receipt=ROOT/'reports'/f'{slug}-delivery-audit.json'
        if receipt.exists():
            r=json.loads(receipt.read_text());r['published_artifacts_sha256'].update(hashes);r['published_artifacts_sha256']['markdown_delivery.json']=sha(case/'markdown_delivery.json');r.update(knowledge_note_sha256=sha(note),documentation_updated_at=now(),markdown_sha256=sha(md),system_mermaid=slot in DIAGRAMS);write_json(receipt,r);shutil.copy2(receipt,ev/'delivery_audit.json')
        receipts.append(record)
    index()
    intro='# 全部50项可编辑复现报告\n\n50份完整报告MD均已保留并入库：7份由报告生成器同步保存，43份从已交付矢量PDF补建可编辑正文与表格，来源在文件开头明示。原PDF、电路和测量数据未因MD补建改变。\n\n28项具有多模块信号、时钟、功率或反馈关系的案例附Mermaid系统框图，基本晶体管图继续保留。框图只覆盖实际实现及测试夹具，未扩展成未实现的整芯片系统。\n\n'
    project=intro+'|编号|模块|报告MD|PDF|系统框图|\n|---|---|---|---|---|\n';knowledge=intro+'|编号|模块|报告MD|PDF|系统框图|\n|---|---|---|---|---|\n'
    for row in rows:
        slot=row['slot'];slug=NAMES[slot][0];diagram='[Mermaid](../cases/'+slug+'/system_block_diagram.mmd)' if slot in DIAGRAMS else '基本电路图'
        project+=f'|{slot:02d}|{slug}|[MD](../cases/{slug}/review_report.md)|[PDF]({slug}-review.pdf)|{diagram}|\n'
        diagram=f'[Mermaid](evidence/{slug}/system_block_diagram.mmd)' if slot in DIAGRAMS else '基本电路图'
        knowledge+=f'|{slot:02d}|{slug}|[MD](evidence/{slug}/review_report.md)|[PDF](evidence/{slug}/review.pdf)|{diagram}|\n'
    (ROOT/'reports/all-reproduction-markdown.md').write_text(project);(KB/'MARKDOWN-REPORTS.md').write_text(knowledge)
    kp=KB/'README.md';s=kp.read_text();at=s.index('\n\n');s=s[:at]+'\n\n[全部50项Markdown与系统框图](MARKDOWN-REPORTS.md)'+s[at:];kp.write_text(s)
    docs=KB/'documentation';docs.mkdir(exist_ok=True)
    for name in ['restore_report_markdown.py','check_restored_tables.py','system_diagrams.py','check_mermaid.mjs','render_system_diagrams.py','publish_markdown_reports.py','audit_markdown.py']:
        shutil.copy2(ROOT/'scripts'/name,docs/name)
    for name in ['markdown-content-audit.json','mermaid-syntax-audit.json','mermaid-render-audit.json','mermaid-visual-review.json']:
        shutil.copy2(ROOT/'reports'/name,docs/name)
    (docs/'README.md').write_text('# 报告MD与系统图补全记录\n\n工具快照供追溯。43份旧MD从已交付PDF恢复，201张表8098个单元格与实际Markdown渲染文本逐格比较通过。28份Mermaid使用11.12.0解析器检查，在本地无头浏览器生成SVG/PNG，并逐图实际查看了文字、连线和DUT边界；实看记录含最终文件哈希。所有处理在本机进行；未向外部服务发送电路内容。新7项MD由原报告生成器同步保存。具体发布哈希见各evidence目录的markdown_delivery.json。\n')
    result=dict(published_at=now(),status='passed',reports=len(receipts),restored_reports=sum(r['restored_from_pdf'] for r in receipts),system_diagrams=sum(r['system_mermaid'] for r in receipts),links_verified=sum(r['links_verified'] for r in receipts),cases=receipts)
    write_json(ROOT/'reports/markdown-delivery-audit.json',result);shutil.copy2(ROOT/'reports/markdown-delivery-audit.json',docs/'markdown-delivery-audit.json')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},ensure_ascii=False))

if __name__=='__main__':main()
