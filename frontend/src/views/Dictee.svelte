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

  const weekInfo = $derived(stand.weken.find((w) => w.nummer === week))
  const aiUit = $derived(stand.health && !stand.health.ai_beschikbaar)
  const alleOpen = $derived(dictee && dictee.zinnen.every((z) => onthuld[z.nr]))
  const aantalGoed = $derived(Object.values(oordelen).filter((o) => o === 'goed').length)
  const aantalBeoordeeld = $derived(Object.keys(oordelen).length)

  function reset() {
    onthuld = {}
    oordelen = {}
  }

  async function laadLaatste(n) {
    fout = null
    dictee = null
    reset()
    ophalen = true
    try {
      const lijst = await api.dictees(n)
      if (lijst.length && week === n) dictee = await api.dictee(lijst[0].id)
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
      const nieuw = await api.maakDictee(week, aantal)
      dictee = nieuw
      reset()
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
      const { [nr]: _, ...rest } = oordelen
      oordelen = rest
    } else {
      oordelen[nr] = oordeel
    }
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
          ontoggle={() => (onthuld[zin.nr] = !onthuld[zin.nr])}
          onoordeel={(o) => beoordeel(zin.nr, o)}
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
