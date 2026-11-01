import numpy as np
from solver import sol
# ChatGPT N5: rho=.3, alpha=1, lam=1, delta=0 (r_R=r_W), sigR=1, corr=1, sigW .8 -> 1.5
for sW in (.8,1.5):
    sR=1;c=1;S=sW**2+sR**2-2*c*sW*sR; muS=0-sW**2/2+sR**2/2; DS=muS+S/2
    sig=np.sqrt(S); gap=sig**2/2-muS   # solver: mut = sig^2/2 - gap
    b,s=sol(.3,1,1,gap,sig)
    print(f"sigW={sW} S={S:.3f} muS={muS:.3f} DS={DS:.3f} delta_eff={gap:.3f} x*={np.exp(b):.6f}")
