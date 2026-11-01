"""Illustrative cohort aggregation (Section 5.3): a cohort shares one benchmark; log standing
y_i ~ N(m, s^2) across people. For each scenario: threshold x*, share at or below it (out of the
race), and the cohort's average grind (rho - q*)/rho, counting those out of the race as zero."""
import numpy as np
from scipy.stats import norm
from solver import sol
rho,alpha,lam=.05,.5,2
def scen(gap,sig,shift=0.0,m=0.0,s=.25):
    b,S=sol(rho,alpha,lam,gap,sig)
    ys=np.linspace(m-5*s,m+5*s,4001)+shift; w=norm.pdf(ys-shift,m,s); w/=w.sum()
    z=np.clip((ys-b)/(8-b),0,1); Fp=np.where(ys>b,S.sol(z)[1],0.0)
    grind=np.where(ys>b,rho*Fp/(1+rho*Fp),0.0)
    out=float(w[ys<=b].sum()); g=float((w*grind).sum())
    return np.exp(b),out,g
rows=[("Baseline (drift gap 2 pts, volatility 10%)",.02,.10,0),
      ("Benchmark runs 2 pts faster (drift gap 4 pts)",.04,.10,0),
      ("Benchmark jumps 10% once",.02,.10,-np.log(1.1)),
      ("Benchmark twice as volatile (20%)",.02,.20,0),
      ("Policy narrows drift gap to 1 pt",.01,.10,0)]
for name,gap,sig,sh in rows:
    xs,out,g=scen(gap,sig,sh)
    print(f"{name:50s} x*={xs:.3f} out={100*out:5.1f}%  avg grind={100*g:5.2f}%")
