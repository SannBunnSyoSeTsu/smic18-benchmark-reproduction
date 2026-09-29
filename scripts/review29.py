from review_pdf import *

def make29():
    case=ROOT/'cases/29-ahuja';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());runs=[ROOT/x for x in r['run_dirs']]
    a=data(runs[0],'ac.ac');d=data(runs[1],'tran.tran');out=ROOT/'reports/29-ahuja-review.pdf'
    with PdfPages(out,metadata={'Title':'29 SMIC18 Ahuja 宽负载运放审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('29 | Ahuja 宽负载运放审查',1,'结论：20 / 63 / 200 pF三种负载及双向大信号，均通过原nominal指标。')
        para(fig,.864,'条件：SMIC18MMRF / tt / 1.8 V / 27°C，50 uA参考，输入共模0.9 V。折叠共源共栅第一级、NMOS共源第二级；6.8 pF补偿返回PMOS电流缓冲管的源端f2。')
        specs=[('20pF增益@10Hz','gain_db',1,'dB'),('20pF UGB','ugb_hz',1e-6,'MHz'),('20pF相位裕量','pm_L',1,'deg'),('63pF相位裕量','pm_M',1,'deg'),('200pF相位裕量','pm_H',1,'deg'),('单位反馈输出误差','offset_V',1e3,'mV'),('总功耗（含参考）','power_W',1e3,'mW'),('最坏建立时间','settling_s',1e6,'us'),('最坏终值误差','final_error_V',1e3,'mV')]
        rows=[]
        for label,key,k,u in specs:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([label,f"{g['value']*k:.4f}",f"{sign}{g['limits']['original']*k:.3f}",f"{sign}{g['limits']['10pct']*k:.3f}",f"{sign}{g['limits']['15pct']*k:.3f}",u])
        table(fig,[.07,.433,.86,.34],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.15,.14,.14,.14,.12],8.5)
        rows=[[q['load_pF'],f"{q['gain_db']:.3f}",f"{q['ugb_hz']/1e6:.4f}",f"{q['phase_margin_deg']:.3f}",'1 / 无回穿'] for q in r['ac_by_load'].values()]
        table(fig,[.07,.248,.86,.13],['负载/pF','10Hz增益/dB','UGB/MHz','PM/deg','0dB交越'],rows,[.16,.23,.19,.19,.23],9)
        para(fig,.204,'200 pF上/下阶跃建立121.264/96.327 ns；终值误差38.01/41.62 uV。测量从输入1%命令交越开始，目标固定为1.2/0.9 V，误差窗口6 mV，不以实际终值重定中心。',9.5)
        para(fig,.094,'仅原理图nominal：未运行其余PVT、无源变化、失配、噪声或版图。模型尺寸均有效，相关信号路径器件最终工作于饱和区。',9.3)
        save(pdf,fig)
        fig=page('拓扑、gm/ID与偏置修正',2,'电流缓冲补偿与直接Miller补偿的连接点不同。')
        ax=fig.add_axes([.07,.705,.86,.17]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3.5))
        for x,w,label in [(0,2.5,'NMOS输入对\nPMOS折叠支路'),(3.4,2.9,'PMOS电流缓冲\nNMOS级联镜'),(7.2,2.7,'NMOS共源\nPMOS电流源')]:
            ax.add_patch(Rectangle((x,1.4),w,1.4,fill=False,edgecolor=BLUE));ax.text(x+w/2,2.1,label,ha='center',va='center',fontsize=9)
        ax.annotate('',xy=(3.4,2.1),xytext=(2.5,2.1),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(2.65,2.45,'f2',fontsize=9)
        ax.annotate('',xy=(7.2,2.1),xytext=(6.3,2.1),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(6.3,2.45,'stage1',fontsize=8)
        ax.plot([2.9,2.9,9.6,9.6],[2.1,.5,.5,1.4],color=GREEN);ax.text(6,.67,'CC = 6.8 pF returns to f2',ha='center',fontsize=9)
        rows=[]
        labels=[('input','MINP/MINN','1'),('n_unit','REF / TAIL / NB','5 / 4 / 2'),('p_unit','偏置 / 折叠 / 输出','1 / 5 / 32.5'),('p_cascode','MFCP/MFCN','4'),('n_cascode','MNCB / MCD/MCO','1 / 4'),('n_mirror','MMD/MMO','1'),('second','MSECOND','1')]
        for key,label,m in labels:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:g}"])
        table(fig,[.07,.422,.86,.235],['器件角色','模型','单位W/L (um)','m','目标gm/ID'],rows,[.31,.11,.22,.21,.15],8.5)
        rows=[]
        for key in ['MINP','MFN','MFCN','MMO','MCO','MSECOND']:
            q=r['operating_point'][key];rows.append([key,f"{abs(q['ids'])*1e6:.2f}",f"{q['gmid']:.2f}",f"{q['gmro']:.1f}",f"{q['headroom_V']*1e3:.1f}"])
        table(fig,[.07,.168,.86,.207],['实际工作点','|I| / uA','gm/ID','gm/gds','余量 / mV'],rows,[.24,.20,.18,.18,.20],8.7)
        para(fig,.128,'初版RCN=11 kΩ时镜管VDS≈177 mV，小于VDSAT≈199 mV。提高RCN到18 kΩ后VDS≈289 mV、余量96 mV；增益86.17→99.18 dB，输出误差147→41.7 uV，速度几乎不变。',9.2)
        save(pdf,fig)
        fig=page('三负载环路与双向动态',3,'全部曲线来自最终同一电路；三个AC条件各有完整1 Hz–300 MHz扫描。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.21,top=.845,hspace=.42,wspace=.36)
        for suffix in ['L','M','H']:
            q=r['ac_by_load'][suffix];h=a['out'+suffix];label=f"{q['load_pF']} pF"
            axs[0,0].semilogx(a['freq'],20*np.log10(abs(h)),label=label)
            axs[0,1].semilogx(a['freq'],np.unwrap(np.angle(h))*180/np.pi,label=label)
        axs[0,0].axhline(0,color=GRAY,lw=.7);axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Gain (dB)');axs[0,0].legend(fontsize=8)
        axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Phase (deg)');axs[0,1].legend(fontsize=8)
        for ax,origin,lim in [(axs[1,0],2e-6,(-.03,.3)),(axs[1,1],12.01e-6,(-.03,.3))]:
            ax.plot((d['time']-origin)*1e6,d['vin'],label='Input',lw=1);ax.plot((d['time']-origin)*1e6,d['out'],label='Output',lw=1);ax.set(xlim=lim,xlabel='Time from edge start (us)',ylabel='Voltage (V)');ax.legend(fontsize=8)
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.158,'AC外部500 MΩ/50 mF伺服只在DC闭合，频带内近似开环；这与第16/41项的串联注入方法不同。200 pF瞬态则直接单位反馈，模拟到20 us，最终1 ns输出采样，最大内部步长0.5 ns。',9.2)
        peak=max(q['post_minus6_peak_db'] for q in r['ac_by_load'].values())
        para(fig,.076,f'三负载均只有一次下降交越，之后直到300 MHz都低于0 dB。首次跌破−6 dB后仍有高频峰值，最坏{peak:.2f} dB；因此PM大并不代表不存在高频再抬升，回穿守卫必须保留。',9)
        save(pdf,fig)
        fig=page('精确电路与可复用认识',4,'RCP、RCN决定共栅余量；补偿电容返回位置决定电流反馈路径。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.866,body,fontsize=7.9,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.36)
        para(fig,.475,'设计认识：低阻f2节点由PMOS共栅管传递补偿电流，避免把CC直接接到高阻stage1形成相同的前馈路径。输入gm约0.359 mS、CC6.8 pF，gm/(2πCC)≈8.41 MHz，与20 pF实测8.375 MHz一致；这是近似选值依据，三负载相位仍来自仿真。',9.4)
        para(fig,.334,'初版外部指标虽已通过，底部镜管却进入线性区，削弱级联镜增益；保留失败工作点与最终修正，有助于区分“测量恰好通过”和“偏置符合设计意图”。PVT未验证，不把96 mV余量称为全角落保证。',9.3)
        para(fig,.21,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python\n scripts/case29_ahuja.py\nPDF：同一Python运行 scripts/review_pdf.py 29',8.7)
        para(fig,.128,'AC/DC：'+r['run_dirs'][0]+'\n动态：'+r['run_dirs'][1],8.3)
        para(fig,.078,'原任务：sky130-ahuja-compensated-two-stage-load-range-pvt。\n合同、LUT哈希和原始PSF见模块与runs目录。',8.3)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(29,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
