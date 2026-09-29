"""Full sampling-feedback review with actual waveforms and transistor sheets."""
from review_pdf import *
from review11 import frame,para,table
import subprocess

def make():
    case=ROOT/'cases/33-sampling-ota-gain1';r=json.loads((case/'latest_results.json').read_text());v=r['values'];z=json.loads((case/'sizing.json').read_text());c=json.loads((case/'numerical_confirmation.json').read_text());a=json.loads((case/'verification_audit.json').read_text());d={k:data(ROOT/p,'ac.ac' if k=='loop' else 'noise.noise' if k=='noise' else 'swing.dc' if k=='ranges' else 'tran.tran',required=['out'] if k=='noise' else ()) for k,p in r['groups'].items() if k!='rejection'}
    body=ROOT/'reports/33-sampling-ota-gain1-body.pdf';out=ROOT/'reports/33-sampling-ota-gain1-review.pdf'
    specs=[('相位裕量','phase_margin_deg',1,'°'),('零差分共模误差','output_common_mode_error_v',1e3,'mV'),('总DC功耗','power_w',1e3,'mW'),('原rise建立时间','rise_settling_time_s',1e9,'ns'),('原fall建立时间','fall_settling_time_s',1e9,'ns'),('原rise动态误差','rise_dynamic_error_fraction',100,'%'),('原fall动态误差','fall_dynamic_error_fraction',100,'%'),('高台静态误差','high_static_error_fraction',100,'%'),('低台静态误差','low_static_error_fraction',100,'%'),('开环3dB输出摆幅','output_range_v',1,'V'),('差分输出噪声','output_noise_vrms',1e6,'uVrms'),('CMFB峰值偏移','cmfb_max_deviation_v',1e3,'mV'),('CMFB释放20ns残差','cmfb_residual_20ns_v',1e3,'mV'),('CMFB释放100ns残差','cmfb_residual_100ns_v',1e3,'mV')]
    with PdfPages(body,metadata={'Title':'33 SMIC18采样反馈OTA增益1审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=frame('33 | 采样反馈OTA：增益1',1,'结论：TT标称14项检查在10%放宽内通过，仅3dB输出摆幅未达原门槛。')
        para(fig,.853,'TT / 1.8V / 27°C；IREF=50uA，VOCM=0.9V。保留Cs=Cf=1pF、每端CL=1pF，差分目标阶跃0.9V，双向建立与原10Hz–10GHz输出噪声积分。',9.2)
        rows=[]
        for name,key,scale,unit in specs:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([name,f"{g['value']*scale:.5g}",*[sign+f"{g['limits'][k]*scale:.5g}" for k in ['original','10pct','15pct']],unit])
        table(fig,[.07,.282,.86,.444],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.16,.15,.15,.15,.10],7.6)
        para(fig,.223,'原开环3dB压缩摆幅要求≥1.8V，实测1.699153V，差5.60%；10%边界1.62V。双向动态误差、静态误差和所有其余适用nominal指标达到原值。',9.0)
        para(fig,.117,'只完成确定性的匹配nominal。原30点PVT的其余29点、另外两点共模扰动和20次局部失配未执行；不能把下文匹配抑制表征当作失配通过。',9.0)
        save(pdf,fig)

        fig=frame('结构、gm/ID与偏置选择',2,'折叠输入、对称共源输出、Miller补偿与连续共模反馈。')
        rows=[]
        for name,q in z['roles'].items():rows.append([name,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}",f"{q['lut_metadata']['vds_V']:g}"])
        table(fig,[.07,.565,.86,.266],['角色','模型','单位W/L um','gm/ID','初算/uA','VDS/V'],rows,[.23,.12,.23,.14,.14,.14],7.9)
        para(fig,.508,'所有模拟角色重新查询既有SMIC18表，单位电流10uA；并联倍数产生输入支路100uA、PMOS折叠源150uA、差额支路50uA、输出支路700uA和共模输入支路50uA。IREF端的50uA也由VDD供给，包含在功耗中。',9.2)
        para(fig,.34,'复用工程第35项已经验证的折叠Miller结构作为初值，保留相同器件角色和尺寸。第33项重新建立自己的完整仿真：电容反馈、0.9V阶跃、1.5pF等效环路负载、3dB压缩摆幅和10GHz噪声频带，未拿35项历史测量作为本项结果。',9.1)
        table(fig,[.07,.137,.86,.117],['网络','最终值','作用'],[['每侧Miller串联RC','400Ω / 2pF','主极点与零点控制'],['每侧共模取样RC','100kΩ // 100fF','输出平均值检测'],['级联偏置电阻','28kΩ / 40kΩ','低余量NMOS/PMOS偏置']], [.33,.29,.38],8.2)
        para(fig,.079,'本题原器件规则允许理想R/C；DUT无独立源、受控源或行为器件。全电路为模拟，无HD数字单元。',9.0)
        save(pdf,fig)

        fig=frame('实际OP、体端与余量',3,'30只MOS的工作点逐个保存；代表性支路列在下表。')
        rows=[]
        for dev in ['MREF','MINP','MSP','MPCP','MNCP','MSINKP','MSECONDP','MLOADP','MCMT','MCMREF','MCMSENSE','MCMD','MCMM','MCMND']:
            q=r['operating_point'][dev];rows.append([dev,f"{abs(q['ids'])*1e6:.5f}",f"{q['gmid']:.4f}",f"{q['vgs']:.4f}",f"{q['vds']:.4f}",f"{q['headroom_V']:.4f}"])
        table(fig,[.07,.355,.86,.476],['器件','|ID|/uA','gm/ID','VGS/V','VDS/V','|VDS|-|VDSAT|'],rows,[.22,.18,.13,.13,.13,.21],7.7)
        para(fig,.295,'输入管体端接vss，真实尾节点电压带来体效应，因此OP的gm/ID不会机械等于零体偏置LUT目标。PMOS信号级联管体端分别接fp/fn；其复制偏置管体端接pcb，完整体端连接在图纸中明确绘出。',9.2)
        para(fig,.155,'所有30只MOS在标称静态点的|VDS|-|VDSAT|均为正；这不代表大信号全过程都保持饱和。对称第二级、较低共模输出阻抗和补偿共同决定建立与共模恢复，静态余量不能替代瞬态验证。',9.2)
        para(fig,.077,'输出零差分共模偏差3.638mV。局部共模检测器使用有限跨导和二极管NMOS负载，偏差及额外电流均保留。',8.9)
        save(pdf,fig)

        fig=frame('差模环路与真实电容反馈建立',4,'原rise对应输出向-0.9V，原fall对应返回0V；名称沿用原验收器。')
        w=d['loop'];h=.5*(w['voutp']-w['voutn']);f=w['freq'];s=d['settling'];t=s['time'];y=s['voutp']-s['voutn']
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.29,top=.84,hspace=.48,wspace=.42)
        axs[0,0].semilogx(f,20*np.log10(abs(h)),color=BLUE);axs[0,0].axhline(0,color=GRAY,ls='--');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Return ratio (dB)')
        axs[0,1].semilogx(f,np.unwrap(np.angle(h))*180/np.pi,color=BLUE);axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Loop phase (deg)')
        axs[1,0].plot(t*1e9,y,color=BLUE);axs[1,0].set(xlabel='Time (ns)',ylabel='Differential output (V)')
        for name,start,stop,target,col in [('rise',25e-9,65e-9,-.9,BLUE),('fall',105e-9,145e-9,0,GREEN)]:
            m=(t>=start)&(t<=stop);axs[1,1].plot((t[m]-start)*1e9,(y[m]-target)*1e3,label=name,color=col)
        axs[1,1].set(xlabel='From original edge origin (ns)',ylabel='Target error (mV)',ylim=(-3,3));axs[1,1].axhspan(-.9,.9,color=GREEN,alpha=.12);axs[1,1].legend(fontsize=7)
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=7)
        para(fig,.231,f"返回比T=A×0.5，环路UGB={v['loop_ugb_hz']/1e6:.6f}MHz，PM={v['phase_margin_deg']:.6f}°；只有一次下降零dB交越，之后未回穿。环路等效每端负载1.5pF，实际建立台使用完整Cs/Cf/CL与1GH直流偏置电感。",9.0)
        para(fig,.107,'0.9V目标和0.9mV误差带保持不变；取各原时间窗的最后容差交越，且末端必须留在带内。输入边沿通过反馈电容产生瞬时反向馈通；源文件的导数峰值不应解释为纯放大器固有压摆率。',9.0)
        save(pdf,fig)

        fig=frame('开环压缩摆幅与全带输出噪声',5,'摆幅按开环DC局部增益下降3dB定义；噪声积分上限固定10GHz。')
        axs=fig.subplots(2,1);fig.subplots_adjust(left=.13,right=.93,bottom=.28,top=.84,hspace=.43)
        g=r['range_derivative'];axs[0].plot(np.array(g['input_V'])*1e6,g['output_V'],'.-',color=BLUE,label='Differential output')
        ax2=axs[0].twinx();ax2.plot(np.array(g['input_V'])*1e6,g['gain_db'],color=GREEN,label='Local gain');ax2.axhline(v['gain_3db_db'],color=GREEN,ls='--');ax2.set_ylabel('Local DC gain (dB)',fontsize=8);ax2.tick_params(labelsize=7)
        axs[0].set(xlabel='Input differential (uV)',ylabel='Output differential (V)')
        n=d['noise'];axs[1].loglog(n['freq'],abs(n['out'])*1e9,color=BLUE);axs[1].set(xlabel='Frequency (Hz)',ylabel='Output noise (nV/sqrt(Hz))')
        from matplotlib.ticker import FuncFormatter
        axs[1].yaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:g}'))
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.231,f"原81点：输入-20至20uV、步长0.5uV。两压缩交点输出{v['output_range_min_v']:.6f}/{v['output_range_max_v']:.6f}V，跨度{v['output_range_v']:.6f}V。0.25uV的161点诊断为{c['diagnostic_range_V']:.6f}V，相差{c['absolute_difference_V']*1e3:.3f}mV；原81点继续作为验收值。",9.0)
        para(fig,.097,f"差分输出噪声{v['output_noise_vrms']*1e6:.6f}uVrms；对输出谱幅度平方做线性频率梯形积分。另用区间幂律PSD积分交叉核对，相对差{r['noise_quadrature']['relative_difference']*100:.5f}%。未以较低输入折算噪声或有限信号带宽替代。",9.0)
        save(pdf,fig)

        fig=frame('共模扰动、参考轨迹与恢复',6,'每个输出同时吸收50uA，20ns平台、100ps边沿；与未扰动相同实例比较。')
        cm=d['cmfb'];t=cm['time'];dist=(cm['voutp']+cm['voutn'])/2;ref=(cm['routp']+cm['routn'])/2
        axs=fig.subplots(2,1);fig.subplots_adjust(left=.14,right=.94,bottom=.36,top=.84,hspace=.35)
        axs[0].plot(t*1e9,dist,color=BLUE,label='Disturbed');axs[0].plot(t*1e9,ref,color=GRAY,label='Undisturbed reference');axs[0].set(ylabel='Output common mode (V)');axs[0].legend(fontsize=8)
        axs[1].plot(t*1e9,(dist-ref)*1e3,color=BLUE);axs[1].set(xlabel='Time (ns)',ylabel='Disturbed - reference (mV)')
        for ax in axs:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        rows=[[key,f'{v[key]*1e3:.9f}'] for key in ['cmfb_static_error_v','cmfb_max_deviation_v','cmfb_residual_20ns_v','cmfb_residual_100ns_v']]
        table(fig,[.07,.19,.86,.13],['测量量','实测/mV'],rows,[.66,.34],8.3)
        para(fig,.147,'峰值窗口20–45ns，残差时刻60.2/140.2ns。扰动结束于40.2ns；没有按20ns理想方波错误提前释放时刻。两只零伏源仅测量外部扰动电流，不改变源电流和DUT。',8.9)
        para(fig,.086,'OP的25mV共模要求针对零差分输入；差分阶跃中最大共模误差45.590mV另作表征，并未满足25mV。',8.9)
        save(pdf,fig)

        fig=frame('功耗、匹配抑制表征与验收边界',7,'完整保留原失配要求的分母与激励语义，但本次不执行失配矩阵。')
        para(fig,.85,f"总DC功耗{v['power_w']*1e3:.9f}mW，由环路台唯一VDD供电源计算；包含外部50uA参考、内部偏置、输入/输出级和连续CMFB。CMFB扰动台含两个DUT，仅用于差分参考恢复测试，其总电流没有拿来代替单DUT功耗。",9.2)
        rows=[]
        for name,q in r['matched_rejection'].items():rows.append([name,f"{q['feedthrough_abs']:.6g}",'对称抵消，非失配结论'])
        table(fig,[.07,.581,.86,.135],['10Hz激励','到差分输出的幅度/V/V','解释'],rows,[.28,.30,.42],8.2)
        para(fig,.527,'抑制比分子按原题使用标称闭环A/(1+0.5A)，约6.02056dB，不误用开环112dB增益。匹配台用±0.25输出反馈到两输入保持DC闭环；共模输入、正电源和负电源三种外部激励分别运行。',9.2)
        para(fig,.367,'负电源激励中VSS对绝对地AC=+1，VDD相对VSS的AC=-1，因此绝对VDD保持不动。对称模型的差分泄漏受浮点抵消限制；即使换算出极大的dB，也不能据此宣称20个失配样本的60/70dB要求通过。',9.2)
        para(fig,.207,'原验收器nominal_functional通过，独立limit_check使用明确expected=1检查当前nominal的功率、噪声和共模恢复。原30点/20样本集合没有伪造；原3dB摆幅判据保留失败，而10%迁移判据通过。',9.2)
        para(fig,.077,'不包含另外29个PVT点、两种非nominal共模扰动、20次局部失配、版图、寄生、电容失配或连续时间反馈网络之外的开关非理想。',9.0)
        save(pdf,fig)

        fig=frame('独立复核、图纸与可重复证据',8,'40个器件实例、140个端子，全部模拟器件、无源值和体端可追溯。')
        para(fig,.85,'25个独立测量核对涵盖环路交越、功耗、共模、双向静动态误差、最后容差交越、3dB压缩摆幅、10GHz噪声积分和共模恢复。原始波形、模型、LUT、DUT及每组输入快照分别保存哈希。',9.2)
        para(fig,.682,'修正了两个测试台接口差异：Spectre不允许AC起止频率相同，因此保留10Hz并额外求一个不计分的11Hz点；电流源p端保存不受支持，改用串联零伏测量源。初版真实报错保留，最终六组及加密扫点全部0错误、0警告。',9.2)
        para(fig,.5,'复现（工程根目录，既有Bridge Python）：\npython scripts/case33_sampling.py\npython scripts/confirm33.py\npython scripts/schematic33.py\npython scripts/audit33.py\npython scripts/review33.py\n更新PDF后，必须重新逐页目检与核对完整总图。',8.8)
        para(fig,.28,'证据：latest_results.json / numerical_confirmation.json / verification_audit.json\n精确网表：circuit.scs；所有30只MOS实际OP在结果中。\n完整四页晶体管图及层次端子表：schematic/\n运行、模型及输入快照：各runs/33目录；生成脚本快照：implementation/',8.5)
        para(fig,.126,'最终电路SHA-256：\n'+r['circuit_sha256'],7.8)
        para(fig,.062,'原资料、PDK和既有Bridge/Spectre环境保持原样；只在本次授权的SMIC18复现分区更新知识库。',8.5)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(case/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1]);write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=4,schematic_sheets_sha256=sha(case/'schematic/sheets.pdf'),render_review_pending=True));print(out)

if __name__=='__main__':make()
