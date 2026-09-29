from review_pdf import *

def make47():
    case=ROOT/'cases/47-charge-pump';r=json.loads((case/'latest_results.json').read_text());s=json.loads((case/'sizing.json').read_text());v=r['values'];t=data(ROOT/r['run_dirs'][1],'tran.tran');c=r['dc_curves'];out=ROOT/'reports/47-charge-pump-review.pdf'
    with PdfPages(out,metadata={'Title':'47 SMIC18 PLL电荷泵审查报告','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('47 | PLL 电荷泵审查报告',1,'结论：DC四状态、宽/窄脉冲、重叠电荷与开关速度全部原nominal通过。')
        para(fig,.861,'条件：SMIC18MMRF / tt / 1.8 V / 27°C，唯一外部模拟参考25 uA。输出0.45–1.15 V检查电流精度，0.30–1.35 V检查关断漏电；瞬态输出钳位0.9 V，控制上/下沿均200 ps。',9.4)
        specs=[('UP绝对电流误差','up_accuracy_error_fraction',100,'%'),('DN绝对电流误差','dn_accuracy_error_fraction',100,'%'),('UP平坦度','up_flatness_fraction',100,'%'),('DN平坦度','dn_flatness_fraction',100,'%'),('UP/DN匹配误差','matching_error_fraction',100,'%'),('两路低/最大漏电','off_current_max_A',1e9,'nA'),('两路高/净电流','both_current_max_A',1e6,'uA'),('UP 10ns电荷误差','up_wide_charge_error_fraction',100,'%'),('DN 10ns电荷误差','dn_wide_charge_error_fraction',100,'%'),('UP 1ns电荷误差','up_narrow_charge_error_fraction',100,'%'),('DN 1ns电荷误差','dn_narrow_charge_error_fraction',100,'%'),('重叠净电荷','overlap_charge_C',1e15,'fC'),('最坏开启时间','dn_turn_on_s',1e12,'ps'),('最坏关断时间','up_turn_off_s',1e12,'ps'),('平均VDD功耗','power_W',1e6,'uW')]
        rows=[]
        for name,key,k,u in specs:
            g=r['gates'][key];rows.append([name,f"{v[key]*k:.5g}"]+[f"≤{g['limits'][tier]*k:.4g}" for tier in ['original','10pct','15pct']]+[u])
        table(fig,[.07,.268,.86,.51],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.30,.18,.14,.14,.14,.10],8.15)
        para(fig,.226,'UP电流49.3352–49.3390 uA；DN为49.3133–49.3296 uA。所有43个DC点、其中29个合规点均保留，匹配按原0.45/0.90/1.15 V三点验收；全29点的最坏匹配也为0.05138%。',9.4)
        para(fig,.121,'没有运行其他PVT或20个tt_mm固定种子；不宣称随机匹配、PLL杂散或锁定性能。开关速度参考时刻与脉冲电荷归一化见第4页，不能将本表延迟直接当作逻辑门传播延迟。',9.4)
        save(pdf,fig)

        fig=page('电流转向、复制偏置与尺寸',2,'主电流始终存在，低控制状态把电流转向内部dummy支路。')
        ax=fig.add_axes([.07,.61,.86,.255]);ax.axis('off');ax.set(xlim=(0,10),ylim=(0,5))
        boxes=[(.1,1.3,2.3,2.8,'IREF 25 uA\nNMOS单位镜\n级联偏置\nPMOS复制支路'),(3.1,3.1,2.4,1.45,'VDD → MPM/MPC\nPMOS电流源+级联'),(3.1,.3,2.4,1.45,'MNC/MNM → VSS\nNMOS级联+电流源'),(6.1,3.1,1.6,1.45,'UP转向\nMSUP/MSDU'),(6.1,.3,1.6,1.45,'DN转向\nMSDN/MSDD')]
        for x,y,w,h,label in boxes:
            ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor=BLUE));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=8)
        for y in [1.025,3.825]:
            ax.annotate('',xy=(3.1,y),xytext=(2.4,2.5),arrowprops=dict(arrowstyle='->',color=GRAY));ax.plot([5.5,6.1],[y,y],color=BLUE)
            ax.plot([7.7,8.2,8.2],[y,y,2.5],color=BLUE)
        ax.plot([8.2,9.5],[2.5,2.5],color=BLUE);ax.text(9,2.72,'VOUT',fontsize=9)
        ax.plot([6.9,6.9,9],[4.55,4.9,4.9],color=GREEN);ax.text(9,4.9,'wu负载',fontsize=8,va='center')
        ax.plot([6.9,6.9,9],[.3,.02,.02],color=GREEN);ax.text(9,.02,'wd负载',fontsize=8,va='center')
        rows=[]
        labels={'n_mirror_unit':'NMOS镜单位','p_mirror_unit':'PMOS镜单位','n_cascode_unit':'NMOS级联单位','p_cascode_unit':'PMOS级联单位','n_cascode_bias':'NCB偏置二极管','p_cascode_bias':'PCB偏置二极管','n_switch':'DN转向管 ×2','p_switch':'UP转向管 ×2','up_dummy_diode':'wu二极管','dn_dummy_follower':'wd源跟随'}
        for name,q in s['roles'].items():rows.append([labels[name],f"{q['rounded_W_um']:g} / {q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"])
        table(fig,[.07,.273,.86,.295],['器件角色','单位W/L (um)','初始gm/ID','LUT单位电流/uA'],rows,[.33,.27,.19,.21],8.4)
        para(fig,.232,'并联倍数：MN0=2；MN1/MN2=1；MNM/MNC=4；MP0=2.5；MPM=10；MPC=4；复制级联MPC0/MNC1=1。单位W均未超过100 um模型上限。UP/UPD/DN反相器为原厂INHDV8/2/4。',9.2)
        para(fig,.118,'偏置滤波：vbp/vbpc/vbnc各1 pF，iref 0.8 pF；dummy负载各0.4 pF，nc/nd各30 fF。DUT只有PDK MOS和正值电容，未加入理想电阻或内部激励源。精确连接见第5页。',9.2)
        save(pdf,fig)

        fig=page('静态合规、匹配与电压余量',3,'输出由外部电压源钳位并测其支路电流；UP为正，DN取吸入电流的绝对方向。')
        xx=np.array(c['output_V']);u=np.array(c['up_A']);dn=np.array(c['dn_A'])
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.13,right=.95,bottom=.39,top=.85,hspace=.48,wspace=.43)
        axs[0,0].plot(xx,u*1e6,label='UP');axs[0,0].plot(xx,dn*1e6,label='DN');axs[0,0].set(ylabel='Current (uA)',xlabel='VOUT (V)',ylim=(49.1,49.5));axs[0,0].legend(fontsize=8)
        axs[0,1].plot(xx,(u-dn)/50e-6*100);axs[0,1].set(ylabel='UP-DN / 50uA (%)',xlabel='VOUT (V)')
        axs[1,0].plot(xx,np.array(c['off_A'])*1e12);axs[1,0].set(ylabel='Both low net (pA)',xlabel='VOUT (V)')
        axs[1,1].plot(xx,np.array(c['both_A'])*1e9);axs[1,1].set(ylabel='Both high net (nA)',xlabel='VOUT (V)')
        for ax in axs.flat:ax.grid(alpha=.2);ax.tick_params(labelsize=8);ax.axvspan(.45,1.15,color=GREEN,alpha=.07)
        rows=[]
        for label,key in [('UP主镜 MPM','U.MPM'),('UP级联 MPC','U.MPC'),('DN主镜 MNM','D.MNM'),('DN级联 MNC','D.MNC')]:
            q=r['compliance_saturation_margins'][key];rows.append([label,f"{q['min_saturation_margin_V']*1e3:.3f}",f"{q['output_V']:.2f}"])
        table(fig,[.07,.205,.86,.13],['合规范围内器件','最小 |VDS|−|VDSAT| / mV','出现的VOUT/V'],rows,[.31,.43,.26],8.8)
        para(fig,.16,'参考MN0的VDS约0.5335 V，主镜约0.255 V；漏压差使电流较理想50 uA低约1.37%。复制支路与输出支路维持相近电流密度和主镜漏压，因此UP/DN匹配优于各自绝对精度。',9.3)
        para(fig,.084,'最紧余量在低端DN级联，仅58.16 mV；它支持本次nominal工作点，不构成跨PVT证明。转向开关在线性区是其正常用途，不能套用电流源饱和判据。',9.1)
        save(pdf,fig)

        fig=page('窄脉冲、重叠电荷与延迟定义',4,'瞬态0–220 ns，最大步长/采样间隔2 ps；开启从输入上升开始计，关断从下降结束计。')
        ax1=fig.add_axes([.11,.61,.83,.245]);ax2=fig.add_axes([.11,.355,.36,.18]);ax3=fig.add_axes([.59,.355,.36,.18])
        tt=t['time'];ii=t['VOUT:p'];ax1.plot(tt*1e9,ii*1e6,lw=.9);ax1.set(xlabel='Time (ns)',ylabel='Output current (uA)',xlim=(10,210));ax1.axhline(0,color=GRAY,lw=.6)
        ax1.text(20,65,'UP 10ns',fontsize=8);ax1.text(57,65,'UP 1ns',fontsize=8);ax1.text(96,65,'DN 10ns',fontsize=8);ax1.text(137,65,'DN 1ns',fontsize=8);ax1.text(177,65,'Overlap',fontsize=8)
        for branch,sgn,start in [('up',1,20e-9),('dn',-1,100e-9)]:
            e=r['edge_definitions'][branch];mask=(tt>=start-40e-12)&(tt<=start+420e-12)
            ax2.plot((tt[mask]-start)*1e12,sgn*ii[mask]/e['plateau_A'],label=branch.upper())
            off=start+10.2e-9;mask=(tt>=off-240e-12)&(tt<=off+120e-12)
            ax3.plot((tt[mask]-off)*1e12,sgn*ii[mask]/e['plateau_A'],label=branch.upper())
        ax2.axhline(.9,color=GRAY,ls='--',lw=.7);ax3.axhline(.05,color=GRAY,ls='--',lw=.7);ax2.set(xlabel='From rise start (ps)',ylabel='I / plateau');ax3.set(xlabel='From fall end (ps)',ylabel='I / plateau')
        for ax in [ax1,ax2,ax3]:ax.grid(alpha=.2);ax.tick_params(labelsize=8)
        ax2.legend(fontsize=8);ax3.legend(fontsize=8)
        rows=[]
        for branch in ['up','dn']:rows.append([branch.upper(),f"{v[f'q_{branch}10_C']*1e15:.4f}",f"{v[f'q_{branch}1_C']*1e15:.4f}",f"{v[f'{branch}_turn_on_s']*1e12:.3f}",f"{v[f'{branch}_turn_off_s']*1e12:.3f}"])
        table(fig,[.07,.202,.86,.085],['支路','10ns电荷/fC','1ns电荷/fC','开启/ps','关断/ps'],rows,[.12,.24,.24,.20,.20],8.6)
        para(fig,.165,'Q10按本支路DC(0.9 V)×10 ns归一；Q1按实测Q10/10归一。积分窗分别15–45、55–75、95–125、135–155 ns；重叠175–205 ns，净电荷1.0983 fC。没有只对理想脉冲持续段积分。',9.2)
        para(fig,.086,'开启门限为末段平台90%，使用首次交越；图中仍有明显注入尖峰。重叠指标是净积分绝对值，不是绝对电流积分。DN关断0.79 ps为2 ps样点间插值；最坏UP13.25 ps满足原50 ps限制。',9.1)
        save(pdf,fig)

        fig=page('精确网表、工程认识与复现',5,'最终电路保留25 uA外部参考、原控制时序和所有nominal测量窗口。')
        body='\n'.join(x for x in (case/'circuit.scs').read_text().splitlines() if not x.startswith('//'))
        fig.text(.075,.862,body,fontsize=7.1,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.25)
        para(fig,.37,'电流转向维持主镜和级联偏置，dummy负载使切换节点电压接近输出。UP nc由关断时1.031 V变为导通1.021 V；DN nd由0.764 V变为0.820 V。残余节点变化与开关注入共同影响短脉冲电荷。',9.2)
        para(fig,.264,'供电功耗284.727 uW按原定义取−VDD×I(VDD)的0–220 ns平均，包含25 uA参考、永久偏置与数字门。输出固定0.9 V的外部源负责收送电荷；该功耗指标不是PLL完整系统的能耗。',9.2)
        para(fig,.162,'复现：/home/IC/CodeX/virtuoso-bridge-lite/.venv/bin/python scripts/case47_charge_pump.py\nPDF：同一Python运行 scripts/review_pdf.py 47\n运行：'+r['run_dirs'][0]+'\n'+r['run_dirs'][1],8.4)
        para(fig,.082,'源任务：sky130-pll-charge-pump-pvt。原始合同、LUT查询、HD来源与全部运行依赖哈希分别保存在cases/47-charge-pump和上述runs目录。',8.6)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=5,render_review_pending=True))
    update_case(47,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
