"""Mermaid architecture views of the implemented multi-block reproductions.

These describe the actual module and its fixture, not an imagined complete chip.
Transistor connectivity remains in circuit.scs and the accompanying schematics.
"""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
DIAGRAMS={}

def define(slot,title,dut,external,edges,note):
    nodes=dict(dut+external);assert len(nodes)==len(dut)+len(external)
    direction='TB'
    lines=[f'flowchart {direction}','    subgraph DUT["DUT"]',f'        direction {direction}']
    lines += [f'        {key}["{label}"]' for key,label in dut];lines+=['    end']
    for key,label in external:
        if slot==5 and key=='CAP':
            lines += ['    subgraph AUX["外部储能"]',f'        {key}["{label}"]','    end']
        else:
            lines += [f'    {key}["{label}"]']
    for a,b,label,control in edges:
        assert a in nodes and b in nodes,(slot,a,b)
        arrow='-.->' if control else '-->';tag=f'|"{label}"|' if label else ''
        lines.append(f'    {a} {arrow}{tag} {b}')
    DIAGRAMS[slot]=dict(title=title,mermaid='\n'.join(lines)+'\n',note=note,nodes=nodes,edges=edges)

define(1,'Class-D半桥',
 [('PH','交叉反馈非交叠时序'),('DRV','分级栅驱动'),('PWR','PMOS上管 / NMOS下管')],
 [('CLK','5MHz时钟'),('LC','固定串联LC'),('LOAD','电阻负载')],
 [('CLK','PH','时钟',True),('PH','DRV','互补控制',True),('DRV','PWR','栅驱动',True),('PWR','LC','开关节点',False),('LC','LOAD','功率',False)],
 '本例是固定时钟驱动的功率级，LC和电阻是外部负载；没有实现音频调制器。')
define(2,'可编程电流镜',
 [('DEC','HD独热译码'),('MIR','两组参考镜与四组权重支路'),('SW','模拟选择开关'),('CAS','共享共栅输出')],
 [('CODE','2位控制码'),('REF','ICC / IPTAT参考电流'),('OUT','输出电流端口与扫描负载')],
 [('CODE','DEC','',True),('REF','MIR','参考',False),('MIR','SW','加权电流',False),('DEC','SW','选择',True),('SW','CAS','',False),('CAS','OUT','Iout',False)],
 '译码只控制模拟电流支路；电流端口的外部电压源属于测量夹具。')
define(5,'全NMOS半桥自举驱动',
 [('NON','HD非交叠与延迟链'),('LS','低侧驱动'),('LVL','高侧电平转换'),('HS','浮动高侧驱动'),('BST','互锁补电 / MIM与MOS存储 / 跟随支路')],
 [('CLK','输入时钟'),('BR','外部全NMOS半桥'),('LOAD','负载及封装寄生'),('CAP','200pF外部自举电容')],
 [('CLK','NON','',True),('NON','LS','低侧指令',True),('NON','LVL','高侧指令',True),('LVL','HS','',True),('LS','BR','GN2',True),('HS','BR','GN',True),('BR','LOAD','开关节点',False),('NON','BST','低侧指令互锁',True),('BST','HS','浮动供电',False),('CAP','BST','储能',False),('BR','BST','VLX / VSW跟随',False)],
 '驱动器是DUT；功率MOS、负载、封装寄生和指定外部自举电容按原夹具单列。')
define(6,'三级环形放大器',
 [('IN','交流耦合输入与弱启动'),('MID','中间动态增益级'),('OUT','Class-AB输出级')],
 [('VIN','差分输入'),('FB','采样 / 反馈电容'),('RST','复位与自调零夹具'),('LOAD','输出负载')],
 [('VIN','FB','采样',False),('FB','IN','误差信号',False),('IN','MID','',False),('MID','OUT','',False),('OUT','FB','电容反馈',False),('OUT','LOAD','',False),('RST','IN','自调零',True),('RST','MID','复位',True),('RST','OUT','复位',True)],
 '图中保留外部开关电容闭环和复位边界；三级信号路径对应DUT，目标闭环增益约8。')

for slot,kind,amp,driver,target in [(7,'PMOS LDO','5T误差放大器','栅极缓冲及补偿','1.2V'),(17,'NMOS LDO','低共模PMOS输入放大器','电流镜电平转换与MIM补偿','0.4V'),(38,'无外部电容LDO','自偏置误差放大器','内部Miller / 前馈补偿','1.0V')]:
    define(slot,kind,[('ERR',amp),('DRV',driver),('PASS',('NMOS' if slot==17 else 'PMOS')+'功率管'),('FB','输出反馈网络')],[('REF','参考电压'),('SUP','输入电源'),('LOAD',target+'输出与指定负载')],[('REF','ERR','设定值',False),('ERR','DRV','误差',False),('DRV','PASS','栅控制',True),('SUP','PASS','供能',False),('PASS','LOAD','稳压输出',False),('LOAD','FB','取样',False),('FB','ERR','负反馈',False)],'反馈、补偿和功率管构成同一稳压环路；参考与负载按本题合同保留。')
define(9,'CML二分频',[('M','主CML锁存器'),('S','从CML锁存器'),('BIAS','尾电流偏置')],[('CLK','差分输入时钟'),('OUT','差分除二输出及负载')],[('CLK','M','一相',True),('CLK','S','另一相',True),('M','S','差分状态',False),('S','M','反相反馈',False),('S','OUT','',False),('BIAS','M','尾电流',True),('BIAS','S','尾电流',True)],'主从锁存闭环实现除二；本例没有完整PLL或额外复位控制器。')
define(15,'未稳压电荷泵',[('EN','HD使能门控与双相驱动'),('FLY','飞跨电容与交叉预充'),('RECT','双相整流及输出存储')],[('CLK','时钟 / EN'),('VDD','1.8V电源'),('LOAD','固定负载及Vout')],[('CLK','EN','',True),('EN','FLY','两相驱动',True),('VDD','FLY','充电',False),('FLY','RECT','电荷转移',False),('RECT','LOAD','升压输出',False)],'电路没有稳压反馈；独立关闭电流沿用使能端口测试。')
define(18,'稳压电荷泵',[('CLKG','HD使能 / 两相逻辑'),('DRV','可调幅度时钟驱动'),('PUMP','飞跨电容与整流'),('FB','输出分压'),('EA','误差放大及PMOS调节')],[('CLK','时钟 / EN'),('VDD','1.8V电源与参考'),('LOAD','约2.34V输出 / 三档负载')],[('CLK','CLKG','',True),('CLKG','DRV','双相',True),('EA','DRV','vclk供电调幅',False),('VDD','EA','电源 / 参考',False),('VDD','PUMP','充电',False),('DRV','PUMP','搬运电荷',False),('PUMP','LOAD','',False),('LOAD','FB','',False),('FB','EA','负反馈',False)],'反馈改变时钟驱动幅度，未把该电路画成PWM或变频控制器。')
define(19,'2:1开关电容变换器',[('PH','HD非交叠相位'),('A','A组开关与飞跨电容'),('B','B组交错开关与飞跨电容'),('OUT','输出汇流 / 存储')],[('CLK','20MHz时钟'),('VDD','输入电源'),('LOAD','轻 / 重负载')],[('CLK','PH','',True),('PH','A','串充 / 并放',True),('PH','B','交错两相',True),('VDD','A','',False),('VDD','B','',False),('A','OUT','',False),('B','OUT','',False),('OUT','LOAD','约Vin的一半',False)],'固定频率开环电荷转移；没有额外误差放大器或负载调频环。')
define(20,'八选一模拟MUX',[('CTRL','HD控制反相'),('S1','第一级4个2:1传输门选择'),('S2','第二级2个2:1选择'),('S3','第三级1个2:1选择')],[('VIN','8路模拟输入'),('SEL','3位地址'),('OUT','输出及负载')],[('VIN','S1','',False),('S1','S2','',False),('S2','S3','',False),('S3','OUT','',False),('SEL','CTRL','',True),('CTRL','S1','最低位',True),('CTRL','S2','中间位',True),('CTRL','S3','最高位',True)],'实际实现为三级二选一树，未画成未实现的八路独热译码器。')
define(22,'差分自举采样驱动',[('BST','两路预充 / 自举存储'),('GATE','跟随输入的栅驱动')],[('CLK','采样时钟'),('VIN','差分输入'),('SW','受驱采样开关与固定负载')],[('CLK','BST','预充 / 跟踪',True),('VIN','BST','源端跟随',False),('BST','GATE','提升栅压',False),('GATE','SW','栅控制',True),('VIN','SW','模拟信号',False)],'框图描述自举驱动及其受驱采样夹具；器件保护和端电压仍以原理图为准。')
define(23,'5位开关电阻DAC',[('DRV','5路HD位驱动'),('SW','按位互补开关'),('R','原生电阻按1/2/4/8/16并联加权')],[('CODE','5位数字输入'),('REF','电源 / 地参考'),('OUT','电压输出及负载')],[('CODE','DRV','',True),('DRV','SW','逐位控制',True),('REF','SW','两参考轨',False),('SW','R','支路电压',False),('R','OUT','加权汇流',False)],'这是二进制加权电阻支路，非电阻串抽头译码结构。')
define(26,'OTA-C双二阶',[('G1','输入跨导与第一积分电容'),('BP','差分带通状态'),('G2','前向跨导与第二积分电容'),('LP','差分低通输出'),('DAMP','阻尼跨导'),('CM','两个状态各自的CMFB')],[('VIN','差分输入'),('REF','偏置电流 / 共模参考')],[('VIN','G1','',False),('G1','BP','',False),('BP','G2','',False),('G2','LP','',False),('LP','G1','反向跨导反馈',False),('BP','DAMP','状态取样',False),('DAMP','BP','阻尼电流',False),('BP','CM','共模取样',False),('LP','CM','共模取样',False),('REF','CM','设定值',True),('CM','G1','共模控制',True),('CM','G2','共模控制',True)],'差模二阶环路和两路共模反馈分别标明；不是简单串联两个独立低通。')

for slot,bits,count,sampling in [(27,4,15,True),(46,3,7,False)]:
    dut=[('REFS',f'{count}个电阻参考阈值'),('CMP',f'{count}路动态比较器'),('LAT','HD锁存温度计码'),('ENC',f'HD编码与{bits}位输出')]
    edges=[('REF','REFS','',False),('REFS','CMP','阈值',False),('CMP','LAT','判决',False),('LAT','ENC','温度计码',False),('ENC','OUT','二进制码',False),('CLK','CMP','评估 / 复位',True)]
    if sampling:dut.insert(0,('SH','共享差分采样保持'));edges += [('VIN','SH','',False),('SH','CMP','保持信号',False),('CLK','SH','采样相',True)]
    else:edges += [('VIN','CMP','模拟信号',False)]
    define(slot,f'{bits}位Flash ADC',dut,[('VIN','模拟输入'),('REF','外部参考电压'),('CLK','外部时钟'),('OUT','数字读数')],edges,'比较器、锁存和编码均在DUT；输入、参考和时钟属于固定测试端口。')
define(28,'FCT余量放大器',[('IN','交叉输入与复位'),('RES','浮动电荷库与偏置复位'),('AMP','浮动共源共栅及输出使能'),('CLKD','原厂HD时钟缓冲')],[('VIN','10 / 20mV差分输入'),('SC','400fF飞跨采样夹具'),('CLK','900MHz采样 / 转移时钟'),('HOLD','输出跟踪开关与50fF保持负载')],[('VIN','SC','',False),('SC','IN','采样电荷',False),('IN','RES','转移',False),('RES','AMP','储能与驱动',False),('AMP','HOLD','余量输出',False),('CLK','CLKD','',True),('CLKD','IN','复位 / 转移',True),('CLKD','RES','复位',True),('CLKD','AMP','输出使能',True),('CLK','SC','采样',True),('CLK','HOLD','原读数时序',True)],'FCT仅为余量放大子模块；外部飞跨/保持网络按原测试保留，不代表已完成整条流水线ADC。')
define(31,'差分底板采样',[('TIM','HD关断顺序控制'),('SW','信号端 / 底板开关'),('CAP','差分采样保持电容')],[('VIN','差分模拟输入'),('CLK','时钟与共模参考'),('OUT','保持输出及原负载')],[('VIN','SW','',False),('CLK','TIM','',True),('TIM','SW','先后关断',True),('SW','CAP','采样电荷',False),('CAP','OUT','保持值',False)],'图表示采样和底板关断时序，后级量化器不在本例范围。')
define(32,'28Gb/s CML发送末级',[('INL','输入串联峰化'),('CORE','单级差分电流转向'),('OUTL','输出串联峰化与中和'),('BIAS','原生尾电流偏置')],[('NRZ','差分NRZ输入'),('TERM','两路50Ω上拉终端'),('OUT','固定负载与眼图测量')],[('NRZ','INL','28Gb/s',False),('INL','CORE','',False),('BIAS','CORE','尾电流',True),('CORE','OUTL','',False),('TERM','OUTL','终端负载',False),('OUTL','OUT','差分输出',False)],'只覆盖发送末级与原固定负载；没有SERDES协议逻辑、均衡器或物理信道模型。')
for slot,gain in [(33,1),(34,8)]:
    define(slot,f'电容反馈增益{gain}放大子系统',[('OTA','折叠输入与对称第二级'),('CM','连续共模反馈')],[('VIN','差分采样输入'),('CS','采样电容Cs'),('CF','反馈电容Cf'),('CLK','采样 / 复位开关夹具'),('LOAD','差分输出与负载'),('REF','共模参考')],[('VIN','CS','采样',False),('CS','OTA','差分误差',False),('OTA','LOAD','',False),('LOAD','CF','输出取样',False),('CF','OTA',f'Cs/Cf={gain}',False),('CLK','CS','采样 / 复位',True),('CLK','CF','复位',True),('LOAD','CM','平均值',False),('REF','CM','',True),('CM','OTA','共模控制',True)],'电容网络与时序是外部闭环夹具，核心DUT为全差分OTA；还保留原报告中的其他独立测量维度。')
define(39,'闭环线驱动',[('AMP','差分输入与镜像增益级'),('AB','浮动Class-AB输出'),('COMP','双路Miller补偿')],[('VIN','信号源 / 输入电阻'),('FB','外部反相反馈'),('LOAD','300Ω交流耦合线路与200pF负载')],[('VIN','AMP','',False),('AMP','AB','',False),('AB','LOAD','',False),('AB','FB','输出取样',False),('FB','AMP','负反馈',False),('AB','COMP','',False),('COMP','AMP','补偿',False)],'框图显示反相闭环、功率输出和外部线路边界；不引入未实现的收发协议。')
define(40,'一阶开关电容ΔΣ调制器',[('SC','输入采样 / 差分电荷求和 / Cs与Ci'),('HOLD','互补判决保持'),('DAC','一位反馈DAC')],[('VIN','低频差分输入'),('OTA','原生外部OTA夹具'),('CMP','原生外部比较器夹具'),('CLK','10MHz两相与比较时钟'),('REF','参考电压与共模'),('BIT','原始一位码流')],[('VIN','SC','',False),('SC','OTA','差分误差',False),('OTA','SC','Ci积分反馈',False),('OTA','CMP','积分状态',False),('CMP','HOLD','判决',False),('HOLD','DAC','上一拍判决',True),('DAC','SC','负反馈电荷',False),('CMP','BIT','原判决节点读出',False),('REF','SC','共模设定',True),('REF','DAC','两参考轨',False),('CLK','SC','采样 / 转移',True),('CLK','CMP','比较时钟',True),('CLK','HOLD','保持相位',True)],'OTA与比较器按原题归为明确迁移的外部晶体管夹具；本次只实现模拟调制器，没有数字抽取滤波器。')
for slot,bits,front in [(42,6,'差分自举采样'),(48,4,'差分传输门采样')]:
    define(slot,f'{bits}位异步SAR ADC',[('S',front),('D','双支路电容DAC'),('C','动态比较器'),('L','HD异步控制与判决寄存'),('R',f'完成后锁存{bits}位输出')],[('VIN','差分输入'),('REF','参考电压'),('CLK','外部采样时钟'),('OUT','数字读数')],[('VIN','S','',False),('S','D','采样电荷',False),('REF','D','',False),('D','C','差分余量',False),('C','L','判决 / valid',False),('L','D','逐位试探',True),('L','C','内部比较时钟',True),('L','R','EOC / 判决位',True),('R','OUT','',False),('CLK','S','采样',True),('CLK','L','复位 / 转换启动',True)],'CDAC、比较器及异步握手均为实际DUT；内部比较时钟由有效判决推进，不能画成外部理想逐位控制。')
define(45,'HD二分频',[('RST','复位极性转换'),('FF','HD翻转触发器反馈'),('GATE','复位输出门控')],[('CLK','输入时钟'),('RESET','异步复位'),('OUT','除二时钟与负载')],[('CLK','FF','',True),('RESET','RST','',True),('RST','FF','异步复位',True),('FF','FF','反相状态反馈',False),('FF','GATE','',False),('RESET','GATE','输出钳位',True),('GATE','OUT','',False)],'对应原厂DRNQN触发器及输出NOR门；不包含完整计数器或PLL。')
define(47,'电流转向电荷泵',[('LOG','UP / DN互补开关控制'),('BIAS','复制偏置与级联电流源'),('STEER','上下电流转向支路')],[('CTRL','UP / DN脉冲'),('REF','参考电流'),('OUT','电流输出端口与固定测量负载')],[('CTRL','LOG','',True),('REF','BIAS','',False),('BIAS','STEER','持续偏置电流',False),('LOG','STEER','注入 / 抽取',True),('STEER','OUT','脉冲电荷',False)],'本例只有电荷泵；鉴相器、环路滤波器和VCO未作为已实现的PLL系统画入。')

def append(case):
    slot=int(case.name[:2])
    if slot not in DIAGRAMS:return False
    q=DIAGRAMS[slot];mmd=case/'system_block_diagram.mmd';mmd.write_text(q['mermaid'])
    md=case/'review_report.md'
    if not md.exists():return False
    s=md.read_text();s=re.sub(r'<!-- SYSTEM-BLOCK-DIAGRAM -->.*?<!-- END-SYSTEM-BLOCK-DIAGRAM -->\n*','',s,flags=re.S)
    block='<!-- SYSTEM-BLOCK-DIAGRAM -->\n## 系统框图\n\n'+q['note']+'\n\n实线表示信号或能量通路，虚线表示时钟、控制或偏置。DUT框外为外部端口或测试夹具；精确端子连接见后附基本电路图。\n\n```mermaid\n'+q['mermaid']+'```\n\n[独立Mermaid源文件](system_block_diagram.mmd) · [框图SVG](markdown_assets/system-block.svg)\n<!-- END-SYSTEM-BLOCK-DIAGRAM -->\n\n'
    pos=s.find('\n## ');assert pos>=0;md.write_text(s[:pos+1]+block+s[pos+1:])
    receipt=case/'markdown_provenance.json'
    if receipt.exists():
        r=json.loads(receipt.read_text());r.setdefault('restored_markdown_sha256',r['markdown_sha256']);r['markdown_sha256']=hashlib.sha256(md.read_bytes()).hexdigest();r['system_diagram_sha256']=hashlib.sha256(mmd.read_bytes()).hexdigest();receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    return True

if __name__=='__main__':
    added=[]
    for case in sorted((ROOT/'cases').iterdir()):
        if case.is_dir() and re.match(r'\d\d-',case.name) and append(case):added.append(int(case.name[:2]))
    print(json.dumps(dict(system_cases=sorted(DIAGRAMS),embedded_cases=added),ensure_ascii=False))
