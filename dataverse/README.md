# Replication Data for: Rational Foreclosure (version 2, November 2026)

Ryan Lester, University of Houston (rslester@cougarnet.uh.edu)

Replication files for Lester, R. (2026), "Rational Foreclosure: Hope as an Economic Variable," working paper, SSRN 6614858, November 2026 revision. Version 2 replaces the code in version 1, which accompanied an earlier draft with different results and numbering.

## What is here

The dataset has three files: this README, the paper (`Lester_2026_Rational_Foreclosure.pdf`), and `rational_foreclosure_replication_v2.zip`, which unpacks to a folder `rational_foreclosure_replication/` holding a copy of this README, `LICENSE`, `CITATION.cff`, `requirements.txt` and the folders below.

| Folder | Contents |
|---|---|
| `code/` | Python code that produces every number, table and figure in the paper. |
| `tool/` | The Hope Gap, the paper's interactive planning tool, as a single HTML file with a data snapshot built in, plus that snapshot as JSON. |
| `pipeline/` | The script and the GitHub Actions workflow that build the tool's data from public sources twice a week. |

## Code (`code/`)

Python 3.10 or later with numpy, scipy and matplotlib (`pip install -r requirements.txt`). Run any script with `python3 <file>` from inside `code/`. The numerics illustrate the theorems; they do not certify them.

| File | What it does | Paper result |
|---|---|---|
| `solver.py` | Core solver: the free-boundary problem by collocation (`sol`), the bound x-bar (`xbar`), the lower bound J_eps (`Jlb`). Imported by every other script. | everything |
| `appendixA_numerical_checks.py` | The 243-point scan checking Theorem 1 (x-bar <= x* < 1, sign conditions), plus a numerical test of the burst bound of Lemma A.4 (no longer reported in the paper, which proves it). About 10 to 20 minutes. | Theorem 1; Appendix C, "Checks of Theorem 1" |
| `sweeps.py` | Calibrations and comparative statics at the baseline. Writes `sweeps.json`. | Tables 2 and 3; the table in Result 1 |
| `robust.py` | Volatility comparisons with the drift gap fixed and with the median growth fixed (576 and 684 comparisons). Writes `robust.json`. | Result 1 |
| `robustD.py` | Volatility comparisons with the expected growth of W/R fixed (756 comparisons). Writes `robustD.json`. | Result 1 |
| `convex.py` | Checks convexity of the value in W/R on the 243 solutions. Writes `convex.json`. | Theorem 2(b); Appendix C, "Convexity" |
| `nonconvex_example.py` | One of the 19 nonconvex cases: the threshold falls with volatility, but the value of staying falls at par. About two minutes. | Section 4.1; Appendix C, "Convexity" |
| `extreme_search.py` | Searches for a reversal of the volatility comparison (D fixed) at strong loss aversion and positional weight, lambda up to 100 and alpha up to 20. | Appendix C, "Result 1" |
| `risky_wealth_reversal.py` | The risky-wealth case in which raising wealth volatility with the raw drift gap fixed raises the threshold. | Proposition 6; Appendix C, "Risky wealth and the raw drift gap" |
| `cohort.py` | The illustrative cohort: share out of the race and average grind under five scenarios. | Table 5, Section 5.3 |
| `deadline.py` | The race with a deadline: the quitting point by years left, by backward induction with the Brennan-Schwartz sweep; checks that it falls as time left grows and approaches the stationary threshold. Writes `deadline.json`. A few minutes. | Proposition 4; Table 4; Appendix C, "The deadline" |
| `welfare.py` | Welfare loss from an imposed exit threshold. | Proposition 5 magnitudes; Result 3; Figure 2 |
| `figs.py` | Produces Figures 1 and 2. | Figures 1 and 2 |
| `shoot.py` | Independent shooting solver (the method used in the interactive page), used to cross-check the collocation solver. | Appendix C, "The solver" |

In the code, `gap` is the drift gap delta = r_R - r_W of the paper.

## The planning tool (`tool/`)

`the_hope_gap.html` opens in any modern browser and needs no internet connection. It solves the model in the browser: without a deadline, by shooting on the free boundary (fourth-order Runge-Kutta with bisection on the quitting point), which matches `code/solver.py` to four digits; with the default working-life deadline (Proposition 4), by the backward induction of `code/deadline.py` on a coarser grid, which matches it to within 0.006 in the quitting point across the settings the page offers. Each group's pay trend is the area's adjusted by that group's earnings growth relative to all workers (`groups.json`), and the lowest income group is measured against starter homes. The data built into this copy are those in `tool/data_2026-11-12/`. The public copy at https://lesterhau.github.io/rational-foreclosure/ is the same page and refreshes its data twice a week.

## Data pipeline (`pipeline/`)

`build_data.py OUT_DIR [PREVIOUS_DIR]` downloads and assembles the tool's data (needs pandas, numpy, requests and openpyxl; no API keys). `build_groups.py OUT_DIR` builds `groups.json`, the group pay trends, from the Census Bureau's bulk files (large; run about monthly). `update_data_workflow.yml` is the GitHub Actions workflow that runs the first on Mondays and Thursdays, the second when its output is more than 28 days old, and publishes the results. Sources:

- FRED, Federal Reserve Bank of St. Louis: consumer and producer prices, PCE prices, GDP, unemployment, earnings, the FHFA U.S. house price index, mortgage rates.
- Federal Housing Finance Agency: state (quarterly) and county (annual) all-transactions house price indexes.
- Bureau of Labor Statistics, Quarterly Census of Employment and Wages: average weekly wages for the nation, states and counties.
- Zillow Research: Zillow Home Value Index for the nation, states, counties and cities, for typical homes and for the bottom tier (starter homes). Zillow data are used with attribution to Zillow.
- U.S. Census Bureau, Quarterly Workforce Indicators (LEHD program): average monthly earnings of workers who held the same job all quarter, by age, sex, education and race and ethnicity, for every county and state.
- U.S. Census Bureau, American Community Survey summary files (2025 1-year; 2020-2024 5-year for smaller counties): population, age, race and ethnicity, education, income, housing tenure, housing units.

## Citation

Lester, R. (2026). Replication data for: Rational Foreclosure. Harvard Dataverse, https://doi.org/10.7910/DVN/V5NSZX

## License

Code, documentation and the planning tool: CC BY 4.0 (see `LICENSE`). Data in `tool/data_2026-11-12/` are derived from the public sources above and remain subject to their terms.
