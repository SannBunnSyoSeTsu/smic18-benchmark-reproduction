from report29 import *
CASE=ROOT/'cases/18-regulated-pump'

def make():
    r=json.loads((CASE/'latest_results.json').read_text());v=r['values'];z=json.loads((CASE/'sizing.json').read_text());body=ROOT/'reports/18-regulated-pump-body.pdf';assert json.loads((CASE/'verification_audit.json').read_text())['status']=='passed'
    with PdfPages(body) as pdf:
        fig=frame('18 | 10MHz稳压电荷泵审查',1,'结论：10%档通过；50uA负载供电电流217.337uA，超过原200uA。')
        para(fig,.85,'双相倍压功率级将1.8V提升至约2.34V，误差放大器调节底板HD驱动的供电幅度。无需电感，但有开关损耗、纹波和补偿面积代价，适合片内辅助偏置。',9.3)
        rows=[[str(q['load_uA']),f"{q['vout_avg_V']:.9f}",f"{q['error_V']*1e3:.6f}",f"{q['ripple_V']*1e3:.6f}",f"{q['enabled_current_A']*1e6:.6f}"] for q in v['enabled']]
        table(fig,[.07,.615,.86,.125],['负载/uA','平均输出/V','误差/mV','纹波/mV','AVDD电流/uA'],rows,[.13,.23,.20,.20,.24],7.9)
        table(fig,[.07,.386,.86,.16],['指标','原门槛','10%','15%'],[['相对2.34V误差/mV','≤117','≤128.7','≤134.55'],['输出纹波/mV','≤5','≤5.5','≤5.75'],['开启AVDD电流/uA','≤200','≤220','≤230'],['关闭AVDD电流/nA','≤100','≤110','≤115']],[.43,.19,.19,.19],8.2)
        para(fig,.327,f"关闭独立DC电流{v['disabled_current_A']*1e9:.9f}nA。全部电压、纹波与关闭电流通过原门槛；只有50uA负载开启电流使用10%档，距220uA边界2.663436uA。",9.2)
        para(fig,.18,'TT/1.8V/40°C；开启1/25/50uA三种负载、外部1nF。每次200us，190–200us评分。其余5个开启PVT点与4个关闭PVT点未执行；不宣称完整PVT通过。',9.2);save(pdf,fig)

        fig=frame('反馈调节与gm/ID初始尺寸',2,'16个模拟MOS、5个原生MIM、27个原生多晶电阻、6个HD单元。')
        para(fig,.85,'参考AVDD/2，输出反馈VOUT/2.6；五管OTA比较二者并控制PMOS MCTRL，改变底板驱动供电vclk。EN关闭时切断分压回路、钳位偏置和控制节点。NNT33预充/整流器承受升压节点电压。',9.2)
        rows=[[k,q['model'],f"{q['rounded_W_um']:g}/{q['L_um']:g}",f"{q['gmid']:g}",f"{q['Id_A']*1e6:g}"] for k,q in z['roles'].items()]
        table(fig,[.07,.412,.86,.302],['角色','模型','单位W/L um','gm/ID','初算I/uA'],rows,[.23,.15,.26,.16,.20],8)
        para(fig,.355,'MCTRL单位23.46/0.36um，m4。两只飞跨MIM各7.5pF；参考/反馈滤波各1pF；控制补偿80pF。RZ为3段W1/L240um工艺多晶电阻串联，总阻约230kΩ，提供稳定所需零点。',9.2)
        para(fig,.20,'HD单元INHDV1、INHDV16、NAND2HDV1保持原厂CDL内部尺寸。底板驱动电源为vclk，井端仍接AVDD。gm/ID用于初算；动态开关及控制管不以固定饱和gm/ID代表整个周期。',9.2);save(pdf,fig)

        fig=frame('完整启动轨迹与评分窗',3,'保存点真实波形；开启仿真与关闭DC分别执行。')
        axs=fig.subplots(2,2);fig.subplots_adjust(left=.12,right=.94,top=.85,bottom=.21,wspace=.38,hspace=.44)
        for q in v['enabled']:
            k=f"load{q['load_uA']}";d=data(ROOT/r['groups'][k],'tran.tran');t=d['time']*1e6;lab=str(q['load_uA'])+'uA';axs[0,0].plot(t,d['VOUT'],label=lab);m=t>=199;axs[0,1].plot(t[m],d['VOUT'][m],label=lab);axs[1,0].plot(t,d['X.vclk'],label=lab)
        axs[1,1].bar([str(q['load_uA']) for q in v['enabled']],[q['enabled_current_A']*1e6 for q in v['enabled']],color=BLUE);axs[1,1].axhline(200,color=GRAY,ls='--',label='original');axs[1,1].axhline(220,color=GREEN,ls=':',label='10%')
        axs[0,0].set(xlabel='Time (us)',ylabel='VOUT (V)');axs[0,1].set(xlabel='Time (us)',ylabel='VOUT (V)');axs[1,0].set(xlabel='Time (us)',ylabel='Driver supply (V)');axs[1,1].set(xlabel='Load (uA)',ylabel='AVDD current (uA)')
        for a in axs.flat:a.legend(fontsize=7)
        clean_axes(axs);para(fig,.15,'2–180us只减少保存点（skipcount100），求解仍遵守完整maxstep；190–200us评分区间保存全部求解点。全程端电压筛查因此是保存样本检查，不是连续时间峰值界限。',9.1);save(pdf,fig)

        fig=frame('补偿迭代、数值复算与警告',4,'保留原失败候选、原门槛未通过记录及全部实际日志。')
        para(fig,.85,'首版80pF直接接AVDD，约20–40kHz低频振荡：1/25/50uA纹波约18.279/20.132/17.925mV。加入3段串联RZ后，纹波降至0.739/1.073/1.774mV；50uA供电电流从220.807降至217.337uA。',9.4)
        para(fig,.67,'25项数值确认：maxstep1→0.5ns、reltol1e-5→1e-6，电路及合同不变。预设输出电压差50uV、电流差0.25uA、控制/vclk差1mV、关闭电流差0.05nA；最大开启电流差0.084215uA，均通过。',9.4)
        para(fig,.49,'8个基线/精算运行均实际0错误。6个开启运行各保留5条SPECTRE-16780 LTE警告；关闭DC无警告。精度复算说明报告指标稳定，不能说警告已消失。未放过其他类别警告。',9.4)
        para(fig,.32,'独立重算25个性能标量，核对48个“负载×器件”记录中的六类端电压极值；N18/P18固定1.98V、NNT33固定3.63V筛查通过。原4组检查诚实返回3过1未过，另行判定10%档通过。',9.4)
        para(fig,.14,'供电电流只统计原合同AVDD感测支路；外部1uA偏置接在感测上游，因此不计入该数值。关闭试验为EN=CLK=0、无负载独立DC，不代表已充电输出的关断瞬态。',9.4);save(pdf,fig)

        lines=(CASE/'circuit.scs').read_text().splitlines()
        for j,chunk in enumerate([lines[:29],lines[29:]]):
            fig=frame('最终网表 '+str(j+1)+'/2',5+j,'全部实例原样列出；模拟与原厂HD供电/井端显式连接。');fig.text(.07,.85,'\n'.join(chunk),fontfamily='DejaVu Sans Mono',fontsize=8,va='top',linespacing=1.55)
            para(fig,.13,'电路SHA-256：\n'+r['circuit_sha256'],7.8);save(pdf,fig)
        fig=frame('复现证据与适用范围',7,'附后6页完整图纸；54实例、192端子独立覆盖。')
        para(fig,.85,'工程根目录使用既有Bridge Python依次运行：\npython scripts/case18_regulated_pump.py\npython scripts/confirm18.py\npython scripts/schematic18.py\npython scripts/audit18.py\npython scripts/review18.py\n生成报告后须实际逐页查看才能发布。',9.6)
        para(fig,.55,'source/与source_provenance保存原任务、检查器及哈希；contract固定测试窗口与功率口径；numerical_plan/baseline/confirmation保留事前容差、两套运行和差异；audit与measurement-review保留独立数值和原检查失败原因。',9.3)
        para(fig,.34,'所有PDK、LUT、HD源CDL和既有Spectre/Bridge环境未修改。理想激励及1nF输出负载仅位于测试台，DUT内部采用真实SMIC18 MOS、多晶电阻和MIM。报告不把原生MIM名义电容当作完成版图面积签核。',9.3)
        para(fig,.15,'尚未验证：其他PVT、负载突变、带电关断、随机失配、噪声、版图、PEX及寿命可靠性。当前结论严格限于三组开启TT40°C及一组关闭DC的既定检查。',9.3);save(pdf,fig)
    finish_report(CASE,body,7)

if __name__=='__main__':make()
