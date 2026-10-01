# Opstarten

Hoe je de app draait: op een nieuw toestel (bv. je laptop) en daarna elke dag.

## Wat niet in git zit (en dus niet meekomt naar een ander toestel)

| Wat | Waar | Op een nieuw toestel |
|---|---|---|
| API-key | `.env` in de root van de repo | Opnieuw aanmaken (zie stap 3) |
| Je woordenlijsten, dictees en resultaten | `data/app.db` (SQLite) | Leeg. Kopieer het bestand mee als je je data wilt houden |
| Python-pakketten | `backend/.venv/` | Opnieuw installeren (stap 4) |
| Node-pakketten | `frontend/node_modules/` | Opnieuw installeren (stap 5) |

> Tip: zet `data/app.db` bv. op een USB-stick of in de cloud als je op twee toestellen wilt werken.
> Later, als de app op de Raspberry Pi draait, staat de data daar en is dit niet meer nodig.

## Nieuw toestel: eenmalig

1. **Installeren:** Git, Python 3 (getest met 3.14) en Node.js (LTS). Voor live checks: Chrome met de Claude-extensie.
2. **Repo binnenhalen:**
   ```bash
   git clone https://github.com/PeachSlayer123/Chinese-learning-site.git Chinees
   cd Chinees
   ```
3. **API-key:** kopieer `.env.example` naar `.env` en vul `ANTHROPIC_API_KEY=` in.
   Gebruik een key die bij een workspace hoort; anders weigert de API met een fout over `anthropic-workspace-id`.
4. **Backend:**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt     # Windows
   # .venv/bin/python -m pip install -r requirements.txt       # macOS / Linux
   ```
5. **Frontend:**
   ```bash
   cd frontend
   npm install
   ```

## Elke keer: de app starten

Zie ook [`werkwijze.md`](werkwijze.md) §4 voor de live-checks in Chrome.

Twee terminals:

```bash
# Terminal 1: backend op http://localhost:8000 (API-docs op /docs)
cd backend
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend op http://localhost:5173
cd frontend
npm run dev
```

Open **http://localhost:5173**. De statusbol rechtsboven moet groen zijn ("AI beschikbaar").

- Oranje ("AI niet beschikbaar"): `.env` ontbreekt of de key is leeg. Herstart de backend na het aanpassen.
- Rood ("Backend niet bereikbaar"): terminal 1 draait niet.
- Nieuwe backend-code lijkt niet geladen? Stop de backend (Ctrl+C) en start hem opnieuw; `--reload` mist soms wijzigingen.

## Verder werken met Claude Code

1. Start Claude Code **in de root van de repo**. Dan leest Claude automatisch `CLAUDE.md`.
2. Zeg bv.: *"Lees docs/meeBezig.md en ga verder."* Daar staat waar we gebleven zijn en wat de volgende stap is.
3. Werk je met meerdere terminals tegelijk (backend + frontend)? Zie [`samenwerking.md`](samenwerking.md)
   en [`werkwijze.md`](werkwijze.md).
4. Browsertools aanzetten in Claude Code: `/chrome` (of herstart Claude Code).

Over de backend-worktree: op de eerste pc werkte de backend-sessie in een aparte map
(`../Chinees-backend`, branch `backend`). Dat is een lokale opstelling. Alles is al in `main` gemerged,
dus op een nieuw toestel heb je die niet nodig. Wil je weer twee terminals tegelijk, maak dan een nieuwe worktree:
`git worktree add ../Chinees-backend -b backend`.
