"""Inlezen van een geüploade woordenlijst (CSV: hanzi,pinyin,betekenis)."""

import csv
import io
import re

VERPLICHTE_KOLOMMEN = ("hanzi", "pinyin", "betekenis")


class OngeldigeLijst(ValueError):
    pass


def week_uit_bestandsnaam(naam: str | None) -> int | None:
    """`week-03.csv` → 3. Geeft None als er geen weeknummer in staat."""
    if not naam:
        return None
    match = re.search(r"week[\s_-]*(\d+)", naam, re.IGNORECASE)
    return int(match.group(1)) if match else None


def lees_csv(inhoud: bytes) -> list[dict]:
    try:
        tekst = inhoud.decode("utf-8-sig")  # -sig: Excel zet soms een BOM vooraan
    except UnicodeDecodeError:
        raise OngeldigeLijst("Het bestand is geen geldige UTF-8-tekst. Sla de CSV op als UTF-8.")

    if not tekst.strip():
        raise OngeldigeLijst("Het bestand is leeg.")

    # Excel met Nederlandse instellingen gebruikt ';' als scheidingsteken.
    eerste_regel = tekst.splitlines()[0]
    scheiding = ";" if eerste_regel.count(";") > eerste_regel.count(",") else ","

    lezer = csv.DictReader(io.StringIO(tekst), delimiter=scheiding)
    kolommen = [(k or "").strip().lower() for k in (lezer.fieldnames or [])]
    ontbrekend = [k for k in VERPLICHTE_KOLOMMEN if k not in kolommen]
    if ontbrekend:
        raise OngeldigeLijst(
            f"Kolommen ontbreken: {', '.join(ontbrekend)}. "
            f"De eerste regel moet zijn: {','.join(VERPLICHTE_KOLOMMEN)}"
        )

    woorden = []
    for regelnr, rij in enumerate(lezer, start=2):
        rij = {(k or "").strip().lower(): (v or "").strip() for k, v in rij.items()}
        if not any(rij.get(k) for k in VERPLICHTE_KOLOMMEN):
            continue  # lege regel
        if not rij["hanzi"] or not rij["pinyin"]:
            raise OngeldigeLijst(f"Regel {regelnr}: hanzi en pinyin zijn verplicht.")
        woorden.append({k: rij[k] for k in VERPLICHTE_KOLOMMEN})

    if not woorden:
        raise OngeldigeLijst("Er staan geen woorden in de lijst.")
    return woorden
