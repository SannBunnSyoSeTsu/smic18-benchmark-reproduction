from review_pdf import *


def make22():
    case=ROOT/'cases/22-bootstrap';r=json.loads((case/'latest_results.json').read_text());v=r['values'];s=r['samples']
    sizes=json.loads((case/'sizing.json').read_text());nc=json.loads((case/'numerical_confirmation.json').read_text())
    a=data(ROOT/r['run_dirs'][0],'tran.tran');d=data(ROOT/r['run_dirs'][1],'tran.tran');out=ROOT/'reports/22-bootstrap-review.pdf'
    with PdfPages(out,metadata={'Title':'22 SMIC18差分自举栅驱动器审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('22 | 差分自举栅驱动器审查',1,'结论：32点相干SDR、64个跟踪栅源电压、双向保持和DUT功耗均通过原nominal。')
        para(fig,.856,'条件：SMIC18MMRF tt / 1.8 V / 27°C；100 MHz时钟、50 ps源边沿、50 Ω源阻抗及两级原厂HD缓冲；输入46.875 MHz，每侧0.4 V峰值、共模0.9 V；每侧固定1 pF保持电容。',9.4)
        rows=[]
        for label,key,k,unit in [('采样SDR','sdr_db',1,'dB'),('最小mid-track VGS','minimum_midtrack_vgs_ratio',1,'VDD'),('正样本保留增益','positive_retained_gain',1,'V/V'),('负样本保留增益','negative_retained_gain',1,'V/V'),('DUT供电功耗','average_power_w',1e6,'uW')]:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([label,f'{v[key]*k:.7g}']+[f'{sign}{g["limits"][tier]*k:.5g}' for tier in ['original','10pct','15pct']]+[unit])
        table(fig,[.07,.495,.86,.265],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.30,.18,.14,.14,.14,.10],8.6)
        para(fig,.448,'采样MOS属于测试台固定负载：宽度64 um保持；原Sky130长度0.15 um低于SMIC n18最小值，因此映射为0.18 um，并在两轮中固定。原手工时钟缓冲替换为INHDV8→INHDV16；这些是目标工艺迁移差异，不能称作原器件完全相同。',9.4)
        para(fig,.323,f'额外检查三组波形中驱动器和采样MOS的端电压：最大|VGS|或|VGD|={v["max_gate_terminal_voltage_V"]:.6f} V，最大|VDS|={v["max_drain_source_voltage_V"]:.6f} V。均通过1.98 V工程线；该线不代表已完成工艺寿命或可靠性签核。',9.4)
        para(fig,.21,f'72 dB目标采用总非基波功率SDR，不能与“最大单个杂散”的SFDR混用。原函数结果{v["sdr_db"]:.6f} dB，独立直接求和非基波功率结果{r["stable_nonfundamental_sum_SDR_dB"]:.6f} dB，避免大数相减的交叉核验一致。',9.4)
        para(fig,.105,'只完成TT/1.8 V/27°C；其余10个PVT点、随机失配、热噪声和PEX未执行。本题500 uW限额仅针对DUT VDD，外部时钟缓冲功率独立列出，不将其误称为总系统能耗。',9.4)
        save(pdf,fig)

        fig=page('自举回路、保护与固定测试负载',2,'CLK低电平跟踪，高电平保持；左右驱动完全对称，分别跟随VINP/VINN。')
        ax=fig.add_axes([.075,.635,.85,.225]);ax.set(xlim=(0,10),ylim=(0,4.8));ax.axis('off')
        boxes=[(.1,2.5,2.8,1.45,'CLK → INHDV8\n产生CLKP'),(3.5,2.5,2.9,1.45,'预充/关断控制\nCBOOT = 1.5 pF'),(7,2.5,2.85,1.45,'gatep / gaten\n自举输出')]
        for x,y,w,h,text in boxes:ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor=BLUE));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=9)
        for x1,x2 in [(2.9,3.5),(6.4,7)]:ax.annotate('',xy=(x2,3.25),xytext=(x1,3.25),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.text(4.9,1.76,'VIN跟踪CBB；CBT随之抬升',ha='center',fontsize=9);ax.annotate('',xy=(4.9,2.5),xytext=(4.9,1.95),arrowprops=dict(arrowstyle='->',color=GREEN))
        ax.text(.2,.8,'VDD → MPRE → PRE → MPRGUARD → VG',fontsize=9,color=GREEN);ax.text(.2,.2,'MPRE栅接CLKP；MPRGUARD栅固定VDD，隔离预充端。',fontsize=8.7,color=GREEN)
        rows=[['自举NMOS单位','n18',f'{sizes["roles"]["n18"]["rounded_W_um"]:g}/0.18','8','200 uA'],['自举PMOS单位','p18',f'{sizes["roles"]["p18"]["rounded_W_um"]:g}/0.18','8','200 uA'],['固定外部采样管','n18','64/0.18','8，反查',f'{sizes["roles"]["fixed_fixture_n18"]["Id_A"]*1e3:.5f} mA']]
        table(fig,[.07,.45,.86,.135],['角色','模型','单位W/L (um)','LUT gm/ID','选点电流'],rows,[.29,.12,.22,.17,.20],8.7)
        para(fig,.407,'LUT均为VDS=0.9 V、VSB=0、TT/27°C；真实开关瞬态不保持该工作点。固定W64 um采样负载通过LUT电流密度反查，只作几何交叉记录，没有按结果调小负载。',9.4)
        para(fig,.3,'每侧9只模拟MOS和1个原厂HD反相器，MPRE/MGTRK/MPVIN/MCASC/MPRGUARD为n单位m2，其余m1；左右各1.5 pF自举储能。电容、寄生负载和预充路径导致实际VGS低于理想VDD，须检验每个跟踪中点。',9.4)
        para(fig,.185,'继承第31项发现的预充端电压问题，首版直接加入保护管，没有在本题重新使用已知端差过高的连接。MLIM/MBPP的PMOS体接CBT；版图必须保留所需独立井。',9.4)
        para(fig,.084,'外部两级时钟缓冲、两只64 um采样MOS和两只1 pF电容只在bench层。DUT只含目标PDK MOS、原厂HD MOS与正值电容，没有内部源、理想R/L/S或行为元件。',9.2)
        save(pdf,fig)

        fig=page('近奈奎斯特频谱与64点栅源检查',3,'输入46.875 MHz = 15/32 × 100 MHz；32个held样本34–344 ns，跟踪中点38–348 ns。')
        ax=fig.add_axes([.115,.695,.83,.16]);ax.plot(np.array(s['time_s'])*1e9,s['output_V'],'o-',ms=3,color=BLUE);ax.set(xlabel='Held sample time (ns)',ylabel='Output difference (V)');ax.grid(alpha=.2)
        ax2=fig.add_axes([.115,.43,.83,.17]);sp=np.array(s['spectrum_amplitude_V']);bins=np.arange(1,17);db=20*np.log10(np.maximum(sp[bins]/sp[15],1e-15));ax2.vlines(bins*3.125,-170,db,color=BLUE,lw=1);ax2.plot(bins*3.125,db,'o',ms=3);ax2.set(xlabel='Sampled spectrum frequency (MHz)',ylabel='Amplitude (dBc)',ylim=(-170,5),xlim=(0,51));ax2.grid(alpha=.2)
        ax3=fig.add_axes([.115,.18,.83,.15]);mid=np.array(s['midtrack_times_s'])*1e9
        for side in ['p','n']:ax3.plot(mid,np.array(s['vgs_'+side+'_V'])/1.8,'o-',ms=3,label=side.upper())
        ax3.axhline(.8,color=GRAY,ls='--',lw=.7);ax3.set(xlabel='Mid-track sample time (ns)',ylabel='VGS / VDD');ax3.legend(fontsize=8,ncol=2);ax3.grid(alpha=.2)
        for z in [ax,ax2,ax3]:z.tick_params(labelsize=8)
        para(fig,.105,'SDR=10log10[(P15+P17)/(ΣP1…31−P15−P17)]，包括Nyquist功率、排除DC；不加窗、不移除启动后的某些差样本。正负两侧每个跟踪中点VGS均读取真实gate−vin，未用对地栅压替代。没有加入噪声或从SDR外推ENOB。',9.2)
        save(pdf,fig)

        fig=page('保持隔离、功耗边界与精度对照',4,'正负两份电路同时验证；22.0–22.1 ns反转输入，24 ns读取原极性的保留量。')
        ax=fig.add_axes([.115,.625,.83,.23]);t=a['time'];m=(t>=19e-9)&(t<=27e-9)
        for tag in ['P','N']:ax.plot(t[m]*1e9,(a['voutp'+tag]-a['voutn'+tag])[m],label='Held '+tag)
        ax.plot(t[m]*1e9,(a['vinpP']-a['vinnP'])[m],color=GRAY,ls='--',label='Input P');ax.axvline(24,color=GREEN,ls=':');ax.set(xlabel='Time (ns)',ylabel='Differential voltage (V)');ax.legend(fontsize=8,ncol=3);ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        rows=[['DUT VDD',f'{v["average_power_w"]*1e6:.6f}','原500 uW门槛使用此项'],['外部HD缓冲供电',f'{v["external_clock_buffer_power_W"]*1e6:.6f}','按原合同排除，另列'],['50 Ω前时钟源',f'{v["external_clock_source_power_W"]*1e6:.6f}','诊断；不是DUT VDD']]
        table(fig,[.07,.433,.86,.12],['端口','平均功率/uW','边界'],rows,[.33,.23,.44],8.7)
        para(fig,.393,'供电积分30–350 ns，共32个时钟周期；功耗为−1.8×平均I(VDD)，保留非负要求。输入源也可能供能，但本题没有以全部源总功率评分；本页不宣称完整系统能耗。',9.3)
        rows=[]
        for label,key,scale in [('SDR / dB','sdr_db',1),('最小VGS / VDD','minimum_midtrack_vgs_ratio',1),('DUT功耗 / uW','average_power_w',1e6)]:rows.append([label,f'{nc["coarse_values"][key]*scale:.9g}',f'{v[key]*scale:.9g}',f'{nc["absolute_changes"][key]*scale:.4g}'])
        table(fig,[.07,.195,.86,.12],['指标','最大步5 ps','最大步2.5 ps','绝对差'],rows,[.31,.23,.23,.23],8.6)
        para(fig,.151,'同电路reltol=2e−6、iabstol=1e−12、vabstol=1e−9、conservative。FFT中存在SPECTRE-16780局部LTE放宽警告；两轮都保留日志，缩步后原门槛保持通过。最终采用2.5 ps数据，无需进一步重复扫描。',9.2)
        save(pdf,fig)

        fig=page('精确DUT网表、证据与复现',5,'左右自举驱动具有相同几何；外部固定采样负载不属于以下DUT网表。')
        fig.text(.075,.86,(case/'circuit.scs').read_text(),fontsize=8.0,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.3)
        para(fig,.52,'源任务：sky130-bootstrap-sampler-fft。原instruction、reference、正式verifier及两个bench已冻结；提取后直接调用原analyze_fft与nominal_passes，只执行nominal，不调用其全PVT调度。',9.4)
        para(fig,.409,'32点FFT额外使用直接求和非基波功率进行数值交叉检查，与原“总功率减信号”结果差小于1e−8 dB。72条器件检查覆盖静态正/负两份和FFT一份驱动及采样MOS；外部缓冲另作功率表征。',9.4)
        para(fig,.299,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case22_bootstrap.py --maxstep-ps 2.5\nPDF：同一Python运行 scripts/review_pdf.py 22\n运行：'+r['run_dirs'][0]+'\n'+r['run_dirs'][1],8.5)
        para(fig,.174,'每个runs目录含bench、DUT、HD及合同/尺寸脚本快照、模型SHA-256、完整日志与PSF。numerical_confirmation.json记录两轮对照，latest_results.json保存32个样本、64个VGS及72条端差。',9.3)
        para(fig,.075,'这一nominal通过只支持当前采样频率、输入幅度、时钟驱动和固定负载；没有验证其他工艺角、失配、相位噪声或版图寄生。',9.1)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=5,render_review_pending=True))
    update_case(22,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
