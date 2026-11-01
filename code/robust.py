import numpy as np, itertools, json
from solver import sol
def X(*p):
    b,s=sol(*p); return float(np.exp(b)) if b is not None else float('nan')
sg=[.05,.1,.15,.2,.25,.3,.35,.4]
res={'meanR':[0,0,0,[]],'medianR':[0,0,0,[]]}   # pairs checked, decreasing, unsolved, counterexamples
for rho,alpha,lam,gap in itertools.product([.05,.1,.2],[.2,1,5],[1,2,10],[-.03,0,.03,.1]):
    xs=[(s,X(rho,alpha,lam,gap,s)) for s in sg if rho-(-gap+s*s)>0.005]
    for (s1,x1),(s2,x2) in zip(xs,xs[1:]):
        r=res['meanR']
        if np.isnan(x1) or np.isnan(x2): r[2]+=1; continue
        r[0]+=1; r[1]+= x2<x1
        if not x2<x1: r[3].append((rho,alpha,lam,gap,s1,s2,x1,x2))
for rho,alpha,lam,mut in itertools.product([.05,.1,.2],[.2,1,5],[1,2,10],[-.05,-.02,0,.02]):
    xs=[(s,X(rho,alpha,lam,s*s/2-mut,s)) for s in sg if rho-(mut+s*s/2)>0.005]
    for (s1,x1),(s2,x2) in zip(xs,xs[1:]):
        r=res['medianR']
        if np.isnan(x1) or np.isnan(x2): r[2]+=1; continue
        r[0]+=1; r[1]+= x2<x1
        if not x2<x1: r[3].append((rho,alpha,lam,mut,s1,s2,x1,x2))
json.dump(res,open('robust.json','w'),indent=1)
for k,v in res.items(): print(k,"pairs",v[0],"decreasing",v[1],"unsolved",v[2],"counterexamples",v[3][:8])
