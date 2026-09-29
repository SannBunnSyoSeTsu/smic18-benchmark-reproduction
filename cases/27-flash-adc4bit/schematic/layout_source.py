from schematic_common import *
from schematics_analog import mos,link,bus,finish

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    if i==1:
        for k in range(16):
            row=k//8;x=4+5*(k%8);y=20-row*12;s.passive(f'RL{k+1}',x,y,vertical=False,reverse=True)
            if k%8:link(s,f'RL{k}','1',f'RL{k+1}','2')
    elif i==2:
        s.cell('XCLK',8,18);s.cell('XSP',23,18);s.cell('XSN',23,7)
        s.passive('CHP',37,18);s.passive('CHN',37,7)
    elif 3<=i<=10:
        for j,k in enumerate(range(1+2*(i-3),min(3+2*(i-3),16))):
            y=18-12*j
            for pol,yy in [('p',y+2),('n',y-2)]:
                s.passive(f'R{k}{pol}A',4,yy,vertical=False);s.passive(f'R{k}{pol}B',13,yy,vertical=False,reverse=True)
                link(s,f'R{k}{pol}A','2',f'R{k}{pol}B','2')
            s.cell(f'XC{k}',25,y);s.cell(f'XS{k}',38,y)
            link(s,f'XC{k}','outp',f'XS{k}','rn',via=[(31,y+.5),(31,y-.5)])
    elif 11<=i<=13:
        names=[n for n in dev if n.startswith(('XE','XB'))];chunk=names[(i-11)*12:(i-10)*12]
        for k,n in enumerate(chunk):s.cell(n,5+(k%4)*11,20-(k//4)*8)
    elif i==14:
        mos(s,[('MPL1',8,21),('MPL2',23,21),('MNL1',8,14),('MNL2',23,14),('MIN1',8,8),('MIN2',23,8),('MTAIL',16,4)]+[(f'MPC{k+1}',38,22-k*6) for k in range(4)])
        for p,n,inp in [('MPL1','MNL1','MIN1'),('MPL2','MNL2','MIN2')]:link(s,p,'D',n,'D');link(s,n,'S',inp,'D')
        bus(s,'tail',[('MIN1','S'),('MIN2','S'),('MTAIL','D')],6);bus(s,'vdd',[('MPL1','S'),('MPL2','S')],24)
    elif i==15:
        mos(s,[('MN',12,13),('MP',31,13)])
        link(s,'MN','D','MP','D',via=[(12,20),(39,20),(39,12)])
        link(s,'MN','S','MP','S',via=[(12,5),(23,5),(23,14)])
    else:
        s.cell('XG1',10,16);s.cell('XG2',32,16)
        link(s,'XG1','ZN','XG2','A2',via=[(22,16),(22,15.5)])
        link(s,'XG2','ZN','XG1','A2',via=[(39,16),(39,8),(5,8),(5,15.5)])
    return finish(s)

def main():
    titles={1:'16段差分参考电阻梯',2:'互补采样时钟与共享差分保持',**{i:f'阈值通道{1+2*(i-3)}–{min(2+2*(i-3),15)}：混合、比较与保持' for i in range(3,11)},**{i:f'HD温度计码编码与输出缓冲 {i-10}/3' for i in range(11,14)},14:'fa_comp：全部动态模拟比较器晶体管',15:'fa_sample：原生互补传输门并联单元',16:'fa_sr：两只原厂NAND的反馈连接'}
    blocks={i:'flash_adc_4bit' for i in range(1,14)};blocks.update({14:'fa_comp',15:'fa_sample',16:'fa_sr'});make_case(27,titles,layout,blocks)

if __name__=='__main__':main()
