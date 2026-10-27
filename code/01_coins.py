"""Step 1. Read the EMC/SCBI scrape, deduplicate, classify each record and assign mints and reigns.

Input  : ../../_data9/emc_scbi_coins_by_mint.json.gz (71,759 rows scraped from the Fitzwilliam Museum's
         public search of EMC and SCBI, one search per mint value, retrieved 27 Oct 2026).
Output : ../work/coins.pkl (all deduplicated records with derived fields; NOT published, it holds
         the catalogue's descriptive text) and ../data/mint_labels.csv (how every mint label was treated).

Rules
- Deduplicate on the EMC/SCBI number (the same coin can come back from several mint searches).
- Source: SCBI numbers are 10xx.nnnn, 1200.nnnn, 1201.nnnn and 1300.nnnn (sylloge volumes and
  museum collections); every other number (a year from 1695 to 2026, then a serial) is an EMC
  single-find record. This is inferred from the number pattern; SCBI records almost never have a
  findspot and EMC records almost always do, which supports it.
- Mint label classes: certain (a single named mint), probable ("York?"), copy ("London (copy?)",
  imitations, not struck at the mint), ambiguous ("Bath or Barnstaple", "L- (London / Lincoln /
  Lewes)"), regional or unidentified ("East Anglian (uncertain)", "Gothaburh"), uncertain, and foreign.
  Only "certain" labels enter the mint statistics; the others are counted and reported.
- Reign periods 973 to 1154 from the Ruler field (and the Type field for Edgar's reform coinage
  and to drop Scottish and Northumbrian namesakes).
Run: python3 01_coins.py
"""
import gzip, json, os, re, collections
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
SRC = os.path.join(ROOT, "..", "_data9", "emc_scbi_coins_by_mint.json.gz")
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)

# == mint labels in Britain and Ireland ==
# canonical mint -> (country). Anything certain but not here is foreign (continental, Islamic, etc.).
ENG_WAL = """Axbridge Aylesbury Barnstaple Bath Bedford Bedwyn Berkeley Bramber Bridport Bristol Bruton Buckingham
Bury_St_Edmunds Cadbury Caistor Cambridge Canterbury Cardiff Carlisle Castle_Rising Chester Chichester Christchurch
Cirencester Cissbury Colchester Corbridge Crewkerne Cricklade Derby Dorchester Dover Droitwich Dunwich Durham Exeter
Eye Frome Gloucester Guildford Hastings Hedon Hereford Hertford Horncastle Huntingdon Hythe Ilchester Ipswich Langport
Launceston Leicester Lewes Lincoln London Lydford Lympne Lynn Maldon Malmesbury Marlborough Milbourne_Port Newark
Newcastle Newport Northampton Norwich Nottingham Oxford Pembroke Pevensey Peterborough Petherton Reading Rhuddlan
Richmond Rochester Romney Rye Salisbury Sandwich Shaftesbury Shrewsbury Southampton Southwark Stafford Stamford Steyning
Sudbury Swansea Tamworth Taunton Thetford Torksey Totnes Tutbury Wallingford Wareham Warminster Warwick Watchet Wilton
Winchcombe Winchester Worcester York Caerphilly Bamburgh""".split()
ENG_WAL = {m.replace("_", " ") for m in ENG_WAL}
WALES = {"Cardiff", "Pembroke", "Rhuddlan", "Swansea", "Caerphilly"}
SCOT = {"Aberdeen", "Ayr", "Berwick", "Edinburgh", "Forfar", "Glasgow", "Inverness", "Kinghorn", "Lanark", "Montrose",
        "Perth", "Renfrew", "Roxburgh", "St Andrews", "Stirling", "Dumfries"}
IRE = {"Carrickfergus", "Downpatrick", "Dublin", "Kilkenny", "Limerick", "Waterford"}
UNIDENTIFIED = {"Gothaburh", "Orsnaforda", "West Saxon mint", "Palace (unidentified)"}
BRIT_IRL = ENG_WAL | SCOT | IRE


def classify(label):
    """Return (class, canonical mint or None, candidates)."""
    s = label.strip()
    if s in ("", "uncertain") or s.endswith("(uncertain)") or "(uncertain;" in s:
        regional = s in ("East Anglian (uncertain)", "Five Boroughs (uncertain)", "West Midlands (uncertain)")
        return ("regional" if regional else "uncertain"), None, ""
    if s in UNIDENTIFIED:
        return "unidentified", None, ""
    m = re.match(r"^(\w)\w*- \((.+)\)$", s)  # "L- (London / Lincoln / Lewes)"
    if m:
        return "ambiguous", None, " / ".join(x.strip(" ?") for x in m.group(2).split("/"))
    if " or " in s or "? " in s:
        parts = [p.strip(" ?") for p in re.split(r" or |\? ", s)]
        fix = {"Shrew": "Shrewsbury", "Bridgenor": "Bridgnorth", "N": "Northampton"}
        return "ambiguous", None, " / ".join(fix.get(p, p) for p in parts)
    if re.search(r"\((copy|derivative)", s):
        base = re.sub(r"\s*\(.*\)$", "", s)
        return "copy", base, ""
    if s.endswith("?"):
        return "probable", s.rstrip(" ?"), ""
    return "certain", s, ""


def country(m):
    if m in WALES: return "Wales"
    if m in ENG_WAL: return "England"
    if m in SCOT: return "Scotland"
    if m in IRE: return "Ireland"
    return "foreign"


# == reign periods ==
PERIODS = [  # key, label, start, end
    ("edgar", "Edgar (reform)", 973, 975), ("edwardm", "Edward the Martyr", 975, 978),
    ("aethelred", "Æthelred II", 978, 1016), ("cnut", "Cnut", 1016, 1035), ("harold1", "Harold I", 1035, 1040),
    ("harthacnut", "Harthacnut", 1040, 1042), ("edwardc", "Edward the Confessor", 1042, 1066),
    ("harold2", "Harold II", 1066, 1066), ("william1", "William I", 1066, 1087), ("william2", "William II", 1087, 1100),
    ("henry1", "Henry I", 1100, 1135), ("stephen", "Stephen", 1135, 1154)]
MAIN7 = ["edgar", "aethelred", "cnut", "edwardc", "william1", "henry1", "stephen"]


def period(ruler, typ):
    if ruler == "Edgar":
        return "edgar" if "Reform" in typ else None
    if ruler == "Æthelred II (the Unready)":
        return "aethelred" if "imitation" not in typ else None
    if ruler == "Æthelred II":  # the field mixes the Northumbrian king of the 840s with the English one
        return "aethelred" if typ.startswith("Æthelred II,") else None
    if ruler == "William I":
        return None if typ.startswith("Scotland") else "william1"
    return {"Edward the Martyr": "edwardm", "Cnut": "cnut", "Harold Harefoot": "harold1", "Harthacnut": "harthacnut",
            "Edward the Confessor": "edwardc", "Harold Godwinesson": "harold2", "William II": "william2",
            "Henry I": "henry1", "Stephen": "stephen"}.get(ruler)


def norm_moneyer(m):
    s = (m or "").strip()
    s = re.sub(r"\[|\]|\(|\)|\?", "", s).strip(" .,")
    if s.lower() in ("", "uncertain", "unknown", "illegible", "uncertain moneyer", "null", "-") or "uncertain" in s.lower():
        return None
    return s.casefold()


def source(num):
    p = num.split(".")[0]
    return "SCBI" if len(p) == 4 and (p.startswith("10") or p in ("1200", "1201", "1300")) else "EMC"


if __name__ == "__main__":
    raw = json.load(gzip.open(SRC))
    recs = raw["records"]
    seen = {}
    for r in recs:
        seen.setdefault(r["EMC/SCBI NUMBER"], r)
    df = pd.DataFrame(list(seen.values()))
    df = df.rename(columns={"EMC/SCBI NUMBER": "id", "Mint as on coin": "mint_on_coin"})
    df["source"] = df.id.map(source)
    cls = df.Mint.map(classify)
    df["mint_class"] = [c[0] for c in cls]
    df["mint"] = [c[1] for c in cls]
    df["candidates"] = [c[2] for c in cls]
    df["country"] = df.mint.map(lambda m: country(m) if m else "")
    df.loc[(df.mint_class == "certain") & (df.country == "foreign"), "mint_class"] = "foreign"
    df["period"] = [period(r, t) for r, t in zip(df.Ruler.fillna(""), df.Type.fillna(""))]
    df["moneyer_norm"] = df.Moneyer.map(norm_moneyer)
    df["url"] = "https://emc.fitzmuseum.cam.ac.uk" + df.rec
    df.to_pickle(os.path.join(ROOT, "work", "coins.pkl"))

    lab = (df.groupby("Mint").agg(records=("id", "size"), in_window=("period", lambda s: s.notna().sum()),
                                  emc=("source", lambda s: (s == "EMC").sum())).reset_index())
    c2 = lab.Mint.map(classify)
    lab["class"] = [c[0] for c in c2]; lab["mint"] = [c[1] for c in c2]; lab["candidates"] = [c[2] for c in c2]
    lab["country"] = lab.mint.map(lambda m: country(m) if isinstance(m, str) else "")
    lab.loc[(lab["class"] == "certain") & (lab.country == "foreign"), "class"] = "foreign"
    lab["treatment"] = lab["class"].map({
        "certain": "counted for this mint", "probable": "not counted (attribution queried); reported as a sensitivity",
        "copy": "not counted (copy or imitation, not struck at the mint)",
        "ambiguous": "not counted (the catalogue gives two or more possible mints)",
        "regional": "not counted (region only)", "unidentified": "not counted (mint name not identified with a place)",
        "uncertain": "not counted (mint unknown)", "foreign": "not counted (outside Britain and Ireland)"})
    lab = lab.rename(columns={"Mint": "label"}).sort_values(["class", "label"])
    lab.to_csv(os.path.join(ROOT, "data", "mint_labels.csv"), index=False)
    print(len(recs), "rows,", len(df), "unique records")
    print(df.mint_class.value_counts().to_dict())
    print(df.source.value_counts().to_dict())
    print(df[df.period.notna()].groupby("period").size().to_dict())
    w = df[df.period.notna()]
    print("window by class", w.mint_class.value_counts().to_dict())
