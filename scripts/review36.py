"""Review PDF for the fully differential telescopic OTA."""
from review_pdf import *

def block(ax,x,y,w,h,label,color=BLUE,size=8):
    ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor=color,lw=1.1))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=size,color=color)

def make36():
    case=ROOT/'cases/36-telescopic';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());g=json.loads((case/'geometry.json').read_text());v=r['values']
    runs=[ROOT/x for x in r['run_dirs']];a=data(runs[0],'ac.ac');d=data(runs[1],'swing.dc');t=data(runs[2],'tran.tran');c=data(runs[3],'tran.tran');cm=data(ROOT/r['cm_loop_diagnostic']['run_dir'],'cmstb.stb')
    h=a['voutp']-a['voutn'];ch=-cm['loopGain'];out=ROOT/'reports/36-telescopic-review.pdf'
    with PdfPages(out,metadata={'Title':'36 SMIC18 全差分Telescopic OTA审查报告','Author':'SMIC18 benchmark reproduction','Subject':'Measured schematic nominal results; no PVT/mismatch claim'}) as pdf:
        fig=page('36 | 全差分 Telescopic OTA 审查',1,'结论：四组原始 nominal 电气验收全部通过，无需10%–15%放宽。')
        para(fig,.858,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；50 uA参考；输入共模0.9 V；每侧2 pF负载。23只MOS、连续时间CMFB与VOCM跟踪偏置；无数字逻辑。',9.5)
        specs=[('差模增益 @1Hz','dc_gain_db',1,'dB'),('差模UGB','ugb_hz',1e-6,'MHz'),('差模相位裕量','phase_margin_deg',1,'deg'),('开环输出CM误差','output_common_mode_error_v',1e3,'mV'),('VDD总功耗，含参考','power_w',1e3,'mW'),('181点差模跟踪误差','closed_loop_tracking_error_v_max',1e3,'mV'),('181点最大CM误差','closed_loop_common_mode_error_v_max',1e3,'mV'),('差模最后进入时间','settling_time_s',1e9,'ns'),('差模末10ns均值误差','settling_static_error_v',1e3,'mV'),('差模终值误差/阶跃','settling_error_fraction',100,'%'),('CM最后进入时间','cm_recovery_time_s',1e9,'ns'),('CM末20ns均值误差','cm_recovery_final_error_v',1e3,'mV')]
        rows=[]
        for label,key,k,u in specs:
            q=r['gates'][key];sign=q.get('comparison','≥' if q['sense']=='min' else '≤')
            rows.append([label,f"{q['value']*k:.4f}",*[f"{sign}{q['limits'][tier]*k:.3f}" for tier in ['original','10pct','15pct']],u])
        table(fig,[.07,.344,.86,.447],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.15,.14,.14,.14,.12],8.2)
        para(fig,.31,'不放宽检查：完整181点，−0.45～+0.45 V、步长5 mV；完整0.90 Vpp。1 Hz～10 GHz内恰好一次下降0 dB交越，此后均低于0 dB；功耗非负，全部数据有限。',9.5)
        para(fig,.211,f"独立CM环路：UGB={r['cm_loop_diagnostic']['ugb_hz']/1e6:.3f} MHz，PM={r['cm_loop_diagnostic']['phase_margin_deg']:.3f}°，高于45°诊断下限。\n与Spectre原生PM之差小于0.002°。",9.5)
        para(fig,.11,'本次仅nominal原理图验证。未执行其余26个PVT点、Monte Carlo、噪声、抑制比或版图寄生；“原始通过”指原阈值在本次nominal条件下通过。',9.3)
        save(pdf,fig)

        fig=page('信号结构、gm/ID与工作点',2,'NMOS输入与尾源、上下共栅级、PMOS顶电流源；CMFB独立调节两侧上拉。')
        ax=fig.add_axes([.07,.69,.86,.19]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,4.5))
        for x,inp,outp,pc,pt,nc in [(0.3,'vinp','voutn','MPCN','MPTN','MNCP'),(4.1,'vinn','voutp','MPCP','MPTP','MNCN')]:
            block(ax,x,3.38,2.25,.55,pt+' p18 / vctrl');block(ax,x,2.57,2.25,.55,pc+' p18 / vbpc');block(ax,x,1.30,2.25,.55,nc+' n18 / vcn');block(ax,x,.49,2.25,.55,'MIN'+('P' if inp=='vinp' else 'N')+' n18 / '+inp)
            ax.plot([x+1.125,x+1.125],[1.85,2.57],color=BLUE);ax.text(x+1.25,2.18,outp,fontsize=8)
            ax.plot([x+1.125,x+1.125],[3.12,3.38],color=BLUE);ax.plot([x+1.125,x+1.125],[1.04,1.30],color=BLUE)
        ax.text(3.3,4.22,'VDD = 1.8 V',ha='center',fontsize=9);ax.text(3.3,.02,'shared MTAIL -> VSS',ha='center',fontsize=9)
        block(ax,7.15,2.65,2.6,1.18,'R/C average\n(voutp+voutn)/2',size=8.5)
        block(ax,7.15,.62,2.6,1.43,'CM error amplifier\ncompare VOCM\noutput vctrl',GREEN,8.5)
        ax.annotate('',xy=(8.45,2.05),xytext=(8.45,2.65),arrowprops=dict(arrowstyle='->',color=GREEN))
        ax.text(6.93,4.08,'CC+RZ: vctrl -> each output',fontsize=7.6,color=GREEN)
        roles=[('input','MINP/MINN; MR1','14; 1'),('n_bias','REF/TAIL/T1/T4/T5/CMT','5/28/2/1/1/2'),('n_cascode','MNCP/MNCN; MD1','14; 1'),('p_cascode','MPCN/MPCP; MDP1','14; 1'),('p_top','PTN/PTP; PB2/PM/CML/CMLO','14; 1'),('cm_input','MCMS/MCMR','1')]
        rows=[]
        for key,label,m in roles:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:g}",f"{q['ft_Hz']/1e6:.0f}"])
        table(fig,[.07,.439,.86,.215],['器件角色','模型','单位W/L um','m','gm/ID','LUT fT MHz'],rows,[.30,.09,.16,.22,.10,.13],7.8)
        rows=[]
        for name in ['MINP','MTAIL','MNCP','MPCN','MPTN','MCMS']:
            q=r['operating_point'][name];rows.append([name,f"{abs(q['ids'])*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['gmro']:.2f}",f"{abs(q['vds']):.4f}",f"{q['headroom_V']*1e3:.2f}"])
        table(fig,[.07,.199,.86,.205],['实测工作点','|I|/uA','gm/ID','gm/gds','|VDS|/V','余量/mV'],rows,[.2,.17,.15,.16,.16,.16],8.4)
        para(fig,.165,'余量=|VDS|−|VDSAT|；全部23只MOS在中心工作点均有正余量。信号支路138.245 uA。LUT零体偏置作初值，实际输入管有0.343 V体偏置；gm/ID=18.067确认实际跨导效率。',9)
        para(fig,.076,'LUT：gmoverid_smic18/lut/tt；原表与SHA-256保存在sizing.json。单位W最大14.24 um；超100 um总宽由m复制实现，模型没有尺寸越界警告。',8.8)
        save(pdf,fig)

        fig=page('差模与共模频率证据',3,'两种环路分别提取。差模高相位裕量不能代替CMFB稳定性验证。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.24,top=.845,hspace=.36,wspace=.35)
        for col,freq,resp,label,ugb in [(0,a['freq'],h,'Differential',v['ugb_hz']),(1,cm['freq'],ch,'Common mode',r['cm_loop_diagnostic']['ugb_hz'])]:
            axs[0,col].semilogx(freq,20*np.log10(abs(resp)),color=BLUE);axs[0,col].axhline(0,color=GRAY,lw=.8);axs[0,col].axvline(ugb,color=GREEN,ls='--',lw=.9)
            axs[0,col].set(xlim=(1,1e10),xlabel='Frequency (Hz)',ylabel='Gain (dB)',title=label)
            axs[1,col].semilogx(freq,np.unwrap(np.angle(resp))*180/np.pi,color=BLUE);axs[1,col].axvline(ugb,color=GREEN,ls='--',lw=.9);axs[1,col].axhline(-180,color=GRAY,lw=.8)
            axs[1,col].set(xlim=(1,1e10),xlabel='Frequency (Hz)',ylabel='Phase (deg)')
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.193,'差模：VINP AC=+0.5 V、VINN AC=−0.5 V，H=Voutp−Voutn，单位差分输入。按原verifier在对数频率上插值首个下降0 dB交越；相位由复数响应展开。扫描每十倍频100点。',9.5)
        para(fig,.093,'共模：在vcm_sense与MCMS栅之间插入零压iprobe，记录Spectre STB。图取−loopGain以统一低频相位为0°；同一符号约定给出67.077° PM，与Spectre原生日志一致。插入探针前后输出OP差小于1 pV。',9.2)
        save(pdf,fig)

        fig=page('完整闭环范围与两类动态',4,'每侧负载保持2 pF；所有曲线来自最终相同的电路快照。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.23,top=.85,hspace=.42,wspace=.35)
        cmd=d['err0'];yd=d['voutp']-d['voutn'];yc=(d['voutp']+d['voutn'])/2
        axs[0,0].plot(cmd,cmd,color=GRAY,ls='--',label='Command');axs[0,0].plot(cmd,yd,color=BLUE,label='Output');axs[0,0].set(xlabel='Differential command (V)',ylabel='Differential output (V)',xlim=(-.45,.45));axs[0,0].legend(fontsize=7)
        axs[0,1].plot(cmd,(yd-cmd)*1e3,label='Differential error');axs[0,1].plot(cmd,(yc-.9)*1e3,label='CM error');axs[0,1].set(xlabel='Differential command (V)',ylabel='Error (mV)',xlim=(-.45,.45));axs[0,1].legend(fontsize=7)
        tt=(t['time']-21e-9)*1e9;dd=(t['voutp']-t['voutn'])*1e3
        axs[1,0].plot(tt,t['err0']*1e3,label='Command',color=GRAY,ls='--');axs[1,0].plot(tt,dd,label='Output',color=BLUE);axs[1,0].axhspan(49,51,color=GREEN,alpha=.15);axs[1,0].axvline(v['settling_time_s']*1e9,color=GREEN,ls='--');axs[1,0].set(xlim=(-3,25),xlabel='Time after command endpoint (ns)',ylabel='Differential voltage (mV)');axs[1,0].legend(fontsize=7)
        ct=(c['time']-21e-9)*1e9;cy=(c['voutp']+c['voutn'])/2
        axs[1,1].plot(ct,c['vocm'],label='VOCM',color=GRAY,ls='--');axs[1,1].plot(ct,cy,label='Output CM',color=BLUE);axs[1,1].axhspan(.945,.955,color=GREEN,alpha=.15);axs[1,1].axvline(v['cm_recovery_time_s']*1e9,color=GREEN,ls='--');axs[1,1].set(xlim=(-3,139),xlabel='Time after command endpoint (ns)',ylabel='Common-mode voltage (V)');axs[1,1].legend(fontsize=7)
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=7.5)
        para(fig,.187,'差模阶跃−50→+50 mV，20–21 ns线性边沿；从21 ns起算，最后进入固定±1 mV窗为6.75 ns。\n观察至140 ns，最后10 ns均值距理想+50 mV为12.42 uV。无重新居中。',9.2)
        para(fig,.094,'VOCM阶跃0.85→0.95 V、同样1 ns边沿；零差分输入保持0.9 V。最后进入固定±5 mV窗为23.0 ns。\n观察至160 ns，末20 ns均值误差1.304 mV。这是有限观察窗指标，不能当作无限时间DC失调。',9.2)
        save(pdf,fig)

        fig=page('最终精确晶体管网表',5,'D G S B端序；MPCN/MPCP及其复制管的体端跟随源端；外部供电与激励均在bench中。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.861,body,fontsize=8.25,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.4)
        para(fig,.255,'偏置节点（中心OP）：tail=0.34288 V，a1/a2=0.55585 V，pn/pp=1.55080 V；\nvcn=1.18629 V，vbpc=0.99592 V，vctrl=1.23665 V。RN复制输入源电位再抬高约0.20 V；RP设定PMOS顶管压降约0.24 V。',9.3)
        para(fig,.145,'CMFB极性：输出均值上升→MCMS电流增加→PMOS镜提供更多vctrl上拉，同时MCMR下拉减小→vctrl上升→主PMOS电流减小→输出均值下降。CC/RZ同时影响CM补偿与差模负载。',9.3)
        para(fig,.085,'精确尺寸和端序另见geometry.json；circuit.scs SHA-256：\n'+sha(case/'circuit.scs'),7.6)
        save(pdf,fig)

        fig=page('失败迭代、测量口径与复现',6,'保留失败证据；没有把仅差模通过的初版记为完成。')
        rows=[['初版','100 / 0.39 / 3k / 1','7.00','未进入窗','CM PM32.90°；尾窗6.731mV'],['第二版','100 / 0.6 / 15k / .36','14.25','135.35','此RZ/CC组合失败；CM PM14.76°'],['最终','140 / 1.0 / 1k / .36','6.75','23.00','全部原nominal通过；CM PM67.08°']]
        table(fig,[.07,.701,.86,.153],['版本','支路uA/CCpF/RZΩ/CM Lμm','DM ns','CM ns','结果'],rows,[.10,.35,.11,.11,.33],7.9)
        para(fig,.662,'关键修正：CM感测输入管由L=1 um改为0.36 um，降低其门电容对RC平均节点的瞬态衰减；CC增至1 pF并将RZ取1 kΩ，稳定共模环路。支路电流从100增到140 uA，补回差模驱动能力。',9.4)
        para(fig,.548,'181点DC保持外部理想反馈：err=command−(Voutp−Voutn)，vinp/vinn=VOCM±err/2。动态由原冻结verifier取“命令首次到终值后，之后全在窗内的首个输出样本”。最大内部步长25 ps，输出采样50 ps；均值按采样点算术平均。',9.3)
        para(fig,.425,'提取直接复用source/tests/verify.py的AC、范围、建立、CM恢复函数，输入改为经过长度/有限值/顺序校验的Spectre PSF复数向量；保留严格>/<及≤边界。差模增益是幅度dB，放宽时加20log10(0.9/0.85)。',9.3)
        para(fig,.314,'复现（工程根目录）：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case36_telescopic.py\n同一Python运行 scripts/review_pdf.py 36 生成本PDF。\n原任务：sky130-telescopic-cascode-ota-pvt-fix',8.7)
        para(fig,.202,'最终原始运行：\n'+'\n'.join(r['run_dirs'])+'\n'+r['cm_loop_diagnostic']['run_dir'],7.8)
        para(fig,.072,'每个run.json保留电路/bench/模型哈希和冻结输入；cases/36-telescopic/source保留源合同、正式verifier与bench。未运行PVT、失配、版图或无源工艺变化。',8.5)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),geometry_sha256=sha(case/'geometry.json'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(36,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

if __name__=='__main__':print(make36())
