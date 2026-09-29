"""Self-contained nominal evidence for the2MHz low-power oscillator."""
from review_pdf import *


def make14():
    case=ROOT/'cases/14-oscillator';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text())
    d=data(ROOT/r['run_dir'],'tran.tran');t=d['time'];v=r['values'];o=r['observations'];out=ROOT/'reports/14-oscillator-review.pdf'
    histories=[]
    for run in sorted((ROOT/'runs/14').glob('*_ramp')):
        if (run/'measurements.json').exists():
            a=json.loads((run/'measurements.json').read_text());b=json.loads((run/'inputs/sizing.json').read_text());histories.append((run,a,b))
    with PdfPages(out,metadata={'Title':'14 SMIC18 低功耗2MHz振荡器审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('14 | 低功耗 2 MHz 振荡器审查',1,'结论：原nominal频率、输出摆幅、完整总功耗全部通过，未使用放宽。')
        para(fig,.850,'条件：SMIC18MMRF tt / mim_tt、1.8 V、27°C；VDD从0 V线性升至1.8 V，斜坡1 us；外部2 uA从测量后的AVDD流入IBN2U；CLKO负载1 pF。',9.5)
        rows=[['频率/MHz',f"{v['frequency_Hz']/1e6:.8f}",'1.8–2.2','1.78–2.22','1.77–2.23'],
          ['摆幅/VDD',f"{v['swing_ratio']:.9f}",'0.95–1.05','0.945–1.055','0.9425–1.0575'],
          ['总功耗/uW',f"{v['power_W']*1e6:.7f}",'≤20','≤22','≤23']]
        table(fig,[.07,.633,.86,.123],['指标','实测','原门槛','10%边界','15%边界'],rows,[.22,.23,.17,.19,.19],8.8)
        para(fig,.584,'频率中心固定2 MHz，放宽只把±0.2 MHz窗口扩至±0.22/0.23 MHz；摆幅中心固定1×VDD，允许偏差由±0.05扩至±0.055/0.0575。起振、有限数据及完整测量窗口不放宽。',9.4)
        rows=[['瞬态总长','20 us，普通DC初始化，无强制IC或额外kick'],['测量区间','10–20 us，端点插值并按实际时间积分'],['频率定义','半供电0.9 V，第2上升沿至第12上升沿共10周期'],['摆幅定义','10–20 us中max(CLKO)−min(CLKO)'],['功耗定义','1.8 V×abs(mean I(VSENSE))，包含2 uA和负载驱动']]
        table(fig,[.07,.315,.86,.179],['冻结的nominal维度','实施方式'],rows,[.22,.78],8.6)
        para(fig,.272,f"19个上升沿落在稳态窗口，合同10周期终点为{o['frequency_edges_s'][-1]*1e6:.6f} us，早于20 us；信号覆盖完整高低电平。三项原门槛对应频率上下界、摆幅上下界和总功耗，共五个数值不等式。",9.3)
        para(fig,.158,'原任务披露5个代表PVT点。本次只复现TT/1.8 V/27°C；其余4点、其他斜坡与负载、相噪、抖动、统计失配及PEX均未执行，不据此声称跨PVT频率精度。',9.3)
        para(fig,.079,'DUT只含工艺MOS、原厂HD反相器和原厂MIM电容。理想电源、外部2 uA和1 pF仅出现在bench层，全部落在可追溯的输入快照内。',9.2)
        save(pdf,fig)

        fig=page('限流环、原厂 HD 与 gm/ID 尺寸',2,'外部2 uA以4:1参考比例产生约0.5 uA转接电流，各限流支路再取2倍单位。')
        ax=fig.add_axes([.07,.649,.86,.214]);ax.set(xlim=(0,11),ylim=(-.7,5));ax.axis('off')
        ax.add_patch(Rectangle((.1,3.45),5.3,1.05,fill=False,edgecolor=BLUE));ax.text(2.75,3.97,'IBN2U → MNREF(m=4)\nMNBP(m=1) → MPREF(m=1)',ha='center',va='center',fontsize=9)
        ax.text(5.8,3.95,'IBN2U / VBP控制三对限流管',fontsize=8.3,color=GREEN)
        for i in range(3):
            x=.45+3.3*i;cx=x+1
            ax.add_patch(Rectangle((x,1.0),2,.8,fill=False,edgecolor=BLUE));ax.text(cx,1.4,f'INHDVL → N{i+1}',ha='center',va='center',fontsize=8.8)
            ax.text(cx,2.25,'p18 m=2 → Pi',ha='center',fontsize=8,color=GREEN);ax.plot([cx,cx],[1.8,2.07],color=GREEN)
            ax.text(cx,.34,'Qi → n18 m=2',ha='center',fontsize=8,color=GREEN);ax.plot([cx,cx],[.66,1],color=GREEN)
            if i<2:ax.annotate('',xy=(x+3.3,1.4),xytext=(x+2,1.4),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.plot([9.05,10.1,10.1,.1,.1,.45],[1.4,1.4,2.85,2.85,1.4,1.4],color=BLUE,lw=.9)
        ax.text(5.4,3.02,'三级反相形成环；每级MIM 10×7.75 um²',ha='center',fontsize=8)
        ax.text(.45,-.37,'N3 → INHDVL → INHDV0 → CLKO (1 pF)；输出缓冲接全局AVDD/AVSS。',fontsize=8.2)
        rows=[]
        for model in ['n18','p18']:
            q=s['roles'][model];rows.append([model,f"{q['rounded_W_um']:.2f}/1.00",'15',f"{q['id_w_Apm']:.4f}",f"{q['Vgs_V']:.4f}",f"{q['gmro']:.2f}"])
        table(fig,[.07,.496,.86,.102],['单位模型','W/L (um)','gm/ID','ID/W(uA/um)','|VGS|表点/V','gm·ro'],rows,[.15,.19,.13,.22,.18,.13],8.3)
        para(fig,.460,'LUT点：TT/27°C、L=1 um、|VDS|=0.45 V、VBS=0、参考W=10 um。\n单位电流0.5 uA，精确Wn/Wp=0.271015/1.280503 um，按20 nm网格取0.28/1.28 um。',9.1)
        rows=[]
        for key,q in r['bias_operating_conditions'].items():rows.append([key,f"{abs(q['ids'])*1e6:.6f}",f"{q['gmid']:.4f}",f"{q['minimum_saturation_headroom_V']:.5f}"])
        table(fig,[.07,.270,.86,.126],['实际偏置管','|平均ID|/uA','实际gm/ID','最小|VDS|−|VDSAT|/V'],rows,[.22,.23,.21,.34],8.6)
        para(fig,.230,'实际值来自10–20 us时间加权平均；三只偏置管饱和余量均为正。窄器件和实际VDS使VGS偏离参考W=10 um的表值，因此LUT给初值，实际工作点作最终核查。',9.1)
        para(fig,.136,'INHDVL内部Wn/Wp=0.28/0.42 um，INHDV0=0.60/0.90 um，L均0.18 um。环内VDD/VSS接Pi/Qi，VNW/VPW接全局AVDD/AVSS；原厂内部模型与尺寸均未修改。',9.1)
        para(fig,.074,'三只MIM每只标称约75.2525 fF，总几何面积232.5 um²，未计布局边界。CT1接N1–AVDD；CT2/3接N2/3–AVSS，为电源斜坡提供实体非对称耦合。',8.9)
        save(pdf,fig)

        fig=page('电源斜坡起振与十周期测频',3,'固定原任务启动激励，全部门槛仍仅使用10–20 us保存区间。')
        ax=fig.add_axes([.11,.661,.83,.191]);ix=t<=3e-6
        ax.plot(t[ix]*1e6,d['CLKO'][ix],color=BLUE,lw=1,label='CLKO');ax.plot(t[ix]*1e6,d['AVDD'][ix],color=GREEN,ls='--',label='AVDD ramp')
        ax.axvline(1,color=GRAY,ls=':',lw=.8);ax.set(xlabel='Time (us)',ylabel='Voltage (V)',xlim=(0,3));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='lower right')
        ax=fig.add_axes([.11,.388,.83,.181]);ix=(t>=10e-6)&(t<=20e-6)
        ax.plot(t[ix]*1e6,d['CLKO'][ix],color=BLUE,lw=.85);e0,e1=np.array(o['frequency_edges_s'])[[0,-1]]*1e6
        ax.axvspan(e0,e1,color=GREEN,alpha=.12);ax.axhline(.9,color=GRAY,ls='--',lw=.7)
        for et in [e0,e1]:ax.axvline(et,color=GREEN,ls=':',lw=1)
        ax.set(xlabel='Time (us)',ylabel='CLKO (V)',xlim=(10,20));ax.grid(alpha=.2)
        para(fig,.328,f"首次向上越过固定0.9 V为{o['first_half_supply_crossing_s']*1e6:.6f} us，发生于供电斜坡内部。这只是启动诊断，不作为额外起振时限。全程没有强制初值、噪声种子或隐藏脉冲源。",9.3)
        para(fig,.230,f"合同选择第2/12个上升沿：t2={e0:.9f} us，t12={e1:.9f} us，十周期={o['period_10_s']*1e6:.9f} us，f=10/(t12−t2)={v['frequency_Hz']/1e6:.9f} MHz。全部11个选中边沿均在规定区间。",9.2)
        para(fig,.128,f"窗口内所有18个完整周期平均得到{o['all_period_average_Hz']/1e6:.9f} MHz，与合同值相对差{o['all_periods_relative_frequency_difference']*100:.7g}%。这项交叉核验确认测频一致，确定性周期差不解释为物理抖动。",9.2)
        save(pdf,fig)

        fig=page('真实环内波形与完整功耗',4,'1 pF负载、两级输出缓冲及外部2 uA都由VSENSE上游统一供电。')
        ax=fig.add_axes([.11,.665,.83,.190]);ix=(t>=11e-6)&(t<=12.3e-6)
        for key,style in [('XDUT.N1','-'),('XDUT.N2','--'),('XDUT.N3',':'),('CLKO','-.')]:ax.plot((t[ix]-11e-6)*1e6,d[key][ix],label=key.replace('XDUT.',''),ls=style,lw=1)
        ax.set(xlabel='Time after 11us (us)',ylabel='Voltage (V)',xlim=(0,1.3));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper right',ncol=4)
        ax=fig.add_axes([.11,.402,.83,.177]);ix=(t>=11e-6)&(t<=12.3e-6)
        ax.plot((t[ix]-11e-6)*1e6,d['VSENSE:p'][ix]*1e6,color=BLUE,lw=.95);ax.axhline(o['current_avg_A']*1e6,color=GREEN,ls='--',label='mean, 10–20us')
        ax.set(xlabel='Time after 11us (us)',ylabel='Supply current (uA)',xlim=(0,1.3));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper right')
        rows=[['实测平均供电电流',f"{o['current_avg_A']*1e6:.8f} uA",'VSENSE:p时间积分/10 us'],['实测总供电功耗',f"{v['power_W']*1e6:.8f} uW",'包含偏置、核心与完整输出驱动'],['其中外部2 uA偏置','3.60000000 uW','2 uA从测量后的AVDD引出'],['理想CL动态功耗估算',f"{o['theoretical_load_dynamic_power_W']*1e6:.8f} uW",'CL·VDD²·f，仅用于预算说明']]
        table(fig,[.07,.185,.86,.149],['功耗口径','数值','说明'],rows,[.32,.25,.43],8.5)
        para(fig,.145,'功耗门槛采用固定10–20 us区间，不能删去外部参考或改用环核心电流。负载估算不是额外实测分量，也不再加到已包含它的总功耗中。',9.1)
        para(fig,.085,'第1级虚拟上轨0.8543–1.8002 V，下轨−0.00007–1.0444 V。限流管随充放电靠近轨端而退出饱和属于机制；HD阱仍接全局轨，微小瞬态越轨来自寄生耦合。',8.9)
        save(pdf,fig)

        fig=page('迭代、精度核验与保留的失败证据',5,'所有三轮均保留实际输入、日志、PSF和测量结果；第三轮达到原门槛。')
        rows=[]
        for i,(_,a,b) in enumerate(histories,1):
            q=a['values'];rows.append([i,f"{b['cap']['area_um2']:.2f}",f"{b['reference_unit_current_A']*1e6:.2f}",f"{q['frequency_Hz']/1e6:.7f}",f"{q['power_W']*1e6:.6f}",{'partial':'频率失败','complete_10pct':'10%功耗放宽','complete_original':'原门槛全过'}[a['status']]])
        table(fig,[.07,.680,.86,.158],['轮次','每只MIM/um²','转接目标/uA','频率/MHz','总功耗/uW','结论'],rows,[.08,.18,.18,.18,.18,.20],8.3)
        para(fig,.633,'第1轮90 um²电容带来1.697 MHz，频率不足。第2轮缩至81.5 um²后频率进入窗口，但功耗20.0727 uW高于原20 uW上限。不能只据频率通过判定本题完成。',9.3)
        para(fig,.525,'第3轮采用0.5 uA LUT单位，MNREF用4个单位接收2 uA，转接镜只用1个单位，每级限流取2个单位；降低转接支路开销并把MIM缩至77.5 um²。最终频率1.97357 MHz，功耗19.0392 uW。',9.3)
        para(fig,.408,'一阶估计f≈I/(3·C·VDD)=2.46085 MHz只用于初值；实际HD内部电容、非理想镜像、波形阈值和缓冲负载增加周期。没有把一阶估计代替晶体管仿真。',9.3)
        rows=[['Spectre容差','reltol=2e-5，vabstol=1e-8 V，iabstol=1e-14 A'],['瞬态步长','maxstep=300 ps，errpreset=conservative；约1690步/周期'],['PSF检查','实际保存波形；采样点有限，时间严格递增，覆盖20 us'],['测量复核','端点插值、真实时间积分；全18周期平均与10周期一致'],['求解/模型检查','最终运行无警告；无CMI-2441模型尺寸越界']]
        table(fig,[.07,.164,.86,.172],['验证项目','证据'],rows,[.24,.76],8.6)
        para(fig,.121,'历史Sky130报告仅提供跨5个PVT点的频率极值和nominal功耗18.9772 uW，不能把极值当作本轮nominal频率。此次19.0392 uW来自SMIC18实际测量。',9.1)
        para(fig,.069,'尚未验证非nominal PVT、器件匹配、版图寄生、频率噪声或外部2 uA的真实发生器；片上使用仍需单独设计和计入该偏置源。',8.9)
        save(pdf,fig)

        fig=page('完整电路、可复现输入与证据边界',6,'接口固定为osc_2m AVDD AVSS CLKO IBN2U；所有HD定义include位于bench层。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.858,body,fontsize=8.15,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.32)
        para(fig,.416,'DUT：9只模拟MOS实例、5个原厂HD反相器、3只原厂MIM。n18/p18所有单元W≤1.28 um，远小于100 um模型上限；整数m保留同一LUT单位。',9.1)
        para(fig,.334,'运行：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python\n scripts/case14_oscillator.py\nPDF：同一Python执行 scripts/review_pdf.py 14',8.9)
        para(fig,.245,'最终运行：'+r['run_dir']+'\n目录内inputs/bench.scs与各DUT/HD/合同快照、run.json、output/bench.raw以及measurements.json共同构成证据链。前两轮也保留于runs/14。',8.7)
        para(fig,.143,'原instruction、正式verifier、bench、reference电路和结果冻结于cases/14-oscillator/source/。LUT、PDK、HD来源及哈希随文件保留；未修改既有工艺、Bridge或LUT环境。',9.0)
        para(fig,.064,'电路SHA256：'+sha(case/'circuit.scs'),7.2)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(14,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out


if __name__=='__main__':print(make14())
