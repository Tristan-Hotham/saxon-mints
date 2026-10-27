# Minted

The Anglo-Saxon and Norman mint towns of England, 973 to 1154, from {{counts.records_unique|int}} coin records in the Fitzwilliam Museum's EMC/SCBI database. Where were coins struck, reign by reign; how far did they travel; and were the towns that struck coins around 1000 still the important towns in 1377, 1801 and today?

**Interactive version:** https://tristan-hotham.github.io/saxon-mints/

This repository holds the interactive page, derived data and the analysis code for the data study *Minted: the Anglo-Saxon and Norman mint towns of England and what became of them* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23689962

## Headline results

- Of {{counts.window_records|int}} records of English kings from Edgar's reform (c. 973) to Stephen (1154), {{counts.window_certain_ew|int}} ({{counts.window_share_certain|pct0}}) name a single, certain mint in England or Wales: {{counts.mints_ew_any|int}} mint places in all.
- Mints with surviving coins: {{mints_per_reign.edgar|int}} for Edgar's reform type, {{mints_per_reign.aethelred|int}} under Æthelred II, a peak of {{mints_per_reign.cnut|int}} under Cnut, {{mints_per_reign.edwardc|int}} under Edward the Confessor, {{mints_per_reign.william1|int}} under William I, {{mints_per_reign.henry1|int}} under Henry I and {{mints_per_reign.stephen|int}} under Stephen.
- Under Æthelred II, London coins name {{towns.London.moneyers_aethelred|int}} moneyers, York {{towns.York.moneyers_aethelred|int}} and Lincoln {{towns.Lincoln.moneyers_aethelred|int}}: together {{london_york_lincoln_share_aethelred|pct0}} of all moneyers in that reign.
- Single finds: the median coin was lost {{circulation.all.median_km|f1}} km from its mint ({{circulation.emc_placed|int}} placed EMC finds); {{circulation.all.beyond100|pct0}} travelled more than 100 km. But {{circulation.all.nearest_obs|pct0}} came from the nearest working mint, {{circulation.all.nearest_ratio|f1}} times the share expected if coins mixed freely, and a random-mint baseline gives a median of {{circulation.random_mint_median_km|int}} km.
- {{destiny.top10_in1377|Words}} of the ten biggest mints of c.1000 were among the {{destiny.list1377_n|int}} largest towns in the 1377 poll tax; {{destiny.top10_in1801|words}} were in the 30 largest towns of 1801. Moneyers under Æthelred II and Census 2021 population: Spearman {{destiny.spearman_aethelred_2021|f2}} ({{destiny.p_aethelred_2021|p}}, {{destiny.n_aethelred_2021|int}} towns); against 1801 only {{destiny.spearman_aethelred_1801|f2}}.
- Only {{destiny.list1801_mints|int}} of the 30 largest towns of 1801, and {{destiny.top30_2021_mints|int}} of England's 30 largest built-up areas today, were mint towns in this period.
- {{destiny.n_vanished|int}} mint towns have fewer than 5,000 people today, among them Wilton, Ilchester, Lydford, Cadbury, Torksey and Dunwich.

## Files

- `index.html`: the interactive page (Leaflet map with a reign slider, charts, tables).
- `header.png`: social card.
- `data/mints.csv`: every placed mint in England and Wales: coordinates, how it was placed (OS Open Names name, type and county), notes on identification, the Wikidata cross-check offset, the catalogue labels counted for it, records 973 to 1154.
- `data/mint_reign.csv`: records, SCBI records, EMC single finds and distinct moneyers per mint per reign period.
- `data/mint_towns.csv`: one row per mint town: moneyers and records per reign, Domesday place matched and its parsed households and burgesses, Russell's 1086 estimate, 1377 and 1801 rank and population (where in the lists), Census 2021 population and its source, mean household income FYE2023.
- `data/mint_labels.csv`: every mint label in the search output and how it was treated (counted, probable, copy, ambiguous, regional, unidentified, uncertain, foreign).
- `data/ambiguous_mints.csv`: the records whose mint is given as two or more possibilities.
- `data/records_index.csv`: one row per record used or considered ({{counts.records_index_rows|int}}): EMC/SCBI number, URL of the full record, source (EMC or SCBI), mint class, mint, reign period, and for placed single finds the findspot rounded to 0.01 degree and the distance from the mint. No descriptive text from the catalogue.
- `data/page_data.json`: compact data for the page.
- `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_coins.py` (deduplicate, classify mints and reigns), `02_geocode.py` (place mints and findspots), `03_analysis.py` (all statistics), `04_build_site.py` (page and README), `05_header.py` (social card), `06_release_figs.py` (paper and blog figures), `07_paper.py` (paper PDF via xelatex).

## Method in brief

**Coins.** The Fitzwilliam Museum's public search of the Corpus of Early Medieval Coin Finds (EMC) and the Sylloge of Coins of the British Isles (SCBI), https://emc.fitzmuseum.cam.ac.uk/, was searched by each of its {{counts.mint_values_searched|int}} mint values on 27 October 2026 ({{counts.rows_scraped|int}} rows). Records were deduplicated by EMC/SCBI number ({{counts.duplicates|int}} duplicates). SCBI and EMC records are told apart by the number pattern (SCBI numbers start 10xx, 1200, 1201 or 1300; EMC numbers start with a year), which the presence of findspots supports. Reigns: Edgar's reform type, then each king from Edward the Martyr to Stephen, from the ruler field. Only records whose mint is a single certain place in England or Wales are counted; queried ("York?"), copied, ambiguous ("Bath or Barnstaple"), regional and unidentified mints are listed but not counted. A mint's size in a reign is its number of distinct moneyer names.

**Places.** Mints are placed at the OS Open Names point of the town or village of the same name, with a short manual table for difficult names (Bedwyn at Great Bedwyn, Cadbury at South Cadbury beside Cadbury Castle, Cissbury at Cissbury Ring, Lynn at King's Lynn, Romney at New Romney, Petherton at North Petherton); Newport is not placed. Horndon, known from one coin not in the database, is shown for reference. EMC findspots are matched to OS Open Names populated places when the name is unique in Great Britain, all its matches lie within 15 km, it is the only city or town of that name, or a "near X" qualifier picks one; county-level findspots are rejected.

**Destiny.** 1086 (Russell's estimates), 1377 (poll tax, {{destiny.list1377_n|int}} towns) and 1801 (census, 30 towns) from Wikipedia's *List of towns and cities in England by historical population*. Domesday households and burgesses from the parsed Hull Domesday Project data in the companion study Domesday Destiny (incomplete for county towns). Census 2021 population summed from LSOAs to the 2022 built-up area of the same name (best fit), London as the London region, and civil parish population for villages without a built-up area. Income: ONS mean total household income FYE2023 by MSOA, population weighted.

**Caveats.** The database is what has been catalogued, not every coin; counts of mints and moneyers are floors and depend on survival and on which collections are published. Moneyer spellings may split one person in two. Findspot matching by name can misplace a find. The 1377 and 1801 lists cover only the largest towns. Built-up area populations by LSOA best fit are crude for small places.

## How to rerun

Python 3 with pandas, numpy, scipy, openpyxl and matplotlib (and Playwright for the header). From `code/`: `python3 01_coins.py && python3 02_geocode.py && python3 03_analysis.py && python3 04_build_site.py`. Inputs are read one folder up and are not included: `_data9/emc_scbi_coins_by_mint.json.gz` (the search output), `_data9/wikipedia_wikitext.json`, `_data8/` (ONS Census 2021, income and geography files, Wikidata settlements), `osnames_gb.tsv` (OS Open Names) and `domesday-destiny/data/domesday_places.csv`.

## Sources and licence

- Coins: Fitzwilliam Museum, EMC/SCBI database (Corpus of Early Medieval Coin Finds; Sylloge of Coins of the British Isles), https://emc.fitzmuseum.cam.ac.uk/ , searched 27 October 2026. The licence of the database is not stated in a form I could confirm, so I treat its records as factual entries in a public catalogue: this repository republishes only derived counts (records and moneyers by mint and reign), record numbers and links to the full records, and derived findspot coordinates, not the catalogue's descriptive text or any images. Please cite the database as "Fitzwilliam Museum, EMC/SCBI database" and consult it for the records themselves.
- Historical populations: Wikipedia contributors, *List of towns and cities in England by historical population* (CC BY-SA 4.0), which cites Russell (1948) for 1086 and 1377 and the 1801 census abstract. Context on Edgar's reform and the number of mints: Wikipedia, *History of the English penny (c. 600 to 1066)* and *Horndon mint* (CC BY-SA 4.0).
- Domesday: Hull Domesday Project, Professor J.J.N. Palmer, George Slater and the University of Hull (CC BY-NC-SA), via https://github.com/embabel-worlds/realm-domesday and my Domesday Destiny study.
- Census 2021, ONS small-area income estimates (FYE2023) and ONS geography lookups: Office for National Statistics, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026.
- Places: OS Open Names, Ordnance Survey, Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2026. Cross-check: Wikidata (CC0).
- Base map tiles on the page: Esri. Map library: Leaflet.

Because the derived data include Hull Domesday Project figures (CC BY-NC-SA), the derived data and the page text are released under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). Code is MIT (see `LICENSE`).

Companion studies: [Is Domesday destiny?](https://tristan-hotham.github.io/domesday-destiny/) and [Silver and Names: Viking hoards and Norse place names](https://tristan-hotham.github.io/viking-silver/).

## Citation

Hotham, T. (2026) *Minted: the Anglo-Saxon and Norman mint towns of England and what became of them*. Zenodo. https://doi.org/10.5281/zenodo.23689962

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
