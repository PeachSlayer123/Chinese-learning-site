// Gedeelde toestand tussen de schermen
import { api } from './api.js'

export const stand = $state({
  weken: [],
  wekenGeladen: false,
  wekenFout: null,
  health: null,
  /** week die het dicteescherm moet openen (gezet vanuit Weken of Uploaden) */
  gekozenWeek: null,
  /** meteen een nieuw dictee maken bij het openen van het dicteescherm */
  directGenereren: false,
})

export async function laadWeken() {
  try {
    stand.weken = await api.weken()
    stand.wekenFout = null
  } catch (e) {
    stand.wekenFout = e.message
  } finally {
    stand.wekenGeladen = true
  }
}

export async function laadHealth() {
  try {
    stand.health = await api.health()
  } catch {
    stand.health = { status: 'offline', ai_beschikbaar: false }
  }
}

export function naarDictee(week, genereren = false) {
  stand.gekozenWeek = week
  stand.directGenereren = genereren
  location.hash = '#dictee'
}
