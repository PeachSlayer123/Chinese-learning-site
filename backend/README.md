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
| `app/dictee.py` | Zinnen laten maken door Claude + controleren + opnieuw vragen; `GecombineerdeBron` (Tatoeba eerst, Claude vult aan) |
| `app/ollama.py` | Lokale AI (Ollama + Qwen op de desktop): pc wekken met Wake-on-LAN, zinnen met een tekenbeperking |
| `app/tatoeba.py` | Echte zinnen uit Tatoeba kiezen die volledig binnen de woordenschat vallen |
| `app/data/tatoeba_cmn.tsv.gz` | Tatoeba-zinnen (vereenvoudigd Chinees + NL/EN), gemaakt met `tools/tatoeba_bouw.py` |
| `app/pinyin.py` | Pinyin berekenen (eigen lijst eerst, anders `pypinyin`) en onbekende tekens zoeken |
| `app/config.py` | Instellingen uit `.env` |

## Hoe een dictee gemaakt wordt

1. Weekwoorden = woorden van de gekozen week; bekende woorden = alle weken met een lager nummer.
2. **Eerst Tatoeba**: echte zinnen waarvan elk teken in de woordenlijsten staat en die minstens één
   weekwoord bevatten. Zo veel mogelijk verschillende weekwoorden, vaak-foute woorden en zinnen met een
   Nederlandse vertaling krijgen voorrang (anders Engels, gemarkeerd met "(EN)").
3. **Lokale AI** (als `OLLAMA_URL` ingesteld is): Qwen via Ollama op de desktop maakt zinnen voor de
   weekwoorden die nog niet aan bod kwamen. Een JSON-schema met een `pattern` laat alleen gekende tekens
   toe. Slaapt de pc, dan wekt de backend hem (`WOL_MAC`) en wacht max. `OLLAMA_WEKTIJD` seconden.
   Gratis, maar de zinnen klinken soms onnatuurlijk (de app toont dat bij de zin).
4. **Claude vult de rest aan** (standaard `claude-haiku-4-5`). Faalt een bron (pc onbereikbaar, geen
   API-key, AI-fout), dan gaat het verder met de volgende, met een waarschuwing. Volgorde instelbaar met
   `ZINNEN_BRONNEN` (standaard `tatoeba,ollama,claude`).
5. De backend controleert elke zin: minstens één weekwoord, en geen tekens buiten de gekende woorden.
   Afgekeurde zinnen worden tot 2 keer opnieuw gevraagd; lukt het niet, dan komt er een waarschuwing.
6. De pinyin wordt door de backend berekend, niet door de AI.
7. Woorden die je eerder fout had (`PUT /api/dictees/{id}/resultaat`) gaan als extra instructie
   mee in de prompt (top 5 op `keer_fout`), zodat ze vaker terugkomen.

### Tatoeba-bestand opnieuw maken

Bron: [Tatoeba](https://tatoeba.org), licentie **CC BY 2.0 FR** (bronvermelding staat in de app en
bij elke zin). Download van <https://downloads.tatoeba.org/exports/per_language/> de bestanden
`cmn/cmn_sentences.tsv.bz2`, `nld/nld_sentences.tsv.bz2`, `eng/eng_sentences.tsv.bz2` en
`https://downloads.tatoeba.org/exports/links.tar.bz2` in één map, en dan (vanuit de repo-root):

```
python tools/tatoeba_bouw.py <map-met-downloads>
```

Dat schrijft `backend/app/data/tatoeba_cmn.tsv.gz` (alleen vereenvoudigde zinnen tot 40 tekens).

## Woordenlijst uit een screenshot

1. De afbeelding wordt gecontroleerd en zo nodig verkleind (Pillow).
2. Claude (standaard `claude-opus-5-5`, instelbaar met `CLAUDE_MODEL_HERKENNING`) geeft de woorden
   terug als JSON: alleen wat op de afbeelding staat.
3. Ontbrekende pinyin berekent de backend met `pypinyin`. Een ontbrekende betekenis vult de AI aan;
   beide komen als waarschuwing terug, zodat je ze kan nakijken.
4. Weigert het model de vraag (veiligheidsfilter), dan probeert de API automatisch een ander model
   (`fallbacks: "default"`).
