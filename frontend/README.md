# Frontend

De webinterface: **Svelte 5 + Vite**, gewoon JavaScript. Ontwerp: 田字格-schrijfvakjes, licht en donker thema.
Later als PWA, zodat hij als app op de gsm staat.

## Schermen

| Tab | Wat | API |
|---|---|---|
| **Dictee** | Pinyin tonen, per zin de oplossing (hanzi + vertaling) tonen, zelf goed/fout aanduiden, laten voorlezen | `GET /api/dictees?week=N`, `GET /api/dictees/{id}`, `POST /api/dictees` |
| **Weken** | Overzicht per week, woorden bekijken, week verwijderen, meteen een dictee starten | `GET /api/weken`, `GET /api/weken/{n}`, `DELETE /api/weken/{n}` |
| **Uploaden** | CSV of foto → nakijken en verbeteren in een tabel → opslaan | `POST /api/weken/herken`, `PUT /api/weken/{n}` |

Het contract staat in [`docs/api.md`](../docs/api.md).

## Starten

Je hebt Node.js nodig (LTS). Eerst de backend starten (zie `backend/README.md`), dan:

```bash
cd frontend
npm install        # alleen de eerste keer
npm run dev        # http://localhost:5173
```

De devserver stuurt alles onder `/api` door naar `http://localhost:8000`, dus CORS is niet nodig.
Draait de backend op een andere poort? Gebruik `API_URL=http://localhost:8001 npm run dev`.

## Bouwen

```bash
npm run build      # statische bestanden in frontend/dist/
npm run preview    # gebouwde versie testen op http://localhost:4173
```

Op de Raspberry Pi komt `dist/` achter dezelfde reverse proxy als de backend (zie `deploy/`).

## Structuur

```
src/
├── main.js              # start de app
├── App.svelte           # header, tabs (#dictee, #weken, #upload)
├── app.css              # kleuren, lettertypes en alle stijlen
├── lib/
│   ├── api.js           # alle calls naar de backend
│   ├── stand.svelte.js  # gedeelde toestand (weken, health)
│   └── tekens.js        # hanzi in vakjes splitsen, voorlezen, datums
├── components/
│   └── Zin.svelte       # één dictee-zin met vakjes
└── views/
    ├── Dictee.svelte
    ├── Weken.svelte
    └── Upload.svelte
```

## Regels

- Geen `alert()`, `confirm()` of `prompt()`: bevestigingen staan in de pagina zelf (zie `docs/werkwijze.md`).
- De API-key komt nooit in de frontend.
