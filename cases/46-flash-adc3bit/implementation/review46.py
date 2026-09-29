from report29 import *
CASE=ROOT/'cases/46-flash-adc3bit'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];z=json.loads((CASE/'sizing.json').read_text());rec=json.loads((CASE/'conversion_records.json').read_text());body=ROOT/'reports/46-flash-adc3bit-body.pdf'
    with PdfPages(body) as pdf:
        fig=frame('46 | 3位Flash ADC审查',1,'结论：TT/1.8V/27°C四类功能记录及原13组检查全部通过。')
        para(fig,.85,'七路动态比较器并行判断输入与电阻梯阈值，SR锁存保持决策，HD逻辑编码成三位。相对逐次逼近无需逐位迭代，速度高；比较器、时钟负载及失配代价随位数增长，适合低位数高速量化。',9.2)
        items=[('时钟到输出/ns','clock_to_output_s',1e9),('核心和参考/uW','core_reference_power_w',1e6),('正向时钟/uW','clock_delivery_power_w',1e6),('DNL/LSB','dnl_lsb',1),('INL/LSB','inl_lsb',1),('绝对误差/LSB','absolute_error_lsb',1),('低频SNDR/dB','sine_low_sndr_db',1),('低频SFDR/dB','sine_low_sfdr_db',1),('低频归一ENOB','sine_low_normalized_enob_bits',1),('高频SNDR/dB','sine_high_sndr_db',1),('高频SFDR/dB','sine_high_sfdr_db',1),('高频归一ENOB','sine_high_normalized_enob_bits',1)]
        rows=[]
        for label,key,scale in items:
            q=r['gates'][key];sign='≤' if q['sense']=='max' else '≥';rows.append([label,f"{q['value']*scale:.6g}",*[sign+f"{q['limits'][t]*scale:.5g}" for t in ['original','10pct','15pct']]])
        table(fig,[.07,.305,.86,.423],['指标','实测','原','10%','15%'],rows,[.31,.19,.17,.165,.165],7.6)
        para(fig,.249,'静态斜坡覆盖8码、7个阈值，单调。跳码错误、缺失跳变、迟到跳变、无效电平和稳定窗违例全为0。有效低≤0.36V、高≥1.44V；9.5–19ns稳定窗及零错误要求不放宽。',9.2)
        para(fig,.12,'归一ENOB来自原16点确定性记录与满量程校正；大于3不表示此3位ADC具备超过3位的物理分辨率，也不代表噪声、抖动或统计测试。',9.2);save(pdf,fig)

        fig=frame('比较器阵列、保持与HD编码',2,'七个11管StrongARM、七个双NAND SR锁存、十二个HD编码门。')
        rows=[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()]
        table(fig,[.07,.650,.86,.19],['角色','模型','W/L um','gm/ID初算','I初算/uA'],rows,[.26,.13,.23,.20,.18],8)
        para(fig,.594,'每个比较器含输入对、时钟尾管、交叉再生NMOS/PMOS各两只及四只预充PMOS。模拟再生核心按gm/ID初算，实际工作在复位、放电和再生等动态状态；固定饱和gm/ID不能代表整个周期。',9.3)
        para(fig,.43,'原厂HD采用INHDV1、NAND2HDV1和NAND4HDV1；SR保持比较器结果，复位期间不把比较器预充值直接当有效输出。编码由6个反相器、5个二输入NAND、1个四输入NAND完成，内部器件尺寸不改。',9.3)
        para(fig,.265,'电阻梯8×500Ω，参考0.6/1.4V，七个阈值节点各0.3pF。比较器与SR为复用定义：共54定义实例259端子；展开为77模拟MOS、26HD、15个R/C，即118个叶级实例。HD内部MOS另由原CDL保存。',9.3)
        para(fig,.11,'时钟50MHz、50Ω源阻抗，三位输出各15fF；模拟输入为原合同理想电压源。电阻/电容为原题允许的理想无源，DUT内部无行为比较器、理想数字函数或受控源。',9.3);save(pdf,fig)

        fig=frame('静态传输、跳码与动态频谱',3,'两组原始正弦相位保持；所有图来自实际精算记录。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.19,wspace=.39,hspace=.45)
        q=rec['ramp'];axs[0,0].step(q['input_V'],q['codes'],where='mid');axs[0,0].set(xlabel='Input (V)',ylabel='Ramp code',yticks=range(8))
        q=rec['transition'];t=np.array(q['edges_s'])*1e9;axs[0,1].step(t,q['expected'],where='post',label='expected');axs[0,1].plot(t,q['codes'],'o',ms=3,label='measured');axs[0,1].set(xlabel='Conversion edge (ns)',ylabel='Transition code',yticks=range(8));axs[0,1].legend(fontsize=7)
        for ax,key,label in [(axs[1,0],'sine_low','3.125 MHz'),(axs[1,1],'sine_high','21.875 MHz')]:
            q=rec[key];p=np.array(q['spectrum_power']);f=np.arange(len(p))*50/16;ax.stem(f,10*np.log10(np.maximum(p/p[q['tone_bin']],1e-8)),bottom=-70,basefmt=' ');ax.set(xlabel='Frequency (MHz)',ylabel=label+' spectrum (dBc)',ylim=(-70,5))
        clean_axes(axs);para(fig,.13,'动态记录每组16码，分别覆盖7种码；不等同于静态缺码。静态全8码检查独立通过。功率100–500ns取有符号核心/参考均值；时钟只积正向供能，峰值电流3.698857mA作为诊断。',9.2);save(pdf,fig)

        fig=frame('测量定义、精度与警告',4,'所有动态试验明确投影至TT标称，保留原频率、相位和判码定义。')
        para(fig,.85,'斜坡0.55→1.45V，100–2100ns；100次转换边沿110–2090ns。阈值取相邻代码对应输入的中点：0.694、0.784、0.883、0.982、1.081、1.189、1.288V。DNL/INL受此离散斜坡步进分辨率限制。',9.3)
        para(fig,.676,'26码跳变序列含0↔7和内部码变化，25个评分周期；每周期检查全部中点交叉，最后/最迟交叉决定时延。每位9.5–19ns保持正确有效电平，未只在一个采样瞬间检查。',9.3)
        para(fig,.51,'两正弦3.125/21.875MHz，相位212°/279.25°，中心1V、峰值0.39V；首边沿50ns，每20ns一次，在边沿+19ns判码。16码DFT中非DC、非基波谱线共同组成SNDR分母，最大杂散形成SFDR。',9.3)
        para(fig,.344,'maxstep0.1→0.05ns、reltol1e-6→1e-7；29项数值确认通过，全部转换码不变，最大核心/参考功率差2.328429nW<2uW。8运行实际0错误，每次2或5条LTE警告保留；精度确认不等于零警告。',9.3)
        para(fig,.177,'独立原Python分析器接收实际Spectre波形，重算斜坡、全部跳变、稳定窗、核心/参考和正向时钟功率、递归DFT；29标量及原13组检查一致通过。模型、LUT、HD和源资料哈希不变。',9.3);save(pdf,fig)
        lines=(CASE/'circuit.scs').read_text().splitlines()
        for j,chunk in enumerate([lines[:31],lines[31:]]):
            fig=frame('最终完整网表 '+str(j+1)+'/2',5+j,'层级定义、7路实例与所有HD编码连接原样列出。');fig.text(.07,.85,'\n'.join(chunk),fontfamily='DejaVu Sans Mono',fontsize=8,va='top',linespacing=1.5);para(fig,.13,'电路SHA-256：\n'+r['circuit_sha256'],7.8);save(pdf,fig)
        fig=frame('范围、归一ENOB与复现证据',7,'附后6页完整电路图；全部转换码和频谱功率随证据保存。')
        para(fig,.85,'原算法：归一SNDR = SNDR + 10log10((16×8/4)² / P基波)，ENOB=(归一SNDR−1.76)/6.02。它保留原满量程归一口径；有限长度、特定相位的无噪声3位记录可能给出>3的值，不能解释为实际精度提升。',9.3)
        para(fig,.67,'核心功率=mean(−1.8·I(VDD)−1.4·I(VREFP)−0.6·I(VREFN))。正向时钟功率单列mean(max(−VCLK·I(VCLK),0))；输入理想源驱动功耗和真实外部时钟发生器损耗未计入原核心指标。',9.3)
        para(fig,.49,'工程根目录，既有Bridge Python：scripts/case46_flash_adc.py → confirm46.py → schematic46.py → audit46.py → review46.py。重生成报告后须重新实际查看。conversion_records与baseline_conversion_records保存每次码流、阈值和谱功率。',9.3)
        para(fig,.31,'contract和原source固定实验条件，数值计划先于精算，独立明细保留原检查结果。当前四类记录都在TT1.8V27°C执行，两个正弦原压力角已明确投影到标称，未冒称原动态PVT点通过。',9.3)
        para(fig,.14,'未做其他PVT、随机失配、噪声、抖动、统计亚稳态、输入驱动阻抗扫描、布局与PEX。PDK、LUT、HD库和既有Bridge/Spectre环境未修改。',9.3);save(pdf,fig)
    finish_report(CASE,body,7)

if __name__=='__main__':make()
