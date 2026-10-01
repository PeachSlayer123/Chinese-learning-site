# Samenwerking: twee terminals tegelijk

Backend en frontend worden tegelijk gebouwd, elk in een eigen Claude Code-sessie.

| | Backend | Frontend |
|---|---|---|
| Map | `D:\FASE-3\Chinees-backend` (git worktree) | `D:\FASE-3\Chinees` |
| Branch | `backend` | `main` (of een eigen `frontend`-branch) |
| Mag aanpassen | `backend/`, `.env.example`, `docs/api.md` | `frontend/` |

## Afspraken

1. **Blijf in je eigen map.** Backend raakt `frontend/` niet aan en omgekeerd.
   Zo zijn er geen merge-conflicten.
2. **Het contract is [`api.md`](api.md).** De frontend bouwt daartegen, ook als de backend
   nog niet af is (gebruik desnoods nepdata met dezelfde vorm).
3. **Contract wijzigen?** Pas `api.md` aan en stuur een bericht naar de andere sessie.
4. **Gedeelde docs** (`meeBezig.md`, `plan.md`, `README.md`): kleine, gerichte aanpassingen,
   zodat het samenvoegen makkelijk blijft.
5. Klaar met een stuk backend? Dan wordt `backend` in `main` gemerged.

## Communicatie tussen de sessies

- Claude-sessies op deze pc kunnen elkaar berichten sturen (`ListAgents` om de andere te
  vinden, `SendMessage` om iets te sturen). Gebruik dat voor vragen en contractwijzigingen.
- De frontend-sessie kan de backend-code altijd lezen in `D:\FASE-3\Chinees-backend`.
- Backend lokaal starten voor tests: zie `backend/README.md` (in de backend-worktree).

## Stand

- Backend (FastAPI + SQLite): wordt gebouwd op branch `backend`. Eerst: woordenlijsten
  uploaden/opvragen, daarna dictee genereren via Claude.
- Frontend: door de andere terminal.
