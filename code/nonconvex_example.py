"""A nonconvex case (Section 4 and Appendix C): the threshold falls with volatility,
but the value of staying does not rise everywhere.

(rho, alpha, lambda, delta) = (.05, 5, 10, -.03); sigma rises from .10 to .15 with
D = sigma^2 - delta held fixed. Solved by collocation (solver.py) at two truncation
points. Expected: x* 0.5416 -> 0.5066; F(0) 308.3 -> 288.8; F(-0.5) 24.1 -> 31.2.
Run: python3 nonconvex_example.py   (about two minutes)
"""
import numpy as np
from solver import sol


def values(rho, alpha, lam, gap, sig, ys, ymax):
    b, s = sol(rho, alpha, lam, gap, sig, ymax=ymax)
    z = (ys - b) / (ymax - b)
    F = np.where(ys > b, s.sol(np.clip(z, 0, 1))[0], 0.0)
    return b, F


rho, alpha, lam, gap = .05, 5, 10, -.03
s1, s2 = .10, .15
D = s1**2 - gap
gap2 = s2**2 - D          # keeps D fixed
ys = np.array([-0.5, -0.3, 0.0, 0.5, 1.0])
for ymax in (8.0, 10.0):
    b1, F1 = values(rho, alpha, lam, gap, s1, ys, ymax)
    b2, F2 = values(rho, alpha, lam, gap2, s2, ys, ymax)
    print(f"ymax={ymax}: x* {np.exp(b1):.4f} -> {np.exp(b2):.4f}")
    for y, f1, f2 in zip(ys, F1, F2):
        print(f"   y={y:+.1f}  F={f1:9.2f}  F_hat={f2:9.2f}  change={100*(f2/f1-1):+.1f}%")
