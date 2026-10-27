"""Step 3. All statistics. Writes data/*.csv, data/results.json and data/page_data.json.

(1) Mints by reign: records, single finds and distinct moneyers per mint per reign period (973 to 1154),
    counting only records whose mint label is a single certain mint in England or Wales.
(2) Circulation: EMC single finds of those coins with a placed findspot: distance from mint to findspot,
    and whether the coin's mint is the nearest mint active in that reign (observed), against the share
    expected if every find were a random draw from the national output (each mint's share of moneyers).
(3) Destiny: each mint town against Domesday (Hull Domesday Project data via Domesday Destiny),
    Russell's 1086 estimates, the 1377 poll tax and the 1801 census (Wikipedia list of towns by
    historical population, which gives the 40 largest in 1377 and the 30 largest in 1801), Census 2021
    population (built-up area, LSOA best fit; civil parish for villages without one) and ONS mean
    household income FYE2023 (MSOA, population weighted).
Run: python3 03_analysis.py
"""
import json, math, os, re, collections
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
HIST = os.path.join(ROOT, ".."); D8 = os.path.join(HIST, "_data8")
import importlib.util
spec = importlib.util.spec_from_file_location("c1", os.path.join(HERE, "01_coins.py")); c1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c1)
PERIODS = c1.PERIODS; MAIN7 = c1.MAIN7; PK = [p[0] for p in PERIODS]; PLAB = {p[0]: p[1] for p in PERIODS}
LATE_AS = PK[:8]; NORMAN = PK[8:]
R = {}


def hav(lat1, lon1, lat2, lon2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def rnd(x, k=4):
    if isinstance(x, (np.floating, float)): return None if math.isnan(x) else round(float(x), k)
    if isinstance(x, (np.integer,)): return int(x)
    return x


coins = pd.read_pickle(os.path.join(ROOT, "work", "coins.pkl"))
MP = pd.read_csv(os.path.join(ROOT, "work", "mint_points.csv"))
F = pd.read_pickle(os.path.join(ROOT, "work", "findspots.pkl")).set_index("findspot")

# == counts and data handling ==
win = coins[coins.period.notna()]
EW = coins.country.isin(["England", "Wales"])
cert = coins[(coins.mint_class == "certain") & EW & coins.period.notna()].copy()
R["counts"] = dict(
    rows_scraped=71759, records_unique=len(coins), duplicates=71759 - len(coins), mint_values_searched=353,
    scbi=int((coins.source == "SCBI").sum()), emc=int((coins.source == "EMC").sum()),
    window_records=len(win), window_certain_ew=len(cert),
    window_share_certain=len(cert) / len(win),
    window_uncertain=int((win.mint_class == "uncertain").sum()), window_probable=int((win.mint_class == "probable").sum()),
    window_ambiguous=int((win.mint_class == "ambiguous").sum()), window_copy=int((win.mint_class == "copy").sum()),
    window_other=int(win.mint_class.isin(["regional", "unidentified", "foreign"]).sum()),
    ambiguous_all=int((coins.mint_class == "ambiguous").sum()), ambiguous_labels=int(coins[coins.mint_class == "ambiguous"].Mint.nunique()),
    window_scbi=int((cert.source == "SCBI").sum()), window_emc=int((cert.source == "EMC").sum()),
    mints_ew_any=int(cert.mint.nunique()),
    moneyer_named_share=float(cert.moneyer_norm.notna().mean()),
)
amb = coins[coins.mint_class == "ambiguous"].groupby(["Mint", "candidates"]).agg(records=("id", "size"), in_window=("period", lambda s: s.notna().sum())).reset_index()
amb.rename(columns={"Mint": "label"}).sort_values("records", ascending=False).to_csv(os.path.join(ROOT, "data", "ambiguous_mints.csv"), index=False)

# == (1) mint x reign ==
g = cert.groupby(["mint", "period"])
MR = g.agg(records=("id", "size"), scbi=("source", lambda s: (s == "SCBI").sum()), emc=("source", lambda s: (s == "EMC").sum()),
           moneyers=("moneyer_norm", lambda s: s.dropna().nunique())).reset_index()
MR["period_order"] = MR.period.map({k: i for i, k in enumerate(PK)})
MR = MR.sort_values(["period_order", "moneyers", "records"], ascending=[True, False, False])
MR["period_label"] = MR.period.map(PLAB)
MR[["mint", "period", "period_label", "records", "scbi", "emc", "moneyers"]].to_csv(os.path.join(ROOT, "data", "mint_reign.csv"), index=False)
# probable labels as a sensitivity: mints active if "York?" etc. are allowed
prob = coins[(coins.mint_class.isin(["certain", "probable"])) & EW & coins.period.notna()]
per = []
for k, lab, a, b in PERIODS:
    m = MR[MR.period == k]
    tot_m = m.moneyers.sum()
    top = m.sort_values(["moneyers", "records"], ascending=False).head(5)
    per.append(dict(key=k, label=lab, start=a, end=b, years=max(b - a, 1), mints=int(len(m)), records=int(m.records.sum()), emc=int(m.emc.sum()),
                    moneyers=int(tot_m), mints_with_probable=int(prob[prob.period == k].mint.nunique()),
                    mints_3plus_records=int((m.records >= 3).sum()),
                    top=[[r.mint, int(r.moneyers), int(r.records)] for r in top.itertuples()],
                    london_share_moneyers=float(m[m.mint == "London"].moneyers.sum() / tot_m) if tot_m else None,
                    top4_share_moneyers=float(m.sort_values("moneyers", ascending=False).moneyers.head(4).sum() / tot_m) if tot_m else None))
R["periods"] = per
P = {p["key"]: p for p in per}
R["mints_per_reign"] = {p["key"]: p["mints"] for p in per}
R["peak_period"] = max(per, key=lambda p: p["mints"])["key"]
# moneyers ranking c. 1000 (Aethelred II) and across the whole window
ae = MR[MR.period == "aethelred"].sort_values(["moneyers", "records"], ascending=False)
R["aethelred_rank"] = [[r.mint, int(r.moneyers), int(r.records)] for r in ae.itertuples()]
allm = cert.groupby("mint").agg(records=("id", "size"), emc=("source", lambda s: (s == "EMC").sum()),
                                moneyers_all=("moneyer_norm", lambda s: s.dropna().nunique()),
                                periods=("period", "nunique")).reset_index()
R["n_mints_aethelred"] = int(len(ae))
R["london_york_lincoln_share_aethelred"] = float(ae[ae.mint.isin(["London", "York", "Lincoln"])].moneyers.sum() / ae.moneyers.sum())
R["one_moneyer_mints_aethelred"] = int((ae.moneyers <= 1).sum())

# == (2) circulation ==
pts = MP.set_index("mint")
E = cert[cert.source == "EMC"].copy()
E["flat"] = E.Findspot.fillna("").map(F.lat); E["flon"] = E.Findspot.fillna("").map(F.lon); E["fmethod"] = E.Findspot.fillna("").map(F.method)
E["mlat"] = E.mint.map(pts.lat); E["mlon"] = E.mint.map(pts.lon)
L = E[E.flat.notna() & E.mlat.notna()].copy()
L["km"] = hav(L.mlat.values, L.mlon.values, L.flat.values, L.flon.values)
# nearest active mint test (active = at least one certain record in that period; output share = moneyers)
mon = MR.set_index(["period", "mint"]).moneyers
near_ok, exp = [], []
for r in L.itertuples():
    act = MR[(MR.period == r.period) & MR.mint.isin(pts.index[pts.lat.notna()])]
    la = act.mint.map(pts.lat).values; lo = act.mint.map(pts.lon).values
    d = hav(r.flat, r.flon, la, lo); j = int(np.argmin(d)); nm = act.mint.values[j]
    near_ok.append(nm == r.mint)
    w = act.moneyers.values.astype(float); w = np.where(w > 0, w, 0.5)
    exp.append(w[j] / w.sum())
L["own_is_nearest"] = near_ok; L["expected_nearest"] = exp
L["era"] = np.where(L.period.isin(LATE_AS), "late_as", "norman")


def circ(df):
    if not len(df): return None
    return dict(n=int(len(df)), median_km=float(df.km.median()), mean_km=float(df.km.mean()), within25=float((df.km <= 25).mean()),
                within50=float((df.km <= 50).mean()), beyond100=float((df.km > 100).mean()), beyond200=float((df.km > 200).mean()),
                nearest_obs=float(df.own_is_nearest.mean()), nearest_exp=float(df.expected_nearest.mean()),
                nearest_ratio=float(df.own_is_nearest.mean() / df.expected_nearest.mean()))


R["circulation"] = dict(all=circ(L), late_as=circ(L[L.era == "late_as"]), norman=circ(L[L.era == "norman"]),
                        by_period={k: circ(L[L.period == k]) for k in PK if (L.period == k).sum() >= 30},
                        emc_records_in_window=int(len(E)), emc_placed=int(len(L)), emc_placed_share=float(len(L) / len(E)),
                        london=circ(L[L.mint == "London"]), york=circ(L[L.mint == "York"]),
                        not_london=circ(L[L.mint != "London"]))
# distance bands for a chart
bands = [0, 10, 25, 50, 100, 150, 200, 300, 1000]
R["circulation"]["bands"] = [dict(lo=a, hi=b, share=float(((L.km > a) & (L.km <= b)).mean()) if a else float((L.km <= b).mean())) for a, b in zip(bands[:-1], bands[1:])]
# Monte Carlo baseline: findspots fixed, mint drawn from the period's national output (moneyer shares)
rng = np.random.default_rng(1)
sim_med = []
act_by = {k: MR[(MR.period == k) & MR.mint.isin(pts.index[pts.lat.notna()])] for k in PK}
for _ in range(200):
    ds = []
    for k, grp in L.groupby("period"):
        a = act_by[k]; w = a.moneyers.values.astype(float); w = np.where(w > 0, w, .5); w /= w.sum()
        pick = rng.choice(len(a), size=len(grp), p=w)
        ds.append(hav(grp.flat.values, grp.flon.values, a.mint.map(pts.lat).values[pick], a.mint.map(pts.lon).values[pick]))
    sim_med.append(np.median(np.concatenate(ds)))
R["circulation"]["random_mint_median_km"] = float(np.mean(sim_med))
pm = L.groupby("mint").agg(n=("km", "size"), median_km=("km", "median"), within50=("km", lambda s: (s <= 50).mean()), nearest=("own_is_nearest", "mean")).reset_index()
pm = pm[pm.n >= 20].sort_values("median_km")
R["circulation"]["per_mint"] = [[r.mint, int(r.n), float(r.median_km), float(r.within50), float(r.nearest)] for r in pm.itertuples()]
R["circulation"]["method_counts"] = L.fmethod.str.replace(r" \(\d+ places\)", "", regex=True).value_counts().to_dict()
R["circulation"]["placed_findspots"] = int(L.Findspot.nunique())

# == (3) destiny ==
W = json.load(open(os.path.join(HIST, "_data9", "wikipedia_wikitext.json")))["List of towns and cities in England by historical population"]["text"]


def table(caption_start):
    i = W.find("|+ " + caption_start); j = W.find("|}", i)
    out = {}
    for line in W[i:j].splitlines():
        m = re.match(r"^\|(?:rowspan=\d+\|)?(?:\d+)?\|\|\[\[(?:[^|\]]+\|)?([^\]]+)\]\][^|]*\|\|\s*([~\d,]*)", line) or re.match(r"^\|\[\[(?:[^|\]]+\|)?([^\]]+)\]\]\|\|([\d,]+)", line)
        if m:
            name = m.group(1).strip(); v = m.group(2).replace(",", "").replace("~", "").strip()
            out[name] = int(v) if v else None
    return out


T1086 = table("Estimates of town populations in 1086"); T1377 = table("1377"); T1801 = table("1801")
# rank by order of appearance
def ranks(t): return {k: i + 1 for i, k in enumerate(t)}
K1377, K1801 = ranks(T1377), ranks(T1801)
WIKI_NAME = {"Lynn": "King's Lynn", "Newcastle": "Newcastle", "Newark": "Newark-on-Trent"}
print("parsed", len(T1086), len(T1377), len(T1801))

# Census 2021 by BUA (LSOA best fit)
lk = pd.DataFrame(json.load(open(os.path.join(D8, "lsoa21_bua22_lookup.json"))))
c21 = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-lsoa.csv")); c21.columns = ["date", "name", "code", "pop", "hh", "ce"]
lk = lk.merge(c21[["code", "pop"]], left_on="LSOA21CD", right_on="code")
lk["london"] = lk.LAD22CD.str.startswith("E09")
BP = lk.groupby(["BUA22CD", "BUA22NM"]).agg(pop=("pop", "sum"), london=("london", "max")).reset_index()
geo = json.load(open(os.path.join(D8, "ons_geo.json")))
BG = pd.DataFrame(geo["bua22_gb"])[["BUA22CD", "BUA22NM", "LAT", "LONG"]]
BP = BP.merge(BG[["BUA22CD", "LAT", "LONG"]], on="BUA22CD", how="left")
LONDON_POP = int(pd.read_csv(os.path.join(D8, "census", "census2021-ts001-rgn.csv")).set_index("geography").loc["London"].iloc[2])
# income
inc = pd.read_excel(os.path.join(D8, "ons_msoa_income_fye2023.xlsx"), sheet_name="Total annual income", header=3)
inc = inc.rename(columns={"MSOA code": "MSOA21CD", "Total annual income (£)": "income"})
mpop = pd.read_csv(os.path.join(D8, "census", "census2021-ts001-msoa.csv")); mpop.columns = ["date", "name", "MSOA21CD", "pop", "hh", "ce"]
mlk = pd.DataFrame(geo["msoa21_bua22_lookup"])[["MSOA21CD", "BUA22CD", "RGN22NM"]]
pwc = pd.DataFrame(geo["msoa21_pwc"])[["MSOA21CD", "_x", "_y"]]
MI = inc[["MSOA21CD", "income"]].merge(mpop[["MSOA21CD", "pop"]], on="MSOA21CD").merge(mlk, on="MSOA21CD").merge(pwc, on="MSOA21CD")
ENG_MEDIAN_MSOA_INCOME = float(MI[MI.MSOA21CD.str.startswith("E")].income.median())

# Domesday (via Domesday Destiny)
DP = pd.read_csv(os.path.join(HIST, "domesday-destiny", "data", "domesday_places.csv"))
DP["clean"] = DP.name.fillna("").str.replace(r"[\[\]{}`']", "", regex=True).str.strip()

BUA_NAME = {"London": None, "Lynn": "King's Lynn", "Newcastle": "Newcastle upon Tyne", "Cadbury": "South Cadbury",
            "Bedwyn": "Great Bedwyn", "Romney": "New Romney", "Petherton": "North Petherton", "Milbourne Port": "Milborne Port",
            "Newark": "Newark-on-Trent", "Droitwich": "Droitwich Spa", "Cissbury": None}

rows = []
for m in pts.index:
    p = pts.loc[m]
    r = dict(mint=m, lat=p.lat, lon=p.lon, country=p.country, place_today=p.os_name if isinstance(p.os_name, str) else "")
    sub = MR[MR.mint == m].set_index("period")
    for k in PK:
        r["moneyers_" + k] = int(sub.moneyers.get(k, 0)); r["records_" + k] = int(sub.records.get(k, 0))
    a = allm.set_index("mint")
    r["records_total"] = int(a.records.get(m, 0)); r["emc_total"] = int(a.emc.get(m, 0))
    r["periods_active"] = int((sub.records > 0).sum()) if len(sub) else 0
    r["moneyers_peak"] = int(sub.moneyers.max()) if len(sub) else 0
    r["moneyers_late_as"] = int(cert[(cert.mint == m) & cert.period.isin(LATE_AS)].moneyer_norm.dropna().nunique())
    act = [k for k in PK if r["records_" + k] > 0]
    r["first_period"] = act[0] if act else ""; r["last_period"] = act[-1] if act else ""
    # Domesday
    dd = None
    if pd.notna(p.lat):
        d = DP[DP.lat.notna()].copy(); d["km"] = hav(p.lat, p.lon, d.lat.values, d.lng.values)
        nm_ = {m.lower(), (r["place_today"] or m).lower()}
        c = d[(d.km <= 4)]
        ex = c[c.clean.str.lower().isin(nm_) | c.clean.str.lower().str.replace(" ", "").isin({x.replace(" ", "") for x in nm_})]
        if not len(ex):
            ex = c[c.clean.str.lower().str.contains(m.lower(), regex=False)]
        if len(ex): dd = ex.sort_values("households1086", ascending=False).iloc[0]
    if dd is None:
        c = DP[DP.clean.str.lower().str.contains(m.lower()) & DP.lat.isna()]
        if len(c) == 1: dd = c.iloc[0]
    r["domesday_place"] = dd["name"] if dd is not None else ""
    r["domesday_county"] = dd["countyName"] if dd is not None else ""
    r["households1086"] = dd["households1086"] if dd is not None else None
    r["burgesses1086"] = dd["burgesses1086"] if dd is not None else None
    wn = WIKI_NAME.get(m, m)
    r["pop1086_russell"] = T1086.get(wn)
    r["pop1377"] = T1377.get(wn); r["rank1377"] = K1377.get(wn)
    r["pop1801"] = T1801.get(wn); r["rank1801"] = K1801.get(wn)
    # 2021
    bn = BUA_NAME.get(m, r["place_today"] or m)
    pop, src, bcd = None, "", None
    if m == "London":
        pop, src = LONDON_POP, "Census 2021, London region (Greater London)"
    elif bn and pd.notna(p.lat):
        c = BP[(BP.BUA22NM == bn) | BP.BUA22NM.str.startswith(bn + " (")].copy()
        if len(c):
            c["km"] = hav(p.lat, p.lon, c.LAT.values, c.LONG.values); c = c[c.km <= 8].sort_values("km")
            if len(c):
                pop, src, bcd = int(c.iloc[0]["pop"]), "Census 2021, built-up area " + c.iloc[0].BUA22NM + " (LSOA best fit)", c.iloc[0].BUA22CD
    if pop is None and dd is not None and pd.notna(dd.get("parishResidents2021")) and "unparished" not in str(dd.parishName):
        pop, src = int(dd["parishResidents2021"]), "Census 2021, civil parish of " + str(dd.parishName) + " (no built-up area)"
    if m == "Cissbury":
        src = "hillfort, no settlement"
    r["pop2021"] = pop; r["pop2021_source"] = src
    # income
    if m == "London":
        q = MI[MI.RGN22NM == "London"]
    elif bcd is not None and (MI.BUA22CD == bcd).any():
        q = MI[MI.BUA22CD == bcd]
    elif pd.notna(p.lat):
        dd2 = hav(p.lat, p.lon, MI._y.values, MI._x.values); q = MI.iloc[[int(np.argmin(dd2))]]
    else:
        q = MI.iloc[0:0]
    r["income_fye2023"] = float(np.average(q.income, weights=q["pop"])) if len(q) else None
    r["income_msoas"] = int(len(q))
    rows.append(r)
T = pd.DataFrame(rows)
T = T[T.records_total > 0].copy()  # Horndon is kept separately
T["rank_aethelred"] = T.moneyers_aethelred.where(T.moneyers_aethelred > 0).rank(ascending=False, method="min")
T["rank2021"] = T.pop2021.rank(ascending=False, method="min")
T.sort_values(["moneyers_aethelred", "moneyers_peak"], ascending=False).to_csv(os.path.join(ROOT, "data", "mint_towns.csv"), index=False)

# placed mints table for publication
MP2 = MP.copy()
MP2["records_973_1154"] = MP2.mint.map(allm.set_index("mint").records).fillna(0).astype(int)
MP2["labels"] = MP2.mint.map(lambda m: "; ".join(sorted(coins[(coins.mint == m) & EW].Mint.unique())))
MP2.to_csv(os.path.join(ROOT, "data", "mints.csv"), index=False)

# == destiny statistics ==
A = T[T.moneyers_aethelred > 0].copy()
ok = A[A.pop2021.notna()]
rho, pv = stats.spearmanr(ok.moneyers_aethelred, ok.pop2021)
pk = T[(T.moneyers_peak > 0) & T.pop2021.notna()]
rho2, pv2 = stats.spearmanr(pk.moneyers_late_as, pk.pop2021)
# 1377: towns outside the top 40 tied at the bottom
A["p1377"] = A.pop1377.fillna(0)
rho3, pv3 = stats.spearmanr(A.moneyers_aethelred, A.p1377)
A["p1801"] = A.pop1801.fillna(0)
rho4, pv4 = stats.spearmanr(A.moneyers_aethelred, A.p1801)
top10 = A.sort_values(["moneyers_aethelred", "records_aethelred"], ascending=False).head(10)
top20 = A.sort_values(["moneyers_aethelred", "records_aethelred"], ascending=False).head(20)
mint_set = set(T.mint) | {"King's Lynn", "Newcastle", "Newark-on-Trent"}
wiki2mint = {"King's Lynn": "Lynn", "Newcastle": "Newcastle", "Newark-on-Trent": "Newark"}
in1377 = [n for n in T1377 if wiki2mint.get(n, n) in set(T.mint)]
in1801 = [n for n in T1801 if wiki2mint.get(n, n) in set(T.mint)]
in1086 = [n for n in T1086 if n in set(T.mint)]
# top English built-up areas 2021 (London boroughs merged into London)
BPx = BP[BP.BUA22CD.str.startswith("E") & ~BP.london].sort_values("pop", ascending=False)
top_bua = [["London", LONDON_POP]] + [[re.sub(r" \(.*\)$", "", r.BUA22NM), int(r.pop)] for r in BPx.head(29).itertuples()]
top_bua = sorted(top_bua, key=lambda x: -x[1])[:30]
eng_pops = np.array(sorted([LONDON_POP] + [int(p) for p in BPx["pop"]], reverse=True))
T["rank2021_england"] = [int((eng_pops > p).sum() + 1) if pd.notna(p) and not str(T.loc[i, "pop2021_source"]).startswith("Census 2021, civil parish") and T.loc[i, "country"] == "England" else None for i, p in zip(T.index, T.pop2021)]
T.sort_values(["moneyers_aethelred", "moneyers_peak"], ascending=False).to_csv(os.path.join(ROOT, "data", "mint_towns.csv"), index=False)
top10 = A.sort_values(["moneyers_aethelred", "records_aethelred"], ascending=False).head(10).merge(T[["mint", "rank2021_england"]], on="mint")
bua_mint_names = set(T.place_today) | set(T.mint)
top30_2021_mints = [n for n, _ in top_bua if n in bua_mint_names]
vanished = T[(T.pop2021.fillna(0) < 5000)].sort_values("moneyers_peak", ascending=False)
grew = T[(T.moneyers_peak <= 3) & (T.pop2021 >= 100000)].sort_values("pop2021", ascending=False)
R["destiny"] = dict(
    n_towns=int(len(T)), n_aethelred=int(len(A)), n_with_pop2021=int(T.pop2021.notna().sum()),
    spearman_aethelred_2021=float(rho), p_aethelred_2021=float(pv), n_aethelred_2021=int(len(ok)),
    spearman_lateas_2021=float(rho2), p_lateas_2021=float(pv2), n_lateas_2021=int(len(pk)),
    spearman_aethelred_1377=float(rho3), p_aethelred_1377=float(pv3), spearman_aethelred_1801=float(rho4), p_aethelred_1801=float(pv4),
    top10=[dict(mint=r.mint, moneyers=int(r.moneyers_aethelred), rank1377=rnd(r.rank1377), rank1801=rnd(r.rank1801), pop2021=rnd(r.pop2021),
                rank2021=rnd(r.rank2021), rank2021_england=rnd(r.rank2021_england)) for r in top10.itertuples()],
    top10_in1377=int(top10.rank1377.notna().sum()), top10_in1801=int(top10.rank1801.notna().sum()),
    top10_over100k_2021=int((top10.pop2021 >= 100000).sum()),
    top20_in1377=int(top20.rank1377.notna().sum()), top20_in1801=int(top20.rank1801.notna().sum()),
    top20_over100k_2021=int((top20.pop2021 >= 100000).sum()),
    list1377_n=len(T1377), list1377_mints=len(in1377), list1377_not_mints=[n for n in T1377 if n not in in1377],
    list1801_n=len(T1801), list1801_mints=len(in1801), list1801_not_mints=[n for n in T1801 if n not in in1801],
    list1086_n=len(T1086), list1086_mints=len(in1086),
    top30_2021=top_bua, top30_2021_mints=len(top30_2021_mints), top30_2021_not_mints=[n for n, _ in top_bua if n not in bua_mint_names],
    vanished=[dict(mint=r.mint, moneyers_peak=int(r.moneyers_peak), moneyers_late_as=int(r.moneyers_late_as), records=int(r.records_total),
                   last=PLAB.get(r.last_period, ""), first=PLAB.get(r.first_period, ""), pop2021=rnd(r.pop2021), src=r.pop2021_source,
                   households1086=rnd(r.households1086), burgesses1086=rnd(r.burgesses1086)) for r in vanished.itertuples()],
    n_vanished=int(len(vanished)), n_grew=int(len(grew)),
    grew=[dict(mint=r.mint, moneyers_peak=int(r.moneyers_peak), pop2021=int(r.pop2021), first=PLAB.get(r.first_period, "")) for r in grew.itertuples()],
    london_pop2021=LONDON_POP, england_median_msoa_income=ENG_MEDIAN_MSOA_INCOME,
    domesday_matched=int((T.domesday_place != "").sum()), burgesses_recorded=int((T.burgesses1086 > 0).sum()),
)
# income by mint size class
T["size_class"] = pd.cut(T.moneyers_late_as, [-1, 2, 9, 1000], labels=["small", "middling", "large"])
R["destiny"]["income_by_class"] = {str(k): dict(n=int(len(v)), median_income=float(v.income_fye2023.median()), median_pop=float(v.pop2021.median()))
                                   for k, v in T.groupby("size_class", observed=True)}
R["destiny"]["size_class_rule"] = "late Anglo-Saxon moneyers (973 to 1066): small 0 to 2, middling 3 to 9, large 10 or more"
rho5, pv5 = stats.spearmanr(T.dropna(subset=["income_fye2023"]).moneyers_late_as, T.dropna(subset=["income_fye2023"]).income_fye2023)
R["destiny"]["spearman_lateas_income"] = float(rho5); R["destiny"]["p_lateas_income"] = float(pv5)

# named towns for the text
def town(m):
    r = T[T.mint == m]
    if not len(r): return None
    r = r.iloc[0]
    return {k: rnd(r[k]) for k in ["moneyers_aethelred", "moneyers_peak", "moneyers_late_as", "records_total", "emc_total", "pop2021", "rank1377", "pop1377",
                                   "rank1801", "pop1801", "pop1086_russell", "households1086", "burgesses1086", "income_fye2023", "periods_active", "rank_aethelred"]} | {
        "pop2021_source": r.pop2021_source, "first": PLAB.get(r.first_period, ""), "last": PLAB.get(r.last_period, "")}
R["towns"] = {m: town(m) for m in ["London", "York", "Lincoln", "Winchester", "Stamford", "Thetford", "Chester", "Norwich", "Exeter", "Canterbury",
                                    "Lydford", "Cadbury", "Bedwyn", "Ilchester", "Wilton", "Torksey", "Dunwich", "Cricklade", "Bristol", "Reading",
                                    "Cissbury", "Southampton", "Newcastle", "Wallingford", "Oxford", "Ipswich", "Watchet", "Axbridge", "Milbourne Port", "Langport", "Lympne", "Castle Rising", "Peterborough", "Cardiff", "Swansea", "Durham", "Pevensey"]}
R["horndon"] = dict(records=0, place="Horndon on the Hill", note="known from one coin of Edward the Confessor (Wikipedia, Horndon mint)")
R["wiki_context"] = dict(reform_mints_about=40, harold2_mints=48, places_active_about=70)
R["coverage"] = dict(emc_findspot_placed_all=float(E.flat.notna().mean()))
R["probable_window_by_mint_top"] = coins[(coins.mint_class == "probable") & coins.period.notna()].mint.value_counts().head(5).to_dict()

# == page data ==
mints_page = []
for r in T.sort_values("mint").itertuples():
    mints_page.append(dict(m=r.mint, la=rnd(r.lat, 4), lo=rnd(r.lon, 4), mon=[int(getattr(r, "moneyers_" + k)) for k in PK],
                           rec=[int(getattr(r, "records_" + k)) for k in PK], p21=rnd(r.pop2021), r1377=rnd(r.rank1377), r1801=rnd(r.rank1801),
                           p1377=rnd(r.pop1377), p1801=rnd(r.pop1801), r1086=rnd(r.pop1086_russell), hh=rnd(r.households1086), bu=rnd(r.burgesses1086),
                           inc=rnd(r.income_fye2023, 0), today=r.place_today, src=r.pop2021_source, emc=int(r.emc_total), dp=r.domesday_place,
                           ml=int(r.moneyers_late_as)))
midx = {d["m"]: i for i, d in enumerate(mints_page)}
finds = [[midx[r.mint], PK.index(r.period), round(r.flat, 3), round(r.flon, 3), round(r.km, 1)] for r in L.itertuples() if r.mint in midx]
PD = dict(periods=[[k, l, a, b] for k, l, a, b in PERIODS], main7=MAIN7, mints=mints_page, finds=finds,
          horndon=[51.52372, 0.40587])
json.dump(PD, open(os.path.join(ROOT, "data", "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# record index: ids, urls and derived fields only (no descriptive text)
RI = coins[coins.period.notna() | (EW & coins.mint_class.isin(["certain", "probable"]))][["id", "url", "source", "mint_class", "mint", "country", "period"]].copy()
RI = RI.merge(L[["id", "flat", "flon", "km", "own_is_nearest"]], on="id", how="left")
RI["flat"] = RI.flat.round(2); RI["flon"] = RI.flon.round(2); RI["km"] = RI.km.round(1)
RI = RI.rename(columns={"flat": "findspot_lat_2dp", "flon": "findspot_lon_2dp", "km": "mint_to_findspot_km", "id": "emc_scbi_number"})
RI.to_csv(os.path.join(ROOT, "data", "records_index.csv"), index=False)
R["counts"]["records_index_rows"] = int(len(RI))
R["counts"]["wikidata_matched"] = int(MP.wikidata_offset_km.notna().sum()); R["counts"]["wikidata_max_offset_km"] = float(MP.wikidata_offset_km.max())
R["counts"]["mints_placed"] = int(MP.lat.notna().sum())


def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    return rnd(o, 6) if isinstance(o, (float, np.floating, np.integer)) else o


json.dump(clean(R), open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(clean({k: R[k] for k in ["counts", "mints_per_reign", "circulation"]}), ensure_ascii=False)[:5000])
