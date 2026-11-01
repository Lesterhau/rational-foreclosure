import numpy as np, json
from solver import sol, xbar
def X(rho,alpha,lam,gap,sig):
    b,s=sol(rho,alpha,lam,gap,sig); return float(np.exp(b)) if b is not None else float('nan')
out={}
base=dict(rho=.05,alpha=.5,lam=2,gap=.02)
sigs=[.02,.05,.10,.15,.20,.25]
# (a) hold mean growth of R fixed (r_R fixed): gap fixed
out['sig_meanR']=[(s,X(.05,.5,2,.02,s),xbar(.05,.02,s)) for s in sigs]
# (b) hold median growth of R fixed: mut = r_W - r_R + s^2/2 fixed at baseline value (s=.10): mut0 = .005-.02=-.015
mut0=.10**2/2-.02
out['sig_medianR']=[(s,X(.05,.5,2,s**2/2-mut0,s)) for s in sigs if .05> -(s**2/2-mut0)+s**2]
out['lam']=[(l,X(.05,.5,l,.02,.10)) for l in [1.0,1.05,2,3,4]]
out['alpha']={str(s):[(a,X(.05,a,2,.02,s)) for a in [.05,.5,1,2,3]] for s in [.05,.10,.20]}
out['gap']=[(g,X(.05,.5,2,g,.10)) for g in [.005,.01,.02,.03,.05]]
out['rho']=[(r,X(r,.5,2,.02,.10)) for r in [.04,.05,.07,.10]]
json.dump(out,open('sweeps.json','w'),indent=1)
for k,v in out.items(): print(k,v)
