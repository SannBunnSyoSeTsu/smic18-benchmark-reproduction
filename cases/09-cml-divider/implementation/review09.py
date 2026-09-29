"""Full CML review from frozen measured results; visual review remains manual."""
from review_pdf import *
from review11 import frame,para,table
import subprocess

def make():
    case=ROOT/'cases/09-cml-divider';r=json.loads((case/'latest_results.json').read_text());z=json.loads((case/'sizing.json').read_text());v=r['values'];freq=v['frequencies']
    waves={key:data(ROOT/r['groups'][key],'tran.tran') for key in freq}
    body=ROOT/'reports/09-cml-divider-body.pdf';out=ROOT/'reports/09-cml-divider-review.pdf'
    with PdfPages(body,metadata={'Title':'09 SMIC18 CML二分频器审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=frame('09 | CML二分频器审查',1,'结论：四个原频点与静态功耗全部通过，无需10%或15%放宽。')
        para(fig,.853,'SMIC18MMRF TT / 1.8V / 27°C。差分时钟源300mVpp、共模0.9V，每端50Ω源阻抗；每端输出负载10fF。外部150uA参考由VDD供给，纳入功耗。',9.3)
        rows=[]
        for key,q in freq.items():
            rows += [[key+' 最小逐周期摆幅',f"{q['minimum_cycle_swing_Vpp']*1e3:.3f}",'≥200','≥180','≥170','mVpp'],[key+' fIN/2分量',f"{q['target_tone_Vpp']*1e3:.3f}",'≥200','≥180','≥170','mVpp'],[key+' 连续交替周期',str(q['alternating_cycles']),'40','40','40','周期']]
        rows.append(['静态总功耗',f"{v['dc_power_W']*1e3:.6f}",'<1.5','<1.65','<1.725','mW'])
        table(fig,[.07,.32,.86,.43],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.33,.15,.13,.13,.13,.13],7.8)
        para(fig,.266,'10GHz最小逐周期摆幅210.371mVpp，距原200mVpp门槛约5.19%；功耗1.455351mW，比原1.5mW上限低约2.98%。两个余量均有限，不能由nominal通过推断跨工艺角通过。',9.0)
        para(fig,.152,'频点、时钟幅值、负载、启动丢弃时间和连续40周期正确交替均保持原合同。10%/15%只放宽摆幅、目标分量幅值和功耗；功能判据从未放宽。',9.1)
        save(pdf,fig)

        fig=frame('锁存结构与gm/ID初始尺寸',2,'互补时钟控制主从静态CML；每个锁存器只有一条共享尾电流。')
        para(fig,.85,'主级在clkp相位采样交换极性的outn/outp反馈，另一相位由交叉耦合对保持；从级在clkn相位采样mp/mn。数据对和再生对通过两只时钟MOS分配尾电流，构成二分频闭环。',9.3)
        rows=[]
        for role,label,m in [('reference','MBIAS / 两只TAIL','1 / 2.3'),('clock','四只时钟管','1'),('data','四只数据管','1'),('regeneration','四只再生管','1')]:
            q=z['roles'][role];rows.append([label,f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}",f"{q['ft_Hz']*1e-9:.3f}"])
        table(fig,[.07,.553,.86,.19],['角色','单位W/L um','m','gm/ID','初算I/uA','LUT fT/GHz'],rows,[.29,.20,.12,.12,.13,.14],7.8)
        para(fig,.502,'参考/尾管L0.36um、gm/ID=16，以较小过驱动保留叠层余量；时钟管L0.18um、gm/ID=14适应150mV差分峰值。数据/再生管gm/ID=8，减小输出节点的交叉耦合栅负载。LUT均为既有TT、VDS0.45V、VSB0V表。',9.2)
        para(fig,.345,'初算每尾345uA，实际停钟工作点约329.264uA。两尾加150uA参考构成约808.53uA总VDD电流。m=2.3是原理图并联倍数，不代表已完成版图匹配。LUT的fT用于选点比较，不能代替完整分频仿真。',9.1)
        para(fig,.211,'RMP/RSN=1200Ω，RMN/RSP=1206Ω。0.5%不对称及outp=1.0V/outn=0.8V nodeset仅选择DC初始相位，瞬态不强制节点。原合同允许DUT内有限正值理想R/C；本实现使用15只原厂n18和4只理想电阻。',9.1)
        para(fig,.092,'时钟源、IREF和输出10fF负载均在测试台内；DUT内部没有独立源、受控源或行为模型。所有MOS体端接vss。',9.0)
        save(pdf,fig)

        fig=frame('全部MOS的实际静态工作点',3,'功耗台把clkp、clkn同时停在0.9V；此OP不是动态锁存状态。')
        rows=[]
        for name,q in r['operating_point'].items():rows.append([name,f"{abs(q['ids'])*1e6:.4f}",f"{q['gmid']:.3f}",f"{q['vgs']:.4f}",f"{q['vds']:.4f}",f"{q['headroom_V']:.4f}"])
        table(fig,[.07,.354,.86,.486],['器件','|ID|/uA','gm/ID','VGS/V','VDS/V','VDS-VDSAT/V'],rows,[.17,.17,.14,.15,.15,.22],7.8)
        para(fig,.3,f"静态iref={r['dc_nodes']['iref']:.6f}V，mtail/stail约0.278747V；数据与再生公共源约0.8433V。高源电位使体效应显著，不能把零体偏置LUT的VGS直接当作电路实际VGS。",9.2)
        para(fig,.178,'停钟时数据对与再生对同时分流，单只上层MOS约82uA，实际gm/ID约11.2；它与150uA初算gm/ID=8并不矛盾。动态时电流重新分配，最终速度由四频点的真实瞬态验收。',9.2)
        para(fig,.079,'静态功耗=-VDD×I(VDD:p)，包括150uA参考；不把外部时钟驱动器的能量计入本题静态功耗指标。',8.8)
        save(pdf,fig)

        fig=frame('四频点的全部40周期观察窗',4,'先丢弃5ns，再按每个输入周期0.4T处的差分符号判断连续交替。')
        axs=fig.subplots(4,1);fig.subplots_adjust(left=.13,right=.94,bottom=.22,top=.84,hspace=.65)
        for ax,(key,q) in zip(axs,freq.items()):
            d=waves[key];t=d['time'];m=t>=5e-9;ax.plot((t[m]-5e-9)*q['frequency_Hz'],(d['outp'][m]-d['outn'][m])*1e3,color=BLUE,lw=1)
            ax.plot(np.arange(40)+.4,np.array(q['samples_V'])*1e3,'.',color='#ba4835',ms=3)
            ax.axhline(0,color=GRAY,lw=.4);ax.set(xlim=(0,40),ylabel=key+' / mV');ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        axs[-1].set_xlabel('Input cycles after 5 ns')
        para(fig,.158,'四条波形均40次有效采样、39次相邻符号交替；±10mV内的样点视为无效。完整逐周期摆幅另行检查，未以选取的局部波形或全窗峰峰值替代。',9.1)
        para(fig,.078,'输出频率还从20次正向过零测得：0.5 / 1 / 2.5 / 5GHz。此列为实测周期结果，区别于预设的fIN/2投影目标频率。',9.0)
        save(pdf,fig)

        fig=frame('10GHz下的动态细节与最小摆幅',5,'最大步长及保存间隔1ps；其他三频点2ps，均严于原台要求。')
        d=waves['10g'];q=freq['10g'];ns=d['time']*1e9
        axs=fig.subplots(3,1);fig.subplots_adjust(left=.13,right=.94,bottom=.28,top=.84,hspace=.52)
        for a,b,label,c in [('srcp','srcn','Source',GRAY),('clkp','clkn','DUT clock',BLUE)]:axs[0].plot(ns,(d[a]-d[b])*1e3,label=label,color=c)
        axs[0].set(xlim=(5,5.6),ylabel='Clock diff (mV)');axs[0].legend(fontsize=7,ncol=2)
        for a,b,label,c in [('X.mp','X.mn','Master',GRAY),('outp','outn','Slave',BLUE)]:axs[1].plot(ns,(d[a]-d[b])*1e3,label=label,color=c)
        axs[1].set(xlim=(5,5.6),xlabel='Time (ns)',ylabel='Latch diff (mV)');axs[1].legend(fontsize=7,ncol=2)
        axs[2].plot(np.arange(40),np.array(q['cycle_swings_Vpp'])*1e3,'o-',ms=3,color=BLUE);axs[2].axhline(200,color='#ba4835',ls='--',label='Original 200mV');axs[2].set(xlabel='Input-cycle index',ylabel='Per-cycle swing (mV)');axs[2].legend(fontsize=7)
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.224,'10GHz源差分幅度300mVpp，DUT时钟引脚299.916mVpp。输出全窗峰峰值416.916mV，最小单输入周期峰峰值210.371mV；窗口切分使两者不同，验收严格采用后者。',9.1)
        para(fig,.113,'fIN/2时间加权分量430.828mVpp。它是去除DC投影后的基波等效幅值，非正弦波的基波峰峰值可以大于实际全波形峰峰值；两种定义不能混用。',9.1)
        save(pdf,fig)

        fig=frame('失败迭代与最终电流分配',6,'保留所有真实失败结果；最终仅相对首版提高尾电流倍数。')
        table(fig,[.07,.595,.86,.245],['尾m / R / 再生gmID','10G最小周期 / 分量','交替周期','结论'],[
            ['2 / 1200Ω / 8','145.42 / 300.65mV','40','摆幅失败'],
            ['2.3 / 900Ω / 10','0.784 / 3.42mV','1','振幅塌陷'],
            ['2.3 / 1400Ω / 10','141.28 / 4.52mV','31','未锁定'],
            ['2.3 / 1200Ω / 8','210.37 / 430.83mV','40','全部原门槛'],
        ],[.32,.35,.13,.20],8.0)
        para(fig,.54,'首版已有正确二分频和足够目标分量，但最小单周期摆幅145.42mV，连15%放宽后的170mV也未达到。最终提高尾镜倍数2→2.3，保持数据/再生尺寸与1200Ω负载，补足高速摆幅，静态功耗从1.30321升至1.45535mW。',9.3)
        para(fig,.378,'900Ω方案同时增加再生管gm/ID至10，输出塌陷；1400Ω方案全窗摆幅虽达557mV，但只有31周期交替且fIN/2分量仅4.52mV。该对比只能说明联合参数对锁存动态的影响，不能从同时改变的两项参数断言单一因果。',9.3)
        para(fig,.224,'小RC时间常数、较大再生gm或较大输出摆幅均不是充分条件。必须同时满足采样传递、再生保持、相位关系、逐周期摆幅和目标频率分量。静态OP正常也不能证明高频功能通过。',9.3)
        para(fig,.103,'最终余量仅限本地TT确定性原理图模型；没有执行其他工艺角、电压温度扫描、随机失配、相位噪声或PEX。',9.1)
        save(pdf,fig)

        fig=frame('原始算法复核与运行证据',7,'17项数值交叉核对；原speed_check的四个TT频点全部通过。')
        para(fig,.85,'把实际Spectre time/outp/outn逐行传给未修改的上游divider_metrics和speed_check；每频点核对全窗摆幅、最小周期摆幅、时间加权目标分量和交替周期共16项，再独立重算静态VDD功耗。模型、LUT、原题和五组最终运行输入哈希一致。',9.1)
        para(fig,.715,'外部有限PWL源逐点实现原PULSE时序，并与解析式交叉核对。早期5GHz运行真实出现CMI-2204：浮点末点造成时间重复；已改为整数飞秒网格并重跑。该失败日志保留且不参与验收。',9.1)
        para(fig,.587,'最终五组Spectre24.1日志均0错误/0警告。Bridge的license error字符串误报与上述真实PWL错误分别记录：最终日志许可检查成功、仿真正常结束、PSF完整，Bridge元数据未改写。',9.0)
        para(fig,.465,'复现命令（virtuoso-bridge-lite/.venv，工程根目录）：\npython scripts/case09_cml.py\npython scripts/schematic09.py\npython scripts/audit09.py\npython scripts/review09.py\n报告重新生成后须重新目检，不自动继承本次检查结论。',8.5)
        para(fig,.27,'五组最终运行：\n'+'\n'.join(r['run_dirs']),8.0)
        para(fig,.092,'原题工艺角ff/ss/fs/sf未计入当前nominal交付。没有修改PDK、Bridge、Spectre或原有LUT环境。',9.0)
        save(pdf,fig)

        fig=frame('精确网表与完整晶体管图纸',8,'顶层端口：vss iref vdd clkn clkp outn outp。')
        net='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.073,.853,net,fontsize=8.5,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.4)
        para(fig,.34,'后附S1/S2含全部15只n18与4只电阻，共19个实例、68个端子。所有D/G/S/B和两端电阻均有连接映射、实例参数及独立核对，没有隐藏子电路。',9.2)
        para(fig,.217,'完整总图：cases/09-cml-divider/schematic/full.svg / full.pdf\n连接清单：schematic/connectivity.json\n独立图纸检查：schematic_independent_review.json',8.8)
        para(fig,.10,'电路SHA-256：\n'+sha(case/'circuit.scs'),8.0)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1])
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=2,schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True))
    print(out)

if __name__=='__main__':make()
