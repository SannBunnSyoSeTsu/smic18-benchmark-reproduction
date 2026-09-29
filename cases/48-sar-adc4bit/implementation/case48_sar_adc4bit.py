from sar_final import *

def final_design():
    design(4,unit_fF=50,dummy_fF=10,sample_scale=1,cmp_scale=1,delay_fF=70,bootstrap=False)

if __name__=='__main__':
    final_design();run(4,step=50e-12,reltol=1e-5)
