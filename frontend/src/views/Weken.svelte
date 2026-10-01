<script>
  import { api } from '../lib/api.js'
  import { stand, laadWeken, naarDictee } from '../lib/stand.svelte.js'
  import { datum } from '../lib/tekens.js'

  let open = $state(null)
  let details = $state({})
  let bevestigWis = $state(null)
  let fout = $state(null)

  const totaal = $derived(stand.weken.reduce((som, w) => som + w.aantal_woorden, 0))

  async function toggle(n) {
    if (open === n) {
      open = null
      return
    }
    open = n
    fout = null
    // altijd vers ophalen: keer_fout verandert na elk nagekeken dictee
    try {
      details[n] = await api.week(n)
    } catch (e) {
      fout = e.message
    }
  }

  async function wis(n) {
    fout = null
    try {
      await api.verwijderWeek(n)
      bevestigWis = null
      if (open === n) open = null
      delete details[n]
      await laadWeken()
    } catch (e) {
      fout = e.message
    }
  }
</script>

<h1>Mijn weken</h1>

{#if !stand.wekenGeladen}
  <div class="laden" role="status">Laden…</div>
{:else if stand.wekenFout}
  <div class="melding fout" role="alert">{stand.wekenFout}</div>
{:else if !stand.weken.length}
  <div class="leeg">
    <p>Je hebt nog geen woordenlijsten.</p>
    <a class="btn primary" href="#upload">Upload je eerste lijst</a>
  </div>
{:else}
  <p class="sub">
    {stand.weken.length} {stand.weken.length === 1 ? 'woordenlijst' : 'woordenlijsten'} · {totaal} woorden in totaal
  </p>
  {#if fout}
    <div class="melding fout" role="alert">{fout}</div>
  {/if}

  <div class="weken">
    {#each stand.weken as w (w.nummer)}
      <div class="week-rij">
        <div class="week-nr"><small>Week</small>{w.nummer}</div>
        <div class="week-info">
          <h2>{w.titel || 'Zonder titel'}</h2>
          <div class="sub" style="font-size:13px">{w.aantal_woorden} woorden · geüpload op {datum(w.geupload_op)}</div>
        </div>
        <div class="week-knoppen">
          {#if bevestigWis === w.nummer}
            <span class="sub" style="font-size:13.5px">Week {w.nummer} verwijderen?</span>
            <button type="button" class="btn small gevaar primary" onclick={() => wis(w.nummer)}>Ja, verwijder</button>
            <button type="button" class="btn small" onclick={() => (bevestigWis = null)}>Annuleer</button>
          {:else}
            <button type="button" class="btn small" onclick={() => toggle(w.nummer)}>
              {open === w.nummer ? 'Sluit lijst' : 'Bekijk woorden'}
            </button>
            <button type="button" class="btn small gevaar" onclick={() => (bevestigWis = w.nummer)}>Verwijder</button>
            <button type="button" class="btn small primary" onclick={() => naarDictee(w.nummer, true)}>Dictee</button>
          {/if}
        </div>
      </div>
      {#if open === w.nummer}
        {#if details[w.nummer]}
          <div class="tabel-wrap">
            <table>
              <thead><tr><th>Hanzi</th><th>Pinyin</th><th>Betekenis</th><th>Fout</th></tr></thead>
              <tbody>
                {#each details[w.nummer].woorden as woord (woord.id)}
                  <tr>
                    <td class="hz">{woord.hanzi}</td><td class="py">{woord.pinyin}</td><td>{woord.betekenis}</td>
                    <td>
                      {#if woord.keer_fout}<span class="keer-fout" title="{woord.keer_fout} keer fout in nagekeken dictees">{woord.keer_fout}×</span>{/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else if !fout}
          <div class="sub" role="status">Laden…</div>
        {/if}
      {/if}
    {/each}
  </div>
{/if}
