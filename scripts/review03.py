from review_pdf import *

def make03():
    case=ROOT/'cases/03-selfbiased-gmr';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values'];run=ROOT/r['run_dir']
    a=data(run,'ac.ac');d=data(run,'tran.tran');out=ROOT/'reports/03-selfbiased-gmr-review.pdf'
    with PdfPages(out,metadata={'Title':'03 SMIC18 自偏置退化GM-R审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('03 | 自偏置退化 GM-R 审查',1,'结论：独立实现的nominal原指标全部通过，无需10%–15%放宽。')
        para(fig,.864,'条件：SMIC18MMRF / tt / 1.8 V / 27°C，外部IREF50 uA，输入共模及VCM0.9 V，每端负载1 pF。DUT只含MOS及正值电阻，VCM为保留兼容端口。')
        info=[('AC增益偏离目标2','gain_error',1,'V/V'),('上端−3dB带宽','bandwidth_Hz',1e-6,'MHz'),('全端口静态功耗','power_W',1e3,'mW'),('3MHz SDR','SDR_dB',1,'dB'),('基波增益偏离目标2','fundamental_gain_error',1,'V/V')]
        rows=[]
        for label,key,k,u in info:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([label,f"{g['value']*k:.5f}",f"{sign}{g['limits']['original']*k:.3f}",f"{sign}{g['limits']['10pct']*k:.3f}",f"{sign}{g['limits']['15pct']*k:.3f}",u])
        table(fig,[.07,.543,.86,.229],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.15,.14,.14,.14,.12],8.4)
        para(fig,.501,f"实际AC差分增益={v['gain_1MHz']:.7f} V/V，拟合基波增益={v['fundamental_gain']:.7f} V/V。正弦差分峰值固定100 mV，未减小激励来换取更高SDR。残差RMS为{v['fit_residual_rms_V']*1e6:.3f} uV。",10)
        para(fig,.366,'电源功耗沿用原定义：VDD、VCM、VIN和VIP端口DC功率绝对值相加。IREF由VDD提供，已经包含；不能借用共模或信号端口供电来隐藏功耗。',10)
        para(fig,.246,'与第04项的区别：本例尾电流来自内部β倍增自偏置，IREF主要终止在参考二极管并控制弱启动下拉；第04项直接从IREF镜像尾电流。两个模块各有独立网表、运行、合同和证据。',10)
        para(fig,.113,'本题原目标为15个工艺温度点，当前只完成指定nominal点。未运行其余14点、供电变化、失配或寄生提取；也未额外宣称冷启动斜坡通过。',9.4)
        save(pdf,fig)
        fig=page('自偏置连接与gm/ID工作点',2,'输入与主偏置使用同一n18单元，按并联倍数扩展电流。')
        ax=fig.add_axes([.07,.726,.86,.15]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3))
        for x,w,label in [(0,2.3,'IREF参考\n弱启动下拉'),(3.1,2.7,'β倍增环\nK=4, RB=3 kΩ'),(6.7,3.3,'源极退化差分对\nRS500 Ω / RL1770 Ω')]:
            ax.add_patch(Rectangle((x,1),w,1.6,fill=False,edgecolor=BLUE));ax.text(x+w/2,1.8,label,ha='center',va='center',fontsize=9)
        for x1,x2 in [(2.3,3.1),(5.8,6.7)]:ax.annotate('',xy=(x2,1.8),xytext=(x1,1.8),arrowprops=dict(arrowstyle='->',color=BLUE))
        rows=[]
        for key,label,m in [('n_unit','MB1/MB2/TAIL/IN±','1/4/25/12.5'),('p_mirror','MP1/MP2','1'),('reference','MREF','1'),('startup','MST','1')]:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:.2f}"])
        table(fig,[.07,.53,.86,.153],['角色','模型','单位W/L(um)','m','目标gm/ID'],rows,[.31,.11,.20,.23,.15],8.3)
        rows=[]
        for key,q in r['operating_point'].items():rows.append([key,f"{abs(q['ids'])*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['headroom_V']*1e3:.1f}"])
        table(fig,[.07,.253,.86,.224],['实际器件','|I|/uA','gm/ID','|VDS|−|VDSAT|/mV'],rows,[.22,.22,.22,.34],8.7)
        para(fig,.206,'输入gm=4.078 mS、gmb=1.000 mS。忽略有限ro时，退化跨导近似gm/[1+(gm+gmb)RS]，体效应不可省略。尾源0.1794 V、饱和余量77.6 mV，是后续跨角落设计需关注的低余量节点。',9.4)
        para(fig,.082,'MB2的gm/ID约21，进入弱反型区；其VDS仍远大于VDSAT。不能把β倍增所有器件都视作强反型平方律器件。',9.3)
        save(pdf,fig)
        fig=page('差分频响与拟合失真',3,'SDR只针对指定确定性正弦响应，不等同于含随机噪声的SNR。')
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.13,right=.94,bottom=.18,top=.846,hspace=.40)
        h=abs(a['vop']-a['von']);axs[0].semilogx(a['freq'],h,color=BLUE);axs[0].axhline(v['gain_1MHz']/np.sqrt(2),color=GRAY,ls='--');axs[0].set(xlabel='Frequency (Hz)',ylabel='Gain (V/V)')
        keep=(d['time']>=.5e-6-1e-15)&(d['time']<=1.5e-6+1e-15);t=d['time'][keep];y=(d['vop']-d['von'])[keep]
        basis=np.column_stack([np.ones(len(t)),np.sin(2*np.pi*3e6*t),np.cos(2*np.pi*3e6*t)]);fit=basis@np.linalg.lstsq(basis,y,rcond=None)[0]
        axs[1].plot(t*1e6,y,label='Output',lw=1);axs[1].plot(t*1e6,fit,label='DC + sine + cosine fit',ls='--',lw=1);axs[1].legend(fontsize=8);axs[1].set(xlabel='Time (us)',ylabel='Differential output (V)')
        axs[2].plot(t*1e6,(y-fit)*1e6,color=BLUE);axs[2].set(xlabel='Time (us)',ylabel='Fit residual (uV)')
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.133,'拟合窗口0.5–1.5 us，等间隔1 ns，共1001点。先以DC、sin、cos三个基函数作最小二乘，再用基波功率除残差均方；保留原信号峰值、频率及外部1 pF负载。',9.3)
        para(fig,.068,'带宽以1 MHz实测增益的1/√2为门槛；AC扫描100 kHz–11 GHz，包含原10 GHz检查点。',9)
        save(pdf,fig)
        fig=page('精确网表、迭代与复现',4,'自偏置改变偏置生成方式，不能自动证明跨PVT恒定增益。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.858,body,fontsize=8.2,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.45)
        para(fig,.566,'初版RL=1900 Ω时AC增益2.14485、基波增益2.13841，超出合同；保持偏置与RS，仅将RL改为1770 Ω，得到2.00086和1.99503，带宽80.25→86.06 MHz。SDR保持约61.98 dB。',9.5)
        para(fig,.427,'主管22.07 uA并不直接保证每个尾源单元也流22.07 uA：二者VDS为0.522和0.179 V，尾电流实际505.94 uA。保留镜像误差和尾源余量，比只记并联倍数更有用。启动支路0.372 uA持续导通，包含在功耗中。',9.4)
        para(fig,.292,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python\n scripts/case03_selfbiased_gmr.py\nPDF：同一Python运行 scripts/review_pdf.py 3',8.7)
        para(fig,.203,'最终运行：'+r['run_dir']+'\n每次运行保留精确网表、LUT查询与模型哈希；当前无模型尺寸越界。',8.6)
        para(fig,.113,'原任务：sky130-gmr-degen-amp-constant-gm-pvt。输入/负载/功耗/SDR定义与原nominal合同一致；结构是本次目标工艺实现，不冒充原参考电路的逐管尺寸迁移。',9.2)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(3,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
