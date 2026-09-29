from review_pdf import *

def make20():
    case=ROOT/'cases/20-mux';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());run=ROOT/r['run_dir'];a=data(run,'ac.ac');v=r['values'];out=ROOT/'reports/20-mux-review.pdf'
    with PdfPages(out,metadata={'Title':'20 SMIC18 八选一模拟复用器审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('20 | 八选一模拟复用器审查',1,'结论：3共模×8选择码×8独立输入传输，全部原nominal指标通过。')
        para(fig,.864,'条件：SMIC18MMRF / tt / 1.8 V / 40°C。40°C沿用本题明确给出的nominal行。每个模拟输入、选择位、AVDD均经50 Ω驱动；AVSS按原bench接理想地，输出负载1 pF。')
        rows=[]
        for label,key,k,u in [('选通DC增益绝对误差','selected_gain_error_dB',1,'dB'),('最坏未选通DC增益','worst_off_dc_dB',1,'dB'),('最坏未选通1MHz增益','worst_off_1mhz_dB',1,'dB'),('最小选通带宽','min_bandwidth_Hz',1e-6,'MHz'),('最大AVDD电流','max_supply_current_A',1e6,'uA')]:
            g=r['gates'][key];sign='≥' if g['sense']=='min' else '≤';rows.append([label,f"{g['value']*k:.6g}",f"{sign}{g['limits']['original']*k:.4g}",f"{sign}{g['limits']['10pct']*k:.4g}",f"{sign}{g['limits']['15pct']*k:.4g}",u])
        table(fig,[.07,.542,.86,.23],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.32,.17,.135,.135,.14,.10],8.1)
        rows=[]
        for cm in [0,.9,1.8]:
            qs=[q for q in r['states'] if q['common_mode_V']==cm]
            rows.append([cm,'8 / 64',f"{min(q['bandwidth_Hz'] for q in qs)/1e6:.4f}",f"{max(q['worst_off_1mhz']['gain_1mhz_dB'] for q in qs):.3f}"])
        table(fig,[.07,.342,.86,.134],['共模/V','状态/独立传输数','最小BW/MHz','最坏串扰@1MHz/dB'],rows,[.17,.30,.25,.28],8.7)
        para(fig,.291,'总计24个选通状态、24条选通传输、168条未选通传输。每条只激励自己的输入源，另外7路AC为0；没有将8路同时激励的和当作独立隔离结果。',9.5)
        para(fig,.181,'所有8路输入在每个状态共享同一DC共模。选通近DC增益在1 mHz测量；带宽相对自身该点下降3.000 dB。门限没有因中间电平Ron较大而改变。',9.3)
        para(fig,.087,'本次不包含其他4个代表性PVT行、不同输入DC电平组合、切换瞬态、失真、噪声、失配和版图寄生；本例的静态隔离不代表动态切换无串扰。',9.2)
        save(pdf,fig)
        fig=page('三级传输门树与HD控制',2,'模拟开关依据目标PDK LUT起步，数字反相信号使用原厂HD单元。')
        ax=fig.add_axes([.07,.608,.86,.265]);ax.axis('off');ax.set(xlim=(0,10),ylim=(-.5,7.8))
        for i in range(8):ax.text(0,7-i,f'VIN{i}',va='center',fontsize=8);ax.plot([.8,2],[7-i,7-i],color=BLUE)
        for j in range(4):
            y=6.5-2*j;ax.add_patch(Rectangle((2,y-.6),1.25,1.2,fill=False,edgecolor=BLUE));ax.text(2.625,y,'2:1\nS0',ha='center',va='center',fontsize=8)
            ax.plot([3.25,4],[y,y],color=BLUE)
        for j in range(2):
            y=5.5-4*j;ax.add_patch(Rectangle((4.5,y-.8),1.25,1.6,fill=False,edgecolor=BLUE));ax.text(5.125,y,'2:1\nS1',ha='center',va='center',fontsize=8)
            for yy in [y-1,y+1]:ax.plot([4,4.5],[yy,y+np.sign(yy-y)*.5],color=BLUE)
            ax.plot([5.75,6.5],[y,y],color=BLUE)
        ax.add_patch(Rectangle((7,2.3),1.25,2.4,fill=False,edgecolor=BLUE));ax.text(7.625,3.5,'2:1\nS2',ha='center',va='center',fontsize=9)
        ax.plot([6.5,7],[5.5,4.2],color=BLUE);ax.plot([6.5,7],[1.5,2.8],color=BLUE);ax.plot([8.25,9.4],[3.5,3.5],color=BLUE);ax.text(9.5,3.5,'VO',va='center',fontsize=9)
        rows=[['n18模拟开关','1.46 / 0.36','10','20 uA'],['p18模拟开关','6.08 / 0.36','10','20 uA'],['INHDV0 ×3','原厂W/L','不重新设计','6只原厂MOS']]
        table(fig,[.07,.425,.86,.123],['角色','W/L (um)','初始gm/ID','LUT参考电流/说明'],rows,[.29,.22,.19,.30],8.7)
        rows=[[q['common_mode_V'],f"{q['stage_Ron_Ohm'][0]:.2f}",f"{q['path_Ron_Ohm']:.2f}"] for q in r['on_resistance']]
        table(fig,[.07,.247,.86,.123],['共模/V','单级Ron/Ω','选通3级总Ron/Ω'],rows,[.22,.36,.42],9)
        para(fig,.196,'每个2:1由两组互补传输门构成，总共14组、28只模拟MOS；选中路径串联3组。3个INHDV0产生选择反相，原厂n18/p18尺寸及模型未改；阱分别接AVDD/AVSS。',9.4)
        para(fig,.092,'gm/ID饱和表只提供初始几何，表征温度27°C；实际验证为40°C。开关在VDS≈0的线性区，Ron取1/(gds,n+gds,p)，不用饱和余量或零电流下gm/ID验收开关。',9.2)
        save(pdf,fig)
        fig=page('完整选择矩阵与频率响应',3,'矩阵行是选择码，列是被独立激励的输入；对角为选通路径。')
        ax1=fig.add_axes([.12,.525,.35,.30]);ax2=fig.add_axes([.59,.525,.35,.30])
        for ci,cm in enumerate([0,.9,1.8]):
            hs=abs(a[f'vo{ci}_0_0']);ax1.semilogx(a['freq'],20*np.log10(np.maximum(hs,1e-300)),label=f'VCM={cm:g}V')
            qs=[q for q in r['states'] if q['common_mode_V']==cm];worst=max(qs,key=lambda q:q['worst_off_1mhz']['gain_1mhz_dB'])['worst_off_1mhz'];off=abs(a[f"vo{ci}_{worst['select']}_{worst['excited_input']}"])
            ax2.semilogx(a['freq'],20*np.log10(np.maximum(off,1e-300)),label=f'VCM={cm:g}V')
        ax1.set(xlabel='Frequency (Hz)',ylabel='Selected gain (dB)',xlim=(1e3,1e9),ylim=(-35,1));ax2.set(xlabel='Frequency (Hz)',ylabel='Unselected gain (dB)',xlim=(1e-3,1e8),ylim=(-190,-60));ax2.axhline(-80,color=GRAY,ls='--')
        for ax in [ax1,ax2]:ax.grid(which='both',alpha=.2);ax.legend(fontsize=7);ax.tick_params(labelsize=8)
        for ci,cm in enumerate([0,.9,1.8]):
            ax=fig.add_axes([.095+ci*.295,.22,.24,.20]);mat=np.empty((8,8))
            for q in r['transfers']:
                if q['common_mode_V']==cm:mat[q['select'],q['excited_input']]=q['gain_1mhz_dB']
            im=ax.imshow(mat,vmin=-170,vmax=0,cmap='viridis',origin='lower');ax.set(title=f'VCM={cm:g}V, 1MHz',xlabel='Excited input',ylabel='Select');ax.set_xticks(range(8));ax.set_yticks(range(8));ax.tick_params(labelsize=7)
        cax=fig.add_axes([.13,.153,.75,.013]);cb=fig.colorbar(im,cax=cax,orientation='horizontal');cb.set_label('Transfer magnitude (dB)',fontsize=8);cb.ax.tick_params(labelsize=7)
        para(fig,.079,'最坏1MHz串扰在VCM=0 V，S=7、激励VIN3：−117.016 dB。矩阵共192条实际AC响应；每条均保留1 mHz至1 GHz原始复数数据。',9)
        save(pdf,fig)
        fig=page('精确电路、范围与复现',4,'模拟路径只有PDK MOS；HD反相器定义另存hd_cells.scs并冻结在运行快照。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.858,body,fontsize=7.35,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.4)
        para(fig,.494,'工程认识：互补传输门能传输两轨附近电平，但Ron并不恒定；中点每级约1.974 kΩ，三段约5.923 kΩ，加外部源电阻与寄生后带宽24.97 MHz，为本例最差共模。不能只在0 V或VDD测试导通。',9.3)
        para(fig,.369,'数字控制采用HD，模拟传输门仍按其开关角色选几何。此电路没有内部理想R/C、理想开关或行为源；50 Ω和1 pF都是外部合同。静态电源电流0.137 nA只代表本次确定性模型，不包含时钟切换功耗。',9.3)
        para(fig,.252,'原验证器把公开deck的db(v(...))改为mag(v(...))后再计算dB；本例直接保留有限线性幅度再转换。带宽采用幅度×10^(−3/20)，未照抄公开deck中未替换的dB乘法。',9)
        para(fig,.158,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python\n scripts/case20_mux.py；PDF：scripts/review_pdf.py 20\n最终运行：'+r['run_dir'],8.4)
        para(fig,.074,'原任务：sky130-analog-input-mux-8to1-pvt。总覆盖24个nominal状态；其他代表性PVT行、动态切码和版图效果未验证。',8.8)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=4,render_review_pending=True))
    update_case(20,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
