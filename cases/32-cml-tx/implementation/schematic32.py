"""Exact transistor pair, neutralization and all four series inductors."""
from schematic_common import Sheet,make_case
from schematics_analog import mos,passive,link,bus,finish

def layout(ax,i,d):
    s=Sheet(ax,i,d)
    mos(s,[('MREF',4,5),('MTAIL',21,5),('MPAIRP',13,13),('MPAIRN',29,13)])
    passive(s,[('LN',13,20,True,True),('LP',29,20,True,True),('LIP',5,13,False),('LIN',21,13,False),('CNEUTP',6,20),('CNEUTN',39,20)])
    # Clear the horizontal coil peaks without changing the shared renderer.
    for label in ax.texts:
        x,y=label.get_position()
        if x in [5,21] and abs(y-13.36)<1e-8:label.set_position((x,13.85))
        elif x in [5,21] and abs(y-13.82)<1e-8:label.set_position((x,14.35))
    link(s,'LN','1','MPAIRP','D');link(s,'LP','1','MPAIRN','D')
    link(s,'LIP','2','MPAIRP','G');link(s,'LIN','2','MPAIRN','G')
    bus(s,'tail',[('MPAIRP','S'),('MPAIRN','S'),('MTAIL','D')],9)
    bus(s,'vss',[('MREF','S'),('MTAIL','S')],1.5)
    s.text(1,24,'输出交叉保证正向极性；同名网络相连。外部每腿50Ω/100fF终端不在DUT内。',7.3)
    return finish(s)

if __name__=='__main__':make_case(32,{1:'CML输出对、输入/输出串联峰化与交叉中和'},layout)
