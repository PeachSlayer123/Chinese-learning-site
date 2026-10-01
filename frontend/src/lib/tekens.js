const LEESTEKENS = '。，？！、；：“”‘’（）《》…—.,?!;:'

/**
 * Splitst een zin in tekens en geeft elk teken een rol voor de 田字格-vakjes:
 * 'leesteken' (altijd zichtbaar), 'week' (deel van een woord van de week), 'onbekend' of ''.
 */
export function tekenRollen(zin) {
  const tekens = Array.from(zin.hanzi)
  const rollen = tekens.map((t) => (LEESTEKENS.includes(t) ? 'leesteken' : ''))
  for (const woord of zin.woorden_van_de_week) {
    let start = zin.hanzi.indexOf(woord)
    while (start !== -1) {
      const begin = Array.from(zin.hanzi.slice(0, start)).length
      for (let i = 0; i < Array.from(woord).length; i++) rollen[begin + i] = 'week'
      start = zin.hanzi.indexOf(woord, start + woord.length)
    }
  }
  tekens.forEach((t, i) => {
    if (zin.onbekende_tekens.includes(t)) rollen[i] = 'onbekend'
  })
  return tekens.map((t, i) => ({ t, rol: rollen[i] }))
}

let kanVoorlezen = false
try {
  kanVoorlezen = 'speechSynthesis' in window && typeof SpeechSynthesisUtterance === 'function'
} catch {
  kanVoorlezen = false
}
export { kanVoorlezen }

export function leesVoor(tekst) {
  try {
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(tekst)
    u.lang = 'zh-CN'
    u.rate = 0.75
    window.speechSynthesis.speak(u)
  } catch {
    // voorlezen niet beschikbaar in deze browser
  }
}

export const datum = (iso) => new Date(iso).toLocaleDateString('nl-BE', { day: 'numeric', month: 'long' })
