// Dunne laag rond de backend. Zie docs/api.md voor het contract.

export class ApiFout extends Error {
  constructor(status, bericht) {
    super(bericht)
    this.status = status
  }
}

function leesDetail(data, status) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  // FastAPI-validatiefouten (422) zijn een lijst
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(' · ')
  return `Er ging iets mis (HTTP ${status}).`
}

async function verzoek(pad, opties = {}) {
  let antwoord
  try {
    antwoord = await fetch('/api' + pad, opties)
  } catch {
    throw new ApiFout(0, 'De backend is niet bereikbaar. Draait hij op poort 8000?')
  }
  if (antwoord.status === 204) return null
  let data = null
  try {
    data = await antwoord.json()
  } catch {
    // geen JSON in het antwoord
  }
  if (!antwoord.ok) throw new ApiFout(antwoord.status, leesDetail(data, antwoord.status))
  return data
}

const json = (methode, body) => ({
  method: methode,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

function metBestand(bestand) {
  const form = new FormData()
  form.append('bestand', bestand)
  return { method: 'POST', body: form }
}

export const api = {
  health: () => verzoek('/health'),

  weken: () => verzoek('/weken'),
  week: (nummer) => verzoek(`/weken/${nummer}`),
  verwijderWeek: (nummer) => verzoek(`/weken/${nummer}`, { method: 'DELETE' }),
  /** CSV of afbeelding lezen zonder op te slaan → { nummer, woorden, waarschuwingen } */
  herken: (bestand) => verzoek('/weken/herken', metBestand(bestand)),
  /** Week aanmaken of vervangen */
  slaWeekOp: (nummer, { titel, woorden }) => verzoek(`/weken/${nummer}`, json('PUT', { titel, woorden })),

  maakDictee: (week, aantal_zinnen) => verzoek('/dictees', json('POST', { week, aantal_zinnen })),
  dictees: (week) => verzoek(week == null ? '/dictees' : `/dictees?week=${week}`),
  dictee: (id) => verzoek(`/dictees/${id}`),
  /** zinnen: [{ nr, goed, foute_woorden? }], overschrijft het vorige resultaat */
  slaResultaatOp: (id, zinnen) => verzoek(`/dictees/${id}/resultaat`, json('PUT', { zinnen })),
  verwijderDictee: (id) => verzoek(`/dictees/${id}`, { method: 'DELETE' }),
}
