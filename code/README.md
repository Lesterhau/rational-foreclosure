# Rational Foreclosure: replication code (October 2026 revision)

Every file in this folder is code or its output. Python 3.10+ with numpy, scipy and matplotlib. Run any script with `python3 <file>` from this folder. Numerics illustrate the theorems; they do not certify them.

| File | What it does | Paper result |
|---|---|---|
| `solver.py` | Core solver: the free-boundary problem by collocation (`sol`), the bound x-bar (`xbar`), the lower bound J_eps (`Jlb`). Imported by every other script. | everything |
| `appendixA_numerical_checks.py` | The 243-point scan checking Theorem 1 (x-bar <= x* < 1, sign conditions), plus the burst-bound test. About 10 to 20 minutes. | Theorem 1; Appendix C, "Checks of Theorem 1" and "The burst bound" |
| `sweeps.py` | Calibrations and comparative statics at the baseline. Writes `sweeps.json`. | Tables 2 and 3; the table in Result 1 |
| `robust.py` | Volatility comparisons with the drift gap fixed and with the median growth fixed (576 and 684 comparisons). Writes `robust.json`. | Result 1 |
| `robustD.py` | Volatility comparisons with the expected growth of W/R fixed (756 comparisons). Writes `robustD.json`. | Result 1 |
| `convex.py` | Checks convexity of the value in W/R on the 243 solutions. Writes `convex.json`. | Theorem 2(b); Appendix C, "Convexity" |
| `nonconvex_example.py` | One of the 19 nonconvex cases: the threshold falls with volatility, but the value of staying falls at par. About two minutes. | Section 4.1; Appendix C, "Convexity" |
| `extreme_search.py` | Searches for a reversal of the volatility comparison (D fixed) at strong loss aversion and positional weight, lambda up to 100 and alpha up to 20. | Appendix C, "Result 1" |
| `risky_wealth_reversal.py` | The risky-wealth case in which raising wealth volatility with the raw drift gap fixed raises the threshold. | Proposition 5; Appendix C, "Risky wealth and the raw drift gap" |
| `cohort.py` | The illustrative cohort: share out of the race and average grind under five scenarios. | Table 4, Section 5.3 |
| `welfare.py` | Welfare loss from an imposed exit threshold. | Proposition 4 magnitudes; Result 3; Figure 2 |
| `figs.py` | Produces Figures 1 and 2. | Figures 1 and 2 |
| `shoot.py` | Independent shooting solver (the method used in the interactive page), used to cross-check the collocation solver. | Appendix C, "The solver" |

In the code, `gap` is the drift gap delta = r_R - r_W of the paper.
