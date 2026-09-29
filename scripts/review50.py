"""Review PDF for the nominal SMIC18 gain-boosted folded amplifier."""
from review_pdf import *

def make50():
    case=ROOT/'cases/50-gainboosted-folded';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values'];runs={k:ROOT/x for k,x in r['runs_by_analysis'].items()};a=data(runs['op_ac'],'ac.ac');h=-a['vout']/a['vinn'];n=data(runs['noise'],'noise.noise',required=['in','out']);d=data(runs['range'],'swing.dc');t=data(runs['settling'],'tran.tran');loops={k:data(ROOT/q['run_dir'],'localstb.stb') for k,q in r['local_booster_loops'].items()};out=ROOT/'reports/50-gainboosted-folded-review.pdf'
    with PdfPages(out,metadata={'Title':'50 SMIC18 增益提升折叠共栅OTA审查','Author':'SMIC18 benchmark reproduction','Subject':'Four original nominal groups and two local booster loop diagnostics'}) as pdf:
        fig=page('50 | 增益提升折叠共栅 OTA 审查',1,'结论：四组 nominal 原门槛全部通过，无性能放宽；两个增益提升环路也通过独立诊断。')
        para(fig,.854,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；50 uA参考、0.9 V输入/输出目标、1 pF负载。41只晶体管，双辅助增益提升折叠一级、级联共源输出级，1.3 pF串1 kΩ Miller补偿。',9.2)
        specs=[('返回比增益 @10Hz','dc_gain_db',1,'dB'),('UGB','ugb_hz',1e-6,'MHz'),('主环路PM','phase_margin_deg',1,'deg'),('静态输出误差','output_common_mode_error_v',1e3,'mV'),('VDD功耗，含参考','power_w',1e3,'mW'),('输入噪声 10Hz–10MHz','input_noise_vrms',1e6,'uVrms'),('连续合格命令区间','closed_loop_range_vpp',1,'Vpp'),('资格区间最大采样误差','closed_loop_tracking_error_v_max',1e3,'mV'),('上升最后进入时间','settling_rise_time_s',1e9,'ns'),('下降最后进入时间','settling_fall_time_s',1e9,'ns'),('上升末5ns均值误差','rise_static_error_v',1e3,'mV'),('下降末5ns均值误差','fall_static_error_v',1e3,'mV'),('最坏均值误差/0.1V','settling_static_error_fraction',100,'%')]
        rows=[]
        for label,key,k,u in specs:
            q=r['gates'][key];sign='≥' if q['sense']=='min' else '≤';rows.append([label,f"{q['value']*k:.4f}",*[f"{sign}{q['limits'][z]*k:.3f}" for z in ['original','10pct','15pct']],u])
        table(fig,[.07,.307,.86,.48],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.33,.14,.14,.14,.14,.11],8)
        para(fig,.266,'10 Hz–100 GHz返回比只有一次下降0 dB交越，之后不回穿。121点命令网格及双向完整观察窗保留；范围资格20 mV和建立0.7 mV固定窗均未改变。独立GPC/GNC局部PM为88.69°/87.95°。',9.2)
        para(fig,.172,'所有41只MOS中心OP饱和余量为正，最小61.94 mV。全部单位W≤14.24 um，超宽总尺寸用m复制；实际Spectre日志没有模型尺寸警告。没有数字单元或DUT内部理想源。',9.2)
        para(fig,.079,'边界：未运行其余26个OP/AC与噪声PVT点、另外两组范围/建立代表点、MC、寄生或无源容差。130 dB名义增益和微伏级偏差不能当成随机失配精度保证。',9)
        save(pdf,fig)

        fig=page('架构、偏置与gm/ID初值',2,'两个辅助放大器调节关键共栅栅压，主电流镜把差分信号转换为单端一级输出。')
        ax=fig.add_axes([.07,.655,.86,.215]);ax.axis('off');ax.set(xlim=(0,12),ylim=(0,4.4))
        for x,y,w,hh,label in [(0,2.25,3.3,1.25,'NMOS输入对 + 50Ω\nPMOS折叠支路'),(4.5,2.25,3.0,1.25,'PMOS/NMOS共栅\n宽摆幅NMOS镜'),(8.7,2.25,3.2,1.25,'级联NMOS共源\n固定PMOS负载')]:
            ax.add_patch(Rectangle((x,y),w,hh,fill=False,edgecolor=BLUE));ax.text(x+w/2,y+hh/2,label,ha='center',va='center',fontsize=8.5)
        for x0,x1 in [(3.3,4.5),(7.5,8.7)]:ax.annotate('',xy=(x1,2.88),xytext=(x0,2.88),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.text(8.08,3.1,'nfirst',ha='center',fontsize=8.5);ax.text(11.9,3.92,'VOUT / 1pF',ha='right',fontsize=8.5)
        ax.plot([8.15,8.15,11.75,11.75],[2.88,.35,.35,2.25],color=GREEN);ax.text(9.9,.58,'1.3pF + 1kohm Miller',ha='center',color=GREEN,fontsize=8.6)
        ax.text(.03,1.6,'p2 -> NF level shift -> PMOS auxiliary -> gpc',fontsize=8.3)
        ax.text(.03,1.0,'n2 -> PMOS auxiliary -> gnc; refs from iref',fontsize=8.3)
        ax.text(.03,.4,'gpc:3pF toVDD; gnc:9pF toVSS',fontsize=8.3)
        roles=[('input','MINP/N','15'),('n_bias','参考/尾源/镜/电流复制','1 / 5 / 10 / 30'),('p_bias','偏置/折叠源/辅助尾源','1 / 4 / 16 / 25'),('n_cascode_diode','MNCB / MNRS / MMD','1 / 1 / 10'),('n_cascode_boosted','MMO','10'),('p_cascode','MPPC/MPRS / MFCP,N','1 / 1 / 10'),('second','MOUT','90'),('out_cascode','MOUTC','90'),('output_load','MOBP / MLOAD','1 / 90'),('aux_pinput','MPA,B / MNA,B','2 / 8'),('aux_nload','MPMA,B / MNMA,B','2 / 8'),('level_shift','MHSF / MHRF','1')]
        rows=[]
        for k,label,m in roles:
            q=s['roles'][k];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:g}"])
        table(fig,[.07,.277,.86,.339],['角色','模型','单位W/L um','m','gm/ID'],rows,[.34,.10,.18,.25,.13],7.7)
        para(fig,.234,'输入目标150 uA/支、gm/ID18给gm≈2.7 mS；50 Ω源退化后约2.38 mS。输出目标900 uA、L0.18 um、gm/ID8，串联1 kΩ大于1/gmout，可把Miller前馈零点移到左半平面；真实多节点响应仍用全频段验证。',9.1)
        para(fig,.107,'输入L0.5 um需要补扫，数据只写本项目lut_supplement。其余角色复用现有SMIC18 LUT；每项查询、VDS、Wref与SHA-256保存在sizing.json。LUT为初值，最终含窄宽与体效应的实际OP如下页。',9.1)
        save(pdf,fig)

        fig=page('工作点、余量与名义高增益',3,'全部41只MOS在中心OP有正的|VDS|−|VDSAT|；表列主信号路径和辅助环路的关键器件。')
        names=['MINP','MINN','MTAIL','MFP','MFN','MFCP','MFCN','MMD','MMO','MCD','MCO','MPA','MPB','MNA','MNB','MOUT','MOUTC','MLOAD'];rows=[]
        for name in names:
            q=r['operating_point'][name];rows.append([name,f"{abs(q['ids'])*1e6:.3f}",f"{q['gmid']:.3f}",f"{q['gmro']:.2f}",f"{abs(q['vds']):.4f}",f"{q['headroom_V']*1e3:.2f}"])
        table(fig,[.07,.370,.86,.489],['MOS','|Id| uA','gm/ID','gm/gds','|VDS| V','饱和余量mV'],rows,[.18,.17,.15,.16,.15,.19],8.2)
        para(fig,.329,'主节点：tail0.32576 V，p1/p2=1.44735/1.43874 V，n1/n2=0.25432/0.26742 V，nfirst0.63549 V，nout0.33459 V。输出0.900002832 V，主输入147.9 uA/支，输出级941.44 uA。',9.2)
        para(fig,.213,'GPC辅助把p2与电流复制pref1.44195 V比较，两个匹配NMOS跟随器将电位移至hs/hr≈0.65 V；GNC辅助直接比较n2与nref0.27223 V。没有供电电阻分压参考，也没有理想误差放大器。',9.2)
        para(fig,.103,'MNB的61.94 mV是最小中心余量，不能推广为全PVT保证。10 Hz的有载内部比值|nfirst/vinn|=105.93 dB、|vout/nfirst|=39.93 dB，相乘等于145.86 dB；这核对数量级，不把两级当成互不加载的独立放大器。',9.1)
        save(pdf,fig)

        fig=page('主环路、闭环噪声与输入LUT',4,'主返回比T=−Vout/Vinn；噪声测试采用单位反馈并以VIN源折算到输入。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.225,top=.85,hspace=.42,wspace=.39)
        axs[0,0].semilogx(a['freq'],20*np.log10(abs(h)),color=BLUE);axs[0,0].axhline(0,color=GRAY,lw=.7);axs[0,0].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Return ratio (dB)',xlim=(10,1e11))
        axs[0,1].semilogx(a['freq'],np.unwrap(np.angle(h))*180/np.pi,color=BLUE);axs[0,1].axvline(v['ugb_hz'],color=GREEN,ls='--');axs[0,1].axhline(-180,color=GRAY,lw=.7);axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Return phase (deg)',xlim=(10,1e11))
        axs[1,0].loglog(n['freq'],abs(n['in'])*1e9,color=BLUE);axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Input noise (nV/sqrt(Hz))',xlim=(10,1e7))
        lut=json.loads(Path(s['roles']['input']['lut_path']).read_text())['data'];gm=np.array(lut['gmid']);m=(gm>=4)&(gm<=24)
        axs[1,1].plot(gm[m],np.array(lut['ft_Hz'])[m]*1e-9,color=BLUE);axs[1,1].axvline(18,color=GREEN,ls='--');axs[1,1].set(xlabel='gm/ID (1/V)',ylabel='Input L=0.5um fT (GHz)',xlim=(4,24));axs[1,1].scatter([18],[s['roles']['input']['ft_Hz']/1e9],color=GREEN,s=18)
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=7.6)
        para(fig,.183,'噪声频带固定10 Hz–10 MHz，共601点；sqrt(∫en²df)的PSD梯形积分30.2883 uVrms，幂律插值积分30.2877 uVrms，相差0.001978%。没有用UGB替换积分上限，也没有缩小带宽。',9.2)
        para(fig,.098,'补扫n18 L0.5 um、Wref10 um、VDS0.9 V、VBS0：603点单调反型分支，gm/ID18处fT1.653 GHz、gm/gds220.27。电流密度、VGS、fT曲线平滑；完整四图和数值校验见50-input-lut-validation.png及lut_validation.json。',9.1)
        save(pdf,fig)

        fig=page('两个增益提升环路与补偿迭代',5,'零压探针位于辅助输出到主共栅栅极，保留原DC连接和闭合的全局单位反馈。')
        axs=fig.subplots(1,2);fig.subplots_adjust(left=.12,right=.94,bottom=.55,top=.845,wspace=.39)
        for k,color in [('gpc',BLUE),('gnc',GREEN)]:
            q=loops[k];hh=-q['loopGain'];axs[0].semilogx(q['freq'],20*np.log10(abs(hh)),color=color,label=k.upper());axs[1].semilogx(q['freq'],np.unwrap(np.angle(hh))*180/np.pi,color=color,label=k.upper())
        axs[0].axhline(0,color=GRAY,lw=.7);axs[0].set(xlabel='Frequency (Hz)',ylabel='Local return ratio (dB)',xlim=(1,1e11));axs[1].axhline(-180,color=GRAY,lw=.7);axs[1].set(xlabel='Frequency (Hz)',ylabel='Local phase (deg)',xlim=(1,1e11))
        for ax in axs:ax.grid(which='both',alpha=.2);ax.legend(fontsize=8);ax.tick_params(labelsize=8)
        rows=[['GPC局部环路','35.744 dB','9.032 MHz','88.690°','1 / 无回穿'],['GNC局部环路','27.533 dB','15.301 MHz','87.951°','1 / 无回穿']]
        table(fig,[.07,.404,.86,.098],['诊断','1Hz增益','UGB','PM','下降交越'],rows,[.25,.18,.19,.17,.21],8.2)
        rows=[['初版','1.5','400','159.449','49.350','带宽/PM失败'],['中间版本','1.2','800','224.840','58.219','PM未达原门槛'],['最终','1.3','1000','261.464','62.400','全部原门槛通过']]
        table(fig,[.07,.235,.86,.128],['主补偿版本','Cc/pF','Rz/Ω','UGB/MHz','PM/deg','结论'],rows,[.19,.14,.14,.17,.16,.20],8.1)
        para(fig,.197,'3 pF/9 pF把辅助输出带宽压到主环路UGB以下，同时保留DC增益提升。两个PM与Spectre原生日志相差不足0.0001°，探针对输出OP扰动不超过12 pV。45°是独立诊断下限，主环路仍按原60°验收。',9.1)
        para(fig,.087,'主Miller电阻增大提高零点超前；并配合Cc调整，解决初版相位不足。内部多极点使UGB不能只按gm/Cc比例推断。未对辅助环路做PVT，也没有把主环路稳定性作为局部环路的替代。',9.1)
        save(pdf,fig)

        fig=page('连续区间与双向最后进入',6,'原定义保留：范围只跨相邻失败/合格点插值；建立使用采样点上的完整余下窗口判据。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.255,top=.85,hspace=.42,wspace=.38)
        axs[0,0].plot(d['vinp'],d['vinp'],color=GRAY,ls='--',label='Command');axs[0,0].plot(d['vinp'],d['vout'],color=BLUE,label='Output');axs[0,0].axvspan(v['closed_loop_range_low_v'],1.5,color=GREEN,alpha=.13);axs[0,0].set(xlabel='Unity-feedback command (V)',ylabel='Output (V)',xlim=(.3,1.5));axs[0,0].legend(fontsize=7)
        axs[0,1].plot(d['vinp'],(d['vout']-d['vinp'])*1e3,color=BLUE);axs[0,1].axhspan(-20,20,color=GREEN,alpha=.13);axs[0,1].axvline(v['closed_loop_range_low_v'],color=GREEN,ls='--');axs[0,1].set(xlabel='Unity-feedback command (V)',ylabel='Tracking error (mV)',xlim=(.3,1.5))
        for ax,reference,target,key,label in [(axs[1,0],20.5e-9,.95,'settling_rise_time_s','Rising'),(axs[1,1],121.5e-9,.85,'settling_fall_time_s','Falling')]:
            tt=(t['time']-reference)*1e9;ax.plot(tt,(t['vout']-target)*1e3,color=BLUE);ax.axhspan(-.7,.7,color=GREEN,alpha=.17);ax.axvline(v[key]*1e9,color=GREEN,ls='--');ax.set(xlim=(-1,20),ylim=(-3,3),xlabel='Time after edge midpoint (ns)',ylabel=label+' target error, zoom (mV)')
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=7.5)
        para(fig,.216,'完整121点0.30–1.50 V、步长10 mV；114个合格采样点从0.37 V至1.50 V，低端在0.36/0.37 V之间按20 mV边界插值，得0.369963 V，连续跨度1.130037 V。1.50 V是扫描上界，未推定物理最大摆幅。',9.1)
        para(fig,.123,'命令0.85→0.95→0.85 V，边沿20–21 ns与121–122 ns。时间原点为20.5/121.5 ns，观察至119.5/240 ns；固定目标±0.7 mV。末5 ns均值窗为114.5–119.5 ns和235–240 ns，误差2.748/3.319 uV。',9.1)
        para(fig,.079,'波形输出50 ps采样、内部最大步长25 ps；原算法取末次越界后首个合格样本，未插值。图仅放大边沿，计算覆盖完整发布窗口。',8.7)
        save(pdf,fig)

        fig=page('精确网表与复现证据',7,'D G S B端序；m复制合法单位管，PMOS体端统一接VDD；精确偏置与嵌套连接如下。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.863,body,fontsize=7.8,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.12)
        para(fig,.257,'复现：既有Bridge Python运行 scripts/case50_gainboosted_folded.py，随后加--mode loops检查局部环路；同一Python运行scripts/review_pdf.py 50生成本报告。源任务：sky130-folded-cascode-ota-gain130-pm60-noise50uv-pvt。',8.7)
        para(fig,.170,'正式运行（OP/AC、噪声、范围、建立、GPC、GNC）：\n'+'\n'.join(r['run_dirs']+[x['run_dir'] for x in r['local_booster_loops'].values()]),7.6)
        para(fig,.071,'冻结source、run inputs、原始PSF和全部模型/LUT哈希均保留；知识稿和审计在case目录。\n精确电路SHA-256：'+sha(case/'circuit.scs'),7.4)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),geometry_sha256=sha(case/'geometry.json'),generated_at=now(),pages=7,render_review_pending=True))
    update_case(50,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

if __name__=='__main__':print(make50())
