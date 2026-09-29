"""Render local Mermaid sources using isolated local CLI/browser for visual review."""
from pathlib import Path
import argparse,subprocess,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1]
T=ROOT/'.report-tools'
def main(slots):
    rows=[]
    for c in sorted((ROOT/'cases').iterdir()):
        p=c/'system_block_diagram.mmd'
        if not p.exists() or (slots and int(c.name[:2]) not in slots):continue
        a=c/'markdown_assets';a.mkdir(exist_ok=True)
        for ext in ['svg','png']:
            cmd=[str(T/'node-v22.14.0-linux-x64/bin/node'),str(T/'mermaid/node_modules/@mermaid-js/mermaid-cli/src/cli.js'),'-i',str(p),'-o',str(a/f'system-block.{ext}'),'-p',str(T/'puppeteer.json'),'-c',str(T/'mermaid-config.json'),'-b','white','--quiet','-w','1400','-s','2']
            q=subprocess.run(cmd,capture_output=True,text=True);assert q.returncode==0,(c.name,q.stderr)
        rows.append(dict(case=c.name,mermaid_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),svg_sha256=hashlib.sha256((a/'system-block.svg').read_bytes()).hexdigest(),png_sha256=hashlib.sha256((a/'system-block.png').read_bytes()).hexdigest()))
        print(c.name,flush=True)
    path=ROOT/'reports/mermaid-render-audit.json'
    prior={x['case']:x for x in json.loads(path.read_text())['cases']} if path.exists() else {}
    prior.update({x['case']:x for x in rows})
    out=dict(rendered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),renderer='mermaid-cli11.12.0 / local headless Chrome131',cases=[prior[k] for k in sorted(prior)])
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slots',type=int,nargs='*');a=p.parse_args();main(a.slots)
