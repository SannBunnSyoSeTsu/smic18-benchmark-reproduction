"""Keep editable Markdown beside the existing Matplotlib PDF delivery format."""
from report29 import *
from module_overviews import overview

class Report:
    def __init__(self,case):
        self.case=case;self.body=ROOT/'reports'/f'{case.name}-body.pdf';self.pdf=PdfPages(self.body);self.n=0;self.fig=None
        self.md=['# '+case.name+' 审查报告','PDF由Python/Matplotlib排版生成。此Markdown从同一报告文本、表格和网表保存，便于编辑；它不是PDF编译输入。完整生成脚本随implementation目录保存。']
    def page(self,title,subtitle):
        self.end_page();self.n+=1;self.fig=frame(title,self.n,subtitle);self.md+=['## '+title]
        if self.n==1:self.md.append(overview(int(self.case.name[:2])))
        self.md.append(subtitle);return self.fig
    def paragraph(self,y,text,size=9.3):
        if self.n==1 and text==overview(int(self.case.name[:2])):return
        para(self.fig,y,text,size);self.md.append(text)
    def table(self,box,headers,rows,widths,size=8):
        table(self.fig,box,headers,rows,widths,size)
        def cell(value):
            return re.sub(r'(?<!\\)\|',r'\\|',str(value)).replace('\r\n','\n').replace('\n','<br>')
        assert all(len(row)==len(headers) for row in rows), 'Markdown table column count differs'
        lines=['| '+' | '.join(cell(x) for x in headers)+' |','| '+' | '.join('---' for _ in headers)+' |']
        lines += ['| '+' | '.join(cell(x) for x in row)+' |' for row in rows]
        # One Markdown block: blank lines separate blocks, never table rows.
        self.md.append('\n'.join(lines))
    def chart(self,description):self.md += [description,f'![{description}](pdf_review/page-{self.n:02d}.png)']
    def netlist(self,text,lines_per_page=48,wrap_long_lines=False):
        import textwrap
        chunks=[];raw=[];display=[]
        for line in text.splitlines():
            visual=(textwrap.wrap(line,width=120,subsequent_indent='    ',break_long_words=False,break_on_hyphens=False) or ['']) if wrap_long_lines else [line]
            if len(display)+len(visual)>lines_per_page:chunks.append((raw,display));raw=[];display=[]
            raw.append(line);display.extend(visual)
        if raw:chunks.append((raw,display))
        for i,(chunk,visual) in enumerate(chunks):
            subtitle='所有实例、尺寸和连接原样列出。'
            if (self.case/'hd_cells.scs').exists():subtitle+='HD内部器件见随附原厂CDL提取。'
            if wrap_long_lines:subtitle+='PDF长行仅作视觉折行，MD保留原始行。'
            self.page(f'完整最终网表 {i+1}/{len(chunks)}',subtitle)
            self.fig.text(.07,.85,'\n'.join(visual),fontfamily='DejaVu Sans Mono',fontsize=7.1,va='top',linespacing=1.4)
            self.md += ['```spectre\n'+'\n'.join(chunk)+'\n```']
    def end_page(self):
        if self.fig is not None:save(self.pdf,self.fig);self.fig=None
    def finish(self):
        self.end_page();self.pdf.close();self.md += ['## 完整电路图','[全部分图PDF](schematic/sheets.pdf) · [电路总图](schematic/full.pdf) · [端子连接审计](schematic/connectivity.json)']
        for p in sorted((self.case/'schematic').glob('sheet-*.png'),key=lambda p:int(p.stem.split('-')[-1])):self.md.append(f'![{p.stem}](schematic/{p.name})')
        (self.case/'review_report.md').write_text('\n\n'.join(self.md)+'\n')
        from system_diagrams import append
        append(self.case)
        from audit_markdown import inspect
        assert not inspect(self.case/'review_report.md')['issues'], 'Markdown table validation failed'
        finish_report(self.case,self.body,self.n)
