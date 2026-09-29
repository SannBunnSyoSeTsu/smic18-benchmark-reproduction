from report29 import *
CASE=ROOT/'cases/30-gilbert-mixer'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];z=json.loads((CASE/'sizing.json').read_text());sp=json.loads((CASE/'spectral_records.json').read_text());body=ROOT/'reports/30-gilbert-mixer-body.pdf'
    with PdfPages(body) as pdf:
        fig=frame('30 | 2.4GHz Gilbert混频器审查',1,'结论：六组RF及四组线性度TT运行全部原门槛通过。')
        para(fig,.85,'双平衡跨导与LO换向四管将RF降至200MHz中频。相对单平衡结构可抑制LO/RF直通，并提供转换增益；代价是多层堆叠余量、偏置功耗及双音失真。适合低中频接收链。',9.2)
        rows=[]
        for label,metric,scale in [('转换增益/dB','conversion_gain_db',1),('LO→IF/dB','lo_if_isolation_db',1),('RF→IF/dB','rf_if_feedthrough_db',1),('LO→RF/dB','lo_rf_isolation_db',1),('输出失衡/uV','output_dc_balance_v',1e6),('输出共模/V','output_common_mode_v',1),('到VDD余量/V','output_headroom_to_vdd_v',1),('总供电/mW','power_w',1e3),('带外杂散/dBc','spur_dbc',1)]:
            qs=[q for k,q in r['gates'].items() if k.startswith('rf') and k.endswith('_'+metric)];q=(min if qs[0]['sense']=='min' else max)(qs,key=lambda q:q['value']);sign='≥' if q['sense']=='min' else '≤';rows.append([label,f"{q['value']*scale:.6g}",*[sign+f"{q['limits'][t]*scale:.5g}" for t in ['original','10pct','15pct']]])
        q=r['gates']['IIP3_mW'];rows.append(['IIP3/dBm',f"{v['linearity']['IIP3_dBm']:.6g}",*['≥'+f"{10*np.log10(q['limits'][t]):.5g}" for t in ['original','10pct','15pct']]])
        for label,key in [('双音增益差/dB','tone_gain_difference_dB_max'),('压缩/dB','compression_dB_max')]:
            q=r['gates'][key];rows.append([label,f"{q['value']:.6g}",*['≤'+f"{q['limits'][t]:.5g}" for t in ['original','10pct','15pct']]])
        table(fig,[.07,.298,.86,.424],['指标最差值','实测','原','10%','15%'],rows,[.28,.21,.17,.17,.17],7.6)
        para(fig,.24,'固定斜率约束：基波0.8–1.2，实测0.976558；IM3为1.8–4，实测3.254322。隔离只在三组2%幅度、2°相位不平衡点评分。极深相消值为仿真结果，数值可置信范围见第6页。',9.1)
        para(fig,.11,'TT/1.8V/27°C，RF=2.3/2.4/2.5GHz，LO=RF−0.2GHz。50Ω/腿源阻抗、200fF/腿外部负载；未执行其他PVT及原10个失配种子。',9.1);save(pdf,fig)

        fig=frame('堆叠、gm/ID尺寸与实际余量',2,'9个常规n18、3个理想电阻、3个理想电容；15实例48端子。')
        rows=[[k,f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()]
        table(fig,[.07,.716,.86,.124],['角色','单位W/L um','gm/ID初算','单位I/uA'],rows,[.23,.31,.23,.23],8.2)
        para(fig,.66,'两尾电流镜m6.5，各目标325uA；RF输入m6.5，总宽19.63um/只，源间650Ω退化。LO四管各m6.5，总宽74.88um/只；3.3kΩ负载，DUT输出75fF/腿，偏置去耦1pF。外部50uA参考从VDD取得，已包含供电功耗。',9.2)
        rows=[];op=r['operating_point']
        for dev in ['MREF','MTAILP','MRFP','MQ1']:
            q={k:op['X.'+dev+':'+k] for k in ['ids','gm','vds','vdsat']};rows.append([dev,f"{q['ids']*1e6:.4f}",f"{q['gm']/q['ids']:.4f}",f"{q['vds']:.6f}",f"{q['vdsat']:.6f}"])
        table(fig,[.07,.357,.86,.151],['DC工作点','ID/uA','实际gm/ID','VDS/V','VDSAT/V'],rows,[.24,.20,.20,.18,.18],8)
        para(fig,.299,'DC时RF管VDS=0.123543V，略低于VDSAT=0.128448V，实际gm/ID约9.98。不能宣称所有管子处于深饱和。这里列出LO静止时DC诊断；转换和线性度验收来自实际大信号LO瞬态。',9.2)
        para(fig,.15,'使用真实常规n18，不把原LVT模型简单改名。初算用较强反型RF管换取余量，LO以较高gm/ID和较大尺寸换取换向能力；体效应、有限输出电阻及源负载效应由工艺模型保留。',9.2);save(pdf,fig)

        fig=frame('RF扫频、不平衡与实际输出',3,'全部六点保留原功能激励；没有只挑最好频率。')
        rows=[[f"{q['RF_Hz']/1e9:g}",'2%/2°' if q['imbalance'] else '平衡',f"{q['conversion_gain_db']:.6f}",f"{q['rf_if_feedthrough_db']:.6f}",f"{q['spur_dbc']:.6f}"] for q in v['rf']]
        table(fig,[.07,.602,.86,.23],['RF/GHz','条件','转换增益/dB','RF→IF/dB','杂散/dBc'],rows,[.15,.18,.23,.23,.21],7.9)
        axs=fig.subplots(1,2);fig.subplots_adjust(left=.12,right=.94,top=.53,bottom=.21,wspace=.36)
        d=data(ROOT/r['groups']['rf2.4_imb'],'tran.tran');t=d['time']*1e9;m=t>=5;axs[0].plot(t[m],d['ifoutp'][m]-d['ifoutn'][m]);axs[0].set(xlabel='Time (ns)',ylabel='IF differential output (V)')
        s=sp['rf2.4_imb'];f=np.array(s['frequency_Hz']);a=np.array(s['amplitudes_V']['out']);ref=a[2];axs[1].stem(f[:31]/1e9,20*np.log10(np.maximum(a[:31]/ref,1e-8)),bottom=-120,basefmt=' ');axs[1].set(xlabel='Frequency (GHz)',ylabel='Output spectrum (dBc)',ylim=(-120,5));clean_axes(axs)
        para(fig,.15,'RF窗口5–15ns，2048点矩形相干DFT，无补零；100MHz整数谱线。输入RF每腿20mV峰值、LO每腿350mV峰值；增益和隔离分母使用DUT端真实差分幅度。',9.2);save(pdf,fig)

        fig=frame('双音外推与大信号压缩',4,'双音2.4/2.45GHz，LO2.2GHz；窗口10–30ns，频谱间距50MHz。')
        rows=[]
        for key,label in [('two_low','每腿每音10mV'),('two_high','每腿每音20mV')]:
            q=v['linearity_raw'][key];rows.append([label,f"{q['fund1']*1e3:.6f}",f"{q['fund2']*1e3:.6f}",f"{q['im3lo']*1e6:.6f}",f"{q['im3hi']*1e6:.6f}"])
        table(fig,[.07,.731,.86,.105],['输入条件','200M/mV','250M/mV','150M/uV','300M/uV'],rows,[.28,.18,.18,.18,.18],7.8)
        para(fig,.675,'IIP3按两音基波平均、较大IM3和DUT端输入平均幅度计算，低/高两次估计取最小，再按100Ω差分端口换算dBm。结果−2.435600dBm≥−4dBm，双音增益差1.359512dB≤1.5dB。',9.2)
        ax=fig.add_axes([.12,.282,.81,.284])
        for key,label in [('two_low','10mV/tone/leg'),('two_high','20mV/tone/leg')]:
            s=sp[key];ax.plot(np.array(s['frequency_Hz'])[1:9]/1e6,20*np.log10(np.maximum(np.array(s['amplitudes_V']['out'])[1:9],1e-10)),'.-',label=label)
        ax.set(xlabel='Frequency (MHz)',ylabel='Differential output (dBV)');ax.legend(fontsize=8);clean_axes(ax)
        para(fig,.19,'单音每腿20→80mV：转换增益5.506084→4.486977dB，压缩1.019106dB≤2dB。IIP3为这两个有限输入幅度的外推，不是无限小信号导数；斜率与两音差同时检查，避免偶然谱线抵消。',9.2);save(pdf,fig)

        fig=frame('最终完整晶体管网表',5,'理想R/C为原题允许元件；DUT内部无受控源或行为放大器。')
        fig.text(.07,.85,(CASE/'circuit.scs').read_text(),fontfamily='DejaVu Sans Mono',fontsize=8,va='top',linespacing=1.55)
        para(fig,.36,'电路SHA-256：\n'+r['circuit_sha256'],8)
        para(fig,.22,'供电功耗包含50uA参考及混频核心；测试台RF、LO理想驱动电源功耗未计入原供电指标。DUT输出电容75fF另叠加外部200fF，未包含布局或封装寄生。',9.3);save(pdf,fig)

        fig=frame('精度边界、独立审计与复现',6,'20次基线/精算运行0错误、0警告；105项数值与独立测量通过。')
        para(fig,.85,'maxstep3→1.5ps、reltol1e-6→1e-7，所有10运行复算。预设转换增益差0.02dB、杂散0.15dB、IIP3差0.05dBm、斜率0.01、输入/输出幅度10uV；最大原始幅度差4.612082uV，全部通过。',9.3)
        para(fig,.675,'极深隔离用线性比值差≤2e-5确认，不能把−129dB相消数字当作真实芯片隔离精度。即使把每个仿真泄漏比加2e-5，仍满足原−45dB门槛；版图失配和寄生未覆盖。',9.3)
        para(fig,.515,'独立使用直接复数DFT而非FFT、逐区间功率积分，复核105标量并调用原7组函数。原ngspice线性化被显式2048点相干重采样替代，保持原时间窗口、频点与幅度比定义；source文件和原门槛未改。',9.3)
        para(fig,.35,'工程根目录，既有Bridge Python：case30_gilbert.py → confirm30.py → schematic30.py → audit30.py → review30.py（均位于scripts/）。附后2页完整图纸；报告生成后须实际查看。',9.3)
        para(fig,.19,'contract、数值计划、基线/精算、独立明细、spectral_records及运行输入和日志完整保留。仅TT1.8V27°C，未做其他PVT、10个随机失配种子、噪声、版图和PEX；原PDK、Bridge、Spectre、LUT未修改。',9.3);save(pdf,fig)
    finish_report(CASE,body,6)

if __name__=='__main__':make()
