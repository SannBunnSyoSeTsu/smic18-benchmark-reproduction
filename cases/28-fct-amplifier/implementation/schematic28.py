from schematic_common import *
from schematics_analog import finish
PLAN={}

def layout(ax,i,dev):
    s=Sheet(ax,i,dev)
    for j,n in enumerate(PLAN[i]):
        x=[8,22,36][j%3];y=21-9*(j//3)
        if dev[n]['kind']=='MOS':s.mos(n,x,y)
        elif dev[n]['kind'] in ('C','R'):s.passive(n,x,y)
        else:s.cell(n,x,y)
    return finish(s)

def main():
    d=read_case(28);dev=d['subcircuits'][d['top']]['devices'];titles={};PLAN.clear()
    for group,label in [('OUTPUT','输出使能与浮动共源共栅支路'),('INPUT','交叉输入与复位'),('BIAS','原生偏置网络'),('RESERVOIR','浮动电荷库与栅偏置复位'),('C','耦合、储能和偏置电容'),('X','原厂HD时钟缓冲')]:
        names=[n for n,q in dev.items() if (q['kind']=='MOS' and '_'+group+'_' in n) or (group=='C' and q['kind']=='C') or (group=='X' and q['kind']=='HD')]
        for k in range(0,len(names),9):
            i=len(titles)+1;titles[i]=f'{label} {k//9+1}/{math.ceil(len(names)/9)}';PLAN[i]=names[k:k+9]
    return make_case(28,titles,layout)

if __name__=='__main__':main()
