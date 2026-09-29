"""Create self-contained module review PDFs from recorded Spectre results."""
from __future__ import annotations
import argparse
import textwrap
import unicodedata
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
from matplotlib.patches import Rectangle, FancyArrowPatch
from module_overviews import overview

FONT=next(p for p in ['/usr/share/fonts/wqy-microhei/wqy-microhei.ttc','/usr/share/fonts/google-droid/DroidSansFallback.ttf','/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc'] if Path(p).is_file())
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=FONT).get_name(),'axes.unicode_minus':False,'pdf.fonttype':42,'font.size':10})
BLUE='#174e73';GRAY='#506273';GREEN='#14775a'

def wrap(s,width=94):
    lines=[];line='';n=0
    for ch in s:
        if ch=='\n':lines.append(line);line='';n=0;continue
        k=2 if unicodedata.east_asian_width(ch) in 'WF' else 1
        if n+k>width:lines.append(line);line='';n=0
        line+=ch;n+=k
    if line:lines.append(line)
    return '\n'.join(lines)

def page(title,number,subtitle):
    fig=plt.figure(figsize=(8.27,11.69),facecolor='white')
    fig.text(.07,.947,title,fontsize=20,color=BLUE,weight='bold',va='top')
    first=number==1
    if first:
        fig._overview_slot=int(re.match(r'^(\d+)',title)[1])
        overview(fig._overview_slot)  # Fail before writing an incomplete first page.
    subtitle_text=fig.text(.07,.886 if first else .909,subtitle,fontsize=9,color=GRAY,va='top')
    line_y=.915 if first else .89
    fig.add_artist(plt.Line2D([.07,.93],[line_y,line_y],transform=fig.transFigure,color=BLUE,lw=1))
    fig.text(.07,.033,'SMIC18MMRF nominal reproduction | Spectre 18.1 | schematic-level',fontsize=8,color=GRAY)
    fig.text(.93,.033,str(number),fontsize=9,color=GRAY,ha='right')
    fig._review_frame_texts=[t for t in fig.texts if not (first and t is subtitle_text)]
    return fig

def para(fig,y,text,size=10,color='#172c3d'):
    fig.text(.07,y,wrap(text),va='top',fontsize=size,color=color,linespacing=1.5)

def table(fig,box,headers,rows,widths=None,fontsize=9):
    ax=fig.add_axes(box);ax.axis('off')
    tb=ax.table(cellText=rows,colLabels=headers,colWidths=widths,cellLoc='left',colLoc='left',bbox=[0,0,1,1])
    tb.auto_set_font_size(False);tb.set_fontsize(fontsize)
    for (r,c),cell in tb.get_celld().items():
        cell.set_edgecolor('#d4dfe7');cell.set_linewidth(.4)
        if r==0:cell.set_facecolor(BLUE);cell.set_text_props(color='white')
        else:cell.set_facecolor('#f1f6f9' if r%2 else 'white')
    return tb

def save(pdf,fig):
    if hasattr(fig,'_overview_slot'):
        # Make room at the beginning while retaining text size and existing page count.
        # Other pages and their measured plots are unchanged.
        scale=.84;anchor=.06
        for t in fig.texts:
            if t not in fig._review_frame_texts:
                x,y=t.get_position();t.set_position((x,anchor+(y-anchor)*scale))
        for ax in fig.axes:
            p=ax.get_position();ax.set_position([p.x0,anchor+(p.y0-anchor)*scale,p.width,p.height*scale])
        fig.text(.07,.892,wrap(overview(fig._overview_slot)),va='top',fontsize=10,color='#172c3d',linespacing=1.5)
    pdf.savefig(fig);plt.close(fig)

def mos(ax,x,y,label,p=False,gateleft=True):
    # D/G/S connectivity is annotated; body ties are specified by exact netlist.
    ax.plot([x,x],[y-.28,y+.28],color=BLUE,lw=2)
    ax.plot([x,x+.17,x+.17],[y+.2,y+.2,y+.48],color=BLUE,lw=1)
    ax.plot([x,x+.17,x+.17],[y-.2,y-.2,y-.48],color=BLUE,lw=1)
    gx=x-.13;ax.plot([gx,gx],[y-.25,y+.25],color=BLUE,lw=1)
    ax.plot([x-.58,gx],[y,y],color=BLUE,lw=1)
    if p:ax.plot(x-.23,y,'o',mfc='white',mec=BLUE,ms=4)
    ax.text(x+.3,y,label,fontsize=9,va='center')
    return x+.17,x-.58

def ota_diagram(ax):
    ax.set(xlim=(-.2,7.8),ylim=(-.8,5.7));ax.axis('off')
    for x,l in [(2,'M3 p18'),(5.4,'M4 p18')]:mos(ax,x,4,l,True)
    for x,l in [(2,'M1 n18'),(5.4,'M2 n18')]:mos(ax,x,2,l)
    mos(ax,3.7,.1,'M5 n18')
    ax.plot([2.17,5.57],[5.1,5.1],color=BLUE)
    for x in [2.17,5.57]:
        ax.plot([x,x],[4.48,5.1],color=BLUE);ax.plot([x,x],[2.48,3.52],color=BLUE)
        ax.plot([x,x],[1.52,1.1],color=BLUE)
    ax.plot([2.17,5.57],[1.1,1.1],color=BLUE);ax.plot([3.87,3.87],[.58,1.1],color=BLUE)
    ax.plot([3.87,3.87],[-.38,-.65],color=BLUE)
    ax.plot([2.17,1.1,1.1,1.42],[3.1,3.1,4,4],color=BLUE)
    ax.plot([1.1,1.1,4.82],[4,4.75,4.75],color=BLUE)
    ax.plot([4.82,4.82],[4.75,4],color=BLUE)
    ax.text(3.8,5.25,'VDD = 1.8 V',ha='center',fontsize=10)
    ax.text(1.35,2,'vinp',ha='right',va='center',fontsize=10)
    ax.text(4.75,2,'vinn',ha='right',va='center',fontsize=10)
    ax.plot([5.57,6.8],[3.1,3.1],color=BLUE);ax.text(6.85,3.1,'vout',va='center',fontsize=10)
    ax.text(3.87,-.77,'VSS',ha='center',fontsize=9)
    ax.text(.05,.1,'ibias = 50 uA\nM6 diode replica',fontsize=9,va='center')
    ax.plot([1.8,3.12],[.1,.1],color=BLUE)
    ax.text(2.2,1.15,'tail',fontsize=8)
    ax.text(2.35,3.06,'nleft',fontsize=8)

def make16():
    case=ROOT/'cases/16-miller';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());runs=[ROOT/x for x in r['run_dirs']]
    a=data(runs[0],'ac.ac');dcscan=data(runs[0],'swing.dc');n=data(runs[1],'noise.noise',required=('in','out'));d=data(runs[2],'tran.tran');v=r['values'];out=ROOT/'reports/16-miller-review.pdf';f=a['freq'];loop=-a['voutl']/a['vinnl']
    with PdfPages(out,metadata={'Title':'16 SMIC18 两级Miller运放审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('16 | 两级 Miller 运放审查',1,'结论：10%放宽条件通过；仅UGB较原200 MHz低0.52%，其余原指标通过。')
        para(fig,.862,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；外部参考50 uA；输入共模0.9 V；负载1 pF。记录全部nominal频域、动态与范围指标，不以单一环路增益代替完整验收。')
        info=[('10Hz环路增益','gain_db',1,'dB'),('UGB','ugb_hz',1e-6,'MHz'),('相位裕量','phase_margin_deg',1,'deg'),('静态输出误差','output_error_V',1e3,'mV'),('总功耗（含参考）','power_W',1e3,'mW'),('输入积分噪声','input_noise_Vrms',1e6,'uVrms'),('闭环PSRR+ @1kHz','psrr_1k_dB',1,'dB'),('闭环PSRR+ @1MHz','psrr_1m_dB',1,'dB'),('闭环CMRR @1kHz','cmrr_1k_dB',1,'dB'),('连续输出范围','output_range_Vpp',1,'Vpp'),('最坏建立时间','settling_s',1e9,'ns'),('最坏最终跟踪误差','settling_error_V',1e3,'mV'),('上升压摆率','slew_rise_V_per_us',1,'V/us'),('下降压摆率','slew_fall_V_per_us',1,'V/us')]
        rows=[]
        for label,key,scale,unit in info:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([label,f"{g['value']*scale:.3f}",f"{sign}{g['limits']['original']*scale:.3f}",f"{sign}{g['limits']['10pct']*scale:.3f}",f"{sign}{g['limits']['15pct']*scale:.3f}",unit])
        tb=table(fig,[.07,.26,.86,.52],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.14,.14,.14,.14,.13],8.3)
        for j in range(6):tb[(2,j)].set_facecolor('#fff1d5')
        para(fig,.219,'噪声增益20的实测−3 dB带宽14.098 MHz，积分10 Hz至该频率，得到22.500 uVrms。环路在10 Hz–10 GHz内只有一次下降跨越0 dB，之后没有回穿。',9.5)
        para(fig,.115,'最终100 mV阶跃跟踪误差1.201 mV，等于阶跃幅度的1.201%，同时满足2 mV与2%两个原条件。未以放宽后的噪声带宽或负载制造通过。',9)
        save(pdf,fig)
        fig=page('电路结构、LUT尺寸与OP',2,'两级电压放大，电流偏置，串联RC跨级补偿。')
        ax=fig.add_axes([.07,.68,.86,.185]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3.5))
        for x,y,w,h,label in [(1,1.45,3.2,1.2,'NMOS差分对\nPMOS镜负载'),(6,1.45,3.2,1.2,'NMOS共源\nPMOS电流源')]:ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor=BLUE));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10)
        ax.annotate('',xy=(1,2),xytext=(.1,2),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(.1,2.85,'VIN±',fontsize=9)
        ax.annotate('',xy=(6,2),xytext=(4.2,2),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(4.35,2.35,'stage1',fontsize=9)
        ax.annotate('',xy=(9.95,2),xytext=(9.2,2),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(9.25,2.85,'VOUT',fontsize=9)
        ax.plot([4.9,4.9,6],[2,.55,.55],color=BLUE);ax.plot([8.9,9.5,9.5],[.55,.55,2],color=BLUE)
        ax.add_patch(Rectangle((6,.1),2.9,.9,fill=False,edgecolor=GREEN));ax.text(7.45,.55,'RZ 1.5 kΩ + CC 0.7 pF',ha='center',va='center',fontsize=8.5)
        rows=[]
        for key,label,multi in [('input','MINN/MINP','1'),('mirror_load','MPD/MPM','1'),('n_bias_unit','MREF/MTAIL/MBN','5 / 14 / 5'),('p_bias_unit','MBP/MLOAD','1 / 12'),('second','MSECOND','1')]:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['L_um']:.2f}",f"{q['rounded_W_um']:.2f}",multi,f"{q['gmid']:.1f}"])
        table(fig,[.07,.458,.86,.18],['器件角色','模型','L/um','单位W/um','m','目标gm/ID'],rows,[.28,.12,.11,.15,.19,.15],8.5)
        rows=[]
        for key in ['MINP','MINN','MPM','MTAIL','MSECOND','MLOAD']:
            q=r['operating_point'][key];rows.append([key,f"{abs(q['ids'])*1e6:.2f}",f"{q['gmid']:.2f}",f"{q['gmro']:.1f}",f"{q['headroom_V']:.3f}"])
        table(fig,[.07,.208,.86,.205],['实际工作点','|I|/uA','gm/ID','gm/gds','饱和余量/V'],rows,[.26,.19,.18,.18,.19],9)
        para(fig,.163,'输入对约69 uA/支，第二级623.9 uA。第二级gm约3.046 mS，1/gm约328 Ω；RZ大于此值，用于形成左半平面零点。完整相位仍由实际环路验证。',9.5)
        para(fig,.084,'尾源、参考、输出负载用单位管并联；模型日志无尺寸越界警告。没有新增数字逻辑。',9)
        save(pdf,fig)
        fig=page('环路、抑制比与噪声',3,'闭环噪声频带由独立AC测得；抑制比保持上游闭环注入方式。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.2,top=.845,hspace=.38,wspace=.37)
        axs[0,0].semilogx(f,20*np.log10(abs(loop)),color=BLUE);axs[0,0].axhline(0,color=GRAY,lw=.7);axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Loop gain (dB)')
        axs[0,1].semilogx(f,np.unwrap(np.angle(loop))*180/np.pi,color=BLUE);axs[0,1].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Loop phase (deg)')
        axs[1,0].loglog(n['freq'],abs(n['in'])*1e9,color=BLUE);axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Input noise (nV/sqrt(Hz))')
        axs[1,1].semilogx(f,-20*np.log10(abs(a['voutp'])),label='PSRR+');axs[1,1].semilogx(f,-20*np.log10(abs(a['voutc'])),label='CMRR');axs[1,1].set(xlabel='Frequency (Hz)',ylabel='Closed-loop rejection (dB)',xlim=(1e3,1e7));axs[1,1].legend(fontsize=8)
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.148,'环路采用原测试串联电压注入，T=−Vout/Vinn；DC保持单位反馈。PSRR输入固定、VDD AC=1；CMRR对vinp与串联反馈各注入同一AC单位，抑制比均为−20log10|Vout|。',9)
        para(fig,.08,'输入噪声为PSF的V/sqrt(Hz)，平方后对频率积分再开根号。没有用开环UGB作为积分终点。',9)
        save(pdf,fig)
        fig=page('阶跃、压摆与连续范围',4,'负载始终1 pF；同时验收正负两个方向，DC范围须围绕0.9 V连续。')
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.13,right=.94,bottom=.155,top=.845,hspace=.41)
        for k,l in [('vinS','Input'),('outS','Output')]:axs[0].plot(d['time']*1e9,d[k],label=l,lw=1)
        axs[0].set(xlim=(0,130),xlabel='Time (ns)',ylabel='Voltage (V)',title='0.85 V ↔ 0.95 V');axs[0].legend(fontsize=8,ncol=2)
        for k,l in [('vinR','Input'),('outR','Output')]:axs[1].plot(d['time']*1e9,d[k],label=l,lw=1)
        axs[1].set(xlim=(10,225),xlabel='Time (ns)',ylabel='Voltage (V)',title='0.65 V ↔ 1.15 V; slew measured 0.75–1.05 V');axs[1].legend(fontsize=8,ncol=2)
        axs[2].plot(dcscan['sweepin'],abs(dcscan['vouts']-dcscan['vinps'])*1e3,color=BLUE);axs[2].axhline(20,color=GRAY,ls='--');axs[2].axvspan(v['output_range_boundaries']['low'],v['output_range_boundaries']['high'],color=GREEN,alpha=.1)
        axs[2].set(ylim=(0,80),xlabel='Input / requested output (V)',ylabel='Tracking error (mV)',title='Contiguous DC tracking range')
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.11,'输出连续范围0.300–1.386 V，共1.086 Vpp；低端受原扫描0.3 V边界限制，未声称0.3 V以下可用。建立时间从5/66 ns阶跃开始到最后进入2 mV误差窗，终值分别在65/130 ns检查。',9)
        save(pdf,fig)
        fig=page('精确电路、权衡与复现',5,'一次第二级gm/ID调整同时改变速度、相位与输入失调。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.85,body,fontsize=8.1,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.5)
        para(fig,.567,'初版第二级gm/ID=3时UGB150.90 MHz，低于15%放宽后的170 MHz下限。保持电流、补偿和其他尺寸，仅改到gm/ID=5，UGB升至198.96 MHz、PM由57.49°升至71.34°。输出静态误差从0.127增至1.165 mV，仍满足动态终值要求。',9.5)
        para(fig,.42,'原因：第二级跨导增大、输出极点与补偿零点改变；其栅压从约0.991降到0.790 V，输入对漏压不再接近相等。因此速度提升同时增加系统失调并降低CMRR，必须联合验收，不能只看UGB。',9.5)
        para(fig,.293,'复现：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case16_miller.py\n生成PDF：同一Python运行 scripts/review_pdf.py 16',8.8)
        para(fig,.21,'静态：'+r['run_dirs'][0]+'\n噪声：'+r['run_dirs'][1]+'\n动态：'+r['run_dirs'][2],8.3)
        para(fig,.1,'原任务：sky130-two-stage-miller-opamp-gain60-ugb200-pm60-noise50uv-pvt。未执行其余PVT点、另外两个代表性动态角落、失配或版图验证。198.96 MHz必须保留10%放宽通过标签。',9)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=5,render_review_pending=True))
    update_case(16,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

def make12():
    case=ROOT/'cases/12-beta';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());runs=[ROOT/x for x in r['run_dirs']]
    c=data(runs[0],'compliance.dc');ds=[data(x,'tran.tran') for x in runs[1:]];v=r['values'];out=ROOT/'reports/12-beta-review.pdf'
    with PdfPages(out,metadata={'Title':'12 SMIC18 beta倍增基准审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('12 | β 倍增基准审查报告',1,'结论：原nominal电流、端口功耗、全输出范围和两种冷启动均通过。')
        para(fig,.863,f"条件：SMIC18MMRF / tt + res_tt / 1.8 V / 27°C。无外部偏置；Iout固定0.9 V时，电流{v['output_current_A']*1e6:.4f} uA，Vref={v['vref_V']:.6f} V，含输出端口的总功耗{v['power_W']*1e6:.3f} uW。")
        labels=[('电流偏离40uA','current_error_A',1e6,'uA'),('Vref偏离0.675V','vref_error_V',1,'V'),('总电气功耗','power_W',1e6,'uW'),('输出范围pp/mean','compliance_flatness',100,'%'),('启动最终I偏离40uA','startup_current_error_A',1e6,'uA'),('启动Vref偏离0.675V','startup_vref_error_V',1,'V'),('斜坡结束后建立','startup_settling_s',1e6,'us'),('输出电流峰值/最终','startup_overshoot',1,'倍'),('峰值正向VDD电流','startup_peak_current_A',1e6,'uA'),('正向VDD能量','startup_energy_J',1e9,'nJ')]
        rows=[]
        for name,key,scale,unit in labels:
            g=r['gates'][key];rows.append([name,f"{g['value']*scale:.4f}",f"≤{g['limits']['original']*scale:.3f}",f"≤{g['limits']['10pct']*scale:.3f}",f"≤{g['limits']['15pct']*scale:.3f}",unit])
        table(fig,[.07,.417,.86,.35],['最坏指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.15,.145,.145,.145,.105],8.2)
        rows=[]
        for z in v['startup']:rows.append([f"{z['ramp_s']*1e6:.0f}",f"{z['final_current_A']*1e6:.4f}",f"{z['overshoot_ratio']:.4f}",f"{z['peak_supply_current_A']*1e6:.3f}",f"{z['positive_vdd_energy_J']*1e9:.4f}"])
        table(fig,[.07,.25,.86,.105],['斜坡/us','最终I/uA','峰值/最终','峰值IVDD/uA','能量/nJ'],rows,[.16,.22,.20,.23,.19],9)
        para(fig,.209,'建立时间0表示在斜坡结束时已进入并持续留在最终电流±10%窗口，并非电路瞬时启动。输出每5 ns记录，内部最大步长2 ns；初始VDD和Vref均为0。',9.5)
        para(fig,.099,'仅nominal范围；未执行27点PVT矩阵、其他供电/温度启动组合、50次MC、版图或可靠性签核。',9)
        save(pdf,fig)
        fig=page('自偏置环、尺寸与启动支路',2,'目标gm/ID来自目标工艺；L=4 um与窄PMOS的缺失表已补充。')
        ax=fig.add_axes([.07,.605,.86,.27]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,6))
        for x,label in [(2,'MP1'),(6,'MP2')]:mos(ax,x,4.2,label,True)
        mos(ax,2,2.1,'MN2 ×4');mos(ax,6,2.1,'MN1')
        ax.plot([2.17,6.17],[5.25,5.25],color=BLUE)
        for x in [2.17,6.17]:ax.plot([x,x],[4.68,5.25],color=BLUE);ax.plot([x,x],[2.58,3.72],color=BLUE)
        ax.plot([2.17,1.1,1.1,1.42],[3.2,3.2,4.2,4.2],color=BLUE)
        ax.plot([1.1,1.1,5.42,5.42],[4.2,4.93,4.93,4.2],color=BLUE)
        ax.plot([6.17,5,5,5.42],[3.15,3.15,2.1,2.1],color=BLUE)
        ax.plot([5,5,1.42,1.42],[2.1,1.4,1.4,2.1],color=BLUE)
        ax.plot([6.17,6.17],[1.62,.3],color=BLUE)
        ax.plot([2.17,2.17],[1.62,1.1],color=BLUE);ax.add_patch(Rectangle((1.98,.55),.38,.55,fill=False,edgecolor=BLUE));ax.plot([2.17,2.17],[.3,.55],color=BLUE)
        ax.plot([2.17,6.17],[.3,.3],color=BLUE)
        ax.text(4.2,5.5,'VDD',ha='center',fontsize=9);ax.text(4.2,0,'VSS',ha='center',fontsize=9)
        ax.text(.6,3.15,'na',fontsize=9);ax.text(6.45,3.15,'Vref → MOUT ×4',fontsize=9)
        ax.text(2.55,.8,'RGM：11.850 kΩ',fontsize=9)
        ax.text(7.6,4.8,'启动：\nMPUP → nx\nMDET检测Vref\nMSTART下拉na',fontsize=8.5,va='top')
        rows=[]
        for key,label,multi in [('n_unit','MN1 / MN2 / MOUT','1 / 4 / 4'),('p_mirror','MP1 / MP2','1'),('startup_pullup','MPUP','1'),('startup_detect','MDET','1'),('startup_inject','MSTART','1')]:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['L_um']:.1f}",f"{q['rounded_W_um']:.2f}",multi,f"{q['gmid']:.3f}"])
        table(fig,[.07,.376,.86,.185],['角色','模型','L/um','W/um','m','目标gm/ID'],rows,[.31,.11,.10,.13,.17,.18],8.5)
        para(fig,.341,'长沟道NMOS取gm/ID=7、10 uA，预测VGS约0.657 V；实际MN1为9.742 uA、gm/ID=7.021。MN2的源极电阻和4:1尺寸比形成非零自偏置，体效应与PMOS镜的VDS差由实际OP处理。',9.5)
        para(fig,.224,'RGM使用PDK的rpposab_3t，W=1 um、L=36 um，第三端接VSS；实际11.850 kΩ。采用模型的片阻、蚀刻、温度、电压系数与基底电容，没有用理想R替换原任务的工艺电阻。',9.5)
        para(fig,.112,'MPUP栅接VSS，属于全摆幅强反型弱电流支路；补扫W=0.24 um/L=4 um、VSD=1.8 V表，以gm/ID=1.278选3 uA。实际3.072 uA；不能用普通gm/ID=8点外推这个偏置。',9.5)
        save(pdf,fig)
        fig=page('冷启动与输出电压范围',3,'全部曲线来自最终网表；从0 V自然上电，没有指定非零初始节点。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.195,top=.845,hspace=.4,wspace=.38)
        for ax,d,z in zip(axs[0],ds,v['startup']):
            ax.plot(d['time']*1e6,-d['VOUT:p']*1e6,color=BLUE);ax.axvline(z['ramp_s']*1e6,color=GRAY,ls='--',lw=.8)
            ax.axhspan(.9*z['final_current_A']*1e6,1.1*z['final_current_A']*1e6,color=GREEN,alpha=.10);ax.set(xlabel='Time (us)',ylabel='Output current (uA)',title=f"{z['ramp_s']*1e6:.0f} us supply ramp")
        axs[1,0].plot(c['vtest'],-c['VOUT:p']*1e6,color=BLUE);axs[1,0].set(xlabel='Output voltage (V)',ylabel='Sink current (uA)',title='121-point compliance')
        d=ds[0];axs[1,1].plot(d['time']*1e6,d['vref'],label='Vref');axs[1,1].plot(d['time']*1e6,d['XDUT.nx'],label='Startup nx');axs[1,1].set(xlim=(0,3),xlabel='Time (us)',ylabel='Voltage (V)',title='Startup injection turns off');axs[1,1].legend(fontsize=8)
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.146,'MDET在Vref上升后把nx压到29.86 mV，MSTART最终电流约3.3 pA；MPUP/MDET仍保留约3.072 uA静态电流。报告的75.53 uW已计入它，不能把“注入关闭”描述成“整个启动支路零功耗”。',9)
        para(fig,.084,'输出0.4–1.6 V时Iout为38.637–39.662 uA；以峰峰值/均值计算平坦度2.613%。',9)
        save(pdf,fig)
        fig=page('精确电路与复现依据',4,'最终网表、LUT查询、PDK电阻模型和全部运行快照可追溯。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.848,body,fontsize=8.2,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.55)
        para(fig,.586,'功耗：max(0,−1.8·I(VDD)) + 0.9·Iout。启动能量只按原测试定义积分正向VDD功率，从0到斜坡结束后10 us；最终电流用最后1 us平均。建立时间从斜坡结束起算，要求之后所有样点持续在±10%窗口。',9.5)
        para(fig,.465,'第一版RGM长度38.5 um时输出34.744 uA，原35 uA下限略未达到，但在10%误差放宽内。把长度改为36 um后输出39.163 uA，达到原指标。最终另补全摆幅窄PMOS LUT，使启动支路尺寸依据对应真实工作区。',9.5)
        para(fig,.331,'复现：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case12_beta.py\n生成PDF：同一Python运行 scripts/review_pdf.py 12\n补充表：lut_supplement/tt；每表metadata保存表征运行路径。',8.8)
        para(fig,.222,'DC/compliance：'+r['run_dirs'][0]+'\n1 us启动：'+r['run_dirs'][1]+'\n10 us启动：'+r['run_dirs'][2]+'\n各run.json包含模型哈希与模型尺寸检查；当前无尺寸越界警告。',8.3)
        para(fig,.107,'原任务：sky130-beta-multiplier-reference-pvt-mc。此报告只证明指定nominal功能，不把自偏置、长沟道或低功耗等结构特征当作跨PVT和失配通过的证据。',9)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(12,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

def make02():
    case=ROOT/'cases/02-mirror';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());run=ROOT/r['run_dir']
    c=data(run,'compliance.dc');v=r['values'];out=ROOT/'reports/02-mirror-review.pdf'
    with PdfPages(out,metadata={'Title':'02 SMIC18 可编程电流镜审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('02 | 可编程电流镜审查报告',1,'结论：四个控制码、参考扰动及完整输出范围均通过原nominal指标。')
        para(fig,.864,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；ICC、IPTAT各50 uA；输出电压名义0.9 V。代码改变两个参考的贡献比例，名义总目标始终为1 mA。')
        specs=[('输出电流误差','output_error',100,'%'),('独立权重误差','weight_error',100,'%'),('贡献比例误差','ratio_error',100,'%'),('参考扰动耦合','isolation_perturbation_V',1e3,'mV'),('切码参考偏移','isolation_code_V',1e3,'mV'),('辅助VDD电流','auxiliary_current_A',1e6,'uA'),('数字引脚电流','digital_current_A',1e6,'uA'),('输出全范围变化','compliance_error',100,'%'),('最小输出电阻','rout_Ohm',1e-3,'kΩ')]
        rows=[]
        for label,key,scale,unit in specs:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤'
            rows.append([label,f"{g['value']*scale:.4f}",f"{sign}{g['limits']['original']*scale:.3f}",f"{sign}{g['limits']['10pct']*scale:.3f}",f"{sign}{g['limits']['15pct']*scale:.3f}",unit])
        table(fig,[.07,.467,.86,.316],['最坏指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.26,.17,.15,.15,.15,.12],8.3)
        rows=[]
        for p,(wi,wp) in zip(r['points'],s['weight_pairs']):
            rows.append([p['code'],f'{wi} / {wp}',f"{p['iout_A']*1e6:.3f}",f"{p['acc']:.4f}",f"{p['aptat']:.4f}"])
        table(fig,[.07,.239,.86,.163],['控制码','目标ACC/APTAT','Iout/uA','ACC实测','APTAT实测'],rows,[.13,.28,.20,.195,.195],9)
        para(fig,.192,'两参考引脚在名义及±5 uA独立扰动下均为0.47885–0.49117 V，满足0.20–1.10 V；所有输出电流均为正。隔离/数字电流的零值是本次模型和数值精度下的结果，不表示真实器件不存在漏电。',9.5)
        para(fig,.088,'辅助VDD电流已扣除两个强制参考电流；输出由外部电压源供电，不计入DUT辅助支路。',9)
        save(pdf,fig)
        fig=page('结构、gm/ID与实际工作点',2,'电流镜使用相同W/L单元复制；译码只用未修改的HD标准单元。')
        ax=fig.add_axes([.07,.63,.86,.235]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,4))
        boxes=[(.1,2.45,2,1.1,'ICC / IPTAT\n二极管参考'),(3,1.7,3.2,1.3,'四组权重镜支路\n(16,4) … (4,16)'),(3,.1,3.2,.9,'HD译码\n2×IN + 4×NOR'),(7.1,1.7,2.8,1.3,'选择开关\n共享共栅管')]
        for x,y,w,h,label in boxes:ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor=BLUE));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=9)
        for xy1,xy2 in [((2.1,3),(3,2.5)),((6.2,2.35),(7.1,2.35)),((6.2,.55),(8.5,1.7)),((8.5,3),(8.5,3.9))]:ax.annotate('',xy=xy2,xytext=xy1,arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.text(8.1,3.72,'IOUT',fontsize=9);ax.text(.2,.45,'b1:b0 →',fontsize=9)
        rows=[['参考与各镜单元','n18','1.00','34.78','1 / 4 / 8 / 12 / 16','16'],['输出共栅单元','n18','0.36','2.12','200','18'],['共栅偏置复制','n18','0.36','2.12','1','18'],['模拟选择开关','n18','0.18','32.84','1','8（初值）']]
        table(fig,[.07,.427,.86,.16],['角色','模型','L/um','单位W/um','m','LUT gm/ID'],rows,[.26,.11,.11,.13,.23,.16],8.5)
        para(fig,.395,'偏置支路：VDD经210 kΩ到共栅栅压，二极管n18下端经50 kΩ到VSS；实测偏置电流4.815 uA。共栅与偏置管使用同一2.12/0.36 um单元，输出m=200。所有单实例宽度均在PDK的100 um上限内。',9.5)
        q=r['operating_point']['0'];rows=[]
        for key,label in [('MICC','参考'),('MIC0','ICC权重16'),('MCASC','共栅'),('MSW0','选择开关')]:
            z=q[key];rows.append([label,f"{z['ids']*1e6:.3f}",f"{z['gmid']:.2f}",f"{z['vds']:.4f}",f"{z['vdsat']:.4f}",str(int(z['region']))])
        table(fig,[.07,.18,.86,.16],['00码实际OP','I/uA','gm/ID','VDS/V','VDSAT/V','region'],rows,[.24,.18,.16,.16,.16,.10],8.5)
        para(fig,.135,f"模拟开关有意工作在线性区，实测Ron约{q['MSW0']['Ron_Ohm']:.2f} Ω；不能要求它保持饱和。gm/ID用于给出初始宽度，实际导通压降与完整外部合同共同确认尺寸。",9.5)
        save(pdf,fig)
        fig=page('全范围电流与独立权重',3,'每码41个均匀电压点，含0.45 V与1.60 V；权重使用±5 uA中心差分。')
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.13,right=.94,bottom=.165,top=.845,hspace=.43)
        for code,p in enumerate(r['points']):
            current=-c[f'VO_c{code}_nom:p'];axs[0].plot(c['vtest'],current*1e6,label=p['code'],lw=1.2);axs[1].plot(c['vtest'],100*(current/p['iout_A']-1),label=p['code'],lw=1.2)
        axs[0].legend(ncol=4,fontsize=8);axs[0].set(xlabel='Output voltage (V)',ylabel='Iout (uA)');axs[1].set(xlabel='Output voltage (V)',ylabel='Deviation from 0.9V (%)')
        x=np.arange(4);axs[2].bar(x-.18,[p['acc'] for p in r['points']],.34,label='Measured ICC');axs[2].bar(x+.18,[p['aptat'] for p in r['points']],.34,label='Measured IPTAT')
        axs[2].plot(x-.18,[p[0] for p in s['weight_pairs']],'k_',ms=13,label='Target');axs[2].plot(x+.18,[p[1] for p in s['weight_pairs']],'k_',ms=13)
        axs[2].set(xticks=x,xticklabels=['00','01','10','11'],xlabel='Ratio code',ylabel='Partial current gain');axs[2].legend(fontsize=8,ncol=3)
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.117,'四条名义电流曲线几乎重合，这是相同单元复制与互补总权重20的结果。输出电阻按0.895/0.905 V中心差分，不以全范围斜率替代局部输出电阻。',9)
        save(pdf,fig)
        fig=page('精确连接与复现路径',4,'内核没有独立源、受控源或理想开关；HD内部器件尺寸保留原库。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.858,body,fontsize=7.4,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.35)
        para(fig,.373,'早期宽度直接乘权重的版本曾触发CMI-2441尺寸越界，已撤回。最终采用同尺寸单元的m复制，日志无该警告。gm/ID文件哈希、HD原CDL哈希、完整单元网表、测试台与模型哈希均随运行保存。',9)
        para(fig,.255,'复现：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case02_mirror.py\n生成PDF：同一Python运行 scripts/review_pdf.py 2\n运行：'+r['run_dir'],8.5)
        para(fig,.142,'范围：SMIC18 tt / 27°C / 1.8 V。保留四码、参考独立扰动、参考端口约束和输出电压范围；没有复现原任务另外两个配对PVT点，也没有验证切码瞬态、噪声、失配或版图。',9)
        para(fig,.071,'原任务：sky130-programmable-icc-iptat-current-mirror-pvt',8.5)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(2,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

def make04():
    case=ROOT/'cases/04-gmr';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());run=ROOT/r['run_dir']
    a=data(run,'ac.ac');d=data(run,'tran.tran');v=r['values'];out=ROOT/'reports/04-gmr-review.pdf'
    f=a['freq'];gain=abs(a['vop']-a['von'])
    sel=(d['time']>=.5e-6-1e-15)&(d['time']<=1.5e-6+1e-15)
    t=d['time'][sel];y=(d['vop']-d['von'])[sel]
    basis=np.column_stack([np.ones(len(t)),np.sin(2*np.pi*3e6*t),np.cos(2*np.pi*3e6*t)])
    fit=basis@np.linalg.lstsq(basis,y,rcond=None)[0]
    with PdfPages(out,metadata={'Title':'04 SMIC18 GM-R 放大器审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('04 | GM-R 放大器审查报告',1,'结论：全部 nominal 原始指标通过；无需10%–15%放宽。2026-09-22')
        para(fig,.863,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；输入共模0.9 V；每个输出各接1 pF；外部参考50 uA。源极退化差分对加电阻负载，核心只使用MOS与正值电阻。')
        rows=[]
        for label,key,scale,unit in [('AC增益偏离2','gain_error',1,'V/V'),('上端−3dB带宽','bandwidth_Hz',1e-6,'MHz'),('总功耗（含参考）','power_W',1e3,'mW'),('3MHz SDR','SDR_dB',1,'dB'),('基波增益偏离2','fundamental_gain_error',1,'V/V')]:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤'
            rows.append([label,f"{g['value']*scale:.4f}",f"{sign}{g['limits']['original']*scale:.4f}",f"{sign}{g['limits']['10pct']*scale:.4f}",f"{sign}{g['limits']['15pct']*scale:.4f}",unit])
        table(fig,[.07,.595,.86,.19],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.15,.15,.15,.15,.11],8.5)
        para(fig,.556,f"AC差分增益@1 MHz = {v['gain_1MHz']:.6f} V/V；3 MHz正弦基波增益 = {v['fundamental_gain']:.6f} V/V。输入为100 mV差分峰值，不能通过减小振幅改善SDR。增益容差围绕目标2扩大，目标值保持2。")
        ax=fig.add_axes([.07,.12,.86,.35]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,6.2))
        ax.plot([1.5,8.1],[5.9,5.9],color=BLUE);ax.text(4.8,6.0,'VDD = 1.8 V',ha='center',fontsize=9)
        for x,gate,outname in [(2.4,'VIN','VON'),(6.8,'VIP','VOP')]:
            xx=x+.17
            ax.add_patch(Rectangle((xx-.15,4.65),.30,.65,fill=False,edgecolor=BLUE))
            ax.plot([xx,xx],[5.3,5.9],color=BLUE);ax.plot([xx,xx],[3.48,4.65],color=BLUE)
            ax.text(xx+.3,5,'RL = 1989 Ω',fontsize=9,va='center')
            mos(ax,x,3,'n18');ax.text(x-.62,3,gate,ha='right',va='center',fontsize=9)
            ax.plot([xx,xx+.8],[4.1,4.1],color=BLUE);ax.text(xx+.85,4.1,outname,fontsize=9,va='center')
            ax.add_patch(Rectangle((xx-.15,1.4),.30,.65,fill=False,edgecolor=BLUE))
            ax.plot([xx,xx],[2.05,2.52],color=BLUE);ax.plot([xx,xx],[1.05,1.4],color=BLUE)
            ax.text(xx+.3,1.72,'RS = 600 Ω',fontsize=9,va='center')
        ax.plot([2.57,6.97],[1.05,1.05],color=BLUE)
        ax.add_patch(Rectangle((3.5,.05),2.6,.75,fill=False,edgecolor=BLUE));ax.text(4.8,.42,f"MTAIL：{r['operating_point']['MTAIL']['ids']*1e6:.2f} uA",ha='center',va='center',fontsize=9)
        ax.plot([4.8,4.8],[.8,1.05],color=BLUE)
        para(fig,.09,'MREF二极管连接，从IREF生成尾管栅压；图中省略体端与参考支路，精确端序见第4页。VCM端口保留，DUT内部不使用。',9)
        save(pdf,fig)
        fig=page('gm/ID尺寸与体效应',2,'LUT给出初值，实际工作点决定退化跨导和余量。')
        rows=[]
        for role,label in [('input','MINN/MINP'),('tail','MTAIL'),('reference','MREF')]:
            q=s['roles'][role];width=f"{q['rounded_W_um']:.2f}" if role!='tail' else '34.78 ×10'
            rows.append([label,f"{q['L_um']:.2f}",width,f"{q['gmid']:.1f}",f"{q['Id_A']*1e6:.1f}",f"{q['lut_metadata']['vds_V']:.2f}"])
        table(fig,[.07,.71,.86,.14],['n18器件','L/um','W/um','gm/ID','目标I/uA','LUT VDS/V'],rows,[.25,.13,.15,.14,.17,.16],9)
        rows=[]
        for name,q in r['operating_point'].items():
            rows.append([name,f"{q['ids']*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['vds']:.4f}",f"{q['vdsat']:.4f}",f"{q['headroom_V']:.4f}"])
        table(fig,[.07,.535,.86,.115],['实际器件','I/uA','gm/ID','VDS/V','VDSAT/V','余量/V'],rows,[.22,.16,.15,.15,.16,.16],9)
        para(fig,.49,'输入管gm=4.419 mS、gmb=1.073 mS，体效应占gm约24%。带退化且忽略ro时，gm_eff≈gm/[1+(gm+gmb)RS]；不能只用gm/(1+gm·RS)。负载与输出电容构成主极点，增大RL提高增益，同时压低带宽。')
        para(fig,.335,'输入管实际源压0.3285 V，LUT采用零体偏置；尾节点0.1837 V，尾管VDS−VDSAT约81 mV。输入实际gm/ID=18.31，尾管16.14。记录体偏置与有限ro的误差，避免把LUT查询值直接当成完整电路工作点。')
        para(fig,.19,'尾管由10个W=34.78 um、L=1 um的参考单元并联，避免超过PDK的单实例W≤100 um范围。实际尾电流482.70 uA，输出共模1.3200 V。旧版W=347.8 um单管结果已撤回；最终运行没有模型尺寸越界警告。')
        para(fig,.09,'所有LUT文件路径、SHA-256、目标点和单元并联信息保存在sizing.json。模型范围检查已成为后续每次运行的门槛；本结果不外推到PVT。',9)
        save(pdf,fig)
        fig=page('频响、正弦与残差证据',3,'SDR按上游正弦拟合定义；1001个等间隔采样点，0.5–1.5 us。')
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.13,right=.94,bottom=.165,top=.845,hspace=.42)
        axs[0].semilogx(f,gain,color=BLUE);axs[0].axhline(v['gain_1MHz']/np.sqrt(2),color=GRAY,ls='--',lw=.8);axs[0].axvline(v['bandwidth_Hz'],color=GREEN,ls='--',lw=.8)
        axs[0].set(xlim=(1e5,1e10),xlabel='Frequency (Hz)',ylabel='Differential gain (V/V)')
        axs[1].plot(t*1e6,y*1e3,color=BLUE,label='Output');axs[1].plot(t*1e6,fit*1e3,color=GREEN,ls='--',label='Sine fit');axs[1].legend(fontsize=8)
        axs[1].set(xlim=(.5,1.5),xlabel='Time (us)',ylabel='VOP - VON (mV)')
        axs[2].plot(t*1e6,(y-fit)*1e6,color=BLUE);axs[2].set(xlim=(.5,1.5),xlabel='Time (us)',ylabel='Fit residual (uV)')
        for ax in axs:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.119,f"SDR=10log10[(a²+b²)/2 / mean(residual²)]；拟合含DC、sin与cos项。残差RMS={v['fit_residual_rms_V']*1e6:.3f} uV。此值是指定振幅/频率下的失真比，不包含随机噪声，也不等同于噪声动态范围。",9)
        save(pdf,fig)
        fig=page('精确电路、迭代与复现',4,'宽度和电阻均来自最终通过的输入快照；没有修改PDK或Bridge。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.85,body,fontsize=8.6,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.55)
        hist=[]
        for p in sorted((ROOT/'runs/04').glob('*_gmr/measurements.json')):
            rr=json.loads(p.read_text());ss=json.loads((p.parent/'inputs/sizing.json').read_text());vv=rr['values']
            hist.append([f"{ss['load_resistance_ohm']:.0f}",f"{vv['gain_1MHz']:.5f}",f"{vv['bandwidth_Hz']/1e6:.3f}",f"{vv['SDR_dB']:.3f}",'并联管通过' if 'implementation' in ss else '尺寸越界撤回'])
        table(fig,[.07,.49,.86,.13],['RL/Ω','1MHz增益','带宽/MHz','SDR/dB','结果'],hist,[.15,.21,.20,.19,.25],8.5)
        para(fig,.452,'功耗按VDD、VCM、VIN、VIP四个DC端口的|V·I|求和，参考电流取自VDD。AC差分激励1 V；瞬态每侧50 mV、反相3 MHz；CL每侧1 pF。先修正RL，再将尾管改为范围内的并联单元完成最终验证。',9.5)
        para(fig,.332,'复现：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case04_gmr.py\n生成PDF：同一Python运行 scripts/review_pdf.py 4\n运行：'+r['run_dir'],8.8)
        para(fig,.217,'原任务：sky130-gmr-degenerated-diff-amp-gain2-bw70m-power1p2mw-sdr60。原始5个工艺角在本次任务中缩为SMIC18 tt。没有执行额外温度、供电、失配或版图寄生验证。',9)
        para(fig,.11,'PSF解析说明：既有解析器把PROP的units元数据当作额外信号；工程读取器仅过滤该元数据，校验真实曲线长度、有限值及时间递增。输入/输出/时间列已与原始标量记录逐点核对。',9)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(4,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

def make44():
    case=ROOT/'cases/44-ota5';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());run=ROOT/r['run_dir']
    out=ROOT/'reports/44-ota5-review.pdf';out.parent.mkdir(parents=True,exist_ok=True)
    raw=data(run,'ac.ac');f=raw['freq'];tv=-raw['yv']/raw['xv'];ti=raw['VYI:p']/raw['VXI:p'];loop=(tv*ti-1)/(tv+ti+2)
    noise=data(run,'noise.noise',required=('in','out'));v=r['values']
    metricinfo=[('环路增益 @1kHz','gain_db',1,'dB'),('UGB','ugb_hz',1e-6,'MHz'),('相位裕量','phase_margin_deg',1,'deg'),('总功耗（含50uA参考）','power_W',1e6,'uW'),('输入噪声 10Hz–10MHz','input_noise_Vrms',1e6,'uVrms'),('开环 CMRR @1kHz','cmrr_db',1,'dB'),('开环 PSRR+ @1kHz','psrr_plus_db',1,'dB'),('开环 PSRR− @1kHz','psrr_minus_db',1,'dB')]
    with PdfPages(out,metadata={'Title':'44 SMIC18 5T OTA 审查报告','Author':'SMIC18 benchmark reproduction','Subject':'Measured nominal transistor-level results; no PVT claim'}) as pdf:
        fig=page('44 | 5T OTA 审查报告',1,'结论：全部 nominal 原始指标通过；无需10%–15%放宽。2026-09-22')
        para(fig,.865,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；输入共模0.9 V；输出负载1 pF；外部偏置50 uA。核心5管加偏置复制管，使用目标工艺gm/ID LUT重新选尺寸。')
        rows=[]
        for name,key,scale,unit in metricinfo:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤'
            rows.append([name,f"{g['value']*scale:.3f}",f"{sign}{g['limits']['original']*scale:.3f}",f"{sign}{g['limits']['10pct']*scale:.3f}",f"{sign}{g['limits']['15pct']*scale:.3f}",unit])
        table(fig,[.07,.50,.86,.285],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.32,.135,.135,.135,.135,.14],8.5)
        ax=fig.add_axes([.07,.105,.86,.36]);ota_diagram(ax)
        para(fig,.088,'图示为信号核心。M6与M5共栅偏置；体端与完整端序见第4页网表。',9)
        save(pdf,fig)
        fig=page('尺寸依据与实际工作点',2,'使用已有SMIC18 LUT；不使用PTM代替目标PDK。')
        rows=[]
        for role,label in [('input','M1/M2 输入对'),('load','M3/M4 镜负载'),('tail','M5 尾源'),('reference','M6 参考')]:
            p=s['roles'][role];rows.append([label,p['model'],f"{p['L_um']:.2f}",f"{p['rounded_W_um']:.2f}",f"{p['gmid']:.1f}",f"{p['Id_A']*1e6:.1f}",f"{p['ft_Hz']/1e9:.2f}"])
        table(fig,[.07,.685,.86,.17],['角色','模型','L/um','W/um','gm/ID','I/uA','fT/GHz'],rows,[.27,.12,.11,.13,.13,.12,.12],9)
        para(fig,.65,'选点：输入对L=1 um、gm/ID=18提供增益、噪声和跨导；PMOS负载采用L=0.36 um、gm/ID=6，把电流镜极点推高。尾源/参考同L，目标尾电流180 uA。宽度按0.02 um记录网格取整。')
        rows=[]
        for name,p in r['operating_point'].items():
            rows.append([name,f"{abs(p['ids'])*1e6:.2f}",f"{p['gmid']:.2f}",f"{p['gmro']:.1f}",f"{abs(p['vds']):.3f}",f"{p['headroom_V']:.3f}"])
        table(fig,[.07,.43,.86,.14],['器件','|Id|/uA','gm/ID','gm/gds','|VDS|/V','余量/V'],rows,[.15,.18,.16,.17,.17,.17])
        para(fig,.395,'余量定义为 |VDS|−|VDSAT|；表中信号输入、镜负载和尾源均为饱和工作。闭环输出0.90107 V，尾节点0.34533 V。输入管有约0.345 V体偏置，实测gm/ID=18.29；因此零体偏置LUT作为初值，实际OP作为确认。')
        para(fig,.255,'设计经验：无需把所有信号器件都取长沟道。长NMOS输入对配较短、强反型PMOS镜，在本任务负载下同时保住DC增益与镜节点速度。这个结论限定于本次SMIC18 nominal工作点，不是跨PVT保证。')
        para(fig,.125,'LUT出处：gmoverid_smic18/lut/tt；每次查询的原文件SHA-256、VDS、L、Wref和目标电流已保存在 cases/44-ota5/sizing.json。',9)
        save(pdf,fig)
        fig=page('频域与噪声证据',3,'全部曲线来自同一电路快照的Spectre PSF；没有用Sky130发布值替代。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.17,top=.84,hspace=.34,wspace=.34)
        axs[0,0].semilogx(f,20*np.log10(abs(loop)),color=BLUE);axs[0,0].axhline(0,color=GRAY,lw=.7);axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Loop gain (dB)',xlim=(10,1e10))
        axs[0,1].semilogx(f,np.unwrap(np.angle(loop))*180/np.pi,color=BLUE);axs[0,1].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Loop phase (deg)',xlim=(10,1e10))
        axs[1,0].loglog(noise['freq'],abs(noise['in'])*1e9,color=BLUE);axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Input noise (nV/sqrt(Hz))')
        adm=raw['vout_dm']/(raw['vinp_dm']-raw['vinn_dm']);acm=raw['vout_cm']/((raw['vinp_cm']+raw['vinn_cm'])/2)
        for label,ratio in [('CMRR',adm/acm),('PSRR+',adm/raw['vout_ps']),('PSRR-',adm/raw['vout_ms'])]:axs[1,1].semilogx(f,20*np.log10(abs(ratio)),label=label)
        axs[1,1].legend(fontsize=8);axs[1,1].set(xlabel='Frequency (Hz)',ylabel='Rejection (dB)',xlim=(10,1e7))
        for ax in axs.flat:ax.grid(True,which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.125,'环路在10 Hz–10 GHz内只有一次下降穿越0 dB。噪声积分为sqrt(∫en² df)，PSF单位已核对为V/sqrt(Hz)。CMRR/PSRR使用自然开环工作点，不能与DC闭环噪声台的工作点混用。',9)
        save(pdf,fig)
        fig=page('精确网表、测量与复现',4,'原始网表和运行输入快照共同构成证据，环境保持未修改。')
        lines=(case/'circuit.scs').read_text().splitlines()
        body='\n'.join(x for x in lines if not x.startswith('//'))
        fig.text(.075,.853,body,fontsize=9.5,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.6)
        para(fig,.575,'测量保持上游定义：Tv=−V(yv)/V(xv)，Ti=I(VYI)/I(VXI)，T=(Tv·Ti−1)/(Tv+Ti+2)。用复数返回比求1 kHz增益、首次下降跨频UGB和相位裕量。功耗为1.8·|I(VDDP)|，含50 uA参考支路。')
        para(fig,.438,'本次只复现 nominal 电气合同；未执行其余26个PVT点、Monte Carlo或版图提取。没有新增数字逻辑。未把本结果作为量产良率、器件可靠性或全工作范围的证明。')
        para(fig,.33,'复现命令（从本工程根目录）：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case44_ota5.py\n生成PDF：同一Python运行 scripts/review_pdf.py 44',9)
        para(fig,.223,'结果：cases/44-ota5/latest_results.json\n运行：'+r['run_dir']+'\n依赖与模型SHA-256：该运行目录/run.json\n参考任务：sky130-ota-5t-gain40-pm60-noise50uv-pvt',8.5)
        para(fig,.093,'审查重点：输入级体偏置、PMOS镜极点、自然开环抑制比定义，以及报告与最终网表哈希是否一致。',9)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(44,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

def make45():
    case=ROOT/'cases/45-divider';r=json.loads((case/'latest_results.json').read_text());v=r['values'];runs=[ROOT/x for x in r['run_dirs']]
    d=data(runs[0],'tran.tran');rr=data(runs[1],'tran.tran')
    h=json.loads((case/'hd_cells_manifest.json').read_text());out=ROOT/'reports/45-divider-review.pdf'
    with PdfPages(out,metadata={'Title':'45 SMIC18 HD 二分频审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('45 | HD 二分频审查报告',1,'结论：原始1 GHz时钟与20 fF负载下，全部 nominal 原始指标通过。')
        para(fig,.863,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；时钟与复位各经20 ohm源阻抗，时钟边沿10 ps。使用原厂HD单元晶体管网表，无行为逻辑、无自定义门尺寸。')
        rows=[]
        for name,key,scale,unit in [('异步复位延迟','reset_delay_s',1e12,'ps'),('最大时钟到输出','clock_delay_s',1e12,'ps'),('占空比偏离50%','duty_error',100,'百分点')]:
            g=r['gates'][key];rows.append([name,f"{g['value']*scale:.4f}",f"≤{g['limits']['original']*scale:.3f}",f"≤{g['limits']['10pct']*scale:.3f}",f"≤{g['limits']['15pct']*scale:.3f}",unit])
        table(fig,[.07,.65,.86,.13],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.15,.14,.14,.14,.14],8.5)
        rows=[['输出频率',f"{v['output_frequency_hz']/1e6:.5f} MHz",'495–505 MHz'],['高电平占空比',f"{min(v['high_duties'])*100:.4f}–{max(v['high_duties'])*100:.4f}%",'49–51%'],['复位保持窗最大值',f"{v['asserted_max_V']*1e3:.3f} mV",'≤360 mV'],['异步释放后/下一沿前',f"{v['release_hold_max_V']*1e3:.3f} mV",'≤360 mV'],['释放后下一有效沿',f"{v['next_edge_V']:.4f} V",'≥1.44 V']]
        table(fig,[.07,.405,.86,.19],['功能检查','实测','原门槛（不放宽）'],rows,[.38,.34,.28],9)
        ax=fig.add_axes([.07,.135,.86,.22]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,4))
        for x,y,w,hx,label in [(3,1.35,2.7,1.6,'DRNQNHDV1\nD = QN'),(7,1.6,2.2,1.1,'NOR2HDV16'),(.25,.15,2.3,.8,'INHDV2')]:
            ax.add_patch(Rectangle((x,y),w,hx,fill=False,edgecolor=BLUE,lw=1.2));ax.text(x+w/2,y+hx/2,label,ha='center',va='center',fontsize=10)
        ax.annotate('',xy=(3,2.55),xytext=(.1,2.55),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(.1,2.8,'clk',fontsize=10)
        ax.annotate('',xy=(7,2.45),xytext=(5.7,2.45),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(6,2.75,'QN',fontsize=9)
        ax.plot([6.3,6.3,2.65,2.65,3],[2.45,3.45,3.45,1.65,1.65],color=BLUE,lw=1)
        ax.plot([1.4,1.4,8.1],[.95,1.1,1.1],color=BLUE);ax.plot([8.1,8.1],[1.1,1.6],color=BLUE);ax.text(5.9,.9,'reset',fontsize=9)
        ax.plot([2.55,4.35,4.35],[.55,.55,1.35],color=BLUE);ax.text(3,.75,'RDN',fontsize=9)
        ax.annotate('',xy=(9.9,2.15),xytext=(9.2,2.15),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(9.15,2.9,'clkout',fontsize=9)
        para(fig,.092,'FF内部状态确实复位；输出NOR提供快速拉低路径。复位释放时内部QN仍为高，不会提前产生输出上升。连接以第3页精确网表为准。',9)
        save(pdf,fig)
        fig=page('瞬态证据与边沿定义',2,'边沿在实际DUT引脚0.9 V处线性插值；没有使用源端理想时刻替代。')
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.12,right=.94,bottom=.17,top=.855,hspace=.38)
        for key,lab in [('clk','CLK'),('clkout','OUT')]:axs[0].plot(d['time']*1e9,d[key],label=lab,lw=1)
        axs[0].set(xlim=(.8,8.3),ylabel='Voltage (V)',xlabel='Time (ns)',title='Divide by 2 at 1 GHz');axs[0].legend(loc='upper right',ncol=2,fontsize=8)
        for key,lab in [('reset','RESET'),('clkout','OUT'),('clk','CLK')]:axs[1].plot(rr['time']*1e9,rr[key],label=lab,lw=1)
        axs[1].set(xlim=(1.5,2.75),ylabel='Voltage (V)',xlabel='Time (ns)',title='Asynchronous assertion and release');axs[1].legend(loc='upper right',ncol=3,fontsize=8)
        axs[1].axvspan(2.05,2.2,color=GREEN,alpha=.1)
        for key,lab in [('clkout','OUT'),('reset','RESET')]:axs[2].plot(rr['time']*1e12,rr[key],label=lab,lw=1)
        axs[2].axhline(.9,color=GRAY,ls='--',lw=.7);axs[2].set(xlim=(1720,1850),ylabel='Voltage (V)',xlabel='Time (ps)',title='Reset edge detail');axs[2].legend(fontsize=8)
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.12,'复位前1.65 ns检查为高；1.85–2.04 ns检查保持低；2.05–2.20 ns检查异步释放保持；2.70 ns检查下一沿已正确翻转。逐周期周期与高/低宽度也单独验收。',9)
        save(pdf,fig)
        fig=page('HD单元与精确连接',3,'所有单元内部MOS尺寸和模型名保持原厂CDL值。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.85,body,fontsize=9,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.7)
        rows=[[c['name'],' '.join(c['pins']),str(c['mos_count'])] for c in h['cells']]
        table(fig,[.07,.565,.86,.13],['原厂单元','端序','MOS数'],rows,[.26,.60,.14],8.5)
        para(fig,.525,'D与QN连接构成T触发器。RDN由reset反相驱动，使异步复位清除FF内部状态。NOR在外部reset为高时直接强制clkout为低，改善复位响应；它没有替代内部复位。VNW接VDD、VPW接VSS。')
        para(fig,.393,'该模块是纯数字时序路径，按用户要求使用HD标准单元，不对其内部器件进行gm/ID重设计。模拟部分的gm/ID要求适用于另外的模拟核心。数字性能以这套原厂晶体管模型的实际瞬态结果为依据。')
        para(fig,.272,'原始库：SCC018UG_HD_RVT_V0.3a\n源CDL SHA-256：'+h['source_sha256']+'\n提取记录：cases/45-divider/hd_cells_manifest.json\n已转换单元：cases/45-divider/hd_cells.scs',8.5)
        para(fig,.135,'未覆盖：其他PVT、时钟抖动、全setup/hold扫描、复位recovery/removal统计、互连寄生。没有把本次波形作为上述范围的证明。',9)
        save(pdf,fig)
        fig=page('迭代、权衡与复现路径',4,'失败迭代保留在runs/45；最终验收使用同一最终电路的两套测试。')
        history=[]
        seen=set()
        for p in sorted((ROOT/'runs/45').glob('*_divide/measurements.json')):
            rr0=json.loads(p.read_text());rd=p.parent;man=json.loads((rd/'inputs/hd_cells_manifest.json').read_text());names=[x['name'] for x in man['cells']]
            ff=next(x for x in names if x.startswith('DRN'));no=next(x for x in names if x.startswith('NOR'));vv=rr0['values']
            history.append([ff.replace('DRNQNHDV','FF V'),no.replace('NOR2HDV','NOR V'),f"{min(vv['high_duties'])*100:.3f}%",f"{max(vv['clock_delays_s'])*1e12:.1f}",f"{vv['reset_delay_s']*1e12:.1f}", '通过' if rr0['status'].startswith('complete') else '占空比失败'])
        table(fig,[.07,.7,.86,.15],['触发器','输出门','最小高占比','延迟/ps','复位/ps','结论'],history,[.15,.15,.2,.16,.16,.18],8.5)
        para(fig,.659,'第一版的频率、复位和时钟延迟通过，但占空比约48.39%，超出15%放宽后的窗口。第二版同时增大FF与输出门也没有解决。最终用FF V1 + NOR V16，得到49.94%左右占空比，同时保留304.5 ps以内延迟与26.8 ps复位。')
        para(fig,.505,'工程认识：门驱动档位同时改变输出上/下沿延迟和前一级负载，因此“所有单元加大”并不保证占空比更好。这里通过未修改的标准单元组合找到时序平衡；不是手改晶体管尺寸。')
        para(fig,.37,'复现命令（工程根目录）：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case45_divider.py --ff 1 --nor 16\n生成PDF：同一Python运行 scripts/review_pdf.py 45',9)
        para(fig,.244,'结果：cases/45-divider/latest_results.json\n分频运行：'+r['run_dirs'][0]+'\n复位运行：'+r['run_dirs'][1]+'\n每次run.json保存精确输入、模型和库哈希。',8.5)
        para(fig,.109,'参考任务：sky130-transistor-divide-by-2。外部时钟、复位波形、源电阻和负载保持原nominal条件。',9)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(45,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('slot',type=int);a=p.parse_args()
    if a.slot==2:print(make02())
    elif a.slot==3:
        from review03 import make03
        print(make03())
    elif a.slot==4:print(make04())
    elif a.slot==7:
        from review07 import make07
        print(make07())
    elif a.slot==10:
        from review10 import make10
        print(make10())
    elif a.slot==8:
        from review08 import make08
        print(make08())
    elif a.slot==12:print(make12())
    elif a.slot==13:
        from review13 import make13
        print(make13())
    elif a.slot==14:
        from review14 import make14
        print(make14())
    elif a.slot==16:print(make16())
    elif a.slot==20:
        from review20 import make20
        print(make20())
    elif a.slot==22:
        from review22 import make22
        print(make22())
    elif a.slot==23:
        from review23 import make23
        print(make23())
    elif a.slot==24:
        from review24 import make24
        print(make24())
    elif a.slot==25:
        from review25 import make25
        print(make25())
    elif a.slot==29:
        from review29 import make29
        print(make29())
    elif a.slot==31:
        from review31 import make31
        print(make31())
    elif a.slot==35:
        from review35 import make35
        print(make35())
    elif a.slot==36:
        from review36 import make36
        print(make36())
    elif a.slot==37:
        from review37 import make37
        print(make37())
    elif a.slot==41:
        from review41 import make41
        print(make41())
    elif a.slot==44:print(make44())
    elif a.slot==45:print(make45())
    elif a.slot==47:
        from review47 import make47
        print(make47())
    elif a.slot==49:
        from review49 import make49
        print(make49())
    elif a.slot==50:
        from review50 import make50
        print(make50())
    else:raise SystemExit('Report writer not yet implemented for this case')

if __name__=='__main__':main()
