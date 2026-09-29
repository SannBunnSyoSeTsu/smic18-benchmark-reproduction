from review_pdf import *


def make07():
    case=ROOT/'cases/07-ldo-ota5';r=json.loads((case/'latest_results.json').read_text());v=r['values']
    a=data(ROOT/r['run_dirs'][0],'ac.ac');s=data(ROOT/r['run_dirs'][2],'dropout.dc');n=data(ROOT/r['run_dirs'][2],'noise.noise',required=['out']);t=data(ROOT/r['run_dirs'][3],'tran.tran')
    out=ROOT/'reports/07-ldo-ota5-review.pdf'
    with PdfPages(out,metadata={'Title':'07 SMIC18 PMOS LDO审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('07 | PMOS LDO 稳压器审查',1,'结论：全部nominal检查在15%退化范围通过；独立真实环路PM决定最终等级。')
        para(fig,.848,'条件：SMIC18MMRF tt / 27°C；VREF=0.8 V、IBIAS=50 uA来自VIN；目标1.2 V，外部300 kΩ/600 kΩ分压，标称1 uF+50 mΩ。保留9个供电/负载点、17个输出网络环路点和原瞬态。',9)
        items=[('最大DC误差','dc_error_V',1e3,'mV'),('最大静态电流','Iq_A',1e6,'uA'),('最小静态电流','min_Iq_A',1e6,'uA'),('源算法最小1Hz增益','dc_loop_gain_db',1,'dB'),('源算法最小UGB','loop_ugb_hz',1e-3,'kHz'),('源算法最小PM','phase_margin_deg',1,'deg'),('PSRR @100Hz','psrr_100hz_db',1,'dB'),('PSRR @1kHz','psrr_1khz_db',1,'dB'),('PSRR @100kHz','psrr_100khz_db',1,'dB'),('PSRR @1MHz','psrr_1mhz_db',1,'dB'),('30mA压差','dropout_V',1e3,'mV'),('10Hz–1MHz输出噪声','noise_Vrms',1e6,'uVrms'),('启动持续90%时间','startup_t90_s',1e6,'us'),('斜坡后±2%建立','startup_settling_after_ramp_s',1e6,'us'),('启动过冲','startup_overshoot_v',1e3,'mV'),('负载跳变峰值误差','load_excursion_V',1e3,'mV'),('电源跳变峰值误差','line_excursion_V',1e3,'mV'),('负载±15mV建立','load_settling_s',1e6,'us'),('电源±15mV建立','line_settling_s',1e6,'us'),('独立STB最小PM','stb_phase_margin_deg',1,'deg'),('独立STB最小UGB','stb_ugb_Hz',1e-3,'kHz')]
        rows=[]
        for label,key,scale,unit in items:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([label,f'{v[key]*scale:.5g}']+[f'{sign}{g["limits"][tier]*scale:.5g}' for tier in ['original','10pct','15pct']]+[unit])
        table(fig,[.07,.195,.86,.57],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.15,.15,.15,.15,.11],8.2)
        para(fig,.156,'原电压比PM54.137°和电源跳变21.900 mV可满足10%边界；真实STB PM53.861°低于10%边界54°，但高于15%边界51°。据此标为complete_15pct，不将电压比结果替代真实稳定性。',9)
        para(fig,.075,'未验证其他工艺/温度、30次失配、SS125输出网络瞬态、版图或可靠性；最小负载为1 mA，本报告不宣称空载稳定。额外17个FVF局部环路PM最小59.047°。',9)
        save(pdf,fig)

        fig=page('五管误差放大器、缓冲和片内补偿',2,'保持五管OTA功能级；总DUT为12只MOS、1个工艺电阻和1组工艺MIM电容。')
        ax=fig.add_axes([.08,.66,.84,.20]);ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
        for x,w,label in [(.1,2.9,'PMOS输入5T OTA\n比较FB与0.8 V'),(3.7,2.6,'PMOS FVF\n30 uA偏置'),(7,2.8,'PMOS功率管\nVOUT / 外部1 uF')]:
            ax.add_patch(Rectangle((x,1.6),w,1.45,fill=False,edgecolor=BLUE));ax.text(x+w/2,2.325,label,ha='center',va='center',fontsize=9)
        for x1,x2 in [(3,3.7),(6.3,7)]:ax.annotate('',xy=(x2,2.325),xytext=(x1,2.325),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.text(3.2,1.05,'ampout → 30 kΩ → 200 pF → VSS',fontsize=9,color=GREEN)
        ax.plot([8.4,8.4,1.5,1.5],[1.6,.35,.35,1.6],color=GRAY);ax.text(4.3,.48,'外部300 kΩ/600 kΩ反馈',fontsize=8.5)
        rows=[['输入对','p18','79.52/1 ×3','18','50 uA/支'],['NMOS镜负载','n18','86.32/4 ×1','14','50 uA/支'],['N偏置单位','n18','23.42/1','14','50 uA'],['P尾源单位','p18','32.26/1','16','10 uA'],['MSF','p18','12.36/0.18','16','30 uA'],['MBUF','p18','0.74/0.18','4','30 uA'],['MPASS单位','p18','49.88/0.18 ×60','6','1 mA/单位']]
        table(fig,[.07,.383,.86,.23],['角色','模型','单位W/L um 与m','LUT gm/ID','初选电流'],rows,[.24,.12,.29,.16,.19],8.7)
        para(fig,.345,'PMOS输入对避免NMOS输入级在低栅压时失去漏端余量。输入对共用独立井并接tail，MSF体接自身源极gate_drive；其余PMOS体接VIN。FVF的pbuf控制MBUF上拉，降低大功率管栅极的等效驱动阻抗。',9.4)
        para(fig,.23,'串联RC从ampout返回VSS，DC时电容开路保留增益；高频时约30 kΩ限制误差级增益，配合200 pF把过渡区放到主交越以下。标称1/(2πRC)约26.5 kHz；真实极点还包括OTA输出电阻与寄生。',9.4)
        para(fig,.125,'MIM采用30×30 um单位、m=228.859，约0.206 mm²电容有效面积；rpposab_3t为W1/L91.1083 um。这是稳定性与面积的明确代价。m含0.2/0.6模拟缩放，并非已完成版图阵列；所有MOS单位W≤86.32 um。',9.2)
        save(pdf,fig)

        fig=page('工作点、完整供电与负载矩阵',3,'9个点均在同一TT/27°C；Iq=abs(I(VIN))−ILOAD，包含外部50 uA参考和分压支路。')
        dcrows=[q for q in r['matrix'] if q['kind']=='dc'];psrows=[q for q in r['matrix'] if q['kind']=='psrr'];rows=[]
        for d,p in zip(dcrows,psrows):
            z=d['values'];ps=p['values'];rows.append([f'{d["vin"]:.2f}',f'{d["load"]*1e3:g}',f'{z["vout_V"]:.6f}',f'{z["Iq_A"]*1e6:.3f}']+[f'{ps[key]:.2f}' for key in ['psrr_100hz_db','psrr_1khz_db','psrr_100khz_db','psrr_1mhz_db']])
        table(fig,[.07,.535,.86,.325],['VIN/V','IL/mA','VOUT/V','Iq/uA','100Hz','1kHz','100kHz','1MHz'],rows,[.10,.10,.17,.13,.125,.125,.125,.125],8.2)
        para(fig,.497,'右侧四列为PSRR/dB。全矩阵最小PSRR仍满足原40/40/20/10 dB；最差DC误差2.958 mV。噪声另在1.8 V、10 mA积分，不把各工况PSRR当成噪声测量。',9.2)
        rows=[]
        for name in ['MINP','MLOUT','MTAIL','MSF','MBUF','MPASS']:
            z=r['operating_point']['D11'][name];lo=r['operating_point']['D02'][name]
            rows.append([name,f'{abs(z["ids"])*1e6:.4g}',f'{z["gmid"]:.3f}',f'{z["headroom_V"]*1e3:.2f}',f'{lo["headroom_V"]*1e3:.2f}'])
        table(fig,[.07,.214,.86,.215],['器件','中心Id/uA','中心gm/ID','中心余量/mV','1.62V/30mA余量'],rows,[.20,.19,.18,.20,.23],8.6)
        para(fig,.172,'表中余量=abs(VDS)−abs(VDSAT)。保存的1.62V/1mA、1.62V/30mA、1.8V/10mA三个OP中12只MOS均为正；最小68.65 mV。功率管gm/ID随负载显著变化，不能把初始LUT点6误写成全负载实测值。',9.2)
        para(fig,.083,'沿用既有LUT与第12项n18 L4补表；所有查询、VDS、Wref和SHA保留。LUT给初宽，实际端压与体连接由最终OP确认。原厂模型、Bridge和已有LUT目录均未修改。',9.1)
        save(pdf,fig)

        fig=page('17个输出网络点与独立稳定性',4,'Lij为3供电×3负载、1uF/50mΩ；Eijk为1.8V、C/ESR/负载的完整8个极端组合。')
        by={q['tag']:q for q in r['stb_diagnostic']['matrix']};fv={q['tag']:q for q in r['fvf_diagnostic']['matrix']};rows=[]
        for q in [x for x in r['matrix'] if x['kind']=='loop']:
            tag=q['tag'];z=q['values'];st=by[tag]['values'];rows.append([tag,f'{q["vin"]:.2f}',f'{q["load"]*1e3:g}',f'{q["cap"]*1e6:g}/{q["esr"]*1e3:g}',f'{z["phase_margin_deg"]:.2f}',f'{st["phase_margin_deg"]:.2f}',f'{st["ugb_hz"]/1e3:.2f}',f'{fv[tag]["values"]["phase_margin_deg"]:.2f}'])
        table(fig,[.07,.285,.86,.57],['点','VIN','IL/mA','C/uF ESR/mΩ','源PM','STB PM','STB/kHz','FVF PM'],rows,[.105,.09,.10,.175,.12,.13,.15,.13],8.0)
        para(fig,.244,'每个主STB均从1 Hz扫到100 MHz，恰有一次下降0 dB交越，此后无回穿。局部FVF从1 Hz扫到1 GHz，探针在pbuf→MBUF栅、主反馈保持闭合；17点全部一次交越，PM最小59.047°，额外工程下限45°。',9.3)
        para(fig,.139,'源算法为−V(gate_drive)/V(gate)，独立STB在两端间放iprobe。功率管反向电容和节点加载会使简单电压比偏离真实返回比，因此两种定义均保留。本例不只依据原算法的54.137°判定完成等级。',9.3)
        para(fig,.065,'仅TT矩阵；原PVT×输出网络交互中的非nominal行未运行，不能用这些17点代替全签核。',9.1)
        save(pdf,fig)

        fig=page('主环路频响、供电抑制与输出噪声',5,'全部曲线来自最终电路的真实PSF；固定积分带宽和输出负载。')
        axes=[fig.add_axes(b) for b in [[.12,.575,.345,.27],[.595,.575,.345,.27],[.12,.19,.345,.27],[.595,.19,.345,.27]]]
        for q in r['stb_diagnostic']['matrix']:
            x=data(ROOT/r['run_dirs'][1],'stb'+q['tag']+'.stb');h=-x['loopGain'];axes[0].semilogx(x['freq'],20*np.log10(abs(h)),lw=.7);axes[1].semilogx(x['freq'],np.unwrap(np.angle(h))*180/np.pi,lw=.7)
        axes[0].axhline(0,color=GRAY,lw=.7);axes[1].axhline(-180,color=GRAY,lw=.7)
        axes[0].set(xlabel='Frequency (Hz)',ylabel='STB return ratio (dB)');axes[1].set(xlabel='Frequency (Hz)',ylabel='STB phase (deg)',ylim=(-240,10))
        for q in psrows:
            tag=q['tag'];axes[2].semilogx(a['freq'],-20*np.log10(abs(a['vout'+tag]/a['vin'+tag])),lw=.8)
        axes[2].set(xlabel='Frequency (Hz)',ylabel='PSRR (dB)');axes[3].loglog(n['freq'],n['out']*1e9,color=BLUE);axes[3].set(xlabel='Frequency (Hz)',ylabel='Output noise (nV/sqrt(Hz))')
        for ax in axes:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.112,'AC每十倍频100点；原提取按log(f)插值交越，PSRR读取原指定频点。输出噪声10 Hz–1 MHz共501点，sqrt(∫en²df)=66.672 uVrms；外部反馈电阻的模型热噪声按原测试连接保留。',9.3)
        save(pdf,fig)

        fig=page('启动、负载/电源跳变与压差',6,'瞬态完整70us、最大内部步2ns、保存步5ns；建立窗保持原定义，不因容差放宽而扩大。')
        axes=[fig.add_axes(b) for b in [[.12,.575,.345,.27],[.595,.575,.345,.27],[.12,.245,.345,.235],[.595,.245,.345,.235]]]
        axes[0].plot(t['time']*1e6,t['voutS'],color=BLUE);axes[0].plot(t['time']*1e6,t['vinS'],color=GRAY,ls='--');axes[0].axhspan(1.176,1.224,color=GREEN,alpha=.13);axes[0].set(xlabel='Startup time (us)',ylabel='Voltage (V)')
        for ax,tag,label in [(axes[1],'T','Load-step error (mV)'),(axes[2],'L','Line-step error (mV)')]:
            ax.plot(t['time']*1e6,(t['vout'+tag]-1.2)*1e3,color=BLUE);ax.axhspan(-15,15,color=GREEN,alpha=.13);ax.set(xlabel='Time (us)',ylabel=label,xlim=(15,65));ax.axvline(20,color=GRAY,ls=':',lw=.8);ax.axvline(40.2,color=GRAY,ls=':',lw=.8)
        axes[3].plot(s['vinD'],s['voutD'],color=BLUE);axes[3].axhline(1.188,color=GREEN,ls='--');axes[3].axvline(1.188+v['dropout_V'],color=GRAY,ls=':');axes[3].set(xlabel='VIN (V), 30mA load',ylabel='VOUT (V)')
        for ax in axes:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.177,'启动VIN在1–21us升至1.8V，负载120Ω；持续90%在24.210us，斜坡后7.395us进入并保持±2%。负载1→25→1mA，电源1.98→1.62→1.98V，均200ns边沿；20–40.2us和40.2–65us分别验收。',9.1)
        para(fig,.117,'负载建立0表示全窗已在±15mV内，并非响应瞬时完成。压差326点、步2mV，首次持续超过1.188V处线性插值：VIN≈1.355593V，压差167.593mV。',9.1)
        para(fig,.068,'低VIN失调区的理想30mA负载会把VOUT拉成负值；没有输出钳位或欠压卸载模型。该区不作可用电压/应力保证，压差仅取持续进入阈值处。',8.8)
        save(pdf,fig)

        fig=page('可复用认识、精确网表与证据',7,'最终12只MOS、原生片阻与MIM；gate_drive和gate在DUT内保持分离。')
        para(fig,.862,'关键失败：无缓冲候选源算法PM71.01°，但同电路真实STB最小仅27.41°，因此撤回。NMOS输入级加PMOS跟随后，重载低压可失去输入管漏端余量；最终改用PMOS输入。小功率管版本又因1uF启动充电不足失败，最终m30→60。',9.3)
        para(fig,.742,'补偿取舍：30kΩ/200pF降低高频增益并恢复相位，但引入约0.206mm²电容面积。不得仅优化原测试的电压比PM，或把静态稳压通过当作启动通过。最终真实STB53.861°使用15%边界；所有其他门槛至多使用10%放宽。',9.3)
        fig.text(.075,.615,(case/'circuit.scs').read_text(),fontsize=8.0,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.35)
        para(fig,.366,'复现：既有Bridge Python运行 scripts/case07_ldo.py --tail-uA 100 --input-gmid 18 --mirror-L 4 --mirror-gmid 14 --pinput --fvf --pass-m 60 --lag-C-pF 200 --lag-R 30000 --full；同模块local_fvf()生成局部诊断。PDF：scripts/review_pdf.py 7。',8.7)
        para(fig,.258,'最终运行：\n'+'\n'.join(r['run_dirs']+[r['fvf_diagnostic']['run_dir']]),8.2)
        para(fig,.114,'原instruction/reference/正式verifier/bench冻结于source；每次运行保存inputs、模型/依赖SHA、日志与PSF。最终五次运行均无警告，geometry.json、sizing.json及verification_audit.json记录单位几何、查表与审计。源任务：sky130-ldo-ota5-robust-pvt-mc。',9.1)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=7,render_review_pending=True))
    update_case(7,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
