"""Append reviewed drawings to frozen reports; no electrical extraction/simulation.

The original PDF is retained. Every original and appended page is rendered
through Poppler before/after merging and must have identical pixel content.
"""
import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageChops
from schematic_common import ROOT,case_path,sha,now,write


def run(args):return subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True).stdout
def pages(pdf):return int(re.search(r'^Pages:\s+(\d+)',run(['pdfinfo',pdf]),re.M)[1])
def render(pdf,dst):
    run(['pdftoppm','-r','90','-png',pdf,dst])
    return sorted(dst.parent.glob(dst.name+'-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
def digest_pixels(path):
    with Image.open(path) as im:return dict(size=list(im.size),rgb_sha256=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest())


def sync_audit(case,b,pp):
    if not (case/'verification_audit.json').exists():return
    prior=json.loads((ROOT/b['archive']/'verification_audit.json').read_text())
    prior['documentation_update']=dict(updated_at=now(),scope='Append complete schematic pages only; existing electrical evidence unchanged',circuit_sha256=b['circuit_sha256'],results_sha256=b['results_sha256'],previous_pdf_sha256=b['pdf_sha256'],current_pdf_sha256=pp['sha256'],schematic_audit_sha256=sha(case/'schematic_audit.json'),report_pages=pp['pages'],all_merged_pages_pixel_identical_to_sources=True)
    historical={k:prior[k] for k in ['pdf','pdf_sha256','pdf_pages'] if k in prior}
    if historical:
        prior['documentation_update']['historical_pdf_fields']=historical
        if 'pdf' in prior:prior['pdf']=pp
        if 'pdf_sha256' in prior:prior['pdf_sha256']=pp['sha256']
        if 'pdf_pages' in prior:prior['pdf_pages']=pp['pages']
    write(case/'verification_audit.json',prior)


def append(slot):
    assert slot!=25,'Case25 already contains its complete schematic; do not append twice'
    case=case_path(slot)
    baseline=json.loads((ROOT/'reports/schematic-retrofit-baseline.json').read_text())
    b=next(r for r in baseline['cases'] if r['slot']==slot)
    original=ROOT/b['archive']/Path(b['pdf']).name
    oldpp=json.loads((ROOT/b['archive']/'pdf_provenance.json').read_text())
    a=json.loads((case/'schematic_audit.json').read_text())
    assert sha(case/'circuit.scs')==b['circuit_sha256']==a['circuit_sha256']
    assert sha(case/'latest_results.json')==b['results_sha256']
    assert sha(original)==b['pdf_sha256']==oldpp['sha256']
    assert a['status']=='passed' and not a['render_review_pending'] and a['all_pages_visually_reviewed']
    for p,h in a['artifacts'].items():assert sha(ROOT/p)==h
    drawing=case/'schematic/sheets.pdf';assert pages(drawing)==a['sheets']
    out=ROOT/b['pdf'];tmp=out.with_name(out.stem+'-merging.pdf')
    run(['pdfunite',original,drawing,tmp])
    assert pages(tmp)==b['pages']+a['sheets']
    # Preserve searchable content as well as pixel output of every page.
    oldtext=run(['pdftotext','-layout',original,'-'])
    prefixtext=run(['pdftotext','-f','1','-l',str(b['pages']),'-layout',tmp,'-'])
    assert oldtext==prefixtext,'Original report text changed during merge'
    renderdir=ROOT/'reports/schematic-retrofit-renders'/case.name
    renderdir.mkdir(parents=True,exist_ok=True)
    comparisons=[]
    with tempfile.TemporaryDirectory(prefix=f'schematic-{slot:02d}-') as scratch:
        scratch=Path(scratch)
        base_images=render(original,scratch/'body')
        drawing_images=render(drawing,scratch/'drawing')
        final_images=render(tmp,scratch/'merged')
        assert len(final_images)==len(base_images)+len(drawing_images)
        for i,(source,final) in enumerate(zip(base_images+drawing_images,final_images),1):
            ds,df=digest_pixels(source),digest_pixels(final)
            assert ds==df,('PDF page changed on merge',slot,i)
            q=dict(page=i,kind='preserved_body' if i<=len(base_images) else 'schematic_appendix',pixel_identical=True,**df)
            if i>len(base_images):
                dst=renderdir/f'page-{i:02d}.png';shutil.copy2(final,dst)
                q.update(path=str(dst.relative_to(ROOT)),sha256=sha(dst))
            comparisons.append(q)
    tmp.replace(out)
    pp=copy.deepcopy(oldpp)
    for key in ['rendered_pages','render_review_images','visually_reviewed_at']:
        pp.pop(key,None)
    pp.update(sha256=sha(out),generated_at=now(),pages=pages(out),body_pages=b['pages'],schematic_pages=a['sheets'],schematic_sheets_sha256=sha(drawing),schematic_audit_sha256=sha(case/'schematic_audit.json'),render_review_pending=False,render_reviewed_at=now(),all_pages_visually_reviewed=True,documentation_only=True,previous_body_pdf=dict(path=str(original.relative_to(ROOT)),sha256=sha(original),pages=b['pages'],previous_render_reviewed_at=oldpp.get('render_reviewed_at')),page_merge_checks=comparisons,render_review_note='Previously reviewed body pages preserved. New schematic sheets and full overview actually inspected by the drawing reviewer. All body and appended pages were independently rendered with Poppler and pixel-compared to their pre-merge source PDFs; every page is identical. No electrical rerun or result change.')
    write(case/'pdf_provenance.json',pp)
    sync_audit(case,b,pp)
    from common import update_case
    update_case(slot,review_pdf_ready=True,pdf_render_review_pending=False,review_pdf_pages=pp['pages'],review_pdf_sha256=pp['sha256'],schematic_complete=True,schematic_pages=a['sheets'],documentation_updated_at=now())
    return dict(slot=slot,pages=pp['pages'],schematic_pages=a['sheets'],all_body_and_schematic_pages_pixel_identical=True,pdf_sha256=pp['sha256'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slots',nargs='+',type=int);args=p.parse_args()
    for slot in args.slots:print(json.dumps(append(slot),ensure_ascii=False),flush=True)
