import numpy as np, math
def rhs(y,F,Fp,P,unres=False):
    rho,alpha,lam,mut,a=P
    v=(math.exp(y)-1)*(1 if y>=0 else lam)
    H=math.log(max(1+rho*Fp,1e-12)) if unres else math.log1p(rho*max(Fp,0.0))
    return (rho*F+H-mut*Fp-alpha*v)/a
def shoot_b(rho,alpha,lam,gap,sig,Y=2.0,h=1e-3):
    a=sig*sig/2; mut=a-gap; D=sig*sig-gap; A=alpha/(rho-D); P=(rho,alpha,lam,mut,a)
    def g(b):
        y=b;F=0.0;Fp=0.0
        while y<Y:
            # RK4
            def f(y,F,Fp): return Fp, rhs(y,F,Fp,P)
            k1=f(y,F,Fp);k2=f(y+h/2,F+h/2*k1[0],Fp+h/2*k1[1]);k3=f(y+h/2,F+h/2*k2[0],Fp+h/2*k2[1]);k4=f(y+h,F+h*k3[0],Fp+h*k3[1])
            F+=h/6*(k1[0]+2*k2[0]+2*k3[0]+k4[0]);Fp+=h/6*(k1[1]+2*k2[1]+2*k3[1]+k4[1]);y+=h
            if Fp<-1e-9: return +1        # b too high
            if Fp>3*A*math.exp(y)+50: return -1   # b too low (explosive branch)
        return 1 if Fp<A*math.exp(Y)-1/rho else -1
    lo,hi=math.log(1e-4),-1e-9
    for _ in range(60):
        m=(lo+hi)/2
        if g(m)>0: hi=m
        else: lo=m
    return math.exp((lo+hi)/2)
from solver import sol
for p in [(.05,.5,2,.02,.10),(.05,1,2.5,.03,.18),(.05,1.5,2.5,.02,.20),(.1,1,2,0,.25),(.05,.5,2,.02,.25),(.05,.5,1,.02,.10)]:
    b,_=sol(*p); print(p,'collocation %.4f'%math.exp(b),'shooting %.4f'%shoot_b(*p))

def integrate(b,F0,Fp0,P,Y,h=1e-3,unres=False,record=None):
    y=b;F=F0;Fp=Fp0
    rho=P[0]
    while y<Y-1e-12:
        hh=min(h,Y-y)
        def f(y,F,Fp): return Fp, rhs(y,F,Fp,P,unres)
        k1=f(y,F,Fp);k2=f(y+hh/2,F+hh/2*k1[0],Fp+hh/2*k1[1]);k3=f(y+hh/2,F+hh/2*k2[0],Fp+hh/2*k2[1]);k4=f(y+hh,F+hh*k3[0],Fp+hh*k3[1])
        F+=hh/6*(k1[0]+2*k2[0]+2*k3[0]+k4[0]);Fp+=hh/6*(k1[1]+2*k2[1]+2*k3[1]+k4[1]);y+=hh
        if unres and Fp<=-1/rho+1e-9: return y,F,Fp,'low'
        if abs(Fp)>1e6: return y,F,Fp,'high'
    return y,F,Fp,'ok'
def value_at(rho,alpha,lam,gap,sig,bt,y0=0.0,Y=2.0):
    a=sig*sig/2; mut=a-gap; D=sig*sig-gap; A=alpha/(rho-D); P=(rho,alpha,lam,mut,a)
    target=A*math.exp(Y)-1/rho
    lo,hi=-1/rho+1e-6, 50.0
    for _ in range(80):
        m=(lo+hi)/2
        y,F,Fp,st=integrate(bt,0.0,m,P,Y,unres=True)
        if st=='low' or (st=='ok' and Fp<target): lo=m
        else: hi=m
    m=(lo+hi)/2
    y,F,Fp,st=integrate(bt,0.0,m,P,y0,unres=True)
    return F
p=(.05,.5,2,.02,.10); xs=shoot_b(*p)
F0=value_at(*p,math.log(xs))
for xt in [0.90,0.85,0.80,0.95,0.97]:
    print(xt,'loss %.4e'%(F0-value_at(*p,math.log(xt))))
print('F0',F0)
