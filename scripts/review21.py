"""Case21 report: same full review and complete-schematic delivery scheme."""
from review_pdf import *
from review11 import frame,para,table
import subprocess

def make():
    case=ROOT/'cases/21-highpsrr-bandgap';r=json.loads((case/'latest_results.json').read_text());z=json.loads((case/'sizing.json').read_text());v=r['values'];nodes=r['dc_nodes']
    runs={k:ROOT/x for k,x in r['groups'].items()};t=data(runs['static'],'temperature.dc');a=data(runs['ac'],'ac.ac');s=data(runs['startup'],'tran.tran')
    body=ROOT/'reports/21-highpsrr-bandgap-body.pdf';out=ROOT/'reports/21-highpsrr-bandgap-review.pdf'
    with PdfPages(body,metadata={'Title':'21 SMIC18 高PSRR带隙基准审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=frame('21 | 高PSRR带隙基准审查',1,'结论：五项适用nominal原门槛全部通过，无需10%或15%放宽。')
        para(fig,.853,'条件：SMIC18MMRF TT / 1.8V / 27°C / 外部1pF。温漂保留-40至85°C、步长1°C的全部126点。该范围对应原题nominal gate，不代表另外三个代表性PVT点通过。',9.3)
        rows=[]
        for label,key,scale,unit in [('输出偏离1.2V','reference_error_V',1e3,'mV'),('全温扫温漂','tempco_ppm_C',1,'ppm/°C'),('供电耦合@0.01Hz','supply_gain_low_dB',1,'dB'),('供电耦合@1MHz','supply_gain_1MHz_dB',1,'dB'),('90–100us启动终值误差','startup_error_fraction',100,'%')]:
            g=r['gates'][key];rows.append([label,f"{g['value']*scale:.6g}",*[f"≤{g['limits'][q]*scale:.6g}" for q in ['original','10pct','15pct']],unit])
        table(fig,[.07,.475,.86,.26],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.15,.14,.14,.14,.14],8.0)
        para(fig,.421,f"标称VBG={v['vref_V']:.6f}V，VDD功耗{v['nominal_power_W']*1e6:.3f}uW。温扫电压{v['temp_min_V']:.6f}–{v['temp_max_V']:.6f}V；最大温扫功耗{v['maximum_temperature_power_W']*1e6:.3f}uW。功耗仅为工程记录，原题没有功耗门槛。",9.1)
        para(fig,.304,'负dB表示供电到输出的传递增益；本次等价电源抑制为70.625dB和35.392dB。10%/15%按耦合幅值扩大，不能对负dB数字直接乘百分比。电压窗口以1.2V为中心、原误差±150mV。',9.1)
        para(fig,.181,'启动误差极小只表示同一确定性模型回到独立DC解，不表示绝对精度、随机失配或测量噪声达到该数量级。输出是高阻参考，1pF测试负载不等于ADC驱动验证。',9.1)
        save(pdf,fig)

        fig=frame('结构与gm/ID尺寸依据',2,'级联PTAT/CTAT核心、第四路自偏置、独立启动及物理RC输出。')
        para(fig,.85,'误差放大器使va≈vb；Q0:Q1面积比1:8建立ΔVBE，经RPTAT形成PTAT电流。输出镜比1:2，RREF叠加QREF的VBE。级联管使上层镜漏压接近；第四路镜向MNB供电，避免VDD电阻偏置直接调制放大器电流。',9.1)
        labels=[('mirror','MP0/MP1/MP2','2/2/4'),('cascode','MPC0/MPC1/MPC2','1/1/2'),('amp_bias_mirror','MPA','1'),('amp_bias_cascode','MPCA','1'),('input','MINA/MINB','1/1'),('load','MPD/MPM','1/1'),('bias','MNB/MTAIL','1/3'),('cascode_bias','MPCB','1'),('startup_p','MPST','1'),('startup_n','MNST/MSTART','1/1')]
        rows=[]
        for key,label,m in labels:
            q=z['roles'][key];rows.append([label,q['model'],f"{q['rounded_W_um']:.2f}/{q['L_um']:g}",m,f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"])
        table(fig,[.07,.405,.86,.34],['器件','模型','单位W/L um','m','gm/ID','初算I/uA'],rows,[.29,.1,.19,.12,.14,.16],7.8)
        para(fig,.352,'全部MOS来自已有目标PDK TT LUT。L4um角色使用本工程既有补充表，VDS=0.9V；L1um角色也用现有0.9V表。体效应、低VDS余量和实际gm/ID均由最终OP复核。每单位镜宽52.02um，避免104um单实例超出100um模型范围。',9.0)
        para(fig,.221,'原厂NPN npn18a4单位2×2um，area=1/8/2。工艺电阻均rpposab_3t且W=1um：RPTAT16.5um、RREF73.3um、RFILT30um；RCB0–4各200um。所有第三端接SUB，bench把SUB接AVSS。',8.9)
        para(fig,.106,'CCORE/CFILT/CCOMP为工艺MIM，名义60/20/0.5pF，总板面积约0.0829mm²，另有1pF外部负载。没有理想R/C、源或行为器件放在DUT内部；未做布局/DRC/PEX。',8.9)
        save(pdf,fig)

        fig=frame('实际工作点与级联余量',3,'全部18个MOS实例；电流幅度列取绝对值，电压符号沿Spectre定义。')
        rows=[]
        for dev,q in r['operating_point'].items():rows.append([dev,f"{abs(q['ids'])*1e6:.5g}",f"{q['gmid']:.3f}",f"{q['vgs']:.4f}",f"{q['vds']:.4f}",f"{q['headroom_V']:.4f}"])
        table(fig,[.07,.31,.86,.536],['器件','|ID|/uA','gm/ID','VGS/V','VDS/V','|VDS|-|VDSAT|'],rows,[.16,.17,.14,.16,.16,.21],7.7)
        para(fig,.262,f"pc0/pc1/pc2={nodes['X.pc0']:.6f}/{nodes['X.pc1']:.6f}/{nodes['X.pc2']:.6f}V，cbias={nodes['X.cbias']:.6f}V。输出上层MP2是最紧余量，约{r['operating_point']['MP2']['headroom_V']*1e3:.2f}mV；这只证明nominal OP。",9.0)
        para(fig,.159,f"MSTART稳态电流{abs(r['operating_point']['MSTART']['ids'])*1e12:.3f}pA，注入关闭；检测器MPST仍有{abs(r['operating_point']['MPST']['ids'])*1e6:.3f}uA直通电流，计入功耗。MNST处于预期低VDS状态，不能以放大管饱和条件判其失败。",9.0)
        save(pdf,fig)

        fig=frame('全温扫与电源耦合',4,'温扫126点；AC为0.01Hz–100MHz，正式门槛仅在0.01Hz和1MHz两点。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.27,top=.84,hspace=.44,wspace=.40)
        axs[0,0].plot(t['temp'],t['VBG'],color=BLUE);axs[0,0].set(xlabel='Temperature (C)',ylabel='VBG (V)')
        axs[0,1].plot(t['temp'],-1.8*t['VDD:p']*1e6,color=BLUE);axs[0,1].set(xlabel='Temperature (C)',ylabel='VDD power (uW)')
        for key,label,col in [('X.vcore','Core',GRAY),('VBG','Output',BLUE)]:axs[1,0].semilogx(a['freq'],20*np.log10(abs(a[key])),color=col,label=label)
        axs[1,0].scatter([.01,1e6],[-60,-30],marker='x',color='#b33a3a',label='Required points');axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Supply gain (dB)');axs[1,0].legend(fontsize=7)
        from matplotlib.ticker import FuncFormatter
        axs[1,0].xaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:g}'))
        axs[1,1].plot(t['temp'],(t['X.va']-t['X.vb'])*1e6,color=BLUE);axs[1,1].set(xlabel='Temperature (C)',ylabel='va - vb (uV)')
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.214,f"温漂=(max-min)/(平均电压×125)={v['tempco_ppm_C']:.6f}ppm/°C。平均电压{v['temp_average_V']:.9f}V，按原.measure AVG沿温度积分，不把126点的简单算术平均替换它。",9.0)
        para(fig,.115,f"0.01Hz供电耦合{v['supply_gain_low_dB']:.6f}dB，1MHz为{v['supply_gain_1MHz_dB']:.6f}dB。输出RC主要衰减高频耦合，无法修复直流供电依赖；低频改善来自级联及核心派生偏置。",9.0)
        save(pdf,fig)

        fig=frame('独立DC目标下的真实供电启动',5,'VDD在首1us从0升至1.8V，运行100us；无非零初值，无强制输出轨迹。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,bottom=.27,top=.84,hspace=.44,wspace=.42)
        us=s['time']*1e6
        for j,xlim in enumerate([(0,100),(0,10)]):
            axs[0,j].plot(us,s['AVDD'],color=GRAY,label='VDD');axs[0,j].plot(us,s['VBG'],color=BLUE,label='VBG');axs[0,j].set(xlabel='Time (us)',ylabel='Voltage (V)',xlim=xlim);axs[0,j].legend(fontsize=8)
        axs[1,0].plot(us,np.maximum(0,-s['VDD:p'])*1e6,color=BLUE);axs[1,0].set(xlabel='Time (us)',ylabel='Positive supply current (uA)',xlim=(0,10))
        axs[1,1].plot(us,(s['VBG']-v['vref_V'])*1e3,color=BLUE);axs[1,1].axhspan(-.01*v['vref_V']*1e3,.01*v['vref_V']*1e3,color=GREEN,alpha=.1);axs[1,1].set(xlabel='Time (us)',ylabel='Independent DC error (mV)',xlim=(5,30),ylim=(-20,20))
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.215,f"独立27°C DC目标={v['vref_V']:.9f}V；90–100us时间平均={v['startup_average_V']:.9f}V，误差约{v['startup_error_fraction']*100:.3g}%，原门槛1%。输出初值0V，所保存网格上的峰值{v['startup_peak_V']:.9f}V。",9.0)
        para(fig,.108,'原题只约束100us内回到独立DC目标，未另设峰值电流、能量、入窗时间或过冲门槛。图中早期轨迹和供电电流作为完整工程证据；不把微小数值尾差解释成真实器件精度。',9.0)
        save(pdf,fig)

        fig=frame('有因果依据的迭代记录',6,'先测供电耦合，再隔离残余通路；失败运行和相同合同均保留。')
        table(fig,[.07,.60,.86,.23],['版本','结构','0.01Hz / 1MHz','结果'],[
            ['首版','长沟道镜；VDD电阻偏置','-54.060 / -32.991dB','低频失败'],
            ['中间版','增加PMOS级联；偏置不变','-57.463 / -34.759dB','低频仍失败'],
            ['最终版','第四路镜生成放大器偏置','-70.625 / -35.392dB','五项原门槛通过'],
        ],[.12,.40,.29,.19],8.0)
        para(fig,.541,'长沟道提高输出电阻，但核心支路与输出支路漏压不同，仍有镜像误差随VDD变化。增加级联后，pc0/pc1/pc2约1.593V，上层镜漏压接近；输出参考的电源耦合下降，但尚未达到60dB目标。',9.3)
        para(fig,.412,'低频AC显示放大器尾电流仍由VDD电阻支路调制；镜负载的二极管节点与pctrl跟随供电的斜率不同，通过输入对有限输出电阻转换成差分误差。最终从PTAT核心单独镜出约3uA，给MNB和三倍MTAIL建立偏置，切断该直接供电通路。',9.3)
        para(fig,.254,'自偏置引入零电流平衡点，所以保留MPST/MNST/MSTART独立启动。最终1us供电斜坡从零供电起动，并回到独立DC解。CCORE60pF、CFILT20pF、CCOMP0.5pF和1pF外部负载在三版间保持一致。',9.2)
        para(fig,.128,'这是一阶、无修调、高阻带隙。约0.083mm²的MIM电容板面积与级联电压余量是实际代价；没有宣称最小面积、最低功耗或完整PVT/失配鲁棒性。',9.2)
        save(pdf,fig)

        fig=frame('原始算法、运行与证据边界',7,'9项数值交叉核对、上游5项nominal checks及完整端子复核。')
        para(fig,.85,'冻结原instruction、参考网表、正式verifier、utils、三份bench及netlist guide。独立重算Spectre温扫、AC和启动原始数据，并传给未改写的上游checks(rows,{NOMINAL})；五项nominal判断全部通过。未调用另外三个PVT点并冒称完整通过。',9.2)
        para(fig,.711,'最终三组输入快照使用同一电路，模型和LUT哈希完整；32个器件、114个端子的型号、参数与连接独立核对。全部模拟MOS、BJT的体端/衬底和工艺无源参数均绘出，没有用功能框代替内部电路。',9.2)
        para(fig,.585,'Spectre24.1实际日志均0错误/0警告。Bridge将日志中的license与“0 errors”组合误报license error；保留该元数据，并按成功许可检查、正常结束及完整PSF核实有效性。PDK、Bridge、Spectre和原LUT未修改。',9.0)
        para(fig,.462,'复现：激活virtuoso-bridge-lite/.venv，在工程根目录执行：\npython scripts/case21_highpsrr_bandgap.py\npython scripts/schematic21.py\npython scripts/audit21.py\npython scripts/review21.py\n重新生成后必须再次目检图纸和PDF；不会自动继承本次目检结论。',8.4)
        para(fig,.275,'最终运行：\n'+'\n'.join(r['run_dirs']),8.1)
        para(fig,.163,'未覆盖：另外三个代表性工艺/电压/温度组合，完整笛卡尔PVT、失配、噪声、版图及PEX、输出缓冲与采样负载驱动。1°C步长的全温扫属于原功能合同；它不等于完成其他工艺角。',9.0)
        save(pdf,fig)

        fig=frame('精确网表与完整图纸',8,'顶层端口顺序AVDD AVSS VBG SUB；DUT只用目标工艺物理器件。')
        net='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.073,.853,net,fontsize=7.4,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.25)
        para(fig,.199,'后附S1–S3为全部32个实例：18MOS、3NPN、8个工艺电阻、3个MIM电容，共114个端子。RFILT/CFILT是DUT的一部分，1pF外部CLOAD不计入DUT器件数。',9.0)
        para(fig,.1,'完整总图：cases/21-highpsrr-bandgap/schematic/full.svg / full.pdf\n连接清单：schematic/connectivity.json；独立图纸核对：schematic_independent_review.json',8.1)
        para(fig,.05,'电路SHA-256：'+sha(case/'circuit.scs'),7.2)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1])
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=3,schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True))
    print(out)

if __name__=='__main__':make()
