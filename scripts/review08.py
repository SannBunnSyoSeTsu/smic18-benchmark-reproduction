from review_pdf import *


def make08():
    case=ROOT/'cases/08-ppsf';r=json.loads((case/'latest_results.json').read_text());v=r['values'];s=json.loads((case/'sizing.json').read_text());cross=json.loads((case/'frequency_crosscheck.json').read_text());a=data(ROOT/r['run_dirs'][0],'ac.ac');o=dc(ROOT/r['run_dirs'][0]);out=ROOT/'reports/08-ppsf-review.pdf'
    with PdfPages(out,metadata={'Title':'08 SMIC18差分推挽源跟随缓冲器','Author':'SMIC18 benchmark reproduction'}) as pdf:
        fig=page('08 | 差分推挽源跟随缓冲器',1,'结论：输入电流资格、全带增益、三个频点SFDR和端口功耗全部原nominal通过。')
        para(fig,.844,'SMIC18MMRF tt / 1.8 V / 27°C；20 uA参考，VCM=0.9 V；差分峰值0.8 V、每侧1 pF负载。保留1–40 MHz AC全带及1/11/41 MHz三个大信号点；未执行其他四个工艺角。',9.4)
        rows=[]
        for label,key,k,unit in [('全AC带最小增益','gain_min_VV',1,'V/V'),('40MHz输入差分电流','input_current_40MHz_A',1e6,'uA'),('全部供电端口DC功耗','power_W',1e6,'uW'),('1MHz基波增益','gain_1MHz_VV',1,'V/V'),('1MHz SFDR','SFDR_1MHz_dB',1,'dB'),('11MHz基波增益','gain_11MHz_VV',1,'V/V'),('11MHz SFDR','SFDR_11MHz_dB',1,'dB'),('41MHz基波增益','gain_41MHz_VV',1,'V/V'),('41MHz SFDR','SFDR_41MHz_dB',1,'dB')]:
            g=r['gates'][key];sign='>' if g['sense']=='min' else '<';rows.append([label,f'{v[key]*k:.7g}']+[f'{sign}{g["limits"][t]*k:.5g}' for t in ['original','10pct','15pct']]+[unit])
        table(fig,[.07,.355,.86,.40],['指标','实测','原门槛','10%边界','15%边界','单位'],rows,[.29,.18,.14,.14,.14,.11],8.4)
        ce=v['input_current_40MHz_A']/(2*np.pi*40e6*.8)*1e15
        para(fig,.302,f'输入电流是不可放宽的资格线：8.177145 uA <20 uA，等效差分输入电容{ce:.3f} fF。全部信号路径为有源MOS缓冲，没有输入至输出的直接电阻导通；耦合电容并不等于有效输入电容。',9.4)
        para(fig,.19,'SFDR沿用原全Nyquist矩形窗定义：49–50 us的1000个1 ns样点，搜索1–500 MHz全部非基波频点，包含Nyquist、排除DC。不截去高次谐波，不用总失真功率SDR替代最大杂散SFDR。',9.4)
        para(fig,.085,'这是电容耦合交流缓冲，不能把1–40 MHz接近单位增益写成直流跟随保证。原SIN瞬态偏置为0 V，DC/AC输入偏置为0.9 V，本次精确保留这一源定义差别。',9.4)
        save(pdf,fig)

        fig=page('推挽跟随、自举共栅与复制偏置',2,'两侧电路对称；MOS体接自身源极，所需隔离井与寄生尚未做版图验证。')
        ax=fig.add_axes([.08,.625,.84,.235]);ax.set(xlim=(0,10),ylim=(0,4.6));ax.axis('off')
        for x,w,label in [(.1,2.6,'VIP / VIN\n各两只5 pF耦合'),(3.45,3,'NMOS + PMOS\n推挽源跟随器'),(7.2,2.6,'VOP / VON\n各1 pF负载')]:
            ax.add_patch(Rectangle((x,2.5),w,1.45,fill=False,edgecolor=BLUE));ax.text(x+w/2,3.23,label,ha='center',va='center',fontsize=9)
        for x1,x2 in [(2.7,3.45),(6.45,7.2)]:ax.annotate('',xy=(x2,3.23),xytext=(x1,3.23),arrowprops=dict(arrowstyle='->',color=BLUE))
        ax.text(.2,1.65,'IREF20uA → N/P镜 → VCM±VGS 及 ±9kΩ压降',fontsize=9)
        ax.text(.2,.82,'每只共栅门由输出经5pF自举；全部栅偏置经1MΩ接入。',fontsize=9,color=GREEN)
        ax.text(.2,.13,'使输入管漏端随源端移动，减小VDS调制；并非理想前馈源。',fontsize=9,color=GREEN)
        rows=[]
        for label,key,m in [('NMOS输入跟随','n_in','6'),('PMOS输入跟随','p_in','6'),('NMOS自举共栅','n_cas','6'),('PMOS自举共栅','p_cas','6'),('N偏置镜','n_bias','1'),('P偏置镜','p_bias','1')]:
            q=s['roles'][key];rows.append([label,q['model'],f'{q["rounded_W_um"]:g}/{q["L_um"]:g}',f'{q["gmid"]:g}',m])
        table(fig,[.07,.357,.86,.225],['角色','模型','单位W/L um','LUT gm/ID','输出支路m'],rows,[.29,.14,.24,.18,.15],8.8)
        para(fig,.313,'每个LUT单位选20 uA、VDS0.45 V，输入和共栅L0.36 um；偏置镜L1 um。输出级m6给每侧目标120 uA，实际113.744 uA。复制支路和信号支路漏压不同，因此不是精确理想镜比例。',9.4)
        para(fig,.201,'源参考用低阈值Sky130器件及三级MOS复制产生共栅偏置。本实现用目标工艺n18/p18和有电流通过的9 kΩ压降产生相应余量；重新查表定尺寸，没有按工艺节点简单缩放宽度。',9.4)
        para(fig,.102,'全DUT19只MOS、8只5 pF电容、8只1 MΩ偏置电阻和2只9 kΩ余量电阻。总耦合/自举电容40 pF；使用原任务允许的正R/C，未做工艺无源匹配或面积签核。',9.3)
        save(pdf,fig)

        fig=page('小信号输入负载、增益与真实工作点',3,'40MHz资格使用|I(VIP)−I(VIN)|，AC差分幅度0.8V；不能单看某一输入引脚。')
        ax=fig.add_axes([.12,.61,.345,.245]);ax.plot(a['freq']/1e6,abs(a['vop']-a['von'])/.8,color=BLUE);ax.axhline(.99,color=GRAY,ls='--');ax.set(xlabel='Frequency (MHz)',ylabel='Differential gain (V/V)',ylim=(.987,1.002));ax.grid(alpha=.2)
        ax2=fig.add_axes([.595,.61,.345,.245]);ax2.plot(a['freq']/1e6,abs(a['VIP:p']-a['VIN:p'])*1e6,color=BLUE);ax2.axhline(20,color=GRAY,ls='--');ax2.set(xlabel='Frequency (MHz)',ylabel='Differential input current (uA)',ylim=(0,21));ax2.grid(alpha=.2)
        rows=[]
        for name in ['MINP','MIPP','MCNP','MCPP','MREF','MBN','MBP']:
            z=r['operating_point'][name];rows.append([name,f'{abs(z["ids"])*1e6:.3f}',f'{z["gmid"]:.3f}',f'{z["headroom_V"]*1e3:.3f}'])
        table(fig,[.07,.315,.86,.215],['器件','|Id| / uA','gm/ID','|VDS|−|VDSAT| / mV'],rows,[.23,.23,.23,.31],8.8)
        para(fig,.273,f'中心输出VOP=VON≈{o["vop"]:.6f} V；输入跟随管NMOS/PMOS余量99.15/83.05 mV，共栅管约604 mV。源体一起移动，模型中消除输入跟随器的体效应增益损失；物理隔离井/结电容仍需未来版图实现和验证。',9.3)
        power=[(p,abs(o[p+':p']*(1.8 if p=='VDD' else .9))*1e6) for p in ['VDD','VCM','VIN','VIP']]
        para(fig,.166,'功耗按原定义Σ|Vport·Iport|：'+', '.join(f'{p}={w:.6f}uW' for p,w in power)+f'；合计{v["power_W"]*1e6:.6f}uW。即使VCM净功率很小，也保留该端口，未用隐藏偏置源供电。',9.2)
        para(fig,.075,'AC增益@1MHz=0.9985244，与大信号基波增益0.9985057分别保存，避免同名字段覆盖。精确尺寸、实际体连接和全部19只MOS工作点均有可追踪记录。',9.1)
        save(pdf,fig)

        fig=page('三个频点的全Nyquist谱与交叉检查',4,'输入差分峰值0.8V；50us总观察，最后1us保留全部1000点矩形窗。')
        for i,q in enumerate(cross['spectra']):
            ax=fig.add_axes([.12,.67-i*.25,.82,.18]);amp=np.array(q['amplitude_V']);f=q['frequency_MHz'];db=20*np.log10(np.maximum(amp[1:]/amp[f],1e-18));ax.plot(np.arange(1,501),db,color=BLUE,lw=.7);ax.plot(q['largest_spur_MHz'],-q['SFDR_dB'],'o',color=GREEN,ms=4);ax.set(xlabel='Spectrum bin frequency (MHz)',ylabel='Amplitude (dBc)',xlim=(0,500),ylim=(-180,5));ax.grid(alpha=.2);ax.tick_params(labelsize=8);ax.text(.02,.92,f'{f}MHz input: SFDR {q["SFDR_dB"]:.4f}dB; max spur {q["largest_spur_MHz"]}MHz',transform=ax.transAxes,va='top',fontsize=8.5)
        para(fig,.105,'三个最大杂散分别为3、33、123 MHz，都是第三谐波。原dynamic_metrics逐频三角求和，与独立rFFT结果最大差小于2e−10 dB；采用相同线性插值/边缘外推规则，未改变原频谱口径。',9.3)
        save(pdf,fig)

        fig=page('大信号波形、测量细节与适用边界',5,'最难的41MHz工况仍保留0.8V差分峰值和每侧1pF负载，没有减小输入幅度。')
        d=data(ROOT/r['run_dirs'][3],'tran.tran');mask=(d['time']>=49e-6)&(d['time']<=49.1e-6)
        ax=fig.add_axes([.12,.625,.82,.23]);ax.plot((d['time'][mask]-49e-6)*1e9,(d['vip']-d['vin'])[mask],color=GRAY,ls='--',label='Input');ax.plot((d['time'][mask]-49e-6)*1e9,(d['vop']-d['von'])[mask],color=BLUE,label='Output');ax.set(xlabel='Time after49us (ns)',ylabel='Differential voltage (V)');ax.legend(fontsize=8);ax.grid(alpha=.2)
        rows=[[str(q['frequency_MHz']),f'{r["values"]["gain_"+str(q["frequency_MHz"])+"MHz_VV"]:.9f}',f'{q["SFDR_dB"]:.6f}',str(q['largest_spur_MHz'])] for q in cross['spectra']]
        table(fig,[.07,.431,.86,.125],['输入/MHz','基波增益V/V','SFDR/dB','最大杂散/MHz'],rows,[.2,.3,.25,.25],8.8)
        para(fig,.391,'原SPICE源的DC为0.9 V，但SIN(0,0.4V,f)的瞬态均值为0 V；Spectre以dc=.9、sinedc=0、ampl=.4保留。输入通过电容传入偏置过的MOS栅，不能将源DC写成全部瞬态也为0.9V。',9.4)
        para(fig,.276,'每轮完整模拟50us，最大内部步100ps、保存1ns，reltol1e−6、vabstol1e−9、iabstol1e−14。原函数筛选49us≤t<50us，再重采样至1000点；基波bins为1/11/41，非基波搜索包含bin500。四个最终运行均无警告。',9.3)
        para(fig,.162,'40MHz输入电流相当于约40.67fF，但DUT使用40pF耦合/自举电容；小输入负载来自跟随抵消，不能因此删除电容面积。1MΩ×5pF为5us偏置时间常数，本例没有独立冷启动或直流传输门槛。',9.3)
        para(fig,.069,'SFDR来自确定性瞬态，不含器件噪声、抖动和失配。只验证tt27；其他四角与隔离井寄生没有实测，不能把106dB SFDR当作量产精度保证。',9.1)
        save(pdf,fig)

        fig=page('精确电路与冻结证据',6,'模拟有源跟随级使用gm/ID LUT；没有数字逻辑，不需要HD标准单元。')
        fig.text(.075,.857,(case/'circuit.scs').read_text(),fontsize=7.5,fontfamily='DejaVu Sans Mono',va='top',linespacing=1.23)
        para(fig,.303,'复现：既有Bridge Python运行 scripts/case08_ppsf.py --full；PDF用 scripts/review_pdf.py 8。最后仅将提取字段区分为AC增益/大信号增益，未改电路或重跑仿真；交叉记录保存最终提取脚本哈希。',9)
        para(fig,.198,'最终运行：\n'+'\n'.join(r['run_dirs']),8.1)
        para(fig,.083,'源任务sky130-buf-ppsf-bs-gain1-sfdr90；instruction/reference/verifier/benches均冻结。inputs、原PSF、模型及LUT哈希、完整工作点和frequency_crosscheck.json一起保存，全部源和运行快照通过审计。',9)
        save(pdf,fig)
    write_json(case/'pdf_provenance.json',dict(pdf=str(out.relative_to(ROOT)),sha256=sha(out),results_sha256=sha(case/'latest_results.json'),circuit_sha256=sha(case/'circuit.scs'),generated_at=now(),pages=6,render_review_pending=True))
    update_case(8,review_pdf=str(out.relative_to(ROOT)),review_pdf_ready=False,pdf_render_review_pending=True)
    return out
