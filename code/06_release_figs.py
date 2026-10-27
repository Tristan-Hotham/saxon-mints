"""Step 6. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png, 1520 px wide).
Maps are drawn from coordinates over the Natural Earth 1:10m land outline (no web tiles).
Run: python3 06_release_figs.py
"""
import json, math, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf"]:
    if os.path.exists(os.path.join(FD, f)): fm.fontManager.addfont(os.path.join(FD, f))
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 13, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#5D6270", "axes.labelcolor": "#1A1F2B", "xtick.color": "#3A3F4B", "ytick.color": "#3A3F4B"})
BG = "#ECEBE6"; FG = "#1A1F2B"; MUT = "#5D6270"; GOLD = "#A27718"; GOLDL = "#D9B65B"; BLUE = "#1F3B70"; MAD = "#A33A2A"; LAND = "#DAD8CF"; RULE = "#CFCDC4"
MONO = "IBM Plex Mono"
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
T = pd.read_csv(os.path.join(ROOT, "data", "mint_towns.csv"))
PK = [p[0] for p in P["periods"]]; PL = {p[0]: p[1] for p in P["periods"]}
PO = os.path.join(ROOT, "release", "paper"); BO = os.path.join(ROOT, "release", "blog")
os.makedirs(PO, exist_ok=True); os.makedirs(BO, exist_ok=True)
K = math.cos(math.radians(52.5))
LAND_POLYS = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LAND_POLYS.append(np.c_[a[:, 0] * K, a[:, 1]])


def basemap(ax, ext=(-6.0, 2.0, 49.9, 55.9)):
    for a in LAND_POLYS:
        ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#BDBBB2", lw=.5, zorder=0))
    ax.set_xlim(ext[0] * K, ext[1] * K); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def save(fig, name, blog):
    out = os.path.join(BO if blog else PO, name)
    if blog:
        if not fig.axes[0].get_position().x0 == 0: fig.tight_layout(pad=1.2)
        fig.savefig(out, dpi=160, facecolor=fig.get_facecolor())
    else:
        fig.savefig(out, dpi=200, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=.15)
    plt.close(fig)


M = pd.DataFrame(P["mints"])
F = pd.DataFrame(P["finds"], columns=["mi", "pi", "la", "lo", "km"])


def mint_map(ax, k, scale=2.3, finds=False, labels=True, fs=10):
    pi = PK.index(k)
    basemap(ax)
    if finds:
        f = F[F.pi.isin(range(len(PK)))]
        ax.scatter(f.lo * K, f.la, s=7, c=BLUE, alpha=.45, lw=0, zorder=1)
    act = M[[r[pi] > 0 for r in M.rec]].copy(); act["n"] = [r[pi] for r in act.mon]
    act = act[act.la.notna()].sort_values("n", ascending=False)
    ina = M[np.array([r[pi] == 0 for r in M.rec]) & M.la.notna().values]
    ax.scatter(ina.lo * K, ina.la, s=8, facecolors="none", edgecolors="#9A9DA5", lw=.6, zorder=2)
    ax.scatter(act.lo * K, act.la, s=(3 + np.sqrt(act.n) * scale) ** 2, c=GOLD, alpha=.88, edgecolors=FG, lw=.7, zorder=3)
    if labels:
        for r in act.head(6).itertuples():
            ax.annotate(r.m, (r.lo * K, r.la), xytext=(7 + math.sqrt(r.n) * scale * .5, 2), textcoords="offset points", fontsize=fs, family=MONO, color=FG, zorder=4)


# == 1. blog hero map: Aethelred II mints and all placed single finds ==
for blog in (True, False):
    fig = plt.figure(figsize=(9.5, 11) if blog else (7, 8.2), facecolor=BG if blog else "white")
    ax = fig.add_axes([0, 0, 1, 1]); mint_map(ax, "aethelred", scale=2.6, finds=True, fs=12 if blog else 9)
    for nm, (dx, dy, ha) in {"Lydford": (-8, -12, "right"), "Cadbury": (-4, -18, "right"), "Torksey": (-8, -12, "right"), "Wilton": (2, -22, "center"), "Ilchester": (-10, 8, "right")}.items():
        r = M[M.m == nm].iloc[0]
        ax.annotate(nm, (r.lo * K, r.la), xytext=(dx, dy), textcoords="offset points", fontsize=11 if blog else 8.5, family=MONO, color=MAD, ha=ha)
    hs = [plt.scatter([], [], s=(3 + math.sqrt(v) * 2.6) ** 2, c=GOLD, edgecolors=FG, lw=.7) for v in (1, 10, 50, 100)]
    lg = ax.legend(hs, ["1", "10", "50", "100"], title="Moneyers under Æthelred II", loc="upper right", frameon=False, labelspacing=1.4, borderpad=1.2,
                   prop={"family": MONO, "size": 11 if blog else 8}, title_fontproperties={"family": MONO, "size": 11 if blog else 8}, ncol=1)
    ax.scatter([], [], s=10, c=BLUE, alpha=.6, label="single find")
    ax.text(.98, .72, "Blue dots: placed single finds\n973 to 1154", transform=ax.transAxes, ha="right", family=MONO, fontsize=11 if blog else 8, color=BLUE)
    save(fig, "b_map.png" if blog else "f_map.png", blog)

# == 2. small multiples, main 7 reigns ==
for blog in (True, False):
    fig, axs = plt.subplots(2, 4, figsize=(9.5, 6.4) if blog else (11, 7.4), facecolor=BG if blog else "white")
    for ax, k in zip(axs.flat, P["main7"]):
        mint_map(ax, k, scale=1.9, labels=False)
        pr = [p for p in R["periods"] if p["key"] == k][0]
        ax.set_title(f"{PL[k]}\n{pr['start']} to {pr['end']} · {pr['mints']} mints", family=MONO, fontsize=9.5 if blog else 9, color=FG)
    axs.flat[-1].axis("off")
    hs = [axs.flat[-1].scatter([], [], s=(3 + math.sqrt(v) * 1.9) ** 2, c=GOLD, edgecolors=FG, lw=.7) for v in (1, 10, 50, 100)]
    axs.flat[-1].legend(hs, ["1", "10", "50", "100"], title="moneyers", loc="center", frameon=False, labelspacing=1.5,
                        prop={"family": MONO, "size": 11 if blog else 9}, title_fontproperties={"family": MONO, "size": 11 if blog else 9})
    fig.tight_layout()
    save(fig, "b_reigns_map.png" if blog else "f_reigns_map.png", blog)

# == 3. mints per reign ==
for blog in (True, False):
    fig, ax = plt.subplots(figsize=(9.5, 5.2) if blog else (7, 3.8), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    pr = R["periods"]; x = np.arange(len(pr))
    cols = [GOLD if p["key"] in P["main7"] else GOLDL for p in pr]
    ax.bar(x, [p["mints"] for p in pr], color=cols, edgecolor="none")
    for i, p in enumerate(pr): ax.text(i, p["mints"] + 1, str(p["mints"]), ha="center", family=MONO, fontsize=11 if blog else 8)
    ax.set_xticks(x); ax.set_xticklabels([p["label"] for p in pr], rotation=35, ha="right", rotation_mode="anchor", fontsize=11 if blog else 7.5, family=MONO)
    ax.set_ylabel("mints with surviving coins"); ax.set_ylim(0, 80); ax.grid(axis="y", color=RULE, lw=.6); ax.set_axisbelow(True)
    save(fig, "b_mints_per_reign.png" if blog else "f_mints_per_reign.png", blog)

# == 4. moneyer ranking, Aethelred II ==
for blog in (True, False):
    rk = R["aethelred_rank"][:20][::-1]
    fig, ax = plt.subplots(figsize=(9.5, 7.5) if blog else (6.5, 5.6), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    pop = T.set_index("mint").pop2021
    ax.barh([r[0] for r in rk], [r[1] for r in rk], color=[MAD if pop.get(r[0], 1e9) < 10000 else GOLD for r in rk])
    for i, r in enumerate(rk): ax.text(r[1] + 1, i, str(r[1]), va="center", family=MONO, fontsize=11 if blog else 8)
    ax.set_xlabel("distinct moneyers on coins of Æthelred II (978 to 1016)")
    ax.tick_params(axis="y", labelsize=12 if blog else 8.5); ax.grid(axis="x", color=RULE, lw=.6); ax.set_axisbelow(True)
    ax.text(.98, .08, "red: fewer than 10,000\nresidents in 2021", transform=ax.transAxes, ha="right", color=MAD, family=MONO, fontsize=11 if blog else 8)
    save(fig, "b_rank.png" if blog else "f_rank.png", blog)

# == 5. distance ==
for blog in (True, False):
    B = R["circulation"]["bands"]
    fig, ax = plt.subplots(figsize=(9.5, 5) if blog else (6.8, 3.6), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    x = np.arange(len(B)); ax.bar(x, [b["share"] * 100 for b in B], color=BLUE, width=.85)
    ax.set_xticks(x); ax.set_xticklabels([("300+" if b["hi"] == 1000 else f"{b['lo']} to {b['hi']}") for b in B], family=MONO, fontsize=10 if blog else 7)
    ax.set_xlabel("km from mint to findspot"); ax.set_ylabel("% of placed single finds"); ax.grid(axis="y", color=RULE, lw=.6); ax.set_axisbelow(True)
    edges = [0, 10, 25, 50, 100, 150, 200, 300, 600]
    def xat(km):
        for i in range(8):
            if km <= edges[i + 1]: return i - .5 + (km - edges[i]) / (edges[i + 1] - edges[i])
    for v, c, lab, yy in [(R["circulation"]["all"]["median_km"], GOLD, "median", 24), (R["circulation"]["random_mint_median_km"], MUT, "random mints", 21)]:
        ax.axvline(xat(v), color=c, lw=2, ls="solid" if c == GOLD else "dashed")
        ax.text(xat(v) + .07, yy, f"{lab} {v:.0f} km", color=c, family=MONO, fontsize=11 if blog else 8)
    ax.set_ylim(0, 26)
    save(fig, "b_distance.png" if blog else "f_distance.png", blog)

# == 6. then and now scatter ==
for blog in (True, False):
    S = T[T.pop2021.notna() & (T.pop2021 > 0)]
    fig, ax = plt.subplots(figsize=(9.5, 7.2) if blog else (6.8, 5.2), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    xs = np.log10(S.moneyers_late_as + 1); ys = S.pop2021
    c = [MAD if p < 5000 else BLUE for p in S.pop2021]
    rg = S.rank1377.notna().values
    ax.scatter(xs[rg], ys[rg], s=(46 if blog else 26) * 2.4, facecolors="none", edgecolors=GOLD, linewidths=2)
    ax.scatter(xs, ys, s=46 if blog else 26, c=c, alpha=.85, lw=0)
    ax.set_yscale("log"); ax.set_ylim(80, 2e7)
    ax.set_yticks([100, 1e3, 1e4, 1e5, 1e6, 1e7]); ax.set_yticklabels(["100", "1,000", "10,000", "100,000", "1 million", "10 million"])
    tk = [0, 1, 3, 10, 30, 100, 200]; ax.set_xticks(np.log10(np.array(tk) + 1)); ax.set_xticklabels(tk)
    ax.set_xlabel("distinct moneyers, 973 to 1066"); ax.set_ylabel("population, Census 2021")
    ax.grid(color=RULE, lw=.6); ax.set_axisbelow(True)
    lab = {"London": (-8, 0, "right"), "York": (8, 2, "left"), "Lincoln": (8, -10, "left"), "Winchester": (8, -2, "left"), "Stamford": (8, -8, "left"),
           "Thetford": (8, 4, "left"), "Wallingford": (8, -3, "left"), "Lydford": (8, -3, "left"), "Cadbury": (-8, -3, "right"), "Torksey": (8, -3, "left"),
           "Ilchester": (8, -3, "left"), "Wilton": (8, -3, "left"), "Bristol": (8, 2, "left"), "Reading": (8, 6, "left"), "Peterborough": (8, -10, "left"),
           "Newcastle": (8, 2, "left"), "Dunwich": (8, -3, "left"), "Norwich": (8, 2, "left")}
    for r in S.itertuples():
        if r.mint in lab:
            dx, dy, ha = lab[r.mint]
            ax.annotate(r.mint, (math.log10(r.moneyers_late_as + 1), r.pop2021), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", family=MONO, fontsize=10 if blog else 7)
    ax.text(.02, .97, f"Spearman (Æthelred II moneyers vs 2021) = {R['destiny']['spearman_aethelred_2021']:.2f}\ngold ring: among the largest towns in 1377\nred: fewer than 5,000 people today",
            transform=ax.transAxes, va="top", family=MONO, fontsize=10 if blog else 7, color=FG)
    save(fig, "b_scatter.png" if blog else "f_scatter.png", blog)
print("figures written")
