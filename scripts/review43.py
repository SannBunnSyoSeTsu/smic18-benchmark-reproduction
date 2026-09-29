"""LNA review: source fixtures, native passives, RF/noise and full drawings."""
from review_pdf import *
from review11 import frame,para,table
import subprocess
from matplotlib.ticker import FuncFormatter
CASE=ROOT/'cases/43-inductive-lna'

def style(axs):
    for ax in np.atleast_1d(axs).flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];s=json.loads((CASE/'sizing.json').read_text());c=json.loads((CASE/'numerical_confirmation.json').read_text());audit=json.loads((CASE/'verification_audit.json').read_text());assert audit['status']=='passed' and c['passed']
    rd=ROOT/r['groups']['rf'];d=data(rd,'band.ac');w=data(rd,'wide.ac');noise=data(rd,'noise.noise',required=['in','out']);f=d['freq'];fw=w['freq'];s11=2*d['rfinf']-1;s21=2*d['rfoutf'];s22=2*d['rfoutr']-1;s12=2*d['rfinr'];a=2*w['rfinf']-1;b=2*w['rfoutf'];cc=2*w['rfoutr']-1;e=2*w['rfinr'];delta=a*cc-b*e;k=(1-abs(a)**2-abs(cc)**2+abs(delta)**2)/(2*abs(b*e))
    specs=[('最小传输功率增益','transducer_gain_db_min',1,'dB'),('通带增益纹波','gain_ripple_db',1,'dB'),('最差S11','s11_db_max',1,'dB'),('最差S22','s22_db_max',1,'dB'),('最差噪声系数','noise_figure_db',1,'dB'),('最差反向S12','reverse_isolation_db_max',1,'dB'),('最小Rollet K','stability_k_min',1,'ratio'),('最大|delta|*','stability_delta_max',1,'ratio'),('完整VDD功耗','power_w',1e3,'mW'),('参考端最低电压*','iref_voltage_v',1,'V'),('参考端最低余量*','iref_headroom_v',1,'V')]
    body=ROOT/'reports/43-inductive-lna-body.pdf';out=ROOT/'reports/43-inductive-lna-review.pdf'
    with PdfPages(body,metadata={'Title':'43 SMIC18 2.4GHz原生无源LNA审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=frame('43 | 2.4GHz电感退化LNA审查',1,'结论：全部标称原门槛通过，无需10%或15%放宽。')
        para(fig,.85,'SMIC18MMRF TT / 1.8V / 27°C / 50uA参考，两端50Ω。增益、匹配、反向隔离及噪声覆盖2.35–2.45GHz；稳定性另覆盖0.1–10GHz。最终通带/噪声各201点、稳定性1601点，包含全部原网格点。',9.1)
        rows=[]
        for label,key,scale,unit in specs:
            q=r['gates'][key];sign='≥' if q['sense']=='min' else ('<' if key=='stability_delta_max' else '≤');rows.append([label,f"{q['value']*scale:.6g}",*[sign+f"{q['limits'][t]*scale:.5g}" for t in ['original','10pct','15pct']],unit])
        table(fig,[.07,.319,.86,.424],['验收量','实测','原门槛','10%','15%','单位'],rows,[.30,.17,.155,.15,.15,.075],7.6)
        para(fig,.26,'增益、纹波与NF按功率比定义dB边界；S参数按幅度比。*标记的参考合规、|delta|<1保持原值，另要求K>1及所有数据有限，不放宽稳定性或缺失测量。',9.0)
        para(fig,.135,'只执行TT标称，原27点PVT中的另外26点与公开0°C诊断未运行；失配、压缩、互调、天线/封装、布局与PEX未验证。小信号通过不等于完整接收机签核。',9.0)
        save(pdf,fig)

        fig=frame('gm/ID尺寸与真实工作点',2,'只有iref外部模拟偏置；电流镜与双NMOS复制栈产生共栅偏置。')
        para(fig,.85,'输入管目标3mA/gmID14，共栅目标3mA/gmID10；偏置复制目标0.3mA。50uA单位LUT查询后以m复制，总输入宽258um、共栅宽115.2um。输入增大gm/ID可减小噪声所需电流，但增加栅电容与匹配电感需求。',9.2)
        table(fig,[.07,.609,.86,.128],['角色','单位W/L um','m','LUT gm/ID'],[['MREF / MNSINK','4.30/0.18','1 / 6','14'],['MIN','4.30/0.18','60','14'],['MCBOT/MCTOP / MCAS','1.92/0.18','6 / 60','10'],['MPDIO / MPMIR','33.94/0.36','各6','14']],[.34,.25,.20,.21],8.2)
        rows=[]
        for dev,q in r['operating_point'].items():rows.append([dev,f"{abs(q['ids'])*1e3:.6f}",f"{q['gmid']:.4f}",f"{q['vgs']:.5f}",f"{q['vds']:.5f}",f"{q['headroom_V']:.5f}"])
        table(fig,[.07,.263,.86,.279],['器件','|ID|/mA','gm/ID','VGS/V','VDS/V','|VDS|-|VDSAT|'],rows,[.17,.18,.14,.15,.15,.21],7.8)
        para(fig,.211,'实际输入/共栅电流3.033245mA；镜吸收支路373.947uA、复制栈366.780uA，高于0.3mA初值，原因包括不同VDS及体效应。两条偏置支路、参考和RF核心全部计入VDD功耗。',9.1)
        para(fig,.106,'MOS使用现有SMIC18 n18/p18 LUT，L0.18/0.36um、VDS0.9V；实际输入gm/ID13.8183、共栅9.9119。所有8只MOS有正电压余量；参数符号沿用Spectre，PMOS电流表中取幅度。',9.0)
        save(pdf,fig)

        fig=frame('完整工艺无源与匹配结构',3,'DUT无用户理想R/C/L；所有spiral均使用文档示例r60um、n3.5的完整模型。')
        table(fig,[.07,.457,.86,.37],['网络','实例/几何','名义量或用途'],[
            ['栅极电感LG','3个ind_rf串联','串联L约9.416925nH，保留每只衬底寄生'],
            ['源退化LS','6个ind_rf并联','独立器件近似L约0.5231625nH'],
            ['漏端电感LD','2个ind_rf串联','串联L约6.27795nH'],
            ['输入CIN','6个mim1_rf，各30×30um','总名义5.4pF'],
            ['iref去耦CBN','6个mim1_rf，各30×30um','总名义5.4pF'],
            ['vcas去耦CBC','4个mim1_rf，各30×30um','总名义3.6pF'],
            ['输出COUT','1个mim1_rf，30×21.833333um','名义0.655pF'],
            ['输出CMATCH','2个mim1_rf，各30×26.456667um','总名义1.5874pF'],
            ['栅偏置RBIAS','rpposab_3t，W1/L150um','第三端接vss；电阻噪声和寄生保留'],
        ],[.21,.40,.39],7.7)
        para(fig,.403,'单个spiral模型串联L=3.138975nH、R=3.7030115Ω，含跨接电容与两侧衬底损耗。以上总L仅是串并联主项估算；实际RF响应使用完整子电路，不以主项理想L/R替换。',9.2)
        para(fig,.257,'mim1_rf含金属串联电阻、电感与衬底支路，名义1fF/um²面积值不等于2.4GHz下的完整阻抗。19个MIM实例逐一绘制，电容板名义总面积16642.4um²；11只spiral还需更大版图面积。',9.2)
        para(fig,.114,'独立spiral之间没有加入互感，尚无物理排布或电磁提取；MOS采用既有n18/p18模型，未额外构造版图门电阻。所有结论限于当前原生模型覆盖，不能假定实芯片有相同性能。',9.0)
        save(pdf,fig)

        fig=frame('通带增益、匹配与噪声',4,'两端50Ω、50uA参考、原101点网格保留，最终201点取最坏值。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.28,top=.84,hspace=.42,wspace=.4);ghz=f/1e9
        axs[0,0].plot(ghz,20*np.log10(abs(s21)),color=BLUE);axs[0,0].set(xlabel='Frequency (GHz)',ylabel='Transducer gain (dB)')
        axs[0,1].plot(ghz,20*np.log10(abs(s11)),label='S11',color=BLUE);axs[0,1].plot(ghz,20*np.log10(abs(s22)),label='S22',color=GREEN);axs[0,1].axhline(-10,ls='--',color=GRAY);axs[0,1].set(xlabel='Frequency (GHz)',ylabel='Reflection (dB)');axs[0,1].legend(fontsize=8)
        axs[1,0].plot(ghz,20*np.log10(noise['in']/np.sqrt(4*1.380649e-23*300.15*50)),color=BLUE);axs[1,0].axhline(2,ls='--',color=GRAY);axs[1,0].set(xlabel='Frequency (GHz)',ylabel='Noise figure (dB)')
        axs[1,1].plot(ghz,20*np.log10(abs(s12)),color=BLUE);axs[1,1].axhline(-30,ls='--',color=GRAY);axs[1,1].set(xlabel='Frequency (GHz)',ylabel='Reverse isolation S12 (dB)');style(axs)
        para(fig,.222,'最终增益18.552718–18.973414dB、纹波0.420696dB；噪声系数最坏1.619038dB。输入匹配最差-10.926464dB，比原-10dB有0.926dB余量，必须与其余指标同时判断。',9.2)
        para(fig,.113,'最差输出匹配-15.769358dB，反向S12为-38.751989dB。保留50Ω输出实负载，未使用开路电压增益代替传输功率增益，也未从噪声中扣掉DUT无源损耗。',9.1)
        save(pdf,fig)

        fig=frame('0.1–10GHz完整稳定性范围',5,'Rollet K与|delta|共同判断；不能仅凭2.4GHz点或反向隔离宣布稳定。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.29,top=.84,hspace=.44,wspace=.42)
        axs[0,0].semilogx(fw/1e9,k,color=BLUE);axs[0,0].axhline(1.2,ls='--',color=GRAY);axs[0,0].set(xlabel='Frequency (GHz)',ylabel='Rollet K')
        axs[0,1].semilogx(fw/1e9,abs(delta),color=BLUE);axs[0,1].axhline(1,ls='--',color=GRAY);axs[0,1].set(xlabel='Frequency (GHz)',ylabel='Magnitude of delta')
        m=(fw>=1.5e9)&(fw<=3.5e9);axs[1,0].plot(fw[m]/1e9,k[m],color=BLUE);axs[1,0].set(xlabel='Frequency (GHz)',ylabel='K near minimum')
        m=fw<=.5e9;axs[1,1].plot(fw[m]/1e9,1-abs(delta[m]),color=BLUE);axs[1,1].set(xlabel='Frequency (GHz)',ylabel='1 - |delta| at low frequency');style(axs)
        for ax in axs[0]:ax.xaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:g}'))
        para(fig,.232,f"K最小{v['stability_k_min']:.9f}，位于{r['worst_frequency_Hz']['K']/1e9:.9f}GHz；|delta|最大{v['stability_delta_max']:.9f}，位于100MHz。低端与1的距离约{1-v['stability_delta_max']:.6f}，明确保留该有限余量。",9.2)
        para(fig,.116,'delta=S11·S22−S12·S21；K=(1−|S11|²−|S22|²+|delta|²)/(2|S12·S21|)。最终1601点均K>1、|delta|<1；这是给定频段及模型的线性双端口判据，未扩称带外、非线性或PVT稳定性。',9.0)
        save(pdf,fig)

        fig=frame('独立测量与频率网格复核',6,'原正向/反向两DUT台保留；输出负载无噪声是原测试条件，DUT噪声全开。')
        para(fig,.85,'正向源AC=1V，串50Ω，输出50Ω：S11=2Vrfin−1、S21=2Vrfout。反向独立DUT用同样端口网络测S22/S12。输入可用功率=1/(8×50)W，输出功率=|Vrfout|²/(2×50)W，独立核对GT=|S21|²。',9.1)
        para(fig,.715,'NF=20log10(max(e_input)/sqrt(4kT×50))，T=300.15K。输入50Ω噪声保留、外部输出50Ω按原台关闭噪声，DUT电阻及RF无源噪声保留。用输出谱除以实际加载AC增益独立重建输入谱，最大相对差约5.15e-12。',9.1)
        rows=[]
        for key,q in c['metrics'].items():rows.append([key,f"{q['baseline']:.8g}",f"{q['refined']:.8g}",f"{q['absolute_difference']:.3g}",f"{q['maximum_difference']:.3g}"])
        table(fig,[.07,.277,.86,.315],['复核量/SI或dB','原网格','加密网格','绝对差','预设上限'],rows,[.33,.18,.18,.155,.155],7.1)
        para(fig,.225,'原通带/噪声101点、稳定性401点；最终201/1601点含全部原频率，reltol从1e-6至1e-7。预设增益/匹配/隔离差≤0.05dB、NF≤0.005dB、K≤基线1%、delta≤1e-4、功耗≤1uW、偏置≤10uV，全部通过。',9.0)
        para(fig,.102,'独立13项测量与原7组检查全部通过。源文件、模型、RF子电路与LUT哈希未变；两个正式精度运行均0错误/0警告。39实例95端子另行独立连接审计。',9.0)
        save(pdf,fig)

        fig=frame('迭代过程与复现入口',7,'调整输出阻抗变换，保持电流、原RF端口与噪声定义。')
        table(fig,[.07,.637,.86,.197],['阶段','变化','结果'],[
            ['首版','LD单spiral；COUT0.5pF/CM1.2pF','增益4.194dB、S22 -0.291dB失败'],
            ['增加漏端L','LD改两spiral串联','增益16.770dB，但S22 -3.870dB仍失败'],
            ['最终匹配','COUT0.655pF、CM1.5874pF','全部原门槛通过'],
            ['精度确认','原101/401点→201/1601点','同电路、同频段、固定精度界限通过'],
        ],[.14,.42,.44],7.8)
        para(fig,.579,'从复数S22推导输出阻抗，在2.4GHz用电容网络估算下一次匹配值，再以完整工艺模型重新验证。没有用理论估算替代最终仿真。早期Spectre lin=101产生102点，发现后改为100个间隔，先恢复原101点再进行加密对照。',9.1)
        para(fig,.409,'复现（工程根目录，既有Bridge Python）：\npython scripts/case43_lna.py\npython scripts/confirm43.py\npython scripts/schematic43.py\npython scripts/audit43.py\npython scripts/review43.py\n报告重建后须重新查看全部页面及完整总图。',8.7)
        para(fig,.19,'source/和source_provenance.json保存原合同/测试台/验收器。iteration_history.json保存失败方案；numerical_plan/baseline/confirmation保留精度计划和对照；verification_audit.json保留独立公式与来源，implementation/冻结本次脚本。',9.0)
        para(fig,.095,'原26个其他PVT点、失配、压缩/互调、布局互感与PEX未执行；不把本次TT结果标记为上游27点完整签核。',9.0)
        save(pdf,fig)

        fig=frame('最终精确电路与证据边界',8,'全部模拟实例在后附三页完整图纸中一一对应；未折叠无源阵列。')
        net=(CASE/'circuit.scs').read_text();fig.text(.07,.85,net,fontsize=6.9,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.32)
        para(fig,.187,'端序：MOS为D G S B；rpposab_3t第三端为衬底；ind_rf和mim1_rf仅有两外部端口，其原厂衬底网络参考全局0，本测试vss=0。完整原厂RF模型未改写为用户理想器件。',8.7)
        para(fig,.09,'DUT SHA-256：\n'+r['circuit_sha256'],7.6)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(CASE/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1]);write_json(CASE/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(CASE/'latest_results.json'),circuit_sha256=sha(CASE/'circuit.scs'),sizing_sha256=sha(CASE/'sizing.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=3,schematic_sheets_sha256=sha(CASE/'schematic/sheets.pdf'),render_review_pending=True));print(out)

if __name__=='__main__':make()
