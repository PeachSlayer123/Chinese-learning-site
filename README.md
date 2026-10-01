# Chinese-learning-site

Een persoonlijke webapp om Chinees te leren, vooral de woordjes die ik elke week moet kennen.
De app draait later op mijn Raspberry Pi en gebruikt de Claude API als ingebouwde AI-tutor.

## Wat de app moet kunnen

1. **Woordenlijst per week uploaden** (bv. een CSV-bestand met hanzi, pinyin en betekenis).
2. **Dictee maken:** de AI maakt zinnen met de woordjes van deze week, eventueel aangevuld met woorden die ik al ken.
   De app toont alleen de **pinyin**. Ik schrijf de karakters op papier.
3. **Oplossing checken:** daarna toont de app de zinnen in karakters (hanzi), met vertaling.
4. Later: meer leeropties met AI (flashcards, gesprekken, uitleg, ...).

Zie [`docs/plan.md`](docs/plan.md) voor het volledige plan.

## Mappenstructuur

```
.
├── backend/           # API-server: woordenlijsten, dictees, praat met Claude
├── frontend/          # Webinterface (later als PWA ook op gsm)
├── data/
│   └── woordenlijsten/  # Woordenlijsten per week (+ voorbeeldformaat)
├── deploy/            # Alles voor het hosten op de Raspberry Pi
├── docs/
│   ├── plan.md        # Doelen, features, roadmap
│   ├── ideeen.md      # Losse ideeën voor later
│   └── meeBezig.md    # Waar ik nu mee bezig ben
├── .env.example       # Voorbeeld van de nodige omgevingsvariabelen
└── CLAUDE.md          # Context voor Claude Code
```

## Aan de slag

> De tech stack ligt nog niet vast, dus de opstartinstructies volgen later.

1. Kopieer `.env.example` naar `.env` en vul je eigen Claude API-key in.
2. **Commit `.env` nooit.** Hij staat al in `.gitignore`.

## Veiligheid

- De Claude API-key staat **alleen in de backend**, nooit in de frontend.
- Zet de Pi niet rechtstreeks open op internet. Gebruik Tailscale of een Cloudflare Tunnel met login (zie `deploy/`).
- Zet een maandelijkse uitgavenlimiet in de Anthropic Console.
