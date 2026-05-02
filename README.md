# Rational Foreclosure: A Stochastic Reference Point Model of Aspirational Abandonment under Positional Drift

[![SSRN](https://img.shields.io/badge/SSRN-6614858-blue?style=flat-square)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6614858)
[![Harvard Dataverse](https://img.shields.io/badge/DOI-10.7910%2FDVN%2FV5NSZX-C90016?style=flat-square)](https://doi.org/10.7910/DVN/V5NSZX)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--7840--5676-A6CE39?style=flat-square&logo=orcid)](https://orcid.org/0009-0002-7840-5676)
[![Version](https://img.shields.io/badge/Version-7.0-green?style=flat-square)]()
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey?style=flat-square)](https://creativecommons.org/licenses/by/4.0/)

**Author:** Ryan S. Lester, RL Perspectives, LLC · University of Houston

---

## Abstract

Why do people abandon aspirations they once pursued with genuine commitment? Standard rational choice models treat goal revision as a straightforward utility-maximizing update. This paper argues otherwise.

I develop a continuous-time stochastic model in which agents maintain aspirational reference points that drift upward with peer comparison signals, while their subjective assessment of their own trajectory is shaped by both current position and accumulated positional history. The central result — the **Volatility-Delay Theorem (Theorem 2)** — establishes that aspiration volatility increases option value, causing rational agents to delay foreclosure longer than naive expected-utility maximization would predict. Crucially, this delay is not irrational: it reflects the real option value of waiting in an uncertain positional environment.

The model generates empirically testable predictions about the timing and conditions of aspirational abandonment, with applications to educational attainment, occupational choice, entrepreneurship, and social mobility research.

**Key theoretical contributions:**
- Stochastic reference point dynamics incorporating Kőszegi-Rabin loss aversion
- BVP (boundary value problem) reformulation of the foreclosure decision
- Volatility-delay theorem establishing that σ_R delays foreclosure via option value channel
- Positional weight theorem (Theorem 4): positional weight delays foreclosure, scaling in σ_R
- Defense of H non-C² discontinuity against technical objections (Section 3.3)

---

## Theoretical Antecedents

| Author(s) | Paper | Contribution to This Work |
|---|---|---|
| Kőszegi & Rabin (2006) | *A Model of Reference-Dependent Preferences* | Core reference point framework |
| Henderson (2012) | *Prospect Theory, Liquidation, and the Disposition Effect* | Option-value approach to loss aversion |
| Genicot & Ray (2017) | *Aspirations and Inequality* | Aspiration formation and social dynamics |

---

## Repository Structure

```
rational-foreclosure/
├── paper/
│   └── rational_foreclosure_v7.pdf        # Current manuscript
├── data/
│   └── README_dataverse.md                # Links to Harvard Dataverse (DOI pending)
├── code/
│   ├── simulation/
│   │   ├── bvp_solver.py                  # BVP reformulation solver
│   │   ├── monte_carlo_paths.py           # Stochastic path simulations
│   │   └── foreclosure_threshold.py       # Threshold computation
│   ├── figures/
│   │   └── generate_figures.py            # All paper figures
│   └── requirements.txt
└── replication/
    └── REPLICATION.md                     # Replication instructions
```

---

## Data

The foreclosure dataset is archived at **Harvard Dataverse** (DOI activation pending). Upon DOI activation, all data and replication code will be fully public and citable.

---

## Status

| Milestone | Status |
|---|---|
| Paper draft (v7.2) | ✅ Complete |
| Harvard Dataverse DOI | ✅ Active — [10.7910/DVN/V5NSZX](https://doi.org/10.7910/DVN/V5NSZX) |
| SSRN preprint | ✅ Posted — [abstract_id=6614858](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6614858) |
| Co-author search (PDE expert, Conjecture 1 → Theorem 1) | 🔄 Active — UH authorized |
| Journal submission | 📋 Target: *Theoretical Economics* |

---

## Citation

```bibtex
@unpublished{lester2026foreclosure,
  author  = {Lester, Ryan S.},
  title   = {Rational Foreclosure: A Stochastic Reference Point Model of 
             Aspirational Abandonment under Positional Drift},
  year    = {2026},
  note    = {Pre-publication manuscript, v7. SSRN preprint forthcoming.},
  url     = {https://github.com/Lesterhau/rational-foreclosure}
}
```

---

## Contact

**Ryan S. Lester** · rslester@cougarnet.uh.edu · [ORCID](https://orcid.org/0009-0002-7840-5676) · [RL Perspectives](https://rlperspectives.com)
