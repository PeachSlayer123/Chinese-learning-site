"""Zinnen uit Tatoeba (https://tatoeba.org): echte, door mensen nagekeken zinnen.

Bron en licentie: Tatoeba, CC BY 2.0 FR (bronvermelding verplicht, zie README en de app).
Het bestand `data/tatoeba_cmn.tsv.gz` bevat de vereenvoudigde Mandarijnse zinnen met een Nederlandse
en/of Engelse vertaling. Opnieuw maken: `tools/tatoeba_bouw.py` (zie backend/README.md).

Een zin is bruikbaar als al zijn hanzi in de woordenlijsten tot en met deze week voorkomen
(dezelfde controle als bij de AI-zinnen) en hij minstens één woord van deze week bevat.
"""

from __future__ import annotations

import csv
import gzip
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import pinyin
from .dictee import RuweZin

STANDAARD_PAD = Path(__file__).with_name("data") / "tatoeba_cmn.tsv.gz"
MIN_LENGTE = 3  # "好！" is geen dictee-zin


@dataclass(frozen=True)
class TatoebaZin:
    id: int
    hanzi: str
    nl: str
    en: str

    @property
    def vertaling(self) -> str:
        return self.nl or f"{self.en} (EN)"


@lru_cache(maxsize=4)
def laad(pad: Path = STANDAARD_PAD) -> tuple[TatoebaZin, ...]:
    if not pad.exists():
        return ()
    with gzip.open(pad, "rt", encoding="utf-8", newline="") as f:
        return tuple(
            TatoebaZin(int(r["id"]), r["hanzi"], r["nl"], r["en"])
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        )


def bruikbare_zinnen(
    zinnen: tuple[TatoebaZin, ...], weekhanzi: list[str], alle_hanzi: list[str]
) -> list[TatoebaZin]:
    return [
        z
        for z in zinnen
        if len(z.hanzi) >= MIN_LENGTE
        and not pinyin.onbekende_tekens(z.hanzi, alle_hanzi)
        and pinyin.gebruikte_woorden(z.hanzi, weekhanzi)
    ]


def kies(
    kandidaten: list[TatoebaZin],
    weekwoorden: list[dict],
    aantal: int,
    rng: random.Random | None = None,
) -> list[TatoebaZin]:
    """Kiest `aantal` zinnen zodat zoveel mogelijk weekwoorden aan bod komen.

    Volgorde van voorkeur per stap: dekt een nog niet geoefend weekwoord, bevat vaak foute woorden
    (`keer_fout`), heeft een Nederlandse vertaling. Daarna beslist het toeval (met lichte voorkeur voor
    korte zinnen), zodat twee dictees van dezelfde week verschillende zinnen krijgen.
    """
    rng = rng or random.Random()
    toeval = {id(z): rng.random() / (1 + len(z.hanzi) / 20) for z in kandidaten}
    fout = {w["hanzi"]: w.get("keer_fout") or 0 for w in weekwoorden}
    weekhanzi = [w["hanzi"] for w in weekwoorden]
    pool = kandidaten[:]
    gekozen: list[TatoebaZin] = []
    gedekt: set[str] = set()
    gezien_hanzi: set[str] = set()
    while pool and len(gekozen) < aantal:

        def score(z: TatoebaZin) -> tuple:
            woorden = pinyin.gebruikte_woorden(z.hanzi, weekhanzi)
            nieuw = len([w for w in woorden if w not in gedekt])  # 2+ nieuwe = even goed: meer variatie
            return (min(nieuw, 2), sum(fout.get(w, 0) for w in woorden), bool(z.nl), toeval[id(z)])

        beste = max(pool, key=score)
        pool.remove(beste)
        if beste.hanzi in gezien_hanzi:
            continue
        gezien_hanzi.add(beste.hanzi)
        gekozen.append(beste)
        gedekt.update(pinyin.gebruikte_woorden(beste.hanzi, weekhanzi))
    return gekozen


class TatoebaZinnenBron:
    """ZinnenBron die alleen zinnen teruggeeft die volledig binnen de woordenschat vallen.

    Kan minder zinnen teruggeven dan gevraagd (of geen): de `GecombineerdeBron` vult dan aan.
    """

    naam = "tatoeba"

    def __init__(self, pad: Path = STANDAARD_PAD, rng: random.Random | None = None):
        self.zinnen = laad(pad)
        self.rng = rng or random.Random()

    def maak_zinnen(
        self, weekwoorden: list[dict], bekende_woorden: list[dict], aantal: int, opmerking: str = ""
    ) -> list[RuweZin]:
        weekhanzi = [w["hanzi"] for w in weekwoorden]
        alle_hanzi = weekhanzi + [w["hanzi"] for w in bekende_woorden]
        kandidaten = bruikbare_zinnen(self.zinnen, weekhanzi, alle_hanzi)
        return [
            RuweZin(hanzi=z.hanzi, vertaling=z.vertaling, bron="tatoeba", bron_id=z.id)
            for z in kies(kandidaten, weekwoorden, aantal, self.rng)
        ]
