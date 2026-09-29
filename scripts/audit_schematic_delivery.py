"""Audit the completed documentation retrofit against its electrical baseline."""
import json
from pathlib import Path
from schematic_common import ROOT,case_path,sha,now,write


def audit():
    base=json.loads((ROOT/'reports/schematic-retrofit-baseline.json').read_text())
    independent_path=ROOT/'reports/schematic-independent-review.json'
    independent=json.loads(independent_path.read_text())
    assert independent['status']=='passed' and independent['passed_case_count']==25
    independent_cases={r['slot']:r for r in independent['cases']}
    kb=ROOT.parent/'Analog-Circuit-Knowledge-Base/SMIC18-Benchmark-Reproduction'
    state=json.loads((ROOT/'status.json').read_text())
    rows=[]
    for b in base['cases']:
        slot=b['slot'];case=case_path(slot);a=json.loads((case/'schematic_audit.json').read_text());p=json.loads((case/'pdf_provenance.json').read_text());row=state['cases'][slot-1]
        assert row['status']==b['status'] and row['review_pdf_ready']
        assert sha(case/'circuit.scs')==b['circuit_sha256']==a['circuit_sha256']
        assert sha(case/'latest_results.json')==b['results_sha256']==p['results_sha256']
        assert a['status']=='passed' and not a['render_review_pending'] and not a['geometric_wire_conflicts']
        assert a['all_rendered_pins_have_drawn_path_to_correct_net_label'] and a['all_pages_visually_reviewed']
        for path,h in a['artifacts'].items():assert sha(ROOT/path)==h
        if slot!=25:
            peer=independent_cases[slot]
            assert peer['status']=='passed' and not peer['errors']
            assert peer['circuit_sha256']==sha(case/'circuit.scs')
            assert peer['connectivity_sha256']==sha(case/'schematic/connectivity.json')
            assert a['final_source_freeze_at'] and not a['rebuild_png_changes']
            assert sha(case/'schematic/renderer_source.py')==a['renderer_sha256']
            assert sha(case/'schematic/layout_source.py')==a['layout_sha256']
            assert p['body_pages']==b['pages'] and p['schematic_pages']==a['sheets']
            assert p['pages']==b['pages']+a['sheets']
            assert len(p['page_merge_checks'])==p['pages'] and all(q['pixel_identical'] for q in p['page_merge_checks'])
            assert p['schematic_audit_sha256']==sha(case/'schematic_audit.json')
        else:assert p['sha256']==b['pdf_sha256'] and p['pages']==b['pages']
        assert sha(ROOT/p['pdf'])==p['sha256'] and not p['render_review_pending']
        assert sha(case/'schematic/sheets.pdf')==p['schematic_sheets_sha256']
        ev=kb/'evidence'/case.name
        for path in ['review.pdf','circuit.scs','latest_results.json','pdf_provenance.json','schematic_audit.json','schematic/full.svg','schematic/full.pdf','schematic/sheets.pdf','schematic/connectivity.json']:
            original=ROOT/p['pdf'] if path=='review.pdf' else case/path
            assert sha(ev/path)==sha(original),(slot,path)
        note=(kb/'cases'/f'{case.name}.md').read_text()
        assert 'schematic/full.svg' in note and 'schematic/sheets.pdf' in note
        rows.append(dict(slot=slot,slug=case.name,pdf=p['pdf'],pdf_pages=p['pages'],schematic_pages=a['sheets'],instances=a['total_instances'],terminals=a['total_terminals'],instance_counts=a['instance_counts'],status=row['status'],circuit_and_results_unchanged=True,source_and_published_hashes_match=True,pdf_sha256=p['sha256']))
    newruns=[];last_started=''
    for path in (ROOT/'runs').glob('*/*/run.json'):
        r=json.loads(path.read_text());stamp=r.get('started_at','');last_started=max(last_started,stamp)
        if stamp>base['started_at']:newruns.append(str(path.relative_to(ROOT)))
    assert not newruns,'Unexpected electrical simulation run during documentation task'
    report=dict(audited_at=now(),status='passed',scope='All26 delivered SMIC18 reports have complete reviewed schematics;25 old reports supplemented,case25 retained',reports=26,newly_supplemented=25,schematic_pages=sum(r['schematic_pages'] for r in rows),new_schematic_pages=sum(r['schematic_pages'] for r in rows if r['slot']!=25),report_pages=sum(r['pdf_pages'] for r in rows),total_definition_instances=sum(r['instances'] for r in rows),total_definition_terminals=sum(r['terminals'] for r in rows),all_circuits_and_results_unchanged=True,new_simulation_runs=newruns,last_existing_simulation_started_at=last_started,cases=rows)
    report['independent_review']=dict(path=str(independent_path.relative_to(ROOT)),sha256=sha(independent_path),status=independent['status'],totals=independent['totals'])
    write(ROOT/'reports/schematic-retrofit-audit.json',report)
    md='# 全部已交付报告：完整电路图目录\n\n'
    md+=f"26份报告均包含晶体管／原厂标准单元图；本轮补齐25份，共新增{report['new_schematic_pages']}页，连同第25项已有图纸共{report['schematic_pages']}页。模拟器件、工艺无源及全部体端已标明，层次模块包含顶层映射和内部完整电路。\n\n"
    md+='本轮只补文档，没有新增仿真或更改任何电路、尺寸、性能数据及验收等级。原报告正文和附图合并后逐页渲染比对一致。所有图纸均经实际目检及静态连接核对；这不是额外电气签核。\n\n'
    md+='|编号|模块|更新后报告|电路分图|可缩放总图|\n|---|---|---|---|---|\n'
    for r in rows:
        e='../cases/'+r['slug']+'/schematic/'
        md+=f"|{r['slot']:02d}|{r['slug']}|[{r['pdf_pages']}页PDF]({Path(r['pdf']).name})|[{r['schematic_pages']}页]({e}sheets.pdf)|[SVG]({e}full.svg) · [PDF]({e}full.pdf)|\n"
    md+='\n[交付审计](schematic-retrofit-audit.json) · [独立静态复核](schematic-independent-review.md) · [原始文档备份](pre-schematic-20260923/) · [补图基线](schematic-retrofit-baseline.json)\n'
    (ROOT/'reports/schematic-retrofit-index.md').write_text(md)
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':audit()
