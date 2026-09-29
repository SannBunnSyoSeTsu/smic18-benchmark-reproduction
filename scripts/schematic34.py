"""Full transistor sheets for the sampling-feedback OTA; no ideal feedback inside DUT."""
from schematic_common import make_case
from schematics_analog import layout35

if __name__=='__main__':
    make_case(34,{1:'单参考与级联偏置',2:'全差分折叠输入级',3:'双输出级及Miller补偿',4:'连续共模反馈与输出检测'},layout35)
