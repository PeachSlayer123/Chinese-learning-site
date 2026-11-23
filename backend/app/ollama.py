"""Lokale AI: Ollama + Qwen op de desktop (GTX 1080), bereikbaar via Tailscale.

Gratis, maar de desktop slaapt meestal. Daarom: eerst kijken of Ollama antwoordt; zo niet, de pc
wekken met Wake-on-LAN (als `WOL_MAC` ingesteld is) en wachten tot Ollama er is.

Qwen gebruikt zonder beperking te veel tekens die de leerling niet kent. Daarom krijgt `hanzi` in het
JSON-schema een `pattern` met enkel de gekende tekens + leestekens: zo kan het model niets anders
schrijven (getest 23/11/2026: 10/10 geldig, maar ongeveer de helft klinkt onnatuurlijk).
"""

from __future__ import annotations

import json
import socket
import time

import httpx

from .dictee import SYSTEEMPROMPT, AIFout, RuweZin, maak_vraag

LEESTEKENS = "，。？！"


def is_hanzi(c: str) -> bool:
    return "一" <= c <= "鿿" or "㐀" <= c <= "䶿"


def stuur_magic_packet(mac: str, broadcast: str = "255.255.255.255", poort: int = 9) -> None:
    """Wake-on-LAN: 6x 0xFF + 16x het MAC-adres, als UDP-broadcast."""
    adres = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    if len(adres) != 6:
        raise ValueError(f"Ongeldig MAC-adres: {mac}")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(b"\xff" * 6 + adres * 16, (broadcast, poort))


def schema(toegelaten: str) -> dict:
    """JSON-schema voor Ollama: `hanzi` mag alleen de toegelaten tekens bevatten."""
    return {
        "type": "object",
        "properties": {
            "zinnen": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "hanzi": {"type": "string", "pattern": f"^[{toegelaten}]{{4,20}}$"},
                        "vertaling": {"type": "string", "maxLength": 120},  # anders soms een heel verhaal
                    },
                    "required": ["hanzi", "vertaling"],
                },
            }
        },
        "required": ["zinnen"],
    }


class OllamaZinnenBron:
    naam = "ollama"

    def __init__(
        self,
        url: str,
        model: str,
        wol_mac: str = "",
        wol_broadcast: str = "255.255.255.255",
        wektijd: float = 120,
        client: httpx.Client | None = None,
        slaap=time.sleep,
        wek=stuur_magic_packet,
    ):
        self.url = url.rstrip("/")
        self.model = model
        self.wol_mac = wol_mac
        self.wol_broadcast = wol_broadcast
        self.wektijd = wektijd
        self.client = client or httpx.Client(timeout=httpx.Timeout(180.0, connect=3.0))
        self.slaap = slaap
        self.wek = wek
        self.fout: str | None = None  # na één mislukte poging niet bij elke ronde opnieuw wachten

    def _antwoordt(self) -> bool:
        try:
            return self.client.get(f"{self.url}/api/tags", timeout=3.0).status_code == 200
        except httpx.HTTPError:
            return False

    def _zorg_dat_wakker(self) -> None:
        if self._antwoordt():
            return
        if not self.wol_mac:
            raise AIFout("De pc met de lokale AI staat uit of slaapt.")
        self.wek(self.wol_mac, self.wol_broadcast)
        gewacht = 0.0
        while gewacht < self.wektijd:
            self.slaap(5)
            gewacht += 5
            if self._antwoordt():
                return
        raise AIFout(f"De pc met de lokale AI werd gewekt, maar antwoordt na {self.wektijd:.0f} s nog niet.")

    def maak_zinnen(
        self, weekwoorden: list[dict], bekende_woorden: list[dict], aantal: int, opmerking: str = ""
    ) -> list[RuweZin]:
        if self.fout:
            raise AIFout(self.fout)
        try:
            return self._maak_zinnen(weekwoorden, bekende_woorden, aantal, opmerking)
        except AIFout as e:
            self.fout = str(e)
            raise

    def _maak_zinnen(self, weekwoorden, bekende_woorden, aantal, opmerking) -> list[RuweZin]:
        self._zorg_dat_wakker()
        tekens = sorted({c for w in weekwoorden + bekende_woorden for c in w["hanzi"] if is_hanzi(c)})
        body = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": schema("".join(tekens) + LEESTEKENS),
            "options": {"temperature": 0.7},
            "messages": [
                {"role": "system", "content": SYSTEEMPROMPT},
                {"role": "user", "content": maak_vraag(weekwoorden, bekende_woorden, aantal, opmerking)},
            ],
        }
        try:
            r = self.client.post(f"{self.url}/api/chat", json=body)
            r.raise_for_status()
            zinnen = json.loads(r.json()["message"]["content"])["zinnen"]
        except httpx.TimeoutException as e:
            raise AIFout("De lokale AI antwoordt te traag.") from e
        except httpx.HTTPError as e:
            raise AIFout(f"De lokale AI gaf een fout: {e}") from e
        except (KeyError, ValueError, TypeError) as e:
            raise AIFout("De lokale AI gaf geen bruikbaar antwoord.") from e
        return [
            RuweZin(hanzi=z["hanzi"], vertaling=z["vertaling"], bron="ollama")
            for z in zinnen
            if isinstance(z, dict) and z.get("hanzi") and z.get("vertaling")
        ][:aantal]
