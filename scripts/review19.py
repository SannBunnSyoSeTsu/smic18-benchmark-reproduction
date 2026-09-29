from report29 import *
CASE=ROOT/'cases/19-sc-converter'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());h,l=r['values']['loads'];z=json.loads((CASE/'sizing.json').read_text());c=json.loads((CASE/'numerical_confirmation.json').read_text());assert c['passed'];body=ROOT/'reports/19-sc-converter-body.pdf'
    with PdfPages(body) as pdf:
        fig=frame('19 | 2:1开关电容降压审查',1,'结论：TT/1.8V/27°C全部轻重负载原门槛通过。')
        para(fig,.85,'20MHz、50Ω时钟源，680Ω/6800Ω匹配负载；零初始储能启动。评分0.3–0.7us，共8个周期；飞跨与输出电容全部位于DUT内部。',9.2)
        items=[('重载转换比下限','heavy_conversion_ratio_min',1),('重载转换比上限','heavy_conversion_ratio_max',1),('重载效率下限','heavy_efficiency_min',100),('轻载转换比下限','light_conversion_ratio_min',1),('轻载转换比上限','light_conversion_ratio_max',1),('轻载效率下限','light_efficiency_min',100),('重载纹波/mV','heavy_ripple_V',1e3),('启动/ns','startup_s',1e9),('启动保持/V','startup_hold_V',1),('轻载总输入/uW','light_input_power_W',1e6),('输出电阻/Ω','output_resistance_ohm',1)]
        rows=[]
        for label,key,s in items:
            q=r['gates'][key];sign='≥' if q['sense']=='min' else '≤';rows.append([label,f"{q['value']*s:.6g}",*[sign+f"{q['limits'][t]*s:.5g}" for t in ['original','10pct','15pct']]])
        table(fig,[.07,.335,.86,.38],['指标','实测','原','10%','15%'],rows,[.32,.19,.17,.16,.16],7.6)
        para(fig,.28,'两负载效率上限固定100%，供电、时钟与负载平均功率必须非负；启动保持目标固定0.6804V。全程模拟功率MOS端电压筛查上限1.98V，不放宽。',9)
        para(fig,.16,f"重/轻载输出{h['vout_mean_V']:.9f}/{l['vout_mean_V']:.9f}V；效率{h['efficiency']*100:.6f}%/{l['efficiency']*100:.6f}%。其余44个有源PVT及2个无源极端条件未执行。",9)
        save(pdf,fig)

        fig=frame('电荷转移、gm/ID与原厂HD',2,'两组四开关交错；数字单元尺寸保持原厂CDL。')
        para(fig,.85,'串联相：PMOS把飞跨上板接VDD，浮置NMOS把下板接VOUT。并联相：上板经NMOS接VOUT，下板接地。A/B两组相反工作；交叉反馈NAND与延迟反相链生成非交叠相，10个分支HD单元驱动功率栅。',9.2)
        rows=[[k,f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()]
        table(fig,[.07,.61,.86,.12],['模拟角色','单位W/L um','初算gm/ID','单位ID/uA'],rows,[.34,.28,.18,.20],8.2)
        table(fig,[.07,.386,.86,.168],['元件','最终实现'],[['浮置NMOS×4','1.36/0.18um，m60，总宽81.6um/只'],['高侧PMOS×2','4.00/0.18um，m24，总宽96um/只'],['底板NMOS×2','2.04/0.18um，m64，总宽130.56um/只'],['CFA/CFB/CO','100×100um MIM，m10.29866/10.29866/28.83625'],['CBPA/CBPB','20×102.9866um MIM，名义各2pF']],[.30,.70],8)
        para(fig,.323,'gm/ID只用于初始电流密度与宽度选择。功率MOS在开关过程中进入线性区、关断和反向传输，不能用固定饱和gm/ID描述整个周期。最终35实例含8功率MOS、5工艺MIM、22个HD单元，共176端子。',9)
        para(fig,.175,'原厂HD：INHDV1、INHDV2、INHDV16和NAND2HDV1；源CDL哈希、引脚与每个内部MOS尺寸冻结。\nMIM名义总量484pF，对应较大电容板面积；未含版图布线和PEX。',9)
        save(pdf,fig)

        fig=frame('启动、稳态输出与时钟能量',3,'完整实际波形；下板负尖峰不从观测范围中剔除。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.19,wspace=.38,hspace=.43)
        for label,color in [('heavy',BLUE),('light',GREEN)]:
            d=data(ROOT/r['groups'][label],'tran.tran');t=d['time']*1e9;axs[0,0].plot(t,d['vout'],label=label,color=color);m=t>=600;axs[0,1].plot(t[m],d['vout'][m],color=color,label=label)
            if label=='heavy':
                m=t<100;axs[1,0].plot(t[m],d['X.cbA'][m],label='bottom A');axs[1,0].plot(t[m],d['X.cbB'][m],label='bottom B');m=(t>=600)&(t<=650);p=-d['clk_src']*d['VCLK:p'];axs[1,1].plot(t[m],p[m]*1e6,label='signed');axs[1,1].plot(t[m],np.maximum(p[m],0)*1e6,label='positive only',ls='--')
        axs[0,0].axhline(.6804,ls=':',color=GRAY);axs[0,0].set(xlabel='Time (ns)',ylabel='VOUT (V)');axs[0,1].set(xlabel='Time (ns)',ylabel='Steady VOUT (V)');axs[1,0].set(xlabel='Startup time (ns)',ylabel='Flying bottom plate (V)');axs[1,1].set(xlabel='Time (ns)',ylabel='External clock power (uW)')
        for ax in axs.flat:ax.legend(fontsize=7)
        clean_axes(axs);para(fig,.13,'电源功率按有符号供能取均值；外部时钟只积分正向瞬时功率，不用返回能量抵扣。所有内部HD时钟与栅极驱动损耗已经计入VDD，避免仅计算功率级效率。',9)
        save(pdf,fig)

        fig=frame('功率口径、失败候选与验证',4,'数值容差在精度复算前冻结；最终电路保持一致。')
        rows=[]
        for q in [h,l]:rows.append([str(q['load_ohm']),*[f"{q[k]*1e6:.6f}" for k in ['supply_power_W','clock_power_W','load_power_W','input_power_W']]])
        table(fig,[.07,.729,.86,.11],['负载/Ω','VDD/uW','正向CLK/uW','负载/uW','总输入/uW'],rows,[.15,.22,.19,.22,.22],7.8)
        para(fig,.675,'首版底板NMOS m16：所有原性能门槛通过，但启动时MN4B的|VGD|约2.204V超过预设1.98V筛查。将其改为m64后，最终最大端电压1.919501V；代价是重载效率约79.29%降至77.76%、轻载效率约37.85%降至34.57%。',9)
        para(fig,.52,'25项数值确认通过：maxstep0.5→0.25ns、reltol1e-6→1e-7。最大重载效率差0.011254个百分点<0.1个百分点，最大供电功率差0.183756uW<2uW，输出电阻差0.001472Ω<0.1Ω；启动差0.0115ps。',9)
        para(fig,.367,'独立复核121个标量：25项性能与96项功率管六端电压差。另调用原8组检查函数，仅把预期点集投影至TT1.8V27°C。4个基线/最终运行均实际0错误；模型、源资料、LUT与原厂HD哈希核对通过。',9)
        para(fig,.218,'启动取0.6804V的最后一次上穿，并单独检查200–700ns最小输出；没有把“首次达到”当成持续启动。输出电阻使用相同条件下轻重载平均电压差除以平均电流差，最终49.622918Ω。',9)
        save(pdf,fig)

        fig=frame('最终网表：全部模拟与HD实例',5,'每个单元的电源与井端都显式连接；工艺MIM未替换为理想电容。')
        fig.text(.07,.851,(CASE/'circuit.scs').read_text(),fontfamily='DejaVu Sans Mono',fontsize=6.8,va='top',linespacing=1.35)
        para(fig,.16,'电路SHA-256：\n'+r['circuit_sha256'],7.8);save(pdf,fig)

        fig=frame('复现证据与范围',6,'附后5页完整电路图，35实例176端子独立覆盖。')
        para(fig,.85,'复现入口（工程根目录，既有Bridge Python）：\npython scripts/case19_sc_converter.py\npython scripts/confirm19.py\npython scripts/schematic19.py\npython scripts/audit19.py\npython scripts/review19.py\n重新生成报告后须实际逐页查看，才可发布知识。',9.5)
        para(fig,.56,'source/保留原任务与检查器；contract.json固定原轻重负载、时钟、启动与功率定义。numerical_plan/baseline/confirmation分开保存容限和两套运行，verification_audit.json给出独立积分及原检查函数结果；所有运行输入与真实日志均留在runs/19/。',9.3)
        para(fig,.35,'本题未规定内部非交叠脉宽门槛；非交叠通过外部效率、输出纹波、轻载功耗和启动共同约束。端电压检查只是保存时间点上的工程筛查，不等于可靠性寿命认证或版图签核。',9.3)
        para(fig,.17,'仅TT/1.8V/27°C。其余44有源PVT点、ll/hh无源极端、噪声、失配、版图和PEX未执行；没有宣称完整47条件通过。原PDK、Bridge、Spectre、LUT及上游知识保持不变。',9.3);save(pdf,fig)
    finish_report(CASE,body,6)

if __name__=='__main__':make()
