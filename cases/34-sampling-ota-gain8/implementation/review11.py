"""Case11 report using the existing review-page and transistor-sheet scheme."""
from review_pdf import *
import subprocess
from module_overviews import overview

def frame(title,num,subtitle):
    fig=page(title,num,subtitle)
    for text in fig.texts:
        if 'Spectre 18.1' in text.get_text():
            text.set_text('SMIC18MMRF TT reproduction | Spectre 24.1 | schematic-level')
    return fig

# Droid's CJK face has no U+2212. Preserve subtraction explicitly in PDF text.
_original_para=para
def para(fig,y,text,*args,**kwargs):
    return _original_para(fig,y,text.replace('\u2212','-'),*args,**kwargs)

_original_table=table
def table(fig,box,headers,rows,*args,**kwargs):
    clean=lambda x:x.replace('\u2212','-') if isinstance(x,str) else x
    return _original_table(fig,box,[clean(x) for x in headers],[[clean(x) for x in row] for row in rows],*args,**kwargs)

def make():
    case=ROOT/'cases/11-bandgap';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values']
    runs={k:ROOT/x for k,x in r['groups'].items()};ln=data(runs['static'],'line.dc');temp=data(runs['static'],'temperature.dc');a=data(runs['acnoise'],'ac.ac');n=data(runs['acnoise'],'noise.noise',required=['out']);st=data(runs['step'],'tran.tran')
    body=ROOT/'reports/11-bandgap-body.pdf';out=ROOT/'reports/11-bandgap-review.pdf'
    info=[('基准偏离1.22V','reference_error_V',1e3,'mV'),('表征点最大功耗','power_W',1e6,'uW'),('六温度点温漂','tempco_ppm_C',1,'ppm/°C'),('线性调整率','line_regulation_V_V',1e3,'mV/V'),('启动窗口偏离1.22V','startup_window_error_V',1e3,'mV'),('斜坡后进入电压窗','startup_entry_s',1e6,'us'),('启动过冲','startup_overshoot_V',1e3,'mV'),('启动峰值电流','startup_peak_A',1e3,'mA'),('正向启动能量','startup_energy_J',1e9,'nJ'),('最大电源耦合','supply_gain',1,'V/V'),('输出积分噪声','noise_Vrms',1e6,'uVrms'),('供电阶跃偏移','line_step_excursion_V',1e3,'mV'),('阶跃1mV建立时间','line_step_settling_s',1e6,'us'),('阶跃末端误差','line_step_final_error_V',1e3,'mV')]
    with PdfPages(body,metadata={'Title':'11 SMIC18 一阶带隙基准审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=frame('11 | 一阶带隙基准审查',1,'结论：适用的TT复现检查全部达到原门槛，无需10%或15%放宽。')
        para(fig,.853,f"标称：1.8 V / 27°C / 外部5 pF，VREF={v['vref_V']:.6f} V，VDD功耗{v['nominal_power_W']*1e6:.3f} uW。TT下保留六温度点及三个电压点表征，动态测试保持27°C；不将其扩称全PVT。",9.4)
        rows=[]
        for label,key,scale,unit in info:
            g=r['gates'][key];rows.append([label,f"{g['value']*scale:.4g}",*[f"≤{g['limits'][t]*scale:.4g}" for t in ['original','10pct','15pct']],unit])
        table(fig,[.07,.27,.86,.48],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.31,.14,.14,.14,.14,.13],7.9)
        para(fig,.218,'电压精度以1.22V为中心，原误差±40mV；10%/15%只扩大误差到±44/46mV。启动时间从斜坡结束计起；阶跃基准取独立DC结果，固定1mV误差带不放宽。',9.0)
        para(fig,.12,'本次为无修调、高阻带隙核心，不包含输出缓冲器。实际运行、网表快照、模型与LUT哈希、测量公式和完整晶体管图均随报告保留。',9.0)
        save(pdf,fig)

        fig=frame('结构与 gm/ID 初始尺寸',2,'一阶 VBE + K·ΔVBE；三路PMOS镜、NPN面积比、误差放大器及独立启动。')
        para(fig,.849,'误差放大器使va≈vb，RPTAT上的电压近似ΔVBE。Q0:Q1发射区面积比1:8，PMOS支路电流比1:1:2；输出为 VBE(QREF) + IOUT·RREF。QREF面积取2，使其电流密度接近Q0。电阻比确定补偿权重，绝对电阻决定电流。',9.4)
        rows=[]
        for key,label,mult in [('mirror','MP0 / MP1 / MP2','1 / 1 / 2'),('input','MINA / MINB','1 / 1'),('load','MPD / MPM','1 / 1'),('bias','MNB / MTAIL','1 / 3'),('startup_p','MPST','1'),('startup_n','MNST / MSTART','1 / 1')]:
            z=s['roles'][key];rows.append([label,z['model'],f"{z['rounded_W_um']:.2f}/1",mult,f"{z['gmid']:g}",f"{z['Id_A']*1e6:g}"])
        table(fig,[.07,.505,.86,.217],['器件','模型','W/L um','m','gm/ID','初算I/uA'],rows,[.27,.12,.15,.16,.15,.15],8.2)
        table(fig,[.07,.287,.86,.158],['器件','工艺模型','最终几何参数'],[
            ['Q0 / Q1 / QREF','npn18a4','单位2×2um；area = 1 / 8 / 2'],
            ['RPTAT / RREF','rpposab_3t','W=1um；L=16.5 / 73.3um'],
            ['RB0–RB7','rpposab_3t','每段W=1um / L=162.5um，8段串联'],
            ['CREF / CCOMP','mim','100×617.92 / 50×10.299um²'],
        ],[.28,.22,.50],8.0)
        para(fig,.234,'LUT：现有gmoverid_smic18 TT表，MOS L=1um；镜与偏置VDS=0.9V，输入对和镜负载VDS=0.45V。初算gm/ID与工作点分别记录，输入对体效应不通过改写LUT掩盖。独立技能文件未迁移，沿用已有GmIdTable接口及已验证数据。',9.0)
        para(fig,.119,'滤波代价：CREF名义60pF，电容板面积约0.0618mm²，另有0.5pF补偿电容及5pF外部负载。模型包含工艺电阻衬底电容与MIM电压/温度系数；未进行布局、DRC或PEX。',9.0)
        save(pdf,fig)

        fig=frame('标称工作点与启动关断',3,'用真实电路OP检查电流、体效应和余量；不把所有器件强制归为同一区域编号。')
        rows=[]
        for dev in ['MP0','MP1','MP2','MINA','MINB','MPD','MPM','MNB','MTAIL','MPST','MNST','MSTART']:
            z=r['operating_point'][dev];rows.append([dev,f"{abs(z['ids'])*1e6:.6g}",f"{z['gmid']:.3f}",f"{z['vgs']:.4f}",f"{z['vds']:.4f}",f"{z['headroom_V']:.4f}"])
        table(fig,[.07,.42,.86,.424],['器件','|ID|/uA','gm/ID','VGS/V','VDS/V','|VDS|−|VDSAT|'],rows,[.17,.17,.15,.15,.15,.21],8.2)
        nodes=r['dc_nodes'];rows=[[k,f'{nodes["X."+k]:.6f}'] for k in ['va','vb','n1','vctat','pctrl','tail','nbias','st']]
        table(fig,[.07,.139,.42,.17],['节点','电压/V'],rows,[.45,.55],8.3)
        para(fig,.381,'输入对实际gm/ID约22/V，源节点约0.266V引入体效应；仍有足够VDS余量。启动检测反相器属于大信号电路，MNST在稳态低VDS，MSTART则关断，不能用放大管饱和条件误判。',9.0)
        fig.text(.55,.297,f"ΔVBE ≈ {(nodes['X.va']-nodes['X.n1'])*1e3:.3f} mV\nva-vb = {(nodes['X.va']-nodes['X.vb'])*1e6:.3f} uV\nMSTART电流 = {abs(r['operating_point']['MSTART']['ids'])*1e12:.3f} pA\n\n表中符号沿用Spectre；\nPMOS电流为负，幅度列取绝对值。",fontsize=9,va='top',linespacing=1.6)
        para(fig,.096,'启动注入关闭不代表启动检测器零功耗：MPST/MNST反相器的剩余直通电流已计入VDD总功耗。这里没有理想电流源给DUT供偏置。',9.0)
        save(pdf,fig)

        fig=frame('温度补偿与线性调整率',4,'TT / bjt_tt / res_tt / mim_tt；温扫在1.8V，电压扫在27°C，二者不是完整笛卡尔PVT。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.29,top=.84,hspace=.46,wspace=.42)
        axs[0,0].plot(temp['temp'],temp['vref'],'.-',color=BLUE);axs[0,0].set(xlabel='Temperature (C)',ylabel='VREF (V)')
        axs[0,1].plot(ln['vddval'],ln['vref'],'.-',color=BLUE);axs[0,1].set(xlabel='Supply (V)',ylabel='VREF (V)')
        axs[1,0].plot(temp['temp'],-1.8*temp['VDD:p']*1e6,'.-',color=BLUE);axs[1,0].axhline(150,color=GRAY,ls='--');axs[1,0].set(xlabel='Temperature (C)',ylabel='VDD power (uW)')
        axs[1,1].plot(ln['vddval'],-ln['vddval']*ln['VDD:p']*1e6,'.-',color=BLUE);axs[1,1].axhline(150,color=GRAY,ls='--');axs[1,1].set(xlabel='Supply (V)',ylabel='VDD power (uW)')
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        rows=[[f'{z["temperature_C"]:g}',f'{z["vref_V"]:.6f}',f'{z["power_W"]*1e6:.3f}'] for z in v['temperature_rows']]
        table(fig,[.07,.104,.86,.135],['温度/°C','输出/V','功耗/uW'],rows,[.25,.4,.35],8.0)
        para(fig,.074,f"TC=(max−min)/(mean×165)={v['tempco_ppm_C']:.6f}ppm/°C；线性调整率=(max−min)/0.36={v['line_regulation_V_V']*1e3:.6f}mV/V。保留全部原定义采样点。",8.4)
        save(pdf,fig)

        fig=frame('从零状态启动：1us 与10us供电斜坡',5,'所有保存内部节点初始为0，skipdc=yes；无强制初始输出、无辅助时钟、无启动行为源。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.29,top=.84,hspace=.42,wspace=.4)
        for j,label in enumerate(['startup1','startup10']):
            d=data(runs[label],'tran.tran');t=d['time']*1e6
            axs[0,j].plot(t,d['vdd'],color=GRAY,label='VDD');axs[0,j].plot(t,d['vref'],color=BLUE,label='VREF');axs[0,j].axhspan(1.18,1.26,color=GREEN,alpha=.12);axs[0,j].set(xlabel='Time (us)',ylabel='Voltage (V)',title=label);axs[0,j].legend(fontsize=8)
            axs[1,j].plot(t,np.maximum(0,-d['VDD:p'])*1e6,color=BLUE);axs[1,j].set(xlabel='Time (us)',ylabel='Positive VDD current (uA)')
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        rows=[]
        for z in v['startup']:rows.append([f"{z['ramp_s']*1e6:g}",f"{z['entry_after_ramp_s']*1e6:.3f}",f"{z['window_min_V']:.6f}–{z['window_max_V']:.6f}",f"{z['overshoot_V']*1e3:.3f}",f"{z['peak_current_A']*1e3:.4f}",f"{z['energy_J']*1e9:.4f}"])
        table(fig,[.07,.163,.86,.093],['斜坡/us','进入/us','后10–20us窗口/V','过冲/mV','峰值/mA','能量/nJ'],rows,[.12,.12,.31,.14,.15,.16],7.8)
        para(fig,.128,'过冲基准取斜坡结束20us时的输出；正向能量积分VDD·max(0,−I(VDD))，覆盖整个启动过程。最终版本无正过冲；这表示所保存2ns时间网格的测量结果。',8.9)
        para(fig,.085,'1us斜坡最难：原3pF补偿/20pF输出电容曾过冲423mV。调整为0.5pF/60pF后保持相同斜坡、节点初始条件和观察窗，全部原门槛通过。',8.7)
        save(pdf,fig)

        fig=frame('供电耦合、输出噪声与双向供电阶跃',6,'AC 10Hz–100MHz；噪声10Hz–1MHz；1.8→1.98→1.62V，10ns边沿。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.29,top=.84,hspace=.43,wspace=.42)
        axs[0,0].loglog(a['freq'],abs(a['vref']),color=BLUE);axs[0,0].axhline(.2,color=GRAY,ls='--');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='|VREF / VDD| (V/V)')
        from matplotlib.ticker import FuncFormatter
        axs[0,0].yaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:g}'))
        axs[0,1].loglog(n['freq'],abs(n['out'])*1e9,color=BLUE);axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Output noise (nV/sqrt(Hz))')
        axs[1,0].plot(st['time']*1e6,st['vref'],color=BLUE);axs[1,0].set(xlabel='Time (us)',ylabel='VREF (V)')
        for z,t0,t1 in zip(v['line_step'],[5e-6,15e-6],[15e-6,30e-6]):
            mask=(st['time']>=t0)&(st['time']<=t1);axs[1,1].plot((st['time'][mask]-t0)*1e6,(st['vref'][mask]-z['independent_dc_target_V'])*1e3,label=z['direction'])
        axs[1,1].axhspan(-1,1,color=GREEN,alpha=.14);axs[1,1].set(xlabel='Time after step (us)',ylabel='DC-target error (mV)');axs[1,1].legend(fontsize=8)
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=8)
        rows=[[z['direction'],f"{z['independent_dc_target_V']:.6f}",f"{z['excursion_V']*1e3:.4f}",f"{z['conservative_settling_s']*1e6:.4f}",f"{z['final_error_V']*1e6:.3f}"] for z in v['line_step']]
        table(fig,[.07,.169,.86,.087],['方向','独立DC目标/V','峰值偏移/mV','1mV建立/us','末端误差/uV'],rows,[.13,.24,.23,.22,.18],8.0)
        para(fig,.131,f"最大电源传递{v['supply_gain_max']:.6f}V/V，出现在{v['supply_gain_peak_Hz']/1e6:.4f}MHz；输出噪声{v['output_noise_Vrms']*1e6:.3f}uVrms。积分使用输出谱的平方，未误用输入折算噪声。",8.9)
        para(fig,.088,'阶跃建立时间保守取最后一次越界后的首个样点，误差带固定1mV，并检查之后持续保持。两段目标均取静态电压扫的独立结果，没有把未收敛尾值当作目标。',8.7)
        save(pdf,fig)

        fig=frame('验收覆盖、迭代与证据复现',7,'仅第11项；原始资料只读，所有新设计与报告在smic18_benchmark_repro工作工程。')
        rows=[['首版','RREF=70.3um；CCOMP=3pF；CREF=20pF','1.20587V，温漂约51ppm/°C'],['直流修正','RREF=73.3um，电容不变','7.453ppm/°C；启动过冲423mV，AC峰0.438'],['最终版本','CCOMP=0.5pF；CREF=60pF','所有适用原门槛通过，保留失败运行']]
        table(fig,[.07,.679,.86,.159],['阶段','实际调整','诊断结果'],rows,[.13,.42,.45],7.8)
        para(fig,.635,'复核：冻结原instruction、reference网表、正式verifier及全部正式bench；Spectre测量与上游analyze函数按同一原始轨迹交叉核对。原verifier要求全PVT/MC，未把本次TT结果送入它并冒称完整通过。',9.0)
        para(fig,.533,'未覆盖：其余MOS/BJT/无源工艺角；动态热低压和冷高压配对；30个固定随机种子；版图、寄生和负载驱动。TT温扫及电压扫是保留的功能表征，不是工艺角或良率签核。最终运行无Spectre警告，无模型尺寸越界。',9.0)
        para(fig,.425,'现用Spectre24.1，原26项18.1结果未改。Bridge把日志中的license与“0 errors”误组合为license error；保留此元数据，按原日志0错误/0警告、成功许可检查和完整数据确认运行有效。没有修改Bridge或Spectre环境。',8.8)
        para(fig,.328,'复现（先激活virtuoso-bridge-lite/.venv，在工程根目录执行）：\npython scripts/case11_bandgap.py\npython scripts/case11_bandgap.py --extract\npython scripts/schematic11.py\npython scripts/audit11.py\npython scripts/review11.py',8.2)
        para(fig,.177,'最终五组运行：\n'+'\n'.join(r['run_dirs']),7.8)
        para(fig,.082,'验收边界预先冻结；没有改变5pF负载、供电范围、频段、温度采样点或启动窗口来制造通过。文档渲染与图纸连接审查完成后才登记正式交付。',8.2)
        save(pdf,fig)

        fig=frame('精确网表与图纸对应',8,'MOS端序D G S B；BJT端序C B E SUB；所有工艺电阻第三端均接vss。')
        net='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.073,.854,net,fontsize=7.6,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.28)
        para(fig,.203,'后附S1–S3为全部27个器件的连接图：12个MOS、3个NPN定义、10个工艺电阻和2个MIM电容，共94个端子。m及area均明确标出；每个图纸端子都有可追踪的导线到正确网络标签。',9.0)
        para(fig,.106,'完整总图：cases/11-bandgap/schematic/full.svg / full.pdf\n图纸连接与参数审计：schematic/connectivity.json / schematic_audit.json\n结果与来源：latest_results.json / verification_audit.json / source_provenance.json',8.1)
        para(fig,.051,'电路SHA-256：'+sha(case/'circuit.scs'),7.3)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1])
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=3,schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True))
    return out

if __name__=='__main__':print(make())
