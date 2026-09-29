from report29 import *
CASE=ROOT/'cases/17-nmos-ldo'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());points=r['values']['load_points'];z=json.loads((CASE/'sizing.json').read_text());c=json.loads((CASE/'numerical_confirmation.json').read_text());assert c['passed']
    body=ROOT/'reports/17-nmos-ldo-body.pdf'
    with PdfPages(body) as pdf:
        fig=frame('17 | 0.4V NMOS LDO审查',1,'结论：两种标称负载的全部原门槛通过；额外真实STB也通过。')
        para(fig,.85,'SMIC18MMRF TT / 1.8V / 27°C，外部40uA偏置电流从ibias流向VSS，外部10pF不变；完整保留1mA与5mA两点。以下PM/GM均为严格大于门槛，工作点余量不放宽。',9)
        specs=[('输出距0.4V误差',None,1e3,'mV'),('静态电流','iq_A',1e6,'uA'),('原串联注入PM','phase_margin_deg',1,'deg'),('原串联注入GM','gain_margin_db',1,'dB'),('真实STB PM','stb_phase_margin_deg',1,'deg'),('真实STB GM','stb_gain_margin_db',1,'dB'),('1kHz PSRR','psrr_1k_dB',1,'dB'),('有流MOS最小余量','min_active_headroom_V',1e3,'mV')]
        rows=[]
        for label,k,scale,unit in specs:
            key=k or 'output_error_V';q=r['gates']['1mA_'+key];sign='>' if q['sense']=='min' else ('<' if k=='iq_A' else '≤')
            vals=[abs(p['vout_V']-.4) if k is None else p[k] for p in points]
            rows.append([label,*[f'{v*scale:.5g}' for v in vals],*[sign+f"{q['limits'][t]*scale:.5g}" for t in ['original','10pct','15pct']],unit])
        table(fig,[.07,.36,.86,.335],['指标','1mA','5mA','原','10%','15%','单位'],rows,[.30,.135,.135,.12,.12,.12,.07],7.2)
        para(fig,.293,'输出分别0.40154054V、0.40111369V；最小原PM88.143°，最小STB PM87.965°。原网格每十倍频40点，最终160点；1Hz–1GHz完整覆盖，无额外0dB回穿。',9)
        para(fig,.17,'其他52个工艺/供电/温度/负载点及50个失配种子未执行；没有将标称两点改写成54点PVT或失配通过。噪声、动态负载、布局、PEX不属于本题本次已测结论。',9)
        save(pdf,fig)

        fig=frame('电路选择、gm/ID与实际工作点',2,'镜像输出把输入共模约0.4V与功率管栅压约1V分开。')
        para(fig,.85,'目标尾电流80uA，每输入支路40uA，输出及复制镜各约80uA；目标IQ约240uA。单位10uA查表后并联，功率管采用50uA单位m100；全部单位W/L在模型范围内。',9)
        rows=[[k,f"{q['rounded_W_um']:.4g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()]
        table(fig,[.07,.62,.86,.14],['角色','单位W/L um','LUT gm/ID','单位ID uA'],rows,[.26,.28,.23,.23],8)
        rows=[]
        for n,q in r['operating_point']['1'].items():
            q5=r['operating_point']['5'][n];rows.append([n,f"{q['ids']*1e6:.5g}",f"{q5['ids']*1e6:.5g}",f"{q5['gmid']:.4f}",f"{q['headroom_V']:.4f}",f"{q5['headroom_V']:.4f}"])
        table(fig,[.07,.22,.86,.34],['器件','ID@1mA/uA','ID@5mA/uA','gmID@5mA','余量@1mA/V','余量@5mA/V'],rows,[.16,.17,.17,.16,.17,.17],7.2)
        para(fig,.163,'PMOS电流带原符号；余量=|VDS|-|VDSAT|。两点均11只MOS有流，最小余量约394mV，远大于固定30mV。无流MOS电容排除规则仍保留，实际补偿使用原生MIM。',9)
        save(pdf,fig)

        fig=frame('原串联注入与真实STB交叉检查',3,'两种返回量低频相同，高频受注入双向耦合影响，分别报告。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.24,wspace=.35,hspace=.45)
        for ma,color in [(1,BLUE),(5,GREEN)]:
            rd=ROOT/r['groups'][f'loop{ma}'];d=data(rd,'ac.ac');st=data(rd,'loop.stb');p=data(ROOT/r['groups'][f'psrr{ma}'],'ac.ac')
            for label,f,t,ls in [('series',d['freq'],-d['loop_out']/d['pass_gate'],'-'),('STB',st['freq'],-st['loopGain'],'--')]:
                axs[0,0].semilogx(f,20*np.log10(abs(t)),color=color,ls=ls,label=f'{ma}mA {label}')
                axs[0,1].semilogx(f,np.unwrap(np.angle(t))*180/np.pi,color=color,ls=ls)
            axs[1,0].semilogx(p['freq'],-20*np.log10(abs(p['vout'])),color=color,label=f'{ma}mA')
            q=r['operating_point'][str(ma)];axs[1,1].plot(range(1,12),[x['headroom_V'] for x in q.values()],'.-',color=color,label=f'{ma}mA')
        axs[0,0].axhline(0,color=GRAY,ls=':');axs[0,0].set(xlabel='Frequency (Hz)',ylabel='Loop magnitude (dB)');axs[0,0].legend(fontsize=6)
        axs[0,1].axhline(-180,color=GRAY,ls=':');axs[0,1].set(xlabel='Frequency (Hz)',ylabel='Loop phase (deg)')
        axs[1,0].set(xlabel='Frequency (Hz)',ylabel='Supply rejection (dB)');axs[1,0].legend(fontsize=7)
        axs[1,1].axhline(.03,color=GRAY,ls=':');axs[1,1].set(xlabel='MOS index (page 2 order)',ylabel='Active MOS headroom (V)');clean_axes(axs)
        para(fig,.18,'原台T=-V(loop_out)/V(pass_gate)；真实STB保存的是带符号返回量，低频相位+180°，按T=-loopGain归一后计算180°+phase。若直接把+180°当零相位，会错误多出180°相位裕量。',9)
        para(fig,.084,'两种测量分别检查首个下降0dB和-180°交越，均有有限GM；不以没有相位交越为由填入无限裕量。高频差异不改变两负载原指标通过的结论。',8.8)
        save(pdf,fig)

        fig=frame('原合同与数值精度确认',4,'从40点/dec、1e-6收紧至160点/dec、1e-7，同一电路和夹具。')
        rows=[]
        keys=['vout_V','iq_A','loop_ugb_Hz','phase_margin_deg','gain_margin_db','stb_ugb_Hz','stb_phase_margin_deg','stb_gain_margin_db','psrr_1k_dB','min_active_headroom_V']
        for key in keys:
            matches=[q for q in c['metrics'] if q['metric'].split('mA_',1)[1]==key];rows.append([key,f"{max(q['absolute_difference'] for q in matches):.6g}",f"{matches[0]['maximum_difference']:.6g}"])
        table(fig,[.07,.49,.86,.34],['指标（SI/deg/dB）','两负载最大差','预先固定上限'],rows,[.49,.255,.255],8)
        para(fig,.427,'20项数值比较全部通过：最大UGB差550.47Hz，PM差小于0.0005°，GM差0.03273dB，输出、电流、PSRR及器件余量为0差异。加密点包含全部原点；最终采用加密结果。',9)
        para(fig,.278,'原PSRR是在完整闭环下把VDD的AC幅度设为1、VLOOP设为0；功耗电流定义IQ=-I(VDD)-ILOAD-40uA，仅按原题扣除外部偏置。独立复核用供电电流分解、复数乘共轭及另一套插值重算20个标量。',9)
        para(fig,.135,'原verifier没有可单独调用的标称检查函数；独立审计导入其门槛常量，将原5组不等式分别应用于两个标称负载，共10组通过，不改写上游54点/50种子完整验收语义。全部8个精度运行日志0错误/0警告。',9)
        save(pdf,fig)

        fig=frame('最终精确网表与工艺无源',5,'NMOS功率管总宽430um，以合法4.3um单位m100实现。')
        fig.text(.07,.85,(CASE/'circuit.scs').read_text(),fontfamily='DejaVu Sans Mono',fontsize=7.35,va='top',linespacing=1.6)
        para(fig,.39,'CGATE名义100pF、COUT名义20pF，均为原生mim，单位100×100um及m倍率；实际模型的面积/周边、电压和温度依赖保留。外部10pF不计入DUT，也没有用外部超大电容替代内部补偿。',9)
        para(fig,.24,'端序MOS为D G S B；NMOS体端接VSS，PMOS体端接VDD。loop_out与pass_gate保持两个端口，由测试台的0V串联电压源及iprobe闭合；DUT内部没有短接，原注入点有效。',9)
        para(fig,.115,'电路SHA-256：\n'+r['circuit_sha256'],7.8)
        save(pdf,fig)

        fig=frame('设计认识、复现路径与范围',6,'13实例48端子独立核对；附后两页展开所有器件及体端。')
        para(fig,.85,'低参考电压与NMOS源跟随功率级需要不同的节点电压。直接把PMOS输入支路漏端当功率管驱动，会压缩输入管余量；本例用两路镜像输出完成电平转移，代价是约247uA静态电流。两个负载的全部11管余量已按实际OP检查。',9.5)
        para(fig,.663,'较大的栅极补偿将主环路UGB控制在约1.9MHz，使低输出电容下仍有约88°PM。此题未规定瞬态建立门槛，因此不据AC结果宣称负载跃变或启动速度通过；未另减小负载来改善稳定性。',9.5)
        para(fig,.494,'复现（工程根目录，现有Bridge Python）：\npython scripts/case17_nmos_ldo.py\npython scripts/confirm17.py\npython scripts/schematic17.py\npython scripts/audit17.py\npython scripts/review17.py\n重建后应重新逐页查看报告和完整总图，再执行交付。',9)
        para(fig,.246,'证据：source/与source_provenance.json，circuit.scs、sizing.json、latest_results.json，numerical_plan/baseline/confirmation.json，verification_audit.json，schematic/connectivity.json。源资料、模型、LUT及所有运行输入均保留哈希。',9)
        para(fig,.105,'未覆盖其他52个PVT/负载点、50次失配、布局或PEX。原PDK、Virtuoso Bridge、Spectre与LUT环境未修改。本批次没有恢复用户已取消的额度监控。',9)
        save(pdf,fig)
    finish_report(CASE,body,6)

if __name__=='__main__':make()
