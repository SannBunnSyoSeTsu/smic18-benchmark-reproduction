from review_pdf import *


def make31():
    case=ROOT/'cases/31-bottom-plate'
    r=json.loads((case/'latest_results.json').read_text());v=r['values']
    s=json.loads((case/'sizing.json').read_text())
    a=data(ROOT/r['run_dirs'][0],'tran.tran');t=a['time']
    confirm=json.loads((case/'numerical_confirmation.json').read_text())
    out=ROOT/'reports/31-bottom-plate-review.pdf'
    with PdfPages(out,metadata={'Title':'31 SMIC18差分底板采样器审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('31 | 差分底板采样器审查报告',1,'结论：双极性采样、保持隔离、相干频谱和全部外部源功耗均通过原nominal门槛。')
        para(fig,.863,'条件：SMIC18MMRF / tt / 1.8 V / 27°C；100 MHz时钟、50 ps源边沿、50 Ω时钟驱动；输入共模0.9 V。两只1 pF采样电容，三个1 pF自举电容；仅原厂HD逻辑、PDK MOS和正值电容。',9.5)
        specs=[('正输入采集误差','positive_acquisition_error_V',1e3,'mV'),('负输入采集误差','negative_acquisition_error_V',1e3,'mV'),('保持前正样本误差','hold_positive_capture_error_V',1e3,'mV'),('保持期间反向输入扰动','hold_isolation_shift_V',1e6,'uV'),('下一次负样本误差','negative_reacquisition_error_V',1e3,'mV'),('80点采样SFDR','sfdr_db',1,'dB'),('差分基波增益误差','gain_error',100,'%'),('存储电荷共模偏移','stored_common_mode_error_v',1e3,'mV'),('五个外部源总功耗','total_source_power_w',1e6,'uW')]
        rows=[]
        for label,key,k,unit in specs:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤'
            rows.append([label,f'{v[key]*k:.6g}']+[f'{sign}{g["limits"][tier]*k:.5g}' for tier in ['original','10pct','15pct']]+[unit])
        table(fig,[.07,.385,.86,.39],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.32,.17,.14,.14,.14,.09],8.4)
        para(fig,.332,'差分存储量严格按(vsp−vtopp)−(vsn−vtopn)计算，共模为两项之和的一半。不能以vsp−vsn替代，也不能把浮置电容端点对地电压当作共模误差。',9.5)
        para(fig,.234,f'额外检查四个测试副本中所有模拟管与HD MOS的端电压：最大|VGS|或|VGD|为{v["max_gate_terminal_voltage_V"]:.6f} V，最大|VDS|为{v["max_drain_source_voltage_V"]:.6f} V，均低于不放宽的1.98 V工程筛查线。该线不是PDK寿命或氧化层额定值声明。',9.5)
        para(fig,.118,'此报告覆盖原题全部nominal功能维度；其余八组FFT PVT、ss/ff保持测试、失配与PEX未执行。确定性SFDR没有包含热噪声，不能据此声称13位ENOB或SNDR。',9.3)
        save(pdf,fig)

        fig=page('采样拓扑、关断顺序与LUT尺寸',2,'先断开共模板，再断开信号输入；自举使信号开关的栅极跟随输入。')
        ax=fig.add_axes([.075,.605,.85,.255]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,5))
        for y,side in [(3.8,'p'),(1.4,'n')]:
            ax.text(.05,y,f'VIN{side.upper()}',va='center',fontsize=9)
            ax.plot([.8,1.4],[y,y],color=BLUE);ax.add_patch(Rectangle((1.4,y-.35),1.25,.7,fill=False,edgecolor=BLUE));ax.text(2.025,y,'MI'+side.upper(),ha='center',va='center',fontsize=9)
            ax.plot([2.65,4.3],[y,y],color=BLUE);ax.plot([4.3,4.3],[y-.35,y+.35],color=BLUE);ax.plot([4.5,4.5],[y-.35,y+.35],color=BLUE);ax.plot([4.5,6.1],[y,y],color=BLUE)
            ax.text(3.2,y+.2,'vs'+side,fontsize=9);ax.text(5,y+.2,'vtop'+side,fontsize=9);ax.text(4.1,y-.64,'1 pF',fontsize=9)
            ax.add_patch(Rectangle((6.1,y-.35),1.35,.7,fill=False,edgecolor=GREEN));ax.text(6.775,y,'MC'+side.upper(),ha='center',va='center',fontsize=9);ax.plot([7.45,9.3],[y,y],color=GREEN)
        ax.plot([9.3,9.3],[1.4,3.8],color=GREEN);ax.text(9.45,2.6,'VCM\n0.9 V',va='center',fontsize=9)
        ax.plot([5.7,5.7],[1.4,2.18],color=GREEN);ax.plot([5.7,5.7],[2.9,3.8],color=GREEN);ax.add_patch(Rectangle((5.13,2.18),1.14,.72,fill=False,edgecolor=GREEN));ax.text(5.7,2.54,'MTS',ha='center',va='center',fontsize=9)
        ax.text(.1,.2,'late → 自举VGp/VGn → MIP/MIN       early → 自举VGc → MCP/MCN/MTS',fontsize=9)
        labels={'input_n18':'MIP / MIN','common_n18':'MCP / MCN','boot_n18':'自举NMOS单位','boot_p18':'自举PMOS单位','top_equalizer_n18':'共模板连接MTS'}
        rows=[]
        for key,q in s['roles'].items():rows.append([labels[key],f'{q["rounded_W_um"]:g} / {q["L_um"]:g}',f'{q["gmid"]:g}',f'{q["Id_A"]*1e6:g}'])
        table(fig,[.07,.38,.86,.18],['器件角色','单位W/L (um)','初算gm/ID','LUT参考电流/uA'],rows,[.35,.25,.18,.22],8.8)
        para(fig,.336,'LUT选点均为VDS=0.9 V、VSB=0；查询只提供初始尺寸，实际开关在时变线性区和关断状态之间转换，表中电流不是电路中的固定偏置。自举NMOS中MPRE/MGTRK/MPVIN/MCASC/MPRGUARD为单位m=2，其余m=1。',9.5)
        para(fig,.221,'时钟链：INHDV4→INHDV4产生early；再经INHDV4→INHDV8产生late，lateb对地20 fF。每个自举驱动内再用两只INHDV4；共10个原厂HD反相器，全部尺寸和井连接保留。',9.5)
        para(fig,.116,'共模侧先关断，把主要关断误差置于固定共模电位；随后关闭信号侧。自举提高输入跟踪线性度，不能取消电荷注入、寄生电容和有限建立时间。第五页给出有效栅源波形。',9.5)
        save(pdf,fig)

        fig=page('双极性采集与真实保持隔离',3,'输入在8.0–8.1 ns从+0.8 V翻转至−0.8 V；仍须保存上一样本，下一拍才采负值。')
        held=lambda tag:a['vsp'+tag]-a['vtopp'+tag]-a['vsn'+tag]+a['vtopn'+tag]
        ax=fig.add_axes([.115,.59,.83,.265]);ax.plot(t*1e9,a['vinpH']-a['vinnH'],label='Differential input',color=GRAY);ax.plot(t*1e9,held('H'),label='Stored differential',color=BLUE);ax.set(xlabel='Time (ns)',ylabel='Differential voltage (V)',xlim=(0,22));ax.legend(fontsize=8);ax.grid(alpha=.2)
        vals=r['hold_observations_V']
        for when,y in zip([7.8,11.5,19.5],vals):ax.plot(when,y,'o',color=GREEN,ms=4);ax.annotate(f'{when:g} ns',(when,y),xytext=(when+.3,y+.12),fontsize=8)
        ax2=fig.add_axes([.115,.33,.36,.17]);mask=(t>=7.75e-9)&(t<=11.55e-9);ax2.plot(t[mask]*1e9,(held('H')[mask]-vals[0])*1e6);ax2.set(xlabel='Time (ns)',ylabel='Hold delta from 7.8 ns (uV)');ax2.grid(alpha=.2)
        ax3=fig.add_axes([.60,.33,.345,.17]);mask=(t>=26e-9)&(t<=30e-9)
        for tag,ref in [('P',.8),('N',-.8)]:ax3.plot(t[mask]*1e9,(held(tag)[mask]-ref)*1e3,label=tag)
        ax3.axvline(29,color=GRAY,ls='--',lw=.7);ax3.axhline(5,color=GRAY,ls=':',lw=.6);ax3.axhline(-5,color=GRAY,ls=':',lw=.6);ax3.set(xlabel='Time (ns)',ylabel='Acquisition error (mV)');ax3.legend(fontsize=8);ax3.grid(alpha=.2)
        for z in [ax,ax2,ax3]:z.tick_params(labelsize=8)
        rows=[[f'{when:g}',f'{y:.9f}',desc] for when,y,desc in zip([7.8,11.5,19.5],vals,['首次正样本','输入已反转但仍保持','下一拍负样本'])]
        table(fig,[.07,.178,.86,.102],['时刻/ns','存储差分/V','测量意义'],rows,[.2,.3,.5],8.8)
        para(fig,.133,f'7.8与11.5 ns之间的判定量为两次端点差：{v["hold_isolation_shift_V"]*1e6:.5f} uV。图中瞬时电容馈通完整保留；原合同没有把保持窗内峰值改成新的硬门槛。两路固定正/负输入在独立副本29 ns取样。',9.5)
        save(pdf,fig)

        _spectral_page(pdf,r)
        _protection_page(pdf,r,a,confirm)
        fig=page('精确网表、复现与证据',6,'电路、原始合同、LUT、HD来源、测试台和最终波形在项目目录保留哈希快照。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.863,body,fontsize=7.0,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.24)
        para(fig,.352,'bootstrap中的MPRE由VDD经PRE预充，新增MPRGUARD的栅接VDD、两通道端连接VG和PRE。MLIM/MBPP的PMOS体接CBT，要求独立井；HD单元的VNW/VPW始终接VDD/VSS。',9.2)
        para(fig,.248,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case31_bottom_plate.py --maxstep-ps 2.5\nPDF：同一Python运行 scripts/review_pdf.py 31\n最终运行：'+r['run_dirs'][0]+'\n'+r['run_dirs'][1],8.3)
        para(fig,.13,'原任务sky130-bottom-plate-sampler-pvt的instruction、reference和verifier已冻结。数值对照见numerical_confirmation.json；撤回的未保护自举版本和失败收敛日志保留为工程教训。没有改动PDK、HD原库或既有验证环境。',9.2)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(31,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out


def _spectral_page(pdf,r):
    v=r['values'];s=r['samples'];fig=page('相干频谱、增益与完整端口功耗',4,'直接调用冻结的上游stored/analyze_fft函数处理Spectre向量，保持80点、bin4和功耗定义。')
    tt=np.array(s['time_s'])*1e9;yy=np.array(s['differential_V']);spec=np.array(s['spectrum_amplitude_V'])
    ax=fig.add_axes([.115,.66,.83,.195]);ax.plot(tt,yy,'o-',ms=3,color=BLUE);ax.set(xlabel='Held sample time (ns)',ylabel='Stored differential (V)');ax.grid(alpha=.2)
    ax2=fig.add_axes([.115,.39,.83,.19]);bins=np.arange(1,40);db=20*np.log10(np.maximum(spec[bins]/spec[4],1e-15));ax2.vlines(bins*1.25,-200,db,color=BLUE,lw=1);ax2.plot(bins*1.25,db,'o',ms=3);ax2.set(xlabel='Sampled spectrum frequency (MHz)',ylabel='Amplitude (dBc)',ylim=(-200,5),xlim=(0,50));ax2.axhline(-80,color=GREEN,ls='--',lw=.7);ax2.grid(alpha=.2)
    for ax in [ax,ax2]:ax.tick_params(labelsize=8)
    keys=[('VDD','vdd_source_power_w'),('VCM','vcm_source_power_w'),('VINP','vinp_source_power_w'),('VINN','vinn_source_power_w'),('时钟源（50 Ω之前）','clock_source_power_w'),('合计','total_source_power_w')]
    table(fig,[.07,.165,.86,.17],['外部源','非负平均功率/uW'],[[label,f'{v[key]*1e6:.6f}'] for label,key in keys],[.65,.35],8.8)
    para(fig,.128,f'采样时刻89–879 ns，5 MHz输入每边0.4 V峰值，bin4；SFDR={v["sfdr_db"]:.4f} dB，基波幅度{spec[4]:.9f} V。功率窗80–880 ns，对每个源分别积分−V×I后取非负，再求和；时钟串联电阻消耗包含在源功率中。无窗函数，不计DC与Nyquist，非SNDR。',9.1)
    save(pdf,fig)


def _protection_page(pdf,r,a,confirm):
    v=r['values'];fig=page('自举保护、关断时序与数值复核',5,'频谱达标之外检查器件端差；绝对栅压高于VDD本身不足以判定保护是否有效。')
    t=a['time'];mask=(t>=6.85e-9)&(t<=7.8e-9);x=t[mask]*1e9
    ax=fig.add_axes([.115,.65,.83,.205]);ax.plot(x,(a['XH.vgc']-a['vcmH'])[mask],label='Common switch VGS');ax.plot(x,(a['XH.vgp']-a['vinpH'])[mask],label='Input+ switch VGS');ax.plot(x,a['clkH'][mask],label='External clock',color=GRAY,ls='--');ax.set(xlabel='Time (ns)',ylabel='Gate drive / clock (V)');ax.legend(fontsize=8);ax.grid(alpha=.2);ax.tick_params(labelsize=8)
    rows=[['传输门基线','56.7456','0.563185','频谱失败'],['未保护自举','97.0926','0.471965','MPRE |VGS|=2.893 V，撤回'],['保护自举/5 ps',f'{confirm["coarse_values"]["sfdr_db"]:.5f}',f'{confirm["coarse_values"]["gain_error"]*100:.6f}','通过，作为精度对照'],['保护自举/2.5 ps',f'{v["sfdr_db"]:.5f}',f'{v["gain_error"]*100:.6f}','最终结果']]
    table(fig,[.07,.435,.86,.14],['方案','SFDR/dB','增益误差/%','判定'],rows,[.26,.17,.21,.36],8.5)
    para(fig,.397,'初始自举在CLK下降而VG仍被抬高时，把接在CLK与VG之间的预充管暴露于2.893 V端差。最终把MPRE源端改接PRE，增加栅接VDD的串联保护管MPRGUARD；保留旧运行，不能把旧频谱pass继续当作可交付实现。',9.3)
    para(fig,.287,f'最终四个测试副本共{len(r["terminal_extrema"])}条MOS检查记录，最大栅至通道端差{v["max_gate_terminal_voltage_V"]:.6f} V，漏源差{v["max_drain_source_voltage_V"]:.6f} V。1.98 V是不放宽的工程检查界限，既未证明长期可靠性，也没有执行其他PVT。',9.3)
    para(fig,.181,f'相同电路缩步5→2.5 ps，reltol=2e−6、iabstol=1e−12、vabstol=1e−9不变；SFDR变化{confirm["absolute_changes"]["sfdr_db"]:.6g} dB，增益误差变化{confirm["absolute_changes"]["gain_error"]*100:.6g}个百分点。两次均通过原门槛，最终使用细步长数据。',9.3)
    para(fig,.081,'Spectre在部分HD/自举管内部源节点报告SPECTRE-16780局部LTE放宽，日志完整保留；上述同电路精度对照用于检验关键结果稳定性。没有把警告删去或称作无警告运行。',9.1)
    save(pdf,fig)
