import numpy as np, itertools, json
from solver import sol
def conv(rho,alpha,lam,gap,sig,ymax=8.0):
    b,s=sol(rho,alpha,lam,gap,sig)
    if b is None: return None
    s2=sig**2;a=s2/2;mut=s2/2-gap
    y=np.linspace(b,ymax,20001)[1:]; z=(y-b)/(ymax-b)
    F,Fp=s.sol(z)
    v=np.where(y>=0,np.exp(y)-1,lam*(np.exp(y)-1))
    Fpp=(rho*F+np.log1p(rho*np.maximum(Fp,0))-mut*Fp-alpha*v)/a
    w=Fpp-Fp   # G''(x) x^2 = F'' - F'
    return float(b), float(w.min()), float(y[np.argmin(w)]), float(Fp.min())
rows=[];bad=[]
for rho,alpha,lam,gap,sig in itertools.product([.05,.1,.2],[.2,1,5],[1,2,10],[-.03,0,.03,.1],[.1,.25,.4]):
    if rho<=-gap+sig**2: continue
    r=conv(rho,alpha,lam,gap,sig)
    if r is None: bad.append((rho,alpha,lam,gap,sig,'unsolved')); continue
    rows.append(((rho,alpha,lam,gap,sig),)+r)
    if r[1]< -1e-6: bad.append((rho,alpha,lam,gap,sig,r))
print("checked",len(rows),"violations",len(bad)); print(bad[:10])
mins=sorted(rows,key=lambda r:r[2])[:5]; print("smallest min(F''-F'):",mins)
json.dump({'rows':rows,'bad':bad},open('convex.json','w'))
