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
- 2026-10-02: Frontend-basis in `frontend/` (Svelte 5 + Vite, JavaScript): tabbladen Dictee / Weken / Uploaden
  gekoppeld aan de echte API, ontwerp volgens het prototype (田字格-vakjes).
  Code staat erin en bouwt; alle API-calls getest via de Vite-proxy. **Nog te doen:** nakijken in Chrome
  (wacht op Claude in Chrome na een herstart van de terminal)
- 2026-10-02: Dictee-resultaat gekoppeld: goed/fout per zin en foute woorden aanduiden worden opgeslagen
  (`PUT /api/dictees/{id}/resultaat`), resultaat wordt teruggezet bij het laden, `keer_fout` in de woordentabel bij Weken

### Klaar
-

## Algemeen klaar
- 2026-10-01: Repo-structuur en docs opgezet

## Notities / problemen
-
