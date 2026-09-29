"""Nominal CML TX report with unchanged stimuli, full gates and complete DUT."""
from review_pdf import *
from review11 import frame,para,table
import subprocess
CASE=ROOT/'cases/32-cml-tx';UI=1/28e9

def rows_for(r,spec):
    rows=[]
    for label,key,scale,unit in spec:
        g=r['gates'][key];sgn='≥' if g['sense']=='min' else '≤'
        rows.append([label,f"{g['value']*scale:.6g}",*[sgn+f"{g['limits'][t]*scale:.5g}" for t in ['original','10pct','15pct']],unit])
    return rows

def style(axes):
    for ax in np.atleast_1d(axes).flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8)

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];s=json.loads((CASE/'sizing.json').read_text());c=json.loads((CASE/'numerical_confirmation.json').read_text());audit=json.loads((CASE/'verification_audit.json').read_text());detail=audit['independent_details'];assert c['passed'] and audit['status']=='passed'
    runs={k:ROOT/p for k,p in r['groups'].items()};ac=data(runs['ac'],'ac.ac');pr=data(runs['prbs7'],'tran.tran');se=data(runs['sensitivity'],'tran.tran');hist=json.loads((CASE/'iteration_history.json').read_text())
    stat=[('差分摆幅下限','swing_v_min',1e3,'mV'),('差分摆幅上限','swing_v_max',1e3,'mV'),('共模距VDD下限','vocm_drop_min_v_min',1e3,'mV'),('共模距VDD上限','vocm_drop_max_v_max',1e3,'mV'),('两符号共模差','cm_shift_v_max',1e3,'mV'),('零输入失调','offset_v_max',1e3,'mV'),('两符号IDD差比','idd_imbalance_fraction_max',100,'%'),('静态轨下限*','static_min_v_min',1,'V'),('静态轨上限*','static_max_v_max',1,'V'),('100MHz增益下限','gain_100mhz_v_min',1,'V/V'),('100MHz增益上限','gain_100mhz_v_max',1,'V/V'),('-3dB带宽','bw_hz_min',1e-9,'GHz'),('100MHz–22GHz峰化','peaking_db_max',1,'dB'),('1–14GHz群延迟变化','group_delay_var_s_max',1e12,'ps')]
    dyn=[('PRBS眼高','prbs_eye_height_v_min',1e3,'mV'),('PRBS最坏上升','prbs_rise_time_s_max',1e12,'ps'),('PRBS最坏下降','prbs_fall_time_s_max',1e12,'ps'),('过冲/欠冲占静态摆幅','overshoot_fraction_max',100,'%'),('动态共模最大偏离','prbs_vocm_dev_max_v_max',1e3,'mV'),('动态轨下限*','prbs_vmin_min',1,'V'),('动态轨上限*','prbs_vmax_max',1,'V'),('确定性抖动峰峰值','prbs_jitter_pp_s_max',1e12,'ps'),('确定性抖动RMS','prbs_jitter_rms_s_max',1e12,'ps'),('DCD','prbs_dcd_s_max',1e12,'ps'),('原样点平均功耗','prbs_avg_power_w_max',1e3,'mW'),('时间加权平均功耗','time_weighted_power_w_max',1e3,'mW'),('低摆幅输出','sens_swing_v_min',1e3,'mV'),('低摆幅最坏上升','sens_rise_time_s_max',1e12,'ps'),('低摆幅最坏下降','sens_fall_time_s_max',1e12,'ps')]
    assert len(stat)+len(dyn)==len(r['gates'])==29
    body=ROOT/'reports/32-cml-tx-body.pdf';out=ROOT/'reports/32-cml-tx-review.pdf'
    with PdfPages(body,metadata={'Title':'32 SMIC18 28Gb/s CML发送器审查','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=frame('32 | 28Gb/s CML发送器审查',1,'结论：10%范围内完成；带宽与低摆幅输出需放宽，其余原门槛通过。')
        para(fig,.85,'SMIC18MMRF TT / 1.8V / 27°C，外部100uA参考；输入共模1.17V。每腿输入50Ω源阻抗、30fF焊盘，输出50Ω到VDD及100fF到地。原PRBS7和低摆幅PWL激励全文保留。',9.1)
        key=[stat[0],stat[11],stat[13],dyn[0],dyn[7],dyn[11],dyn[12]]
        table(fig,[.07,.422,.86,.30],['验收量','实测','原门槛','10%边界','15%边界','单位'],rows_for(r,key),[.31,.15,.16,.15,.15,.08],7.9)
        para(fig,.36,'PRBS第二周期127个采样、63个跳变（31升/32降）及低摆幅8个采样、4升/4降全部满足；符号错误均为0。功能、测量完整性、有限值和输出轨范围保持原要求。',9.2)
        para(fig,.211,'只运行TT标称；原题另外两个配对点ss/1.62V/-40°C与ff/1.98V/125°C未执行。无随机噪声或失配仿真，不能把这里的确定性抖动当作总抖动或误码率。',9.2)
        para(fig,.085,'四只原生n18、两只15fF电容及四只200pH理想电感；正值理想R/C/L为原题明确允许。电感损耗、面积、耦合与PEX尚未验证。',9.1)
        save(pdf,fig)

        fig=frame('结构、gm/ID尺寸与实际偏置',2,'跨接漏端使正差分输入对应正差分输出；无内部重复终端或理想偏置源。')
        para(fig,.85,'MREF与MTAIL由外部100uA参考形成1:200电流镜；差分对目标每支10mA。较低输入gm/ID用更高电流换取较小栅电容和较短延迟；尾源gm/ID=18降低所需余量。串联电感补偿输入、输出电容，交叉电容用于中和反馈。',9.2)
        table(fig,[.07,.618,.86,.12],['角色','W/L um','m','目标gm/ID','初算电流'],[['MREF','39.76/0.36','1','18','100uA'],['MTAIL','39.76/0.36','200','18','20mA'],['MPAIRP/N','0.64/0.18','各100','3','各10mA']],[.22,.22,.15,.19,.22],8.4)
        rows=[]
        for tag in ['off','one']:
            for dev,q in r['operating_point'][tag].items():rows.append([tag+'/'+dev,f"{q['ids']*1e3:.6f}",f"{q['gmid']:.4f}",f"{q['vgs']:.5f}",f"{q['vds']:.5f}",f"{q['headroom_V']:.5f}"])
        table(fig,[.07,.277,.86,.265],['输入/器件','ID/mA','gm/ID','VGS/V','VDS/V','VDS-VDSAT/V'],rows,[.24,.17,.13,.14,.14,.18],7.6)
        para(fig,.226,'off为零差分，one为+150mV差分。实际尾电流18.707–18.713mA，低于20mA初值；零输入每支9.35368mA、gm/ID=3.097。输入管体接vss，实际尾节点约0.207V，体效应与电流镜VDS差异由OP确认。',9.1)
        para(fig,.10,'使用既有TT LUT：输入L0.18um/VDS0.9V、参考L0.36um/VDS0.45V，按单位100uA查询并保留路径/哈希。四只MOS均有正VDS余量；对称结果不代表失配下零失调。',9.0)
        save(pdf,fig)

        fig=frame('完整静态及AC验收门槛',3,'14个标量边界；*为不放宽的输出轨检查，数值均来自最终电路。')
        table(fig,[.07,.285,.86,.55],['测量','实测','原门槛','10%','15%','单位'],rows_for(r,stat),[.32,.16,.15,.145,.145,.08],7.7)
        para(fig,.232,'静态输入分别为±150mV、0差分，共模1.17V。输出两个符号为±204.850mV差分；输出共模1.33216677V。共模差、零输入失调与IDD不平衡在匹配模型中为0。',9.2)
        para(fig,.126,'AC用两路幅度0.5V、相差180°的源构成1V差分激励；源端定义增益，50Ω/30fF输入网络计入传递函数。带宽按原算法在幅度轴与频率轴线性插值首个-3dB交越。',9.1)
        save(pdf,fig)

        fig=frame('幅频、相位与群延迟',4,'10MHz–50GHz，每十倍频50点；群延迟变化仅在1–14GHz统计。')
        f=ac['freq'];h=ac['voutp']-ac['voutn'];phase=np.unwrap(np.angle(h));gd=-np.diff(phase)/(2*np.pi*np.diff(f));mid=(f[1:]+f[:-1])/2
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.29,top=.84,hspace=.43,wspace=.4)
        axs[0,0].semilogx(f/1e9,abs(h),color=BLUE);axs[0,0].axhline(v['gain_100mhz_v']/np.sqrt(2),ls='--',color=GRAY);axs[0,0].set(xlabel='Frequency (GHz)',ylabel='Gain (V/V)')
        axs[0,1].semilogx(f/1e9,phase*180/np.pi,color=BLUE);axs[0,1].set(xlabel='Frequency (GHz)',ylabel='Unwrapped phase (degree)')
        from matplotlib.ticker import FuncFormatter
        for ax in axs[0]:ax.xaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:g}'))
        mask=(mid>=1e9)&(mid<=14e9);axs[1,0].plot(mid[mask]/1e9,gd[mask]*1e12,'.-',color=BLUE);axs[1,0].set(xlabel='Frequency (GHz)',ylabel='Physical group delay (ps)')
        freqs=np.linspace(.1,25,600)*1e9;axs[1,1].plot(freqs/1e9,20*np.log10(np.interp(freqs,f,abs(h))/v['gain_100mhz_v']),color=BLUE);axs[1,1].axhline(-3.0103,ls='--',color=GRAY);axs[1,1].axvline(v['bw_hz']/1e9,color=GREEN,ls=':');axs[1,1].set(xlabel='Frequency (GHz)',ylabel='Relative gain (dB)');style(axs)
        para(fig,.226,'群延迟=-dφ/dω，其中φ以弧度计算。原ac_analysis.py把输入相位视为度，原SPICE台则输出ph()；迁移明确导出DEGREES接口后调用未改动分析器，并与弧度导数独立核对。',9.2)
        units=detail['ac_phase_units'];para(fig,.111,f"真实群延迟变化{v['group_delay_var_s']*1e12:.6f}ps；误将弧度当度会得到{units['incorrect_radian_as_degree_diagnostic_s']*1e12:.6f}ps，该错误单位诊断不参与评分。通带峰化0dB也不表示绝对传播延迟为零。",9.1)
        save(pdf,fig)

        fig=frame('原PRBS7眼图与确定性抖动',5,'28Gb/s，UI=35.7142857ps；运行两个127位周期，只验收第二周期。')
        d=detail['prbs7'];t=pr['time'];y=pr['voutp']-pr['voutn'];delay=d['mean_delay_s'];axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.94,bottom=.30,top=.84,hspace=.45,wspace=.40)
        m=(t>=127*UI)&(t<=139*UI);axs[0,0].plot((t[m]-127*UI)*1e12,y[m]*1e3,color=BLUE);axs[0,0].plot((t[m]-127*UI)*1e12,(pr['dinp'][m]-pr['dinn'][m])*1e3,color=GRAY,alpha=.6);axs[0,0].set(xlabel='From second-period start (ps)',ylabel='Differential voltage (mV)')
        grid=np.linspace(-.5,1.5,401)
        for n in range(128,252):axs[0,1].plot(grid,np.interp((n+grid)*UI+delay,t,y)*1e3,color=BLUE,alpha=.14,lw=.65)
        axs[0,1].axvline(.5,color=GREEN,ls='--');axs[0,1].set(xlabel='Delay-compensated time (UI)',ylabel='Eye differential (mV)')
        axs[1,0].plot(d['sample_indices'],np.array(d['sample_values_V'])*1e3,'.',color=BLUE);axs[1,0].set(xlabel='Original bit index',ylabel='Center samples (mV)')
        err=np.array(d['edge_errors_s']);axs[1,1].plot(d['edge_indices'],(err-np.mean(err))*1e12,'.-',color=BLUE);axs[1,1].set(xlabel='Transition bit index',ylabel='Mean-removed timing error (ps)');style(axs)
        para(fig,.241,f"平均传播偏移{delay*1e12:.6f}ps，采样时刻为(n+0.5)UI+该偏移；127个样点无符号错，眼高{v['prbs_eye_height_v']*1e3:.6f}mV。63个过零交越逐一匹配且不重复使用。",9.2)
        para(fig,.12,'峰峰值/RMS抖动取过零误差减均值后统计；DCD为上、下沿平均偏移之差。眼图仅用于可视化；评分使用原始自适应轨迹和原检查器，不从画图重采样结果计算。',9.1)
        save(pdf,fig)

        fig=frame('完整瞬态验收门槛',6,'15个标量边界，加功能计数与零符号错误；所有原始门槛及两档边界均列出。')
        table(fig,[.07,.268,.86,.568],['测量','实测','原门槛','10%','15%','单位'],rows_for(r,dyn),[.32,.16,.15,.145,.145,.08],7.5)
        para(fig,.224,'PRBS 20–80%边沿阈值来自独立静态两电平，不按动态峰值重新缩放。过冲和欠冲分别为1.916018/1.915712mV，按静态409.700132mV摆幅归一化；动态共模偏移以静态共模为基准。',9.0)
        para(fig,.116,'原验收功耗为自适应原样点IDD算术均值×1.8V；另按第二周期真实时间加权积分，同样检查45mW上限。两者含参考电流和输出终端的VDD功耗，按原合同不计输入信号源。',9.0)
        save(pdf,fig)

        fig=frame('200mVpp差分输入敏感性',7,'12UI交替码，前4UI预热；后8个延迟补偿中心样点验收，原PWL未改。')
        d=detail['sensitivity'];t=se['time'];y=se['voutp']-se['voutn'];axs=fig.subplots(2,1);fig.subplots_adjust(left=.13,right=.94,bottom=.31,top=.84,hspace=.39)
        axs[0].plot(t*1e12,(se['srcp']-se['srcn'])*1e3,label='Source',color=GRAY);axs[0].plot(t*1e12,y*1e3,label='Output',color=BLUE);axs[0].scatter(np.array(d['sample_times_s'])*1e12,np.array(d['sample_values_V'])*1e3,color=GREEN,s=15,label='8 score samples');axs[0].set(xlabel='Time (ps)',ylabel='Differential voltage (mV)');axs[0].legend(fontsize=8)
        axs[1].plot(t*1e12,se['voutp'],label='VOUTP',color=BLUE);axs[1].plot(t*1e12,se['voutn'],label='VOUTN',color=GREEN);axs[1].set(xlabel='Time (ps)',ylabel='Output voltage (V)');axs[1].legend(fontsize=8);style(axs)
        para(fig,.244,f"低摆幅平均传播偏移{d['mean_delay_s']*1e12:.6f}ps。输出取min(ones)-max(zeros)={v['sens_swing_v']*1e3:.6f}mV，低于原250mV、达到10%边界225mV；8个符号均正确，4升/4降均完整测得。",9.2)
        para(fig,.124,'低摆幅边沿阈值按该测试中心样点的高/低平均电平定义，保留原分析器规则；最坏上/下沿7.742050/7.742701ps。没有增加输入振幅、移除50Ω/30fF或放宽功能计数。',9.1)
        save(pdf,fig)

        fig=frame('固定界限的数值精度对照',8,'两个瞬态从0.2ps/1e-6收紧至0.1ps/1e-7，gear2only；最终使用细步长轨迹。')
        rows=[]
        for key,q in c['metrics'].items():
            scale,unit=(1e12,'ps') if key.endswith('_s') else (1e3,'mW' if key.endswith('_w') else 'mV')
            rows.append([key.replace('prbs_','').replace('sens_','SENS_'),f"{q['baseline']*scale:.7g}",f"{q['refined']*scale:.7g}",f"{q['absolute_difference']*scale:.5g}",f"{q['maximum_difference']*scale:g} {unit}"])
        table(fig,[.07,.422,.86,.404],['复核量','0.2ps / 1e-6','0.1ps / 1e-7','绝对差','预设上限'],rows,[.29,.185,.185,.17,.17],7.7)
        para(fig,.36,'预设：眼高/低摆幅差≤0.5mV；抖动、DCD与四种最坏边沿时间差≤0.05ps；时间加权功耗差≤0.05mW；等级、功能检查保持。全部通过，最大眼高差48.269uV、低摆幅差30.078uV。',9.2)
        para(fig,.211,'37个独立标量从原PSF重算，与报告值一致。独立交越向量检查唯一匹配、样点范围与计数；原23组检查以仅TT输入调用，其中带宽与低摆幅输出为原门槛失败，明确保留。',9.2)
        para(fig,.09,'最终四组及两个瞬态基线均0错误/0警告；检查实际Spectre完成日志、输入快照及模型/LUT哈希。10实例28端子另用独立解析器核对，全部体端明确。',9.0)
        save(pdf,fig)

        fig=frame('失败迭代与最终精确网表',9,'保留AC成功但功能失败的候选；没有改变原采样算法来制造通过。')
        table(fig,[.07,.618,.86,.217],['阶段','参数变化','结果/取舍'],[
            ['初版','8mA / gmID8 / C15fF','BW8.654GHz，群延迟变化11.91ps'],
            ['提速','16mA / gmID4 / C30fF','无L时10.726GHz，输出L240pH后12.879GHz'],
            ['双端峰化','输入L300pH / 输出L240pH','BW23.593GHz；原PRBS/敏感性功能失败'],
            ['加大中和','C100fF，其他保持','BW23.471GHz；PRBS32错、敏感性8错'],
            ['最终','20mA / gmID3 / C15fF / 两端L200pH','延迟降至半UI内，全部功能通过；两项10%'],
        ],[.13,.39,.48],7.6)
        para(fig,.558,'早期绝对传播偏移约19ps，超过半UI；原分析器按最近过零搜索，在交替码下可能选到相邻边沿，造成眼中心错误。群延迟变化小和AC带宽通过都不能替代原瞬态功能检查。',9.0)
        text=(CASE/'circuit.scs').read_text();fig.text(.07,.426,text,fontsize=7.3,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.6)
        para(fig,.113,'所有电感为200pH、所有中和电容为15fF，均为正值理想无源；无行为源、开关或传递函数。每腿外部50Ω终端/100fF负载仅在测试台，DUT中不重复。',9.0)
        save(pdf,fig)

        fig=frame('复现入口、证据与适用边界',10,'图纸、PDF、源快照、数值对照与知识笔记绑定同一最终电路。')
        para(fig,.85,'复现（工程根目录，既有Bridge Python）：\npython scripts/case32_tx.py\npython scripts/confirm32.py\npython scripts/schematic32.py\npython scripts/audit32.py\npython scripts/review32.py\n重新生成报告后须重新逐页查看及核对完整总图。',9.0)
        para(fig,.579,'latest_results.json：29个边界、原/放宽结果及三种静态输入OP。\nverification_audit.json：37个独立标量与23组原检查。\nnumerical_confirmation.json：两种瞬态的细步长对照。\nsource/：原instruction、solution、benches和分析器冻结副本。\niteration_history.json：未采用候选、功能失败与原运行路径。\nschematic/：完整晶体管图、参数及端子连接映射。\nimplementation/：生成、审计和报告脚本快照。',8.8)
        para(fig,.344,'本次是给定负载下的28Gb/s单级CML标称验证；其余ss/ff配对点、失配、噪声、通道/封装、驱动静电防护、电感有限Q、版图面积及PEX未执行。理想电感获得的提速不能直接换算为实芯片性能。',9.2)
        para(fig,.19,'输入输出终端、共模、PWL边沿、PRBS7序列和验收窗口均未改变。严格计数防止缺失边沿冒充通过，时间加权功耗检查防止自适应采样偏差掩盖功耗。',9.0)
        para(fig,.095,'DUT SHA-256：\n'+r['circuit_sha256'],7.8)
        save(pdf,fig)
    subprocess.run(['pdfunite',str(body),str(CASE/'schematic/sheets.pdf'),str(out)],check=True)
    pages=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(out)],text=True),re.M)[1]);write_json(CASE/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(CASE/'latest_results.json'),circuit_sha256=sha(CASE/'circuit.scs'),sizing_sha256=sha(CASE/'sizing.json'),generated_at=now(),pages=pages,body_pages=10,schematic_pages=1,schematic_sheets_sha256=sha(CASE/'schematic/sheets.pdf'),render_review_pending=True));print(out)

if __name__=='__main__':make()
