<script>
  import { tick } from 'svelte'
  import { api } from '../lib/api.js'
  import { stand, laadWeken, naarDictee } from '../lib/stand.svelte.js'

  const TOEGELATEN = '.csv,text/csv,image/png,image/jpeg,image/webp,image/gif'

  let bestandsnaam = $state('')
  let herkennen = $state(false)
  let woorden = $state(null)
  let waarschuwingen = $state([])
  let nummer = $state(null)
  let titel = $state('')
  let vervang = $state(false)
  let fout = $state(null)
  let opgeslagen = $state(null)
  let sleept = $state(false)

  const volgende = $derived(Math.max(0, ...stand.weken.map((w) => w.nummer)) + 1)
  const bestaat = $derived(stand.weken.some((w) => w.nummer === Number(nummer)))
  const isFoto = $derived(!/\.csv$/i.test(bestandsnaam))

  async function kies(bestand) {
    if (!bestand) return
    fout = null
    opgeslagen = null
    if (/\.hei[cf]$/i.test(bestand.name)) {
      fout = 'HEIC-foto\'s (iPhone) worden niet ondersteund. Zet de foto eerst om naar JPG.'
      return
    }
    bestandsnaam = bestand.name
    woorden = null
    herkennen = true
    try {
      const r = await api.herken(bestand)
      woorden = r.woorden.map((w) => ({ hanzi: w.hanzi, pinyin: w.pinyin, betekenis: w.betekenis ?? '' }))
      waarschuwingen = r.waarschuwingen
      nummer = r.nummer ?? volgende
      titel = ''
      vervang = false
    } catch (e) {
      fout = e.status === 503 ? 'Een foto lezen lukt pas met een API-key in .env. Een CSV-bestand werkt wel.' : e.message
    } finally {
      herkennen = false
    }
  }

  function opDrop(e) {
    e.preventDefault()
    sleept = false
    kies(e.dataTransfer?.files?.[0])
  }

  async function rijErbij() {
    woorden.push({ hanzi: '', pinyin: '', betekenis: '' })
    await tick()
    document.getElementById(`w-${woorden.length - 1}-hanzi`)?.focus()
  }

  function annuleer() {
    woorden = null
    waarschuwingen = []
    fout = null
  }

  async function opslaan() {
    fout = null
    const n = Number(nummer)
    if (!Number.isInteger(n) || n < 1) {
      fout = 'Geef een geldig weeknummer in (1 of hoger).'
      return
    }
    const lijst = woorden
      .map((w) => ({ hanzi: w.hanzi.trim(), pinyin: w.pinyin.trim(), betekenis: w.betekenis.trim() }))
      .filter((w) => w.hanzi)
    if (!lijst.length) {
      fout = 'Voeg minstens één woord toe voordat je opslaat.'
      return
    }
    if (lijst.some((w) => !w.pinyin)) {
      fout = 'Elk woord heeft pinyin nodig. Vul de lege pinyin-cellen aan.'
      return
    }
    if (bestaat && !vervang) {
      fout = `Week ${n} bestaat al. Vink "Vervang week ${n}" aan om de lijst te vervangen.`
      return
    }
    try {
      const week = await api.slaWeekOp(n, { titel: titel.trim() || null, woorden: lijst })
      opgeslagen = { nummer: week.nummer, aantal: week.woorden.length }
      woorden = null
      waarschuwingen = []
      await laadWeken()
    } catch (e) {
      fout = e.message
    }
  }
</script>

<h1>Woordenlijst uploaden</h1>
<p class="sub">
  Een CSV met de kolommen <code>hanzi,pinyin,betekenis</code>, of gewoon een foto of screenshot van je lijst.
  Je kunt alles nog nakijken voordat je opslaat.
</p>

{#if herkennen}
  <div class="laden" role="status">
    <span class="pen" aria-hidden="true">读</span>
    {isFoto ? 'Claude leest de woorden van je foto… (5 tot 20 seconden)' : 'Bestand lezen…'}
  </div>
{:else if !woorden}
  <div
    class="drop"
    class:over={sleept}
    role="region"
    aria-label="Bestand neerzetten"
    ondragover={(e) => {
      e.preventDefault()
      sleept = true
    }}
    ondragleave={() => (sleept = false)}
    ondrop={opDrop}
  >
    <span class="groot" aria-hidden="true">词</span>
    <strong>Sleep je CSV-bestand of een foto van je woordenlijst hierheen</strong>
    <span class="sub">CSV, PNG, JPG, WEBP of GIF. Foto's van een iPhone (HEIC) eerst omzetten naar JPG.</span>
    <label class="btn" for="up-bestand">Kies een bestand</label>
    <input
      type="file"
      id="up-bestand"
      accept={TOEGELATEN}
      hidden
      onchange={(e) => {
        kies(e.currentTarget.files[0])
        e.currentTarget.value = ''
      }}
    />
  </div>
{/if}

{#if fout}
  <div class="melding fout" role="alert">{fout}</div>
{/if}
{#if opgeslagen}
  <div class="melding ok" role="status">
    Week {opgeslagen.nummer} opgeslagen met {opgeslagen.aantal} woorden.
    <button type="button" class="btn small primary" style="margin-left:8px" onclick={() => naarDictee(opgeslagen.nummer, true)}>
      Maak meteen een dictee
    </button>
  </div>
{/if}

{#if woorden && !herkennen}
  {#if waarschuwingen.length}
    <div class="warnings" role="note" style="margin-top:16px">
      <strong>Controleer even</strong>
      <ul>
        {#each waarschuwingen as w, i (i)}<li>{w}</li>{/each}
      </ul>
    </div>
  {/if}

  <div class="form-rij">
    <label class="veld" for="up-nummer">Weeknummer<input type="number" id="up-nummer" min="1" bind:value={nummer} /></label>
    <label class="veld" for="up-titel" style="flex:1;min-width:200px">
      Titel (optioneel)<input type="text" id="up-titel" placeholder="bv. Les 4: familie" bind:value={titel} />
    </label>
    {#if bestaat}
      <label class="check" for="up-vervang"><input type="checkbox" id="up-vervang" bind:checked={vervang} /> Vervang week {nummer}</label>
    {/if}
    <button type="button" class="btn primary" onclick={opslaan}>Opslaan</button>
    <button type="button" class="btn" onclick={annuleer}>Annuleer</button>
  </div>
  {#if bestaat}
    <p class="sub" style="margin-top:8px;color:var(--warn)">Week {nummer} bestaat al. Opslaan vervangt de huidige lijst.</p>
  {/if}

  <p class="sub" style="margin-top:14px">
    {bestandsnaam} · {woorden.length} woorden {isFoto ? 'herkend' : 'gevonden'} · klik in een cel om te verbeteren
  </p>
  <div class="tabel-wrap">
    <table class="bewerk">
      <thead>
        <tr><th>Hanzi</th><th>Pinyin</th><th>Betekenis</th><th><span class="visually-hidden">Verwijderen</span></th></tr>
      </thead>
      <tbody>
        {#each woorden as woord, i (woord)}
          <tr>
            <td class="hz"><input id="w-{i}-hanzi" aria-label="Hanzi rij {i + 1}" bind:value={woord.hanzi} /></td>
            <td class="py"><input id="w-{i}-pinyin" aria-label="Pinyin rij {i + 1}" bind:value={woord.pinyin} /></td>
            <td><input id="w-{i}-betekenis" aria-label="Betekenis rij {i + 1}" bind:value={woord.betekenis} /></td>
            <td class="actie">
              <button type="button" class="btn small" aria-label="Verwijder rij {i + 1}" onclick={() => woorden.splice(i, 1)}>✕</button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  <button type="button" class="btn small" style="margin-top:10px" onclick={rijErbij}>+ Woord toevoegen</button>
{/if}
