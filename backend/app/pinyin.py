"""Pinyin en controle van zinnen.

De pinyin komt niet van de AI (zie CLAUDE.md): woorden uit de eigen lijsten krijgen de pinyin
uit die lijst, de rest wordt berekend met `pypinyin`.
"""

from pypinyin import Style, lazy_pinyin

LEESTEKENS = {
    "。": ".", "，": ",", "、": ",", "？": "?", "！": "!", "：": ":", "；": ";",
    "“": '"', "”": '"', "‘": "'", "’": "'", "（": "(", "）": ")", "…": "...",
}
GEEN_SPATIE_ERVOOR = {".", ",", "?", "!", ":", ";", ")", "..."}


def is_hanzi(teken: str) -> bool:
    return "一" <= teken <= "鿿" or "㐀" <= teken <= "䶿"


def segmenteer(zin: str, woordenboek: dict[str, str]) -> list[tuple[str, str | None]]:
    """Knipt een zin in stukken: (tekst, pinyin uit lijst) of (tekst, None) als onbekend.

    Gulzig: op elke positie het langste woord uit het woordenboek.
    """
    max_lengte = max((len(w) for w in woordenboek), default=1)
    stukken: list[tuple[str, str | None]] = []
    i = 0
    while i < len(zin):
        for lengte in range(min(max_lengte, len(zin) - i), 0, -1):
            kandidaat = zin[i : i + lengte]
            if kandidaat in woordenboek:
                stukken.append((kandidaat, woordenboek[kandidaat]))
                i += lengte
                break
        else:
            stukken.append((zin[i], None))
            i += 1
    return stukken


def zin_naar_pinyin(zin: str, woordenboek: dict[str, str]) -> str:
    """'我在学习中文。' → 'Wǒ zài xuéxí zhōngwén.'"""
    tokens: list[str] = []
    onbekend = ""  # opeenvolgende onbekende hanzi samen aan pypinyin geven (betere klanken)

    def spoel_onbekend() -> None:
        nonlocal onbekend
        if onbekend:
            tokens.extend(lazy_pinyin(onbekend, style=Style.TONE))
            onbekend = ""

    for tekst, pinyin in segmenteer(zin, woordenboek):
        if pinyin is not None:
            spoel_onbekend()
            tokens.append(pinyin)
        elif is_hanzi(tekst):
            onbekend += tekst
        else:
            spoel_onbekend()
            tokens.append(LEESTEKENS.get(tekst, tekst))
    spoel_onbekend()

    resultaat = ""
    for token in tokens:
        if not token.strip():
            continue
        if resultaat and token not in GEEN_SPATIE_ERVOOR and not resultaat.endswith("("):
            resultaat += " "
        resultaat += token
    return resultaat[:1].upper() + resultaat[1:]


def onbekende_tekens(zin: str, bekende_woorden: list[str]) -> list[str]:
    """Hanzi in de zin die in geen enkel gekend woord voorkomen (zonder dubbels, in volgorde)."""
    gekend = {teken for woord in bekende_woorden for teken in woord}
    gezien: list[str] = []
    for teken in zin:
        if is_hanzi(teken) and teken not in gekend and teken not in gezien:
            gezien.append(teken)
    return gezien


def gebruikte_woorden(zin: str, woorden: list[str]) -> list[str]:
    return [w for w in woorden if w in zin]
