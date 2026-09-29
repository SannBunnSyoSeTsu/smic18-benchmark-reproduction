"""Review PDF for the SMIC18 three-stage nested Miller nominal reproduction."""
from review_pdf import *

def make37():
    case=ROOT/'cases/37-nested-miller';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values'];runs={k:ROOT/x for k,x in r['runs_by_analysis'].items()}
    a=data(runs['pvt'],'ac.ac');h=-a['vout']/a['vinn'];d=data(runs['swing'],'swing.dc');t=data(runs['settling'],'tran.tran');z=data(runs['slew'],'tran.tran');out=ROOT/'reports/37-nested-miller-review.pdf'
    with PdfPages(out,metadata={'Title':'37 SMIC18 三级嵌套Miller OTA审查报告','Author':'SMIC18 benchmark reproduction','Subject':'Original five measurement groups at deterministic nominal only'}) as pdf:
        fig=page('37 | 三级嵌套 Miller OTA 审查',1,'结论：五组 nominal 检查全部达到原门槛，未用性能放宽；其余44个PVT点未执行。')
        para(fig,.854,'条件：SMIC18MMRF / tt / 1.8 V / 27°C，5 uA参考，输入共模和输出目标0.9 V，理想负载200 pF。16只MOS与8 pF/3 pF嵌套电容，所有偏置从iref产生。',9.3)
        specs=[('返回比增益 @0.1Hz','dc_gain_db',1,'dB'),('UGB','ugb_hz',1e-3,'kHz'),('相位裕量','phase_margin_deg',1,'deg'),('驱动效率 FOM','drive_fom_khz_pf_per_uw',1,'见下式'),('静态输出误差','output_common_mode_error_v',1e3,'mV'),('VDD总功耗，含参考','power_w',1e6,'uW'),('VINP DC电流绝对值','input_bias_vinp_a',1e9,'nA'),('VINN DC电流绝对值','input_bias_vinn_a',1e9,'nA'),('连续合格命令区间','closed_loop_range_vpp',1,'Vpp'),('0.4→0.9V建立时间','settling_time_s',1e6,'us'),('终值误差/0.5V阶跃','settling_error_fraction',100,'%'),('上升压摆率','slew_rise_v_per_us',1,'V/us'),('下降压摆率','slew_fall_v_per_us',1,'V/us')]
        rows=[]
        for label,key,k,u in specs:
            q=r['gates'][key];sign={'<':'<','<=':'≤','>=':'≥'}[q['comparison']];rows.append([label,f"{q['value']*k:.4f}",*[f"{sign}{q['limits'][tier]*k:.3f}" for tier in ['original','10pct','15pct']],u])
        table(fig,[.07,.307,.86,.48],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.15,.14,.14,.14,.12],8.1)
        para(fig,.268,'FOM = UGB(kHz) × 200 pF / 功耗(uW)；451.659 × 200 / 243.627 = 370.779 kHz·pF/uW。负载、输入幅度、观察窗、20 mV范围资格窗和10 mV建立窗均保持原定义。',9.2)
        para(fig,.175,'AC从0.01 Hz至100 MHz只有一次下降0 dB交越，之后不回穿。中心OP全部16只MOS有正的饱和余量，五次正式运行无模型尺寸警告。输入电流0是本模型读数，不是实际器件零泄漏承诺。',9.2)
        para(fig,.080,'范围边界：仅nominal原理图；其余PVT、局部失配、寄生、封装、老化和无源容差未运行。原任务也未要求局部失配；本报告不声称完成原45点PVT签核。',9)
        save(pdf,fig)

        fig=page('三级增益链、嵌套补偿与LUT',2,'保留参考架构：A1反相、A2非反相、A3反相；从VINP到输出总极性为正。')
        ax=fig.add_axes([.07,.658,.86,.218]);ax.axis('off');ax.set(xlim=(0,12),ylim=(-.2,4.2))
        for x,w,label in [(0,3,'A1 NMOS差分对\nPMOS镜负载'),(4.25,3.2,'A2 NMOS共源\nPMOS电流镜'),(8.55,3,'A3 NMOS共源\nPMOS固定源')]:
            ax.add_patch(Rectangle((x,2.2),w,1.25,fill=False,edgecolor=BLUE,lw=1.2));ax.text(x+w/2,2.825,label,ha='center',va='center',fontsize=8.8)
        ax.annotate('',xy=(4.25,2.825),xytext=(3,2.825),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(3.55,3.08,'n1',ha='center',fontsize=9)
        ax.annotate('',xy=(8.55,2.825),xytext=(7.45,2.825),arrowprops=dict(arrowstyle='->',color=BLUE));ax.text(8,3.08,'n2',ha='center',fontsize=9)
        ax.plot([11.55,11.9],[2.825,2.825],color=BLUE);ax.text(11.9,3.63,'VOUT\nCL200pF',ha='right',fontsize=8.5)
        ax.plot([3.65,3.65,11.85,11.85],[2.825,.12,.12,2.825],color=GREEN);ax.text(7.65,.31,'C1 = 8 pF: VOUT <-> n1',ha='center',fontsize=8.8,color=GREEN)
        ax.plot([8,8,11.65,11.65],[2.825,1.2,1.2,2.825],color=GREEN);ax.text(9.8,1.37,'C2 = 3 pF',ha='center',fontsize=8.8,color=GREEN)
        ax.text(.03,1.1,'iref 5 uA\nNMOS/PMOS bias mirrors',fontsize=8.5)
        rows=[]
        for key,label,m in [('input','MI1 / MI2','1'),('first_mirror','MP1A / MP1B','1'),('second_n','MA2','1'),('second_mirror','MPD2 / MPM2','1 / 2'),('n_bias','REF / TAIL / BP1 / VBN / S2','1 / 0.48 / 1 / 1 / 1'),('p_bias','MPDM / MS2B / ML3','1 / 1 / 21'),('output_n','MA3','1')]:
            q=s['roles'][key];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:g}"])
        table(fig,[.07,.352,.86,.255],['角色','模型','单位W/L um','m','目标gm/ID'],rows,[.32,.10,.18,.27,.13],8.1)
        para(fig,.310,'输入L=1 um、每支目标1.2 uA、gm/ID=18，gm≈21.6 uS，初估gm/(2π·8pF)≈430 kHz。A2选gm/ID=8，让n1保留足够电位，使输入MI2的漏源压不被压低；输出L=0.36 um、目标105 uA、gm/ID=14。',9.3)
        para(fig,.175,'全部单位W≤17.02 um；ML3以4.68 um、m=21得到98.28 um等效总宽。MTAIL的m=0.48是连续模型缩放；实版需转换为合规匹配几何并重新提取验证，不能直接将小数m视作完整布局。',9.2)
        para(fig,.081,'LUT采用既有SMIC18 tt表，Wref=10 um、零体偏置；每项VDS、尺寸、源路径与SHA-256均在sizing.json。实际OP吸收体效应和窄宽偏差；未改PDK或原LUT，无需补扫。',9)
        save(pdf,fig)

        fig=page('中心工作点与手算闭合',3,'余量定义为|VDS|−|VDSAT|；以下是0.9 V输入目标、单位反馈、200 pF负载的实际OP。')
        rows=[]
        for name,q in r['operating_point'].items():rows.append([name,f"{abs(q['ids'])*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['gmro']:.2f}",f"{abs(q['vds']):.4f}",f"{q['headroom_V']*1e3:.2f}"])
        table(fig,[.07,.419,.86,.438],['MOS','|Id| uA','gm/ID','gm/gds','|VDS| V','饱和余量mV'],rows,[.19,.16,.15,.16,.15,.19],8.4)
        para(fig,.380,'节点：tail=0.34545 V，na=1.15400 V，n1=0.61062 V，nb=1.19570 V，n2=0.54474 V，vout=0.896845 V。MI2饱和余量最小，为172.60 mV；中心OP通过不等于全摆幅、全PVT均饱和。',9.3)
        para(fig,.270,'按OP的gm和输出电导，A1≈41.23 dB，A2≈38.22 dB，A3≈40.41 dB；简单相加119.86 dB，与119.59 dB的返回比实测相近。A2估算包含PMOS镜的gm比；这些是低频近似，不能替代环路测量。',9.3)
        para(fig,.159,'实际尾流2.3704 uA / C1 8 pF ≈0.2963 V/us，吻合双向0.3002/0.2935 V/us。输出上拉109.643 uA / CL 200 pF≈0.5482 V/us，说明本例主要由前级补偿电容充放电限制压摆。',9.3)
        para(fig,.078,'119 dB增益来自三个有限增益级，8 pF/3 pF嵌套反馈安排极点。保持微功耗同时得到200 pF驱动，需要共同预算带宽、输出静态电流、补偿电容和压摆率。',9)
        save(pdf,fig)

        fig=page('返回比与完整直流扫描',4,'返回比T=−V(vout)/V(vinn)，由输出与反相端之间的AC1串联电压源提取。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.235,top=.85,hspace=.40,wspace=.37)
        axs[0,0].semilogx(a['freq'],20*np.log10(abs(h)),color=BLUE);axs[0,0].axhline(0,color=GRAY,lw=.7);axs[0,0].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Return ratio (dB)',xlim=(.01,1e8))
        axs[0,1].semilogx(a['freq'],np.unwrap(np.angle(h))*180/np.pi,color=BLUE);axs[0,1].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,1].axhline(-180,color=GRAY,lw=.7);axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Return phase (deg)',xlim=(.01,1e8))
        axs[1,0].plot(d['vinp'],d['vinp'],color=GRAY,ls='--',label='Command');axs[1,0].plot(d['vinp'],d['vout'],color=BLUE,label='Output');axs[1,0].axvspan(.1,1.168,color=GREEN,alpha=.13);axs[1,0].set(xlabel='Unity-feedback command (V)',ylabel='Output (V)',xlim=(.1,1.7));axs[1,0].legend(fontsize=7)
        axs[1,1].plot(d['vinp'],(d['vout']-d['vinp'])*1e3,color=BLUE);axs[1,1].axhspan(-20,20,color=GREEN,alpha=.13);axs[1,1].axvline(1.168,color=GREEN,ls='--');axs[1,1].set(xlabel='Unity-feedback command (V)',ylabel='Tracking error, zoom (mV)',xlim=(.1,1.7),ylim=(-30,30))
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=7.5)
        para(fig,.193,'AC：100点/十倍频，增益取0.1 Hz，首个下降交越按对数频率插值求UGB/PM；0.01 Hz–100 MHz仅一次下降交越。完整801点DC：0.1→1.7 V、步长2 mV；535点构成0.100–1.168 V连续资格区间。',9.2)
        para(fig,.091,'1.168 V命令误差19.9966 mV，下一点1.170 V误差20.7050 mV，不再合格。0.100 V是扫描下界，未声称物理极限；低输入电压时偏置可能很弱，静态跟踪区间不代表整个区间均具相同带宽或压摆能力。',9.2)
        save(pdf,fig)

        fig=page('固定建立窗口与双向压摆',5,'时间从原刺激边沿开始计；建立容差中心固定0.9 V，不随实际终值0.896845 V平移。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.235,top=.85,hspace=.42,wspace=.37)
        tt=(t['time']-2e-6)*1e6
        axs[0,0].plot(tt,t['vinp'],color=GRAY,ls='--',label='Command');axs[0,0].plot(tt,t['vout'],color=BLUE,label='Output');axs[0,0].axhspan(.89,.91,color=GREEN,alpha=.16);axs[0,0].axvline(v['settling_time_s']*1e6,color=GREEN,ls='--');axs[0,0].set(xlim=(-.5,6),xlabel='Time after2us edge start (us)',ylabel='Settling output (V)');axs[0,0].legend(fontsize=7)
        axs[0,1].plot(tt,(t['vout']-.9)*1e3,color=BLUE);axs[0,1].axhspan(-10,10,color=GREEN,alpha=.16);axs[0,1].set(xlim=(0,48),ylim=(-20,20),xlabel='Time after2us edge start (us)',ylabel='Fixed-target error, zoom (mV)')
        for ax,edge,lab in [(axs[1,0],2e-6,'Rising'),(axs[1,1],42.1e-6,'Falling')]:
            tz=(z['time']-edge)*1e6;ax.plot(tz,z['vinp'],color=GRAY,ls='--',label='Command');ax.plot(tz,z['vout'],color=BLUE,label='Output');ax.axhline(.75,color=GREEN,ls=':');ax.axhline(1.05,color=GREEN,ls=':');ax.set(xlim=(-.5,5),xlabel='Time after command edge (us)',ylabel=lab+' output (V)');ax.legend(fontsize=7)
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=7.3)
        para(fig,.190,'建立：0.4→0.9 V，2.0–2.1 us线性边沿，观察到50 us。2%×0.5 V=10 mV窗，最后越界落在2.37–2.38 us之间；原算法取首个合格采样点2.38 us。末点误差3.1553 mV，即阶跃幅度的0.6311%。',9.2)
        para(fig,.089,'压摆：0.65↔1.15 V，边沿100 ns，下降边沿开始42.1 us；原算法从42 us搜索。固定0.75/1.05 V输出交越线性插值得0.30025/0.29345 V/us。输出采样10 ns，内部最大步长5 ns；没有把采样精度当作连续时间精确值。',9.2)
        save(pdf,fig)

        fig=page('精确网表、测量来源与复现',6,'DUT仅使用16个目标工艺MOS与两个正电容；独立刺激和理想200 pF负载均在bench中。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.861,body,fontsize=8.5,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.31)
        para(fig,.524,'原instruction、参考solution、verify.py、utils.py和五套bench已冻结。将真实PSF向量适配为原Plot结构，直接调用extract_metrics；原nominal_functional也通过。未调用或伪造45点矩阵检查。',9.2)
        para(fig,.410,'输入偏置另用两输入独立固定0.9 V、开环输出的原bench；两输入电流均读0 A。该bench输出约7.88 mV，不用于0.9 V静态输出门槛；后者在单位反馈AC/OP bench测量。0 A不能证明ESD、栅泄漏或封装漏电也为零。',9.2)
        para(fig,.296,'复现（工程根目录）：\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case37_nested_miller.py\n同一Python运行 scripts/review_pdf.py 37 生成PDF。\n源任务：sky130-three-stage-nested-miller-ota-pvt',8.6)
        para(fig,.181,'正式运行（依次AC/OP、输入偏置、DC范围、建立、压摆）：\n'+'\n'.join(r['run_dirs']),8)
        para(fig,.079,'各run保留inputs、原始PSF、模型与网表哈希。精确电路SHA-256：\n'+sha(case/'circuit.scs'),7.8)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),geometry_sha256=sha(case/'geometry.json'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(37,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

if __name__=='__main__':print(make37())
