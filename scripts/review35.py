"""Self-contained review PDF for the deterministic nominal FD Miller amplifier."""
from review_pdf import *

def make35():
    case=ROOT/'cases/35-fd-miller';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values'];runs={k:ROOT/x for k,x in r['runs_by_analysis'].items()}
    a=data(runs['ac'],'ac.ac');h=a['voutp']-a['voutn'];n=data(runs['noise'],'noise.noise',required=('in','out'));d=data(runs['range'],'swing.dc');t=data(runs['settling'],'tran.tran');c=data(runs['cm'],'tran.tran');cm=data(ROOT/r['cm_loop_diagnostic']['run_dir'],'cmstb.stb');ch=-cm['loopGain'];out=ROOT/'reports/35-fd-miller-review.pdf'
    with PdfPages(out,metadata={'Title':'35 SMIC18 全差分两级Miller运放审查报告','Author':'SMIC18 benchmark reproduction','Subject':'Deterministic nominal only; original20-seed mismatch rejection excluded'}) as pdf:
        fig=page('35 | 全差分两级 Miller 运放审查',1,'结论：确定性 nominal 原门槛全部通过；原20种子失配拒斥试验未执行。')
        para(fig,.854,'条件：SMIC18MMRF / tt / 1.8 V / 27°C，50 uA参考，输入共模0.9 V，每侧1 pF。30只MOS；折叠共栅第一级、对称共源输出级、每侧2 pF/400 Ω Miller支路。',9.3)
        specs=[('差模增益 @10Hz','gain_db',1,'dB'),('差模UGB','ugb_hz',1e-6,'MHz'),('差模相位裕量','phase_margin_deg',1,'deg'),('输出共模误差','cm_error_V',1e3,'mV'),('输出差分不平衡','balance_error_V',1e6,'uV'),('VDD功耗，含参考','power_W',1e3,'mW'),('输入噪声 10Hz–15MHz','input_noise_Vrms',1e6,'uVrms'),('连续有效差分范围','range_Vpp',1,'Vpp'),('范围内最大跟踪误差','range_tracking_error_V',1e3,'mV'),('差模最后容差交越','settling_s',1e9,'ns'),('320ns终值误差/目标','settling_error_fraction',100,'%'),('CM最后容差交越','cm_recovery_s',1e9,'ns'),('1us共模终值误差','cm_final_error_V',1e3,'mV')]
        rows=[]
        for label,key,k,u in specs:
            q=r['gates'][key];sign='≥' if q['sense']=='min' else '≤';rows.append([label,f"{q['value']*k:.4f}",*[f"{sign}{q['limits'][tier]*k:.3f}" for tier in ['original','10pct','15pct']],u])
        table(fig,[.07,.312,.86,.476],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.15,.14,.14,.14,.12],8.1)
        para(fig,.275,'完整321点命令−0.8～+0.8 V、步长5 mV均通过5 mV跟踪窗，连续有效范围1.6 Vpp。差模AC额外检查只有一次下降0 dB交越、此后不回穿；功耗为正，数据完整且有限。',9.2)
        para(fig,.176,'独立CM STB：UGB47.674 MHz、PM51.147°，满足45°诊断下限。主表的60°门槛对应差模PM。全部30只MOS在中心OP有正的饱和余量。',9.2)
        para(fig,.083,'范围边界：其余PVT、20个固定种子local-mismatch、版图寄生与无源变化未执行。匹配CMRR/PSRR只作数值表征，不能替代原失配验收，也不能把nV级平衡推广到失配。',9)
        save(pdf,fig)

        fig=page('架构、尺寸与目标工艺LUT',2,'所有偏置从iref生成；DUT中仅MOS及正值R/C，没有内部独立或受控源。')
        ax=fig.add_axes([.07,.70,.86,.175]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3.7))
        for x,w,label in [(0,2.7,'NMOS差分输入\nPMOS折叠/共栅'),(3.6,2.7,'stagep / stagen\nNMOS共栅/受控下拉'),(7.3,2.7,'对称NMOS共源\n固定PMOS负载')]:
            ax.add_patch(Rectangle((x,1.55),w,1.4,fill=False,edgecolor=BLUE,lw=1.1));ax.text(x+w/2,2.25,label,ha='center',va='center',fontsize=8.7)
        for x0,x1 in [(2.7,3.6),(6.3,7.3)]:ax.annotate('',xy=(x1,2.25),xytext=(x0,2.25),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.plot([4.95,4.95,9.75,9.75],[1.55,.6,.6,1.55],color=GREEN);ax.text(7.2,.80,'each: 400 ohm + 2 pF Miller',ha='center',fontsize=8.7,color=GREEN)
        ax.text(.1,.7,'VOUT average -> CM amp -> first-stage sinks',fontsize=8.5)
        ax.text(.1,3.28,'VINP -> VOUTP; VINN -> VOUTN',fontsize=8.5)
        roles=[('input','MINP/MINN','10'),('n_bias','REF/TAIL/偏置/受控下拉','5/20/1/5'),('p_bias','偏置/折叠源/CM镜','1/15/5,10'),('n_cascode','MDN / MNCP,MNCN','1 / 5'),('p_cascode','MDP / MPCP,MPCN','1 / 5'),('second','MSECONDP/MSECONDN','70'),('output_load','MOBP / MLOADP,MLOADN','1 / 70'),('cm_input','MCMREF/MCMSENSE','5')]
        rows=[]
        for key,label,m in roles:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:g}",f"{q['ft_Hz']/1e6:.0f}"])
        table(fig,[.07,.35,.86,.30],['器件角色','模型','单位W/L um','m','gm/ID','LUT fT MHz'],rows,[.31,.09,.17,.18,.11,.14],8)
        para(fig,.308,'gm/ID初值：输入L=1 um、gm/ID=18、每侧100 uA，gm1≈1.8 mS；Cc=2 pF给出gm1/(2πCc)≈143 MHz。输出L=0.36 um、gm/ID=6、目标700 uA，gm2≈4.2 mS，400 Ω大于1/gm2，串联零点移到左半平面。',9.3)
        para(fig,.174,'全部单位W≤10.26 um；总宽较大的输入/PMOS输出以m复制。NMOS输出单位W=0.30 um、m=70，仍在模型范围内；LUT Wref=10 um只作初值，实际OP已包含窄宽效应与体偏置。',9.2)
        para(fig,.079,'LUT使用既有gmoverid_smic18/lut/tt；每个查询的VDS、L、温度、体偏置、源路径与SHA-256保存在sizing.json。无需补扫，没有改动PDK、Bridge或原LUT。',9)
        save(pdf,fig)

        fig=page('实际工作点与CMFB修正',3,'CMFB动作节点的阻抗和偏置平衡共同影响恢复；原动态门槛通过仍须检查环路。')
        rows=[]
        for name in ['MINP','MTAIL','MSP','MPCP','MNCP','MSINKP','MSECONDP','MLOADP','MCMSENSE','MCMND']:
            q=r['operating_point'][name];rows.append([name,f"{abs(q['ids'])*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['gmro']:.2f}",f"{abs(q['vds']):.4f}",f"{q['headroom_V']*1e3:.2f}"])
        table(fig,[.07,.53,.86,.325],['器件','|Id|/uA','gm/ID','gm/gds','|VDS|/V','饱和余量/mV'],rows,[.22,.16,.15,.16,.15,.16],8.4)
        para(fig,.491,'中心节点：tail=0.34531 V，fp/fn=1.39783 V，stagep/stagen=0.69318 V，sinkp/sinkn=0.28708 V；vcmfb=0.52037 V。输出每侧732.06 uA，主输入98.77 uA。余量=|VDS|−|VDSAT|；不是全PVT保证。',9.2)
        rows=[['CM镜比1.2，初版','11.215','0.1533','13.680°','8.254','31.387'],['CM镜比2.0，最终','56.073','0.7665','51.147°','3.638','14.163']]
        table(fig,[.07,.297,.86,.12],['版本','ND电流/uA','ND gm/mS','CM PM','CM误差/mV','恢复/ns'],rows,[.29,.15,.15,.14,.14,.13],8.1)
        para(fig,.258,'CM镜的额外上拉电流流过二极管NMOS MCMND，后者与一阶受控下拉近似匹配电流密度。镜比从1.2改为2.0，同时把ND的m从1增至5，使动作节点近似1/gm由6.52 kΩ降到1.30 kΩ；独立CM UGB从87.88降到47.67 MHz，PM从13.68°升到51.15°。',9.2)
        para(fig,.111,'CM极性：输出平均值升高→MCMSENSE下拉增强、镜像上拉减小→vcmfb下降→第一阶段下拉减小→stagep/stagen上升→输出NMOS电流上升→输出均值下降。该修正保留晶体管级连续反馈。',9.2)
        save(pdf,fig)

        fig=page('频率、噪声与共模环路证据',4,'差模增益/PM、闭环输入噪声和CM STB使用各自正确的连接与测量定义。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.22,top=.85,hspace=.38,wspace=.34)
        axs[0,0].semilogx(a['freq'],20*np.log10(abs(h)),color=BLUE);axs[0,0].axhline(0,color=GRAY,lw=.7);axs[0,0].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Differential gain (dB)',xlim=(10,1e10))
        axs[0,1].semilogx(a['freq'],np.unwrap(np.angle(h))*180/np.pi,color=BLUE);axs[0,1].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Differential phase (deg)',xlim=(10,1e10))
        axs[1,0].loglog(n['freq'],abs(n['in'])*1e9,color=BLUE);axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Input noise (nV/sqrt(Hz))',xlim=(10,15e6))
        axs[1,1].semilogx(cm['freq'],np.unwrap(np.angle(ch))*180/np.pi,color=BLUE);axs[1,1].axvline(r['cm_loop_diagnostic']['ugb_hz'],color=GREEN,ls='--');axs[1,1].axhline(-180,color=GRAY,lw=.7);axs[1,1].set(xlabel='Frequency (Hz)',ylabel='CM loop phase (deg)',xlim=(1,1e10))
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.178,'差模AC输入±0.5 V，H=Voutp−Voutn，10 Hz取增益；首次下降交越计算UGB/PM。噪声是单位差分闭环的输入等效谱，积分sqrt(∫en²df)，频带严格10 Hz–15 MHz；没有把UGB当成噪声积分上限。',9.2)
        para(fig,.086,'噪声含619个频点；线性频率梯形积分与PSD幂律插值积分相差0.00095%。CM用感测节点到MCMSENSE栅的零压探针；图取−loopGain，51.1473°与Spectre原生51.1477°一致。',9.2)
        save(pdf,fig)

        fig=page('完整范围与动态目标',5,'最后容差交越从20 ns边沿开始计；差模固定2 mV窗，共模固定15 mV窗。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.23,top=.85,hspace=.42,wspace=.35)
        cmd=d['src'];yd=d['voutp']-d['voutn'];axs[0,0].plot(cmd,cmd,color=GRAY,ls='--',label='Command');axs[0,0].plot(cmd,yd,color=BLUE,label='Output');axs[0,0].set(xlabel='Differential command (V)',ylabel='Differential output (V)',xlim=(-.8,.8));axs[0,0].legend(fontsize=7)
        axs[0,1].plot(cmd,(yd-cmd)*1e6,color=BLUE);axs[0,1].set(xlabel='Differential command (V)',ylabel='Tracking error (uV)',xlim=(-.8,.8))
        tt=(t['time']-20e-9)*1e9;td=t['voutp']-t['voutn'];axs[1,0].plot(tt,t['src'],color=GRAY,ls='--',label='Command');axs[1,0].plot(tt,td,color=BLUE,label='Output');axs[1,0].axhspan(.198,.202,color=GREEN,alpha=.16);axs[1,0].axvline(v['settling_s']*1e9,color=GREEN,ls='--');axs[1,0].set(xlim=(-3,35),xlabel='Time after edge start (ns)',ylabel='Differential output (V)');axs[1,0].legend(fontsize=7)
        ct=(c['time']-20e-9)*1e9;cy=(c['voutp']+c['voutn'])/2;axs[1,1].plot(ct,c['vocm'],color=GRAY,ls='--',label='VOCM');axs[1,1].plot(ct,cy,color=BLUE,label='Output CM');axs[1,1].axhspan(.935,.965,color=GREEN,alpha=.16);axs[1,1].axvline(v['cm_recovery_s']*1e9,color=GREEN,ls='--');axs[1,1].set(xlim=(-3,100),xlabel='Time after edge start (ns)',ylabel='Output common mode (V)');axs[1,1].legend(fontsize=7)
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=7.5)
        para(fig,.183,'差模−0.2→+0.2 V、20–21 ns线性边沿；误差窗为最终目标0.2 V的1%，即2 mV。全波形末次容差交越线性插值后减20 ns，得到9.356 ns。320 ns瞬时终值误差0.4807 uV，不以实际终值重新居中。',9.2)
        para(fig,.087,'VOCM 0.85→0.95 V、同样1 ns边沿，零差分输入保持0.9 V。15 mV窗的末次交越减20 ns为14.163 ns；观察至1 us，终值误差4.971 mV≤10 mV。图仅放大边沿，提取扫描完整观察窗。',9.2)
        save(pdf,fig)

        fig=page('最终精确晶体管网表',6,'D G S B端序；共栅PMOS体端各接源端，物理设计必须保留相应独立井。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.862,body,fontsize=8.05,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.30)
        para(fig,.222,'第一阶段PMOS固定源与NMOS输入电流之差流入折叠支路；连续CMFB调节两个底部下拉。输出为两组NMOS共源与PMOS固定电流负载，Miller支路直接从各输出返回各自stage节点。',9.3)
        para(fig,.116,'精确尺寸、m、总宽与端序另见geometry.json；最终circuit.scs SHA-256：\n'+sha(case/'circuit.scs'),8)
        save(pdf,fig)

        fig=page('拒斥范围边界、提取与复现',7,'原20种子随机失配要求未执行；下面保留匹配nominal激励的原始结果，不能作为实际拒斥承诺。')
        rows=[]
        for label,key in [('CMRR','CMRR'),('PSRR+','PSRR_plus'),('PSRR−','PSRR_minus')]:
            q=r['matched_rejection'][key];lim=q['original_mismatch_limit_dB'];rows.append([label,f"{q['10']['disturbance_to_differential_gain']:.3e}",f"{q['10']['rejection_db']:.2f}",f"≥{lim:g}",f"≥{lim+20*np.log10(.9):.3f}",f"≥{lim+20*np.log10(.85):.3f}"])
        table(fig,[.07,.718,.86,.135],['指标','10Hz扰动→差模 V/V','形式计算dB','原失配门槛','10%边界','15%边界'],rows,[.12,.25,.17,.17,.15,.14],8.1)
        para(fig,.680,'三个超高dB数值来自理想匹配对称性与求解/输出精度残差。1 MHz时三种扰动的差分残差均为0，dB未定义；没有把零残差改成任意大“通过”数值。20个固定种子41000–41019均未运行，此项明确排除。',9.3)
        para(fig,.556,'CMRR/PSRR定义为差模信号增益与相应扰动到差分输出增益之比。负电源测试令VSS AC=+1、VDD对VSS AC=−1，使绝对VDD不动；输入及VOCM相对VSS保持原bench连接。不是输出共模抑制比。',9.3)
        para(fig,.433,'原instruction、参考电路、verify.py、utils.py和六套bench均已冻结。提取按bench的.meas定义适配PSF，并用原verifier的nominal_functional/threshold函数核对标量门槛；不运行原PVT/MC调度。差模采样50 ps、CM采样100 ps，内部最大步长25/50 ps。',9.3)
        para(fig,.312,'复现（工程根目录）：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case35_fd_miller.py\n同一Python运行 scripts/review_pdf.py 35 生成PDF。\n原任务：sky130-fd-two-stage-miller-opamp-gain60-pm60-noise50uv-pvt',8.5)
        para(fig,.202,'最终运行（依次AC、noise、range、settling、CM、rejection、CM STB）：\n'+'\n'.join(r['run_dirs']+[r['cm_loop_diagnostic']['run_dir']]),7.6)
        para(fig,.079,'每个run.json保存模型与输入哈希；inputs/与原始PSF保留。仅nominal原理图，不含剩余PVT、失配、寄生与无源容差。',8)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),geometry_sha256=sha(case/'geometry.json'),generated_at=now(),pages=7,render_review_pending=True))
    update_case(35,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

if __name__=='__main__':print(make35())
