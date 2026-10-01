# Mee bezig

Wat er nu gebeurt en waar we gebleven zijn. Backend en frontend worden tegelijk gebouwd
in twee terminals (zie [`samenwerking.md`](samenwerking.md)). **Elke kant werkt alleen zijn eigen sectie bij.**

## Backend (terminal 1, worktree `../Chinees-backend`, branch `backend`)

### Nu bezig
- ⏸️ Niets: screenshot-upload is klaar en gemerged. Wacht op feedback van de frontend.

### Hierna
- Prompts bijsturen op basis van echte woordenlijsten van de gebruiker
- `POST /api/dictees/{id}/resultaat`: fouten bijhouden (fase 1, optioneel)
- Printversie van een dictee (frontend of backend, nog afspreken)

### Klaar
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
- (vult de frontend-terminal zelf in)

### Klaar
-

## Algemeen klaar
- 2026-10-01: Repo-structuur en docs opgezet

## Notities / problemen
-
