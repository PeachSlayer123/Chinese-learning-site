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
    database_pad: Path = field(
        default_factory=lambda: Path(os.getenv("DATABASE_PATH", REPO_ROOT / "data" / "app.db"))
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _lijst(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
        )
    )


instellingen = Instellingen()
