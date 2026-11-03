# Rational Foreclosure

**Paper:** Lester, R. (2026). *Rational Foreclosure: Hope as an Economic Variable.* Working paper, University of Houston. [Read the current version (PDF)](paper/Lester_2026_Rational_Foreclosure.pdf) · [SSRN 6614858](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6614858).

**Try it:** [The Hope Gap](https://lesterhau.github.io/rational-foreclosure/) shows, for any U.S. state, county or large city, how far people are from giving up on a home or a decent standard of living, and what it would take to bring them back.

**Planning tool:** [The Hope Gap](https://lesterhau.github.io/rational-foreclosure/), for federal, state, county and city officials. Data refresh twice a week.

**Replication package:** Harvard Dataverse, [doi:10.7910/DVN/V5NSZX](https://doi.org/10.7910/DVN/V5NSZX) (version 2 is the October 2026 revision).

## What the paper shows

A loss-averse agent measures her wealth against a benchmark that moves at random (local house prices, the cost of living) and may stop keeping score for good. The paper proves that she quits at a threshold strictly below the benchmark, with an explicit lower bound; that a more volatile benchmark delays quitting, which gives hope an exact value; that a benchmark that runs away hastens it; and that holding her in the race past her threshold has an exact, strictly positive welfare cost. If the race must end by a date, as a working life does, every race has a quitting point, and of two people equally far behind, the one with less time left quits first (Proposition 4). Because the benchmark is shared, one shock moves a whole cohort toward its threshold at once.

## What the tool does

Pick a place, a goal (owning a home, or keeping up with the cost of living) and a group. The tool reports the **Hope Gap** for that place (the tipping point minus the gap between the goal's growth and pay growth, in points a year; above zero means hope holds), the model's quitting point, how many people are past it, what happens under several scenarios, and what it would take in homes built or pay growth to close the gap, with a dated plan for the chosen office. By default the race ends at 67, so each person's quitting point depends on the working years they have left. Each group gets its own pay trend (Census Quarterly Workforce Indicators, by age, sex, education, and race and ethnicity), the lowest income group is measured against starter homes, and a comparison table shows every group side by side. The model is solved in the browser; nothing the user enters leaves the page.

## Repository layout

```
.
├── paper/                        # the paper (PDF) and its LaTeX source
├── tool/                         # The Hope Gap: page template, build script, and an offline copy with data built in
├── pipeline/build_data.py        # builds data/core.json, counties.json, places.json from FRED, FHFA, BLS QCEW, Zillow and the Census Bureau
├── pipeline/build_groups.py      # builds data/groups.json, group pay trends, from the Census Quarterly Workforce Indicators
├── .github/workflows/data.yml    # runs the pipeline twice a week (group data about monthly) and publishes to the gh-pages branch under /data
├── code/                         # replication code for the paper (mirror of the Dataverse package, version 2)
├── data/README.md                # where the tool's data live and how they are built
└── README.md
```

The `gh-pages` branch holds the live page (`index.html`) and the published data (`data/`). An offline copy of the page, with a data snapshot built in, is in the Dataverse package (`tool/the_hope_gap.html`).

## Replication

```bash
pip install numpy scipy matplotlib
cd code
python3 sweeps.py        # Tables 2 and 3 and the table in Result 1
python3 deadline.py      # Proposition 4: quitting point by years left (Table 4)
python3 welfare.py       # Proposition 5 magnitudes, Result 3, Figure 2
python3 cohort.py        # Table 5
python3 figs.py          # Figures 1 and 2
```

`appendixA_numerical_checks.py` runs the 243-point scan behind Appendix C (10 to 20 minutes). `shoot.py` is the independent shooting solver used by the tool; it matches the collocation solver to four digits. See `code/README.md` for the full table of scripts and the results each reproduces.

## Data sources for the tool

FRED (BLS and BEA national series), FHFA House Price Index (state and county), BLS Quarterly Census of Employment and Wages, Zillow Home Value Index, Census American Community Survey. Sources, dates and fallbacks are listed on the page under *Data and methods*.

## Citation

```bibtex
@unpublished{lester2026foreclosure,
  author = {Lester, Ryan},
  title  = {Rational Foreclosure: Hope as an Economic Variable},
  year   = {2026},
  note   = {Working paper, University of Houston. SSRN 6614858. Replication package: doi:10.7910/DVN/V5NSZX},
  url    = {https://github.com/Lesterhau/rational-foreclosure}
}
```

## License

CC BY 4.0 (code, text and data). Data published under `data/` on the `gh-pages` branch are derived from the public sources listed above and remain subject to their terms.

## Contact

Ryan Lester, rslester@cougarnet.uh.edu, [ORCID 0009-0002-7840-5676](https://orcid.org/0009-0002-7840-5676).
