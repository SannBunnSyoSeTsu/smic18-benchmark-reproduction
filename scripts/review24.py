"""Full nominal review for the five-stage SMIC18 current-starved ring VCO."""
from review_pdf import *


def make24():
    case=ROOT/'cases/24-ring-vco';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text())
    op=json.loads((case/'operating_conditions.json').read_text());xc=json.loads((case/'frequency_crosscheck.json').read_text())
    d=data(ROOT/r['run_dirs'][0],'tran.tran');p=data(ROOT/r['run_dirs'][1],'tran.tran');v=r['values'];qs=r['tuning']['plateaus']
    out=ROOT/'reports/24-ring-vco-review.pdf'
    with PdfPages(out,metadata={'Title':'24 SMIC18 电流饥饿环形VCO审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('24 | 电流饥饿环形 VCO 审查',1,'结论：四平台调谐、启动、波形、功耗及成对推频全部达到原nominal门槛。')
        para(fig,.849,'条件：SMIC18MMRF tt、27°C，调谐供电1.8 V，外载20 fF。控制电压0.9/1.0/1.1/1.2 V，各稳定平台1 us。推频保留TT/27°C、VCTRL=1.1 V、VDD=1.71/1.89 V。',9.4)
        info=[('f(0.9 V)下界','f_0p9_min_Hz',1e-6,'MHz'),('f(0.9 V)上界','f_0p9_max_Hz',1e-6,'MHz'),
          ('f(1.2 V)','f_1p2_Hz',1e-6,'MHz'),('高/低调谐比','tuning_ratio',1,'比值'),
          ('最小KVCO','kvco_min_Hz_per_V',1e-6,'MHz/V'),('KVCO最大/最小','kvco_linearity_ratio',1,'比值'),
          ('最大频率漂移','frequency_settling_drift',100,'%'),('占空偏离50%','duty_error_from_half',100,'百分点'),
          ('首次上升过半轨','startup_time_s',1e9,'ns'),('四平台最坏低值','output_low_fraction',100,'%VDD'),
          ('四平台最坏高值','output_high_fraction',100,'%VDD'),('1.2 V控制平均功耗','power_W',1e6,'uW'),
          ('供电推频绝对值','supply_pushing_pct_per_V',1,'%/V')]
        rows=[]
        for label,key,k,u in info:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([label,f"{g['value']*k:.6g}"]+[sign+f"{g['limits'][z]*k:.5g}" for z in ['original','10pct','15pct']]+[u])
        table(fig,[.07,.289,.86,.484],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.285,.18,.135,.135,.14,.125],8.2)
        para(fig,.245,'实际高电平占空52.690%，满足45–55%；原verifier对高/低相位取较短者，报告47.310%。放宽只扩大50%中心两侧允许误差，不移动中心。',9.3)
        para(fig,.166,'四平台频率严格递增；4组五周期测量、4组晚期两周期测量都在各自平台结束前完成。两路推频各有完整五周期。窗口完整性、起振有效性和有限数据不放宽。',9.2)
        para(fig,.077,'未执行其余26个调谐PVT点、SS/FF推频、失配、相噪/抖动和PEX。近零确定性频率漂移只说明两个时间窗周期一致，不能解释为真实振荡器无抖动。',9.1)
        save(pdf,fig)

        fig=page('HD 延迟单元与模拟限流偏置',2,'环内数字反相器保持原厂内部MOS，仅在供电端外接gm/ID定尺寸限流管。')
        ax=fig.add_axes([.07,.626,.86,.253]);ax.set(xlim=(0,11),ylim=(-.3,5.5));ax.axis('off')
        ax.add_patch(Rectangle((.1,3.75),4.25,1.15,fill=False,edgecolor=BLUE));ax.text(2.22,4.32,'VCTRL → MVIN + RDEG 47kΩ\nMPDIO → MPSRC → MNDIO',ha='center',va='center',fontsize=9)
        ax.plot([4.35,9.9],[4.65,4.65],color=GREEN);ax.text(5.9,4.91,'pdio / ndio 控制5对限流管',fontsize=8,color=GREEN)
        for i in range(5):
            x=.35+i*2.05
            ax.add_patch(Rectangle((x,1.25),1.5,.85,fill=False,edgecolor=BLUE));ax.text(x+.75,1.67,f'INHDV2\nn{i+1}',ha='center',va='center',fontsize=8)
            ax.plot([x+.75,x+.75],[2.1,2.6],color=GREEN);ax.text(x+.75,2.82,'p18 限流',ha='center',fontsize=7.5,color=GREEN)
            ax.plot([x+.75,x+.75],[.7,1.25],color=GREEN);ax.text(x+.75,.4,'n18 限流',ha='center',fontsize=7.5,color=GREEN)
            if i<4:ax.annotate('',xy=(x+2.05,1.67),xytext=(x+1.5,1.67),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.plot([10.05,10.7,10.7,.1,.1,.35],[1.67,1.67,3.43,3.43,1.67,1.67],color=BLUE,lw=.9)
        ax.text(5.5,3.59,'n5反馈到第1级；每级输出对地30 fF',fontsize=8,ha='center')
        ax.text(.35,-.14,'n5 → INHDV0 → INHDV2 → vout；两个输出缓冲接全局VDD/VSS。',fontsize=8.3)
        rows=[]
        for key in ['n18','p18']:
            q=s['roles'][key];rows.append([key,f"{q['rounded_W_um']:.2f}/0.36",'15',f"{q['id_w_Apm']:.4f}",f"{q['Vgs_V']:.4f}",f"{q['gmro']:.2f}"])
        table(fig,[.07,.471,.86,.100],['模拟单位','W/L (um)','gm/ID','ID/W(uA/um)','VGS表点/V','gm·ro'],rows,[.18,.18,.13,.20,.17,.14],8.4)
        para(fig,.433,'LUT点：27°C、|VDS|=0.45 V、VBS=0、参考W=10 um、ID=10 uA。n18单位2.04/0.36 um，用于MVIN/MNDIO/五个下限流；p18单位8.52/0.36 um，用于二极管、转接镜及五个上限流。',9.2)
        rows=[[q['control_V'],f"{q['devices']['MVIN']['ids']*1e6:.4f}",f"{q['devices']['MVIN']['gmid']:.3f}",f"{q['devices']['MVIN']['min_saturation_headroom_V']:.4f}"] for q in op['plateaus']]
        table(fig,[.07,.230,.86,.147],['VCTRL/V','MVIN均值/uA','实际gm/ID','最小饱和余量/V'],rows,[.20,.27,.25,.28],8.6)
        para(fig,.189,'表中实际值取稳定平台时间加权平均；余量为采样到的最小|VDS|−|VDSAT|。MVIN源极升高产生体效应，所以实际VGS不能直接等同零体偏LUT；本次实际gm/ID约14.45–16.93。',9.2)
        para(fig,.091,'INHDV2原厂Wn/Wp=1.17/1.76 um，INHDV0=0.60/0.90 um，L均0.18 um。核心VDD/VSS接虚拟轨sXt/sXb；VNW/VPW始终接全局VDD/VSS，内部MOS尺寸和模型未改。',9.0)
        save(pdf,fig)

        fig=page('调谐、线性度与固定测量窗口',3,'所有四个控制平台均测五个完整周期；最低频率不能借用下一个控制平台的边沿。')
        ax=fig.add_axes([.11,.619,.37,.229]);ax.plot([q['control_V'] for q in qs],[q['frequency_Hz']/1e6 for q in qs],'o-',color=BLUE)
        ax.axhline(25,color=GRAY,ls='--',lw=.8);ax.set(xlabel='VCTRL (V)',ylabel='Frequency (MHz)',xticks=[.9,1,1.1,1.2]);ax.grid(alpha=.2)
        ax=fig.add_axes([.59,.619,.35,.229]);ax.bar([.95,1.05,1.15],np.array(r['tuning']['kvco_Hz_per_V'])/1e6,width=.064,color=GREEN)
        ax.axhline(30,color=GRAY,ls='--',lw=.8);ax.set(xlabel='Interval midpoint (V)',ylabel='KVCO (MHz/V)',xticks=[.95,1.05,1.15],ylim=(0,50));ax.grid(axis='y',alpha=.2)
        rows=[]
        for q in qs:
            rows.append([q['control_V'],f"{q['frequency_Hz']/1e6:.6f}",f"{q['drift']*100:.7g}",f"{q['period_end_s']*1e6:.6f}",f"{q['late_end_s']*1e6:.6f}",f"{q['plateau_end_s']*1e6:.3f}"])
        table(fig,[.07,.380,.86,.158],['控制/V','频率/MHz','早晚漂移/%','五周期终点/us','晚2周期终点/us','平台终点/us'],rows,[.12,.19,.19,.19,.19,.12],8.1)
        para(fig,.335,'频率=5/(第6上升沿−第1上升沿)，选沿起点是平台开始后300 ns。漂移比较早期与晚期各两周期：|fearly−flate|/mean；晚期选沿起点是平台结束前300 ns。平台分别开始于51、1052、2053、3054 ns。',9.3)
        para(fig,.230,'最小KVCO=40.752 MHz/V，最大/最小=1.07673；3个斜率都为正。1.1 V控制频率25.227 MHz，0.9→1.2 V调谐比1.75153。测得的是四点局部区间斜率，不声称更宽控制范围内线性。',9.2)
        para(fig,.130,f"交叉核验：把各稳定窗内全部10/13/17/19个完整周期求平均，与合同五周期结果最大相对差{xc['max_relative_difference']*100:.7g}%。本次无求解警告；确定性模型不包含相噪、热噪声或失配抖动。",9.1)
        save(pdf,fig)

        fig=page('真实起振、占空比与虚拟电源',4,'普通DC初始化；控制由0 V在50–51 ns升至0.9 V，没有额外kick或强制初值。')
        ax=fig.add_axes([.11,.663,.83,.196]);ix=d['time']<=220e-9
        ax.plot(d['time'][ix]*1e9,d['vout'][ix],color=BLUE,lw=1,label='vout');ax.plot(d['time'][ix]*1e9,d['vctrl'][ix],color=GREEN,ls='--',label='vctrl')
        ax.axvline(r['tuning']['startup_crossing_s']*1e9,color=GRAY,ls=':',label='first rising VDD/2');ax.axhline(.9,color=GRAY,lw=.6)
        ax.set(xlabel='Time (ns)',ylabel='Voltage (V)',xlim=(0,220));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper right')
        ax=fig.add_axes([.11,.380,.83,.186]);start=2.35e-6;end=2.48e-6;ix=(d['time']>=start)&(d['time']<=end)
        for key,label,style in [('vout','vout','-'),('XVCO.s1t','stage1 upper rail','--'),('XVCO.s1b','stage1 lower rail',':')]:ax.plot((d['time'][ix]-start)*1e9,d[key][ix],label=label,ls=style,lw=1)
        ax.set(xlabel='Time after 2.35us (ns)',ylabel='Voltage (V)',xlim=(0,130));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper right')
        para(fig,.314,f"起振首次上升过半电源于{r['tuning']['startup_crossing_s']*1e9:.5f} ns，相对51 ns平台开始为{v['startup_time_s']*1e9:.5f} ns。四平台输出最小值约−0.865/−1.061/−1.251/−1.434 mV，最大值约1.8024–1.8036 V，均跨越10%与90%阈值。",9.2)
        para(fig,.212,'1.1 V真实高电平占空52.690%；原verifier报告较短相位47.310%，两者不是两次测量冲突。HD输出缓冲承担20 fF，环内虚拟电源随周期移动，不能把sXt/sXb误连成HD阱电位。',9.2)
        para(fig,.114,'稳定段第1级虚拟轨约−3.83 mV至1.80406 V；毫伏级越轨来自瞬态寄生耦合。限流管在充放电过程中并非全程饱和，靠近轨端退出饱和属于工作机制；静态偏置三管保持正饱和余量。',9.2)
        save(pdf,fig)

        fig=page('供电推频与完整 VDD 功耗',5,'推频是本题nominal敏感度维度，保留1.71 V和1.89 V两路实际瞬态。')
        ps=r['pushing']['supplies'];rows=[[q['VDD_V'],f"{q['frequency_Hz']/1e6:.6f}",f"{q['edges_s'][0]*1e9:.6f}",f"{q['edges_s'][-1]*1e9:.6f}"] for q in ps]
        table(fig,[.07,.722,.86,.122],['VDD/V','五周期频率/MHz','起始沿/ns','结束沿/ns'],rows,[.18,.28,.27,.27],9)
        ax=fig.add_axes([.11,.435,.83,.207]);ix=(p['time']>=550e-9)&(p['time']<=800e-9)
        ax.plot(p['time'][ix]*1e9,p['outLOW'][ix],label='VDD=1.71V',color=BLUE,lw=1);ax.plot(p['time'][ix]*1e9,p['outHIGH'][ix],label='VDD=1.89V',color=GREEN,ls='--',lw=1)
        ax.set(xlabel='Time (ns)',ylabel='Output (V)',xlim=(550,800));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper right')
        para(fig,.374,'推频=|fhigh−flow|/mean(fhigh,flow)/0.18×100=83.5229 %/V。VDD升高反而降低频率：电流限制下每次充放电需要更大的电压摆幅，偏置/体效应/寄生也参与；验收使用绝对灵敏度。',9.2)
        rows=[[q['control_V'],f"{q['average_bias_current_A']*1e6:.4f}",f"{q['average_VDD_current_A']*1e6:.4f}"] for q in qs]
        table(fig,[.07,.183,.86,.137],['VCTRL/V','V→I支路平均/uA','全VDD稳定窗平均/uA'],rows,[.2,.36,.44],8.8)
        para(fig,.141,'功耗门槛使用原3.754–4.054 us窗口：−1.8×mean(I(VDD))=84.6706 uW。包含V→I、镜像支路、五级环和两级输出缓冲；上表全稳定窗均值与此300 ns门槛窗口略有差别。',9.1)
        para(fig,.086,'理想RDEG和五个30 fF电容为原任务明确允许项，本次未替代成实际工艺无源件。结果不含其片阻/容值PVT、匹配和布局面积保证。',8.9)
        save(pdf,fig)

        fig=page('完整网表、复现与证据范围',6,'保留全部设计尺寸、HD接口与两类bench的输入快照和真实PSF。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.858,body,fontsize=8.25,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.34)
        para(fig,.396,'DUT：14只模拟MOS + 7个原厂HD反相器 + 47 kΩ源极电阻 + 五个30 fF节点电容。所有HD定义include都在bench层；snapshot闭包和模型哈希见各run.json。',9.2)
        para(fig,.307,'运行：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python\n scripts/case24_ring_vco.py\nPDF：同一Python执行 scripts/review_pdf.py 24',8.8)
        para(fig,.218,'真实输出目录：\n'+'\n'.join(r['run_dirs'])+'\n每目录包含inputs、run.json、output/bench.raw和measurements.json。',8.6)
        para(fig,.127,'原instruction、正式verifier、bench与reference冻结于cases/24-ring-vco/source/。首次LUT候选即通过；未用原Sky130成绩替代测量。除本轮nominal外，PVT、失配、相噪/抖动及PEX均未验证。',9.0)
        para(fig,.057,'电路SHA256：'+sha(case/'circuit.scs'),7.2)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(24,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out


if __name__=='__main__':print(make24())
