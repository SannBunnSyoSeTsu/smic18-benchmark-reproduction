"""Review report for the low-power cascoded-load Miller amplifier."""
from review_pdf import *

def make41():
    case=ROOT/'cases/41-lowpower-miller'
    r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values']
    runs=[ROOT/x for x in r['run_dirs']]
    a=data(runs[0],'ac.ac');sweep=data(runs[0],'swing.dc');n=data(runs[1],'noise.noise',required=('in','out'));d=data(runs[2],'tran.tran')
    f=a['freq'];loop=-a['voutl']/a['vinnl'];out=ROOT/'reports/41-lowpower-miller-review.pdf'
    with PdfPages(out,metadata={'Title':'41 SMIC18 低功耗 Miller 运放审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('41 | 低功耗 Miller 运放审查',1,'结论：全部原nominal指标通过，无需使用10%–15%性能放宽。')
        para(fig,.863,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；外部参考50 uA；输入共模0.9 V；负载2 pF。第一级级联PMOS镜负载，第二级为PMOS共源与NMOS电流源。')
        info=[('10Hz环路增益','gain_db',1,'dB'),('UGB','ugb_hz',1e-6,'MHz'),('相位裕量','phase_margin_deg',1,'deg'),('静态输出误差','output_error_V',1e3,'mV'),('总功耗（含参考）','power_W',1e6,'uW'),('输入积分噪声','input_noise_Vrms',1e6,'uVrms'),('闭环PSRR+ @1kHz','psrr_1k_dB',1,'dB'),('闭环PSRR+ @1MHz','psrr_1m_dB',1,'dB'),('闭环CMRR @1kHz','cmrr_1k_dB',1,'dB'),('连续输出范围','output_range_Vpp',1,'Vpp'),('最坏建立时间','settling_s',1e9,'ns'),('最坏最终跟踪误差','settling_error_V',1e3,'mV'),('上升压摆率','slew_rise_V_per_us',1,'V/us'),('下降压摆率','slew_fall_V_per_us',1,'V/us')]
        rows=[]
        for label,key,scale,unit in info:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤'
            rows.append([label,f"{g['value']*scale:.3f}",f"{sign}{g['limits']['original']*scale:.3f}",f"{sign}{g['limits']['10pct']*scale:.3f}",f"{sign}{g['limits']['15pct']*scale:.3f}",unit])
        table(fig,[.07,.26,.86,.52],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.14,.14,.14,.14,.13],8.3)
        para(fig,.216,'噪声增益20的实测−3 dB带宽2.14287 MHz，10 Hz积分到该频率得到23.239 uVrms。环路在10 Hz–10 GHz只下降跨越一次0 dB，之后无回穿。',9.5)
        para(fig,.116,'100 mV阶跃最坏终值误差16.13 uV，即0.01613%，同时满足2 mV及2%限制。额外PVT、Monte Carlo与版图验证不在本次nominal范围内。',9.3)
        save(pdf,fig)
        fig=page('结构、gm/ID尺寸与工作点',2,'同一PMOS单元电流密度贯穿镜负载、共栅管和第二级。')
        ax=fig.add_axes([.07,.725,.86,.14]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3))
        for x,label in [(1,'NMOS差分对\n级联PMOS镜负载'),(6,'PMOS共源\nNMOS电流源')]:
            ax.add_patch(Rectangle((x,1),3,1.5,fill=False,edgecolor=BLUE));ax.text(x+1.5,1.75,label,ha='center',va='center',fontsize=10)
        ax.annotate('',xy=(1,1.7),xytext=(0,1.7),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(.1,2.7,'VIN±',fontsize=9)
        ax.annotate('',xy=(6,1.7),xytext=(4,1.7),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(4.2,2,'stage1',fontsize=9)
        ax.annotate('',xy=(10,1.7),xytext=(9,1.7),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(9.2,2.7,'VOUT',fontsize=9)
        ax.plot([4.8,4.8,9.5,9.5],[1.7,.3,.3,1.7],color=GREEN);ax.text(7,.45,'RZ 700 Ω + CC 2 pF',ha='center',fontsize=9)
        rows=[['MINN/MINP','n18','30.76 / 1','1','18'],['MREF/MTAIL/MLOAD/MCBN','n18','3.22 / 1','5 / 6 / 14 / 1','12'],['MPD/MPM/MCD/MCM','p18','3.14 / 0.36','3 each','10'],['MPCB / MSECOND','p18','3.14 / 0.36','1 / 14','10']]
        table(fig,[.07,.526,.86,.159],['角色','模型','单位W/L (um)','m','目标gm/ID'],rows,[.34,.10,.20,.21,.15],8.1)
        rows=[]
        for key in ['MINP','MINN','MPM','MCD','MCM','MTAIL','MSECOND','MLOAD','MPCB']:
            q=r['operating_point'][key];rows.append([key,f"{abs(q['ids'])*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['gmro']:.1f}",f"{q['headroom_V']*1e3:.1f}"])
        table(fig,[.07,.217,.86,.27],['实际工作点','|I| / uA','gm/ID','gm/gds','饱和余量/mV'],rows,[.24,.20,.18,.18,.20],8.6)
        para(fig,.175,'RB=22 kΩ使MPCB源端为1.57631 V；共栅管源端1.57599/1.57603 V，体偏置相近。偏置VBP=0.88527 V。PMOS镜管饱和余量仅44.9 mV，虽nominal通过，仍需单独做PVT才能判断稳健性。',9.2)
        para(fig,.072,'第二级实际gm=1.42786 mS，1/gm=700.35 Ω，与RZ=700 Ω接近；抵消前馈零点的初算仍须由实际环路相位确认。',9)
        save(pdf,fig)
        fig=page('环路、噪声及供电抑制',3,'维持上游的串联电压注入、闭环抑制比和噪声积分口径。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.2,top=.845,hspace=.38,wspace=.37)
        axs[0,0].semilogx(f,20*np.log10(abs(loop)),color=BLUE);axs[0,0].axhline(0,color=GRAY,lw=.7);axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Loop gain (dB)')
        axs[0,1].semilogx(f,np.unwrap(np.angle(loop))*180/np.pi,color=BLUE);axs[0,1].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Loop phase (deg)')
        axs[1,0].loglog(n['freq'],abs(n['in'])*1e9,color=BLUE);axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Input noise (nV/sqrt(Hz))')
        axs[1,1].semilogx(f,-20*np.log10(abs(a['voutp'])),label='PSRR+');axs[1,1].semilogx(f,-20*np.log10(abs(a['voutc'])),label='CMRR');axs[1,1].set(xlabel='Frequency (Hz)',ylabel='Closed-loop rejection (dB)',xlim=(1e3,1e7));axs[1,1].legend(fontsize=8)
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.15,'环路T=−Vout/Vinn，DC单位反馈。PSRR采用VDD AC=1、输入固定；CMRR在vinp与串联反馈同向注入AC=1；两者均按−20log10|Vout|计算。这些是本题闭环定义。',9.2)
        para(fig,.08,'噪声使用噪声增益20的独立闭环AC确定积分上限；PSF输入噪声幅度平方积分再开根号，未以UGB替代。',9.2)
        save(pdf,fig)
        fig=page('双向阶跃、压摆与连续范围',4,'全部使用2 pF外部负载；压摆刺激按本题10 ns/71 ns的时序。')
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.13,right=.94,bottom=.16,top=.845,hspace=.41)
        for k,l in [('vinS','Input'),('outS','Output')]:axs[0].plot(d['time']*1e9,d[k],label=l,lw=1)
        axs[0].set(xlim=(0,130),xlabel='Time (ns)',ylabel='Voltage (V)',title='0.85 V ↔ 0.95 V');axs[0].legend(fontsize=8,ncol=2)
        for k,l in [('vinR','Input'),('outR','Output')]:axs[1].plot(d['time']*1e9,d[k],label=l,lw=1)
        axs[1].set(xlim=(0,130),xlabel='Time (ns)',ylabel='Voltage (V)',title='0.65 V ↔ 1.15 V; measure 0.75–1.05 V');axs[1].legend(fontsize=8,ncol=2)
        axs[2].plot(sweep['sweepin'],abs(sweep['vouts']-sweep['vinps'])*1e3,color=BLUE);axs[2].axhline(20,color=GRAY,ls='--')
        axs[2].set(xlabel='Input / requested output (V)',ylabel='Tracking error (mV)',title='Contiguous DC tracking range: 0.3–1.5 V')
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.117,'正负100 mV阶跃分别15.949/17.477 ns进入并保持2 mV窗口，65/130 ns终值均合格。整个原DC扫描0.3–1.5 V均满足20 mV跟踪误差；只声明这1.2 V范围，不向扫描边界外延伸。',9.2)
        save(pdf,fig)
        fig=page('精确电路、设计认识与复现',5,'高抑制比来自拓扑与偏置匹配；当前证据限于nominal。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.858,body,fontsize=8.1,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.45)
        para(fig,.541,'镜负载与第二级采用同一个p18单位管，通过m改变电流。两输入漏极电位1.17225/1.17703 V，仅差4.774 mV；这有助于减小确定性系统失调，本次单位反馈输出误差16.05 uV。它不能代表随机失配失调。',9.4)
        para(fig,.406,'级联镜提升第一级输出电阻并减少供电耦合；但额外叠管消耗余量，上层MPM仅余44.9 mV。不要把90.83 dB的nominal闭环PSRR或88.58 dB增益直接视为跨角落保证。所有器件宽度均在模型有效范围。',9.4)
        para(fig,.277,'复现：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case41_lowpower_miller.py\n生成PDF：同一Python运行 scripts/review_pdf.py 41',8.6)
        para(fig,.192,'静态：'+r['run_dirs'][0]+'\n噪声：'+r['run_dirs'][1]+'\n动态：'+r['run_dirs'][2],8.3)
        para(fig,.085,'原任务：sky130-two-stage-miller-opamp-gain70-ugb20-pm60-noise50uv-pvt。本次未执行其他PVT、失配、寄生或版图验证；报告绑定最终网表及实测JSON哈希。',9)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=5,render_review_pending=True))
    update_case(41,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
