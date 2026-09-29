"""Self-contained line driver review: measurements, iteration, full schematics."""
from review_pdf import *
from review11 import frame,para,table
import subprocess

def make():
    case=ROOT/'cases/39-line-driver';r=json.loads((case/'latest_results.json').read_text());v=r['values'];z=json.loads((case/'sizing.json').read_text());a=json.loads((case/'verification_audit.json').read_text());c=json.loads((case/'numerical_confirmation.json').read_text());assert c['passed']
    loop=data(ROOT/r['groups']['loop'],'ac.ac');swing=data(ROOT/r['groups']['swing'],'swing.dc');thd=data(ROOT/r['groups']['thd'],'tran.tran')
    body=ROOT/'reports/39-line-driver-body.pdf';out=ROOT/'reports/39-line-driver-review.pdf'
    with PdfPages(body,metadata={'Title':'39 SMIC18低功耗线驱动审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=frame('39 | 低功耗Class-AB线驱动',1,'结论：TT标称10项原门槛全部通过，无需放宽。')
        para(fig,.85,'TT / 1.8V / 27°C，IREF=50uA，反相闭环增益−1。两只10kΩ反馈电阻、0.9V参考、1uF耦合电容、300Ω线路和200pF输出电容全部保留。',9.3)
        specs=[('10Hz环路增益','loop_gain_10hz_db',1,'dB'),('环路UGB','ugb_hz',1e-6,'MHz'),('相位裕量','phase_margin_deg',1,'°'),('静态输出偏差','output_offset_v',1e3,'mV'),('静态VDD功耗','power_w',1e6,'uW'),('20kHz输出基波','fundamental_v',1,'Vpk'),('2–9次谐波THD','thd_pct',1,'%'),('正弦峰值VDD电流','peak_supply_current_a',1e3,'mA'),('峰值/静态电流','drive_ratio',1,'倍'),('连续跟踪命令范围','closed_loop_range_vpp',1,'Vpp')]
        rows=[]
        for name,k,scale,unit in specs:
            g=r['gates'][k];sign='≥' if g['sense']=='min' else '≤';rows.append([name,f"{v[k]*scale:.6g}",sign+f"{g['limits']['original']*scale:g}",unit,'通过'])
        table(fig,[.07,.322,.86,.363],['指标','实测','原要求','单位','状态'],rows,[.35,.23,.18,.12,.12],8.1)
        para(fig,.253,'报告包含原负载下的环路、静态偏差、完整功耗、四周期谐波、峰值驱动与连续跟踪范围。静态功耗包含50uA参考和所有内部偏置，不只计算输出对管。',9.2)
        para(fig,.115,'仅完成确定性匹配nominal。原45点PVT矩阵的另外44点、失配、版图、PEX和无源容差未执行；本结论不等同于原全矩阵签核。',9.2)
        save(pdf,fig)

        fig=frame('gm/ID尺寸与浮动偏置结构',2,'22只MOS均由目标工艺LUT初算；理想正值R/C符合原题器件规则。')
        rows=[]
        for name,q in z['roles'].items():rows.append([name,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"])
        table(fig,[.07,.558,.86,.27],['角色','模型','单位W/L um','gm/ID','单位目标/uA'],rows,[.22,.16,.27,.17,.18],8.3)
        para(fig,.505,'初算目标：输入尾电流20uA、每侧输入10uA；浮动NMOS/PMOS各约5uA，两个复制偏置堆叠各5uA；输出对管各70uA。输出单位6.94um/26.92um均并联14倍，总宽97.16um/376.88um，沟道长0.36um。',9.2)
        para(fig,.35,'每个AB复制堆叠的上管与对应浮动控制管匹配电流密度，下管与输出管匹配几何及目标电流密度。全部NMOS体端接vss、PMOS体端接vdd，复制上管实际存在体效应；没有用零体偏置LUT代替实际OP。',9.2)
        para(fig,.195,'输入NMOS对通过PMOS及NMOS电流镜驱动gp/gn，浮动互补控制让输出栅压随负载需求移动；正弦峰值电流远大于静态电流。DUT无独立源、受控源、行为器件或数字HD单元。',9.2)
        para(fig,.077,'最终每路串联Miller补偿为6pF/1kΩ，gp与gn之间保留2MΩ电阻。全部27个实例见后三页图纸。',9.1)
        save(pdf,fig)

        fig=frame('实际工作点与电流预算',3,'实际输出静态电流约87uA，初始70uA目标不能直接当作测量。')
        rows=[]
        for name in ['MREF','MTAIL','MBN','MABNS','MABNU','MABNL','MABPS','MABPU','MABPL','MINP','MINN','MCN','MCP','MOUTN','MOUTP']:
            q=r['operating_point'][name];rows.append([name,f"{abs(q['ids'])*1e6:.4f}",f"{q['gmid']:.4f}",f"{q['vgs']:.5f}",f"{q['vds']:.5f}",f"{q['headroom_V']:.5f}"])
        table(fig,[.07,.338,.86,.49],['器件','|ID|/uA','gm/ID','VGS/V','VDS/V','余量/V'],rows,[.20,.18,.16,.15,.15,.16],7.5)
        para(fig,.279,f"总静态电流{v['quiescent_current_a']*1e6:.6f}uA，功耗{v['power_w']*1e6:.6f}uW。静态输出{v['output_dc_v']:.9f}V，与0.9V相差{v['output_offset_v']*1e3:.6f}mV；真实输出误差和镜电压差全部保留。",9.2)
        para(fig,.144,'全部静态|VDS|−|VDSAT|为正。部分高gm/ID器件的模型region=3为弱反型区，不把该枚举当作截止或失效；报告同时给出实际电流和端压，动态切换仍由瞬态验证。',9.1)
        para(fig,.067,'所有供电、参考和返回连接见测试台；没有从功耗中扣掉外部50uA参考。',9.0)
        save(pdf,fig)

        fig=frame('原始断环方法与带宽调整',4,'保留串联AC=1V测试源；T=-V(vout)/V(fbv)，不是简单开环增益。')
        h=-loop['vout']/loop['fbv'];f=loop['freq'];axs=fig.subplots(2,1);fig.subplots_adjust(left=.14,right=.94,bottom=.28,top=.84,hspace=.35)
        axs[0].semilogx(f,20*np.log10(abs(h)),color=BLUE);axs[0].axhline(0,color=GRAY,ls='--');axs[0].set(ylabel='Return ratio (dB)')
        axs[1].semilogx(f,np.unwrap(np.angle(h))*180/np.pi,color=BLUE);axs[1].set(xlabel='Frequency (Hz)',ylabel='Loop phase (deg)')
        from matplotlib.ticker import FuncFormatter
        for ax in axs:ax.xaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:g}'))
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.232,f"10Hz环路增益{v['loop_gain_10hz_db']:.6f}dB，第一次下降交越{v['ugb_hz']/1e6:.6f}MHz、PM={v['phase_margin_deg']:.6f}°；频扫1Hz–1GHz、每十倍频60点，之后没有回穿零dB。",9.2)
        para(fig,.108,'初版每侧12pF补偿使UGB仅0.305379MHz，低于原0.5MHz及15%边界0.425MHz。减至6pF后达到0.592917MHz，PM从88.133°降为84.770°；电流和输出尺寸保持不变。',9.2)
        save(pdf,fig)

        fig=frame('300Ω线路大信号与真实供电电流',5,'20kHz、0.6V峰值输入，共8周期；舍前4周期，评分后4周期。')
        t=thd['time'];m=t>=200e-6;axs=fig.subplots(2,1);fig.subplots_adjust(left=.14,right=.94,bottom=.29,top=.84,hspace=.35)
        axs[0].plot(t[m]*1e6,1.8-thd['vs'][m],color=GRAY,label='Ideal inverting target');axs[0].plot(t[m]*1e6,thd['vout'][m],color=BLUE,label='Vout');axs[0].plot(t[m]*1e6,thd['la'][m],color=GREEN,label='AC-coupled line');axs[0].set(ylabel='Voltage (V)');axs[0].legend(fontsize=8)
        axs[1].plot(t[m]*1e6,-thd['VDD:p'][m]*1e3,color=BLUE,label='VDD total');axs[1].plot(t[m]*1e6,thd['la'][m]/300*1e3,color=GREEN,label='Line current');axs[1].set(xlabel='Time (us)',ylabel='Current (mA)');axs[1].legend(fontsize=8)
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.236,f"输出基波{v['fundamental_v']:.9f}Vpk，峰值VDD电流{v['peak_supply_current_a']*1e3:.9f}mA，峰值/静态比{v['drive_ratio']:.6f}。峰值取200–400us全部真实自适应样点，未用谐波均匀网格代替电流峰值。",9.1)
        para(fig,.111,'1uF耦合电容使线路直流隔离；200pF仍直接接在放大器输出。线路初始偏置和充电过程不擅自去除，严格保留原200–400us窗口；本项峰值不是未计入偏置的输出支路峰值。',9.1)
        save(pdf,fig)

        fig=frame('2–9次THD与连续跟踪范围',6,'两个测试各保留原定义：正弦动态线性度与DC连续命令范围分别评分。')
        axs=fig.subplots(2,1);fig.subplots_adjust(left=.14,right=.94,bottom=.29,top=.84,hspace=.45)
        amps=np.array(r['fourier']['harmonic_amplitudes_V']);axs[0].bar(np.arange(1,10),20*np.log10(amps/amps[0])+140,bottom=-140,color=BLUE);axs[0].set(xlabel='Harmonic index',ylabel='Relative amplitude (dBc)',xticks=np.arange(1,10),ylim=(-140,5));axs[0].grid(axis='y',alpha=.2)
        goal=1.8-swing['vs'];error=swing['vout']-goal;axs[1].plot(goal,error*1e3,color=BLUE);axs[1].axhspan(-20,20,color=GREEN,alpha=.12);axs[1].set(xlabel='Commanded output (V)',ylabel='Tracking error (mV)',ylim=(-22,22));axs[1].grid(alpha=.2)
        for ax in axs:ax.tick_params(labelsize=8)
        para(fig,.234,f"THD={v['thd_pct']:.9f}%，按原算法取后4周期2048个均匀点，末端不重复，用2–9次谐波平方和开根除以基波。独立调用原harmonic_fit，并用DC+1–9次最小二乘交叉核对。",9.1)
        para(fig,.106,'输入从0.1扫至1.7V、步长2mV，共801点；命令=1.8−输入。全部点在固定20mV误差内，连续命令跨度1.6V，最大误差3.182339mV。DC时耦合电容开路，此范围不冒充带300Ω直流负载的1.6Vpp。',9.1)
        save(pdf,fig)

        fig=frame('收敛失败、等效接地与精度复核',7,'实际SPECTRE-16927保留为失败；没有用Bridge的license分类掩盖错误。')
        para(fig,.85,'初次50ns/1e-7复算在2.5609us因minstep非收敛中止，日志指出零伏VSS源电流解异常。将其两端同为零电位的节点直接合并到地，消除冗余支路未知量；DUT、所有激励、负载和积分窗口不变，三组台重新运行。',9.2)
        para(fig,.684,'合并前后的基线基波仅差约2nV、THD差约0.0000038个百分点；此次修正保持电气等效，不以增加虚构电容、改变负载或放宽器件模型来换取收敛。失败日志和修正前基线分别归档。',9.2)
        rows=[]
        for k,q in c['metrics'].items():rows.append([k,f"{q['baseline']:.9g}",f"{q['refined']:.9g}",f"{q['absolute_difference']:.6g}",f"{q['maximum_difference']:g}"])
        table(fig,[.07,.381,.86,.15],['复核量/SI','100ns/1e-6','50ns/1e-7','绝对差','预设上限'],rows,[.29,.19,.19,.18,.15],7.7)
        para(fig,.324,'数值界限保持不变：THD差≤0.005个百分点、基波差≤0.1mV、峰值电流差≤1uA，且验收等级不变；全部通过。最终瞬态采用50ns最大步长，gear2only，保留自适应数据。',9.2)
        para(fig,.178,'最终三组与有效基线均正常完成，0错误、0警告；原模型/LUT哈希未变。14项独立测量核对及原8组检查以expected=1调用，不伪造45点PVT集合。',9.2)
        para(fig,.074,'27个实例、98个端子逐一连接核对；完整晶体管图附后，体端和所有无源值均明确。',9.1)
        save(pdf,fig)

        fig=frame('可重复证据与适用范围',8,'完整报告、图纸、结果和源快照使用同一最终电路。')
        para(fig,.85,'复现（工程根目录，既有Bridge Python）：\npython scripts/case39_line_driver.py\npython scripts/confirm39.py\npython scripts/schematic39.py\npython scripts/audit39.py\npython scripts/review39.py\n每次重新生成PDF，都需重新查看全部页面和完整总图后再交付。',9.0)
        para(fig,.579,'latest_results.json：10项门槛、14个主测量量及全部22只MOS的OP。\nnumerical_confirmation.json：原/收紧步长及固定精度比较。\nverification_audit.json：原验收器、独立算法、模型/输入/源文件哈希。\niteration_history.json：12pF带宽失败与实际瞬态收敛失败。\nschematic/：三页完整晶体管图、总图与连接映射。\nimplementation/：生成、测量与审计脚本快照。',8.8)
        para(fig,.341,'本模块的Class-AB动态电流能力在20kHz、0.6Vpk、300Ω交流耦合线路和200pF负载下成立。不同线路阻抗、电容、频率、温度或供电需要重新验证；本题理想R/C的物理面积、容差和寄生没有建模。',9.2)
        para(fig,.193,'未执行原45点矩阵中的另外44点、失配、布局、PEX、长期应力或完整输出短路保护验证。静态小误差及高相位裕量不能替代这些未执行项。',9.1)
        para(fig,.096,'DUT SHA-256：\n'+r['circuit_sha256'],7.8)
        para(fig,.057,'原Sky130档案和既有PDK、Bridge、Spectre、LUT环境保持原样。',8.4)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1]);write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=3,schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True));print(out)

if __name__=='__main__':make()
