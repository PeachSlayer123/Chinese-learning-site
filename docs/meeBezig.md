# Mee bezig

Wat er nu gebeurt en waar we gebleven zijn. Backend en frontend worden tegelijk gebouwd
in twee terminals (zie [`samenwerking.md`](samenwerking.md)). **Elke kant werkt alleen zijn eigen sectie bij.**

## Backend (terminal 1, worktree `../Chinees-backend`, branch `backend`)

### Nu bezig
- ⏸️ Niets. Wacht op de volgende taak of op feedback van de frontend.

### Hierna
- Prompts bijsturen op basis van echte woordenlijsten van de gebruiker
- Printversie van een dictee (frontend of backend, nog afspreken)

### Klaar
- 2026-10-02: Resultaat wissen met `{"zinnen": []}` (vraag van de frontend)
- 2026-10-02: Dictee-resultaat: `PUT /api/dictees/{id}/resultaat`, `Woord.keer_fout`,
  `Dictee.resultaat`, `DicteeSamenvatting.aantal_goed`. Vaak foute woorden gaan mee in de prompt.
  Fix: een week vervangen verwijderde ook haar dictees. 34 tests
- 2026-10-02: `/api/weken/herken` accepteert ook CSV (één voorbeeldpad voor de frontend). 21 tests.
  Screenshot-herkenning getest met de echte API (4/4 woorden en het weeknummer goed gelezen)
- 2026-10-02: Woordenlijst uploaden als screenshot/foto (`POST /api/weken` met afbeelding,
  `POST /api/weken/herken`, `PUT /api/weken/{nummer}`). 20 tests
- 2026-10-02: Basis-backend: upload/opvragen/verwijderen van weken, woorden, dictees genereren
  via Claude met controle en pinyin via `pypinyin`. 10 tests (`backend/README.md`)
- 2026-10-02: API-contract (`docs/api.md`) en samenwerkingsafspraken (`docs/samenwerking.md`)
- 2026-10-02: Backend-stack gekozen: Python + FastAPI + SQLite

## Frontend (terminal 2, hoofdmap)

### Nu bezig
- ⏸️ Niets. Volgende sessie: start bij "Hierna".

### Hierna
- Grondig nakijken in Chrome (gsm- en computerbreedte, licht/donker) met de Claude-extensie en de
  lus uit `werkwijze.md` §4. Dat is nog niet gebeurd; de gebruiker heeft de app wel zelf geprobeerd ("werkt redelijk prima")
- Lijst van eerdere dictees per week tonen (`GET /api/dictees?week=N` geeft al `aantal_goed`)
- Printversie van een dictee (alleen pinyin + genummerde lijnen); afspreken met de backend
- PWA (installeerbaar op de gsm)
- Eventueel: stijl overnemen van een site die de gebruiker mooi vindt (via Chrome)

### Klaar
- 2026-10-02: Alles uitvinken wist het resultaat (`{"zinnen": []}`)
- 2026-10-02: Dictee-resultaat gekoppeld: goed/fout per zin en foute woorden aanduiden worden opgeslagen
  (`PUT /api/dictees/{id}/resultaat`), resultaat wordt teruggezet bij het laden, `keer_fout` in de woordentabel bij Weken
- 2026-10-02: Frontend-basis in `frontend/` (Svelte 5 + Vite, JavaScript): tabbladen Dictee / Weken / Uploaden
  gekoppeld aan de echte API, ontwerp volgens het klikbare prototype (田字格-vakjes). Zie `frontend/README.md`

## Open punten voor de volgende sessie (eerst bespreken met de gebruiker)
- **API-key op de laptop:** `.env` bestaat daar nog niet. Claude zegt dit expliciet aan het begin van de sessie,
  en de gebruiker maakt `.env` aan (zie `docs/opstarten.md`, stap 3)
- **Data op meerdere toestellen:** `data/app.db` staat alleen op de pc. Een oplossing zoeken zodat de woordenlijsten
  overal hetzelfde zijn. Opties om te bespreken: de backend vroeg op de Raspberry Pi zetten (één server, bereikbaar
  via Tailscale), of tijdelijk `app.db` meekopiëren of synchroniseren (USB, cloudmap).
  Voorkeur van de gebruiker: een eigen "cloud" thuis op de Pi die de data bijhoudt en de site live zet (zie `ideeen.md`)

## Algemeen klaar
- 2026-10-02: Laptop getest: backend op poort 8001 + frontend starten werkt, app laadt in Chrome zonder
  console-fouten, "AI beschikbaar" (key werkt). `app.db` op de laptop is nog leeg (geen woordenlijsten)
- 2026-10-02: Laptop opgezet in `C:\Users\alexc\FASE3\Chinees` (Python 3.14.3, Node 22.19 in `PATH`):
  backend-venv + `npm install`. 34 tests groen, frontend bouwt. `.env` en `app.db` ontbreken daar nog
- 2026-10-01: Repo-structuur en docs opgezet

## Notities / problemen
- Opstarten op een nieuw toestel en elke dag: [`opstarten.md`](opstarten.md)
- `.env` (API-key) en `data/app.db` (alle woordenlijsten en dictees) staan **niet** in git.
  Op een ander toestel: opnieuw een `.env` maken en `app.db` meekopiëren als je je data wilt houden
- Op de eerste pc staat Node in `D:\` (`D:\node.exe`). Terminals die vóór de installatie gestart zijn, vinden het niet
- **Laptop: poort 8000 is door Windows gereserveerd** (WinError 10013, geen admin). Daar de backend op `--port 8001`
  draaien en de frontend met `API_URL=http://localhost:8001 npm run dev` starten. `.env` staat er nu wel (key werkt)
- `uvicorn --reload` laadt nieuwe backend-code soms niet; dan de backend helemaal herstarten
- De eerste API-key (`sk-ant-usr-…dgAA`) werkte niet (geen workspace) en staat in een chatgesprek: intrekken in de Console
