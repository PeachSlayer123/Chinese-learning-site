"""Woordenlijst herkennen uit een screenshot of foto, met Claude (vision).

De AI leest alleen over wat op de afbeelding staat. Ontbrekende pinyin berekent de backend zelf
(`pypinyin`, zie CLAUDE.md); een ontbrekende betekenis vult de AI aan, met een waarschuwing.
"""

import base64
import io
from pathlib import Path
from typing import Protocol

import anthropic
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel
from pypinyin import Style, lazy_pinyin

from .dictee import AIFout

AFBEELDING_EXTENSIES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic", ".heif", ".bmp"}
API_FORMATEN = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp", "GIF": "image/gif"}
MAX_ZIJDE = 2576  # langste zijde in pixels; meer heeft het model niet nodig
MAX_BYTES = 3_500_000  # ruim onder de API-limiet van 5 MB per afbeelding
MAX_UPLOAD_BYTES = 20_000_000


class OngeldigeAfbeelding(ValueError):
    pass


class HerkendWoord(BaseModel):
    hanzi: str
    pinyin: str  # "" als er geen pinyin op de afbeelding staat
    betekenis: str
    betekenis_door_ai: bool  # True als de betekenis niet op de afbeelding stond


class HerkendeLijst(BaseModel):
    week: int | None  # weeknummer als dat op de afbeelding staat
    woorden: list[HerkendWoord]
    opmerking: str  # bv. onleesbare stukken; "" als alles duidelijk was


class LijstHerkenner(Protocol):
    def herken(self, afbeelding: bytes, media_type: str) -> HerkendeLijst: ...


SYSTEEMPROMPT = """\
Je zet een foto of screenshot van een Chinese woordenlijst om naar gestructureerde data.
De lijst is van een Nederlandstalige leerling Chinees.

Regels:
- Neem elk woord van de lijst over, in de volgorde van de afbeelding. Sla titels, nummers en
  kolomkoppen over.
- "hanzi": de karakters precies zoals ze er staan (vereenvoudigd of traditioneel, niet omzetten).
- "pinyin": zoals op de afbeelding, met toontekens (zet toonnummers zoals "ni3" om naar "nǐ").
  Staat er geen pinyin bij een woord, geef dan "". Verzin geen pinyin.
- "betekenis": zoals op de afbeelding, in de taal van de lijst. Staat er geen betekenis bij,
  geef dan zelf een korte Nederlandse betekenis en zet "betekenis_door_ai" op true.
- "week": het weeknummer als dat duidelijk op de afbeelding staat (bv. "Week 3", "第三周"), anders null.
- "opmerking": korte uitleg in het Nederlands als iets onleesbaar of twijfelachtig was, anders "".
- Staat er geen Chinese woordenlijst op de afbeelding, geef dan een lege lijst en leg het uit in "opmerking"."""


def is_afbeelding(bestandsnaam: str | None, content_type: str | None) -> bool:
    if content_type and content_type.startswith("image/"):
        return True
    return Path(bestandsnaam or "").suffix.lower() in AFBEELDING_EXTENSIES


def bereid_afbeelding_voor(inhoud: bytes) -> tuple[bytes, str]:
    """Controleert de afbeelding en verkleint ze indien nodig. Geeft (bytes, media_type) terug."""
    if len(inhoud) > MAX_UPLOAD_BYTES:
        raise OngeldigeAfbeelding("De afbeelding is te groot (max. 20 MB).")
    try:
        img = Image.open(io.BytesIO(inhoud))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise OngeldigeAfbeelding(
            "Dit afbeeldingsformaat wordt niet ondersteund. Gebruik PNG, JPG of WEBP "
            "(iPhone: zet de camera op 'Meest compatibel' of maak een screenshot)."
        )

    if img.format in API_FORMATEN and len(inhoud) <= MAX_BYTES and max(img.size) <= MAX_ZIJDE:
        return inhoud, API_FORMATEN[img.format]

    img = ImageOps.exif_transpose(img)  # foto's van een gsm staan soms gedraaid
    img.thumbnail((MAX_ZIJDE, MAX_ZIJDE))
    uit = io.BytesIO()
    img.convert("RGB").save(uit, format="JPEG", quality=90)
    return uit.getvalue(), "image/jpeg"


class ClaudeLijstHerkenner:
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
        self.model = model

    def herken(self, afbeelding: bytes, media_type: str) -> HerkendeLijst:
        try:
            antwoord = self.client.beta.messages.parse(
                model=self.model,
                max_tokens=16000,
                system=SYSTEEMPROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64.standard_b64encode(afbeelding).decode("ascii"),
                                },
                            },
                            {"type": "text", "text": "Zet deze woordenlijst om."},
                        ],
                    }
                ],
                output_format=HerkendeLijst,
                output_config={"effort": "medium"},
                # Weigert het model (veiligheidsfilter), dan probeert de API een ander model.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError as e:
            raise AIFout("De AI krijgt even te veel vragen. Probeer het zo opnieuw.") from e
        except anthropic.APIStatusError as e:
            raise AIFout(f"De AI gaf een fout ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise AIFout("Geen verbinding met de AI. Check de internetverbinding.") from e

        if antwoord.stop_reason == "refusal" or antwoord.parsed_output is None:
            raise AIFout(f"De AI kon de afbeelding niet verwerken (stop_reason: {antwoord.stop_reason}).")
        return antwoord.parsed_output


def verwerk_herkenning(lijst: HerkendeLijst) -> tuple[list[dict], list[str]]:
    """Maakt van de AI-uitvoer woorden in hetzelfde formaat als de CSV, plus waarschuwingen."""
    woorden: list[dict] = []
    berekende_pinyin, ai_betekenis = [], []
    for w in lijst.woorden:
        hanzi = w.hanzi.strip()
        if not hanzi or any(bestaand["hanzi"] == hanzi for bestaand in woorden):
            continue
        pinyin = w.pinyin.strip()
        if not pinyin:
            pinyin = "".join(lazy_pinyin(hanzi, style=Style.TONE))
            berekende_pinyin.append(hanzi)
        if w.betekenis_door_ai:
            ai_betekenis.append(hanzi)
        woorden.append({"hanzi": hanzi, "pinyin": pinyin, "betekenis": w.betekenis.strip()})

    waarschuwingen = []
    if lijst.opmerking.strip():
        waarschuwingen.append(f"AI: {lijst.opmerking.strip()}")
    if berekende_pinyin:
        waarschuwingen.append(
            f"Geen pinyin op de afbeelding, automatisch berekend voor: {' '.join(berekende_pinyin)}"
        )
    if ai_betekenis:
        waarschuwingen.append(
            f"Geen betekenis op de afbeelding, aangevuld door de AI voor: {' '.join(ai_betekenis)}"
        )
    return woorden, waarschuwingen
