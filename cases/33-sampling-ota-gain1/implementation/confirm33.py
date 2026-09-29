"""Range derivative resolution check; keep original81point sweep as scored data."""
from case33_sampling import *

def main():
    quota_guard();r=json.loads((CASE/'latest_results.json').read_text());assert r['status'].startswith('complete_')
    b=bench('ranges').replace('step=500n','step=250n');rd=run_spectre(33,'range_resolution',b,[CASE/'circuit.scs',CASE/'sizing.json',CASE/'contract.json'])
    d=data(rd,'swing.dc');x=d['vin_diff'];y=d['voutp']-d['voutn'];assert len(x)==161
    g=np.gradient(y,x);db=20*np.log10(g);limit=max(db)-3;cross=[]
    for i in range(len(x)-1):
        if (db[i]-limit)*(db[i+1]-limit)<0:cross.append(float(y[i]+(limit-db[i])/(db[i+1]-db[i])*(y[i+1]-y[i])))
    assert len(cross)==2;value=cross[1]-cross[0];base=r['values']['output_range_v'];tol=.05;stable={k:value>=lim for k,lim in r['gates']['output_range_v']['limits'].items()}==r['gates']['output_range_v']['passes']
    q=dict(generated_at=now(),circuit_sha256=r['circuit_sha256'],reason='Derivative-based3dB output range depends on input sweep resolution; compare0.5uV original with0.25uV diagnostic',original_group=r['groups']['ranges'],diagnostic_run=str(rd.relative_to(ROOT)),baseline_points=81,diagnostic_points=161,baseline_range_V=base,diagnostic_range_V=value,absolute_difference_V=abs(value-base),maximum_difference_V=tol,same_acceptance_tiers=stable,passed=abs(value-base)<=tol and stable,scored_data='Original81point sweep retained without substitution')
    write_json(CASE/'numerical_confirmation.json',q);print(json.dumps(q,indent=2));assert q['passed']

if __name__=='__main__':main()
