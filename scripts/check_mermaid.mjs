import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { JSDOM } from '../.report-tools/mermaid/node_modules/jsdom/lib/api.js';
const root = path.resolve(import.meta.dirname, '..');
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const {default:mermaid} = await import('../.report-tools/mermaid/node_modules/mermaid/dist/mermaid.esm.mjs');
mermaid.initialize({startOnLoad:false,securityLevel:'strict'});
const rows=[];
for (const name of fs.readdirSync(path.join(root,'cases')).sort()) {
  const f=path.join(root,'cases',name,'system_block_diagram.mmd');
  if (!fs.existsSync(f)) continue;
  const result=await mermaid.parse(fs.readFileSync(f,'utf8'));
  if (!result) throw new Error(`Mermaid parse rejected ${name}`);
  rows.push({case:name,diagramType:result.diagramType,status:'passed',mermaid_sha256:createHash('sha256').update(fs.readFileSync(f)).digest('hex')});
}
const report={checked_at:new Date().toISOString(),mermaid_version:'11.12.0',check:'Actual Mermaid parser in isolated documentation tools; no circuit data sent to external services.',diagrams:rows.length,status:'passed',cases:rows};
fs.writeFileSync(path.join(root,'reports/mermaid-syntax-audit.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:'passed',diagrams:rows.length}));
