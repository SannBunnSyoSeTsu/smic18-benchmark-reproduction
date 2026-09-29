"""Check completed module PDFs, frozen circuits, LUT and knowledge evidence."""
from common import *
import subprocess
from publish_knowledge import KB,NAMES
from module_overviews import overview

def audit():
    state=json.loads((ROOT/'status.json').read_text());assert len(state['cases'])==50
    rows=[]
    for row in state['cases']:
        if not (row.get('nominal_complete') and row.get('review_pdf_ready')):continue
        slot=row['slot'];slug,_=NAMES[slot];case=ROOT/'cases'/slug
        r=json.loads((case/'latest_results.json').read_text());p=json.loads((case/'pdf_provenance.json').read_text());pdf=ROOT/p['pdf']
        assert r['status']==row['status'] and r['status'].startswith('complete_')
        tier=r['status'].removeprefix('complete_');assert r['pass_tiers'][tier] and r['all_nominal_checks_complete']
        assert not p['render_review_pending'] and p.get('render_reviewed_at')
        assert pdf.read_bytes().startswith(b'%PDF-') and sha(pdf)==p['sha256']
        assert sha(case/'circuit.scs')==p['circuit_sha256'] and sha(case/'latest_results.json')==p['results_sha256']
        info=subprocess.run(['pdfinfo',str(pdf)],check=True,capture_output=True,text=True).stdout
        assert int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])==p['pages']
        first_page=subprocess.run(['pdftotext','-f','1','-l','1',str(pdf),'-'],check=True,capture_output=True,text=True).stdout
        compact=lambda t:re.sub(r'\s+','',t)
        intro=compact(overview(slot));page_text=compact(first_page)
        assert intro in page_text and page_text.index(intro)<page_text.index('结论：')
        for run in r.get('run_dirs',[r.get('run_dir')]):
            meta=json.loads((ROOT/run/'run.json').read_text())
            assert meta['status']=='completed' and meta['model_dimensions_valid']
            assert sha(ROOT/run/'inputs/circuit.scs')==sha(case/'circuit.scs')
            assert sha(ROOT/meta['netlist'])==meta['netlist_sha256']
            for dep in meta['dependencies'].values():assert sha(ROOT/dep['snapshot'])==dep['sha256']
        if (case/'sizing.json').exists():
            for role in json.loads((case/'sizing.json').read_text())['roles'].values():
                assert sha(role['lut_path'])==role['lut_sha256']
        ev=KB/'evidence'/slug
        assert sha(ev/'review.pdf')==sha(pdf)
        assert sha(ev/'circuit.scs')==sha(case/'circuit.scs')
        assert sha(ev/'latest_results.json')==sha(case/'latest_results.json')
        note=(KB/'cases'/f'{slug}.md').read_text()
        assert overview(slot) in note and note.index(overview(slot))<note.index('状态：')
        rows.append(dict(slot=slot,status=row['status'],pdf=p['pdf'],pages=p['pages'],pdf_sha256=p['sha256'],evidence_consistent=True))
    report=dict(audited_at=now(),delivered_cases=len(rows),remaining_cases=50-len(rows),cases=rows)
    write_json(ROOT/'reports/delivery-audit.json',report)
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':audit()
