"""Append verified module evidence to the user-authorized new knowledge folder."""
from common import *
import shutil
from module_overviews import overview

KB=WORKSPACE/'Analog-Circuit-Knowledge-Base/SMIC18-Benchmark-Reproduction'
NAMES={2:('02-mirror','可编程电流镜：单元复制、低余量共栅与完整端口合同'),4:('04-gmr','GM-R：源极体效应、增益精度与负载极点'),12:('12-beta','β倍增基准：非零自偏置、真实启动与输出端口功耗'),16:('16-miller','两级Miller运放：第二级gm/ID的速度、失调与补偿权衡'),44:('44-ota5','5T OTA：长输入管与短镜负载的gm/ID组合'),45:('45-divider','HD 二分频：复位状态与输出占空比联合约束')}
NAMES[41]=('41-lowpower-miller','低功耗Miller：级联镜、单位电流密度与供电抑制')
NAMES[29]=('29-ahuja','Ahuja补偿：宽负载范围、低阻返回点与级联镜余量')
NAMES[13]=('13-constant-gm','恒跨导增益：自偏置、体效应和宽度专属LUT')
NAMES[14]=('14-oscillator','低功耗2MHz振荡器：限流、起振与输出负载功耗')
NAMES[3]=('03-selfbiased-gmr','自偏置退化GM-R：跨导控制、端口功耗与失真口径')
NAMES[20]=('20-mux','八选一模拟MUX：共模相关导通电阻与完整隔离矩阵')
NAMES[22]=('22-bootstrap','自举栅驱动：近奈奎斯特采样、跟踪过驱动与预充保护')
NAMES[23]=('23-resistor-dac','5位电阻DAC：开关电阻、码间线性度与建立时间')
NAMES[24]=('24-ring-vco','电流饥饿环形VCO：调谐增益、起振与电流限制')
NAMES[31]=('31-bottom-plate','差分底板采样：关断顺序、电荷注入与采样频谱')
NAMES[35]=('35-fd-miller','全差分两级Miller：差模补偿、共模环路与输出驱动')
NAMES[36]=('36-telescopic','全差分套筒OTA：级联增益、共模反馈与电压余量')
NAMES[37]=('37-nested-miller','三阶嵌套Miller：多级增益、补偿环路与负载驱动')
NAMES[47]=('47-charge-pump','PLL电荷泵：复制偏置、电流转向与脉冲电荷精度')
NAMES[49]=('49-lc-vco','LC压控振荡器：谐振调谐、负阻起振与噪声约束')
NAMES[50]=('50-gainboosted-folded','高增益折叠运放：增益提升、局部环路与快速建立')
NAMES[7]=('07-ldo-ota5','PMOS LDO：误差放大器余量、栅极缓冲与补偿')
NAMES[10]=('10-tia','跨阻放大器：电流读出、输入阻抗与反馈带宽')
NAMES[8]=('08-ppsf','推挽源跟随缓冲：自举共栅、输入负载与全带频谱')
NAMES[25]=('25-complementary-ab','互补轨到轨Class-AB：尾电流转向、浮动偏置与双路径补偿')
NAMES[11]=('11-bandgap','一阶带隙基准：温度补偿、真实启动与供电扰动')
NAMES[21]=('21-highpsrr-bandgap','高PSRR带隙：级联镜、自偏置与物理RC滤波')

def publish(slot):
    slug,title=NAMES[slot];case=ROOT/'cases'/slug
    result=json.loads((case/'latest_results.json').read_text())
    contract=json.loads((case/'contract.json').read_text())
    supply=contract.get('VDD_V',1.8);temperature=contract.get('temperature_C',27)
    pp=json.loads((case/'pdf_provenance.json').read_text())
    state=json.loads((ROOT/'status.json').read_text())['cases'][slot-1]
    assert state['nominal_complete'] and state['review_pdf_ready']
    assert not pp['render_review_pending']
    assert sha(ROOT/pp['pdf'])==pp['sha256'] and sha(case/'latest_results.json')==pp['results_sha256']
    assert sha(case/'circuit.scs')==pp['circuit_sha256']
    dst=KB/'evidence'/slug;dst.mkdir(parents=True,exist_ok=True)
    files=['circuit.scs','contract.json','latest_results.json','pdf_provenance.json']
    files += [f for f in ['sizing.json','geometry.json','hd_cells.scs','hd_cells_manifest.json','source_provenance.json','numerical_confirmation.json','numerical_review.json','verification_audit.json','operating_conditions.json','frequency_crosscheck.json','initial_bootstrap_voltage_diagnostic.json','lut_validation.json','stb_diagnostic.json','schematic_audit.json','measurement-review.md'] if (case/f).exists()]
    for file in files:shutil.copy2(case/file,dst/file)
    if slot in (11,21):
        for file in ['environment.json','latest_runs.json','schematic_independent_review.json','implementation_provenance.json']:
            shutil.copy2(case/file,dst/file)
        for source in case.glob('testbench_*.scs'):shutil.copy2(source,dst/source.name)
        for directory in ['source','implementation','pdf_review']:
            shutil.copytree(case/directory,dst/directory,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    if (case/'schematic').is_dir():shutil.copytree(case/'schematic',dst/'schematic',dirs_exist_ok=True)
    if (case/'sizing.json').exists():
        for role in json.loads((case/'sizing.json').read_text())['roles'].values():
            source=Path(role['lut_path'])
            assert sha(source)==role['lut_sha256']
            (dst/'lut').mkdir(exist_ok=True);shutil.copy2(source,dst/'lut'/source.name)
    shutil.copy2(ROOT/pp['pdf'],dst/'review.pdf')
    e='../evidence/'+slug+'/'
    tier=result['status'].removeprefix('complete_')
    acceptance='全部对应 nominal 原始指标通过' if tier=='original' else f'全部对应 nominal 指标在{tier.replace("pct","%")}放宽条件内通过；原门槛差异见正文'
    head=f'''# {slot:02d} · {title}

{overview(slot)}

状态：**SMIC18MMRF / TT / {supply:g} V / {temperature:g}°C，{acceptance}**。只宣称原理图级 nominal；未执行其他PVT、失配或版图验证。审查PDF已逐页检查中文、图表和网表可读性。

[审查 PDF]({e}review.pdf) · [精确电路]({e}circuit.scs) · [验收合同]({e}contract.json) · [实测结果]({e}latest_results.json)

'''
    if pp.get('schematic_pages'):
        head+=f'当前报告：**{pp["body_pages"]}页正文＋{pp["schematic_pages"]}页完整电路图，共{pp["pages"]}页**。下文历史交付记录中的页数对应当时的正文版本。\n\n'
    if slot==11:
        head+='本项动态测试为1.8V/27°C/5pF；TT温漂保留1.8V下−40/0/27/60/100/125°C六点，线性调整率保留27°C下1.62/1.8/1.98V三点。全部14项适用原门槛通过。现用Spectre24.1，历史26项18.1结果保持原样。\n\n'
    if slot==21:
        head+='本项为TT/1.8V/27°C/1pF；温漂保留−40至85°C、步长1°C的126点功能表征。全部5项适用原门槛通过，未执行原题另外三个代表性PVT点。现用Spectre24.1。\n\n'
    if slot==2:
        head+='''## 设计与完整验收

两个n18二极管参考的单元W/L=34.78/1 µm，目标50 µA、gm/ID=16。四组输出支路分别复制(16,4)、(12,8)、(8,12)、(4,16)个相同单元。HD两只反相器与四只NOR产生独热选择；每支路一个n18模拟开关，单位W/L=32.84/0.18 µm。

共栅管使用2.12/0.36 µm单元m=200，偏置复制管m=1；原始选点gm/ID=18，目标总电流1 mA。VDD经210 kΩ、二极管与50 kΩ串接形成偏置，实际辅助电流4.815 µA。模拟选择开关由gm/ID点得到初宽，实际在线性区工作，nominal Ron约23.36 Ω；饱和区余量要求不适用于该开关。

四码名义输出均为973.539 µA，误差2.6461%；独立权重最大误差4.4974%，权重比误差0.005814%。每码41个均匀点覆盖0.45–1.60 V，最坏电流变化0.08095%，局部输出电阻815.33 kΩ以上。参考端电压0.47885–0.49117 V，包含所有独立±5 µA扰动。辅助VDD已扣除100 µA外部参考，数字电流在模型中为零。

## 工程认识

相同L仍不够：电流镜用相同W/L单元并联，既避免单实例宽度超出模型范围，又避免把大幅改变W引入的模型宽度效应混入镜像比。所有参考与输出单元保持一致，最终四码名义电流重合。这里的m是原理图并联倍数，不是已完成的版图匹配阵列。

共栅输出使底部镜管的漏端接近0.218 V，显著隔离0.45–1.60 V的输出变化。单元VDS仍小于参考二极管的约0.485 V，因此存在约2.65%的总电流偏差；它符合合同，不应被误解为理想无误差复制。

只有1 mA标称值不能证明贡献比例正确。本例保留20个静态参考/代码组合、每码完整compliance扫描、±5 mV的局部输出电阻测量，以及参考引脚和电流端口检查。参考隔离和数字引脚的零值限定于该确定性模型与数值精度，不能推出真实漏电为零。

## 模型范围的纠正记录

初始输出支路按总宽度写成单个器件，部分宽度超过SMIC18 n18/p18模型的100 µm上限，出现CMI-2441。即使外部测量曾通过，也不能作为有效复现。相关运行标为invalid_model_dimensions并保留；最终改为并联单元后重新验证，模型日志无越界警告。项目现对该警告直接阻止完成判定。

'''
        head+=f'[LUT与并联单元记录]({e}sizing.json) · [HD来源与哈希]({e}hd_cells_manifest.json)\n\n'
    elif slot==3:
        head+='''## 电路与实测

本例独立实现自偏置源极退化放大器，未把第04项结果直接计入。β倍增n18单元5.04/0.36 µm，目标20 µA、gm/ID=16，MB2 m=4，RB=3 kΩ；输入每支同单元m=12.5，尾源m=25。p18镜18.76/1 µm。每侧RS=500 Ω、RL=1770 Ω。50 µA参考由14.88/1 µm n18终止，并驱动W0.24/L4 µm的弱启动下拉。DUT仅MOS与正值R，VCM端口保留但内部不用。

全部原nominal通过：1 MHz差分增益2.0008587 V/V、相对该增益的上端−3 dB带宽86.0638 MHz、全外部端口DC功耗1.079304 mW。3 MHz/100 mV差分峰值下，拟合基波增益1.9950292、SDR61.9817 dB、残差112.292 µVrms。原增益窗口1.98–2.02、带宽60 MHz、功耗1.5 mW和SDR60 dB均保持。

## 自偏置和退化分别解决什么

β倍增环使主管gm与RB相关，源极退化再降低有效跨导和信号非线性。实际输入gm4.078 mS、gmb1.000 mS，近似gm_eff=gm/[1+(gm+gmb)RS]，不能忽略体效应。MB2实际gm/ID21.04、处于弱反型，不能对整个自偏置环无条件使用强反型平方律。

主管电流22.068 µA；尾源25个相同单位却只流505.942 µA，因其VDS0.1794 V明显低于主管0.5220 V。相同W/L单元保证几何一致，不等于镜像电流无误差。尾源饱和余量77.64 mV；本次只作nominal，不宣称其余14个工艺温度点的增益均稳定。

## 迭代与测量

初版RL1900 Ω增益2.14485、基波增益2.13841，超出窗口。保持偏置及RS，将RL改为1770 Ω后增益回到目标，带宽80.25→86.06 MHz，SDR约61.98 dB。这次调整有明确的负载增益/极点依据，并保留两次运行。

SDR使用0.5–1.5 µs最终窗口的1001个等间隔样点，拟合DC+sin+cos，再求基波功率/残差均方。它不包含随机噪声。功耗统计VDD、VCM、VIN、VIP各端口功率绝对值；IREF已经从VDD供电，避免隐藏辅助端口功耗。

启动下拉采用第13项补充的窄管专属LUT，目标gm/ID8.558，实际8.591、电流0.372 µA。它持续导通并计入功耗；本任务没有冷启动斜坡门槛，也未为本电路额外宣称冷启动通过。4页PDF含开篇功能/应用说明、尺寸、工作点、频响、残差与精确网表。

'''
        head+=f'[完整LUT查询]({e}sizing.json) · [LUT副本]({e}lut/)\n\n'
    elif slot==4:
        head+='''## 设计与实测

输入对 n18 97.50/0.36 µm，每支目标250 µA、gm/ID=18；尾管由34.78/1 µm单元并联10个，参考管同W/L单个，gm/ID=16。源极退化每侧600 Ω，最终负载每侧1989 Ω，外部负载每侧1 pF。VCM保留端口，内部不取电。

实测：1 MHz差分增益2.002687 V/V，上端−3 dB带宽74.2695 MHz，总DC功耗0.958864 mW（包含50 µA参考）。3 MHz、100 mV差分峰值下，基波增益1.997394 V/V，正弦拟合SDR为63.8824 dB，残差RMS为90.3294 µV。全部原始nominal门槛通过。

## 工程认识

输入管实际gm=4.419 mS、gmb=1.073 mS，体效应不可忽略。有限ro之前的退化跨导近似gm/[1+(gm+gmb)RS]；只用gm/(1+gm·RS)会高估增益。输入源压0.3285 V，零体偏置LUT给出的尺寸须以实际OP确认；实测输入gm/ID=18.31。

初始RL=1900 Ω导致增益不足，调为1989 Ω提高增益并降低输出极点。但这两次旧运行的尾管写成W=347.8 µm单实例，超出PDK模型100 µm上限，故全部撤回。最终将尾管改为与参考完全同尺寸的10个并联单元，重新验证得到本页结果，日志无模型越界警告。旧数据保留在PDF迭代表中并明确标注失效。

尾管目标500 µA，实际482.70 µA；参考与输出镜管VDS不同，几何比并非精确电流比。尾节点仅0.1837 V、饱和余量81 mV，结论严格限定nominal。没有把这里的尾源余量外推到低压或PVT。

SDR沿用原测试的DC+sin+cos最小二乘拟合，窗口0.5–1.5 µs；它是指定刺激下的失真比，不含随机噪声。功耗检查保留VDD/VCM/VIN/VIP全部端口，避免用额外共模端口供电隐藏功耗。

'''
        head+=f'[完整 LUT 查询]({e}sizing.json)\n\n'
    elif slot==12:
        head+='''## 设计与实测

自偏置核心：MN1为n18 3.70/4 µm，MN2同单位m=4并在源极串PDK电阻；输出MOUT同单位m=4。PMOS镜每管9.38/1 µm。n18 L=4 µm缺失LUT已在本工程补扫，目标每支10 µA、gm/ID=7，预测VGS约0.657 V。最终MN1为9.742 µA、gm/ID=7.021。

RGM为原厂rpposab_3t，W=1 µm、L=36 µm、基底接VSS，实际11.850 kΩ。模型保留片阻、两侧蚀刻、电压/温度系数与基底电容。原任务不允许任意理想电阻代替工艺器件，本例使用SMIC对应模型。

最终输出39.1631 µA，Vref=0.656335 V，电气总功耗75.5330 µW。0.4–1.6 V输出扫描共121点，电流38.6367–39.6617 µA，峰峰值/均值为2.6134%，低于原8%限制。功耗包含0.9 V电流输出端口吸收的功率，不能只统计VDD。

1 µs和10 µs的0→1.8 V供电斜坡都从Vref=0自然启动。峰值/最终电流分别1.01147、1.00114；峰值正向VDD电流22.611/22.404 µA，正向供电能量0.41622/0.55709 nJ。两种情况下斜坡结束时已稳定在最终电流±10%内，因此按合同计的斜坡后建立时间为0；不表示物理电路瞬时启动。

## 启动支路：关断的是哪一部分

MPUP是W0.24/L4 µm的弱PMOS上拉，栅接VSS；当核心未工作时将nx拉高，MSTART下拉PMOS镜的na节点，启动偏置环。Vref升高后MDET把nx钳到29.86 mV，MSTART电流降到约3.3 pA。

MPUP和MDET仍流过3.072 µA，已经计入功耗。不能将注入晶体管关断写成整个启动电路零静态功耗。为了正确选这个全摆幅支路，另扫W=0.24 µm/L=4 µm、VSD=1.8 V的宽度专属LUT，把gm/ID范围延伸到1；在VSG=1.8 V处选到gm/ID=1.278，实际也是1.278。没有用gm/ID=8的中等反型点外推。

## 迭代和边界

RGM长度38.5 µm的初版输出34.744 µA，稍低于原35 µA下限，仅在10%容差放宽内。减至36 µm后达到原35–45 µA窗口；长沟道保持了输出电流平坦度。这里的“恒gm”结构不等同于跨工艺或温度精确恒定，本次没有运行另外26个PVT点或50次MC。

启动验收沿用正式测试定义：最后1 µs算最终电流；建立时间自斜坡结束起，之后所有样点须持续在±10%；能量只积分正向VDD功率至斜坡后10 µs。没有用预置非零节点替代冷启动。

'''
        head+=f'[LUT查询与器件选点]({e}sizing.json) · [本案例使用的LUT副本]({e}lut/)\n\n'
    elif slot==13:
        head+='''## 电路和实测结果

β倍增偏置主NMOS单元W19.94/L1 µm，目标45 µA、gm/ID=14；源退化支路m=4、尾源m=2、输入对各m=1。PMOS镜为42.20/1 µm，目标gm/ID=10。RB=1.45 kΩ、每侧RL=5.6 kΩ。外部50 µA参考由14.88/1 µm n18二极管终止，并控制W0.24/L4 µm启动下拉。

最终1 MHz差分增益3.601451 V/V，−3 dB带宽55.4226 MHz（相对1 MHz增益），1 GHz增益0.199794 V/V。负载压降VDD−VCM,out=259.777 mV，总功耗424.366 µW，包含参考与持续启动电流。对称确定性模型零输入差分不平衡为0；没有MC，因此不宣称真实失调为0。

61点±60 mV DC扫描中，±2 mV得到中心增量增益3.601900；±30 mV为3.571418、±60 mV为3.480033，最坏相对误差3.3834%，小于原8%。这项“增量增益误差”的口径不是全扫导数，也不是SFDR。

## 显式冷启动

Spectre skipdc=yes，从全部节点0 V开始。VDD/VCM在0.1–1.1 µs上升，IREF在1.2–1.22 µs由0升到50 µA，差分输入在10–10.02 µs由0升到20 mV。8–9 µs的零输入不平衡约5.3e−17 V；14–15 µs的绝对输出/20 mV为3.588420，前后负载压降259.777/259.785 mV，均满足原窗口。

启动波形中自偏置在IREF加载前已经随电源建立，说明该指定斜坡下寄生充放电也参与启动。这里只证明给定冷启动合同；不能由单条波形证明所有电源斜率或启动机制均稳健。启动下拉最终仍有0.3720 µA，并未关断，已经计入功耗。

## gm≈1/RB只是初算

RB1.2 kΩ初版自偏置电流偏高，增益4.195、功耗520.1 µW；增益连15%误差窗口也超出。保持W/L和RL，仅把RB提高到1.45 kΩ，全部原nominal通过。

最终主管电流46.998 µA、gm=0.64959 mS，gm×RB≈0.942。输入每支46.388 µA、gm=0.65120 mS、gm/ID=14.038。即使主/输入单位电流密度相近，输入源极约0.342 V的体效应使VGS从主管的0.5182 V提高至0.6080 V。中等反型、体效应、镜支路漏压差与有限ro意味着RL/RB=3.862不能直接当作3.601的实测增益。

## 窄启动管需要相应几何的查表依据

最初用Wref10 µm的L4表，以gm/ID=12、200 nA选得W0.24 µm；该窄管实际gm/ID约8.59、电流约372 nA。为解决这项具体差异，补扫同W0.24/L4、VDS1.35 V的nominal表。在参考二极管LUT预测VGS=0.54648 V处选到gm/ID=8.558、电流375.48 nA；实际VGS0.54572 V、gm/ID8.591，与选点一致。最终W/L保持不变，依赖的新表和表征PSF均保留。

所有原nominal指标通过；27点PVT的增益max/min≤1.15仍不在当前复现范围，不能用一个点自行构造比值1来宣称通过。4页PDF包含全部尺寸、工作点、启动/线性曲线及精确网表。

'''
        head+=f'[完整 LUT 查询]({e}sizing.json) · [使用的LUT副本]({e}lut/)\n\n'
    elif slot==16:
        head+='''## 设计与验收结果

NMOS差分对71.76/1 µm，目标70 µA/支、gm/ID=18；PMOS镜17.86/1 µm、gm/ID=5。NMOS偏置单元3.22/1 µm，参考/尾源/输出偏置分别m=5/14/5。第二级n18为13.04/0.36 µm、目标600 µA、gm/ID=5；p18输出电流源46.90/1 µm、m=12。串联补偿RZ=1.5 kΩ、CC=0.7 pF。

实测10 Hz增益79.1317 dB、UGB198.961 MHz、PM71.344°，10 Hz–10 GHz只跨越一次0 dB且无回穿。**UGB比原200 MHz少0.52%，所以完成标签为complete_10pct，不能写成原指标全通过。** 10%门槛为180 MHz，其他指标全部达到原门槛。

总功耗1.55411 mW，包含50 µA外部参考。噪声增益20的闭环−3 dB带宽14.0981 MHz，10 Hz积分到该带宽得22.500 µVrms。闭环PSRR+在1 kHz/1 MHz分别46.614/46.525 dB，CMRR在1 kHz为65.402 dB。

单位反馈连续跟踪范围0.300–1.38623 V，跨度1.08623 Vpp；低端只到原测试0.3 V扫描边界，不外推。100 mV阶跃的最坏建立时间4.3137 ns，最终误差1.20145 mV（1.20145%）。0.5 V大信号阶跃上/下压摆率153.05/155.48 V/µs。

## 第二级gm/ID不能孤立选择

初版第二级gm/ID=3时，输入两管漏压接近一致，静态输出误差仅0.127 mV、CMRR88.57 dB；但UGB150.90 MHz连15%门槛170 MHz也未达到，相位裕量57.49°。

保持电流和补偿，只把第二级目标gm/ID升至5，实际跨导从1.817升到3.046 mS，UGB和相位都改善。代价是第二级所需栅压由约0.991降到0.790 V，引起第一级输入对漏压差增大，系统失调变为1.165 mV，CMRR降至65.40 dB。两者仍满足原指标，但这个联合权衡是此例最重要的知识。

最终1/gm2约328 Ω，小于1.5 kΩ补偿电阻，对应左半平面零点的设计方向；完整回路仍按实际复数环路和无回穿条件验收，不能仅凭零点公式宣称稳定。

## 测量合同必须保留

环路沿用本题串联电压注入T=−Vout/Vinn，与44题的双注入实现不同，不能只因文件名相似混用。PSRR/CMRR也保持本题单位反馈外部注入定义。噪声频带由噪声增益20的独立AC测得，既不是固定10 MHz，也不是开环UGB。

建立时间检查两个方向到最后进入2 mV窗口，并另验收65/130 ns的终值误差。电气通过与完整PDF分别维护状态；本模块5页PDF包含波形、原/放宽边界、全部器件尺寸和最终网表。

'''
        head+=f'[完整 LUT 查询]({e}sizing.json)\n\n'
    elif slot==29:
        head+='''## 设计与验收

输入n18 W20.50/L1 µm，目标20 µA/支、gm/ID=18；p18折叠支路目标100 µA/支。折叠后约80 µA经PMOS共栅缓冲流入宽摆幅NMOS级联镜。第二级n18 W30.82/L0.36 µm、gm/ID=8、目标650 µA，p18镜像电流源供电。6.8 pF补偿直接返回输出侧PMOS共栅管的源端f2，不接第一级高阻输出stage1。

50 µA参考通过n18 W3.22/L1 µm单元m=5转换为偏置，尾源m=4、偏置支路m=2。p18偏置单元18.76/1 µm，折叠源m=5、输出源m=32.5。共栅单元p18为9.38/0.36 µm、n18为2.26/0.36 µm，工作支路各m=4；底部镜n18为12.30/1 µm。几何倍数是原理图参数，本次未生成版图单元阵列。

最终原nominal全部通过：20 pF增益99.1806 dB、UGB8.37480 MHz、PM96.4675°；63 pF为8.39476 MHz、95.7663°；200 pF为8.45106 MHz、93.4842°。每条1 Hz–300 MHz响应都仅一次下降交越，此后无回穿。单位反馈输出误差41.678 µV，总功耗1.71985 mW（含参考）。

200 pF的0.9→1.2→0.9 V阶跃，上/下建立时间121.264/96.327 ns；12/20 µs终值误差38.010/41.622 µV。时间从输入1%命令交越计算，目标是已知1.2/0.9 V，持续误差窗6 mV；没有用实际终值重新定义零误差。

## 偏置修正比只看门槛更有价值

初版RCN=11 kΩ时，NMOS镜VDS约177 mV、VDSAT约199 mV，处在线性区。外部增益86.17 dB、UGB8.37 MHz和相位等仍然达标，但它不符合级联镜的工作点意图，因此未交付。

把RCN提高到18 kΩ，抬升共栅栅压，使底部镜VDS约289 mV、饱和余量96 mV。输出阻抗恢复后增益提高约13 dB，输出误差从147降至41.7 µV，UGB几乎不变。相关原/修正版Spectre运行均保留；这不是模型尺寸越界，也没有撤销或修改PDK模型。

## 电流缓冲补偿的测量证据

补偿电流进入f2，再由PMOS共栅管传到stage1；返回低阻节点改变了相对于直接Miller跨级连接的前馈路径。输入实际gm约0.359 mS，gm/(2π·6.8 pF)约8.41 MHz，与20 pF下8.375 MHz接近。此近似只用于初算；200 pF、63 pF的稳定性来自各自实际复数响应，不能由轻载结果代替。

首次跌破−6 dB之后，20/63 pF仍有高频再抬升，最高分别−2.752/−5.175 dB；200 pF未高于−6 dB。都没有重新越过0 dB，但“首次交越相位裕量大”并不等同于“后续频段没有峰值”。原任务的回穿守卫因此必须保留。

AC保留原500 MΩ/50 mF直流伺服，频带内近似开环；瞬态用直接单位反馈。只复现tt/1.8 V/27°C，不宣称原45点或其他corner的63 pF守卫也通过。4页PDF已逐页检查，含全部器件尺寸、工作点、曲线和精确电路。

'''
        head+=f'[完整 LUT 查询]({e}sizing.json)\n\n'
    elif slot==41:
        head+='''## 设计和完整nominal结果

输入n18为30.76/1 µm，目标30 µA/支、gm/ID=18；NMOS偏置单元3.22/1 µm、gm/ID=12，参考/尾源/输出电流源/共栅偏置分别m=5/6/14/1。所有PMOS使用同一3.14/0.36 µm单元、gm/ID=10；镜负载和共栅管各m=3，第二级m=14，偏置二极管m=1。补偿700 Ω串2 pF；外部负载始终2 pF。

原nominal全部通过：10 Hz增益88.5831 dB、UGB38.0852 MHz、相位裕量64.5454°、总功耗471.164 µW（含50 µA参考）。静态单位反馈输出误差16.054 µV。噪声增益20的闭环带宽2.14287 MHz；10 Hz至该频率输入积分噪声23.2385 µVrms。1 kHz/1 MHz闭环PSRR+为90.8303/32.4615 dB，1 kHz CMRR89.7416 dB。

0.3–1.5 V整个原扫描范围都满足20 mV连续跟踪条件，仅声明1.2 Vpp，不外推到扫描边界外。100 mV上/下阶跃建立15.9493/17.4775 ns，最坏终值误差16.1346 µV（0.0161346%）。0.5 V上/下阶跃压摆率28.7094/26.5581 V/µs。频率、时序、负载、双向动态检查均保留原任务口径。

## 单元电流密度和漏压对齐

第二级PMOS与第一级镜负载使用相同W/L单位，通过m分别承载约140 µA和30 µA。相近的单位电流密度使其VSG相近，输入两管漏压1.17225/1.17703 V仅相差4.774 mV。本次确定性系统失调很小；没有执行MC，不能由此宣称随机失调同样只有16 µV。

级联PMOS镜提高第一级阻抗并抑制供电扰动。22 kΩ源端电阻让偏置二极管的源极1.57631 V，与两个共栅管的源极1.57599/1.57603 V接近，因而体偏置也接近。实际偏置VBP=0.88527 V。

## 饱和余量和补偿的边界

共栅支路消耗额外电压空间：上层MPM的VSD=223.97 mV、VSDSAT=179.04 mV，余量只有44.93 mV。nominal所有相关管处在饱和区，但这不构成跨PVT稳健性的证据。高增益、高PSRR和低失调都应与这个余量一起记录。

第二级实际gm=1.42786 mS，1/gm=700.35 Ω，接近串联补偿电阻700 Ω。近似抵消前馈零点是选值依据；最终仍验收实际复数环路，确认相位裕量64.55°和无0 dB回穿。

## 测量可比性

沿用原题电压注入T=−Vout/Vinn，不能混用第44题的双注入定义。闭环PSRR/CMRR均为指定单位注入下的−20log10|Vout|。噪声积分终点来自独立噪声增益20的AC测试。压摆刺激在10/71 ns开始，保留本题时序，不直接复用第16题较长时序。三次最终Spectre运行没有模型尺寸越界；5页PDF已逐页审查。

'''
        head+=f'[完整 LUT 查询]({e}sizing.json)\n\n'
    elif slot==44:
        head+='''## 设计与实测

输入对 n18 92.96/1.0 µm，以每支90 µA、gm/ID=18查询SMIC18 LUT；PMOS镜 p18 10.52/0.36 µm，gm/ID=6；尾源/参考 n18 同L=1 µm，宽39.92/11.10 µm。所有尺寸都有LUT路径与SHA-256。

实测：环路增益43.144 dB，UGB 173.009 MHz，PM 81.526°，功耗409.838 µW（含50 µA参考），10 Hz–10 MHz输入噪声19.517 µVrms。自然开环CMRR 79.929 dB，PSRR+ 42.911 dB，PSRR− 79.900 dB。无需使用10%–15%的放宽。

## 工程认识

输入对用长沟道与较高gm/ID获得增益/噪声性能；镜负载取较短沟道、较低gm/ID保持镜节点速度。本例说明“所有信号器件同样加长”并不是必要条件。

零体偏置LUT只是初值：输入管实际VSB约0.345 V，实测gm/ID=18.29，仍接近选点；尾源目标180 µA，实际177.69 µA。保留这一预测/工作点差异，比只记最终W/L更有价值。

双注入Middlebrook与输入噪声台保持DC闭环；CMRR/PSRR另用自然开环DC工作点。DC标量包含带PROP的器件量及不带PROP的节点/源电流，解析时不能只读前者。

'''
        head+=f'[完整 LUT 查询]({e}sizing.json) · [原知识：5T分析](../../5T-Differential-Amplifier-Analysis.md)\n\n'
    elif slot==45:
        head+='''## 实现与实测

DRNQNHDV1 的D接QN形成T触发器；INHDV2把高有效reset转为FF的低有效RDN；NOR2HDV16用QN和reset生成clkout。内部状态被真正复位，外部门仅增加快速输出拉低路径。所有HD单元的晶体管尺寸保持原厂CDL。

实测：原1 GHz输入下输出500.031 MHz；高占空比49.9376%–49.9471%；最大时钟延迟304.49 ps；复位延迟26.78 ps。复位保持与异步释放保持分别约8.99/7.66 mV，下一有效沿后输出1.792 V；原100 ps复位、400 ps延迟和49%–51%占空比均通过。

## 失败迭代带来的认识

FF V1 + NOR V4 的占空比48.391%，FF V4 + NOR V8仍只有48.507%，均超出15%放宽后的误差窗口。最终FF V1 + NOR V16合格，代价是时钟延迟增加但仍低于400 ps。驱动档位同时改变负载和上/下沿传播差，不能以“所有门加大”代替波形检查。

只有输出钳位而没有清除内部FF状态，会破坏释放后的语义。本方案同时使用内部异步复位和输出快速路径，并保留1.85–2.04 ns、2.05–2.20 ns及2.70 ns的分段验收。

此模块是纯数字标准单元实现，不重设计其内部MOS；模拟模块仍按gm/ID LUT要求执行。

'''
        head+=f'[HD 单元来源与哈希]({e}hd_cells_manifest.json)\n\n'
    else:
        body=(case/'knowledge.md').read_text().rstrip()
        # Some worker drafts are standalone notes with their own opening.
        # Use the shared title/overview above and preserve their detailed body.
        if '\n## ' in body and (body.startswith('# ') or '\n# ' in body.split('\n## ',1)[0]):
            body='## '+body.split('\n## ',1)[1]
        if slot in (11,21):
            def evidence_link(match):
                target=match.group(1)
                if target.startswith(('/', '#')) or '://' in target:return match.group(0)
                resolved=(case/target).resolve()
                if resolved.is_relative_to(case):
                    return ']('+e+str(resolved.relative_to(case))+')'
                return ']('+str(resolved)+')'
            body=re.sub(r'\]\(([^)]+)\)',evidence_link,body)
        head+=body+'\n\n'
        if (case/'sizing.json').exists():head+=f'[完整 LUT 查询]({e}sizing.json)\n\n'
        if (case/'hd_cells_manifest.json').exists():head+=f'[HD 单元来源与哈希]({e}hd_cells_manifest.json)\n\n'
    head+='## 复现与证据\n\n'
    if (case/'schematic_audit.json').exists():
        fig=json.loads((case/'schematic_audit.json').read_text())
        head+=f'[完整电路总图 SVG]({e}schematic/full.svg) · [总图 PDF]({e}schematic/full.pdf) · [{fig["sheets"]}页电路分图]({e}schematic/sheets.pdf) · [引脚与层次连接映射]({e}schematic/connectivity.json) · [图纸审计]({e}schematic_audit.json)\n\n'
    runs=result.get('run_dirs',[result.get('run_dir')])
    for run in runs:head+=f'- [Spectre 运行记录]({ROOT/run}/run.json) · [原始输出]({ROOT/run}/output/bench.raw/)\n'
    head+=f'- [工程脚本]({ROOT}/scripts/) · [项目状态]({ROOT}/status.json)\n'
    head+='\n原Sky130案例保持原样；本页是目标工艺实测的新记录。模型文件留在既有本地PDK目录，没有上传或修改。\n'
    (KB/'cases').mkdir(parents=True,exist_ok=True);(KB/'cases'/f'{slug}.md').write_text(head)

def index():
    KB.mkdir(parents=True,exist_ok=True)
    state=json.loads((ROOT/'status.json').read_text());ready=[c for c in state['cases'] if c.get('nominal_complete') and c.get('review_pdf_ready')]
    diagrams=[json.loads((ROOT/'cases'/NAMES[c['slot']][0]/'schematic_audit.json').read_text()) for c in ready if c['slot'] in NAMES and (ROOT/'cases'/NAMES[c['slot']][0]/'schematic_audit.json').exists()]
    diagram_summary=''
    if diagrams:
        diagram_summary=f"现有 **{len(diagrams)}份报告含完整电路图，共{sum(d['sheets'] for d in diagrams)}页图纸**；模拟部分绘制晶体管及工艺无源，数字部分使用原厂标准单元符号。各份报告及总图见下表。2026-09-23的历史26项补图记录保存在[原目录]({ROOT}/reports/schematic-retrofit-index.md)，该历史批次没有新增仿真或修改电气结果。\n\n"
    if any(c['slot']==11 for c in ready):
        diagram_summary+='2026-09-26新增第11项一阶带隙基准：TT范围内14项原门槛全部通过，11页PDF含3页完整电路图。20项测量交叉核对及27实例/94端子核对通过；本次对话授权完成知识库更新。其余模块未启动。\n\n'
    if any(c['slot']==21 for c in ready):
        diagram_summary=diagram_summary.replace('其余模块未启动。','随后按用户继续工作指令推进剩余模块。')
        diagram_summary+='2026-09-26续作完成第21项高PSRR带隙：5项TT原门槛通过，低频/1MHz抑制70.625/35.392dB，126点温漂40.308ppm/°C；11页PDF含3页完整图纸。\n\n'
    text=f'''# SMIC18 Benchmark 复现知识库

目标为全部50项，在SMIC18MMRF nominal条件下完成模拟gm/ID设计、HD数字单元实现、指标验证及每模块可审查PDF。当前已完成电气验证和PDF交付 **{len(ready)}/50**，其余尚未完成，后续按用户安排继续；不能把Sky130历史通过计入本统计。

工作工程：[smic18_benchmark_repro]({ROOT}/README.md)。允许10%–15%性能下降的换算规则见 [验收规则]({ROOT}/contracts/acceptance-policy.md)。原始工艺学习资料在 [Analog Design Bench V2](../Analog-Design-Bench-V2-Lessons/README.md)，不做覆盖。

{diagram_summary}\
| 编号 | 原任务 | 状态 | 本地知识/PDF |
|---|---|---|---|
'''
    for c in state['cases']:
        slot=c['slot'];ready_case=c.get('nominal_complete') and c.get('review_pdf_ready')
        link='待完成'
        if ready_case and slot in NAMES:
            slug,_=NAMES[slot];link=f'[知识笔记](cases/{slug}.md) · [PDF](evidence/{slug}/review.pdf)'
            if (KB/'evidence'/slug/'schematic/full.svg').exists():link+=f' · [电路总图](evidence/{slug}/schematic/full.svg)'
        text+=f"| {slot:02d} | {c['source_task_id']} | {c['status']} | {link} |\n"
    text+='\n本目录仅新增用户授权的SMIC18复现记录；其他知识库文件保持不变。所有结果为原理图级本地仿真，不等同于PVT或版图签核。\n'
    (KB/'README.md').write_text(text)

if __name__=='__main__':
    rows=json.loads((ROOT/'status.json').read_text())['cases']
    for n in NAMES:
        if rows[n-1].get('nominal_complete') and rows[n-1].get('review_pdf_ready'):publish(n)
    index()
