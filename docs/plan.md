# Plan

## Doel

Elke week moet ik een lijst Chinese woordjes kennen. Deze app helpt me die te oefenen,
vooral met **dictees**: de app geeft pinyin, ik schrijf de karakters op papier en check daarna de oplossing.

## Kernflow: het dictee

1. **Upload** de woordenlijst van deze week (bv. `week-03.csv`).
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
- **Kosten:** dictees genereren is een simpele taak, dus een goedkoop model (bv. Haiku) volstaat waarschijnlijk.

## Roadmap

### Fase 0: Setup
- [x] Repo-structuur en docs
- [ ] Tech stack kiezen
- [ ] Backend en frontend die "hello world" doen

### Fase 1: MVP (dictee)
- [ ] Woordenlijst uploaden (CSV) en opslaan
- [ ] Lijst van alle weken/woorden bekijken
- [ ] Dictee genereren via de Claude API
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
| Backend | Python (FastAPI) / Node | ? |
| Frontend | React / Svelte / plain HTML+JS | ? |
| Database | SQLite (aanbevolen voor 1 gebruiker) | ? |
| Uploadformaat | CSV / Excel / tekst / foto van de lijst | ? |
| Schrift | Vereenvoudigd / traditioneel | ? |
| Raspberry Pi-model | 3 / 4 / 5 | ? |
