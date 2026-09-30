"""Build readable Markdown from frozen reports; never run EDA or rewrite PDFs.

Requires PyMuPDF, Markdown, and Poppler's pdftohtml. PDF text/table recovery
retains the recorded cells; figure-only clips exclude report prose and tables.
The earlier publication commit is the stable input for repeatable correction.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import html
import json
import re
import subprocess
import sys

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from restore_report_markdown import pdf_pages, recover_page, recover_tables, prose

BASE = '0d018d12741f99c4fd0c7ad105c4434f18638623'
# These two panels contain textual callouts beside a table, not a graph.
CALLOUTS = {
    ('11-bandgap', 3): 'ΔVBE ≈ 54.862 mV，va−vb = 41.966 μV，MSTART 稳态电流为 6.656 pA。表中电流符号沿用 Spectre：PMOS 电流为负，幅度列取绝对值。',
    ('25-complementary-ab', 3): '体效应复制关系为 GN ≈ XN、GP ≈ YP，IABN + IABP = K。MOUTN/P 的并联倍数 m=20，MABNL/PL 为 m=1。',
}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def original(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + str(path.relative_to(ROOT))], cwd=ROOT).decode()


def compact(s):
    return re.sub(r'\s+', '', s)


def source_phrases():
    phrases = {}
    templates = []
    for path in (ROOT / 'scripts').glob('*.py'):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) >= 24:
                phrases.setdefault(compact(node.value), node.value)
            elif isinstance(node, ast.JoinedStr):
                chunks = [c.value if isinstance(c, ast.Constant) else None for c in node.values]
                if sum(len(c or '') for c in chunks) > 30:
                    pattern = ''.join(re.escape(compact(c)) if c is not None else r'(.+?)' for c in chunks)
                    templates.append((re.compile('^' + pattern + '$'), chunks))
    return phrases, templates


PHRASES, TEMPLATES = source_phrases()


def repair_paragraphs(body):
    repaired = []
    for block in body.split('\n\n'):
        if not block.startswith(('|', '```', '<', '![')):
            plain = html.unescape(re.sub(r'\\([_*\\])', r'\1', block))
            known = PHRASES.get(compact(plain))
            if known:
                block = prose(known).replace('\n', ' ')
            else:
                for pattern, chunks in TEMPLATES:
                    match = pattern.fullmatch(compact(plain))
                    if match and all(re.fullmatch(r'[\d.eE+−-]+', g) for g in match.groups()):
                        values = iter(match.groups())
                        block = prose(''.join(c if c is not None else next(values) for c in chunks)).replace('\n', ' ')
                        break
        repaired.append(block)
    return '\n\n'.join(repaired)


def figure_regions(page, pdfpage):
    """Use PDF text roles to separate graphics from editable report content."""
    tables, used = recover_tables(page)
    sx, sy = pdfpage.rect.width / page['width'], pdfpage.rect.height / page['height']
    drawings = pdfpage.get_drawings()
    obstacles = [(0, page['height'] * .10), (page['height'] * .94, page['height'])]
    for table in tables:
        cells = [t for t in page['texts'] if t['i'] in table['pdf_text_indices']]
        low = min(t['top'] for t in cells) * sy
        high = max(t['top'] + t['height'] for t in cells) * sy
        # Text bounds do not include the table border or header background.
        for d in drawings:
            r = d['rect']
            if d['fill'] is not None and 2 < r.height < 80 and r.width > 8:
                if any(r.contains(fitz.Point((t['left'] + t['width'] / 2) * sx,
                                             (t['top'] + t['height'] / 2) * sy)) for t in cells):
                    low = min(low, r.y0)
                    high = max(high, r.y1)
        obstacles.append((low / sy - 2, high / sy + 2))
    extras = []
    for t in page['texts']:
        if t['i'] in used or t['top'] < page['height'] * .10 or t['top'] > page['height'] * .94:
            continue
        if 'Mono' in t['family'] or t['color'] in ['#172c3d', '#506273']:
            obstacles.append((t['top'] - 2, t['top'] + t['height'] + 2))
        else:
            extras.append(t)
    merged = []
    for lo, hi in sorted(obstacles):
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(hi, merged[-1][1])
        else:
            merged.append([lo, hi])
    bands = [(a[1], b[0]) for a, b in zip(merged, merged[1:]) if b[0] > a[1]]
    regions = []
    for lo, hi in bands:
        labels = [t for t in extras if lo <= t['top'] + t['height'] / 2 <= hi]
        if not labels:
            continue
        # Include chart axes and diagram strokes as well as all tick/legend text.
        rects = [fitz.Rect(t['left'] * sx, t['top'] * sy,
                           (t['left'] + t['width']) * sx,
                           (t['top'] + t['height']) * sy) for t in labels]
        for d in drawings:
            r = d['rect']
            if r.y0 >= lo * sy and r.y1 <= hi * sy and (r.width > 1 or r.height > 1):
                rects.append(r)
        box = fitz.Rect(rects[0])
        for r in rects[1:]:
            box |= r
        # Poppler reports the advance width of rotated labels, not their true
        # horizontal extent. Keep the page width so vertical axis labels survive.
        box = fitz.Rect(0, max(lo * sy, box.y0 - 7),
                        pdfpage.rect.width, min(hi * sy, box.y1 + 7))
        assert box.height > 10 and box.width > 20, (page['number'], box)
        regions.append((box, lo, hi))
    accounted = sum(sum(lo <= t['top'] + t['height'] / 2 <= hi for t in extras) for _, lo, hi in regions)
    if accounted != len(extras):
        raise ValueError(('Figure labels overlap report text; review required', page['number'], len(extras), accounted))
    return regions


def export_figures(case, pages, doc):
    assets = case / 'markdown_assets'
    assets.mkdir(exist_ok=True)
    records = []
    for page in pages:
        n = page['number']
        if (case.name, n) in CALLOUTS:
            continue
        for k, (box, lo, hi) in enumerate(figure_regions(page, doc[n - 1]), 1):
            name = f'figure-{n:02d}-{k:02d}'
            png = assets / (name + '.png')
            doc[n - 1].get_pixmap(matrix=fitz.Matrix(2, 2), clip=box, alpha=False).save(png)
            one = fitz.open()
            outpage = one.new_page(width=box.width, height=box.height)
            outpage.show_pdf_page(outpage.rect, doc, n - 1, clip=box)
            svg = assets / (name + '.svg')
            svg.write_text(outpage.get_svg_image())
            records.append(dict(page=n, position=(lo + hi) / 2, clip_pdf_points=list(box),
                                png=str(png.relative_to(case)), svg=str(svg.relative_to(case)),
                                png_sha256=digest(png), svg_sha256=digest(svg)))
    return records


def netlist_and_schematics(case):
    parts = ['## 完整网表与电路图',
             '[Spectre 网表](circuit.scs) · [全部分图 PDF](schematic/sheets.pdf) · '
             '[电路总图](schematic/full.svg) · [端子连接](schematic/connectivity.json)',
             '<details>\n<summary>展开完整 Spectre 网表</summary>\n\n```spectre\n' +
             (case / 'circuit.scs').read_text().rstrip() + '\n```\n\n</details>']
    for p in sorted((case / 'schematic').glob('sheet-*.png'), key=lambda p: int(p.stem.split('-')[-1])):
        parts.append(f'![电路分图 {p.stem.split("-")[-1]}](schematic/{p.name})')
    return '\n\n'.join(parts)


def revise(case):
    md = case / 'review_report.md'
    before = original(md)
    proof = json.loads((case / 'pdf_provenance.json').read_text())
    pdf = case / 'review.pdf'
    assert digest(pdf) == proof['sha256']
    restored = (case / 'markdown_provenance.json').exists()
    doc = fitz.open(pdf)
    pages = pdf_pages(pdf, proof['body_pages'])
    selected = pages if restored else [p for p in pages if p['number'] == 3]
    figures = export_figures(case, selected, doc)
    if restored:
        parts = []
        for page in pages:
            title, body, record = recover_page(page)
            body = re.sub(r'<details>.*?</details>', '', body, flags=re.S)
            # All monospaced PDF blocks are partial/wrapped copies of circuit.scs.
            body = re.sub(r'```text\n.*?\n```', '', body, flags=re.S)
            body = repair_paragraphs(body)
            if (case.name, page['number']) in CALLOUTS:
                body += '\n\n' + CALLOUTS[case.name, page['number']]
            body = re.sub(r'\n{3,}', '\n\n', body).strip()
            body = re.sub(r'见第\d+页', '见文末完整网表', body)
            title = re.sub(r'^\d+\s*[|｜]\s*', '', title)
            if page['number'] == 1:
                parts += ['# ' + case.name[:2] + ' · ' + title,
                          '[审查 PDF](review.pdf) · [实测结果](latest_results.json) · '
                          '[验收合同](contract.json) · [最终网表](circuit.scs)', '## 验收结果', body]
                system = re.search(r'<!-- SYSTEM-BLOCK-DIAGRAM -->.*?<!-- END-SYSTEM-BLOCK-DIAGRAM -->', before, re.S)
                if system:
                    parts.append(system.group())
            else:
                parts += ['## ' + title, body]
            for f in figures:
                if f['page'] == page['number']:
                    parts.append(f'![{title}]({f["png"]})\n\n[查看矢量图]({f["svg"]})')
        parts += [netlist_and_schematics(case),
                  '## 报告来源\n\n正文与表格整理自已交付的矢量 PDF，图表单独提取；'
                  '本文件是后续整理的 Markdown，不是原 PDF 的编译输入。'
                  '原 PDF、网表及测量数据保持原值。']
        after = '\n\n'.join(p for p in parts if p)
    else:
        after = before
        for m in list(re.finditer(r'!\[([^\]]*)\]\(pdf_review/page-0?3\.png\)', after)):
            replacement = '\n\n'.join(f'![{m.group(1)}]({f["png"]})\n\n[查看矢量图]({f["svg"]})' for f in figures)
            after = after.replace(m.group(), replacement)
        after = re.sub(r'## 完整最终网表.*', netlist_and_schematics(case), after, flags=re.S)
    after = re.sub(r'\n{3,}', '\n\n', after).strip() + '\n'
    md.write_text(after)
    receipt = dict(case=case.name, source_commit=BASE, markdown_sha256=digest(md),
                   pdf_sha256=digest(pdf), circuit_sha256=digest(case / 'circuit.scs'),
                   results_sha256=digest(case / 'latest_results.json'),
                   removed_page_images=len(re.findall(r'!\[.*?\]\([^)]*page-', before)),
                   removed_label_dumps=before.count('图内标注与坐标文字'),
                   figures=figures, review_status='awaiting_visual_review')
    (case / 'markdown_readability.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'figures'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('slots', nargs='*', type=int)
    args = p.parse_args()
    for case in sorted((ROOT / 'cases').glob('[0-9][0-9]-*')):
        if not args.slots or int(case.name[:2]) in args.slots:
            revise(case)
