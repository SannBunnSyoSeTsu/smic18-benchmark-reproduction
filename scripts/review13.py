from review_pdf import *

def make13():
    case=ROOT/'cases/13-constant-gm';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values'];runs=[ROOT/x for x in r['run_dirs']]
    a=data(runs[0],'ac.ac');l=data(runs[0],'linearity.dc');d=data(runs[1],'tran.tran');out=ROOT/'reports/13-constant-gm-review.pdf'
    with PdfPages(out,metadata={'Title':'13 SMIC18 恒跨导增益放大器审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('13 | 恒跨导增益放大器审查',1,'结论：原nominal增益、带宽、功耗、线性度和零能量冷启动均通过。')
        para(fig,.863,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；IREF=50 uA；输入共模0.95 V；每端负载500 fF。自偏置β倍增环产生输入跨导，电阻负载把差分电流转换为电压。')
        rows=[['1MHz差分增益',f"{v['gain_1mhz']:.5f}",'3.0–4.0','2.95–4.05','2.925–4.075','V/V'],['−3dB带宽',f"{v['bandwidth_Hz']/1e6:.4f}",'≥30','≥27','≥25.5','MHz'],['VDD−输出共模',f"{v['load_drop_V']*1e3:.3f}",'150–400','137.5–412.5','131.25–418.75','mV'],['确定性输出不平衡',f"{v['imbalance_V']*1e3:.3g}",'≤10','≤11','≤11.5','mV'],['总VDD功耗',f"{v['power_W']*1e6:.3f}",'≤500','≤550','≤575','uW'],['最坏增量增益误差',f"{v['linearity_error']*100:.4f}",'≤8','≤8.8','≤9.2','%']]
        table(fig,[.07,.486,.86,.258],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.30,.16,.15,.15,.15,.09],8.2)
        st=v['startup'];rows=[['8–9us零输入不平衡',f"{st['zero_imbalance_V']*1e3:.3g} mV",'≤10 mV'],['14–15us绝对阶跃增益',f"{st['step_gain']:.5f} V/V",'3.0–4.0 V/V'],['零输入负载压降',f"{st['zero_load_drop_V']*1e3:.3f} mV",'150–400 mV'],['阶跃后负载压降',f"{st['step_load_drop_V']*1e3:.3f} mV",'150–400 mV'],['全部已存节点初值',f"{st['initial_max_node_V']:g} V",'零能量初态']]
        table(fig,[.07,.229,.86,.2],['冷启动合同','实测','原门槛'],rows,[.45,.30,.25],9)
        para(fig,.185,'增益和共模范围按“固定中心、扩大误差窗口”放宽，未直接乘上下限。冷启动增益是阶跃后的绝对差分输出除20 mV，不能先减去零输入失调来掩盖不平衡。',9.4)
        para(fig,.078,'只完成nominal点；未把单点增益写成27点PVT的max/min≤1.15证明，也未执行统计失配。零不平衡限于对称确定性模型。',9.2)
        save(pdf,fig)
        fig=page('β倍增环、尺寸与实际工作点',2,'同一NMOS单位用于主偏置、尾源和差分对；宽度专属LUT修正启动支路。')
        ax=fig.add_axes([.07,.712,.86,.16]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3.5))
        for x,y,w,h,label in [(0,1.5,2.3,1.25,'50 uA参考\n弱启动下拉'),(3.2,1.5,2.9,1.25,'β倍增自偏置\nK=4, RB=1.45 kΩ'),(7.1,1.5,2.9,1.25,'差分对 + 电阻负载\nRL=5.6 kΩ each')]:
            ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor=BLUE));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=8.8)
        for x1,x2 in [(2.3,3.2),(6.1,7.1)]:ax.annotate('',xy=(x2,2.1),xytext=(x1,2.1),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.text(3.3,.57,'自偏置电流由器件及RB共同决定；IREF用于参考终端与启动。',fontsize=9)
        rows=[]
        for key,label,m in [('n_master_input','MB1/MB2/TAIL/IN±','1 / 4 / 2 / 1'),('p_mirror','MP1/MP2','1'),('reference','MREF','1'),('startup','MST','1')]:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:.2f}"])
        table(fig,[.07,.51,.86,.155],['器件角色','模型','单位W/L(um)','m','目标gm/ID'],rows,[.31,.10,.20,.23,.16],8.4)
        rows=[]
        for key in ['MB1','MB2','MP1','MP2','MTAIL','MINP','MST']:
            q=r['operating_point'][key];rows.append([key,f"{abs(q['ids'])*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['headroom_V']*1e3:.1f}"])
        table(fig,[.07,.239,.86,.22],['实际工作点','|I| / uA','gm/ID','饱和余量/mV'],rows,[.25,.25,.25,.25],8.8)
        para(fig,.191,'主支47.00 uA、输入46.39 uA/支。输入实际gm=0.6512 mS、gm/ID=14.04，接近目标14；体偏置使其VGS=0.6080 V，高于主管0.5182 V，但单位电流密度仍接近。',9.4)
        para(fig,.087,'启动管W0.24/L4 um：专属LUT预测gm/ID=8.558、I=0.3755 uA；实际8.591、0.3720 uA。它启动后持续导通，已计入功耗。',9.3)
        save(pdf,fig)
        fig=page('频响、线性度与冷启动证据',3,'供电、输入共模和参考电流分别按原题时序上升。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.215,top=.845,hspace=.44,wspace=.35)
        h=abs(a['voutp']-a['voutn']);axs[0,0].semilogx(a['freq'],h,color=BLUE);axs[0,0].axhline(v['gain_1mhz']/np.sqrt(2),color=GRAY,ls='--');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Differential gain (V/V)')
        axs[0,1].plot(l['vdtest']*1e3,(l['voutp']-l['voutn'])*1e3,color=BLUE);axs[0,1].plot(l['vdtest']*1e3,l['vdtest']*v['central_gain']*1e3,ls='--',color=GRAY);axs[0,1].set(xlabel='Differential input (mV)',ylabel='Differential output (mV)')
        for key,label in [('vdd','VDD'),('X.nb','Bias nb'),('X.nc','Bias nc')]:axs[1,0].plot(d['time']*1e6,d[key],label=label,lw=1)
        axs[1,0].set(xlim=(0,2),xlabel='Time (us)',ylabel='Voltage (V)');axs[1,0].legend(fontsize=8)
        axs[1,1].plot(d['time']*1e6,(d['voutp']-d['voutn'])*1e3,label='Output');axs[1,1].plot(d['time']*1e6,d['vd']*1e3,label='Input');axs[1,1].axvspan(8,9,color=GREEN,alpha=.1);axs[1,1].axvspan(14,15,color=GREEN,alpha=.1);axs[1,1].set(xlim=(7,16),xlabel='Time (us)',ylabel='Differential voltage (mV)');axs[1,1].legend(fontsize=8)
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.164,'VDD与VCM在0.1–1.1 us从0升至1.8/0.95 V；IREF在1.2–1.22 us从0升至50 uA。差分输入在10–10.02 us从0升至20 mV。skipdc=yes且所有节点初值为0；没有预置非零自偏置节点。',9.3)
        para(fig,.081,'DC扫描−60至+60 mV，每2 mV一点；中心增益由±2 mV差分计算，以±30/±60 mV相对零点的增量增益比较，最坏误差3.3834%。这不是SFDR或随机失配测试。',9.2)
        save(pdf,fig)
        fig=page('精确电路、修正与复现',4,'结构近似、目标工艺LUT和完整测试合同需要同时保留。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.856,body,fontsize=8.2,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.5)
        para(fig,.592,'RB=1.2 kΩ初版电流偏高：增益4.195、功耗520.1 uW，未满足完整原/放宽合同。保持W/L与RL，仅把RB调到1.45 kΩ，得到增益3.601、功耗424.4 uW，且冷启动与线性度仍通过。',9.5)
        para(fig,.467,'理想平方律与无体效应假设下可估gm≈1/RB；最终实测gm主管×RB≈0.942，不能把RL/RB=3.862直接当成实际增益。中等反型、体效应、镜支路VDS不同以及有限输出电导都使该关系出现偏差。',9.5)
        para(fig,.341,'最初用Wref10 um LUT选启动管gm/ID=12，却在W0.24 um下测得约8.59。补扫同W/L、VDS1.35 V的窄管表，以参考二极管预测栅压选点后得到8.558；最终尺寸不变，但依据已与实际几何一致。',9.4)
        para(fig,.218,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python\n scripts/case13_constant_gm.py\nPDF：同一Python运行 scripts/review_pdf.py 13',8.6)
        para(fig,.136,'AC/DC：'+r['run_dirs'][0]+'\n冷启动：'+r['run_dirs'][1],8.3)
        para(fig,.077,'原任务：sky130-constant-gm-stable-gain-amplifier-pvt。\n只声明nominal实测；PVT增益稳定性和随机失配仍未验证。',8.6)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(13,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
