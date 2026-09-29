"""Case 23 review PDF; measurements always read from actual PSF-backed results."""
from review_pdf import *


def make23():
    case=ROOT/'cases/23-resistor-dac'
    r=json.loads((case/'latest_results.json').read_text())
    s=json.loads((case/'sizing.json').read_text())
    nc=json.loads((case/'numerical_confirmation.json').read_text())
    runs=[ROOT/x for x in r['run_dirs']]
    dr,dc,do=[data(x,'tran.tran') for x in runs]
    out=ROOT/'reports/23-resistor-dac-review.pdf'
    with PdfPages(out,metadata={'Title':'23 SMIC18 五位开关电阻DAC审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('23 | 五位开关电阻 DAC 审查',1,'结论：完整确定性nominal检查达到原门槛，无需10%或15%放宽。')
        para(fig,.846,'条件：SMIC18MMRF tt + res_tt，1.8 V、27°C；输出负载1 pF，200 MS/s。五路数字输入均经原厂HD两级有限强度缓冲，50 ps命令边沿与原代码/时间窗一致。',9.6)
        info=[('最大端点拟合INL','inl_lsb_max',1,'LSB'),('最大绝对DNL','dnl_lsb_max',1,'LSB'),
          ('码0绝对误差','zero_code_error_V',1e3,'mV'),('码31绝对误差','full_scale_error_V',1e3,'mV'),
          ('DUT平均功耗','power_avg_W',1e6,'uW'),('最坏大进位建立','settling_time_s',1e9,'ns'),
          ('最坏窗口末误差','settling_end_error_lsb_max',1,'LSB'),('最坏越界峰值','excursion_lsb_max',1,'LSB'),
          ('六码最大输出电阻','rout_max_Ohm',1e-3,'kOhm')]
        rows=[]
        for name,key,k,u in info:
            g=r['gates'][key]
            rows.append([name,f"{g['value']*k:.5f}",f"≤{g['limits']['original']*k:.4g}",f"≤{g['limits']['10pct']*k:.4g}",f"≤{g['limits']['15pct']*k:.4g}",u])
        table(fig,[.07,.421,.86,.355],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.17,.14,.14,.14,.12],8.3)
        table(fig,[.07,.249,.86,.123],['功能维度','实际覆盖','不放宽的功能检查'],[
          ['200 MS/s爬码','全部32码 / 31步','全部正步长；160个输入位采样正确'],
          ['双向大进位','3↔4、7↔8、15↔16','6条有限最后入带时刻 / 末端误差'],
          ['输出电阻','0、4、15、16、28、31','6点均为正；向电源范围内施加5 uA']],[.23,.29,.48],8.6)
        driver=r['ramp']['external_driver_power_avg_W']*1e6;total=driver+r['values']['power_avg_W']*1e6
        para(fig,.204,f'最小步长53.250 mV，严格单调。功耗积分2.5–162.5 ns，只计DUT VDD，沿用原验证器；外部输入缓冲另耗约{driver:.3f} uW，两者总和约{total:.3f} uW。',9.3)
        para(fig,.107,'本次为确定性nominal迁移，不包含其余10个PVT点、8个固定种子局部失配回归、Monte Carlo良率和版图寄生。10%/15%只列数值边界；未延长5 ns代码或观察窗口。',9.3)
        save(pdf,fig)

        fig=page('电路连接、权重与 LUT 尺寸',2,'32个同尺寸工艺电阻：五组二进制权重支路，加一个恒接地的LSB终端。')
        ax=fig.add_axes([.07,.600,.86,.278]);ax.axis('off');ax.set(xlim=(0,10.5),ylim=(-.8,5.8))
        for bit in range(5):
            y=5-bit
            ax.text(0,y,f'b{bit}',fontsize=9,va='center')
            ax.plot([.38,.9],[y,y],color=BLUE)
            ax.add_patch(Rectangle((.9,y-.28),1.22,.56,fill=False,edgecolor=BLUE))
            ax.text(1.51,y,s['receiver_cells'][bit],fontsize=7.4,ha='center',va='center')
            ax.plot([2.12,2.6],[y,y],color=BLUE);ax.text(2.26,y+.15,f'nb{bit}',fontsize=7)
            ax.add_patch(Rectangle((2.6,y-.34),2.25,.68,fill=False,edgecolor=GREEN))
            ax.text(3.725,y,'n18→VSS / p18→VDD\n共栅nb，m='+str(2**bit),fontsize=7.6,ha='center',va='center')
            ax.plot([4.85,5.65],[y,y],color=BLUE);ax.text(5,y+.15,f'sw{bit}',fontsize=7)
            ax.add_patch(Rectangle((5.65,y-.28),1.62,.56,fill=False,edgecolor=BLUE))
            ax.text(6.46,y,f'{2**bit} × Runit 并联',fontsize=8,ha='center',va='center')
            ax.plot([7.27,8.2],[y,y],color=BLUE)
        ax.plot([8.2,8.2],[0,5],color=BLUE);ax.plot([8.2,9.3],[2.5,2.5],color=BLUE);ax.text(9.4,2.5,'vout',fontsize=10,va='center')
        ax.add_patch(Rectangle((5.65,-.28),1.62,.56,fill=False,edgecolor=BLUE));ax.text(6.46,0,'1 × Runit',fontsize=8,ha='center',va='center')
        ax.plot([4.7,5.65],[0,0],color=BLUE);ax.text(4.2,0,'VSS',fontsize=8,va='center');ax.plot([7.27,8.2],[0,0],color=BLUE)
        ax.text(.9,-.64,'DUT引脚：vss b0 b1 b2 b3 b4 vdd vout；所有MOS阱接相应电源轨。',fontsize=8)
        rows=[]
        for d in ['n18','p18']:
            q=s['roles'][d];rows.append([d,f"{q['rounded_W_um']:.2f} / 0.18",'6',f"{q['id_w_Apm']:.3f}",f"{q['Vgs_V']:.4f}",f"{q['ft_Hz']/1e9:.2f}"])
        table(fig,[.07,.453,.86,.104],['模拟开关单位','W/L (um)','gm/ID','ID/W (uA/um)','VGS表点/V','fT表点/GHz'],rows,[.2,.2,.12,.2,.14,.14],8.3)
        para(fig,.413,'LUT：27°C、VDS=0.9 V、参考W=10 um。选gm/ID=6、参考ID=200 uA，得到单位Wn=3.24 um、Wp=9.08 um。每位m=1/2/4/8/16；最大有效Wp=145.28 um由合法单位并联实现。',9.3)
        para(fig,.321,'饱和LUT仅用于初始几何，200 uA不是电路偏置。实际开关由0/1.8 V驱动，导通时处于线性区；32码实测最坏开关轨压降约14.20 mV。单位开关尺寸与电阻电导同权重缩放。',9.2)
        para(fig,.229,'每个Runit采用rpposab_3t，W=1 um、L=96 um，第三端接VSS。32个相同单位保留蚀刻、电压/温度系数与基底电容。Runit手算约31.611 kΩ，Rout≈Runit/32≈987.84 Ω；实测范围986.74–993.87 Ω。',9.2)
        para(fig,.133,'理想关系：Vout=(Σ 2^i·bi)/32·VDD。终端的一份电导保证分母32。全码平均静态功耗手算约546 uW，实测含内部数字翻转约645 uW。DUT无理想R/C、行为源或理想开关。',9.2)
        save(pdf,fig)

        fig=page('完整 32 码：动态爬码与线性度',3,'每码5 ns，在7+5k ns采样；端点拟合与绝对端点误差同时检查。')
        codes=r['ramp']['codes'];ks=np.arange(32);samples=np.array([q['output_V'] for q in codes])
        ax=fig.add_axes([.11,.616,.83,.242]);ax.plot(dr['time']*1e9,dr['vout'],color=BLUE,lw=.85,label='Actual output');ax.plot([q['sample_s']*1e9 for q in codes],samples,'o',ms=3,color=GREEN,label='32 samples')
        ax.set(xlabel='Time (ns)',ylabel='Output (V)',xlim=(0,162.5),ylim=(-.04,1.83));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='upper left')
        ax1=fig.add_axes([.11,.301,.365,.213]);ax2=fig.add_axes([.58,.301,.365,.213])
        ax1.plot(ks,[q['inl_LSB'] for q in codes],'o-',ms=3,color=BLUE);ax2.plot(ks[1:],[q['dnl_LSB'] for q in codes[1:]],'o-',ms=3,color=GREEN)
        for ax,label in [(ax1,'Endpoint-fit INL (LSB)'),(ax2,'DNL (LSB)')]:
            ax.set(xlabel='Code',ylabel=label,xlim=(0,31),ylim=(-.275,.275));ax.axhline(.25,color=GRAY,ls='--',lw=.8);ax.axhline(-.25,color=GRAY,ls='--',lw=.8);ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        para(fig,.235,'LSBfit=(V31−V0)/31=56.13983 mV；INL[k]=(V[k]−V[0])/LSBfit−k；DNL[k]=(V[k]−V[k−1])/LSBfit−1。理想LSB仍为56.25 mV，绝对码0/31目标保持0 V与1.74375 V。',9.2)
        para(fig,.141,'动态码31误差3.299 mV，包含有限建立时间；独立长驻留输出电阻测试中，未加载码31约1.743296 V，距理想1.743750 V约0.454 mV。二者测量时间不同，不能混用静态端点替代200 MS/s验收。',9.2)
        para(fig,.073,'命令边沿50 ps，保持原PULSE/PWL。输入驱动采用原厂INHDV3→INHDV32两级缓冲，保留单独VDRV供电；DUT内数字反相同样采用HD。',8.8)
        save(pdf,fig)

        fig=page('六种大进位：建立与峰值越界',4,'以命令时刻为零；理想目标码与±0.25 LSB带均不随端点拟合移动。')
        trs=r['major_carry']['transitions']
        for i,q in enumerate(trs):
            ax=fig.add_axes([.11+(i%2)*.465,.707-(i//2)*.205,.365,.140])
            tm=dc['time']-q['trigger_s'];sel=(tm>=-.6e-9)&(tm<=5.01e-9)
            target=q['stop_code'];ax.plot(tm[sel]*1e9,dc['vout'][sel]/(.05625),lw=1,color=BLUE)
            ax.axhspan(target-.25,target+.25,color=GREEN,alpha=.12);ax.axhline(q['start_code'],color=GRAY,ls=':',lw=.8)
            ax.axvline(q['settling_time_s']*1e9,color=GREEN,ls='--',lw=.8);ax.set(title=f"{q['start_code']} -> {q['stop_code']}",xlabel='After command (ns)',ylabel='Output / ideal LSB',xlim=(-.5,5))
            ax.grid(alpha=.2);ax.tick_params(labelsize=7);ax.xaxis.label.set_size(7);ax.yaxis.label.set_size(7);ax.title.set_size(9)
        rows=[[f"{q['start_code']}→{q['stop_code']}",f"{q['settling_time_s']*1e9:.4f}",f"{q['end_error_LSB']:.5f}",f"{q['excursion_LSB']:.5f}"] for q in trs]
        table(fig,[.07,.087,.86,.121],['跃迁','最后入带 / ns','4.99 ns误差 / LSB','指令两电平外峰值 / LSB'],rows,[.15,.26,.27,.32],8.1)
        para(fig,.241,'最坏16→15：3.0839 ns、峰值0.86573 LSB；六条波形均仅一次入带交叉。上行15→16不能替代下行验收。',8.7)
        save(pdf,fig)

        fig=page('负载扰动、数值对照与复现',5,'输出电阻保留原六个代表代码及向电源范围内的5 uA扰动方向。')
        rows=[]
        for q in r['output_resistance']['codes']:
            rows.append([q['code'],'注入' if q['direction']=='inject' else '吸收',f"{q['unloaded_V']:.7f}",f"{q['loaded_V']:.7f}",f"{q['rout_Ohm']:.4f}"])
        table(fig,[.07,.672,.86,.178],['代码','5 uA方向','未加载/V','加载/V','Rout/Ω'],rows,[.12,.18,.23,.23,.24],8.8)
        ax=fig.add_axes([.11,.422,.83,.180]);ax.plot(do['time']*1e9,do['vout'],lw=1,color=BLUE)
        for i in range(6):ax.axvspan(i*30+15,i*30+30,color=GREEN,alpha=.10)
        ax.set(xlabel='Time (ns)',ylabel='Output (V)',xlim=(0,180));ax.grid(alpha=.2)
        para(fig,.361,'每个代码驻留30 ns：前15 ns无负载，后15 ns施加5 uA；采样于本窗口14 ns和29 ns。码0取(Vloaded−Vunloaded)/5 uA，其余取相反电压差。保留整个扰动波形，非用1/gds替代外部测试。',9.2)
        para(fig,.260,f"数值对照：三类bench步长均缩小5倍（最终2/1/5 ps），reltol由2e−5收紧到2e−6。全部指标最大相对变化{nc['max_relative_metric_change']*100:.5f}%。ramp/Rout仍有SPECTRE-16780局部LTE提示；没有模型尺寸越界，结论稳定。",9.1)
        para(fig,.153,'复现：在smic18_benchmark_repro目录执行\n/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case23_dac.py --refined\nPDF：同一Python执行 scripts/review_pdf.py 23',8.6)
        para(fig,.068,'源任务与冻结instruction/verifier/bench：cases/23-resistor-dac/source/。失配统计与其他PVT点未执行；本次测得的单调性不能代表布局后匹配或良率。',8.9)
        save(pdf,fig)

        fig=page('完整 DUT 网表与证据路径',6,'所有D/G/S/B、数字单元端口、并联数、电阻单位与基底连接均可逐行核对。')
        body='\n'.join(line for line in (case/'circuit.scs').read_text().splitlines() if not line.startswith('//'))
        fig.text(.073,.858,body,fontsize=7.25,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.26)
        para(fig,.209,'HD单元保持原厂内部W/L和模型，定义见hd_cells.scs及manifest。所有include位于bench层；冻结inputs中的电路+HD文件构成实际运行闭包。LUT与模型完整SHA256见sizing.json、各run.json。',8.9)
        para(fig,.130,'最终实测运行（每目录均有inputs、run.json、output/bench.raw和测量JSON）：\n'+'\n'.join(r['run_dirs']),8.0)
        para(fig,.047,'电路SHA256：'+sha(case/'circuit.scs'),7.2)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(23,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out


if __name__=='__main__':print(make23())
