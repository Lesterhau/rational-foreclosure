"""Numerical checks for Appendix A (Rational Foreclosure).
Scans rho in {.05,.1,.2}, alpha in {.2,1,5}, lambda in {1,2,10}, r_R-r_W in {-.03,0,.03,.1},
sigma in {.1,.25,.4}; 324 grid points, 243 with rho > D = r_W - r_R + sigma^2.
For each eligible point: solves the free-boundary ODE in y = log x by collocation (scipy solve_bvp),
then checks xbar <= x* < 1, J_eps > 0 at its maximizing eps, F(0) >= J_eps,
and the candidate sign conditions F >= 0, F' >= 0 on the computed solution.
The Hamiltonian uses log(1 + rho*max(F',0)), the p+ form used in the appendix.
Numerics illustrate the theorems; they do not certify them.
Hard cases are retried with a tighter mesh and more starting values.
Expected final line: eligible 243 solved 243 violations 0 min(x*-xbar)=0.0163
Run: python3 appendixA_numerical_checks.py   (needs numpy, scipy; about 10-20 minutes)
"""
import numpy as np, itertools
from scipy.integrate import solve_bvp
from scipy.optimize import minimize_scalar
def sol(rho,alpha,lam,gap,sig,ymax=8.0,guess=0.7):
    # notation: gap = r_R - r_W ; mut = r_W - r_R + sig^2/2 (drift of Y) ; D = r_W - r_R + sig^2 = mut + sig^2/2
    s2=sig**2;a=s2/2;mut=s2/2-gap;D=-gap+s2;A=alpha/(rho-D)
    # far field: F ~ A e^y - y/rho + C (the e^y terms give A=alpha/(rho-D); the y terms give slope -1/rho)
    v=lambda y: np.where(y>=0,np.exp(y)-1,lam*(np.exp(y)-1))
    def f(z,Y,p):
        b=p[0];L=ymax-b;y=b+z*L;F,Fp=Y
        return L*np.vstack([Fp,(rho*F+np.log1p(rho*np.maximum(Fp,0.0))-mut*Fp-alpha*v(y))/a])
    def bc(Ya,Yb,p): return np.array([Ya[0],Ya[1],Yb[1]-(A*np.exp(ymax)-1/rho)])
    for tol,nodes,n0,gs in ((1e-7,500000,1500,(guess,.9,.5,.3,.15,.05)),
                            (1e-6,3000000,4000,tuple(np.linspace(.99,.05,20)))):
        for g in gs:
            z=np.linspace(0,1,n0);b0=np.log(g);y=b0+z*(ymax-b0)
            s=solve_bvp(f,bc,z,np.vstack([A*np.exp(y)*.5,A*np.exp(y)*.5]),p=[b0],tol=tol,max_nodes=nodes)
            if s.status==0: return s.p[0],s
    return None,None
def xbar(rho,gap,sig):
    D=-gap+sig**2; a=sig**2/2
    # a*b^2+(D-a)*b-rho=0, negative root
    beta=(-(D-a)-np.sqrt((D-a)**2+4*a*rho))/(2*a)
    return (rho-D)/rho*beta/(beta-1)
def Jlb(eps,rho,alpha,lam,gap,sig):
    mut=sig**2/2-gap; m=mut-rho; D=mut+sig**2/2
    # theta: positive root of (sig^2/2) th^2 - m th - rho = 0, so exp(-th*Y - rho*t) is a martingale for Y = m t - sig Z
    # (Lemma 'Two Brownian facts' (a): hitting a LOWER level). E[exp(-rho T_eps)] = exp(-th*eps).
    th=(m+np.sqrt(m*m+2*rho*sig**2))/sig**2; L=np.exp(-th*eps); kap=2*rho-D
    return alpha*((1-np.exp(-eps)*L)/kap-(1-L)/rho-(lam-1)*(1-np.exp(-eps))*(1-L)/rho)
viol=0;n=0;worst=1e9;n_elig=0
rows=[]
for rho,alpha,lam,gap,sig in itertools.product([.05,.1,.2],[.2,1,5],[1,2,10],[-.03,0,.03,.1],[.1,.25,.4]):
    D=-gap+sig**2
    if rho<=D: continue
    n_elig+=1
    b,s=sol(rho,alpha,lam,gap,sig)
    if b is None: print("UNSOLVED",(rho,alpha,lam,gap,sig)); continue
    n+=1
    xs=np.exp(b); xb=xbar(rho,gap,sig)
    r=minimize_scalar(lambda e:-Jlb(e,rho,alpha,lam,gap,sig),bounds=(1e-6,2),method='bounded')
    jl=-r.fun
    F0=s.sol((0-b)/(8.0-b))[0] if b<0 else 0.0
    Yb=s.sol(np.linspace(0,1,4001))
    signs_ok = (Yb[0].min()>=-1e-6) and (Yb[1].min()>=-1e-6)   # candidate sign conditions: F>=0, F'>=0
    ok = (xb<=xs+1e-6) and (xs<1) and (jl>0) and (F0>=jl-1e-6) and signs_ok
    if not ok: viol+=1; rows.append((rho,alpha,lam,gap,sig,xb,xs,jl,F0))
    worst=min(worst, xs-xb)
print("eligible",n_elig,"solved",n,"violations",viol,"min(x*-xbar)=%.4f"%worst)
for r in rows[:10]: print(r)
print("example baseline rho=.1 a=1 lam=2 gap=0 sig=.25: xbar=%.4f"%xbar(.1,0,.25))

# --- Burst bound of Lemma (Late consumption bursts have no value) ---
def burst_check(rho=.1,rW=.03):
    from scipy.integrate import quad
    H=lambda q: q/rho-1-np.log(q/rho)
    K0=np.log(rho)/rho+(rW-rho)/rho**2
    g=lambda u: quad(lambda r: -np.exp(-rho*r)*np.log1p(-np.exp(-rho*(u-r))),0,u,points=[u-1e-9],limit=200)[0]
    rng=np.random.default_rng(0);worst=-1e9
    for _ in range(200000):
        T=rng.uniform(.01,80);s=rng.uniform(0,T*.9999);q=np.exp(rng.uniform(-12,12))
        worst=max(worst,np.exp(-rho*T)/rho*q-np.exp(-rho*s)*H(q)+np.exp(-rho*s)*np.log1p(-np.exp(-rho*(T-s))))
    print("legendre max violation:",worst)
    for (T,Dl,M,q0) in ((10,.01,1e4,rho),(30,1e-4,1e8,rho),(60,.5,1e4,.2)):
        t=np.linspace(0,T,2000000);dt=t[1]-t[0];q=np.where(t>=T-Dl,M,q0)
        Q=np.cumsum(q)*dt
        br=np.exp(-rho*T)*Q[-1]/rho-np.sum(np.exp(-rho*t)*H(q))*dt
        print(f"T={T} Delta={Dl} M={M:.0e}: gain-cost={br:.4f} g(T)={g(T):.4f} ok={br<=g(T)+1e-6}")
# burst_check()  # uncomment to run (about a minute)
