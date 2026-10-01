<script>
  import { tekenRollen, kanVoorlezen, leesVoor } from '../lib/tekens.js'

  /** zin: Zin uit docs/api.md, open: oplossing zichtbaar, oordeel: '' | 'goed' | 'fout' */
  let { zin, open, oordeel, ontoggle, onoordeel } = $props()

  const tekens = $derived(tekenRollen(zin))
</script>

<li class="zin" class:revealed={open} class:goed={oordeel === 'goed'} class:fout={oordeel === 'fout'}>
  <span class="nr">{zin.nr}</span>
  <div class="zin-body">
    <p class="pinyin">{zin.pinyin}</p>
    <div class="vakjes" aria-label={open ? zin.hanzi : `Schrijfvakjes, ${tekens.length} tekens`}>
      {#each tekens as teken, i (i)}
        <span class="vak {teken.rol}"><span>{teken.t}</span></span>
      {/each}
    </div>

    {#if open}
      <div class="oplossing">
        <p class="vertaling">{zin.vertaling}</p>
        <div class="chips">
          <span class="eyebrow">Woorden van de week</span>
          {#each zin.woorden_van_de_week as woord (woord)}
            <span class="chip"><span class="zh">{woord}</span></span>
          {/each}
          {#each zin.onbekende_tekens as teken (teken)}
            <span class="chip warn">onbekend: <span class="zh">{teken}</span></span>
          {/each}
        </div>
      </div>
    {/if}

    <div class="zin-actions">
      <button type="button" class="btn small" onclick={ontoggle}>
        {open ? 'Verberg oplossing' : 'Toon oplossing'}
      </button>
      {#if kanVoorlezen}
        <button type="button" class="btn small" onclick={() => leesVoor(zin.hanzi)}>Lees voor</button>
      {/if}
      {#if open}
        <span class="zelf">
          Had je het juist?
          <button type="button" class="btn small goed" aria-pressed={oordeel === 'goed'} onclick={() => onoordeel('goed')}>Goed</button>
          <button type="button" class="btn small fout" aria-pressed={oordeel === 'fout'} onclick={() => onoordeel('fout')}>Fout</button>
        </span>
      {/if}
    </div>
  </div>
</li>
