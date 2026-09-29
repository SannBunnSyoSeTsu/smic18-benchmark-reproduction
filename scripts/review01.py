"""Self-contained original-window Class-D report and all hierarchy drawings."""
from review_pdf import *
from review11 import frame,para,table
import subprocess

def make():
    case=ROOT/'cases/01-class-d';r=json.loads((case/'latest_results.json').read_text());v=r['values'];z=json.loads((case/'sizing.json').read_text());c=json.loads((case/'numerical_confirmation.json').read_text());a=json.loads((case/'verification_audit.json').read_text())
    waves={key:data(ROOT/r['groups'][key],'tran.tran') for key in ['t27_r1','t27_r3','t27_r16','t125_r16']}
    body=ROOT/'reports/01-class-d-body.pdf';out=ROOT/'reports/01-class-d-review.pdf'
    with PdfPages(body,metadata={'Title':'01 SMIC18 Class-D半桥审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        tier=r['status'].removeprefix('complete_');conclusion='全部原门槛通过' if tier=='original' else tier.replace('pct','%')+'放宽范围内完成，逐项保留原门槛比较'
        fig=frame('01 | Class-D半桥功率级审查',1,'结论：'+conclusion+'。')
        para(fig,.85,'SMIC18MMRF TT / 1.8V；保留原27°C和125°C两个效率分组，每温度7种负载，共14点。时钟5MHz、2ns边沿、50Ω源阻抗；外部3uH与345pF串联LC保持原值。',9.1)
        rows=[]
        for title,key,scale,unit in [('27°C峰值效率','peak_27',100,'%'),('27°C最低效率','all_27',100,'%'),('125°C峰值效率','peak_125',100,'%'),('125°C最低效率','all_125',100,'%'),('所有点最小输出功率','minimum_output_power',1e3,'mW')]:
            g=r['gates'][key];rows.append([title,f"{g['value']*scale:.6f}",*[f">{g['limits'][t]*scale:g}" for t in ['original','10pct','15pct']],unit])
        table(fig,[.07,.47,.86,.24],['验收量','实测','原门槛','10%','15%','单位'],rows,[.30,.19,.15,.14,.14,.08],8)
        para(fig,.397,'效率下限按线性比例放宽，所有比较仍为严格大于。输出功率>30mW是防止无功率输出的功能检查，本项保持原值，未随效率一起放宽；效率≤100%及正有限功率也不放宽。',9.2)
        para(fig,.248,'输入功率覆盖半桥、全部HD逻辑和栅驱动器，以及50Ω之前的时钟源。对原18–20us窗口做时间加权积分，不用非均匀样点的算术平均，也不减掉驱动功耗或LC储能变化。',9.2)
        para(fig,.104,'本报告为固定时钟的原理图级功率验证；未执行其他工艺角、失配、音频调制、失真、版图或PEX，也不构成瞬态过压寿命签核。',9.1)
        save(pdf,fig)

        fig=frame('功率管、gm/ID初值与物理寄生',2,'目标工艺实际W50um、L0.18um表征，驱动点取完整1.8V端点。')
        rows=[]
        for key,name in [('power_p','PMOS上管'),('power_n','NMOS下管')]:
            q=z['roles'][key];rows.append([name,q['model'],f"{q['gmid']:.6f}",f"{q['Id_A']*1e3:.6f}",f"{q['cgg_full_drive_F']*1e15:.3f}"])
        table(fig,[.07,.707,.86,.12],['角色','模型','gm/ID (1/V)','表征ID (mA)','Cgg/fF'],rows,[.23,.15,.22,.23,.17],8.5)
        para(fig,.654,'表征条件TT/27°C、VDS=1.8V、VSB=0V，扫描VGS至1.8V。表征ID用于单位宽度选择，不是半桥的直流偏置；功率管导通时主要处于低VDS区，不能把饱和LUT的gm/ID当作开关损耗模型。最终功率仍由动态Spectre验证。',9.3)
        table(fig,[.07,.365,.86,.15],['参数','上管p18','下管n18'],[
            ['单位W/L','50/0.18um','50/0.18um'],['并联组与每组m','4组×512','2组×512'],['总W',f"{z['power_total_width_um']['p18']:g}um",f"{z['power_total_width_um']['n18']:g}um"],['每单位AD=AS / PD=PS','15um² / 100.6um','15um² / 100.6um']], [.40,.30,.30],8.4)
        para(fig,.317,'每单位扩散延伸取0.3um，并显式填写面积和周长。首轮单个PMOS m=2048使单实例源漏寄生电阻低于Spectre默认minr，被CMI-2318删除；最终拆为四组m=512保留原寄生，未改minr或PDK电阻参数。',9.1)
        para(fig,.179,'n18补充LUT的gm/ID下限最初截掉VGS=1.8V端点；用同一次原始扫描重新提取到gm/ID≥0.5，保留实际端点，没有外推。两份W50um专用表仅写入本工程，既有gmoverid表保持不变。',9.1)
        para(fig,.120,'加宽会减小导通电阻，同时增加栅极、结电容和栅驱动负担。总宽度与大并联倍数不等于已完成合理布局；扩散共享、金属损耗和封装仍待验证。',8.9)
        save(pdf,fig)

        fig=frame('完整14点功率与效率',3,'负载、温度和积分窗保留原题；m0–m13逐项对应原验收器。')
        rows=[]
        for temp in [27,125]:
            for load in [1,2,3,6,8,12,16]:
                q=v[f't{temp}_r{load}'];rows.append([f'{temp}',f'{load}',f"{q['p_out_W']*1e3:.6f}",f"{q['p_vdd_W']*1e3:.6f}",f"{q['p_clk_W']*1e6:.6f}",f"{q['p_in_W']*1e3:.6f}",f"{q['efficiency']*100:.6f}"])
        table(fig,[.07,.348,.86,.48],['温度/°C','RL/Ω','Pout/mW','PVDD/mW','Pclk/uW','Pin/mW','η/%'],rows,[.12,.08,.17,.17,.14,.17,.15],7.5)
        para(fig,.283,'Pin = |1.8×mean(I_VDD)| + |mean(VSS×I_VSS)| + |mean(VCLK×I_VCLK)|。电流方向沿Spectre电压源正端；先积分带符号功率再取绝对值。VSS为理想零伏，仍保留该项。',9.2)
        para(fig,.14,'Pout = |mean(V_RLnode×I_VMEAS_RL)|。零伏电流感测源与RL串联；独立用mean(V_RL²/RL)核对输出实功率。所有源电流按同一个18–20us窗口计算。',9.2)
        save(pdf,fig)

        fig=frame('负载依赖与效率代价',4,'曲线由实测14点组成；不把峰值效率推广至全部负载。')
        axs=fig.subplots(2,1);fig.subplots_adjust(left=.13,right=.94,bottom=.26,top=.84,hspace=.35)
        loads=[1,2,3,6,8,12,16]
        for temp,color in [(27,BLUE),(125,GREEN)]:
            axs[0].plot(loads,[100*v[f't{temp}_r{x}']['efficiency'] for x in loads],'o-',label=f'{temp} C',color=color)
            axs[1].plot(loads,[1e3*v[f't{temp}_r{x}']['p_out_W'] for x in loads],'o-',label=f'{temp} C',color=color)
        axs[0].set(ylabel='Efficiency (%)');axs[1].set(xlabel='Load resistance (ohm)',ylabel='Output power (mW)');axs[1].axhline(30,color=GRAY,ls='--',label='Original power guard')
        for ax in axs:ax.grid(alpha=.2);ax.legend(fontsize=8)
        para(fig,.206,'低阻负载中的较大谐振电流提高导通与换向损耗；高阻负载输出功率下降时，逻辑和栅驱动动态损耗占比增加。原题在两个温度都同时约束峰值与最低效率，单个漂亮峰值不足以通过。',9.3)
        para(fig,.084,'驱动器各级仅并联完整原厂HD单元，没有改动单元内部W/L或体端。非交叠时序、缓冲扇出与总栅电容需要共同权衡。',9.1)
        save(pdf,fig)

        fig=frame('建立、换向与栅极波形',5,'原DC初始解和20us运行；图中节点取真实PSF，不以逻辑理想波形代替。')
        axs=fig.subplots(3,2);fig.subplots_adjust(left=.13,right=.94,bottom=.23,top=.84,hspace=.52,wspace=.40)
        for j,key in enumerate(['t27_r1','t125_r16']):
            d=waves[key];t=d['time'];m=t>=19.6e-6;ns=(t[m]-19.6e-6)*1e9
            axs[0,j].plot(t*1e6,d['VMEAS_RL:p'],color=BLUE,lw=.5);axs[0,j].set(xlabel='Time (us)',ylabel='Tank current (A)',title=key)
            axs[1,j].plot(ns,d['sw'][m],color=BLUE);axs[1,j].set(xlabel='From 19.6 us (ns)',ylabel='SW (V)')
            for node,col in [('X.gp',BLUE),('X.gn',GREEN)]:axs[2,j].plot(ns,d[node][m],label=node,color=col)
            axs[2,j].set(xlabel='From 19.6 us (ns)',ylabel='Power gates (V)');axs[2,j].legend(fontsize=7)
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=7)
        swmin=min(q['SW_min_V'] for q in v.values());swmax=max(q['SW_max_V'] for q in v.values())
        para(fig,.181,f"14点测量窗内SW范围总包络{swmin:.6f}至{swmax:.6f}V。谐振电流在换向时给节点寄生充放电，可产生轨外尖峰；效率指标已计入其能量代价。没有把这些尖峰裁去或用理想钳位消除。",9.0)
        para(fig,.076,'原合同不设专门的死区时间或端压寿命评分；本报告不由效率通过推断无直通电流或可靠性通过。实际版图与寿命评估还需检查全部器件端间应力。',8.9)
        save(pdf,fig)

        fig=frame('固定积分窗与LC储能',6,'保留原18–20us合同，同时记录窗口两端谐振器的能量。')
        rows=[]
        for temp in [27,125]:
            for load in [1,3,16]:
                q=v[f't{temp}_r{load}'];rows.append([f'{temp} / {load}',f"{q['tank_energy_start_J']*1e9:.6f}",f"{q['tank_energy_end_J']*1e9:.6f}",f"{q['tank_energy_rate_W']*1e3:.6f}"])
        table(fig,[.07,.598,.86,.23],['温度°C / RLΩ','E(18us) / nJ','E(20us) / nJ','ΔE/Δt / mW'],rows,[.25,.25,.25,.25],8.2)
        para(fig,.538,'E = 0.5×L×I² + 0.5×C×(V_lc_node−V_rl_node)²。电感、电容和VMEAS_RL严格串联，故采用感测源电流计算电感储能。能量差只是解释固定窗状态的诊断量，没有从Pin中扣除。',9.3)
        para(fig,.383,'5MHz下固定LC的电抗并非精确抵消，低阻负载还具有较高Q。20us时的轨迹不应自动视为所有负载都达到严格周期稳态；本次完整执行原测试窗，另列储能变化，避免把有限窗比值当作任意长时间的稳态效率。',9.3)
        para(fig,.212,'先对电压与电流分别插值到18us和20us，再逐段梯形积分瞬时功率。全部窗口自适应样点保留，未抽稀开关边沿，未改用等间隔粗采样或算术均值。',9.2)
        para(fig,.086,'初版请求L1:p在此Spectre电感上无对应输出，被日志明确拒绝。修正为拓扑上严格相同的串联感测电流，最终台已移除无效save项；首轮错误日志完整归档。',9.0)
        save(pdf,fig)

        assert c['passed'] and c.get('all14_final_use_refined_parameters')
        fig=frame('数值收敛与独立验收',7,'全部14点最终采用0.25ns/1e-7；六个代表点与0.5ns/1e-6比较。')
        rows=[]
        for key,m in c['metrics'].items():rows.append([key,f"{m['efficiency']['absolute_difference']*100:.6g}",f"{m['p_in_W']['absolute_difference']*1e3:.6g}",f"{m['p_out_W']['absolute_difference']*1e3:.6g}"])
        table(fig,[.07,.604,.86,.22],['复核点','Δη / 百分点','ΔPin / mW','ΔPout / mW'],rows,[.25,.25,.25,.25],8.2)
        para(fig,.547,'固定界限：效率差≤0.1个百分点，Pin/Pout差各≤0.2mW，且验收等级不变。首轮1ns/1e-5与0.5ns/1e-6对比失败，最大功率差约0.679mW；未放宽收敛界限，改为全14点0.25ns/1e-7，六点与中间精度再比较。',9.2)
        para(fig,.387,'SPECTRE-16780表示换向附近局部截断误差容差暂时放宽，日志原样保留。两温度各选1/3/16Ω检查换向、近峰值和低功率区。其余八点采用相同最终精度；最终无CMI寄生删除、尺寸越界或无效save警告。',9.2)
        para(fig,.254,f"独立审计对14组原始PSF以逐段标量积分重算7类测量，共{len(a['measurement_cross_checks'])}项核对。将独立值组成原m0–m13，再送入未改动的原验收器main()和sanity_error()；保持严格比较与全点集合。",9.2)
        para(fig,.106,'Bridge元数据中license error来自旧字符串分类器；实际Spectre日志均正常完成且0错误，许可、原始波形及所有模型哈希另行核对。没有据此忽略真实CMI或ERROR信息。',9.0)
        save(pdf,fig)

        fig=frame('精确顶层与HD驱动层次',8,'所有本地子电路在后附六页图纸逐一定义展开。')
        text=(case/'circuit.scs').read_text();top=text[text.index('subckt half_bridge'):]
        fig.text(.07,.848,top,fontsize=6.8,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.65)
        para(fig,.479,'bank4由四个原厂INHDV32并联组成。driver_p：INHDV4→INHDV32→2×bank4→8×bank4，为四级同相链；driver_n：INHDV8→bank4→4×bank4，为三级反相链。NAND交叉反馈和四级MIM负载延迟形成先关后开的逻辑时序。',9.2)
        para(fig,.315,'delay4含四个INHDV1，每级输出接0.1pF工艺MIM，顶层调用两次。所有HD VNW接vdd、VPW接vss；内部晶体管和模型名与原厂CDL一致。DUT无理想R/C/L、内部独立源或行为器件。',9.2)
        para(fig,.174,f"共{a['schematic_instances']}个子电路定义实例、{a['schematic_terminals']}个定义端子逐一核对；并联层次展开后的所有路径也独立检查。相同定义绘制一次，重复调用和每一端口映射均保留。静态图纸审计不是版图LVS。",9.1)
        para(fig,.072,'DUT SHA-256：\n'+r['circuit_sha256'],7.5)
        save(pdf,fig)

        fig=frame('迭代、复现入口与适用边界',9,'报告、图纸、测量和知识库共享同一最终电路哈希。')
        para(fig,.85,'首轮未拆组PMOS在27°C的1/3/16Ω效率为90.208/95.648/82.718%，但出现CMI-2318，未用于验收。拆组后全14点电气通过，第一次六点数值对照仍失败；最终全14点进一步收紧精度。所有失败与中间结果分别保留。',9.2)
        para(fig,.69,'复现（工作工程根目录，既有Bridge Python）：\npython scripts/case01_classd.py\npython scripts/confirm01.py\npython scripts/schematic01.py\npython scripts/audit01.py\npython scripts/review01.py\n每次重新生成报告，都须重新逐页目检并核对总图后才能交付。',8.7)
        para(fig,.432,'证据入口：\nlatest_results.json：14点功率、原/放宽门槛和最终运行路径\nnumerical_confirmation.json：6点收敛对照及基线/最终分组\nverification_audit.json：98项测量、原验收器与模型/HD/LUT哈希\nschematic/connectivity.json：全部器件端子和层次映射\niteration_history.json：未采用版本及其真实错误原因\nimplementation/：本次生成及审查脚本快照',8.7)
        para(fig,.196,'测量包含功率级和驱动功耗，却不包含外部理想LC的损耗、实际PCB或封装损耗。固定5MHz、1.8V、指定14点的结果不能替代音频系统、PWM调制、全PVT或不同谐振网络验证。',9.1)
        para(fig,.08,'原Sky130资料与既有PDK、Bridge、Spectre及LUT环境保持原样。本次更新写入SMIC18复现分区，并保留已交付模块的证据哈希。',9.0)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1])
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=pages,body_pages=9,schematic_pages=6,schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True));print(out)

if __name__=='__main__':make()
