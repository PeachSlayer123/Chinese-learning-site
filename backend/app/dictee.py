"""Dictee genereren: Claude maakt zinnen, de backend controleert ze en berekent de pinyin."""

from typing import Protocol

import anthropic
from pydantic import BaseModel

from . import pinyin

MAX_EXTRA_RONDES = 2  # hoe vaak we zinnen die de controle niet halen opnieuw vragen


class RuweZin(BaseModel):
    hanzi: str
    vertaling: str


class ZinnenAntwoord(BaseModel):
    zinnen: list[RuweZin]


class AIFout(RuntimeError):
    """De AI-call is mislukt (netwerk, rate limit, ongeldig antwoord, ...)."""


class ZinnenBron(Protocol):
    def maak_zinnen(
        self, weekwoorden: list[dict], bekende_woorden: list[dict], aantal: int, opmerking: str
    ) -> list[RuweZin]: ...


SYSTEEMPROMPT = """\
Je maakt dictee-zinnen voor een Nederlandstalige leerling Chinees (vereenvoudigde karakters).
De leerling hoort/ziet alleen de pinyin en schrijft de karakters op papier, dus de zinnen moeten
binnen zijn woordenschat blijven.

Regels:
- Elke zin bevat minstens één woord uit "Woorden van deze week". Verdeel de weekwoorden over de
  zinnen zodat ze allemaal minstens één keer voorkomen.
- Gebruik verder zoveel mogelijk alleen woorden uit "Woorden die de leerling al kent".
  Lukt dat niet, gebruik dan alleen heel eenvoudige basiswoorden (HSK 1), zo weinig mogelijk.
- Korte, natuurlijke zinnen (4 tot 12 karakters), met Chinese leestekens.
- "vertaling" is een natuurlijke Nederlandse vertaling.
- Geef alleen de gevraagde JSON terug."""


def _woordregels(woorden: list[dict]) -> str:
    return "\n".join(f"- {w['hanzi']} ({w['pinyin']}): {w['betekenis']}" for w in woorden) or "(geen)"


class ClaudeZinnenBron:
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key, timeout=60.0)
        self.model = model

    def maak_zinnen(
        self, weekwoorden: list[dict], bekende_woorden: list[dict], aantal: int, opmerking: str = ""
    ) -> list[RuweZin]:
        vraag = (
            f"Woorden van deze week:\n{_woordregels(weekwoorden)}\n\n"
            f"Woorden die de leerling al kent:\n{_woordregels(bekende_woorden)}\n\n"
            f"Maak precies {aantal} zinnen."
        )
        if opmerking:
            vraag += f"\n\n{opmerking}"
        try:
            antwoord = self.client.messages.parse(
                model=self.model,
                max_tokens=4000,
                system=SYSTEEMPROMPT,
                messages=[{"role": "user", "content": vraag}],
                output_format=ZinnenAntwoord,
            )
        except anthropic.RateLimitError as e:
            raise AIFout("De AI krijgt even te veel vragen. Probeer het zo opnieuw.") from e
        except anthropic.APIStatusError as e:
            raise AIFout(f"De AI gaf een fout ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise AIFout("Geen verbinding met de AI. Check de internetverbinding.") from e

        if antwoord.stop_reason == "refusal" or antwoord.parsed_output is None:
            raise AIFout(f"De AI gaf geen bruikbaar antwoord (stop_reason: {antwoord.stop_reason}).")
        return antwoord.parsed_output.zinnen


def _controleer(zin: RuweZin, weekhanzi: list[str], bekende_hanzi: list[str]) -> list[str]:
    """Geeft een lijst problemen terug (leeg = zin is in orde)."""
    problemen = []
    if not pinyin.gebruikte_woorden(zin.hanzi, weekhanzi):
        problemen.append("bevat geen woord van deze week")
    onbekend = pinyin.onbekende_tekens(zin.hanzi, bekende_hanzi)
    if onbekend:
        problemen.append(f"bevat onbekende tekens: {' '.join(onbekend)}")
    return problemen


def genereer_dictee(
    bron: ZinnenBron, weekwoorden: list[dict], bekende_woorden: list[dict], aantal: int
) -> tuple[list[dict], list[str]]:
    """Maakt een dictee. Geeft (zinnen, waarschuwingen) terug in de vorm van docs/api.md.

    `bekende_woorden` = woorden van vorige weken (zonder de weekwoorden zelf).
    """
    weekhanzi = [w["hanzi"] for w in weekwoorden]
    alle_woorden = weekwoorden + bekende_woorden
    alle_hanzi = [w["hanzi"] for w in alle_woorden]
    woordenboek = {w["hanzi"]: w["pinyin"] for w in alle_woorden}

    goed: list[RuweZin] = []
    beste_afgekeurde: list[RuweZin] = []
    opmerking = ""

    for _ in range(1 + MAX_EXTRA_RONDES):
        nodig = aantal - len(goed)
        if nodig <= 0:
            break
        afgekeurd = []
        for zin in bron.maak_zinnen(weekwoorden, bekende_woorden, nodig, opmerking):
            if any(zin.hanzi == g.hanzi for g in goed):
                continue
            (afgekeurd if _controleer(zin, weekhanzi, alle_hanzi) else goed).append(zin)
        if afgekeurd:
            beste_afgekeurde = afgekeurd
            redenen = "; ".join(
                f"'{z.hanzi}' {', '.join(_controleer(z, weekhanzi, alle_hanzi))}" for z in afgekeurd
            )
            opmerking = (
                f"Deze zinnen werden afgekeurd: {redenen}. "
                f"Maak nieuwe zinnen die wel aan de regels voldoen. "
                f"Deze zinnen heb je al (niet herhalen): {' / '.join(g.hanzi for g in goed) or '-'}"
            )

    # Na de extra rondes: aanvullen met de beste afgekeurde zinnen, met een waarschuwing.
    waarschuwingen = []
    zinnen_ruw = goed[:aantal] + beste_afgekeurde[: max(0, aantal - len(goed))]

    zinnen = []
    for nr, zin in enumerate(zinnen_ruw, start=1):
        onbekend = pinyin.onbekende_tekens(zin.hanzi, alle_hanzi)
        gebruikt = pinyin.gebruikte_woorden(zin.hanzi, weekhanzi)
        if onbekend:
            waarschuwingen.append(f"Zin {nr} bevat onbekende tekens: {' '.join(onbekend)}")
        if not gebruikt:
            waarschuwingen.append(f"Zin {nr} bevat geen woord van deze week")
        zinnen.append(
            {
                "nr": nr,
                "hanzi": zin.hanzi,
                "pinyin": pinyin.zin_naar_pinyin(zin.hanzi, woordenboek),
                "vertaling": zin.vertaling,
                "woorden_van_de_week": gebruikt,
                "onbekende_tekens": onbekend,
            }
        )

    if len(zinnen) < aantal:
        waarschuwingen.append(f"Er konden maar {len(zinnen)} van de {aantal} zinnen gemaakt worden.")
    niet_gebruikt = [h for h in weekhanzi if not any(h in z["hanzi"] for z in zinnen)]
    if niet_gebruikt:
        waarschuwingen.append(f"Niet geoefend in dit dictee: {' '.join(niet_gebruikt)}")

    return zinnen, waarschuwingen
