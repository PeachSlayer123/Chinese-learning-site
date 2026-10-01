# API-contract (backend ↔ frontend)

Dit is de afspraak tussen backend en frontend. **Wijzigingen hieraan altijd eerst hier aanpassen**
en melden aan de andere kant (zie [`samenwerking.md`](samenwerking.md)).

- Basis-URL lokaal: `http://localhost:8000`
- Alle endpoints beginnen met `/api`
- JSON in en uit (UTF-8), behalve de upload (multipart/form-data)
- Fouten: HTTP-statuscode + `{"detail": "uitleg in het Nederlands"}`
- Interactieve docs zodra de backend draait: `http://localhost:8000/docs`
- CORS staat open voor `http://localhost:5173` (Vite) en `http://localhost:3000`.
  Andere origin nodig? Zet `CORS_ORIGINS` in `.env` (kommagescheiden).

## Datatypes

```ts
type Woord = {
  id: number
  hanzi: string        // "学习"
  pinyin: string       // "xuéxí" (toontekens)
  betekenis: string    // "leren / studeren"
  week: number         // weeknummer waar het woord bij hoort
  keer_fout: number    // hoe vaak dit woord fout was in nagekeken dictees (0 = nooit)
}

type WeekSamenvatting = {
  nummer: number        // 3
  titel: string | null  // vrij veld, bv. "Les 3: op school"
  aantal_woorden: number
  geupload_op: string   // ISO 8601, bv. "2026-10-02T14:03:00"
}

type Week = WeekSamenvatting & { woorden: Woord[] }

type WeekNaUpload = Week & { waarschuwingen: string[] }  // [] bij een CSV

type NieuwWoord = { hanzi: string; pinyin: string; betekenis: string }

type HerkendeWeek = {
  nummer: number | null         // uit de bestandsnaam (week-03.csv), anders van de afbeelding, anders null
  woorden: NieuwWoord[]
  waarschuwingen: string[]      // bv. "Geen pinyin op de afbeelding, automatisch berekend voor: 老师"
}

type Zin = {
  nr: number                    // 1, 2, 3, ...
  hanzi: string                 // "我在学习中文。"
  pinyin: string                // "Wǒ zài xuéxí zhōngwén." (hoofdletter + westerse leestekens)
  vertaling: string             // Nederlandse vertaling
  woorden_van_de_week: string[] // welke weekwoorden erin zitten, bv. ["学习", "中文"]
  onbekende_tekens: string[]    // tekens die niet in een geüploade lijst staan (ideaal: [])
}

type ZinResultaat = {
  nr: number
  goed: boolean
  foute_woorden: string[]       // optioneel bij versturen; hanzi die in die zin fout waren
}

type Dictee = {
  id: number
  week: number
  aangemaakt_op: string
  zinnen: Zin[]
  waarschuwingen: string[]      // bv. "Zin 3 bevat onbekende tekens: 很"
  resultaat: ZinResultaat[] | null  // null = nog niet nagekeken
}

type DicteeSamenvatting = {
  id: number; week: number; aangemaakt_op: string; aantal_zinnen: number
  aantal_goed: number | null    // null = nog niet nagekeken
}
```

> De backend geeft altijd de volledige oplossing mee. **De frontend beslist** wat getoond wordt
> (eerst alleen `pinyin`, na een klik `hanzi` + `vertaling`).

## Endpoints

### `GET /api/health`
→ `200 {"status": "ok", "ai_beschikbaar": true}`
`ai_beschikbaar` is `false` als er geen API-key ingesteld is (dan geeft dictee genereren `503`).

### Weken / woordenlijsten

| Methode | Pad | Body | Antwoord |
|---|---|---|---|
| `POST` | `/api/weken` | multipart: `bestand` (CSV **of afbeelding**, verplicht), `nummer` (int, optioneel), `titel` (optioneel), `vervang` (`true`/`false`, optioneel) | `201 WeekNaUpload` |
| `POST` | `/api/weken/herken` | multipart: `bestand` (CSV of afbeelding) | `200 HerkendeWeek` (**niet** opgeslagen) |
| `PUT` | `/api/weken/{nummer}` | JSON `{"titel": "Les 4" \| null, "woorden": NieuwWoord[]}` (min. 1 woord) | `200 Week` (maakt aan of vervangt) |
| `GET` | `/api/weken` | – | `200 WeekSamenvatting[]` (gesorteerd op nummer) |
| `GET` | `/api/weken/{nummer}` | – | `200 Week` / `404` |
| `DELETE` | `/api/weken/{nummer}` | – | `204` / `404` |
| `GET` | `/api/woorden?tot_week=N` | – | `200 Woord[]` (alle woorden, of alleen weken ≤ N) |

Upload-details:
- CSV met kolommen `hanzi,pinyin,betekenis` (zie `data/woordenlijsten/voorbeeld-week.csv`).
- Geen `nummer` meegegeven? Dan haalt de backend het uit de bestandsnaam (`week-03.csv` → 3).
- Bestaat de week al: `409`, tenzij `vervang=true` (dan wordt de lijst vervangen).
- Ongeldige CSV: `422` met uitleg in `detail`.

Screenshot/foto van de woordenlijst:
- Formaten: PNG, JPG, WEBP, GIF (max. 20 MB; grote foto's verkleint de backend zelf). HEIC (iPhone) werkt niet.
- Herkend aan `content-type: image/*` of de extensie.
- Claude leest de woorden uit de afbeelding (duurt ~5-20 s, toon een laadindicator).
  Ontbreekt de pinyin, dan berekent de backend die; ontbreekt de betekenis, dan vult de AI ze aan.
  Beide komen in `waarschuwingen`: **toon die aan de gebruiker**.
- Weeknummer: `nummer` uit het formulier > bestandsnaam > weeknummer op de afbeelding.
- Fouten: `503` geen API-key (CSV werkt wel nog), `502` AI-fout, `422` geen afbeelding/geen woorden gevonden.
- **Aanbevolen flow (CSV én afbeelding):** `POST /api/weken/herken` → woorden in een bewerkbare tabel tonen →
  gebruiker verbetert → `PUT /api/weken/{nummer}`. Snelle flow zonder nakijken: `POST /api/weken` met de afbeelding.

### Dictees

| Methode | Pad | Body | Antwoord |
|---|---|---|---|
| `POST` | `/api/dictees` | `{"week": 3, "aantal_zinnen": 5}` (`aantal_zinnen` 1–15, standaard 5) | `201 Dictee` |
| `GET` | `/api/dictees?week=N` | – | `200 DicteeSamenvatting[]` (nieuwste eerst; `week` optioneel) |
| `GET` | `/api/dictees/{id}` | – | `200 Dictee` / `404` |
| `PUT` | `/api/dictees/{id}/resultaat` | `{"zinnen": [{"nr": 1, "goed": false, "foute_woorden": ["学习"]}, {"nr": 2, "goed": true}]}` | `200 Dictee` / `404` / `422` |
| `DELETE` | `/api/dictees/{id}` | – | `204` / `404` |

- Genereren duurt een paar seconden (AI-call): toon een laadindicator.
- `404` als de week niet bestaat, `503` als de AI niet beschikbaar is, `502` als de AI-call mislukt.
- De **pinyin** komt niet van de AI maar wordt door de backend berekend
  (woorden uit je lijsten krijgen jouw pinyin, de rest via `pypinyin`).
- Bekende woorden = woorden van de gekozen week + alle weken met een lager nummer.

Resultaat (wat had ik fout?):
- Opnieuw sturen **overschrijft** het vorige resultaat. Niet meegestuurde zinnen = niet nagekeken.
- `foute_woorden` is optioneel. Een foute zin zonder `foute_woorden` telt als fout voor alle
  weekwoorden in die zin (`woorden_van_de_week`). Een zin met `foute_woorden` is altijd fout.
- `422` bij een onbekend `nr`, een dubbel `nr`, of een fout woord dat niet in die zin staat.
- Woorden die vaak fout waren (`Woord.keer_fout`) komen in nieuwe dictees vaker terug.
- Een week vervangen (`PUT /api/weken/{n}` of upload met `vervang`) houdt de dictees en resultaten van die week bij.

## Later (nog niet gebouwd)
- (niets gepland, vragen welkom)
