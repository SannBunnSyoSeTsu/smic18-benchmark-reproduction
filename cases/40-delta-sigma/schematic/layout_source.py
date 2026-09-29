from schematic_common import *
from schematics_analog import mos,link,bus,finish
PLAN={}

def layout(ax,i,dev):
    s=Sheet(ax,i,dev);kind,names=PLAN[i]
    if kind=='top':
        s.cell('XADC',12,13);s.cell('XOTA',33,19);s.cell('XSA',33,7)
    elif kind=='ota':
        mos(s,[('MREF',4,5),('MTAIL',24,5),('MINP',16,12),('MINN',32,12),('MLN',16,21),('MLP',32,21)])
        link(s,'MLN','D','MINP','D');link(s,'MLP','D','MINN','D');bus(s,'tail',[('MINP','S'),('MINN','S'),('MTAIL','D')],8)
        bus(s,'vdd',[('MLN','S'),('MLP','S')],24)
    elif kind=='cm':
        mos(s,[('MCLE',11,21),('MCLR',30,21),('MCSENSE',11,14),('MCREF',30,14),('MCTAIL',21,7)])
        link(s,'MCLE','D','MCSENSE','D');link(s,'MCLR','D','MCREF','D');bus(s,'ctail',[('MCSENSE','S'),('MCREF','S'),('MCTAIL','D')],10)
        for n,x,y in [('RAVP',9,4),('RAVN',32,4),('CAVP',9,1),('CAVN',32,1)]:s.passive(n,x,y,vertical=False)
    else:
        for k,n in enumerate(names):
            x=6+15*(k%3);y=21-9*(k//3)
            if dev[n]['kind']=='MOS':s.mos(n,x,y)
            elif dev[n]['kind'] in ('R','C'):s.passive(n,x,y)
            else:s.cell(n,x,y)
    return finish(s)

def main():
    d=read_case(40);titles={};blocks={};PLAN.clear()
    def page(b,title,kind,names=None):
        i=len(titles)+1;titles[i]=title;blocks[i]=b;PLAN[i]=(kind,names)
    page('sigma_system','完整环路与外部原生OTA/比较器接口','top')
    page('ds_ota','固定原生OTA夹具：差分主放大支路','ota')
    page('ds_ota','固定原生OTA夹具：共模反馈与取样','cm')
    names=list(d['subcircuits']['ds_comparator']['devices'])
    for k in range(0,len(names),8):page('ds_comparator',f'固定原生动态比较器 {k//8+1}/2','grid',names[k:k+8])
    groups=[('采样和积分电容',['CSP','CSN','CIP','CIN']),('反馈判决保持',['MHNa','MHPa','CHa','RHa','MHNb','MHPb','CHb','RHb']),('一位参考DAC',['MDPH','MDPHP','MDPL','MDPLP','MDNH','MDNHP','MDNL','MDNLP']),('输入采样互补开关',[f'MS{k}{p}' for k in range(1,5) for p in ('','P')]),('积分转移互补开关',[f'MI{k}{p}' for k in range(1,5) for p in ('','P')]),('直流泄放支路',[n for n in d['subcircuits']['sigma_adc']['devices'] if n.startswith('R_')])]
    for name,items in groups:page('sigma_adc',name,'grid',items)
    return make_case(40,titles,layout,blocks)

if __name__=='__main__':main()
