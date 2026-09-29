from report29 import *
CASE=ROOT/'cases/38-capless-ldo'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());points=r['values']['line_points'];st=r['values']['startup'];z=json.loads((CASE/'sizing.json').read_text());c=json.loads((CASE/'numerical_confirmation.json').read_text());assert c['passed']
    body=ROOT/'reports/38-capless-ldo-body.pdf'
    with PdfPages(body) as pdf:
        fig=frame('38 | 无外部电容LDO审查',1,'结论：TT27°C两档供电的全部原指标通过，无需性能放宽。')
        para(fig,.85,'1.5V与1.8V供电；完整0–20mA DC，20mA PSR，0.5→20→0.5mA双向动态。TT1.8V另做100us斜坡启动。所有输出电容在DUT内部，合计977pF，原1nF预算不放宽。',9)
        labels=[('DC误差','dc_error_V',1e3,'mV'),('空载IQ','iq_A',1e6,'uA'),('PSR 1kHz','psr1k_dB',1,'dB'),('PSR 100kHz','psr100k_dB',1,'dB'),('PSR 1MHz','psr1M_dB',1,'dB'),('阶跃最坏偏差','step_excursion_V',1e3,'mV'),('阶跃尾窗偏差','step_recovery_V',1e3,'mV')]
        rows=[]
        for label,key,scale,unit in labels:
            a=r['gates']['1.5_'+key];b=r['gates']['1.8_'+key];sign='≥' if a['sense']=='min' else '≤'
            rows.append([label,*[f'{q[key]*scale:.6g}' for q in points],*[sign+(f"{a['limits'][t]*scale:.4g}/{b['limits'][t]*scale:.4g}" if a['limits'][t]!=b['limits'][t] else f"{a['limits'][t]*scale:.4g}") for t in ['original','10pct','15pct']],unit])
        table(fig,[.07,.416,.86,.306],['指标','1.5V','1.8V','原','10%','15%','单位'],rows,[.24,.14,.14,.135,.135,.135,.075],7.2)
        para(fig,.353,f"启动峰值{st['peak_V']:.9f}V：原上限1.05V；按相对1V的过冲量放宽时10%/15%上限为1.055/1.0575V。200–400us最坏误差{st['tail_error_V']*1e3:.6f}mV，原20mV，放宽22/23mV。本版原值全部通过。",9)
        para(fig,.196,'仅TT27°C，保留两档供电这一功能维度；另外28个DC/阶跃点、8个PSR点及3个启动角落未执行。原题的理想内部电容不含实际密度、容差、压变和寄生，不能据此宣称真实面积或版图性能。',9)
        save(pdf,fig)

        fig=frame('gm/ID初算与最终实测偏置',2,'自偏置电阻调整后，实际电流密度与最初5uA查表点不同。')
        rows=[[k,f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()]
        table(fig,[.07,.657,.86,.18],['角色','单位W/L um','初算gm/ID','初算ID uA'],rows,[.26,.28,.23,.23],8)
        rows=[]
        for n,q in r['operating_point']['1.8'].items():rows.append([n,f"{q['ids']*1e6:.6g}",f"{abs(q['gm']/q['ids']):.5g}",f"{q['vgs']:.4f}",f"{q['vds']:.4f}",f"{abs(q['vds'])-abs(q['vdsat']):.4f}"])
        table(fig,[.07,.207,.86,.391],['器件/1.8V20mA','ID/uA','实际gm/ID','VGS/V','VDS/V','电压余量/V'],rows,[.23,.17,.16,.14,.14,.16],7.2)
        para(fig,.151,'实际尾电流10.9999uA、镜输出约19.7uA，较初算5uA尾电流增大；输入gm/ID约14.23，未将初算18写成最终工作点。功率管15.66/0.36um×400，总宽6264um，实测gm/ID10.1267。',8.9)
        para(fig,.078,'输入PMOS体端接tail，需要隔离井实现；其他PMOS体端接vin，NMOS接VSS。固定1.8V模型用于给定供电范围，本次未生成版图。',8.6)
        save(pdf,fig)

        fig=frame('完整负载扫描、供电抑制与动态',3,'无外部电容；所有动态窗口对固定1.0V目标评分。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.21,wspace=.38,hspace=.46)
        for q,color in zip(points,[BLUE,GREEN]):
            tag=str(q['supply_V']);d=data(ROOT/r['groups']['dc'+tag],'loads.dc');a=data(ROOT/r['groups']['psr'+tag],'ac.ac');t=data(ROOT/r['groups']['step'+tag],'tran.tran')
            axs[0,0].plot(d['iload']*1e3,(d['vout']-1)*1e3,color=color,label=tag+'V')
            axs[0,1].semilogx(a['freq'],-20*np.log10(abs(a['vout'])),color=color,label=tag+'V')
            axs[1,0].plot(t['time']*1e6,t['vout'],color=color,label=tag+'V')
            m=(t['time']>=60e-6)&(t['time']<=65e-6);axs[1,1].plot((t['time'][m]-60e-6)*1e6,t['vout'][m],color=color,label=tag+'V')
        axs[0,0].set(xlabel='Load current (mA)',ylabel='DC error from 1V (mV)');axs[0,0].legend(fontsize=7)
        axs[0,1].set(xlabel='Frequency (Hz)',ylabel='PSR (dB)');axs[0,1].legend(fontsize=7)
        axs[1,0].set(xlabel='Time (us)',ylabel='Load step output (V)');axs[1,0].axhline(.97,color=GRAY,ls=':');axs[1,0].axhline(1.03,color=GRAY,ls=':')
        axs[1,1].set(xlabel='Time after falling load start (us)',ylabel='Output (V)');clean_axes(axs)
        para(fig,.153,'0.5mA→20mA在20–21us完成，20mA→0.5mA在60–61us完成。暂态窗20–41us/60–81us允许±150mV；尾窗41–60us/81–100us要求±30mV。最坏暂态72.301mV、尾窗2.627mV。',9)
        para(fig,.067,'最终DC每0.1mA一点共201点，包含原0.2mA网格；PSR100Hz–10MHz每十倍频160点，包含原20点/dec网格。',8.7)
        save(pdf,fig)

        fig=frame('从零电源启动与有限过冲余量',4,'供电100us斜坡，负载2kΩ，不用关断时仍吸电流的理想电流负载。')
        d=data(ROOT/r['groups']['start'],'tran.tran');t=d['time'];v=d['vout'];peak=int(np.argmax(v));axs=fig.subplots(2,1);fig.subplots_adjust(left=.13,right=.94,top=.85,bottom=.30,hspace=.43)
        axs[0].plot(t*1e6,d['vin'],label='VIN',color=GRAY);axs[0].plot(t*1e6,v,label='VOUT',color=BLUE);axs[0].set(xlabel='Time (us)',ylabel='Voltage (V)');axs[0].legend(fontsize=8)
        m=(t>=t[peak]-5e-6)&(t<=t[peak]+5e-6);axs[1].plot(t[m]*1e6,v[m],color=BLUE);axs[1].axhline(1.05,color=GRAY,ls='--',label='Original peak bound');axs[1].set(xlabel='Time near startup peak (us)',ylabel='VOUT (V)');axs[1].legend(fontsize=8);clean_axes(axs)
        para(fig,.24,f"全0–400us最大VOUT={st['peak_V']:.9f}V，距1.05V原门槛仅{(1.05-st['peak_V'])*1e3:.6f}mV。200–400us范围{st['tail_min_V']:.9f}–{st['tail_max_V']:.9f}V；没有改用最终值作为1V误差中心。",9)
        para(fig,.105,'startup原最大步长400ns；本次基线200ns，最终100ns且收紧reltol，峰值只变1.056uV。该余量仅对已验证TT条件成立，未宣称其他三个启动角落也通过。VREF按原台始终0.4V。',9)
        save(pdf,fig)

        fig=frame('迭代与数值确认',5,'保留失败候选；总电容始终在1nF预算内。')
        hist=json.loads((CASE/'iteration_history.json').read_text());rows=[]
        for idx,h in enumerate(hist):
            if idx>=5:break
            p=h['parameters'];v=h['values'];rows.append([str(idx+1),f"{p['rs']/1000:g}",f"{p['cf']:g}/{p['cout']:g}/{p['esrc']:g}",f"{v['line_points'][0]['psr1M_dB']:.3f}",f"{v['startup']['peak_V']:.6f}",h['status'].replace('complete_','')])
        table(fig,[.07,.624,.86,.206],['候选','Rs/kΩ','Cf/C2/C1 pF','1.5V PSR1M','启动峰值/V','等级'],rows,[.09,.11,.26,.20,.19,.15],7.5)
        para(fig,.57,'提高直接输出电容占比并增加Cf前馈，改善高频PSR和负载扰动；Rs从20kΩ降至12.3kΩ，提高真实偏置与控制速度，降低启动过冲。代价是空载IQ从57.37uA升至93.87uA，原100uA余量约6.13uA。',9)
        rows=[]
        groups=[('DC输出误差','dc_error_V'),('空载电流','iq_A'),('PSR任一点','dB'),('暂态各窗口电压','_V'),('启动峰值','startup_peak_V')]
        for label,key in groups:
            ss=[q for q in c['metrics'] if (key in q['metric'])];rows.append([label,f"{max(q['absolute_difference'] for q in ss):.6g}",f"{max(q['maximum_difference'] for q in ss):.6g}"])
        table(fig,[.07,.282,.86,.195],['比较（SI/dB）','最大绝对差','预先上限'],rows,[.46,.27,.27],8)
        para(fig,.225,'38项数值对照通过：步长20→10ns、启动200→100ns，reltol1e-6→1e-7；DC步进0.2→0.1mA，AC40→160点/dec。最大受检电压差8.834uV<200uV；PSR差0.000492dB<0.01dB。',9)
        para(fig,.09,'40项独立测量核对与原8组检查函数通过，明确投影至TT27两供电及一启动。14个基线/最终运行0错误/0警告；静态预算独立累加4个电容得977pF。',9)
        save(pdf,fig)

        fig=frame('最终精确电路',6,'原生n18/p18与正值理想R/C；无内部源、模型、理想开关或外部CLOAD。')
        fig.text(.07,.853,(CASE/'circuit.scs').read_text(),fontfamily='DejaVu Sans Mono',fontsize=7.1,va='top',linespacing=1.42)
        para(fig,.266,'内部电容：Miller CM3pF、前馈CF10pF、阻尼支路C1=694pF/RESR150Ω、直接输出C2=270pF，总977pF。30k/20k分压比固定0.4，VREF仍是原0.4V，没有通过调整目标掩盖误差。',9)
        para(fig,.139,'电路SHA-256：\n'+r['circuit_sha256'],7.8)
        save(pdf,fig)

        fig=frame('测量语义、复现入口与未覆盖项',7,'24实例76端子，附后三页展开全部电路；环境和原资料不修改。')
        para(fig,.85,'IQ为无外部负载时|I(VIN)|，包括内部20uA左右的分压电流。原题明确不计理想VREF供电；本实现VREF只连接输入MOS栅极，DC测得0A。动态输出没有外部电容，补偿和输出储能均在内部预算内。',9.4)
        para(fig,.676,'原任务以外部输出窗口评分，不给拓扑独立的环路断点，因此PM/UGB不是验收项。本次用完整双向负载阶跃与真实启动检验规定动态；没有给未测的内部环路裕量编造数值。理想R/C的容差、密度与版图耦合仍未模拟。',9.4)
        para(fig,.50,'复现（工程根目录，既有Bridge Python）：\npython scripts/case38_capless_ldo.py\npython scripts/confirm38.py\npython scripts/schematic38.py\npython scripts/audit38.py\npython scripts/review38.py\n重新生成报告和图纸后须再次实际逐页查看。',9)
        para(fig,.25,'source/及source_provenance.json冻结原合同、网表及检查器。iteration_history.json保留五个候选；numerical_plan/baseline/confirmation记录固定数值容限；verification_audit.json和independent_measurement_details.json给出独立窗口、原函数与电容预算。',9)
        para(fig,.106,'原30点DC/阶跃中其余28点、10点PSR中其余8点、4点启动中其余3点未执行。失配、噪声、版图、PEX与实际电容面积/工艺容差未验证。',9)
        save(pdf,fig)
    finish_report(CASE,body,7)

if __name__=='__main__':make()
