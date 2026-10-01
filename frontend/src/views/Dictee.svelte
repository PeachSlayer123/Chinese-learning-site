<script>
  import { onMount } from 'svelte'
  import { api } from '../lib/api.js'
  import { stand } from '../lib/stand.svelte.js'
  import Zin from '../components/Zin.svelte'

  let week = $state(null)
  let aantal = $state(5)
  let dictee = $state(null)
  let laden = $state(false)
  let ophalen = $state(false)
  let fout = $state(null)
  let onthuld = $state({})
  let oordelen = $state({})
  let foute = $state({})
  let opslag = $state('')
  let opslagVersie = 0

  const weekInfo = $derived(stand.weken.find((w) => w.nummer === week))
  const aiUit = $derived(stand.health && !stand.health.ai_beschikbaar)
  const alleOpen = $derived(dictee && dictee.zinnen.every((z) => onthuld[z.nr]))
  const aantalGoed = $derived(Object.values(oordelen).filter((o) => o === 'goed').length)
  const aantalBeoordeeld = $derived(Object.keys(oordelen).length)

  // Nieuw of geladen dictee tonen; een eerder resultaat wordt teruggezet en die zinnen staan open
  function zetDictee(d) {
    dictee = d
    onthuld = {}
    oordelen = {}
    foute = {}
    opslag = ''
    for (const r of d?.resultaat ?? []) {
      onthuld[r.nr] = true
      oordelen[r.nr] = r.goed ? 'goed' : 'fout'
      if (r.foute_woorden.length) foute[r.nr] = [...r.foute_woorden]
    }
  }

  async function bewaarResultaat() {
    const zinnen = Object.entries(oordelen).map(([nr, o]) => {
      const r = { nr: Number(nr), goed: o === 'goed' }
      if (o === 'fout' && foute[nr]?.length) r.foute_woorden = foute[nr]
      return r
    })
    // Een lege lijst (alles terug uitgevinkt) wist het resultaat op de server
    const versie = ++opslagVersie
    opslag = 'bezig'
    try {
      await api.slaResultaatOp(dictee.id, zinnen)
      if (versie === opslagVersie) opslag = 'ok'
    } catch (e) {
      if (versie === opslagVersie) {
        opslag = ''
        fout = 'Je resultaat is niet opgeslagen: ' + e.message
      }
    }
  }

  async function laadLaatste(n) {
    fout = null
    zetDictee(null)
    ophalen = true
    try {
      const lijst = await api.dictees(n)
      if (lijst.length && week === n) zetDictee(await api.dictee(lijst[0].id))
    } catch (e) {
      fout = e.message
    } finally {
      ophalen = false
    }
  }

  async function genereer() {
    laden = true
    fout = null
    try {
      zetDictee(await api.maakDictee(week, aantal))
    } catch (e) {
      fout = e.status === 503 ? 'De AI is niet beschikbaar: er staat geen API-key in .env.' : e.message
    } finally {
      laden = false
    }
  }

  function kiesWeek(n) {
    week = n
    laadLaatste(n)
  }

  function toonAlles() {
    const open = !alleOpen
    onthuld = Object.fromEntries(dictee.zinnen.map((z) => [z.nr, open]))
  }

  function beoordeel(nr, oordeel) {
    if (oordelen[nr] === oordeel) {
      delete oordelen[nr]
      delete foute[nr]
    } else {
      oordelen[nr] = oordeel
      if (oordeel === 'goed') delete foute[nr]
    }
    fout = null
    bewaarResultaat()
  }

  function foutWoord(nr, woord) {
    const lijst = foute[nr] ?? []
    foute[nr] = lijst.includes(woord) ? lijst.filter((w) => w !== woord) : [...lijst, woord]
    oordelen[nr] = 'fout'
    fout = null
    bewaarResultaat()
  }

  // Eerste week kiezen zodra de weken geladen zijn
  let gestart = false
  $effect(() => {
    if (gestart || !stand.wekenGeladen || !stand.weken.length) return
    gestart = true
    const n = stand.gekozenWeek ?? stand.weken.at(-1).nummer
    week = n
    if (stand.directGenereren) {
      stand.directGenereren = false
      genereer()
    } else {
      laadLaatste(n)
    }
  })

  onMount(() => () => {
    stand.gekozenWeek = week
  })
</script>

{#if !stand.wekenGeladen}
  <div class="laden" role="status">Laden…</div>
{:else if stand.wekenFout}
  <h1>Dictee</h1>
  <div class="melding fout" role="alert">
    {stand.wekenFout} Start de backend met
    <code>uvicorn app.main:app --reload --port 8000</code> (zie <code>backend/README.md</code>).
  </div>
{:else if !stand.weken.length}
  <h1>Dictee</h1>
  <div class="leeg">
    <p>Je hebt nog geen woordenlijsten.</p>
    <a class="btn primary" href="#upload">Upload je eerste lijst</a>
  </div>
{:else}
  <h1>Dictee week {week}</h1>
  <p class="sub">
    {#if weekInfo?.titel}{weekInfo.titel} ·
    {/if}Schrijf de karakters op papier en check daarna per zin.
  </p>

  <div class="toolbar">
    <select id="kies-week" aria-label="Week" value={week} onchange={(e) => kiesWeek(Number(e.currentTarget.value))}>
      {#each stand.weken as w (w.nummer)}
        <option value={w.nummer}>Week {w.nummer}</option>
      {/each}
    </select>
    <select id="kies-aantal" aria-label="Aantal zinnen" bind:value={aantal}>
      {#each Array.from({ length: 15 }, (_, i) => i + 1) as n (n)}
        <option value={n}>{n} {n === 1 ? 'zin' : 'zinnen'}</option>
      {/each}
    </select>
    <button type="button" class="btn primary" onclick={genereer} disabled={laden || aiUit}>Nieuw dictee</button>
    <span class="spacer"></span>
    {#if dictee && !laden}
      {#if opslag === 'bezig'}
        <span class="opslag" role="status">Opslaan…</span>
      {:else if opslag === 'ok'}
        <span class="opslag" role="status">Opgeslagen</span>
      {/if}
      {#if aantalBeoordeeld}
        <span class="score">{aantalGoed} van {dictee.zinnen.length} goed</span>
      {/if}
      <button type="button" class="btn" onclick={toonAlles}>
        {alleOpen ? 'Verberg oplossingen' : 'Toon alle oplossingen'}
      </button>
    {/if}
  </div>

  {#if aiUit}
    <div class="melding fout" role="note">
      De AI is niet beschikbaar, dus nieuwe dictees maken lukt nu niet. Zet je API-key in <code>.env</code> en herstart de backend.
    </div>
  {/if}
  {#if fout}
    <div class="melding fout" role="alert">{fout}</div>
  {/if}

  {#if laden}
    <div class="laden" role="status">
      <span class="pen" aria-hidden="true">写</span>
      Claude schrijft {aantal} {aantal === 1 ? 'zin' : 'zinnen'} met de woorden van week {week}…
    </div>
  {:else if ophalen}
    <div class="laden" role="status">Laden…</div>
  {:else if dictee}
    {#if dictee.waarschuwingen.length}
      <div class="warnings" role="note">
        <strong>Let op</strong>
        <ul>
          {#each dictee.waarschuwingen as w, i (i)}<li>{w}</li>{/each}
        </ul>
      </div>
    {/if}
    <ol class="zinnen">
      {#each dictee.zinnen as zin (zin.nr)}
        <Zin
          {zin}
          open={!!onthuld[zin.nr]}
          oordeel={oordelen[zin.nr] ?? ''}
          foute={foute[zin.nr] ?? []}
          ontoggle={() => (onthuld[zin.nr] = !onthuld[zin.nr])}
          onoordeel={(o) => beoordeel(zin.nr, o)}
          onfoutwoord={(w) => foutWoord(zin.nr, w)}
        />
      {/each}
    </ol>
  {:else if !fout}
    <div class="leeg">
      <p>Er is nog geen dictee voor week {week}.</p>
      <p>Kies hoeveel zinnen je wilt en klik op <strong>Nieuw dictee</strong>.</p>
    </div>
  {/if}
{/if}
