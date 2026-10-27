"""Step 2. Place the mints and the single-find findspots.

Mints: every mint in England and Wales with at least one certain record, placed at the OS Open Names
point of the town or village that carries its name today. The lookup table below gives, for each
mint label, the OS Open Names name to look up, a county filter, and a note where the identification
needs one (Bedwyn = Great Bedwyn; Cadbury = the hillfort of Cadbury Castle beside South Cadbury;
Cissbury = the hillfort of Cissbury Ring; Lynn = King's Lynn; Romney = New Romney; Petherton = North
Petherton; Milbourne Port = Milborne Port). Newport is left unplaced: several places of that name are
possible. Horndon (Horndon on the Hill) is added from the Wikipedia article "Horndon mint": it is known
from one coin, which is not in the search output. Each mint is cross-checked against the nearest
Wikidata settlement with the same label (CC0), and the offset is recorded.

Findspots (EMC single finds only): the findspot text is cleaned ("Lincoln, near" -> Lincoln,
"Royston, near, productive site" -> Royston; parenthetical detail dropped; county-only findspots such
as 'Norfolk' rejected) and matched to OS Open Names populated places (name1 or name2). A findspot is
accepted only if the name is unique in Great Britain, or if every place with that name lies within
15 km of the others (then their mean point is used). The findspot strings are not published; only
the derived coordinates (rounded to 0.01 degree) and the method.
Run: python3 02_geocode.py
"""
import json, os, re, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
HIST = os.path.join(ROOT, "..")
OSN = os.path.join(HIST, "osnames_gb.tsv")

# mint label -> (OS Open Names name, county filter substring or "", note)
LOOKUP = {
    "Bath": ("Bath", "Somerset", ""), "Bedwyn": ("Great Bedwyn", "Wiltshire", "Bedwyn is placed at Great Bedwyn."),
    "Berkeley": ("Berkeley", "Gloucestershire", ""), "Bramber": ("Bramber", "West Sussex", ""),
    "Bristol": ("Bristol", "", ""), "Bury St Edmunds": ("Bury St Edmunds", "Suffolk", ""),
    "Cadbury": ("South Cadbury", "Somerset", "The mint was at the hillfort of Cadbury Castle, beside South Cadbury (Wikipedia, History of the English penny)."),
    "Cissbury": ("Cissbury Ring", "West Sussex", "The hillfort of Cissbury Ring, near Findon."),
    "Chester": ("Chester", "Cheshire", ""), "Christchurch": ("Christchurch", "Christchurch", ""),
    "Dorchester": ("Dorchester", "Dorset", "Dorchester, Dorset."), "Durham": ("Durham", "Durham", ""),
    "Eye": ("Eye", "Suffolk", ""), "Hereford": ("Hereford", "Herefordshire", ""), "Hythe": ("Hythe", "Kent", ""),
    "Lynn": ("King's Lynn", "Norfolk", "Lynn is placed at King's Lynn."), "Newark": ("Newark-on-Trent", "Nottinghamshire", ""),
    "Newcastle": ("Newcastle upon Tyne", "", "Newcastle upon Tyne."), "Petherton": ("North Petherton", "Somerset", "Petherton is placed at North Petherton."),
    "Milbourne Port": ("Milborne Port", "Somerset", ""), "Romney": ("New Romney", "Kent", "Romney is placed at New Romney."),
    "Rochester": ("Rochester", "Medway", ""), "Richmond": ("Richmond", "North Yorkshire", "Richmond, North Yorkshire."),
    "Salisbury": ("Salisbury", "Wiltshire", "Placed at modern Salisbury; the medieval town stood at Old Sarum, about 3 km north, until the 13th century."),
    "Sudbury": ("Sudbury", "Suffolk", "Sudbury, Suffolk."), "Stafford": ("Stafford", "Staffordshire", ""),
    "Steyning": ("Steyning", "West Sussex", ""), "Warwick": ("Warwick", "Warwickshire", ""), "Wilton": ("Wilton", "Wiltshire", "Wilton, Wiltshire."),
    "Reading": ("Reading", "Reading", ""), "Rhuddlan": ("Rhuddlan", "Denbighshire", ""), "Pembroke": ("Pembroke", "Pembrokeshire", ""),
    "Swansea": ("Swansea", "Swansea", ""), "Cardiff": ("Cardiff", "Cardiff", ""), "Caerphilly": ("Caerphilly", "Caerphilly", ""),
    "Lydford": ("Lydford", "Devon", "Lydford, Devon."), "Launceston": ("Launceston", "Cornwall", ""),
    "Droitwich": ("Droitwich Spa", "Worcestershire", ""), "Hedon": ("Hedon", "East Riding", ""), "Caistor": ("Caistor", "Lincolnshire", ""),
    "Bamburgh": ("Bamburgh", "Northumberland", ""), "Horndon": ("Horndon on the Hill", "Thurrock", "Known from one coin of Edward the Confessor (Wikipedia, Horndon mint); not in the search output."),
    "Newport": (None, "", "Not placed: several places called Newport are possible."),
    "Langport": ("Langport", "Somerset", ""), "Frome": ("Frome", "Somerset", ""), "Watchet": ("Watchet", "Somerset", ""),
    "Taunton": ("Taunton", "Somerset", ""), "Bruton": ("Bruton", "Somerset", ""), "Crewkerne": ("Crewkerne", "Somerset", ""),
    "Ilchester": ("Ilchester", "Somerset", ""), "Axbridge": ("Axbridge", "Somerset", ""), "Warminster": ("Warminster", "Wiltshire", ""),
    "Malmesbury": ("Malmesbury", "Wiltshire", ""), "Marlborough": ("Marlborough", "Wiltshire", ""), "Cricklade": ("Cricklade", "Wiltshire", ""),
    "Wareham": ("Wareham", "Dorset", ""), "Bridport": ("Bridport", "Dorset", ""), "Shaftesbury": ("Shaftesbury", "Dorset", ""),
    "Totnes": ("Totnes", "Devon", ""), "Barnstaple": ("Barnstaple", "Devon", ""), "Exeter": ("Exeter", "Devon", ""),
    "Guildford": ("Guildford", "Surrey", ""), "Lewes": ("Lewes", "East Sussex", ""), "Hastings": ("Hastings", "East Sussex", ""),
    "Pevensey": ("Pevensey", "East Sussex", ""), "Rye": ("Rye", "East Sussex", ""), "Chichester": ("Chichester", "West Sussex", ""),
    "Dover": ("Dover", "Kent", ""), "Sandwich": ("Sandwich", "Kent", ""), "Lympne": ("Lympne", "Kent", ""), "Canterbury": ("Canterbury", "Kent", ""),
    "Maldon": ("Maldon", "Essex", ""), "Colchester": ("Colchester", "Essex", ""), "Ipswich": ("Ipswich", "Suffolk", ""),
    "Dunwich": ("Dunwich", "Suffolk", ""), "Thetford": ("Thetford", "Norfolk", ""), "Norwich": ("Norwich", "Norfolk", ""),
    "Castle Rising": ("Castle Rising", "Norfolk", ""), "Cambridge": ("Cambridge", "Cambridgeshire", ""), "Huntingdon": ("Huntingdon", "Cambridgeshire", ""),
    "Peterborough": ("Peterborough", "Peterborough", ""), "Hertford": ("Hertford", "Hertfordshire", ""), "Bedford": ("Bedford", "Bedford", ""),
    "Buckingham": ("Buckingham", "Buckinghamshire", ""), "Aylesbury": ("Aylesbury", "Buckinghamshire", ""), "Oxford": ("Oxford", "Oxfordshire", ""),
    "Wallingford": ("Wallingford", "Oxfordshire", ""), "Winchester": ("Winchester", "Hampshire", ""), "Southampton": ("Southampton", "Southampton", ""),
    "London": ("London", "Greater London", ""), "Southwark": ("Southwark", "Greater London", ""), "Gloucester": ("Gloucester", "Gloucestershire", ""),
    "Winchcombe": ("Winchcombe", "Gloucestershire", ""), "Cirencester": ("Cirencester", "Gloucestershire", ""), "Worcester": ("Worcester", "Worcestershire", ""),
    "Shrewsbury": ("Shrewsbury", "Shropshire", ""), "Tamworth": ("Tamworth", "Staffordshire", ""), "Tutbury": ("Tutbury", "Staffordshire", ""),
    "Derby": ("Derby", "Derby", ""), "Nottingham": ("Nottingham", "Nottingham", ""), "Leicester": ("Leicester", "Leicester", ""),
    "Northampton": ("Northampton", "Northamptonshire", ""), "Lincoln": ("Lincoln", "Lincolnshire", ""), "Stamford": ("Stamford", "Lincolnshire", ""),
    "Torksey": ("Torksey", "Lincolnshire", ""), "Horncastle": ("Horncastle", "Lincolnshire", ""), "York": ("York", "York", ""),
    "Carlisle": ("Carlisle", "Cumbria", ""), "Corbridge": ("Corbridge", "Northumberland", ""),
}
RANK = {"City": 0, "Town": 1, "Village": 2, "Suburban Area": 3, "Hamlet": 4, "Other Settlement": 5, "Hill Or Mountain": 6}


def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


if __name__ == "__main__":
    os_ = pd.read_csv(OSN, sep="\t", usecols=["name1", "name2", "type", "local_type", "lat", "lon", "county", "country"], dtype=str)
    os_["lat"] = os_.lat.astype(float); os_["lon"] = os_.lon.astype(float)
    os_ = os_[os_.type.isin(["populatedPlace", "landform"])]
    coins = pd.read_pickle(os.path.join(ROOT, "work", "coins.pkl"))
    cert = coins[(coins.mint_class == "certain") & coins.country.isin(["England", "Wales"])]
    mints = sorted(set(cert.mint)) + ["Horndon"]
    # Wikidata settlements for a cross-check
    wd = json.load(open(os.path.join(HIST, "_data8", "uk_bundle_wikidata_osm.json")))["wd_settlements_pop_tsv"].splitlines()[1:]
    WD = {}
    for l in wd:
        f = l.split("\t")
        m = re.match(r'"(.+)"@en', f[1]); c = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", f[3])
        if m and c:
            WD.setdefault(m.group(1), set()).add((float(c.group(2)), float(c.group(1))))
    rows = []
    for m in mints:
        name, cty, note = LOOKUP.get(m, (m, "", ""))
        if name is None:
            rows.append(dict(mint=m, lat=None, lon=None, country="England", os_name="", os_type="", os_county="", method="not placed", note=note, wikidata_offset_km=None)); continue
        c = os_[((os_.name1 == name) | (os_.name2 == name))]
        if cty:
            c2 = c[c.county.fillna("").str.contains(cty, regex=False)]
            c = c2 if len(c2) else c
        c = c[c.type == "populatedPlace"] if (c.type == "populatedPlace").any() else c
        c = c.assign(r=c.local_type.map(RANK).fillna(9)).sort_values("r")
        if not len(c):
            print("NOT FOUND", m, name); continue
        b = c.iloc[0]
        cand = WD.get(m, set()) | WD.get(name, set())
        off = min((hav(b.lat, b.lon, a, o) for a, o in cand), default=None)
        rows.append(dict(mint=m, lat=round(b.lat, 5), lon=round(b.lon, 5), country=b.country, os_name=name, os_type=b.local_type,
                         os_county=b.county, method="OS Open Names point" + (" (landform)" if b.type == "landform" else ""), note=note,
                         wikidata_offset_km=None if off is None else round(off, 2)))
    M = pd.DataFrame(rows)
    M.to_csv(os.path.join(ROOT, "work", "mint_points.csv"), index=False)
    print(M.to_string())
    print("wikidata offsets >5 km:", M[M.wikidata_offset_km > 5][["mint", "wikidata_offset_km"]].values.tolist())

    # == findspots ==
    emc = coins[coins.source == "EMC"]
    pp = os_[os_.type == "populatedPlace"]
    idx = {}
    for n1, n2, la, lo, lt in zip(pp.name1, pp.name2, pp.lat, pp.lon, pp.local_type):
        for n in (n1, n2):
            if isinstance(n, str):
                idx.setdefault(n.casefold(), []).append((la, lo, lt))

    def clean(s):
        s = (s or "").strip()
        if not s or s.lower() in ("uncertain", "unknown") or s.startswith("'") or s.startswith('"'):
            return None, "no usable findspot"
        s = re.sub(r"\(.*?\)", "", s).replace("\\", "")
        parts = [p.strip() for p in s.split(",")]
        head = parts[0]
        anchor = None
        for p in parts[1:]:
            m_ = re.match(r"^(?:near|nr\.?)\s+([A-Z][\w' -]+)$", p)
            if m_:
                anchor = m_.group(1).strip()
        near = any(p.lower().startswith(("near", "nr")) for p in parts[1:]) or " near " in s.lower()
        head = re.sub(r"\b(productive site|area|parish|environs|district)\b.*$", "", head, flags=re.I).strip()
        head = re.sub(r"^(near|nr\.?)\s+", "", head, flags=re.I).strip()
        head = re.sub(r"\s+(Abbey|Castle|Priory)$", "", head).strip()
        return (head or None), ("near" if near else "at"), anchor

    out = {}
    for s in emc.Findspot.fillna("").unique():
        h, how, anchor = (clean(s) + (None,))[:3]
        if not h:
            out[s] = (None, None, "rejected: " + how); continue
        c = idx.get(h.casefold())
        if not c:
            out[s] = (None, None, "rejected: no OS Open Names match"); continue
        la = np.array([x[0] for x in c]); lo = np.array([x[1] for x in c])
        spread = max(hav(la.min(), lo.min(), la.max(), lo.max()), 0) if len(c) > 1 else 0
        towns = [x for x in c if x[2] in ("City", "Town")]
        anc = idx.get(anchor.casefold()) if anchor else None
        if len(c) == 1 or spread <= 15:
            out[s] = (round(float(la.mean()), 4), round(float(lo.mean()), 4), f"OS Open Names, {'unique name' if len(c) == 1 else 'all matches within 15 km'}, {how}")
        elif anc and len(anc) == 1:
            b = min(c, key=lambda x: hav(x[0], x[1], anc[0][0], anc[0][1]))
            out[s] = (round(b[0], 4), round(b[1], 4), f"OS Open Names, nearest match to the place named after 'near', {how}")
        elif len(towns) == 1:
            out[s] = (round(towns[0][0], 4), round(towns[0][1], 4), f"OS Open Names, the only city or town of that name, {how}")
        else:
            out[s] = (None, None, f"rejected: name ambiguous ({len(c)} places)")
    F = pd.DataFrame([(k, *v) for k, v in out.items()], columns=["findspot", "lat", "lon", "method"])
    F.to_pickle(os.path.join(ROOT, "work", "findspots.pkl"))
    n = emc.Findspot.fillna("").map(lambda s: out[s][0] is not None)
    print("EMC records", len(emc), "findspot placed", int(n.sum()), f"{n.mean():.1%}")
    print(F.method.str.replace(r" \(\d+ places\)", "", regex=True).value_counts())
