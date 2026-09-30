"""Validate the published snapshot without EDA software or third-party Python packages."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((ROOT / 'publication/files.sha256.json').read_text())
    for name, digest in manifest.items():
        assert sha(ROOT / name) == digest, f'Published file changed: {name}'
    state = json.loads((ROOT / 'status.json').read_text())
    cases = sorted(p for p in (ROOT / 'cases').iterdir() if p.is_dir() and re.match(r'^\d{2}-', p.name))
    assert len(cases) == len(state['cases']) == 50
    mermaid = 0
    pdf_pages = 0
    for row, case in zip(state['cases'], cases):
        assert int(case.name[:2]) == row['slot'] and row['nominal_complete'] and row['review_pdf_ready']
        result = json.loads((case / 'latest_results.json').read_text())
        proof = json.loads((case / 'pdf_provenance.json').read_text())
        assert result['status'] == row['status']
        assert not proof['render_review_pending']
        assert sha(case / 'circuit.scs') == proof['circuit_sha256']
        assert sha(case / 'latest_results.json') == proof['results_sha256']
        assert sha(case / 'review.pdf') == sha(ROOT / proof['pdf']) == proof['sha256']
        text = (case / 'review_report.md').read_text()
        assert len(text) > 1000 and (case / 'schematic/full.svg').is_file()
        readable = json.loads((case / 'markdown_readability.json').read_text())
        assert readable['review_status'] == 'passed'
        assert sha(case / 'review_report.md') == readable['markdown_sha256']
        assert not re.search(r'!\[[^\]]*\]\([^)]*(?:markdown_assets|pdf_review)/page-\d', text)
        assert '图内标注与坐标文字' not in text
        netlists = re.findall(r'```spectre\n(.*?)\n```', text, re.S)
        assert netlists == [(case / 'circuit.scs').read_text().rstrip()]
        for fig in readable['figures']:
            assert sha(case / fig['png']) == fig['png_sha256']
            assert sha(case / fig['svg']) == fig['svg_sha256']
        if (case / 'system_block_diagram.mmd').exists():
            source = (case / 'system_block_diagram.mmd').read_text()
            assert '```mermaid\n' + source + '```' in text
            assert (case / 'markdown_assets/system-block.svg').is_file()
            mermaid += 1
        pdf_pages += proof['pages']
    assert mermaid == 28 and pdf_pages == 533
    prohibited = []
    large = []
    secrets = []
    secret_pattern = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{50,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}')
    for name in manifest:
        p = ROOT / name
        if p.name == 'hd_cells.scs' or p.suffix in {'.cdl', '.lib', '.lic'} or p.name == 'license.dat' or 'output' in p.relative_to(ROOT).parts:
            prohibited.append(name)
        if p.stat().st_size >= 50 * 1024**2:
            large.append(name)
        if p.suffix.lower() in {'.py', '.sh', '.md', '.json', '.toml', '.yml', '.yaml', '.scs', '.spi', '.txt'} and secret_pattern.search(p.read_bytes()):
            secrets.append(name)
    assert not prohibited, prohibited
    assert not large, large
    assert not secrets, f'Possible credential material in: {secrets}'
    print(json.dumps({'status': 'passed', 'files_sha256_checked': len(manifest), 'cases': len(cases), 'pdf_pages': pdf_pages, 'mermaid_diagrams': mermaid, 'acceptance_counts': dict(Counter(r['status'] for r in state['cases'])), 'vendor_libraries': 0, 'large_files': 0, 'credential_patterns': 0}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
