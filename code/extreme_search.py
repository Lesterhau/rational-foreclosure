"""Search for reversals of the volatility comparison at extreme preferences (Appendix C, Result 1).

With D = sigma^2 - delta held fixed, solve for x* at sigma = .05, .10, ..., .30 and report any
case in which x* rises with sigma. Grid: rho = .05, alpha in {1, 5, 20},
lambda in {10, 30, 100}, D in {-.05, 0, .02}: 27 combinations, 135 comparisons.
Add .10 to RHOS to extend it. Run: python3 extreme_search.py (about an hour).
"""
import itertools
import numpy as np
from solver import sol

reversals = 0
RHOS = [.05]
for rho, alpha, lam, D in itertools.product(RHOS, [1, 5, 20], [10, 30, 100], [-.05, 0, .02]):
    if rho <= D + 0.005:
        continue
    prev, row = None, []
    for sig in [.05, .10, .15, .20, .25, .30]:
        b, _ = sol(rho, alpha, lam, sig**2 - D, sig)
        xs = None if b is None else float(np.exp(b))
        row.append(xs)
        if prev is not None and xs is not None and xs > prev + 1e-6:
            reversals += 1
            print("REVERSAL", rho, alpha, lam, D, sig, prev, "->", xs, flush=True)
        if xs is not None:
            prev = xs
    print(rho, alpha, lam, D, [None if r is None else round(r, 4) for r in row], flush=True)
print("reversals:", reversals)
