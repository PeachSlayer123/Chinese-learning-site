"""Instellingen, gelezen uit omgevingsvariabelen of uit `.env` in de root van de repo."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _lijst(waarde: str) -> list[str]:
    return [deel.strip() for deel in waarde.split(",") if deel.strip()]


@dataclass
class Instellingen:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    # Dictees maken is een eenvoudige taak, dus standaard het goedkope Haiku-model (zie docs/plan.md).
    claude_model: str = field(default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-haiku-4-5"))
    # Een woordenlijst lezen uit een screenshot vraagt meer precisie: standaard Claude Opus.
    claude_model_herkenning: str = field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL_HERKENNING", "claude-opus-5-5")
    )
    database_pad: Path = field(
        default_factory=lambda: Path(os.getenv("DATABASE_PATH", REPO_ROOT / "data" / "app.db"))
    )
    # Waar dictee-zinnen vandaan komen, in volgorde van voorkeur. "tatoeba" = echte zinnen (gratis),
    # "ollama" = lokale AI op de desktop (gratis, alleen als OLLAMA_URL ingesteld is),
    # "claude" vult de rest aan (alleen als er een API-key is).
    zinnen_bronnen: list[str] = field(
        default_factory=lambda: _lijst(os.getenv("ZINNEN_BRONNEN", "tatoeba,ollama,claude"))
    )
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", ""))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3.5:9b"))
    # Wake-on-LAN voor de pc met Ollama (leeg = niet wekken). Werkt alleen als de container het
    # thuisnetwerk ziet (network_mode: host op de Pi).
    wol_mac: str = field(default_factory=lambda: os.getenv("WOL_MAC", ""))
    wol_broadcast: str = field(default_factory=lambda: os.getenv("WOL_BROADCAST", "255.255.255.255"))
    ollama_wektijd: float = field(default_factory=lambda: float(os.getenv("OLLAMA_WEKTIJD", "120")))
    tatoeba_pad: Path = field(
        default_factory=lambda: Path(
            os.getenv("TATOEBA_PAD", Path(__file__).with_name("data") / "tatoeba_cmn.tsv.gz")
        )
    )
    # Map met de gebouwde frontend (`npm run build`). Alleen gezet in Docker: dan serveert de backend
    # ook de site, zodat alles op één poort draait. Lokaal blijft dit leeg en draait Vite apart.
    frontend_map: Path | None = field(
        default_factory=lambda: Path(p) if (p := os.getenv("FRONTEND_DIR")) else None
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _lijst(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        )
    )


instellingen = Instellingen()
