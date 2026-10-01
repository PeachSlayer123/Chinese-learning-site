# CLAUDE.md

> **Begin van elke sessie (vooral op een nieuw toestel, bv. de laptop):** kijk of `.env` in de root bestaat
> en een `ANTHROPIC_API_KEY` bevat. Zo niet: **zeg dat expliciet tegen de gebruiker voordat je aan iets begint**
> (zonder key werken dictees en foto-upload niet). Zeg ook dat `data/app.db` (de woordenlijsten en dictees)
> niet in git zit en op een nieuw toestel dus leeg is. Zie `docs/opstarten.md` en "Open punten" in `docs/meeBezig.md`.

Persoonlijke app om Chinees te leren (wekelijkse woordenlijsten, dictees met pinyin, AI-tutor via de Claude API).
Wordt gehost op een Raspberry Pi.

- Docs en communicatie in het **Nederlands**.
- **Volg altijd `docs/werkwijze.md`**: taak claimen en communiceren met andere sessies, afvinken als je klaar bent, live checken in Chrome.
- Lees `docs/plan.md` voor doelen en roadmap en `docs/meeBezig.md` voor de huidige stand.
- Werk `docs/meeBezig.md` bij als je een taak afrondet.
- De API-key blijft in de backend, nooit in frontend-code en nooit in git.
- Woordenboekfeiten (pinyin, betekenis) komen bij voorkeur uit een vaste bron (CC-CEDICT of de geüploade lijst), niet uit de AI.
