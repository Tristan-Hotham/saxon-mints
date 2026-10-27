"""Step 7. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Minted.tex and compile it with xelatex (figures from 06_release_figs.py).
Placeholders: {{path|fmt}} as in 04_build_site.py, with % escaped for LaTeX.
Run: python3 07_paper.py
"""
import json, os, re, shutil, subprocess
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Minted"
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f3": return f"{v:.3f}"
    if f == "p": return "p $<$ 0.001" if v < 0.001 else f"p = {v:.3f}"
    if f == "words": return WORDS[int(v)] if int(v) < len(WORDS) else f"{int(v):,}"
    if f == "Words": w = fmt(v, "words"); return w[0].upper() + w[1:]
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
num = lambda v: "" if v is None else f"{int(round(v)):,}"
# Table: circulation by period
rows = ""
for p in R["periods"]:
    c = R["circulation"]["by_period"].get(p["key"])
    if not c: continue
    rows += f"{tex(p['label'])} & {c['n']:,} & {c['median_km']:.1f} & {c['within50'] * 100:.0f} & {c['beyond100'] * 100:.0f} & {c['nearest_obs'] * 100:.1f} & {c['nearest_exp'] * 100:.1f}\\\\\n"
for k, lab in (("late_as", "All, 973 to 1066"), ("norman", "All, 1066 to 1154"), ("all", "All")):
    c = R["circulation"][k]
    rows += ("\\midrule " if k == "late_as" else "") + f"{lab} & {c['n']:,} & {c['median_km']:.1f} & {c['within50'] * 100:.0f} & {c['beyond100'] * 100:.0f} & {c['nearest_obs'] * 100:.1f} & {c['nearest_exp'] * 100:.1f}\\\\\n"
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Placed single finds by reign (reigns with at least 30). Median: km from mint to findspot. "
      "Nearest: share of finds struck at the nearest working mint, observed and expected if each find were a random draw from the reign's output weighted by moneyers.}\\label{tab:circ}"
      "\\begin{tabular}{lrrrrrr}\\toprule Reign & Finds & Median km & \\% within 50 km & \\% beyond 100 km & Nearest (\\%) & Expected (\\%)\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}\\end{table}")
# Table: top 10
T = pd.read_csv(os.path.join(ROOT, "data", "mint_towns.csv")).set_index("mint")
rows = ""
for t in R["destiny"]["top10"]:
    r = T.loc[t["mint"]]
    rows += (f"{tex(t['mint'])} & {t['moneyers']} & {num(r.pop1086_russell) if pd.notna(r.pop1086_russell) else ''} & "
             f"{int(r.rank1377) if pd.notna(r.rank1377) else ''} & {num(r.pop1377) if pd.notna(r.pop1377) else ''} & "
             f"{int(r.rank1801) if pd.notna(r.rank1801) else ''} & {num(r.pop1801) if pd.notna(r.pop1801) else ''} & {num(r.pop2021)} & {int(r.rank2021)}\\\\\n")
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{The ten mints with most moneyers under Æthelred II, then and now. 1086: Russell's estimate. "
      "1377: poll tax rank and population; 1801: census rank and population (blank: not in the list). 2021: Census 2021 residents of the built-up area "
      "(London: London region) and rank among the " + str(R["destiny"]["n_with_pop2021"]) + " mint towns with a population.}\\label{tab:top10}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lrrrrrrrr}\\toprule Mint & Moneyers & 1086 & 1377 rank & 1377 & 1801 rank & 1801 & 2021 & 2021 rank\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}}\\end{table}")
# Table: vanished
rows = ""
for v in R["destiny"]["vanished"]:
    if v["moneyers_peak"] < 3 and not (v["burgesses1086"] or 0) >= 25 and v["mint"] not in ("Cadbury", "Cissbury", "Bedwyn"): continue
    src = "parish" if "parish" in v["src"] else ("built-up area" if "built-up" in v["src"] else "none")
    rows += (f"{tex(v['mint'])} & {v['moneyers_peak']} & {v['records']:,} & {tex(v['first'])} & {tex(v['last'])} & "
             f"{num(v['burgesses1086'])} & {num(v['pop2021']) if v['pop2021'] is not None else '0'} & {src}\\\\\n")
TV = ("\\begin{table}[tbp]\\centering\\small\\caption{Mint towns with fewer than 5,000 residents today: those with a peak of three or more moneyers in a reign, "
      "or 25 or more Domesday burgesses, plus Cadbury, Cissbury and Bedwyn. Peak: most moneyers in any reign. First and last: reigns with surviving coins, 973 to 1154. "
      "Burgesses: parsed Domesday entries (blank: none parsed).}\\label{tab:vanished}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lrrllrrl}\\toprule Mint & Peak moneyers & Records & First & Last & Burgesses 1086 & 2021 & 2021 unit\\\\\\midrule\n"
      + rows + "\\bottomrule\\end{tabular}}\\end{table}")

s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_CIRC}}", TC).replace("{{TABLE_TOP10}}", TT).replace("{{TABLE_VANISHED}}", TV)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-800:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
