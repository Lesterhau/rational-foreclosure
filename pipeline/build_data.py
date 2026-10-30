#!/usr/bin/env python3
"""Build the data behind The Hope Gap planning tool from public sources.

Usage: python build_data.py OUT_DIR [PREVIOUS_DATA_DIR]

Sources (no API keys required; CENSUS_API_KEY is used if set):
  FRED (St. Louis Fed)      national prices, GDP, jobs, pay, FHFA U.S. home price index
  FHFA                      state (quarterly) and county (annual) home price indexes
  BLS QCEW                  average weekly wages for the nation, states and counties
  Zillow Research           typical home values (ZHVI) for the nation, states, counties, cities
  Census ACS (API)          population, age, race and ethnicity, education, income, tenure
  Census relationship file  which county each city mostly lies in

Every source is fetched independently. If one fails, the previous run's values are kept,
and the failure is written to build_log.txt.
"""
import io, json, math, os, sys, time, zipfile, datetime as dt, traceback
import numpy as np
import pandas as pd
import requests

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
PREV = sys.argv[2] if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) HopeGapData/1.0 (+https://lesterhau.github.io/rational-foreclosure/)"}
LOG, STATUS = [], {}
KEY = os.environ.get("CENSUS_API_KEY") or ""

def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    LOG.append(m)

def get(url, tries=4, **kw):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=180, **kw)
            if r.status_code == 200 and r.content:
                return r
            log("  HTTP", r.status_code, url[:160])
            if r.status_code in (400, 404):
                return None
        except Exception as e:
            log("  ERR", url[:160], repr(e)[:200])
        time.sleep(4 * (i + 1))
    return None

def num(x):
    try:
        v = float(x)
    except Exception:
        return None
    if not math.isfinite(v) or v <= -555555555:
        return None
    return v

def rnd(x, d=4):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(float(x), d)

def stage(name):
    def deco(fn):
        def run(*a, **k):
            log(f"== {name}")
            t = time.time()
            try:
                out = fn(*a, **k)
                STATUS[name] = "ok"
                log(f"   {name}: ok in {time.time()-t:.0f}s")
                return out
            except Exception as e:
                STATUS[name] = "failed: " + repr(e)[:200]
                log(f"   {name}: FAILED", repr(e)[:300])
                log(traceback.format_exc()[-1500:])
                return None
        return run
    return deco

FIPS = {"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT","10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN","19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI","27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ","35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA","44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA","53":"WA","54":"WV","55":"WI","56":"WY"}
ABBR = {v: k for k, v in FIPS.items()}
NAMES = {"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"}

# ---------------------------------------------------------------- previous run
def load_prev(name):
    if not PREV:
        return None
    p = os.path.join(PREV, name)
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:
            return None
    return None

PREV_CORE = load_prev("core.json") or {}
PREV_CTY = {c["f"]: c for c in (load_prev("counties.json") or [])}
PREV_PLC = {c["f"]: c for c in (load_prev("places.json") or [])}

# ---------------------------------------------------------------- FRED
def fred(sid):
    r = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")
    if r is None:
        raise RuntimeError("FRED " + sid)
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "v"]
    df["date"] = pd.to_datetime(df["date"])
    df["v"] = pd.to_numeric(df["v"], errors="coerce")
    return df.dropna().set_index("date")["v"]

def yoy(s):
    last = s.index[-1]
    prev = last - pd.DateOffset(years=1)
    if prev not in s.index:
        prev = s.index[s.index.get_indexer([prev], method="nearest")[0]]
    return 100 * (s[last] / s[prev] - 1), last

def qavg(s):
    """Quarterly averages keyed by (year, quarter)."""
    g = s.groupby([s.index.year, s.index.quarter]).mean()
    return {(int(y), int(q)): float(v) for (y, q), v in g.items()}

@stage("FRED national series")
def national():
    ids = ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE", "PPIFIS", "GDPC1", "GDP", "UNRATE", "CES0500000003",
           "LES1252881500Q", "LES1252881600Q", "A939RX0Q048SBEA", "USSTHPI", "MORTGAGE30US"]
    S = {}
    for i in ids:
        try:
            S[i] = fred(i)
        except Exception as e:
            log("  missing", i, e)
        time.sleep(0.5)
    F = {}
    def put(k, val, date, src, unit="%"):
        F[k] = {"v": rnd(val, 2), "d": pd.Timestamp(date).strftime("%Y-%m-%d"), "s": src, "u": unit}
    for k, sid, src in [("cpi", "CPIAUCSL", "BLS CPI-U, all items"), ("core", "CPILFESL", "BLS CPI-U, excluding food and energy"),
                        ("pce", "PCEPI", "BEA PCE price index"), ("corepce", "PCEPILFE", "BEA PCE excluding food and energy"),
                        ("ppi", "PPIFIS", "BLS PPI, final demand"), ("ahe", "CES0500000003", "BLS average hourly earnings, private")]:
        if sid in S:
            v, d = yoy(S[sid]); put(k, v, d, src)
    for k, sid, src in [("rgdp", "GDPC1", "BEA real GDP, annual rate"), ("ngdp", "GDP", "BEA nominal GDP, annual rate")]:
        if sid in S:
            s = S[sid]; put(k, 100 * ((s.iloc[-1] / s.iloc[-2]) ** 4 - 1), s.index[-1], src)
    if "UNRATE" in S:
        put("unemp", S["UNRATE"].iloc[-1], S["UNRATE"].index[-1], "BLS unemployment rate")
    if "MORTGAGE30US" in S:
        put("mort", S["MORTGAGE30US"].iloc[-1], S["MORTGAGE30US"].index[-1], "Freddie Mac 30-year fixed rate")
    if "USSTHPI" in S:
        v, d = yoy(S["USSTHPI"]); put("hpi1", v, d, "FHFA House Price Index, all transactions")
    # since 1979: pay, prices, output per person
    def avg_year(s, y):
        x = s[s.index.year == y]
        return float(x.mean()) if len(x) else None
    def last4(s):
        return float(s.iloc[-4:].mean()), s.index[-1]
    lr = {}
    if "LES1252881500Q" in S and "CPIAUCSL" in S:
        p0 = avg_year(S["LES1252881500Q"], 1979); p1, d1 = last4(S["LES1252881500Q"])
        c0 = avg_year(S["CPIAUCSL"], 1979); c1 = float(S["CPIAUCSL"].iloc[-12:].mean())
        lr.update({"pay79": rnd(p0, 0), "payNow": rnd(p1, 0), "payX": rnd(p1 / p0, 2), "cpiX": rnd(c1 / c0, 2), "realPay": rnd(100 * (p1 / p0 / (c1 / c0) - 1), 1), "d": d1.strftime("%Y-%m-%d")})
    if "A939RX0Q048SBEA" in S:
        g0 = avg_year(S["A939RX0Q048SBEA"], 1979); g1, _ = last4(S["A939RX0Q048SBEA"])
        lr["gdppc"] = rnd(100 * (g1 / g0 - 1), 1)
    if "LES1252881600Q" in S:
        s = S["LES1252881600Q"]; a = s.groupby(s.index.year).mean()
        a = a[(a.index >= 1990) & (a.index < pd.Timestamp.today().year)]
        lr["sigReal"] = rnd(float(np.std(np.diff(np.log(a.values)), ddof=1)), 4)
    F["since1979"] = lr
    return F, S

# ---------------------------------------------------------------- FHFA
@stage("FHFA state index")
def fhfa_state():
    r = get("https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.csv")
    if r is None:
        raise RuntimeError("download")
    df = pd.read_csv(io.StringIO(r.text), header=None)
    if not str(df.iloc[0, 1]).strip().isdigit():
        df = df.iloc[1:]
    df = df.iloc[:, :4]
    df.columns = ["st", "y", "q", "v"]
    df["y"] = df["y"].astype(int); df["q"] = df["q"].astype(int); df["v"] = pd.to_numeric(df["v"], errors="coerce")
    out = {}
    for st, g in df.dropna().groupby("st"):
        out[str(st).strip()] = {(int(a), int(b)): float(c) for a, b, c in zip(g["y"], g["q"], g["v"])}
    log("   states:", len(out), "latest", max(max(v) for v in out.values()))
    return out

@stage("FHFA county index")
def fhfa_county():
    r = get("https://www.fhfa.gov/hpi/download/annual/hpi_at_county.xlsx")
    if r is None:
        raise RuntimeError("download")
    raw = pd.read_excel(io.BytesIO(r.content), header=None)
    # Columns by position, per the file's own note: A state, B county, C FIPS, D year, E annual change,
    # F index (base 100 when first recorded), G base 1990, H base 2000.
    df = raw.iloc[:, [2, 3, 5]].copy()
    df.columns = ["f", "y", "v"]
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df["v"] = pd.to_numeric(df["v"], errors="coerce")
    df = df[(df["y"] > 1960) & (df["y"] < 2100)]
    df["f"] = df["f"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(5)
    out = {}
    for f, g in df.dropna().groupby("f"):
        out[f] = {int(a): float(b) for a, b in zip(g["y"], g["v"])}
    log("   counties:", len(out))
    return out

def trend_q(series, end, years):
    a, b = series.get(end), series.get((end[0] - years, end[1]))
    return None if not a or not b else math.log(a / b) / years

def trend_y(series, end, years):
    a, b = series.get(end), series.get(end - years)
    return None if not a or not b else math.log(a / b) / years

def hpi_stats_q(series):
    end = max(series)
    yrs_lr = end[0] - 1990
    ann = [math.log(series[(y, 4)] / series[(y - 1, 4)]) for y in range(1991, end[0] + 1) if (y, 4) in series and (y - 1, 4) in series]
    return {"g1": rnd(trend_q(series, end, 1)), "g5": rnd(trend_q(series, end, 5)), "g10": rnd(trend_q(series, end, 10)),
            "glr": rnd(trend_q(series, end, yrs_lr)), "lr0": 1990, "sig": rnd(float(np.std(ann, ddof=1)) if len(ann) > 5 else None),
            "end": f"{end[0]} Q{end[1]}"}

def hpi_stats_y(series):
    end = max(series)
    ann = [math.log(series[y] / series[y - 1]) for y in range(1991, end + 1) if y in series and y - 1 in series and series[y - 1] > 0]
    lr0 = 1990 if 1990 in series else min(series)
    return {"g1": rnd(trend_y(series, end, 1)), "g5": rnd(trend_y(series, end, 5)), "g10": rnd(trend_y(series, end, 10)),
            "glr": rnd(trend_y(series, end, end - lr0)) if end - lr0 >= 10 else None, "lr0": lr0,
            "sig": rnd(float(np.std(ann, ddof=1)) if len(ann) >= 10 else None), "end": str(end)}

# ---------------------------------------------------------------- QCEW
def qcew_quarter(y, q):
    r = get(f"https://data.bls.gov/cew/data/api/{y}/{q}/industry/10.csv", tries=2)
    if r is None:
        return None
    df = pd.read_csv(io.StringIO(r.text), dtype={"area_fips": str})
    df = df[(df["own_code"] == 0)]
    return {a: float(w) for a, w in zip(df["area_fips"], df["avg_wkly_wage"]) if float(w) > 0}

def qcew_annual(y):
    r = get(f"https://data.bls.gov/cew/data/api/{y}/a/industry/10.csv", tries=2)
    if r is not None:
        df = pd.read_csv(io.StringIO(r.text), dtype={"area_fips": str})
    else:
        r = get(f"https://data.bls.gov/cew/data/files/{y}/csv/{y}_annual_singlefile.zip", tries=2)
        if r is None:
            return None
        z = zipfile.ZipFile(io.BytesIO(r.content))
        df = pd.read_csv(z.open(z.namelist()[0]), dtype={"area_fips": str, "industry_code": str})
        df = df[df["industry_code"].astype(str) == "10"]
    df = df[(df["own_code"] == 0)]
    return {a: float(w) for a, w in zip(df["area_fips"], df["annual_avg_wkly_wage"]) if float(w) > 0}

@stage("BLS QCEW wages")
def qcew():
    today = dt.date.today()
    end = None
    for y in range(today.year, today.year - 2, -1):
        for q in (4, 3, 2, 1):
            if (y, q) >= (today.year, (today.month - 1) // 3 + 1):
                continue
            d = qcew_quarter(y, q)
            if d:
                end, cur = (y, q), d
                break
        if end:
            break
    if not end:
        raise RuntimeError("no recent QCEW quarter")
    log("   latest quarter", end)
    W = {"end": end, 0: cur}
    for k in (1, 5, 10):
        W[k] = qcew_quarter(end[0] - k, end[1]) or {}
        log(f"   {k}y back:", len(W[k]))
    W["2019"] = qcew_quarter(2019, end[1]) or {}
    la = end[0] - 1 if end[1] < 4 else end[0]
    W["ann"] = qcew_annual(la) or {}
    W["ann1990"] = qcew_annual(1990) or {}
    W["annY"] = la
    log("   annual", la, len(W["ann"]), "1990", len(W["ann1990"]))
    return W

def pay_stats(W, area):
    if not W or area not in W[0]:
        return None
    w = W[0][area]
    def g(k):
        b = W.get(k, {}).get(area)
        return rnd(math.log(w / b) / k) if b else None
    lr = None
    a1, a0 = W["ann"].get(area), W["ann1990"].get(area)
    if a1 and a0:
        lr = rnd(math.log(a1 / a0) / (W["annY"] - 1990))
    return {"wk": rnd(w, 0), "g1": g(1), "g5": g(5), "g10": g(10), "glr": lr, "lr0": 1990,
            "w19": rnd(W["2019"].get(area), 0), "end": f"{W['end'][0]} Q{W['end'][1]}"}

# ---------------------------------------------------------------- Zillow
ZBASE = "https://files.zillowstatic.com/research/public_csvs/zhvi/"
def zillow(kind):
    r = get(ZBASE + f"{kind}_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv")
    if r is None:
        raise RuntimeError("download " + kind)
    df = pd.read_csv(io.StringIO(r.text))
    dcols = [c for c in df.columns if c[:2] in ("19", "20")]
    last = dcols[-1]
    return df, last

@stage("Zillow home values")
def zhvi():
    out = {"state": {}, "county": {}, "city": {}, "us": None}
    df, last = zillow("Metro")
    us = df[df["RegionType"].astype(str).str.lower() == "country"]
    if len(us):
        out["us"] = (float(us.iloc[0][last]), last)
    df, last = zillow("State")
    for _, r in df.iterrows():
        v = num(r[last])
        if v:
            out["state"][str(r["RegionName"])] = (v, last)
    df, last = zillow("County")
    for _, r in df.iterrows():
        v = num(r[last])
        if v:
            f = f"{int(r['StateCodeFIPS']):02d}{int(r['MunicipalCodeFIPS']):03d}"
            out["county"][f] = (v, last)
            out.setdefault("cname", {})[(str(r["RegionName"]).lower(), f[:2])] = f
            out.setdefault("cnameRev", {})[f] = str(r["RegionName"])
    df, last = zillow("City")
    stc = "State" if "State" in df.columns else "StateName"
    for _, r in df.iterrows():
        v = num(r[last])
        if v:
            out["city"][(str(r["RegionName"]).lower(), str(r[stc]).upper())] = (v, last, str(r.get("CountyName", "")))
    log("   states", len(out["state"]), "counties", len(out["county"]), "cities", len(out["city"]), "date", last)
    return out

# ---------------------------------------------------------------- Census ACS
AGE_M = {0: [7, 8, 9, 10], 1: [11, 12], 2: [13, 14], 3: [15, 16], 4: [17, 18, 19], 5: [20, 21, 22, 23, 24, 25]}
AGE_VARS = [f"B01001_{i:03d}E" for i in range(7, 26)] + [f"B01001_{i:03d}E" for i in range(31, 50)]
OTHER_VARS = (["B03002_001E", "B03002_003E", "B03002_004E", "B03002_006E", "B03002_012E",
               "B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E",
               "B19013_001E", "B19013H_001E", "B19013B_001E", "B19013I_001E", "B19013D_001E", "B19013G_001E",
               "B19049_002E", "B19049_003E", "B19049_004E", "B19049_005E",
               "B19080_001E", "B19080_002E", "B19080_003E", "B19080_004E", "B19080_005E",
               "B20004_001E", "B20004_002E", "B20004_003E", "B20004_004E", "B20004_005E", "B20004_006E",
               "B25003_001E", "B25003_002E", "B25119_002E", "B25119_003E",
               "B11001_001E", "B25001_001E", "B25077_001E", "B01001_001E"])

def acs_record(r):
    g = lambda v: num(r.get(v))
    ages = []
    for k in range(6):
        ages.append(sum((g(f"B01001_{i:03d}E") or 0) + (g(f"B01001_{i+24:03d}E") or 0) for i in AGE_M[k]))
    fem = sum(g(f"B01001_{i:03d}E") or 0 for i in range(31, 50))
    adults = sum(ages) or None
    tot = g("B03002_001E") or None
    race = None
    if tot:
        w, b, a, h = (g("B03002_003E") or 0), (g("B03002_004E") or 0), (g("B03002_006E") or 0), (g("B03002_012E") or 0)
        race = [rnd(w / tot), rnd(b / tot), rnd(h / tot), rnd(a / tot), rnd(max(0, tot - w - b - a - h) / tot)]
    e25 = g("B15003_001E")
    ba = rnd(sum(g(f"B15003_{i:03d}E") or 0 for i in (22, 23, 24, 25)) / e25) if e25 else None
    earn = None
    if g("B20004_001E"):
        nb = [x for x in (g("B20004_002E"), g("B20004_003E"), g("B20004_004E")) if x]
        bb = [x for x in (g("B20004_005E"), g("B20004_006E")) if x]
        earn = {"all": g("B20004_001E"), "noBA": rnd(float(np.mean(nb)), 0) if nb else None, "BA": rnd(float(np.mean(bb)), 0) if bb else None}
    hh = g("B25003_001E")
    own = g("B25003_002E")
    return {"pop": g("B01001_001E"), "ages": [rnd(x, 0) for x in ages], "fem": rnd(fem / adults) if adults else None,
            "race": race, "ba": ba, "inc": g("B19013_001E"),
            "incRace": [g("B19013H_001E"), g("B19013B_001E"), g("B19013I_001E"), g("B19013D_001E"), g("B19013G_001E")],
            "incAge": [g("B19049_002E"), g("B19049_003E"), g("B19049_004E"), g("B19049_005E")],
            "q": [g(f"B19080_{i:03d}E") for i in range(1, 6)], "earn": earn,
            "own": rnd(own / hh) if hh and own is not None else None,
            "incOwn": g("B25119_002E"), "incRent": g("B25119_003E"),
            "hh": g("B11001_001E"), "units": g("B25001_001E"), "acsVal": g("B25077_001E")}

TABLES = ["b01001", "b03002", "b15003", "b19013", "b19013b", "b19013d", "b19013g", "b19013h", "b19013i", "b19049",
          "b19080", "b20004", "b25003", "b25119", "b11001", "b25001", "b25077"]
NEED = set(AGE_VARS) | set(OTHER_VARS)
SFBASE = "https://www2.census.gov/programs-surveys/acs/summary_file/{y}/table-based-SF/"
PREFIX = {"us": "0100000US", "state": "0400000US", "county": "0500000US", "place": "1600000US"}

def sf_name(c):
    """B01001_E007 -> B01001_007E"""
    if "_E" in c:
        t, n = c.split("_E", 1)
        return f"{t}_{n}E"
    return None

def sf_table(y, kind, table, prefixes):
    url = SFBASE.format(y=y) + f"data/{kind}YRData/acsdt{kind.lower()}y{y}-{table}.dat"
    r = requests.get(url, headers=UA, timeout=600, stream=True)
    if r.status_code != 200:
        log("  HTTP", r.status_code, url)
        return None
    rows, hdr = [], None
    for line in r.iter_lines():
        if isinstance(line, bytes):
            line = line.decode("utf-8", "replace")
        if hdr is None:
            hdr = line.split("|")
            keep = [k for k, c in enumerate(hdr) if c == "GEO_ID" or (sf_name(c) in NEED)]
            continue
        if line.startswith(prefixes):
            parts = line.split("|")
            rows.append([parts[k] for k in keep])
    cols = ["GEO_ID" if hdr[k] == "GEO_ID" else sf_name(hdr[k]) for k in keep]
    return pd.DataFrame(rows, columns=cols).set_index("GEO_ID")

def sf_names(y, kind):
    url = SFBASE.format(y=y) + f"documentation/Geos{y}{kind}YR.txt"
    r = get(url, tries=2)
    if r is None:
        return {}
    try:
        df = pd.read_csv(io.StringIO(r.content.decode("utf-8", "replace")), sep="|", dtype=str)
        return dict(zip(df["GEO_ID"], df["NAME"]))
    except Exception as e:
        log("   geos parse", e)
        return {}

def sf_all(y, kind, prefixes):
    frames = []
    for t in TABLES:
        df = sf_table(y, kind, t, prefixes)
        if df is None:
            return None
        frames.append(df)
    return pd.concat(frames, axis=1)

ACS_YEARS = [2025, 2024]

@stage("Census ACS")
def census():
    out = {"us": None, "state": {}, "county": {}, "place": {}, "src": {}}
    for y in ACS_YEARS:
        df = sf_all(y, "1", (PREFIX["us"], PREFIX["state"], PREFIX["county"], PREFIX["place"]))
        if df is None or not len(df):
            continue
        names = sf_names(y, "1")
        src = f"ACS {y} 1-year"
        for gid, r in df.iterrows():
            rec = acs_record(r.to_dict())
            code = gid.split("US", 1)[1]
            if gid.startswith(PREFIX["us"]):
                out["us"] = rec
            elif gid.startswith(PREFIX["state"]):
                out["state"][code] = rec
            elif gid.startswith(PREFIX["county"]):
                rec["name"] = names.get(gid, ""); rec["acs"] = src; out["county"][code] = rec
            elif gid.startswith(PREFIX["place"]):
                rec["name"] = names.get(gid, ""); rec["acs"] = src; out["place"][code] = rec
        out["src"] = {"us": src, "state": src, "county1": src}
        break
    # 5-year for every county; skipped when the previous run already holds this vintage
    for y in [2024, 2023]:
        tag = f"ACS {y-4}-{y} 5-year"
        have = [c for c in PREV_CTY.values() if c.get("acs") == tag]
        if len(have) > 2500:
            log("   5-year", tag, "already loaded; keeping previous values for small counties")
            out["src"]["county5"] = tag
            break
        df = sf_all(y, "5", (PREFIX["county"],))
        if df is None or not len(df):
            continue
        names = sf_names(y, "5")
        n = 0
        for gid, r in df.iterrows():
            code = gid.split("US", 1)[1]
            if code in out["county"]:
                continue
            rec = acs_record(r.to_dict()); rec["name"] = names.get(gid, ""); rec["acs"] = tag
            out["county"][code] = rec; n += 1
        out["src"]["county5"] = tag
        log("   5-year counties added:", n)
        break
    log("   us", bool(out["us"]), "states", len(out["state"]), "counties", len(out["county"]), "places", len(out["place"]), out["src"])
    return out

# ---------------------------------------------------------------- assemble
def main():
    t0 = time.time()
    fedS = national()
    F, S = fedS if fedS else (PREV_CORE.get("fed", {}), {})
    FS = fhfa_state() or {}
    FC = fhfa_county() or {}
    W = qcew()
    Z = zhvi() or {"state": {}, "county": {}, "city": {}, "us": None}
    C = census() or {"us": None, "state": {}, "county": {}, "place": {}, "src": {}}

    prev_states = {s["f"]: s for s in PREV_CORE.get("states", [])}

    # national
    us = dict(PREV_CORE.get("us", {}))
    if C.get("us"):
        us.update(C["us"]); us["acs"] = C["src"].get("us")
    if "USSTHPI" in S:
        us["hpi"] = hpi_stats_q(qavg(S["USSTHPI"]))
        us["hpi"]["src"] = "FHFA U.S. all-transactions index"
    p = pay_stats(W, "US000")
    if p:
        us["pay"] = p
    if Z.get("us"):
        us["val"], us["valDate"] = rnd(Z["us"][0], 0), Z["us"][1]
    if "CPIAUCSL" in S and W:
        cq = qavg(S["CPIAUCSL"]); e = W["end"]
        us["cpiT"] = {"g1": rnd(trend_q(cq, e, 1)), "g5": rnd(trend_q(cq, e, 5)), "g10": rnd(trend_q(cq, e, 10)),
                      "glr": rnd(trend_q(cq, e, e[0] - 1990)), "c19": rnd(cq.get((2019, e[1])), 3), "c0": rnd(cq.get(e), 3),
                      "sig": F.get("since1979", {}).get("sigReal") or 0.015, "end": f"{e[0]} Q{e[1]}"}
    us["n"] = "United States"

    states = []
    for f, a in FIPS.items():
        name = NAMES[a]
        rec = dict(prev_states.get(f, {}))
        rec.update({"f": f, "a": a, "n": name})
        if f in C.get("state", {}):
            rec.update(C["state"][f]); rec["acs"] = C["src"].get("state")
        if a in FS:
            rec["hpi"] = hpi_stats_q(FS[a]); rec["hpi"]["src"] = "FHFA state all-transactions index"
        p = pay_stats(W, f + "000")
        if p:
            rec["pay"] = p
        if name in Z.get("state", {}):
            rec["val"], rec["valDate"] = rnd(Z["state"][name][0], 0), Z["state"][name][1]
        states.append(rec)

    counties = []
    keys = set(C.get("county", {})) | set(PREV_CTY)
    for f in sorted(keys):
        if f[:2] not in FIPS:
            continue
        rec = dict(PREV_CTY.get(f, {}))
        rec["f"] = f; rec["s"] = f[:2]
        if f in C.get("county", {}):
            c = C["county"][f]; rec.update({k: v for k, v in c.items() if k != "name"})
            rec["n"] = c["name"].split(",")[0]
        if not rec.get("n"):
            rec["n"] = Z.get("cnameRev", {}).get(f, "")
        if f in FC:
            rec["hpi"] = hpi_stats_y(FC[f]); rec["hpi"]["src"] = "FHFA county index (annual)"
        p = pay_stats(W, f)
        if p:
            rec["pay"] = p
        if f in Z.get("county", {}):
            rec["val"], rec["valDate"] = rnd(Z["county"][f][0], 0), Z["county"][f][1]
        counties.append(rec)

    places = []
    keys = set(C.get("place", {})) | set(PREV_PLC)
    for f in sorted(keys):
        if f[:2] not in FIPS:
            continue
        rec = dict(PREV_PLC.get(f, {}))
        rec["f"] = f; rec["s"] = f[:2]
        if f in C.get("place", {}):
            c = C["place"][f]; rec.update({k: v for k, v in c.items() if k != "name"})
            rec["n"] = c["name"].split(",")[0]
        nm = rec.get("n", "")
        for suf in (" city and borough", " consolidated government (balance)", " metropolitan government (balance)", " unified government (balance)",
                    " city (balance)", " (balance)", " municipality", " borough", " city", " town", " village", " CDP", " urban county"):
            if nm.endswith(suf):
                nm = nm[: -len(suf)]
                break
        z = Z.get("city", {}).get((nm.lower(), FIPS[f[:2]]))
        if z:
            rec["val"], rec["valDate"] = rnd(z[0], 0), z[1]
            cf = Z.get("cname", {}).get((z[2].lower(), f[:2]))
            if cf:
                rec["c"] = cf
        places.append(rec)

    core = {"built": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "fed": F, "us": us, "states": states,
            "status": STATUS, "acs": C.get("src", {}), "qcewEnd": (f"{W['end'][0]} Q{W['end'][1]}" if W else PREV_CORE.get("qcewEnd"))}
    json.dump(core, open(os.path.join(OUT, "core.json"), "w"), separators=(",", ":"))
    json.dump(counties, open(os.path.join(OUT, "counties.json"), "w"), separators=(",", ":"))
    json.dump(places, open(os.path.join(OUT, "places.json"), "w"), separators=(",", ":"))
    log(f"wrote core ({len(states)} states), {len(counties)} counties, {len(places)} places in {time.time()-t0:.0f}s")
    log("status", json.dumps(STATUS))

try:
    main()
except Exception:
    log("FATAL", traceback.format_exc())
finally:
    open(os.path.join(OUT, "build_log.txt"), "w").write("\n".join(LOG) + "\n")
