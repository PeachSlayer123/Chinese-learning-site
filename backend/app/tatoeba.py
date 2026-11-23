"""Zinnen uit Tatoeba (https://tatoeba.org): echte, door mensen nagekeken zinnen.

Bron en licentie: Tatoeba, CC BY 2.0 FR (bronvermelding verplicht, zie README en de app).
Het bestand `data/tatoeba_cmn.tsv.gz` bevat de vereenvoudigde Mandarijnse zinnen met een Nederlandse
en/of Engelse vertaling. Opnieuw maken: `tools/tatoeba_bouw.py` (zie backend/README.md).

Een zin is bruikbaar als al zijn hanzi in de woordenlijsten tot en met deze week voorkomen
(dezelfde controle als bij de AI-zinnen) en hij minstens één woord van deze week bevat.
"""

from __future__ import annotations

import csv
import math
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
    alleen_nieuw: bool = False,
) -> list[TatoebaZin]:
    """Kiest `aantal` zinnen zodat zoveel mogelijk weekwoorden aan bod komen.

    Volgorde van voorkeur per stap: dekt nog niet geoefende weekwoorden (2 of meer telt even zwaar),
    bevat een woord dat vaak fout was (`keer_fout`), heeft een Nederlandse vertaling. Daarna beslist het
    toeval (lichte voorkeur voor korte zinnen), zodat elk dictee andere zinnen krijgt.

    `alleen_nieuw`: stoppen zodra geen enkele zin nog een nieuw weekwoord oefent. De rest gaat dan
    naar de volgende bron (lokale AI/Claude), die vooral de niet-geoefende woorden (namen, getallen)
    krijgt.
    """
    rng = rng or random.Random()
    toeval = {id(z): rng.random() / (1 + len(z.hanzi) / 20) for z in kandidaten}
    fout = {w["hanzi"] for w in weekwoorden if w.get("keer_fout")}
    weekhanzi = [w["hanzi"] for w in weekwoorden]
    woorden_in = {id(z): pinyin.gebruikte_woorden(z.hanzi, weekhanzi) for z in kandidaten}
    pool = kandidaten[:]
    gekozen: list[TatoebaZin] = []
    gedekt: set[str] = set()
    gezien_hanzi: set[str] = set()
    while pool and len(gekozen) < aantal:

        def nieuw(z: TatoebaZin) -> int:
            return len([w for w in woorden_in[id(z)] if w not in gedekt])

        def score(z: TatoebaZin) -> tuple:
            met_fout = any(w in fout for w in woorden_in[id(z)])
            return (min(nieuw(z), 2), met_fout, bool(z.nl), toeval[id(z)])

        beste = max(pool, key=score)
        if alleen_nieuw and nieuw(beste) == 0:
            break
        pool.remove(beste)
        if beste.hanzi in gezien_hanzi:
            continue
        gezien_hanzi.add(beste.hanzi)
        gekozen.append(beste)
        gedekt.update(woorden_in[id(beste)])
    return gekozen


class TatoebaZinnenBron:
    """ZinnenBron die alleen zinnen teruggeeft die volledig binnen de woordenschat vallen.

    `maak_zinnen` geeft alleen zinnen die nieuwe weekwoorden oefenen (kan dus minder zijn dan gevraagd);
    de `GecombineerdeBron` vraagt de rest aan de volgende bron en roept op het einde `vul_aan` op als
    er nog plaatsen over zijn. Zinnen uit `vermijden` (bv. uit de vorige dictees van deze week) komen
    alleen terug als er niets anders is.
    """

    naam = "tatoeba"

    def __init__(
        self,
        pad: Path = STANDAARD_PAD,
        rng: random.Random | None = None,
        vermijden: set[str] | None = None,
    ):
        self.zinnen = laad(pad)
        self.rng = rng or random.Random()
        self.vermijden: set[str] = set(vermijden or ())
        self.gegeven: set[str] = set()
        # Gezet door GecombineerdeBron als er nog een bron na Tatoeba komt: dan blijft ± 1/3 van de
        # zinnen vrij voor weekwoorden die in geen enkele Tatoeba-zin passen (namen, getallen, ...).
        self.laat_ruimte = False

    def _kies(self, weekwoorden, bekende_woorden, aantal, alleen_nieuw, met_vermeden) -> list[RuweZin]:
        weekhanzi = [w["hanzi"] for w in weekwoorden]
        alle_hanzi = weekhanzi + [w["hanzi"] for w in bekende_woorden]
        bruikbaar = bruikbare_zinnen(self.zinnen, weekhanzi, alle_hanzi)
        if alleen_nieuw and self.laat_ruimte:
            onvindbaar = [h for h in weekhanzi if not any(h in z.hanzi for z in bruikbaar)]
            aantal -= min(math.ceil(aantal / 3), len(onvindbaar))
        weg = self.gegeven if met_vermeden else self.gegeven | self.vermijden
        kandidaten = [z for z in bruikbaar if z.hanzi not in weg]
        gekozen = kies(kandidaten, weekwoorden, max(aantal, 0), self.rng, alleen_nieuw=alleen_nieuw)
        self.gegeven.update(z.hanzi for z in gekozen)
        return [
            RuweZin(hanzi=z.hanzi, vertaling=z.vertaling, bron="tatoeba", bron_id=z.id) for z in gekozen
        ]

    def maak_zinnen(
        self, weekwoorden: list[dict], bekende_woorden: list[dict], aantal: int, opmerking: str = ""
    ) -> list[RuweZin]:
        return self._kies(weekwoorden, bekende_woorden, aantal, alleen_nieuw=True, met_vermeden=False)

    def vul_aan(self, weekwoorden: list[dict], bekende_woorden: list[dict], aantal: int) -> list[RuweZin]:
        """Laatste redmiddel: ook zinnen zonder nieuw weekwoord, en desnoods uit vorige dictees."""
        zinnen = self._kies(weekwoorden, bekende_woorden, aantal, alleen_nieuw=False, met_vermeden=False)
        if len(zinnen) < aantal:
            zinnen += self._kies(
                weekwoorden, bekende_woorden, aantal - len(zinnen), alleen_nieuw=False, met_vermeden=True
            )
        return zinnen
