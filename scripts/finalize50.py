"""Close the authorized final seven only after all 50 audited deliveries exist."""
from common import *
from publish_knowledge import KB,NAMES
from collections import Counter

def main():
    state=json.loads((ROOT/'status.json').read_text());rows=state['cases'];assert len(rows)==50 and all(x['nominal_complete'] and x['review_pdf_ready'] and not x['pdf_render_review_pending'] for x in rows)
    delivery=json.loads((ROOT/'reports/delivery-audit.json').read_text());assert delivery['delivered_cases']==50 and delivery['remaining_cases']==0
    documentation=json.loads((ROOT/'reports/markdown-delivery-audit.json').read_text());assert documentation['status']=='passed' and documentation['reports']==50 and documentation['system_diagrams']==28
    planned=[5,6,27,28,40,42,48];counts=Counter(x['status'] for x in rows);receipts=[]
    for slot in planned:
        slug=NAMES[slot][0];case=ROOT/'cases'/slug;r=json.loads((ROOT/'reports'/f'{slug}-delivery-audit.json').read_text());assert r['status']=='passed' and r['all_pages_visually_reviewed'] and (case/'review_report.md').is_file();receipts.append(r)
    text='# 最后七项复现交付：工程50/50\n\n本次05、06、27、28、40、42、48全部交付。沿用约定nominal范围、原刺激/负载/窗口、gm/ID初算、原厂HD、Spectre精算、独立核对、完整图纸和逐页PDF审查；不是全PVT/失配/PEX签核。\n\n'
    text+=f"累计：{counts['complete_original']}项原指标、{counts['complete_10pct']}项10%档、{counts['complete_15pct']}项15%档。\n\n|编号|模块|验收档|PDF页数|独立数值核对|审查报告|Markdown|知识库|\n|---|---|---|---:|---:|---|---|---|\n"
    for slot,r in zip(planned,receipts):
        slug=NAMES[slot][0];tier={'complete_original':'原指标','complete_10pct':'10%','complete_15pct':'15%'}[r['acceptance']]
        text+=f"|{slot:02d}|{slug}|{tier}|{r['pdf_pages']}|{r['measurement_cross_checks']}|[PDF]({Path(r['pdf']).name})|[MD](../cases/{slug}/review_report.md)|[笔记]({KB}/cases/{slug}.md)|\n"
    text+='\n05的平均VGS和最短死区未满足原门槛，达到10%档；28的增益与保持误差未满足原门槛，综合达到15%档。峰值保护与固定夹具/窗口按各项合同保留。\n\nPDF由Matplotlib生成；本次七项的可编辑MD由报告生成器同步保存，MD不是PDF编译输入。已修复Markdown表格空行/竖线问题；27、30、39、46的频谱柱/杆改为从图底基线向上绘制并重新发布，电路与数值结果未变。\n\n[完整50项目录](current-delivery-index.md) · [全局交付审计](delivery-audit.json) · [Markdown审计](markdown-table-audit.json)。额度监控已按用户指令停用，无外部模型调用，无PDK/Bridge/Spectre环境改动。\n'
    text+='\n全部50份报告MD已补齐并入库，其中43份从原PDF恢复，201张表8098单元格通过逐格渲染核对；28项系统类案例增加Mermaid框图。第40项ΔΣ频谱已改为log频率轴，并标明20dB/dec理论参照，未改变码流或评分。\n\n[全部报告MD与框图](all-reproduction-markdown.md)。\n'
    (ROOT/'reports/batch-20260929-final-seven.md').write_text(text)
    session=json.loads((ROOT/'current-session.json').read_text());session.update(updated_at=now(),finished_at=now(),newly_delivered_cases=planned,active_case=None,concurrent_case=[],delivered_cases=50,remaining_cases=0,remaining_slots=[],stage='All50 nominal reproductions delivered and visually reviewed;50 editable reports and28 Mermaid system diagrams published; spectrum baseline and delta-sigma log-frequency fixes complete.',documentation_stage='All50 report Markdown files and28 visually reviewed Mermaid diagrams published with verified links and unchanged electrical evidence.',documentation_corrected_cases=[27,30,39,40,46],documentation_delivery_audit='reports/markdown-delivery-audit.json',status='complete',scope_complete=True,current_request_complete=True,full_50_designs_complete=True,no_next_case_started=True,final_batch_report='reports/batch-20260929-final-seven.md',acceptance_counts=dict(counts));write_json(ROOT/'current-session.json',session)
    head=f'''<!-- CURRENT-CONTINUATION -->
2026-09-29最后七项 **05、06、27、28、40、42、48** 全部完成并入库，累计 **50/50**。累计 **{counts['complete_original']}原 / {counts['complete_10pct']}十 / {counts['complete_15pct']}十五**，仅约定TT/nominal范围。本次工作完成，额度监控停用。

[完整交付目录](reports/current-delivery-index.md) · [最后七项汇总](reports/batch-20260929-final-seven.md) · [全部报告MD与框图](reports/all-reproduction-markdown.md) · [机器状态](current-session.json)

全部50份报告MD已补齐，28项系统类案例附Mermaid框图，Markdown表格已核对。27/30/39/46频谱基线及40的log频率轴已更正并重新发布，电路与数值结果未改。
<!-- END-CURRENT-CONTINUATION -->'''
    path=ROOT/'README.md';s=re.sub(r'<!-- CURRENT-CONTINUATION -->.*?<!-- END-CURRENT-CONTINUATION -->',head,path.read_text(),flags=re.S);s=s.replace('工程总目标为全部50项，最后七项续作进行中。','工程全部50项已在约定nominal范围完成。');path.write_text(s)
    (ROOT/'HANDOFF.md').write_text('# 本次任务已完成：50/50\n\n最后七项全部完成、精算核对、完整原理图、PDF逐页实看和知识库发布结束。\n\n[最后七项汇总](reports/batch-20260929-final-seven.md) · [全局交付审计](reports/delivery-audit.json) · [当前目录](reports/current-delivery-index.md)。\n\n仅nominal范围，05为10%档、28为15%档，其余本次五项原指标；累计'+str(dict(counts))+'。MD表格及频谱基线反馈已处理。50份报告MD与28份Mermaid系统图已入库，第40项频谱已改为log频率轴。无进一步仿真或监控任务；不自动扩大到PVT/失配/PEX。知识库修改授权仅本次对话，不改长期AGENTS。\n')
    with (ROOT/'WORKLOG.md').open('a') as f:f.write('\n\n## '+now()+' · 最后七项交付完成\n\n工程50/50完成。05为10%档，28为15%档，06/27/40/42/48原指标；完成同方案精算、独立审查、完整原理图、逐页PDF实看并入库。Markdown表格及27/30/39/46频谱基线修正完成。详见[批次汇总](reports/batch-20260929-final-seven.md)。\n')
    print(json.dumps(dict(delivered=50,remaining=0,counts=dict(counts),new_pdf_pages=sum(x['pdf_pages'] for x in receipts),summary='reports/batch-20260929-final-seven.md'),ensure_ascii=False))

if __name__=='__main__':main()
