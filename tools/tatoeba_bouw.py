"""Bouwt een compact Tatoeba-bestand: Mandarijnse zinnen (vereenvoudigd) + NL/EN-vertaling.
Gebruik: python tools/tatoeba_bouw.py <downloadmap> [uitvoer.tsv.gz]
Zonder uitvoer: backend/app/data/tatoeba_cmn.tsv.gz. Uitleg: backend/README.md."""
import bz2, csv, gzip, sys, tarfile
from pathlib import Path

STANDAARD = Path(__file__).resolve().parents[1] / "backend" / "app" / "data" / "tatoeba_cmn.tsv.gz"
dl = Path(sys.argv[1])
uit = Path(sys.argv[2]) if len(sys.argv) > 2 else STANDAARD
csv.field_size_limit(10**7)

def lees(naam):
    with bz2.open(dl / naam, "rt", encoding="utf-8") as f:
        for rij in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(rij) >= 3:
                yield int(rij[0]), rij[2]

def vereenvoudigd(zin):
    """Alle hanzi moeten in GB2312 staan (≈ vereenvoudigd); traditionele tekens vallen daar buiten."""
    for c in zin:
        if "一" <= c <= "鿿":
            try:
                c.encode("gb2312")
            except UnicodeEncodeError:
                return False
    return True

cmn = {i: t for i, t in lees("cmn_sentences.tsv.bz2") if vereenvoudigd(t) and len(t) <= 40}
nld = dict(lees("nld_sentences.tsv.bz2"))
eng = dict(lees("eng_sentences.tsv.bz2"))
print("cmn vereenvoudigd:", len(cmn), "nld:", len(nld), "eng:", len(eng))

nl_van, en_van = {}, {}
with tarfile.open(dl / "links.tar.bz2", "r:bz2") as tar:
    lid = next(m for m in tar.getmembers() if m.name.endswith(".csv"))
    for regel in tar.extractfile(lid):
        a, b = regel.decode().split("\t")[:2]
        a, b = int(a), int(b)
        if a in cmn:
            if b in nld and a not in nl_van: nl_van[a] = nld[b]
            if b in eng and a not in en_van: en_van[a] = eng[b]

n = 0
with gzip.open(uit, "wt", encoding="utf-8", newline="") as f:
    f.write("id\thanzi\tnl\ten\n")
    for i, t in sorted(cmn.items()):
        nl, en = nl_van.get(i, ""), en_van.get(i, "")
        if not (nl or en):
            continue
        f.write("\t".join(x.replace("\t", " ") for x in (str(i), t, nl, en)) + "\n")
        n += 1
print("geschreven:", n, "zinnen met vertaling; met NL:", sum(1 for i in cmn if i in nl_van), "→", uit, uit.stat().st_size // 1024, "KB")
