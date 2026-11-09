"""A race with a deadline (Proposition 'A deadline', Section 4.3).

Solves the finite-horizon problem F_s(y) = sup over consumption and exit times tau <= s, where s is the time left
before the race ends, by backward induction on the variational inequality
    max( -dF/ds + a F'' + mut F' - rho F - log(1 + rho max(F',0)) + f(y),  -F ) = 0,   F_0 = 0,
with a = sigma^2/2, mut = sigma^2/2 - gap, f(y) = alpha v(e^y - 1). Implicit Euler in s for the linear part,
the consumption term and the flow explicit; each step's complementarity problem (F >= 0) is solved exactly by
the Brennan-Schwartz sweep, the standard method for American-style stopping problems with one boundary. Boundary: F = 0 at the bottom of the grid;
at the top, F'' - F' = (1 - e^{-rho s})/rho, the far-field condition. For large y the solution behaves like
A(s) e^y + B(s) y + C(s) with B(s) = -(1 - e^{-rho s})/rho (the y-terms of the equation give B' = -rho B - 1, B(0) = 0),
and the discrete top condition below is exact for that shape. In the stationary limit this is the far field
A e^y - y/rho + C used by solver.py. The grid runs from y = -6 to y = 6.
(Before November 9, 2026 the code imposed F'' = F', exact only for A e^y + C, with the grid's top at y = 2.5. The
first two calibrations are unchanged to four digits; the third, where rho < D and the value grows fastest, came out
too high at long horizons: 0.5027 instead of 0.5016 at s = 40, and 0.3296 instead of 0.3104 at s = 100. Raising the
top to y = 8, under either top condition, reproduces the current values.)

Reports the quitting point x*_s = exp(b(s)) for several s, checks that it falls as s grows, and checks that
it approaches the stationary threshold of solver.py when rho > D. In the second calibration rho <= D, so the
stationary problem has no threshold; x*_s still exists for every finite s and falls toward zero.
Run: python3 deadline.py   (needs numpy, scipy; a few minutes)
"""
import numpy as np
from scipy.linalg import solve_banded


def deadline(rho, alpha, lam, gap, sig, S, yL=-6.0, yU=6.0, dy=0.005, ds=1 / 100, report=None, far_y=True):
    a = sig ** 2 / 2
    mut = sig ** 2 / 2 - gap
    y = np.arange(yL, yU + dy / 2, dy)
    n = len(y)
    f = alpha * np.where(y >= 0, np.exp(y) - 1, lam * (np.exp(y) - 1))
    # implicit operator (I - ds L) on interior points 1..n-2; L F = a F'' + mut F' - rho F
    lo = -ds * (a / dy ** 2 - mut / (2 * dy))
    di = 1 + ds * (2 * a / dy ** 2 + rho)
    up = -ds * (a / dy ** 2 + mut / (2 * dy))
    m = n - 2
    ab = np.zeros((3, m))
    ab[0, 1:] = up
    ab[1, :] = di
    ab[2, :-1] = lo
    # top boundary: F_{n-1} = F_{n-2} + e^dy (F_{n-2} - F_{n-3}) + kap(s), folded into the last interior row.
    # This is exact for A e^y + B y + C with kap = B dy (1 - e^dy); with B(s) = -(1 - e^{-rho s})/rho it is the
    # discrete form of F'' - F' = (1 - e^{-rho s})/rho. far_y=False drops the y-term (the pre-Nov-2026 condition F'' = F').
    ed = np.exp(dy)
    kap = (lambda s: (1 - np.exp(-rho * s)) / rho * dy * (ed - 1)) if far_y else (lambda s: 0.0)
    ab[1, -1] = di + up * (1 + ed)
    ab[2, -2] = lo - up * ed
    # Brennan-Schwartz: eliminate from the top of the grid down, then substitute from the bottom up, projecting onto
    # F >= 0 as we go. This solves each implicit step's complementarity problem exactly when, as here, the stopping
    # region lies below a single boundary.
    A = ab[2, :].copy(); A = np.concatenate([[0.0], A[:-1]])      # sub-diagonal aligned with rows
    B = ab[1, :].copy()
    C = np.concatenate([ab[0, 1:], [0.0]])                         # super-diagonal aligned with rows
    Bp = np.empty(m); Bp[-1] = B[-1]
    for i in range(m - 2, -1, -1):
        Bp[i] = B[i] - C[i] * A[i + 1] / Bp[i + 1]
    ratio = C[:-1] / Bp[1:]
    Al = A.tolist(); Bpl = Bp.tolist(); ratl = ratio.tolist()
    F = np.zeros(n)
    steps = int(round(S / ds))
    want = sorted(report or [S])
    out = {}
    k = 0
    for i in range(1, steps + 1):
        s = i * ds
        Fp = (F[2:] - F[:-2]) / (2 * dy)
        rhs = (F[1:-1] + ds * (f[1:-1] - np.log1p(rho * np.maximum(Fp, 0.0)))).tolist()
        rhs[-1] -= up * kap(s)
        rp = rhs[:]
        for j in range(m - 2, -1, -1):
            rp[j] = rhs[j] - ratl[j] * rp[j + 1]
        prev = 0.0
        col = [0.0] * m
        for j in range(m):
            v = (rp[j] - Al[j] * prev) / Bpl[j]
            prev = v if v > 0 else 0.0
            col[j] = prev
        F[1:-1] = col
        F[0] = 0.0
        F[-1] = F[-2] + ed * (F[-2] - F[-3]) + kap(s)
        while k < len(want) and s >= want[k] - 1e-9:
            out[want[k]] = boundary(y, F)
            k += 1
    return out


def boundary(y, F, tol=1e-9):
    """Free boundary from the computed value: near b, F ~ K (y - b)^2, so sqrt(F) is linear; extrapolate its root."""
    pos = np.where(F > tol)[0]
    if len(pos) == 0:
        return np.nan
    j = pos[0]
    if j == 0:
        return -np.inf
    j2 = min(j + 6, len(y) - 1)
    r1, r2 = np.sqrt(F[j]), np.sqrt(F[j2])
    if r2 <= r1:
        return y[j - 1]
    b = y[j] - r1 * (y[j2] - y[j]) / (r2 - r1)
    return float(min(max(b, y[j - 1]), y[j]))


if __name__ == "__main__":
    from solver import sol, xbar
    S_LIST = [1, 2, 5, 10, 20, 30, 40, 60, 100]
    cases = [("Baseline (rho > D)", dict(rho=0.05, alpha=0.5, lam=2.0, gap=0.02, sig=0.10)),
             ("Moderate volatility (rho > D)", dict(rho=0.05, alpha=1.0, lam=2.5, gap=0.03, sig=0.18)),
             ("Favorable trend (rho <= D)", dict(rho=0.05, alpha=0.5, lam=2.0, gap=0.01, sig=0.25))]
    rows = []
    for name, p in cases:
        D = p["sig"] ** 2 - p["gap"]
        res = deadline(S=max(S_LIST), report=S_LIST, **p)
        xs = [np.exp(res[s]) for s in S_LIST]
        if p["rho"] > D:
            b, _ = sol(p["rho"], p["alpha"], p["lam"], p["gap"], p["sig"])
            stat = np.exp(b)
        else:
            stat = 0.0
        mono = all(xs[i + 1] <= xs[i] + 1e-4 for i in range(len(xs) - 1))
        rows.append((name, D, xs, stat, mono))
        print(f"{name}: D={D:.4f}, rho={p['rho']}")
        print("   years left : " + "  ".join(f"{s:>6}" for s in S_LIST) + "   stationary")
        print("   x*_s       : " + "  ".join(f"{x:6.3f}" for x in xs) + f"   {stat:6.3f}")
        print("   falls as time left grows:", mono, (f"; gap to stationary at s=100: {xs[-1]-stat:+.4f}" if stat else ""))
    import json
    json.dump({n: {"D": D, "s": S_LIST, "x": [round(x, 4) for x in xs], "stationary": round(st, 4), "monotone": mono}
               for n, D, xs, st, mono in rows}, open("deadline.json", "w"), indent=1)
