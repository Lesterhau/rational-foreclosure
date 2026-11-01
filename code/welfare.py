import numpy as np, sys
from scipy.integrate import solve_bvp
from solver import sol
def run(rho,alpha,lam,gap,sig,xts_low,xts_high,y0=0.0,ymax=8.0):
    s2=sig**2;a=s2/2;mut=s2/2-gap;D=-gap+s2;A=alpha/(rho-D)
    v=lambda y: np.where(y>=0,np.exp(y)-1,lam*(np.exp(y)-1))
    b,sopt=sol(rho,alpha,lam,gap,sig)
    Fopt=lambda y: float(sopt.sol((y-b)/(ymax-b))[0]) if y>b else 0.0
    def Fthr(bt):
        L=ymax-bt
        def f(z,Y):
            y=bt+z*L;F,Fp=Y
            H=-np.log(np.maximum(1+rho*Fp,1e-12))   # unrestricted consumption: sup_q{-qp-H_rho(q)}=-log(1+rho p)
            return L*np.vstack([Fp,(rho*F-H-mut*Fp-alpha*v(y))/a])
        bc=lambda Ya,Yb: np.array([Ya[0],Yb[1]-(A*np.exp(ymax)-1/rho)])
        z=np.linspace(0,1,4000);y=bt+z*L
        g0=np.array([[Fopt(t) for t in y],[0*t for t in y]])
        g0[1]=np.gradient(g0[0],y)
        s=solve_bvp(f,bc,z,g0,tol=1e-6,max_nodes=3000000)
        if s.status!=0: return None
        return lambda yy: float(s.sol((yy-bt)/L)[0]) if yy>bt else 0.0
    print("params",(rho,alpha,lam,gap,sig),"x*=%.4f F(y0)=%.6f"%(np.exp(b),Fopt(y0)))
    out=[]
    for xt in xts_low:
        bt=np.log(xt);h=b-bt;g=Fthr(bt)
        if g is None: print("fail",xt); continue
        Lo=Fopt(y0)-g(y0); out.append(('late',xt,h,Lo)); print(" forced-late  x~=%.3f h=%.4f loss=%.3e loss/h^2=%.4f share=%.2f%%"%(xt,h,Lo,Lo/h**2,100*Lo/Fopt(y0)))
    for xt in xts_high:
        bt=np.log(xt);h=bt-b;g=Fthr(bt)
        if g is None: print("fail",xt); continue
        Lo=Fopt(y0)-g(y0); out.append(('early',xt,h,Lo)); print(" forced-early x~=%.3f h=%.4f loss=%.3e loss/h^2=%.4f share=%.2f%%"%(xt,h,Lo,Lo/h**2,100*Lo/Fopt(y0)))
    return b,Fopt(y0),out
if __name__=="__main__": run(.05,.5,2,.02,.10,[0.935,0.93,0.92,0.90,0.85,0.80],[0.95,0.96,0.97])
if __name__=="__main__": run(.05,1.5,2.5,.02,.20,[0.65,0.60,0.55,0.50],[0.70,0.75])
