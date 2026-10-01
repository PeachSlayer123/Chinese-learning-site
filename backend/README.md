# Backend

De API-server van de app: Python + **FastAPI** + **SQLite**.
De enige plek waar de Claude API-key gebruikt wordt.

Het contract met de frontend staat in [`docs/api.md`](../docs/api.md).

## Starten (Windows, vanuit `backend/`)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000/api/health>
- Interactieve docs (alle endpoints uitproberen): <http://localhost:8000/docs>
- De API-key en andere instellingen komen uit `.env` in de root van de repo (zie `.env.example`).
  Zonder key werkt alles behalve dictees genereren (`503`).
- De database komt standaard in `data/app.db` (staat in `.gitignore`).

## Tests

```powershell
.venv\Scripts\python -m pytest
```

De tests gebruiken een nep-AI, dus ze kosten geen API-tegoed.

## Opbouw

| Bestand | Wat |
|---|---|
| `app/main.py` | Endpoints (FastAPI) |
| `app/db.py` | SQLite-tabellen en queries |
| `app/woordenlijst.py` | CSV inlezen (ook `;`-CSV uit Excel) |
| `app/herkenning.py` | Woordenlijst lezen uit een screenshot/foto met Claude (vision) |
| `app/dictee.py` | Zinnen laten maken door Claude + controleren + opnieuw vragen |
| `app/pinyin.py` | Pinyin berekenen (eigen lijst eerst, anders `pypinyin`) en onbekende tekens zoeken |
| `app/config.py` | Instellingen uit `.env` |

## Hoe een dictee gemaakt wordt

1. Weekwoorden = woorden van de gekozen week; bekende woorden = alle weken met een lager nummer.
2. Claude (standaard `claude-haiku-4-5`) geeft zinnen terug als JSON (`hanzi` + `vertaling`).
3. De backend controleert elke zin: minstens één weekwoord, en geen tekens buiten de gekende woorden.
   Afgekeurde zinnen worden tot 2 keer opnieuw gevraagd; lukt het niet, dan komt er een waarschuwing.
4. De pinyin wordt door de backend berekend, niet door de AI.

## Woordenlijst uit een screenshot

1. De afbeelding wordt gecontroleerd en zo nodig verkleind (Pillow).
2. Claude (standaard `claude-opus-5-5`, instelbaar met `CLAUDE_MODEL_HERKENNING`) geeft de woorden
   terug als JSON: alleen wat op de afbeelding staat.
3. Ontbrekende pinyin berekent de backend met `pypinyin`. Een ontbrekende betekenis vult de AI aan;
   beide komen als waarschuwing terug, zodat je ze kan nakijken.
4. Weigert het model de vraag (veiligheidsfilter), dan probeert de API automatisch een ander model
   (`fallbacks: "default"`).
