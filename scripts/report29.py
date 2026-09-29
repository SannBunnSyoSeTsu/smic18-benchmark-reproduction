"""Render new batch PDFs with the established opening and full schematic scheme."""
from review_pdf import *
from review11 import frame,para,table
import subprocess
from matplotlib.ticker import FuncFormatter

def finish_report(case,body,body_pages):
    r=json.loads((case/'latest_results.json').read_text());sc=json.loads((case/'schematic_audit.json').read_text())
    out=ROOT/'reports'/f'{case.name}-review.pdf'
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    n=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1]);assert n==body_pages+sc['sheets']
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=r['circuit_sha256'],sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=n,body_pages=body_pages,schematic_pages=sc['sheets'],schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True))
    dest=case/'pdf_review';dest.mkdir(exist_ok=True)
    for p in dest.glob('page-*.png'):p.unlink()
    subprocess.run(['pdftoppm','-scale-to','1500','-png',str(out),str(dest/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    for p in sorted(dest.glob('page-*.png')):
        q=dest/f'page-{int(p.stem.split("-")[-1]):02d}.png'
        if p!=q:p.rename(q)
    assert len(list(dest.glob('page-*.png')))==n
    print(str(out))

def clean_axes(axs):
    for ax in np.atleast_1d(axs).flat:
        ax.grid(alpha=.22);ax.tick_params(labelsize=8)
        if ax.get_xscale()=='log':ax.xaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v:g}'))
