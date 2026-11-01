# Data

The planning tool's data are not stored on this branch. They are built twice a week by `pipeline/build_data.py`
(run by `.github/workflows/data.yml`) from FRED, FHFA, BLS QCEW, Zillow and the Census Bureau, and published to the
`gh-pages` branch under `data/` (`core.json`, `counties.json`, `places.json`, `build_log.txt`).

The paper's numerical results need no external data; the code in `code/` regenerates them. The replication package,
with a dated snapshot of the tool's data, is on Harvard Dataverse: https://doi.org/10.7910/DVN/V5NSZX
