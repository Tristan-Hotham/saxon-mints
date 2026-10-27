"""r/dataisbeautiful collage for Minted (saxon-mints). Run from this folder: python3 collage.py
Every number is read from ../data/results.json, ../data/page_data.json or ../data/mint_towns.csv."""
import json, math, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, Circle

F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#E9E8E2"; FG = "#17213A"; MUT = "#5E6372"; LAND = "#D8D6CC"; GOLD = "#A9791A"; GOLDL = "#E2C676"; BLUE = "#1F3B70"; MAD = "#A33A2A"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
T = pd.read_csv(os.path.join(ROOT, "data", "mint_towns.csv")).set_index("mint")
K = math.cos(math.radians(52.5))
LANDP = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LANDP.append(np.c_[a[:, 0] * K, a[:, 1]])

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# == title ==
fig.text(0.04, 0.968, "Did England's money towns stay big?", fontproperties=DISP, fontsize=40, color=FG, va="top")
fig.text(0.04, 0.917, f"Around the year 1000 every English penny named the town that struck it. I mapped {R['counts']['window_certain_ew']:,} coins from\n"
         f"{R['counts']['mints_ew_any']} mints (973 to 1154) and followed each mint town to the poll tax of 1377, the 1801 census and 2021.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.4)

# == hero map: Aethelred II mints as coins ==
ax = fig.add_axes([0.0, 0.335, 0.6, 0.53])
for a in LANDP:
    ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#BFBDB3", lw=.6, zorder=0))
ax.set_xlim(-5.9 * K, 1.9 * K); ax.set_ylim(49.9, 55.3); ax.set_aspect("equal"); ax.axis("off")
fd = pd.DataFrame(P["finds"], columns=["mi", "pi", "la", "lo", "km"])
ax.scatter(fd.lo * K, fd.la, s=2.2, c=BLUE, alpha=.45, lw=0, zorder=1, rasterized=True)
ai = [p[0] for p in P["periods"]].index("aethelred")
ms = sorted([m for m in P["mints"] if m["la"] is not None and m["rec"][ai]], key=lambda m: -m["mon"][ai])
for m in ms:
    x, y = m["lo"] * K, m["la"]; n = m["mon"][ai]; r = .025 + math.sqrt(n) * .0125
    ax.add_patch(Circle((x, y), r, fc=GOLD, ec=FG, lw=.9, zorder=3, alpha=.95))
    if r > .075:
        ax.add_patch(Circle((x, y), r * .78, fc="none", ec=GOLDL, lw=1, ls=(0, (1, 1.6)), zorder=4))
        ax.plot([x - r * .35, x + r * .35], [y, y], color=FG, lw=1.4, zorder=5, solid_capstyle="round")
        ax.plot([x, x], [y - r * .35, y + r * .35], color=FG, lw=1.4, zorder=5, solid_capstyle="round")
lab = {"London": (12, -2, "left"), "York": (12, 0, "left"), "Lincoln": (12, 4, "left"), "Winchester": (0, -24, "center"), "Stamford": (12, -8, "left")}
for nm, (dx, dy, ha) in lab.items():
    m = [q for q in ms if q["m"] == nm][0]
    ax.annotate(f"{nm} {m['mon'][ai]}", (m["lo"] * K, m["la"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", family=MONO, fontsize=11, color=FG, zorder=6)
for nm, (dx, dy, ha) in {"Lydford": (-10, -10, "right"), "Cadbury": (-8, -16, "right"), "Ilchester": (-10, 8, "right"), "Torksey": (-10, -10, "right"), "Wilton": (4, 13, "center")}.items():
    m = [q for q in P["mints"] if q["m"] == nm][0]
    ax.annotate(nm, (m["lo"] * K, m["la"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", family=MONO, fontsize=10.5, color=MAD, zorder=6)
ax.text(.02, .985, "Mints of Æthelred II, 978 to 1016\ncoin size = moneyers named on its pennies\nblue = single coins found, 973 to 1154\nred = under 5,000 people today",
        transform=ax.transAxes, va="top", family=MONO, fontsize=10.5, color=FG, linespacing=1.45)

# == headline numbers ==
tx = fig.add_axes([0.62, 0.36, 0.36, 0.50]); tx.axis("off")
c = R["circulation"]; d = R["destiny"]
notes = [(f"{R['mints_per_reign']['cnut']}", GOLD, f"mints struck coins for Cnut, the peak.\n{R['towns']['London']['moneyers_aethelred']} moneyers worked for Æthelred II\nin London alone."),
         (f"{d['top10_in1377']} of 10", BLUE, "biggest mints of c.1000 were still among\nEngland's largest towns in 1377."),
         (f"{d['list1801_mints']} of 30", MAD, "largest towns of 1801 had ever been\nmint towns. Manchester, Liverpool,\nBirmingham and Leeds had no mint then."),
         (f"{c['all']['median_km']:.0f} km", BLUE, f"median distance a lost penny had\ntravelled, yet {c['all']['nearest_ratio']:.1f}x more likely than\nchance to come from the nearest mint.")]
for (big, col, small), y in zip(notes, [1.0, 0.74, 0.50, 0.24]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=36, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# == table: top ten mints then and now ==
bx = fig.add_axes([0.04, 0.105, 0.55, 0.205]); bx.axis("off")
fig.text(0.04, 0.312, "THE TEN BIGGEST MINTS OF c.1000, THEN AND NOW", family=MONO, fontsize=10.5, color=MUT)
top = d["top10"]
X = [0.0, 0.37, 0.55, 0.72, 0.89]
for x, h in zip(X, ["", "moneyers\nc.1000", "rank\n1377", "rank\n1801", "rank\n2021"]):
    bx.text(x + (0.0 if not h else 0.0), 1.0, h, family=MONO, fontsize=9.5, color=MUT, va="top", ha="left" if not h else "center", transform=bx.transAxes, linespacing=1.2)
for i, t in enumerate(top):
    y = 0.84 - i * 0.087
    bx.text(X[0], y, t["mint"], fontproperties=DISP, fontsize=14, color=FG, va="center", transform=bx.transAxes)
    bx.scatter([X[1] - 0.085], [y], s=20 + t["moneyers"] * 2.2, transform=bx.transAxes, c=GOLD, edgecolors=FG, lw=.7, clip_on=False)
    bx.text(X[1], y, str(t["moneyers"]), family=MONO, fontsize=11, color=FG, va="center", ha="center", transform=bx.transAxes)
    for x, v in zip(X[2:], [t["rank1377"], t["rank1801"], t["rank2021_england"]]):
        if v is None:
            bx.text(x, y, "not listed", family=MONO, fontsize=9, color=MAD, va="center", ha="center", transform=bx.transAxes)
        else:
            bx.text(x, y, f"{int(v)}", family=MONO, fontsize=11, color=BLUE if v <= 30 else FG, fontweight="medium", va="center", ha="center", transform=bx.transAxes)
bx.text(0, -0.03, "1377: poll tax, 41 largest towns. 1801: census, 30 largest. 2021: built-up areas. Blue: top 30.", family=MONO, fontsize=8.8, color=MUT, va="top", transform=bx.transAxes, linespacing=1.35)

# == vanished mints ==
vx = fig.add_axes([0.64, 0.095, 0.34, 0.215]); vx.axis("off")
fig.text(0.64, 0.312, "MINT TOWNS THAT FADED", family=MONO, fontsize=10.5, color=MUT)
tw = R["towns"]
rows = [("Wilton", f"{tw['Wilton']['moneyers_late_as']} moneyers", f"{tw['Wilton']['pop2021']:,.0f} people"),
        ("Ilchester", f"{tw['Ilchester']['moneyers_late_as']} moneyers", f"{tw['Ilchester']['pop2021']:,.0f}"),
        ("Lydford", f"{tw['Lydford']['moneyers_late_as']} moneyers", f"{tw['Lydford']['pop2021']:,.0f} (parish)"),
        ("Cadbury", f"{tw['Cadbury']['moneyers_late_as']} moneyers", f"{tw['Cadbury']['pop2021']:,.0f} (parish)"),
        ("Torksey", f"{tw['Torksey']['burgesses1086']:,.0f} burgesses", f"{tw['Torksey']['pop2021']:,.0f} (parish)"),
        ("Dunwich", f"c.{tw['Dunwich']['pop1086_russell']:,.0f} people", f"{tw['Dunwich']['pop2021']:,.0f} (parish)")]
vx.text(0.0, 1.0, "then", family=MONO, fontsize=9.5, color=MUT, transform=vx.transAxes, va="top"); vx.text(0.38, 1.0, "", transform=vx.transAxes)
vx.text(0.62, 1.0, "2021", family=MONO, fontsize=9.5, color=MUT, transform=vx.transAxes, va="top")
for i, (n, a, b) in enumerate(rows):
    y = 0.87 - i * 0.15
    vx.scatter([0.03], [y - 0.035], s=110, transform=vx.transAxes, c=GOLD, edgecolors=FG, lw=.8, clip_on=False)
    vx.text(0.08, y, n, fontproperties=DISP, fontsize=15, color=MAD, transform=vx.transAxes, va="top")
    vx.text(0.08, y - 0.075, a, family=MONO, fontsize=9.5, color=FG, transform=vx.transAxes, va="top")
    vx.text(0.62, y - 0.02, b, family=MONO, fontsize=10.5, color=FG, transform=vx.transAxes, va="top")
fig.text(0.64, 0.072, "Torksey: Domesday 1086.\nDunwich: Russell's 1086 estimate.", family=MONO, fontsize=8.8, color=MUT)

# == footer ==
fig.text(0.04, 0.012,
         "Data: Fitzwilliam Museum, EMC/SCBI database of early medieval coins (searched 27 Oct 2026; counts derived, only coins with a certain mint).\n"
         "Wikipedia, List of towns and cities in England by historical population (CC BY-SA). Hull Domesday Project (CC BY-NC-SA). ONS Census 2021 (OGL v3).\n"
         "Contains OS data © Crown copyright and database right 2026 (OS Open Names, OGL v3). Natural Earth. Counts of mints and moneyers are floors.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.  tristan-hotham.github.io/saxon-mints",
         family=MONO, fontsize=8.6, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(HERE, "did_englands_money_towns_stay_big.png"), facecolor=BG, dpi=200)
print("ok")
