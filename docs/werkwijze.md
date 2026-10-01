# Werkwijze

Vaste regels voor elke Claude Code-sessie in dit project. **Altijd volgen.**
De details over twee terminals tegelijk staan in [`samenwerking.md`](samenwerking.md).

## 1. Voor je aan iets begint

1. Lees [`meeBezig.md`](meeBezig.md) en [`plan.md`](plan.md): wat is er al gedaan, wat doet iemand anders nu?
2. Kijk of er andere sessies draaien: `ListAgents`.
3. **Claim je taak:**
   - Zet ze onder "Nu bezig" in je eigen sectie van `meeBezig.md` (met datum).
   - Stuur een kort bericht naar de andere sessies (`SendMessage`): wat je gaat doen en welke mappen je aanraakt.
4. Werk in je eigen map en branch:
   - Backend: worktree `D:\FASE-3\Chinees-backend`, branch `backend`.
   - Frontend: `D:\FASE-3\Chinees`, branch `main` of `frontend`.
   - Grotere of riskante taak? Maak er een aparte branch (of worktree) voor.

## 2. Terwijl je bezig bent

- Raak geen bestanden aan van een andere sessie (zie de tabel in `samenwerking.md`).
- Verander je het API-contract? Pas eerst [`api.md`](api.md) aan en stuur meteen een bericht naar de andere kant.
- Loop je vast op iets van de andere kant? Stuur een bericht met een vraag in plaats van het zelf aan te passen.
- Gedeelde docs (`plan.md`, `meeBezig.md`, `README.md`): kleine, gerichte aanpassingen.

## 3. Als je klaar bent

1. Tests draaien (backend: `pytest`) en, bij iets zichtbaars, nakijken in Chrome (zie hieronder).
2. **Afvinken:** zet het vakje in `plan.md` op `[x]` (met datum als dat nuttig is).
3. Verplaats de taak in `meeBezig.md` van "Nu bezig" naar "Klaar" (met datum en een korte uitleg).
4. Werk de rest bij wat nodig is: `api.md`, `README.md`'s, `.env.example`.
5. Commit (kleine, duidelijke commits) en merge je branch in `main` als het af is.
6. Stuur een bericht naar de andere sessies: wat er klaar is en wat ze ervan moeten weten.

## 4. Live feedback in Chrome

Met de **Claude in Chrome-extensie** kan Claude zelf de app openen, bekijken en testen.
Jij kijkt mee in hetzelfde Chrome-venster en geeft feedback in de terminal.

### Opstarten

1. Chrome open, de Claude-extensie aangemeld en verbonden.
2. Backend draaien (zie `backend/README.md`): `http://localhost:8000` (API-docs op `/docs`).
3. Frontend draaien (zie `frontend/README.md`): `cd frontend`, eenmalig `npm install`, dan `npm run dev`
   → `http://localhost:5173`. De devserver stuurt `/api` door naar `http://localhost:8000`
   (andere backend: `API_URL=http://localhost:8001 npm run dev`). Gebouwde versie: `npm run build` + `npm run preview` (`:4173`).
   - Node staat in `D:\` (`D:\node.exe`, `D:\npm.cmd`). Vindt de terminal `npm` niet? Zet `D:\` in `PATH` of herstart de terminal.
   - **Na een backend-merge op `main`: backend op `:8000` altijd hard herstarten.** `--reload` pikt nieuwe
     code op Windows niet altijd echt op (ziet de wijziging, maar draait oude code). De backend-sessie stuurt een seintje
     naar de sessie die `:8000` draait; die maakt eerst een kopie van `data/app.db` en herstart dan.
   - Test een andere sessie mee? Dan een eigen poort en een eigen `DATABASE_PATH`, zodat `:8000` en `data/app.db` ongemoeid blijven.
4. Claude opent zijn eigen tabblad (een aparte tabgroep "Claude"). Laat dat tabblad open staan.

### De lus na elke zichtbare wijziging

1. Code aanpassen.
2. Pagina herladen in het Claude-tabblad.
3. **Screenshot** bekijken: ziet het eruit zoals bedoeld?
4. **Console** nakijken op fouten (`read_console_messages`, alleen errors).
5. **Netwerk** nakijken: geven de `/api/...`-calls de juiste status (`read_network_requests`)?
6. Bij schermen voor de gsm: ook op gsm-breedte bekijken (venster op ±390×844).
   Werkt het verkleinen niet, dan staat het venster waarschijnlijk gemaximaliseerd: zet het eerst op "niet gemaximaliseerd".
7. Pas als dat allemaal klopt: de taak "klaar" noemen.

### Feedback geven

- Typ gewoon in de terminal wat je ziet of wil ("knop te klein", "pinyin groter").
- Claude past aan, herlaadt en checkt opnieuw met een screenshot.
- Is de code van een andere sessie (bv. `frontend/` van de frontend-sessie)? Dan past Claude ze niet zelf aan,
  maar stuurt de feedback (wat, waar, screenshot-beschrijving, console-fout) naar die sessie.
- Voor een flow met meerdere stappen (upload → dictee → oplossing) kan Claude een GIF opnemen.

### Regels voor de browser

- **Geen `alert()`, `confirm()` of `prompt()` in de frontend.** Die blokkeren de extensie.
  Gebruik meldingen of bevestigingen in de pagina zelf.
- Claude vult geen echte API-keys of wachtwoorden in via de browser.
- Claude werkt alleen in zijn eigen tabblad, niet in jouw andere tabs.
- Werkt de extensie niet (geen verbinding, fouten)? Na 2-3 pogingen stopt Claude en vraagt wat je wil doen.
