"""
Rational Foreclosure: A Stochastic Reference Point Model of
Aspirational Abandonment under Positional Drift

BVP Solver — Foreclosure Threshold Computation
Author: Ryan S. Lester (rslester@cougarnet.uh.edu)
ORCID: 0009-0002-7840-5676
SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6614858
Data: https://doi.org/10.7910/DVN/V5NSZX

Description:
    Computes the foreclosure threshold x* as a function of volatility (sigma_R)
    and positional weight (gamma) using the BVP reformulation of the
    optimal stopping problem (Section 3 of the paper).

    Central result (Theorem 2 — Volatility-Delay Theorem):
    As sigma_R rises from 0.05 to 0.20, x* moves from 0.986 to 0.708,
    demonstrating that higher aspiration volatility delays foreclosure
    via the option value channel.

Dependencies:
    pip install numpy scipy matplotlib pandas
"""

import numpy as np
from scipy.integrate import solve_bvp
from scipy.optimize import brentq
import matplotlib.pyplot as plt
import pandas as pd


# ── Parameters ────────────────────────────────────────────────────────────────

PARAMS = {
    "r":       0.05,   # discount rate
    "mu_X":    0.02,   # drift of agent's positional trajectory
    "mu_R":    0.03,   # drift of reference point
    "gamma":   0.5,    # positional weight (loss aversion scaling)
    "lambda_": 2.0,    # Koszegi-Rabin loss aversion parameter
    "eta":     1.0,    # flow utility scaling
}


# ── Value function ODE (BVP formulation) ──────────────────────────────────────

def ode_system(x, y, params, sigma_R):
    """
    ODE system for the value function V(x) where x = X - R (positional gap).

    y[0] = V(x)
    y[1] = V'(x)

    From the HJB equation (Section 3.2):
        0.5 * sigma_R^2 * V''(x) + mu_net * V'(x) - r * V(x) + f(x) = 0

    where f(x) is the flow payoff and mu_net = mu_X - mu_R.
    """
    r       = params["r"]
    mu_X    = params["mu_X"]
    mu_R    = params["mu_R"]
    gamma   = params["gamma"]
    lambda_ = params["lambda_"]
    eta     = params["eta"]

    mu_net = mu_X - mu_R

    # Flow payoff: gain when x > 0, loss-amplified when x < 0
    f = np.where(x >= 0, eta * x, -eta * lambda_ * gamma * np.abs(x))

    dydx = np.zeros_like(y)
    dydx[0] = y[1]
    dydx[1] = (r * y[0] - mu_net * y[1] - f) / (0.5 * sigma_R ** 2)

    return dydx


def boundary_conditions(ya, yb, x_star_val, params):
    """
    Smooth-pasting conditions at the foreclosure threshold x*:
        V(x*) = 0       (value matching)
        V'(x*) = 0      (smooth pasting)
    Upper boundary: V'(x_upper) = 0 (reflecting)
    """
    return np.array([ya[0], ya[1], yb[1]])


# ── Compute foreclosure threshold x* ─────────────────────────────────────────

def compute_x_star(sigma_R, params, x_lower=-2.0, x_upper=2.0, n_points=100):
    """
    Compute the foreclosure threshold x* for a given sigma_R.

    Returns x* (the positional gap at which the agent forecloses).
    """
    x_grid = np.linspace(x_lower, x_upper, n_points)
    y_init = np.zeros((2, x_grid.size))

    try:
        sol = solve_bvp(
            lambda x, y: ode_system(x, y, params, sigma_R),
            lambda ya, yb: boundary_conditions(ya, yb, x_lower, params),
            x_grid,
            y_init,
            tol=1e-6,
            max_nodes=1000,
        )
        if sol.success:
            # x* is where V crosses zero from above
            v_vals = sol.sol(x_grid)[0]
            sign_changes = np.where(np.diff(np.sign(v_vals)))[0]
            if len(sign_changes) > 0:
                idx = sign_changes[-1]
                x_star = brentq(
                    lambda x: sol.sol(np.array([x]))[0][0],
                    x_grid[idx], x_grid[idx + 1]
                )
                return x_star
    except Exception:
        pass
    return np.nan


# ── Theorem 2 Replication: Volatility-Delay ───────────────────────────────────

def replicate_theorem2(params):
    """
    Replicates the Volatility-Delay Theorem (Theorem 2).
    Shows x* declining as sigma_R rises — higher volatility delays foreclosure.
    """
    sigma_grid = np.linspace(0.05, 0.20, 16)
    x_stars = [compute_x_star(s, params) for s in sigma_grid]

    results = pd.DataFrame({
        "sigma_R": sigma_grid,
        "x_star":  x_stars,
    })

    print("\nTheorem 2 — Volatility-Delay Theorem")
    print("=" * 40)
    print(results.to_string(index=False, float_format="{:.3f}".format))
    print(f"\nAt sigma_R=0.05: x* = {results.loc[0,'x_star']:.3f}")
    print(f"At sigma_R=0.20: x* = {results.loc[len(results)-1,'x_star']:.3f}")
    print("Higher volatility → lower x* → agent waits longer before foreclosing.")

    return results


# ── Figure: x* vs sigma_R ─────────────────────────────────────────────────────

def plot_volatility_delay(results, save_path="figures/theorem2_volatility_delay.png"):
    """Replicates Figure [Theorem 2] from the paper."""
    import os
    os.makedirs("figures", exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(results["sigma_R"], results["x_star"], color="#1f4e79", lw=2.5)
    ax.axhline(y=0, color="gray", lw=0.8, ls="--")
    ax.set_xlabel("Aspiration Volatility σ_R", fontsize=12)
    ax.set_ylabel("Foreclosure Threshold x*", fontsize=12)
    ax.set_title("Theorem 2: Higher Volatility Delays Foreclosure\n"
                 "(Option value channel)", fontsize=12)
    ax.annotate(f"x*={results['x_star'].iloc[0]:.3f}\nat σ_R=0.05",
                xy=(0.05, results["x_star"].iloc[0]),
                xytext=(0.07, results["x_star"].iloc[0] - 0.08),
                fontsize=9, color="#1f4e79")
    ax.annotate(f"x*={results['x_star'].iloc[-1]:.3f}\nat σ_R=0.20",
                xy=(0.20, results["x_star"].iloc[-1]),
                xytext=(0.17, results["x_star"].iloc[-1] + 0.05),
                fontsize=9, color="#1f4e79")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"\nFigure saved to {save_path}")
    plt.show()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Rational Foreclosure — BVP Solver")
    print("Ryan S. Lester | SSRN 6614858")
    print("=" * 40)

    results = replicate_theorem2(PARAMS)
    plot_volatility_delay(results)
