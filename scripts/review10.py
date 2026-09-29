"""Review case 10 from frozen PSF results; this script never starts simulations."""
from review_pdf import *


def make10():
    case=ROOT/'cases/10-tia'
    r=json.loads((case/'latest_results.json').read_text());v=r['values']
    s=json.loads((case/'sizing.json').read_text());nr=json.loads((case/'numerical_review.json').read_text())
    a=data(ROOT/r['runs_by_analysis']['ac'],'ac.ac')
    n=data(ROOT/r['runs_by_analysis']['noise'],'noise.noise',required=['in','out'])
    t=data(ROOT/r['runs_by_analysis']['sfdr'],'tran.tran')
    spectrum=np.loadtxt(ROOT/r['measurement_detail']['sfdr']['spectrum'],delimiter=',',skiprows=1)
    out=ROOT/'reports/10-tia-review.pdf'
    with PdfPages(out,metadata={'Title':'10 SMIC18 两级模拟反相器跨阻放大器审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('10 | 跨阻放大器 TIA 审查',1,'结论：15%放宽通过；仅带宽低于原门槛13.38%，其他6项原门槛全部通过。')
        para(fig,.856,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；IREF=20 uA，VCM=0.9 V，输入电容0.3 pF，输出负载0.2 pF。保持正式100 MHz、10 uA峰值电流激励，以及固定10–500 MHz噪声积分频带。',9.8)
        info=[('ZT @1 MHz','zt_1m_ohm',1e-3,'kΩ'),('上侧−3 dB带宽','bandwidth_hz',1e-6,'MHz'),('最大输入电流噪声','noise_density_a_per_rt_hz',1e12,'pA/√Hz'),('积分输入电流噪声','integrated_noise_a_rms',1e9,'nArms'),('大信号基波ZT','large_signal_zt_ohm',1e-3,'kΩ'),('全谱SFDR','sfdr_db',1,'dBc'),('外部端口总DC功耗','power_w',1e3,'mW')]
        rows=[]
        for label,key,scale,unit in info:
            q=r['gates'][key];sign=q['comparison'];rows.append([label,f"{v[key]*scale:.4f}",*[f"{sign}{q['limits'][tier]*scale:.4f}" for tier in ['original','10pct','15pct']],unit])
        tb=table(fig,[.07,.454,.86,.29],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.26,.14,.15,.15,.15,.15],8.1)
        for j in range(6):tb[(2,j)].set_facecolor('#fff1d5')
        para(fig,.413,'带宽649.6269 MHz：未达到原750 MHz或10%边界675 MHz；高于15%下界637.5 MHz约12.13 MHz。完整结果状态为complete_15pct，不能标为原门槛全部通过。',9.7)
        para(fig,.310,'正式大信号ZT为8.1677 kΩ，比原8 kΩ门槛高2.10%；SFDR为70.6750 dBc，最大杂散200 MHz。未用公共诊断的5 uA幅度替代正式10 uA，也未仅在指定谐波或500 MHz以内搜索杂散。',9.7)
        para(fig,.206,'功耗为|VDD·I(VDD)|+|VCM·I(VCM)|，两项分别4.6885666 mW与4.3019 nW；20 uA参考已从VDD取电，不重复累加。SFDR按基波/杂散幅度比放宽，dB下限加20log10(0.90/0.85)。原门槛均使用严格>或<比较。',9.5)
        para(fig,.084,'本报告仅覆盖一个nominal点的AC/功耗、噪声和正式SFDR三组测量；原15点PT矩阵的其余14点、失配和版图寄生均未执行。',9.1)
        save(pdf,fig)

        fig=page('模拟反相器结构、gm/ID与工作点',2,'保留原两级电阻反馈结构；NMOS与PMOS同时导通，属于模拟增益级。')
        ax=fig.add_axes([.07,.681,.86,.187]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,4))
        for x,label in [(1.1,'MN1 + MP1\n模拟反相器'),(6.5,'MN2 + MP2\n模拟反相器')]:
            ax.add_patch(Rectangle((x,1.25),2.1,1.15,fill=False,edgecolor=BLUE));ax.text(x+1.05,1.825,label,ha='center',va='center',fontsize=9)
        ax.plot([.15,1.1],[1.825,1.825],color=BLUE);ax.text(.10,2.5,'IN',fontsize=9)
        ax.plot([3.2,4.0],[1.825,1.825],color=BLUE);ax.plot([5.35,6.5],[1.825,1.825],color=BLUE);ax.text(3.40,2.08,'N1',fontsize=8);ax.text(5.77,2.08,'NBUF',fontsize=8)
        ax.add_patch(Rectangle((4.0,1.53),1.35,.59,facecolor='white',edgecolor=GREEN));ax.text(4.675,1.825,'RIN2 1.5k',ha='center',va='center',fontsize=8)
        ax.plot([8.6,9.85],[1.825,1.825],color=BLUE);ax.text(9.0,2.5,'VOUT',fontsize=9)
        for x1,x2,label in [(.65,3.55,'RF1 4k'),(6.0,9.15,'RFB2 4.5k')]:
            ax.plot([x1,x1,x2,x2],[1.825,3.3,3.3,1.825],color=GREEN);ax.text((x1+x2)/2,3.4,label,ha='center',fontsize=8.5,color=GREEN)
        ax.plot([.65,.65],[1.825,.55],color=BLUE);ax.text(.65,.14,'CIN 0.3pF / RB 1M→VCM',ha='left',fontsize=8)
        ax.plot([9.15,9.15],[1.825,.55],color=BLUE);ax.text(9.15,.14,'CL 0.2pF',ha='right',fontsize=8)
        rows=[]
        for k,name,mult in [('n_amp','MN1 / MN2','15 / 11'),('p_amp','MP1 / MP2','15 / 11'),('reference','MREF','1')]:
            q=s['roles'][k];rows.append([name,q['model'],f"{q['L_um']:.2f}",f"{q['rounded_W_um']:.2f}",mult,f"{q['gmid']:.1f}",f"{q['lut_metadata']['vds_V']:.2f}"])
        table(fig,[.07,.512,.86,.133],['器件','模型','L/um','单位W/um','m','LUT gm/ID','LUT |VDS|'],rows,[.21,.10,.10,.14,.12,.13,.20],8.4)
        rows=[]
        for name,q in r['operating_point'].items():rows.append([name,f"{abs(q['ids'])*1e6:.3f}",f"{q['gm']*1e3:.4f}",f"{q['gmid']:.3f}",f"{q['gmro']:.2f}",f"{abs(q['vds']):.4f}",f"{q['headroom_V']:.4f}"])
        table(fig,[.07,.284,.86,.19],['实际OP','|ID|/uA','gm/mS','gm/ID','gm/gds','|VDS|/V','饱和余量/V'],rows,[.13,.16,.14,.13,.14,.14,.16],8.4)
        para(fig,.251,'LUT以100 uA模拟单位管起步，取n/p的gm/ID=3.4/3.9，使栅压约0.9 V。低gm/ID对应强反型与较高速度；最终第一/二级复制15/11份，目标1.5/1.1 mA。实际偏置1.4912/1.0936 mA，所有单位W≤8.86 um，均在模型范围内。',9.2)
        para(fig,.137,'反馈电阻完成直流自偏置：IN=0.895220 V，N1=0.895201 V，VOUT=0.895258 V。MREF只以二极管连接终止20 uA端口，未镜像到两级。三份既有TT LUT只读使用；5只管均饱和，最小余量0.3935 V。DUT仅5只MOS与4只正电阻。',9.1)
        save(pdf,fig)

        fig=page('固定负载下的跨阻带宽与噪声',3,'带宽参考1 MHz跨阻；应用噪声频带固定为10–500 MHz。')
        ax=fig.add_axes([.12,.584,.81,.275]);f=a['freq'];zt=abs(a['vout'])
        ax.semilogx(f,20*np.log10(zt),color=BLUE,label='Measured |ZT|')
        ax.axhline(20*np.log10(v['zt_1m_ohm']/np.sqrt(2)),color=GRAY,ls=':',label='ZT(1 MHz) / sqrt(2)')
        ax.axvline(v['bandwidth_hz'],color=GREEN,ls='--',label='BW 649.63 MHz');ax.axvline(750e6,color='#b26e19',ls=':',label='Original 750 MHz')
        ax.set(xlim=(1e6,10.1e9),xlabel='Frequency (Hz)',ylabel='Transimpedance (dB ohm)');ax.legend(fontsize=7.5,loc='lower left');ax.grid(alpha=.2,which='both')
        axs=[fig.add_axes([.12,.252,.35,.235]),fig.add_axes([.585,.252,.35,.235])]
        ff=n['freq'];ni=abs(n['in']);cumulative=np.r_[0,np.cumsum((ni[1:]**2+ni[:-1]**2)/2*np.diff(ff))]**.5
        axs[0].semilogx(ff,ni*1e12,color=BLUE);axs[0].axhline(5,color=GRAY,ls='--');axs[0].set(xlabel='Frequency (Hz)',ylabel='Input noise (pA/sqrt(Hz))',ylim=(0,5.5),xlim=(1e7,5e8))
        axs[1].semilogx(ff,cumulative*1e9,color=BLUE);axs[1].axhline(100,color=GRAY,ls='--');axs[1].set(xlabel='Integration endpoint (Hz)',ylabel='10 MHz to f noise (nArms)',ylim=(0,110),xlim=(1e7,5e8))
        for ax in axs:ax.grid(alpha=.2,which='both');ax.tick_params(labelsize=8)
        para(fig,.194,'AC共401点，1 MHz–10.1 GHz、100点/十倍频程；按原fall=1取首个下降−3 dB交越。线性频率插值得649.6269 MHz，改用对数频率为649.5933 MHz，差0.00517%。10 GHz跨阻10.0018 Ω，因此本例不使用“≥10 GHz”下界分支。',9.1)
        para(fig,.100,'噪声171点覆盖10–500 MHz，每点输入电流谱均低于5 pA/√Hz，最坏点为500 MHz。对谱密度平方积分再开根号：66.66484 nArms；分段幂律积分66.66503 nArms，差0.000289%。未随实际带宽改变积分终点。',9.1)
        save(pdf,fig)

        fig=page('正式10 uA正弦与全谱SFDR',4,'仅移除均值与基波；所有剩余非DC FFT频点均参与最大杂散搜索。')
        ax=fig.add_axes([.12,.674,.81,.18]);mask=t['time']>=150e-9
        ax.plot(t['time'][mask]*1e9,t['vout'][mask],color=BLUE);ax.set(xlabel='Time (ns)',ylabel='VOUT (V)',xlim=(150,170));ax.grid(alpha=.2)
        ff=spectrum[:,0];sp=spectrum[:,1];dBc=20*np.log10(np.maximum(sp,1e-30)/r['measurement_detail']['sfdr']['fundamental_amplitude_V'])
        ax=fig.add_axes([.12,.40,.81,.185]);ax.semilogx(ff[1:],dBc[1:],color=BLUE,lw=.8)
        ax.plot([1e8,2e8],[0,-v['sfdr_db']],'o',color=GREEN,ms=4);ax.axhline(-70,color=GRAY,ls='--',lw=.7)
        ax.set(xlim=(6.25e6,51.2e9),ylim=(-220,5),xlabel='All non-DC FFT bins (Hz)',ylabel='Amplitude / fundamental (dBc)');ax.grid(alpha=.2,which='both')
        para(fig,.346,'冻结verify.py的sfdr_metrics直接读取PSF转出的17位文本：取最后16周期，即10–170 ns；线性插值到每周期1024点，共16384点。减均值后用2|rFFT|/N，bin 16为100 MHz基波，最大其余非DC线为200 MHz；无加窗、无只看谐波的筛选。',9.1)
        para(fig,.233,'基波81.677255 mV，最大杂散23.897372 uV，SFDR=70.675020 dBc；基波幅度除以10 uA得到8.167725 kΩ。100 MHz小信号AC跨阻8.171706 kΩ，大信号变化−0.04871%；1 MHz原跨阻为8.263725 kΩ。三者定义不可互换。',9.1)
        para(fig,.141,'完整瞬态17409个保存点，间隔9.765625 ps，内部maxstep=5 ps。原生采样的100/200 MHz最小二乘幅度比与正式FFT相差1.3e−10 dB；交叉检查验证提取一致性，不构成步长收敛误差界限。未作额外精度扫描。',9.0)
        para(fig,.077,'save IIN:p被Spectre忽略并产生两条警告；理想电流源仍按冻结bench的100 MHz/10 uA运行，VOUT完整。没有保存IIN电流波形，因此不声称对该波形另作实测。',8.1)
        save(pdf,fig)

        fig=page('原合同映射与设计权衡',5,'同一正式刺激、负载、功率端口和观察窗口；原函数保留其nominal单点集合。')
        rows=[['AC / 功耗','1 MHz–10.1 GHz，dec 100；DC端口电流','ZT=|VOUT|，IIN AC=1 A；首个下降−3 dB点；VDD+VCM绝对功率'],['噪声','10–500 MHz，dec 100，输出VOUT','Spectre iprobe=IIN输入电流谱；全频点最大值和固定频带积分'],['正式SFDR','100 MHz、10 uApeak；170 ns结束','末16周期×1024点；全部非DC杂散；同时门控基波ZT']]
        rows=[[x[0],wrap(x[1],38),wrap(x[2],44)] for x in rows]
        table(fig,[.07,.617,.86,.23],['源测量组','固定条件','本次实现'],rows,[.17,.35,.48],8.8)
        para(fig,.576,'直接调用冻结ac_checks、noise_checks、sfdr_check，传入集合{tt,27°C}，保留严格> / <比较；原6个分组检查中仅带宽失败。SFDR分组同时要求大信号ZT与SFDR，所以最终合计7个标量门槛。未把单点伪装成15点PT覆盖。',9.2)
        rows=[['初版','900 / 800','5.55k / 5.5k / 13.2k','10.1354','583.330','3.0781','仅AC'],['第二版','1300 / 1200','4.7k / 4.9k / 13.2k','9.7416','541.871','4.5096','仅AC'],['完整候选','1500 / 1100','3.9k / 1.5k / 4.5k','8.0523','661.355','4.6886','15%通过'],['最终固定','1500 / 1100','4.0k / 1.5k / 4.5k','8.2637','649.627','4.6886','15%通过']]
        table(fig,[.07,.309,.86,.195],['版本','目标电流/uA','RF1 / RIN2 / RFB2','ZT/kΩ','BW/MHz','P/mW','证据'],rows,[.13,.16,.27,.12,.12,.11,.12],7.7)
        para(fig,.272,'有限环路增益使理想电阻乘积RF1·RFB2/RIN2=12 kΩ降到实测8.2637 kΩ。AC分解：带载首级ZT=3.56665 kΩ，第二级电压增益2.31694；乘积与总ZT一致。输入阻抗431.6 Ω，不能仅以RF1的数值等同输入阻抗。',9.2)
        para(fig,.171,'增加电流的第二版同时改变了电阻与器件电容，带宽反而下降，不能归因为单独电流效应。第二级改用1.5k/4.5k，在比值3下控制NBUF时间常数；这些权衡须以完整AC、噪声与正式大信号共同验证。',9.1)
        para(fig,.079,'完整候选的基波ZT=7.9622 kΩ，比原门槛低0.473%；最终只把RF1从3.9k改到4.0k，恢复两项ZT原门槛，带宽由661.35降至649.63 MHz，SFDR由70.874降至70.675 dBc。停止进一步优化并明确保存带宽放宽标签。',8.9)
        save(pdf,fig)

        fig=page('精确电路与可复现证据',6,'端口顺序 IREF IN VCM VDD VOUT VSS；MOS端序D G S B，体端接对应电源。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.077,.855,body,fontsize=9.0,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.5)
        para(fig,.515,'MOS模型：SMIC_018_MMRF/models/spectre/ms018_v1p7_spe.lib，section=tt。NMOS与PMOS模拟级采用既有TT gm/ID LUT初值，LUT路径、偏置、尺寸、模型与源文件SHA-256均在case与run快照中。单位宽度合法，无新数字电路或额外DUT电容。',9.0)
        para(fig,.414,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case10_tia.py\n报告：同一Python运行 scripts/review_pdf.py 10。当前脚本默认值已固定最终版本；历史执行脚本保留在各run的inputs中，电路与合同逐字对应。',8.7)
        para(fig,.323,'最终正式运行：\n'+ '\n'.join(r['run_dirs']),8.4)
        para(fig,.218,'源任务：sky130-tia-zt8k-bw750m-noise5p-sfdr70-power5m-pt。instruction、reference与三份正式bench、verify.py及utils.py已冻结在cases/10-tia/source。latest_results、numerical_review、verification_audit、pdf_provenance与knowledge.md构成审查入口。',8.7)
        para(fig,.128,'限制：仅tt/1.8 V/27°C，理想正电阻与测试电容；未验证其余PT、供电变化、额外光电二极管电容、失配、提取互连或电阻版图寄生。SFDR原门槛余量0.675 dB，不能推广为角落或硅后裕量。',8.9)
        para(fig,.055,'精确电路SHA-256：'+sha(case/'circuit.scs'),7.3)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),geometry_sha256=sha(case/'geometry.json'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(10,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out


if __name__=='__main__':print(make10())
