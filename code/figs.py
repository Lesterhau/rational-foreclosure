import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from solver import sol, xbar
from welfare import run
plt.rcParams.update({'pdf.fonttype':42,'mathtext.fontset':'cm','font.family':'serif','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
# Figure 1: x* against sigma, two conventions, with the proven lower bound
S=np.linspace(.02,.25,24); mut0=.10**2/2-.02
xm=[np.exp(sol(.05,.5,2,.02,s)[0]) for s in S]
xd=[np.exp(sol(.05,.5,2,s*s/2-mut0,s)[0]) for s in S]
xb=[xbar(.05,.02,s) for s in S]
fig,ax=plt.subplots(figsize=(5.6,3.4))
ax.plot(S,xm,'k-',lw=1.6,label=r'$x^*$, mean growth of $R$ held fixed')
ax.plot(S,xd,'k--',lw=1.4,label=r'$x^*$, median growth of $R$ held fixed')
ax.plot(S,xb,color='0.55',lw=1.2,ls=':',label=r'proved lower bound $\bar x$ (mean fixed)')
ax.axhline(1,color='0.8',lw=.8)
ax.set_xlabel(r'reference volatility $\sigma$'); ax.set_ylabel(r'exit threshold $x^*=W/R$')
ax.set_ylim(0,1.05); ax.legend(frameon=False,fontsize=8.5,loc='lower left')
ax.text(.03,.62,'continue',fontsize=9,color='0.3'); ax.text(.205,.12,'exit',fontsize=9,color='0.3')
fig.tight_layout(); fig.savefig('fig1_volatility.pdf')
# Figure 2: welfare loss against displaced threshold, baseline
b,F0,out=run(.05,.5,2,.02,.10,list(np.linspace(.935,.80,10)),list(np.linspace(.946,.975,6)))
xs=np.exp(b)
pts=sorted([(o[1],o[3]) for o in out])
fig,ax=plt.subplots(figsize=(5.6,3.2))
X=[p[0] for p in pts]; L=[p[1] for p in pts]
ax.plot([xs]+X,[0]+L,'ko',ms=3.5)
xx=np.linspace(min(X),max(X),200); c=np.mean([l/(np.log(xs)-np.log(x))**2 for x,l in pts if abs(np.log(xs)-np.log(x))<.03])
ax.plot(xx,c*(np.log(xx)-np.log(xs))**2,color='0.5',lw=1,label=r'quadratic, $c\,(\log\tilde x-\log x^*)^2$')
ax.axvline(xs,color='0.7',lw=.8); ax.text(xs+.002,max(L)*.85,r'$x^*$',fontsize=9)
ax.text(.865,max(L)*.62,'forced to\ncontinue',fontsize=9,color='0.3'); ax.text(.952,max(L)*.55,'forced\nto exit',fontsize=9,color='0.3')
ax.set_xlabel(r'imposed exit threshold $\tilde x$'); ax.set_ylabel(r'welfare loss at $x=1$ (utils)')
ax.legend(frameon=False,fontsize=8.5,loc='upper center'); fig.tight_layout(); fig.savefig('fig2_welfare.pdf')
print("c=",c,"F0=",F0)
