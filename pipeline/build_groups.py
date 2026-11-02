#!/usr/bin/env python3
"""Group pay trends for The Hope Gap.

Builds groups.json: for the nation, every state and every county, how fast each group's pay has grown
relative to all workers in the same place, over the last 1, 5 and 10 years and since 1990.

Source: U.S. Census Bureau, Quarterly Workforce Indicators (QWI, LEHD program), public-use bulk files
  https://lehd.ces.census.gov/data/qwi/latest_release/<st>/
Measure: EarnS, average monthly earnings of workers who held the same job all quarter, weighted by EmpS.
Groups: age (sex-by-age files), sex (same), education (sex-by-education files, workers 25 and older),
race and ethnicity (race-by-ethnicity files). All industries, all ownership (state, local and private).

Each group's figure is a differential: the group's yearly log pay growth minus that of all workers in the
same place and period. The planning tool adds it to the area's QCEW pay trend, so the all-workers figure
there is unchanged and groups differ only by how their pay has moved relative to everyone else's.

Usage: python build_groups.py OUT_DIR
"""
import concurrent.futures as cf
import datetime as dt
import gzip
import io
import json
import math
import os
import re
import sys
import tempfile
import time
import traceback

import pandas as pd
import requests

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
os.makedirs(OUT, exist_ok=True)
BASE = "https://lehd.ces.census.gov/data/qwi/latest_release/"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) HopeGapData/1.0 (+https://lesterhau.github.io/rational-foreclosure/)"}
LOG = []
MIN_EMP = 100          # stable jobs per quarter, below which a county cell is too small to report
FIPS = ["01","02","04","05","06","08","09","10","11","12","13","15","16","17","18","19","20","21","22","23","24","25","26","27","28",
        "29","30","31","32","33","34","35","36","37","38","39","40","41","42","44","45","46","47","48","49","50","51","53","54","55","56"]
ABBR = dict(zip(FIPS, ["al","ak","az","ar","ca","co","ct","de","dc","fl","ga","hi","id","il","in","ia","ks","ky","la","me","md","ma","mi","mn","ms",
                      "mo","mt","ne","nv","nh","nj","nm","ny","nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv","wi","wy"]))
OK_FLAGS = {1, 9}      # 1 = OK, 9 = fuzzed but released; 5 (suppressed), -1 and -2 (not available) are dropped


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    LOG.append(m)


def get(url, stream=False, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=300, stream=stream)
            if r.status_code == 200:
                return r
            log("  HTTP", r.status_code, url)
            if r.status_code in (403, 404):
                return None
        except Exception as e:
            log("  ERR", url, repr(e)[:200])
        time.sleep(5 * (i + 1))
    return None


def find_files(st):
    """Read the state's directory listing and pick the county and state files for the three tabulations."""
    r = get(BASE + st + "/")
    names = sorted(set(re.findall(r'qwi_%s_[a-z0-9_]+\.csv\.gz' % st, r.text))) if r is not None else []
    out = {}
    for demo in ("sa", "se", "rh"):
        for geo in ("gc", "gs"):
            pat = re.compile(r"qwi_%s_%s_f_%s_n_o[a-z]*_u\.csv\.gz" % (st, demo, geo))
            c = [n for n in names if pat.fullmatch(n)]
            # prefer all ownership (state, local and private) over private only
            c.sort(key=lambda n: (0 if "_oslp_" in n else 1, n))
            if c:
                out[(demo, geo)] = c[0]
    return out, len(names)


COLS = ["geography", "industry", "ownercode", "sex", "agegrp", "race", "ethnicity", "education",
        "firmage", "firmsize", "year", "quarter", "EmpS", "EarnS", "sEarnS"]


def read_file(st, name):
    """Stream one bulk file and return rows with usable earnings, aggregated to payroll and jobs."""
    t = time.time()
    r = get(BASE + st + "/" + name, stream=True)
    if r is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv.gz")
    size = 0
    for chunk in r.iter_content(1 << 20):
        tmp.write(chunk)
        size += len(chunk)
    tmp.close()
    parts = []
    try:
        for df in pd.read_csv(tmp.name, compression="gzip", usecols=lambda c: c in COLS, dtype=str, chunksize=400_000):
            df = df[(df["industry"].isin(["00", "0"])) & (df["firmage"].isin(["0", "00"])) & (df["firmsize"].isin(["0", "00"]))]
            if "ownercode" in df:
                df = df[df["ownercode"].isin(["A00", "A05"])]
            df = df[pd.to_numeric(df["year"], errors="coerce") >= 1990]
            fl = pd.to_numeric(df["sEarnS"], errors="coerce")
            df = df[fl.isin(OK_FLAGS)]
            emp = pd.to_numeric(df["EmpS"], errors="coerce")
            earn = pd.to_numeric(df["EarnS"], errors="coerce")
            ok = emp.notna() & earn.notna() & (emp > 0) & (earn > 0)
            df = df[ok].copy()
            df["emp"] = emp[ok]
            df["pay"] = emp[ok] * earn[ok]
            df["t"] = df["year"].astype(int) * 4 + df["quarter"].astype(int) - 1
            parts.append(df[["geography", "ownercode", "sex", "agegrp", "race", "ethnicity", "education", "t", "emp", "pay"]])
    finally:
        os.unlink(tmp.name)
    out = pd.concat(parts) if parts else None
    if out is not None and "A00" in set(out["ownercode"]):
        out = out[out["ownercode"] == "A00"]
    log(f"   {name}: {size/1e6:.1f} MB, {0 if out is None else len(out)} rows, {time.time()-t:.0f}s")
    return out


# cell definitions: (tabulation, list of (column filters)) -> rows whose payroll and jobs are summed
def cells(demo, df):
    """Return {cell: DataFrame of [geography, t, emp, pay]} for one tabulation, plus the all-workers rows."""
    S = lambda **kv: df.loc[pd.concat([df[k] == v for k, v in kv.items()], axis=1).all(axis=1)]
    ANY = lambda col, vals: df[col].isin(vals)
    out = {}
    if demo == "sa":
        out["all"] = S(sex="0", agegrp="A00")
        for i, ags in enumerate([["A02", "A03"], ["A04"], ["A05"], ["A06"], ["A07"], ["A08"]]):
            out[f"a{i}"] = df[(df["sex"] == "0") & ANY("agegrp", ags)]
        out["s0"] = S(sex="2", agegrp="A00")
        out["s1"] = S(sex="1", agegrp="A00")
    elif demo == "se":
        out["all"] = S(sex="0", education="E0")
        out["e0"] = df[(df["sex"] == "0") & ANY("education", ["E1", "E2", "E3"])]
        out["e1"] = S(sex="0", education="E4")
    else:
        out["all"] = S(race="A0", ethnicity="A0")
        cross = ((df["race"] != "A0") & (df["ethnicity"] == "A1")).any()
        eth = "A1" if cross else "A0"
        out["r0"] = S(race="A1", ethnicity=eth)
        out["r1"] = S(race="A2", ethnicity=eth)
        out["r2"] = S(race="A0", ethnicity="A2")
        out["r3"] = S(race="A4", ethnicity=eth)
        out["r4"] = df[ANY("race", ["A3", "A5", "A7"]) & (df["ethnicity"] == eth)]
        out["_cross"] = cross
    return out


def series(rows):
    """geography -> {t: (emp, pay)} summed over the rows of a cell."""
    if rows is None or not len(rows):
        return {}
    g = rows.groupby(["geography", "t"])[["emp", "pay"]].sum()
    out = {}
    for (geo, t), v in g.iterrows():
        out.setdefault(geo, {})[t] = (v["emp"], v["pay"])
    return out


def avg4(s, t_end):
    """Average monthly earnings over the four quarters ending at t_end, and average jobs; None if any quarter is missing."""
    e = p = 0.0
    for t in range(t_end - 3, t_end + 1):
        if t not in s:
            return None, None
        e += s[t][0]
        p += s[t][1]
    return (p / e if e > 0 else None), e / 4


def growth(s, end, years, min_emp):
    a, ea = avg4(s, end)
    b, eb = avg4(s, end - 4 * years)
    if a is None or b is None or ea < min_emp or eb < min_emp:
        return None
    return math.log(a / b) / years


def build_geo(cellser, geo, end, lr_start, min_emp):
    """Differentials (1e-4 units, ints) and jobs for one geography."""
    allS = cellser["all"].get(geo, {})
    if not allS:
        return None
    lr_years = (end - lr_start) // 4
    g_all = {k: growth(allS, end, k, 0) for k in (1, 5, 10)}
    g_all["lr"] = growth(allS, end, lr_years, 0) if lr_years >= 10 else None
    out = {}
    for c, ser in cellser.items():
        if c == "all" or c.startswith("_"):
            continue
        s = ser.get(geo, {})
        if not s:
            out[c] = None
            continue
        d = []
        for k in (1, 5, 10, "lr"):
            yrs = lr_years if k == "lr" else k
            if k == "lr" and lr_years < 10:
                d.append(None)
                continue
            g = growth(s, end, yrs, min_emp)
            d.append(None if (g is None or g_all[k] is None) else int(round((g - g_all[k]) * 1e4)))
        _, w = avg4(s, end)
        out[c] = d + [int(round(w)) if w else 0]
    return out


def latest_common(allS_by_geo, min_cover=0.9):
    """Latest quarter for which at least min_cover of geographies have four full quarters of all-workers data."""
    ts = set()
    for s in allS_by_geo.values():
        ts.update(s.keys())
    if not ts:
        return None
    n = len(allS_by_geo)
    for t in sorted(ts, reverse=True):
        k = sum(1 for s in allS_by_geo.values() if all(u in s for u in range(t - 3, t + 1)))
        if k >= min_cover * n:
            return t
    return None


def first_full(allS):
    ts = sorted(allS.keys())
    for t in ts:
        if all(u in allS for u in range(t, t + 4)):
            return t + 3
    return None


def do_state(fips):
    st = ABBR[fips]
    files, nlist = find_files(st)
    log(f"== {st.upper()}: {nlist} files listed; using", ", ".join(sorted(files.values())) or "none")
    res = {"st": None, "cty": {}, "cross": None}
    gs_cells, gc_cells = {}, {}
    for demo in ("sa", "se", "rh"):
        for geo, store in (("gs", gs_cells), ("gc", gc_cells)):
            name = files.get((demo, geo))
            if not name:
                continue
            df = read_file(st, name)
            if df is None or not len(df):
                continue
            cs = cells(demo, df)
            if demo == "rh":
                res["cross"] = bool(cs.pop("_cross", False))
            for c, rows in cs.items():
                if c == "all":
                    store.setdefault("all_" + demo, series(rows))
                else:
                    store[c] = series(rows)
            del df
    if not gs_cells:
        return fips, res
    # state
    allS = gs_cells.get("all_sa") or gs_cells.get("all_se") or gs_cells.get("all_rh")
    allS_geo = next(iter(allS.values())) if allS else {}
    end = latest_common(allS) if allS else None
    if end is None:
        return fips, res
    lr_start = max(first_full(allS_geo) or end, 1990 * 4 + 3)
    res["end"] = end
    res["lr_start"] = lr_start

    def assemble(store, geo, min_emp):
        merged = {}
        for demo in ("sa", "se", "rh"):
            base = store.get("all_" + demo)
            if not base:
                continue
            sub = {"all": base}
            for c, ser in store.items():
                if c.startswith("all_"):
                    continue
                if (demo == "sa" and c[0] in "as") or (demo == "se" and c[0] == "e") or (demo == "rh" and c[0] == "r"):
                    sub[c] = ser
            r = build_geo(sub, geo, end, lr_start, min_emp)
            if r:
                merged.update(r)
        return merged or None

    sg = next(iter(allS.keys()))
    res["st"] = assemble(gs_cells, sg, 0)
    ctys = set(gc_cells.get("all_sa", {})) | set(gc_cells.get("all_se", {})) | set(gc_cells.get("all_rh", {}))
    for cg in ctys:
        r = assemble(gc_cells, cg, MIN_EMP)
        if r:
            res["cty"][cg.zfill(5)] = r
    log(f"   {st.upper()}: end {end//4} Q{end%4+1}, since {lr_start//4}, {len(res['cty'])} counties, race x ethnicity cross: {res['cross']}")
    return fips, res


def main():
    t0 = time.time()
    states, ctys, ends, lr0 = {}, {}, {}, {}
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(do_state, f) for f in FIPS]
        for fu in cf.as_completed(futs):
            try:
                f, r = fu.result()
            except Exception:
                log("FAILED state", traceback.format_exc()[-800:])
                continue
            if r.get("st"):
                states[f] = r["st"]
                ends[f] = r["end"]
                lr0[f] = r["lr_start"] // 4
            ctys.update(r["cty"])
    # nation: each group's differential is the jobs-weighted average of the state differentials, so states whose
    # latest quarter or first year differs do not change the mix of states from one period to the other
    us = None
    if states:
        merged = {}
        keys = set().union(*[set(s) for s in states.values()])
        for c in keys:
            row = []
            for i in range(4):
                num = den = 0.0
                for f, s in states.items():
                    v = s.get(c)
                    if v and v[i] is not None and v[4]:
                        num += v[i] * v[4]
                        den += v[4]
                row.append(int(round(num / den)) if den else None)
            row.append(int(sum((s.get(c) or [0] * 5)[4] for s in states.values())))
            merged[c] = row
        e = sorted(ends.values())
        us = {"c": merged, "end": f"{e[len(e)//2]//4} Q{e[len(e)//2]%4+1}", "lr0": sorted(lr0.values())[len(lr0) // 2],
              "note": "Jobs-weighted average of state differentials."}
    out = {
        "built": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"),
        "src": "U.S. Census Bureau, Quarterly Workforce Indicators (LEHD), average monthly earnings of stable jobs (EarnS)",
        "units": "differential in yearly log pay growth versus all workers in the same place, x 1e-4; then average stable jobs",
        "order": ["1", "5", "10", "lr", "jobs"],
        "us": us,
        "st": {f: {"c": states[f], "end": f"{ends[f]//4} Q{ends[f]%4+1}", "lr0": lr0[f]} for f in states},
        "cty": ctys,
    }
    json.dump(out, open(os.path.join(OUT, "groups.json"), "w"), separators=(",", ":"))
    log(f"wrote groups.json: {len(states)} states, {len(ctys)} counties in {time.time()-t0:.0f}s")


try:
    main()
except Exception:
    log("FATAL", traceback.format_exc())
finally:
    open(os.path.join(OUT, "groups_log.txt"), "w").write("\n".join(LOG) + "\n")
