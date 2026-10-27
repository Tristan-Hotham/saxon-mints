"""Step 8. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 08_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "04_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)(.+?)\}\}", b.sub, t)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m

d = R["destiny"]
title = "Minted: The Anglo-Saxon and Norman Mint Towns of England and What Became of Them"
meta = dict(
    title="Minted: were England's mint towns still the big towns?",
    slug="saxon-mints",
    excerpt=(f"Around the year 1000, every English penny named the town that struck it. I followed the {R['mints_per_reign']['aethelred']} mint towns of "
             f"Æthelred II forward to 1377, 1801 and 2021. {d['top10_in1377']} of the 10 biggest were still among England's largest towns in 1377; Lydford, Cadbury and Torksey are villages now."),
    seo_description="Were the towns that struck England's coins around 1000 still the big towns in 1377, 1801 and today? Mostly yes, with some vanished mints.",
    tags=["Anglo-Saxon", "coins", "mints", "medieval towns", "Domesday", "census", "maps", "data"],
    header_alt=(f"Title card reading 'Minted' in old gold on a pale silver-grey background, beside a map of England and Wales with gold coin-like discs for the "
                f"mints of Æthelred II, sized by their moneyers. Text: around 1000, pennies were struck in {R['mints_per_reign']['aethelred']} English towns; "
                f"{d['top10_in1377']} of the 10 biggest mints were still among the largest towns in 1377; Lydford, Cadbury and Torksey are villages now."))
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

# abstract from the paper template (filled)
pt = open(os.path.join(ROOT, "release", "paper", "Hotham_Minted.tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("$<$", "<")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title=title,
    description_html=f"<p>{ab}</p><p>Interactive version: https://tristan-hotham.github.io/saxon-mints/. Data and code: https://github.com/Tristan-Hotham/saxon-mints. Blog post: to follow.</p>",
    keywords=["Anglo-Saxon coinage", "mints", "moneyers", "medieval towns", "urban history", "single finds", "Domesday", "poll tax 1377", "Census 2021", "open data"],
    licence="cc-by-nc-sa-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/saxon-mints", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/saxon-mints/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://emc.fitzmuseum.cam.ac.uk/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://en.wikipedia.org/wiki/List_of_towns_and_cities_in_England_by_historical_population", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://digitalcollections.hull.ac.uk/collections/3t945r28b", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ons.gov.uk/census", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", "Hotham_Minted.pdf"), Z)
for f in ["mints.csv", "mint_reign.csv", "mint_towns.csv", "mint_labels.csv", "ambiguous_mints.csv", "records_index.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "saxon-mints_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p): zf.write(p, f"saxon-mints/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"saxon-mints/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t)).split()))
