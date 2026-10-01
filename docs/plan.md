# Plan

## Doel

Elke week moet ik een lijst Chinese woordjes kennen. Deze app helpt me die te oefenen,
vooral met **dictees**: de app geeft pinyin, ik schrijf de karakters op papier en check daarna de oplossing.

## Kernflow: het dictee

1. **Upload** de woordenlijst van deze week: een CSV (bv. `week-03.csv`) **of gewoon een screenshot/foto**
   van de lijst. Bij een afbeelding leest de AI (Claude) de woorden eruit.
2. **Genereer** een dictee: de AI (Claude) maakt X zinnen die
   - de woordjes van deze week gebruiken,
   - verder alleen woorden gebruiken die ik al ken (woorden van vorige weken).
3. **Toon alleen de pinyin** (met toontekens, bv. *wǒ xuéxí zhōngwén*).
4. Ik **schrijf de karakters op papier**.
5. **Toon de oplossing:** hanzi + pinyin + Nederlandse vertaling.
6. (Optioneel) Ik geef aan welke zinnen of woorden ik fout had, zodat de app die vaker terugbrengt.

### Aandachtspunten

- **Controle van de AI-output:** de backend checkt of elke zin echt de woorden van de week bevat,
  en of er geen onbekende woorden in staan. Is dat niet zo, dan vraagt hij een nieuwe zin.
- **Gestructureerde output:** Claude geeft de zinnen terug als JSON (hanzi, pinyin, vertaling, gebruikte woorden).
- **Printbaar:** een printversie (alleen pinyin + genummerde lijnen) is handig.
- **Screenshot herkennen:** de AI leest alleen over wat op de afbeelding staat. Ontbreekt de pinyin,
  dan berekent de backend die (`pypinyin`). Ontbreekt de betekenis, dan vult de AI ze aan,
  met een waarschuwing (later liever uit CC-CEDICT).
- **Kosten:** dictees genereren is een simpele taak, dus een goedkoop model (bv. Haiku) volstaat waarschijnlijk.

## Roadmap

### Fase 0: Setup
- [x] Repo-structuur en docs
- [ ] Tech stack kiezen (backend gekozen: FastAPI + SQLite)
- [ ] Backend en frontend die "hello world" doen (backend ✅ 2026-10-02, frontend nog niet)

### Fase 1: MVP (dictee)
- [x] Woordenlijst uploaden (CSV) en opslaan (backend; scherm in frontend nog te doen)
- [ ] Woordenlijst uploaden als **screenshot/foto**: AI herkent hanzi, pinyin en betekenis (backend: bezig)
- [ ] Herkende woorden nakijken/verbeteren vóór het opslaan (frontend)
- [ ] Lijst van alle weken/woorden bekijken
- [x] Dictee genereren via de Claude API (backend; nog niet getest met echte API-key)
- [ ] Pinyin tonen → oplossing tonen
- [ ] Lokaal draaien

### Fase 2: Op de Pi
- [ ] Docker-setup
- [ ] Draaien op de Raspberry Pi
- [ ] Veilige toegang (Tailscale)
- [ ] Backups

### Fase 3: Meer leeropties
- Zie [`ideeen.md`](ideeen.md)

## Beslissingen die nog open staan

| Vraag | Opties | Keuze |
|---|---|---|
| Backend | Python (FastAPI) / Node | Python (FastAPI) |
| Frontend | React / Svelte / plain HTML+JS | ? |
| Database | SQLite (aanbevolen voor 1 gebruiker) | SQLite |
| Uploadformaat | CSV / Excel / tekst / foto van de lijst | CSV + screenshot/foto (via AI) |
| Schrift | Vereenvoudigd / traditioneel | ? |
| Raspberry Pi-model | 3 / 4 / 5 | ? |
