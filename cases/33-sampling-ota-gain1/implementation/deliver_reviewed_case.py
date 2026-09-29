"""Finalize an actually viewed report; never called by report generators.

The caller must have visually inspected every report page, every split schematic
and the full overview, then supply a truthful review note. No simulation here.
"""
from common import *
import argparse
import collections
import contextlib
import io
import shutil
from publish_knowledge import KB,NAMES,publish,index
from schematic_common import confirm_visual

def finish(slot,review_note):
    assert review_note.strip()
    slug,_=NAMES[slot];case=ROOT/'cases'/slug
    monitor=ROOT/'monitor/weekly-20260926-continue'
    assert not (monitor/'TRIGGER.json').exists(),'User stop condition triggered'
    r=json.loads((case/'latest_results.json').read_text());p=json.loads((case/'pdf_provenance.json').read_text());a=json.loads((case/'verification_audit.json').read_text())
    assert r['status'].startswith('complete_') and r['all_nominal_checks_complete'] and a['status']=='passed'
    assert r['pass_tiers'][r['status'].removeprefix('complete_')]
    assert p['sha256']==sha(ROOT/p['pdf']) and p['circuit_sha256']==r['circuit_sha256']==a['circuit_sha256']==sha(case/'circuit.scs')
    assert p['results_sha256']==a['results_sha256']==sha(case/'latest_results.json')
    rendered=sorted((case/'pdf_review').glob('page-*.png'));assert len(rendered)==p['pages']
    sc=confirm_visual(slot,review_note)
    p.update(render_review_pending=False,render_reviewed_at=now(),all_pages_visually_reviewed=True,render_review_note=review_note,rendered_pages={str(x.relative_to(ROOT)):sha(x) for x in rendered})
    write_json(case/'pdf_provenance.json',p)
    a.update(pdf_review_pending=False,pdf=p['pdf'],pdf_sha256=p['sha256'],pdf_pages=p['pages'],schematic_visual_review_complete=True,delivery_reviewed_at=now())
    write_json(case/'verification_audit.json',a)
    impl=case/'implementation';impl.mkdir(exist_ok=True)
    names=[f'case{slot:02d}_*.py',f'audit{slot:02d}.py',f'review{slot:02d}.py',f'schematic{slot:02d}.py','common.py','review_pdf.py','module_overviews.py','review11.py','schematic11.py','schematic_common.py','schematic25.py','audit_schematic_independent.py','publish_knowledge.py','audit_delivery.py','deliver_reviewed_case.py','hd_cells.py']
    sources=sorted({x for pattern in names for x in (ROOT/'scripts').glob(pattern)})
    if slot in (1,9,15,33):sources.append(ROOT/'scripts/case21_highpsrr_bandgap.py') # imported quota guard
    if slot==1:sources += [ROOT/'scripts/confirm01.py',ROOT/'scripts/supplement_lut.py']
    if slot==33:sources += [ROOT/'scripts/confirm33.py',ROOT/'scripts/schematics_analog.py']
    if slot==15:sources += [ROOT/'scripts/confirm15.py',ROOT/'scripts/supplement_lut.py']
    manifest={}
    for src in sources:
        dst=impl/src.name;shutil.copy2(src,dst);manifest[str(src.relative_to(ROOT))]=dict(sha256=sha(src),snapshot=str(dst.relative_to(ROOT)))
    (impl/'README.md').write_text('# Source snapshots\n\nFrozen generation and verification sources. These are provenance copies; use the scripts/ entry points in the project root. Rebuilding the report requires a new actual visual review. Do not invoke deliver_reviewed_case until every page and the full schematic have been viewed.\n')
    write_json(case/'implementation_provenance.json',dict(captured_at=now(),sources=manifest))
    before=json.loads((ROOT/'status.json').read_text());unchanged={}
    for row in before['cases']:
        if row['slot']==slot or not row['nominal_complete']:continue
        old_slug=NAMES[row['slot']][0]
        for base in [KB/'cases'/f'{old_slug}.md',KB/'evidence'/old_slug]:
            for path in ([base] if base.is_file() else base.rglob('*')):
                if path.is_file():unchanged[str(path.relative_to(KB))]=sha(path)
    if (ROOT/'reports/delivery-audit.json').exists():
        backup=ROOT/'reports'/f'delivery-audit-before-{slot:02d}.json'
        if not backup.exists():shutil.copy2(ROOT/'reports/delivery-audit.json',backup)
    update_case(slot,status=r['status'],nominal_complete=True,review_pdf_ready=True,pdf_render_review_pending=False,review_pdf=p['pdf'],review_pdf_pages=p['pages'],review_pdf_sha256=p['sha256'],report=str((case/'latest_results.json').relative_to(ROOT)),model_dimensions_valid=True,opening_overview_ready=True,schematic_complete=True,schematic_pages=p['schematic_pages'],run_dirs=r['run_dirs'],knowledge_note=str((case/'knowledge.md').relative_to(ROOT)),verification_audit=str((case/'verification_audit.json').relative_to(ROOT)),documentation_updated_at=now())
    publish(slot);index()
    for path,h in unchanged.items():assert sha(KB/path)==h,path
    ev=KB/'evidence'/slug;published={}
    for dst in ev.rglob('*'):
        if not dst.is_file():continue
        rel=dst.relative_to(ev);src=ROOT/p['pdf'] if str(rel)=='review.pdf' else case/rel
        assert src.is_file() and sha(src)==sha(dst),str(dst)
        published[str(rel)]=sha(dst)
    note=KB/'cases'/f'{slug}.md';links=[]
    for target in re.findall(r'\]\(([^)]+)\)',note.read_text()):
        if target.startswith('#') or '://' in target:continue
        path=Path(target) if target.startswith('/') else note.parent/target
        assert path.exists(),str(path);links.append(target)
    from audit_delivery import audit
    with contextlib.redirect_stdout(io.StringIO()):global_audit=audit()
    state=json.loads((ROOT/'status.json').read_text());ready=[x for x in state['cases'] if x['nominal_complete']];pending=[x for x in state['cases'] if not x['nominal_complete']]
    summary=dict(delivered_at=now(),status='passed',slot=slot,acceptance=r['status'],scope=r['scope'],gates=len(r['gates']),measurement_cross_checks=len(a.get('measurement_cross_checks',[])),schematic_instances=sc['total_instances'],schematic_terminals=sc['total_terminals'],schematic_pages=p['schematic_pages'],pdf_pages=p['pages'],all_pages_visually_reviewed=True,pdf=p['pdf'],pdf_sha256=p['sha256'],circuit_sha256=p['circuit_sha256'],results_sha256=p['results_sha256'],verification_audit_sha256=sha(case/'verification_audit.json'),pdf_provenance_sha256=sha(case/'pdf_provenance.json'),knowledge_note=str(note),knowledge_note_sha256=sha(note),published_artifacts_sha256=published,published_links_verified=len(links),prior_knowledge_files_unchanged=len(unchanged),global_delivered_cases=len(ready),global_remaining_cases=len(pending),full_pvt_mc_signoff=False)
    write_json(ROOT/'reports'/f'{slug}-delivery-audit.json',summary);shutil.copy2(ROOT/'reports'/f'{slug}-delivery-audit.json',ev/'delivery_audit.json')
    session=json.loads((ROOT/'current-session.json').read_text());session['newly_delivered_cases']=sorted(set(session.get('newly_delivered_cases',[])+[slot]));session.update(updated_at=now(),active_case=None,delivered_cases=len(ready),remaining_cases=len(pending),last_delivery_audit=f'reports/{slug}-delivery-audit.json');write_json(ROOT/'current-session.json',session)
    text=f'# 当前复现交付目录：{len(ready)}/50\n\n原理图级TT/nominal范围；各题保留相应功能维度，具体边界见分项报告。\n\n|编号|状态|审查PDF|完整电路图|知识库|\n|---|---|---|---|---|\n'
    for row in ready:
        name=NAMES[row['slot']][0];text+=f"|{row['slot']:02d}|{row['status']}|[{row['review_pdf_pages']}页]({Path(row['review_pdf']).name})|[总图](../cases/{name}/schematic/full.pdf)|[笔记]({KB}/cases/{name}.md)|\n"
    text+=f'\n[全局交付审计](delivery-audit.json) · [实时工程状态](../status.json)。剩余{len(pending)}项：'+', '.join(f"{x['slot']:02d}" for x in pending)+'。\n'
    (ROOT/'reports/current-delivery-index.md').write_text(text)
    print(json.dumps(dict(slot=slot,status='delivered',delivered_cases=len(ready),remaining_cases=len(pending),prior_KB_files_unchanged=len(unchanged),pdf_pages=p['pages'],measurement_checks=len(a.get('measurement_cross_checks',[]))),ensure_ascii=False))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slot',type=int);p.add_argument('--actual-visual-review-note',required=True);args=p.parse_args();finish(args.slot,args.actual_visual_review_note)
