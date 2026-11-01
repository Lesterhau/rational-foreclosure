import numpy as np, itertools, json
from solver import sol
def X(*p):
    b,s=sol(*p); return float(np.exp(b)) if b is not None else float('nan')
sg=[.05,.1,.15,.2,.25,.3,.35,.4]
r=[0,0,0,[]]
for rho,alpha,lam,D in itertools.product([.05,.1,.2],[.2,1,5],[1,2,10],[-.05,-.02,0,.02]):
    if D>=rho-.005: continue
    xs=[(s,X(rho,alpha,lam,s*s-D,s)) for s in sg]   # gap = r_R - r_W chosen so that D = s^2 - gap is fixed
    for (s1,x1),(s2,x2) in zip(xs,xs[1:]):
        if np.isnan(x1) or np.isnan(x2): r[2]+=1; continue
        r[0]+=1; r[1]+= x2<x1
        if not x2<x1: r[3].append((rho,alpha,lam,D,s1,s2,x1,x2))
json.dump(r,open('robustD.json','w'),indent=1)
print("Dfixed pairs",r[0],"decreasing",r[1],"unsolved",r[2],"counterexamples",r[3][:8])
