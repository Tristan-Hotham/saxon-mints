"""Step 5. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf and
IBMPlexMono-Medium.ttf as FONT_DIR (from github.com/google/fonts); otherwise system serif is used.
Coastline: Natural Earth 1:10m land for the British Isles, as extracted for the lighthouse project.
Run: FONT_DIR=/path/to/fonts python3 05_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(52.5))
X0, X1, Y0, Y1 = -5.9 * K, 1.9 * K, -55.3, -49.9
Hh = 600; Ww = Hh * (X1 - X0) / (Y1 - Y0)


def pr(lat, lon):
    return (lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh


COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
land = ""
for g in json.load(open(COAST)):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = poly[0]
        if min(q[1] for q in ring) < 49.6 and max(q[0] for q in ring) > 1.0:
            continue
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in ring)) + "Z"
ai = [p[0] for p in P["periods"]].index("aethelred")
coins = ""
for m in sorted(P["mints"], key=lambda m: -m["mon"][ai]):
    if m["la"] is None or not m["rec"][ai]:
        continue
    x, y = pr(m["la"], m["lo"]); r = 3 + math.sqrt(m["mon"][ai]) * 2.4
    coins += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#B98A22" fill-opacity=".9" stroke="#1F3B70" stroke-width="1.3"/>'
    if r > 9:
        coins += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * .72:.1f}" fill="none" stroke="#F3E3B0" stroke-width="1" stroke-dasharray="1.5 2"/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
d = R["destiny"]
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 50%,#F4F3EE 0%,#ECEBE6 55%,#DEDCD4 100%);color:#1A1F2B;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:70px;top:78px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#5D6270;display:flex;gap:12px;align-items:center}}
.k b{{background:#1F3B70;color:#ECEBE6;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:64px;top:118px;margin:0;font:900 150px/.9 Fraunces,Georgia,serif;letter-spacing:-.02em;color:#A27718}}
p{{position:absolute;left:70px;top:312px;width:600px;margin:0;font-size:28px;line-height:1.36;color:#1A1F2B}}
p b{{color:#1F3B70}}
.f{{position:absolute;left:70px;bottom:44px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#5D6270}}
svg{{position:absolute;right:20px;top:15px}}
</style></head><body>
<div class="k"><b>Data study</b><span>Coins × towns · 973 to 1154</span></div>
<h1>Minted</h1>
<p>Around 1000, pennies were struck in <b>{R['mints_per_reign']['aethelred']} English towns</b>. {d['top10_in1377']} of the 10 biggest mints were still among the largest towns in 1377. Lydford, Cadbury and Torksey are villages now.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#DAD8CF" stroke="#BDBBB2" stroke-width="1"/>{coins}</svg>
</body></html>"""
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
