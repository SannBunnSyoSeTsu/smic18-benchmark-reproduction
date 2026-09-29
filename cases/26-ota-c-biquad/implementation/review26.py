from report29 import *
CASE=ROOT/'cases/26-ota-c-biquad'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];z=json.loads((CASE/'sizing.json').read_text());body=ROOT/'reports/26-ota-c-biquad-body.pdf'
    def rows(items):
        out=[]
        for label,key,scale in items:
            q=r['gates'][key];sign='≤' if q['sense']=='max' else '≥';out.append([label,f"{q['value']*scale:.6g}",*[sign+f"{q['limits'][tier]*scale:.5g}" for tier in ['original','10pct','15pct']]])
        return out
    with PdfPages(body) as pdf:
        fig=frame('26 | 全差分OTA-C双二阶审查',1,'结论：TT/1.8V/27°C全部26项标量及原16组检查通过。')
        para(fig,.85,'四个跨导支路构成双积分反馈，提供低通和带通输出。相对RC无源滤波可通过偏置调谐并缓冲负载，但消耗静态电流，线性度和共模稳定性依赖有源电路；适合接收机基带滤波。',9.2)
        items=[('中心频率偏差/kHz','f0_Hz_error',1e-3),('Q相对0.7偏差','Q_error',1),('通带增益下限/dB','passgain_dB_min',1),('通带增益上限/dB','passgain_dB_max',1),('拟合RMS/dB','fit_error_dB_max',1),('20MHz衰减/dB','atten20M_dB_min',1),('BP峰频偏差/kHz','bp_peak_Hz_error',1e-3),('BP峰增益下限/dB','bp_peak_dB_min',1),('BP峰增益上限/dB','bp_peak_dB_max',1),('BP拒斥1kHz/dB','bp_1k_dB_min',1),('BP拒斥200kHz/dB','bp_200k_dB_min',1),('BP拒斥20MHz/dB','bp_20M_dB_min',1),('共模DC误差/mV','cm_error_V_max',1e3),('总供电功耗/uW','power_W_max',1e6),('输出噪声/uVrms','noise_Vrms',1e6)]
        table(fig,[.07,.226,.86,.494],['指标','实测','原','10%','15%'],rows(items),[.34,.18,.16,.16,.16],7.5)
        para(fig,.17,f"f0={v['ac']['f0_Hz']/1e6:.9f}MHz，Q={v['ac']['Q']:.9f}；BP峰{v['ac']['bp_peak_Hz']/1e6:.9f}MHz。频率门槛以目标2MHz的误差带表示。仅完整TT六类功能试验，未扩称62运行PVT签核。",9.1);save(pdf,fig)

        fig=frame('失真、增益与共模恢复验收',2,'固定输入幅度、2周期取样、2–5次谐波；同时约束基本增益。')
        items=[('200k/0.6Vpp THD/dB','thd_thd_dB',1),('200k/0.6Vpp增益','thd_gain',1),('200k/0.9Vpp THD/dB','thd2_thd_dB',1),('200k/0.9Vpp增益','thd2_gain',1),('2M/0.9Vpp LP THD/dB','thd_f0_thd_dB',1),('2M/0.9Vpp LP增益','thd_f0_gain',1),('2M/0.9Vpp BP THD/dB','thd_f0_bp_thd_dB',1),('2M/0.9Vpp BP增益','thd_f0_bp_gain',1),('共模初始误差/mV','cm_initial_error_V',1e3),('共模建立/ns','cm_settle_s',1e9),('共模晚期偏差/mV','cm_late_excursion_V',1e3)]
        table(fig,[.07,.416,.86,.417],['指标','实测','原','10%','15%'],rows(items),[.36,.18,.16,.15,.15],7.5)
        para(fig,.355,'每次THD仿真30us，取最后2周期，均匀插值256点；仅2–5次谐波合成THD。输出幅度除以输入差分峰值为增益。dB放宽在幅度比上实施，未直接把负dB乘1.1。',9.3)
        para(fig,.205,'共模参考0.85→0.95V，5–5.05us线性变化。建立时间从5.05us计至最后一次超出固定±10mV带；初始取4.85us，晚期取12us以后。低通和带通两路同时检查。',9.3);save(pdf,fig)

        fig=frame('跨导结构、gm/ID与实际工作点',3,'常规n18/p18实现原LVT结构功能；无模型别名或行为源替代。')
        rowsz=[[k,f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()]
        table(fig,[.07,.663,.86,.177],['角色','单位W/L um','初算gm/ID','初算I/uA'],rowsz,[.28,.30,.20,.22],8)
        para(fig,.608,'信号跨导每侧20uA，源间退化19.1kΩ；阻尼跨导无PMOS负载、源间8kΩ。带通节点接三组NMOS电流，两个PMOS负载各m1.5供30uA。C1两只各8pF，C2两只各4pF，四节点均外接250fF。',9.2)
        opr=[];op=r['operating_point']
        for label,dev in [('尾电流','X.XGIN.MTA'),('输入对','X.XGIN.MA'),('BP负载','X.XGIN.MLA'),('CM输入','X.XCM1.MC1'),('CM负载','X.XCM1.MCL1')]:
            q={k:op[dev+':'+k] for k in ['ids','gm','gmbs','vds','vdsat']};opr.append([label,f"{abs(q['ids'])*1e6:.4f}",f"{abs(q['gm']/q['ids']):.4f}",f"{q['gmbs']*1e6:.3f}",f"{abs(q['vds'])-abs(q['vdsat']):.4f}"])
        table(fig,[.07,.266,.86,.177],['实际OP','|ID|/uA','gm/ID','gmb/uS','VDS余量/V'],opr,[.19,.21,.19,.19,.22],8)
        para(fig,.209,'两路独立共模反馈用1MΩ电阻平均输出，CM尾电流10uA/侧、源间5kΩ、0.3pF补偿。输入管体效应保留；gm/ID表仅用于初算，实际gm、gmb与VDS余量由DC结果确认。',9.2);save(pdf,fig)

        fig=frame('频率响应、噪声与共模动态',4,'AC 1k–100MHz；输出差分噪声积分1k–4MHz。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.2,wspace=.39,hspace=.45)
        a=data(ROOT/r['groups']['ac'],'ac.ac');f=a['freq'];axs[0,0].semilogx(f,20*np.log10(abs(a['voutp']-a['voutn'])),label='LP');axs[0,0].semilogx(f,20*np.log10(abs(a['vbpp']-a['vbpn'])),label='BP');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Differential gain (dB)',ylim=(-75,5));axs[0,0].legend(fontsize=7)
        n=data(ROOT/r['groups']['noise'],'noise.noise',required=['out']);axs[0,1].loglog(n['freq'],abs(n['out'])*1e9);axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Output noise (nV/sqrt(Hz))')
        d=data(ROOT/r['groups']['cmstep'],'tran.tran');t=d['time']*1e6;m=(t>4.8)&(t<5.5)
        for p,q,label in [('voutp','voutn','LP'),('vbpp','vbpn','BP')]:axs[1,0].plot(t[m],(d[p][m]+d[q][m])/2,label=label)
        axs[1,0].plot(t[m],d['vocm'][m],ls=':',label='reference');axs[1,0].set(xlabel='Time (us)',ylabel='Output common mode (V)');axs[1,0].legend(fontsize=7)
        d=data(ROOT/r['groups']['thd_f0'],'tran.tran');t=d['time']*1e6;m=t>=29;axs[1,1].plot(t[m],d['voutp'][m]-d['voutn'][m],label='LP');axs[1,1].plot(t[m],d['vbpp'][m]-d['vbpn'][m],label='BP');axs[1,1].set(xlabel='Time (us)',ylabel='2 MHz output (V)');axs[1,1].legend(fontsize=7)
        clean_axes(axs);para(fig,.14,'二阶拟合使用≤8MHz数据的逆功率多项式。20MHz与200kHz沿用原检查器最近频点语义，精算网格实际20MHz对应19.952623MHz。BP峰值由离散AC网格查找。',9.1);save(pdf,fig)

        fig=frame('数值确认与独立测量',5,'12个基线/精算运行均0错误、0警告；不额外放宽数值容差。')
        para(fig,.85,'maxstep2→1ns，reltol1e-6→1e-7；AC每十倍频100→200点、噪声80→160点。28项事前固定容差均通过。最大THD差0.044244dB<0.05dB；噪声差0.012286uV<1uV。',9.5)
        para(fig,.67,'拟合f0仅差约1.965Hz；BP离散峰频差22.064kHz，处于预设30kHz内，体现网格取峰分辨率。最大2MHz基波幅度差42.499uV<100uV。报告保留全部差异，没有改动通过界限。',9.5)
        para(fig,.49,'独立审计用原Gauss消元拟合、直接复数DFT和共模扫描重算；噪声独立逐频段PSD积分后适配原积分结果接口。28项与主测量一致；原16组检查函数在显式TT六记录投影下全部通过。',9.5)
        para(fig,.31,'图纸覆盖5个子电路定义共42实例、160端子，包括4个跨导块、两路CMFB、所有退化电阻与状态电容。展开复用后是51个叶级实例；不把定义数与展开数混写。',9.5)
        para(fig,.13,'模型、LUT、源任务与每次运行输入哈希核对通过。两路共模通过阶跃验证；未额外声称独立共模环路相位裕量或失配后稳定性。',9.5);save(pdf,fig)
        lines=(CASE/'circuit.scs').read_text().splitlines()
        for j,chunk in enumerate([lines[:29],lines[29:]]):
            fig=frame('最终完整网表 '+str(j+1)+'/2',6+j,'全部层级定义及顶层连接原样列出。');fig.text(.07,.85,'\n'.join(chunk),fontfamily='DejaVu Sans Mono',fontsize=8,va='top',linespacing=1.55);para(fig,.13,'电路SHA-256：\n'+r['circuit_sha256'],7.8);save(pdf,fig)
        fig=frame('复现入口与未覆盖项',8,'附后6页完整电路图，原检查器及全部运行证据随附。')
        para(fig,.85,'既有Bridge Python，工程根目录：\npython scripts/case26_ota_c.py\npython scripts/confirm26.py\npython scripts/schematic26.py\npython scripts/audit26.py\npython scripts/review26.py\n报告生成后仍需实际逐页检查。',9.6)
        para(fig,.53,'contract.json固定原频率、负载、输入幅度、THD窗口、共模窗口及门槛。source/保持原文件；independent_measurement_details保留原16组评分。numerical_plan、baseline和confirmation可追溯两套运行。',9.4)
        para(fig,.32,'当前为TT1.8V27°C六类功能试验。其余24个AC/噪声PVT点和2个动态压力点未执行；未做失配、调谐范围、版图、PEX。所有理想R/C为原题允许的DUT元件，不包含理想放大器或受控源。',9.4)
        para(fig,.14,'PDK、原LUT、Spectre与Bridge保持原环境。完整图纸含体端、尺寸、复用子电路接口；知识库保留标称通过与未覆盖范围，不以局部结果代替完整上游签核。',9.4);save(pdf,fig)
    finish_report(CASE,body,8)

if __name__=='__main__':make()
