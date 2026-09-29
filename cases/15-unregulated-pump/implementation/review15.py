"""Charge-pump report built from measured PSF and original time windows."""
from review_pdf import *
from review11 import frame,para,table
import subprocess

def make():
    case=ROOT/'cases/15-unregulated-pump';r=json.loads((case/'latest_results.json').read_text());z=json.loads((case/'sizing.json').read_text());v=r['values'];q=z['roles']['transfer']
    e=data(ROOT/r['groups']['enabled'],'tran.tran');d=data(ROOT/r['groups']['disabled'],'tran.tran');c=json.loads((case/'numerical_confirmation.json').read_text())
    body=ROOT/'reports/15-unregulated-pump-body.pdf';out=ROOT/'reports/15-unregulated-pump-review.pdf'
    with PdfPages(body,metadata={'Title':'15 SMIC18 未稳压倍压电荷泵审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        tier=r['status'].removeprefix('complete_');conclusion='四项原nominal门槛全部通过。' if tier=='original' else tier.replace('pct','%')+'放宽范围内完成，原门槛差异见下表。'
        fig=frame('15 | 未稳压倍压电荷泵审查',1,'结论：'+conclusion)
        para(fig,.853,'SMIC18MMRF TT / 1.8V / 40°C；10MHz输入、1ps边沿、时钟及EN各50Ω源阻抗。开启输出带1nF和50uA；关闭台仅带1nF，EN自零时刻拉低，外部时钟仍运行。',9.2)
        rows=[]
        for label,key,scale,unit in [('输出距2.5V误差','output_error',1,'V'),('输出纹波','ripple',1e3,'mVpp'),('开启平均电流','enabled_current',1e6,'uA'),('关闭平均电流','disabled_current',1e9,'nA')]:
            g=r['gates'][key];rows.append([label,f"{g['value']*scale:.6g}",*[f"≤{g['limits'][x]*scale:g}" for x in ['original','10pct','15pct']],unit])
        table(fig,[.07,.52,.86,.21],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.17,.14,.14,.14,.12],8.1)
        para(fig,.45,f"输出平均{v['vout_en_avg']:.9f}V，最小/最大{v['vout_en_min']:.9f}/{v['vout_en_max']:.9f}V。原窗口2.2–2.8V；以中心2.5V扩大误差，10%为2.17–2.83V，15%为2.155–2.845V。",9.2)
        para(fig,.308,'开启仿真到200us，全部指标取190–200us；独立关闭仿真到10us，平均电流取9–10us。电流是供电感测源的时间平均再取绝对值，不是电流绝对值的平均。两种工作状态不共享电源感测支路。',9.2)
        para(fig,.16,'只复现原八个代表点中的TT/40°C。未完成其余七点、完整PVT或失配；本题没有效率指标，也没有验证已充电状态下拉低EN的放电轨迹。',9.2)
        save(pdf,fig)

        fig=frame('器件选择、gm/ID与两相电荷搬运',2,'厚氧低阈值传输管、工艺MIM和未修改的HD数字单元。')
        para(fig,.85,'NAND用EN门控外部时钟，串联两级反相器生成ph0/ph1。两块MIM电容交替抬升p0/p1；另一泵节点驱动预充MOS，把低相节点预充到接近AVDD。两只门极接泵节点的整流MOS把高相电荷送到VOUT。',9.1)
        table(fig,[.07,.562,.86,.19],['角色','器件/几何','选点/用途'],[
            ['两只整流MOS',f"{q['model']} W{q['rounded_W_um']:g}/L{q['L_um']:g}um",f"gm/ID={q['gmid']:g}，初算{q['Id_A']*1e6:g}uA"],
            ['两只预充MOS',f"{z['roles']['precharge']['model']} W{z['roles']['precharge']['rounded_W_um']:g}/L{z['roles']['precharge']['L_um']:g}um",f"gm/ID={z['roles']['precharge']['gmid']:g}，初算{z['roles']['precharge']['Id_A']*1e6:g}uA"],
            ['CF0/CF1',f"mim，100um×{z['parameters']['cap_pf']/.0971:.4f}um",f"各名义{z['parameters']['cap_pf']:g}pF"],
            ['使能逻辑','NAND2HDV1','原厂CDL尺寸与井端'],
            ['两相驱动',z['parameters']['cell']+'×2','原厂CDL尺寸与井端'],
        ],[.19,.47,.34],8.1)
        para(fig,.504,f"新表征在已有Spectre环境内完成，仅写入本工程lut_supplement。选点TT/27°C、VDS1.8V、VSB0V；预测VGS={q['Vgs_V']:.6f}V、fT={q['ft_Hz']*1e-9:.3f}GHz。最终电路按原合同40°C运行，实际泵节点体效应和双向导通不能由这一个LUT工作点代替。",9.0)
        para(fig,.347,'nnt33的零体偏置低阈值使正VGS表的gm/ID最高约6.96。曾请求gm/ID=8，被查表器明确拒绝；最终选择表内gm/ID=6，没有钳位、外推或把n18表冒充厚氧表。',9.2)
        para(fig,.218,f"两块MIM名义总板面积{z['physical_capacitance']['plate_area_um2_total']:.1f}um²，模型包含电压和温度系数。外部1nF电容不计入片上MIM面积；本次未做布局、DRC或寄生提取。",9.0)
        para(fig,.098,'DUT没有理想R/C、内部源或行为器件。NAND与反相器内部8只MOS保持原厂HD尺寸，四只模拟MOS按目标工艺gm/ID重新设计。',9.0)
        save(pdf,fig)

        fig=frame('开启建立过程与独立关闭状态',3,'沿原台采用DC初始解；未把它解释为任意电源斜坡下的冷启动保证。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.26,top=.84,hspace=.43,wspace=.4)
        for ax,wave,label in [(axs[0,0],e,'Enabled'),(axs[0,1],d,'Disabled')]:ax.plot(wave['time']*1e6,wave['VOUT'],color=BLUE);ax.set(xlabel='Time (us)',ylabel='VOUT (V)',title=label)
        axs[0,1].set_ylim(0,2)
        t=e['time'];m=t>=180e-6;axs[1,0].plot(t[m]*1e6,e['VOUT'][m],color=BLUE,lw=.5);axs[1,0].set(xlabel='Time (us)',ylabel='VOUT (V)',xlim=(180,200))
        td=d['time'];md=td>=9e-6;axs[1,1].plot(td[md]*1e6,d['VSENSE:p'][md]*1e3,color=BLUE);axs[1,1].set(xlabel='Time (us)',ylabel='Disabled VDD current (mA)',xlim=(9,10))
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.201,f"最终单周期均值{v['output_last_cycle_mean_V']:.9f}V，190–200us均值{v['vout_en_avg']:.9f}V。固定50uA负载一直存在；最后窗口计算真实上下峰值，没有用尾段平均减去漂移来缩小纹波。",9.1)
        para(fig,.097,'关闭台自开始EN=0，输出约1.8V，仍有正负供电电流尖峰；原指标取9–10us带符号电流的时间平均，不要求输出归零，也不测试已开启状态关闭后的泄放。',9.0)
        save(pdf,fig)

        fig=frame('最后四周期的泵送与输出纹波',4,'10MHz原始时钟继续运行；曲线均来自最终实际瞬态数据。')
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.13,right=.94,bottom=.23,top=.84,hspace=.5)
        ns=(e['time']-199.6e-6)*1e9;m=e['time']>=199.6e-6
        for name,col in [('X.ph0',BLUE),('X.ph1',GRAY)]:axs[0].plot(ns[m],e[name][m],label=name,color=col)
        for name,col in [('X.p0',BLUE),('X.p1',GRAY)]:axs[1].plot(ns[m],e[name][m],label=name,color=col)
        axs[2].plot(ns[m],(e['VOUT'][m]-v['vout_en_avg'])*1e3,color=BLUE)
        for ax,label in zip(axs,['Bottom plates (V)','Pump nodes (V)','VOUT - mean (mV)']):ax.set(xlim=(0,400),ylabel=label);ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        axs[0].legend(fontsize=7,ncol=2);axs[1].legend(fontsize=7,ncol=2);axs[2].set_xlabel('Time from 199.6 us (ns)')
        para(fig,.164,'电荷转移由MOS实际阈值、体效应、导通电阻、底板时序和MIM容值共同决定。两级HD反相器并非理想互补源，交叠与有限边沿会增加回流和动态损耗；不能由2×VDD直接预测带载输出。',9.1)
        para(fig,.077,'输出纹波包含开关耦合尖峰。最终190–200us保留全部自适应样点，不用稀疏等间隔输出遗漏尖峰。',9.0)
        save(pdf,fig)

        fig=frame('供电积分、数值复核与端电压',5,'原台时间窗不变；收敛对照采用同一电路和完整200us运行。')
        rows=[]
        for key,qc in c['metrics'].items():rows.append([key,f"{qc['baseline']:.8g}",f"{qc['refined']:.8g}",f"{qc['absolute_difference']:.4g}"])
        table(fig,[.07,.646,.86,.19],['指标（SI单位）','1ns / 1e-5','0.5ns / 1e-6','绝对差'],rows,[.34,.23,.23,.20],7.8)
        para(fig,.593,'初版1ps时钟边沿附近出现SPECTRE-16780：局部截断误差容差暂时放宽。相关日志完整保留；通过减小最大步长、收紧相对容差的独立运行比较最终输出、纹波及两种平均电流，不凭“0错误”自动忽略警告。',9.1)
        rows=[]
        for dev in r['terminal_voltages']['enabled']:rows.append([dev['name'],*[f"{dev['peaks_V'][k]:.4f}" for k in ['VGS','VGD','VDS','VGB','VDB','VSB']]])
        table(fig,[.07,.322,.86,.19],['器件','|VGS|','|VGD|','|VDS|','|VGB|','|VDB|','|VSB|'],rows,[.22,.13,.13,.13,.13,.13,.13],7.9)
        para(fig,.278,'上表按网表端名计算；MRECT的有效源漏在整流导通时交换，VGS=0不代表未导通。厚氧器件使用固定3.63V工程筛查线，性能放宽不改变它；这只是1.1×标称电压的工程筛查，不是工厂寿命、结击穿或可靠性签核。核心HD数字管保持原厂1.8V供电。',9.0)
        para(fig,.147,'0–2us及180–200us保存全部自适应样点；2–180us仅输出每100点之一以限制文件大小，求解器仍完整计算所有步。开启测量窗完全未抽点，关闭轨迹也未抽点；中段稀疏轨迹不用于宣称每次瞬态端压的严格上界。',9.0)
        save(pdf,fig)

        fig=frame('迁移失败与最终取舍',6,'目标工艺的阈值、体效应和电荷回流需要重新验证。')
        hist=json.loads((case/'iteration_history.json').read_text());rows=[]
        for k,h in enumerate(hist,1):
            par=json.loads((ROOT/h['run_dirs'][0]/'inputs/sizing.json').read_text())['parameters'];a=h['values'];label=f"{par.get('pre_model',par['model'])}→{par['model']} /{par['cap_pf']:g}pF"+(' +CL' if par.get('clamp_uA',0) else f" /gm{par['gm_id']:g}")+(f" PRE{par['pre_current_uA']:g}u" if 'pre_current_uA' in par else '');label=('* '+label) if par.get('pre_model')=='n33' and par['model']=='nnt33' else label;rows.append([label,f"{a['vout_en_avg']:.5f}",f"{a['ripple_V']*1e3:.4f}",f"{a['enabled_current_A']*1e6:.3f}"])
        rows.append(['最终电路',f"{v['vout_en_avg']:.5f}",f"{v['ripple_V']*1e3:.4f}",f"{v['enabled_current_A']*1e6:.3f}"])
        table(fig,[.07,.51,.86,.32],['预充→整流 / 电容 / 钳位','VOUT/V','纹波/mV','开启/uA'],rows,[.44,.18,.19,.19],8.1)
        para(fig,.472,'带*的混合管版本触发体结模型线性化，仅作故障诊断。常规n33从17.04um加宽到70.92um，输出只由2.06235升至2.08827V，仍低于15%边界。宽度增大减少部分导通压降，同时增加被泵节点和时钟驱动的寄生；不能靠无限加宽消除体效应阈值损失。',9.2)
        para(fig,.345,'低阈值nnt33在gm/ID=6、16.84/1um下将10pF版输出提高到2.61424V，但开启电流290.002uA、纹波5.320mV，仍未合格。低阈值并不自动等于更低总电流；切换期间回流和耦合必须一起测量。',9.2)
        para(fig,.172,'混合n33预充/nnt33整流版及钳位版出现启动体结CMI-2139/2144警告，且有端压越界或200us尚未稳定，未用于交付。最终返回全nnt33，用较窄预充管降低回流，并调整飞跨电容。未稳压泵在指定负载上的输出是电荷平衡结果；本项没有将负载减小、外部电容增大或时钟降频来制造通过。',9.2)
        save(pdf,fig)

        fig=frame('精确DUT网表与HD来源',7,'顶层端口顺序AVDD AVSS CLK EN VOUT；供电与井端全部明确。')
        net='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.073,.853,net,fontsize=8.1,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.45)
        para(fig,.5,'三个HD实例共8只原厂MOS；四只模拟MOS和两块工艺MIM共同构成9个顶层实例、39个端子。后附完整图纸绘出全部模拟器件、HD信号/供电/井端。HD内部CDL完整副本和源块哈希随证据归档。',9.1)
        para(fig,.345,'NAND2HDV1的端口为A1 A2 ZN VDD VSS VNW VPW；INHDV16为I ZN VDD VSS VNW VPW。VNW接AVDD、VPW接AVSS。未改写原厂晶体管宽长、并联倍数或模型名。',9.1)
        para(fig,.215,'完整总图：cases/15-unregulated-pump/schematic/full.pdf\n独立连接核对：schematic_independent_review.json\n原厂单元与哈希：hd_cells.scs / hd_cells_manifest.json',8.7)
        para(fig,.096,'DUT SHA-256：\n'+r['circuit_sha256'],8.0)
        save(pdf,fig)

        fig=frame('原始验收复核与可重复证据',8,'原题四项nominal判据与五个原始测量量独立重算。')
        para(fig,.85,'独立逐段梯形积分、边界插值和极值检查，重算VOUT平均/最大/最小及两种感测电流。把这些原始测量量传给未修改的上游checks(rows,{TT40C})，保留其绝对平均电流和完整集合检查。未把TT单点冒称八点PVT完成。',9.1)
        para(fig,.698,'模型、LUT、原题、HD源文件和最终两组输入快照均记录SHA-256。数值收敛对照与失败迭代保留各自不可覆盖的原始运行；Bridge若报license error，依据实际许可检查、0错误结束和PSF完整性区别字符串误报。',9.1)
        para(fig,.545,'复现（工程根目录，既有virtuoso-bridge-lite/.venv）：\npython scripts/case15_pump.py\npython scripts/confirm15.py\npython scripts/schematic15.py\npython scripts/audit15.py\npython scripts/review15.py\n重新生成PDF后须逐页目检；交付状态不会自动继承。',8.6)
        para(fig,.329,'最终运行：\n'+'\n'.join(r['run_dirs'])+'\n收敛基线及参数：numerical_confirmation.json',8.2)
        para(fig,.204,'保留范围：原10MHz/1ps/50Ω控制输入、50uA开启负载、1nF外部电容、开启200us及关闭10us、各自原平均窗口。没有对外部夹具或工艺模型进行性能优化。',9.1)
        para(fig,.092,'未覆盖另外七个代表点、完整PVT、失配、效率、已充电后的关断泄放、版图及PEX。PDK与既有Bridge/Spectre/LUT环境未改。',9.0)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1])
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=1,schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True))
    print(out)

if __name__=='__main__':make()
