"""Review document plus complete, netlist-linked transistor schematic sheets."""
from review_pdf import *
import subprocess

def make25():
    case=ROOT/'cases/25-complementary-ab';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values']
    runs={k:ROOT/x for k,x in r['groups'].items()};a=data(runs['ac'],'ac.ac');d=data(runs['track'],'track.dc');n=data(runs['noise'],'noise.noise',required=('in','out'));q=data(runs['reject'],'ac.ac');t=data(runs['step'],'tran.tran');u=data(runs['thd'],'tran.tran')
    body=ROOT/'reports/25-complementary-ab-body.pdf';out=ROOT/'reports/25-complementary-ab-review.pdf'
    with PdfPages(body,metadata={'Title':'25 SMIC18 互补轨到轨Class-AB运放','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('25 | 互补轨到轨 Class-AB 运放',1,'结论：全部适用 nominal 原门槛通过；未使用10%或15%放宽。')
        para(fig,.848,'SMIC18MMRF / TT / 1.8 V / 27°C；唯一20 uA参考，4 pF负载。跟踪、阶跃、噪声和失真另有10 kΩ接0.9 V。45 MOS、12 R、6 C，全部模拟器件有目标工艺gm/ID依据。',9.1)
        specs=[('核心范围最小增益','gain_3_dB',1,'dB'),('近轨最小增益','gain_4_dB',1,'dB'),('最小UGB','ugb_3_Hz',1e-6,'MHz'),('核心范围最小PM','pm_2_deg',1,'°'),('近轨最小PM','pm_0_deg',1,'°'),('五共模UGB最大/最小','ugb_ratio',1,''),('核心最大跟踪误差','tracking_core_error_V',1e3,'mV'),('宽范围最大跟踪误差','tracking_band_error_V',1e3,'mV'),('合格输入共模跨度','icmr_span_V',1,'V'),('最坏高轨余量','icmr_high_headroom_V',1,'V'),('全扫最大VDD功耗','tracking_power_W',1e3,'mW'),('10Hz–1MHz输入噪声','noise_Vrms',1e6,'uVrms'),('最小双向压摆率','slew_up_Vus',1,'V/us'),('最后100ns最大误差','settle_tail_error_V',1e3,'mV'),('CMRR @1MHz','CMRR_1M_dB',1,'dB'),('PSRR @1MHz','PSRR_1M_dB',1,'dB'),('1kHz Fourier THD','THD_percent',1,'%'),('最大残差/0.4V','THD_residual_fraction',100,'%')]
        rows=[]
        for name,key,k,unit in specs:
            z=r['gates'][key];sign='≥' if z['sense']=='min' else '≤';rows.append([name,f"{v[key]*k:.5g}",*[sign+f"{z['limits'][tier]*k:.5g}" for tier in ['original','10pct','15pct']],unit])
        table(fig,[.07,.275,.86,.505],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.33,.14,.14,.14,.14,.11],7.4)
        para(fig,.235,'五个输入共模：0.1、0.2、0.9、1.6、1.7 V；AC输出均由DC伺服维持0.9 V。独立闭环STB最小PM86.569°，五条1 Hz–1 GHz环路均只有一次下降交越且无回穿。',9)
        para(fig,.142,'输入扫0–1.8 V共361点；固定20 mV资格窗得到0–1.795 V跨度。末点上限依原提取定义，不外推。最低轨余量0 V也达原要求；1 kHz CMRR115.268 dB、10 Hz PSRR90.945 dB。',8.9)
        para(fig,.071,'范围：原25点PVT约化为nominal；未执行其余24点、两组非nominal拒斥/失真点、3个失配种子或PEX。附图S1–S4完整绘制全部63个器件；另提供整张矢量总图。',8.8)
        save(pdf,fig)

        fig=page('架构选择与gm/ID定尺寸',2,'互补输入、尾电流转向、折叠电流汇合、浮动AB控制和两路串联RC补偿均为真实器件。')
        para(fig,.855,'输入：NMOS和PMOS差分对各40 uA基础尾电流，源退化分别500/300 Ω。转向镜为1:1，低共模由PMOS对承接、高共模由NMOS对承接；中间两对重叠工作。折叠支路目标40 uA，输出静态目标约200 uA。',9.3)
        roles=[('nbias','N偏置/尾源/转向镜'),('pbias','P偏置/尾源/转向镜'),('nin','N输入与同尺寸N转向'),('pin','P输入与同尺寸P转向'),('ncas','N共栅及复制二极管'),('pcas','P共栅及复制二极管'),('pmirror','P长沟道求和镜'),('nab','N浮动管/偏置上管'),('pab','P浮动管/偏置上管'),('nout','N输出/偏置下管'),('pout','P输出/偏置下管'),('nref','N转向门限二极管'),('pref','P转向门限二极管')]
        rows=[]
        for key,label in roles:
            z=s['roles'][key];rows.append([label,z['model'],f"{z['rounded_W_um']:.2f}/{z['L_um']:g}",f"{z['gmid']:g}",f"{z['Id_A']*1e6:g}",f"{z['Vgs_V']:.4f}"])
        table(fig,[.07,.365,.86,.36],['角色','模型','单位W/L um','gm/ID','单位Id/uA','LUT |VGS|'],rows,[.31,.10,.18,.12,.14,.15],8.0)
        para(fig,.321,'所有查询使用既有TT/27°C、Wref10 um、VBS=0表：L1的|VDS|=0.45 V，L4为0.9 V。W由Id/(Id/W)得到并量化20 nm，宽单元用m并联。最大单位W69.42 um；未超出100 um模型上限。本模块无需新扫LUT。',9.2)
        para(fig,.220,'输入每管m4；主P镜m6；N/P浮动管m2与偏置上管m1维持相同单位电流密度；输出m20与下管m1复制目标偏置。器件实际gm/ID随体偏、漏压及共模变化，不能把LUT目标当成全范围实测常数。',9.2)
        para(fig,.115,'补偿最终为每路12 pF串1 kΩ，分别返回fp2、fn2；两输出栅各0.5 pF。两输入经15 kΩ/4 pF耦合至ntail以改善高频共模跟随。全部R/C允许使用理想器件；无源面积、容差与寄生未签核。',9.1)
        save(pdf,fig)

        fig=page('尾电流交接与浮动Class-AB偏置',3,'电流预算和体效应复制决定可用工作点；浮动N/P管共同从gp向gn传导。')
        para(fig,.858,'令SN、SP为两只转向管电流，基础尾电流T=40 uA。理想镜比下：IN=T+SP−SN，IP=T+SN−SP，因此IN+IP=80 uA；折叠底部电流设为60 uA+0.5SN−0.5SP，得到K=Isink−IP/2=40 uA。真实镜管漏压不同，以下保留实测偏差。',9.2)
        rows=[]
        for row in r['ac_rows']:
            op=row['operating_points'];rows.append([f"{row['cm_V']:g}",*[f"{abs(op[k]['ids'])*1e6:.3f}" for k in ['MNINN','MPINN','MNSW','MPSW','MNC2','MOUTN']]])
        table(fig,[.07,.602,.86,.145],['VCM/V','N输入/支uA','P输入/支uA','SN/uA','SP/uA','K/uA','输出Iq/uA'],rows,[.11,.16,.16,.14,.14,.14,.15],8.0)
        para(fig,.554,'中点输入gm/ID为N22.29/P22.00，近轨单边活动对约19.6–20.1；活动输入总gm变化不大。两条尾支路不会在交接时同时消失。截止的互补输入或转向管是预期状态，不对这些管强求饱和导通。',9.1)
        para(fig,.451,'N偏置：上管(MABNU)与浮动管(MABN)同L、同单位电流密度，体均接VSS；下管(MABNL)复制输出N管VGS。于是gn≈xn。P偏置同理：上管MABPU与MABP的体均接VDD，源分别yp、gp；保留相同体偏使gp≈yp，不能只把上管体接本地源。',9.2)
        mid=r['ac_rows'][2]['nodes'];nod=lambda name:mid['X2.'+name]
        rows=[[k,f"{nod(k):.6f} V"] for k in ['xn','gn','yp','gp','vabn','vabp','fn2','fp2']]
        table(fig,[.07,.151,.46,.204],['中心工作点','实测'],rows,[.40,.60],8.3)
        ax=fig.add_axes([.59,.16,.32,.19]);ax.axis('off');ax.text(0,.93,'体效应复制关系\n\nGN ≈ XN\nGP ≈ YP\nIABN + IABP = K\n\nMOUTN/P: m20\nMABNL/PL: m1',va='top',fontsize=10,color=BLUE)
        para(fig,.10,'中心输出静态电流205.922 uA；完整阶跃期间源出峰值503.770 uA、灌入峰值813.736 uA，超过静态电流，体现AB驱动。全输入扫的VDD最大1.083 mW已经包含20 uA参考支路。',9.0)
        save(pdf,fig)

        fig=page('五共模稳定性与补偿修正',4,'原AC返回比T=−VOUT/VINN；另外以原负载下的真实闭环STB交叉检查。')
        axs=fig.subplots(2,1);fig.subplots_adjust(left=.12,right=.94,bottom=.36,top=.85,hspace=.31)
        for i,cm in enumerate([.1,.2,.9,1.6,1.7]):
            h=-a[f'out{i}']/a[f'vinn{i}'];axs[0].semilogx(a['freq'],20*np.log10(abs(h)),label=f'{cm:g} V');axs[1].semilogx(a['freq'],np.unwrap(np.angle(h))*180/np.pi,label=f'{cm:g} V')
        axs[0].axhline(0,color=GRAY,lw=.7);axs[0].set(ylabel='Return ratio (dB)',xlim=(1,1e9));axs[0].legend(ncol=5,fontsize=7.7)
        axs[1].axhline(-180,color=GRAY,lw=.7);axs[1].set(ylabel='Phase (deg)',xlabel='Frequency (Hz)',xlim=(1,1e9))
        for ax in axs:ax.grid(which='both',alpha=.18);ax.tick_params(labelsize=8)
        rows=[]
        for i,z in enumerate(r['ac_rows']):
            m=z['metrics'];st=r['native_stb']['rows'][i];rows.append([f"{z['cm_V']:g}",f"{m['gain_db']:.3f}",f"{m['ugb_hz']/1e6:.4f}",f"{m['phase_margin_deg']:.3f}",f"{st['phase_margin_deg']:.3f}"])
        table(fig,[.07,.195,.86,.125],['VCM/V','10Hz增益/dB','UGB/MHz','原AC PM/°','真实STB PM/°'],rows,[.14,.23,.22,.22,.19],8.1)
        para(fig,.152,'初版6 pF/5 kΩ：中点UGB54.321 MHz、PM19.684°，共模UGB比4.739，失败；近轨PM虽大也不能代表中点。改为12 pF/1 kΩ后五点均通过，最小双向压摆率仍2.627 V/us。',9.1)
        para(fig,.071,'gm平坦不能单独证明UGB平坦。两路补偿零极点及内部加载共同决定返回比。本次仅修正一次后满足原指标；五个原AC及STB响应在1Hz–1GHz均无0dB回穿。',8.9)
        save(pdf,fig)

        fig=page('轨到轨跟踪、功耗、噪声与拒斥',5,'保留原负载、频段和固定0.9V拒斥共模；不由匹配模型推断失配性能。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.29,top=.85,hspace=.43,wspace=.43)
        axs[0,0].plot(d['vinp'],(d['vout']-d['vinp'])*1e3,color=BLUE);axs[0,0].set(xlabel='VIN command (V)',ylabel='Tracking error (mV)',xlim=(0,1.8));axs[0,0].axvspan(.1,1.7,alpha=.07,color=GREEN)
        axs[0,1].plot(d['vinp'],-1.8*d['VDD:p']*1e3,color=BLUE);axs[0,1].axhline(1.5,color=GRAY,ls='--');axs[0,1].set(xlabel='VIN command (V)',ylabel='VDD static power (mW)',xlim=(0,1.8))
        axs[1,0].loglog(n['freq'],abs(n['in'])*1e9,color=BLUE);axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Input noise (nV/sqrt(Hz))',xlim=(10,1e6))
        axs[1,1].semilogx(q['freq'],20*np.log10(abs(q['outD']/q['outC'])),label='CMRR');axs[1,1].semilogx(q['freq'],20*np.log10(abs(q['outD']/q['outP'])),label='PSRR');axs[1,1].set(xlabel='Frequency (Hz)',ylabel='Rejection (dB)',xlim=(10,1e8));axs[1,1].legend(fontsize=8)
        for ax in axs.flat:ax.grid(which='both',alpha=.2);ax.tick_params(labelsize=7.7)
        rows=[['CMRR @1kHz',v['CMRR_1k_dB'],70],['CMRR @1MHz',v['CMRR_1M_dB'],55],['PSRR @10Hz',v['PSRR_10Hz_dB'],45],['PSRR @1MHz',v['PSRR_1M_dB'],10]]
        table(fig,[.07,.148,.86,.092],['指标','实测/dB','原下限/dB'],[[z[0],f'{z[1]:.6f}',str(z[2])] for z in rows],[.45,.30,.25],8.1)
        para(fig,.109,'原噪声bench在DC闭环，但AC由大电容把负输入接地；本次如实测其输入折算谱，固定10Hz–1MHz积分12.894430 uVrms。此数不是独立实测的闭环输出总噪声。',8.7)
        para(fig,.067,'0.2–1.6V与0.1–1.7V误差均≤53.093uV；5mV/20mV误差窗保持。0.9V确定性偏差−23.487uV；3个随机失配种子未执行，不能视为失调良率。',8.6)
        save(pdf,fig)

        fig=page('大信号双向驱动与低失真',6,'阶跃0.2↔1.6V，4pF并10kΩ；THD为0.9V中心、0.4V峰值、1kHz。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.32,top=.85,hspace=.43,wspace=.42)
        axs[0,0].plot(t['time']*1e6,t['vinp'],color=GRAY,label='VIN');axs[0,0].plot(t['time']*1e6,t['vout'],color=BLUE,label='VOUT');axs[0,0].set(xlabel='Time (us)',ylabel='Voltage (V)',xlim=(0,5));axs[0,0].legend(fontsize=8)
        axs[0,1].plot(t['time']*1e6,abs(t['X.MOUTN:ids'])*1e6,label='Sink N');axs[0,1].plot(t['time']*1e6,abs(t['X.MOUTP:ids'])*1e6,label='Source P');axs[0,1].set(xlabel='Time (us)',ylabel='Output device current (uA)',xlim=(0,5));axs[0,1].legend(fontsize=8)
        mask=u['time']>=.0035;axs[1,0].plot(u['time'][mask]*1e3,(u['vout'][mask]-u['vinp'][mask])*1e6,color=BLUE);axs[1,0].set(xlabel='Time (ms)',ylabel='Tracking residual (uV)',xlim=(3.5,5))
        amps=np.array(r['fourier']['harmonic_amplitudes_V']);axs[1,1].bar(np.arange(2,10),20*np.log10(amps[1:]/amps[0])+145,bottom=-145,color=BLUE);axs[1,1].set(xlabel='Harmonic number',ylabel='Harmonic / fundamental (dBc)',xticks=np.arange(2,10),ylim=(-145,-80))
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=7.7)
        rows=[['上升20%→80% SR',f"{v['slew_up_Vus']:.6f} V/us",'≥2'],['下降80%→20% SR',f"{v['slew_down_Vus']:.6f} V/us",'≥2'],['两个末100ns窗误差',f"{v['settle_tail_error_V']*1e6:.3f} uV",'≤5000 uV'],['Fourier h2..h9 THD',f"{v['THD_percent']:.9f} %",'≤0.01 %'],['3.5–5ms最大残差/幅度',f"{v['THD_residual_fraction']*100:.6f} %",'≤0.5 %']]
        table(fig,[.07,.159,.86,.12],['正式指标','实测','原门槛'],rows,[.43,.34,.23],8)
        para(fig,.115,'阶跃观察5us；边沿1–1.01us/3–3.01us，SR用0.48/1.32V交越；末窗2.9–3us和4.9–5us。最大步0.5ns，1ns保存；没有缩短观察窗或按实测终值重定义误差。',8.7)
        para(fig,.069,'THD仿真5ms、最大步50ns、250ns保存；取最后1ms相干周期，DC+1..9谐波拟合。原默认200点和4000点交叉一致。失真不包含随机瞬态噪声。',8.7)
        save(pdf,fig)

        fig=page('测量合同、复现路径与证据边界',7,'六组正式nominal运行，加一组包含五共模分析的真实闭环STB；本轮只设计第25项。')
        rows=[['AC','五共模；1Hz–1GHz；输出DC0.9V；4pF+1TΩ','五点gain/UGB/PM/power和比值'],['跟踪','0–1.8V，5mV步进；4pF+10kΩ','361点、固定误差窗、全扫功耗'],['噪声','10Hz–1MHz，负输入AC接地','原输入折算谱；501点积分'],['CMRR/PSRR','固定0.9V，差分基准实例','4pF与100MΩ；指定频点'],['阶跃','完整5us，两方向和两个末100ns窗','首个20/80%交越与最大误差'],['失真','5ms正弦；最后1ms Fourier','1..9次谐波、1.5ms残差窗'],['STB诊断','真实闭合反馈、五个共模点','原AC负载；每条单次交越']]
        table(fig,[.07,.596,.86,.254],['运行','保持的原测试定义','验收覆盖'],rows,[.13,.49,.38],7.5)
        para(fig,.550,'所有最终运行模型尺寸合法，六组正式运行使用同一电路SHA；全部LUT及源合同已冻结。AC与STB各有两条SPECTRE-294提示：保存1480条信号可能减慢初始化；数据完整，未发生模型尺寸越界或仿真失败。其他最终运行无警告。',9.2)
        para(fig,.430,'独立复核：原默认200点Fourier与4000点THD一致；噪声输出谱/传递增益逐点等于输入谱，PSD梯形与幂律积分约差0.0004%。这些是现有PSF后处理核对，没有重跑电气或改变合同。',9.1)
        para(fig,.332,'复现命令（在工程根目录，用既有Bridge Python）：\npython scripts/case25_complementary_ab.py --full\npython scripts/case25_complementary_ab.py --stb\npython scripts/case25_complementary_ab.py --extract\npython scripts/schematic25.py\npython scripts/review_pdf.py 25',8.2)
        para(fig,.196,'最终运行路径：\n'+'\n'.join(r['run_dirs']),7.9)
        para(fig,.076,'原题其余PVT、代表非nominal点、3次固定失配回归、真实参考噪声、无源容差和版图寄生均未完成。大增益与低确定性误差不能作为这些范围的通过证据。',8.8)
        save(pdf,fig)

        fig=page('精确晶体管网表与图纸对应',8,'D G S B端序；每个器件均在附图S1–S4中出现，体端与跨页同名网络明确标识。')
        net='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.074,.859,net,fontsize=7.4,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.12)
        para(fig,.115,'图纸：cases/25-complementary-ab/schematic/full.svg与full.pdf提供整张总图；sheets.pdf为后附分图。connectivity.json和schematic_audit.json检查每个实例与引脚。网表为唯一电气真源，图纸数值从该文件自动提取。',8.6)
        para(fig,.051,'电路SHA-256：'+sha(case/'circuit.scs'),7.4)
        save(pdf,fig)
    sheets=case/'schematic/sheets.pdf'
    if not sheets.exists():return body
    subprocess.run(['pdfunite',str(body),str(sheets),str(out)],check=True)
    info=subprocess.run(['pdfinfo',str(out)],check=True,capture_output=True,text=True).stdout;pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),sizing_sha256=sha(case/'sizing.json'),geometry_sha256=sha(case/'geometry.json'),generated_at=now(),pages=pages,body_pages=8,schematic_pages=pages-8,schematic_sheets_sha256=sha(sheets),render_review_pending=True))
    update_case(25,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out

if __name__=='__main__':print(make25())
