<script>
  import { onMount } from 'svelte'
  import { stand, laadWeken, laadHealth } from './lib/stand.svelte.js'
  import Dictee from './views/Dictee.svelte'
  import Weken from './views/Weken.svelte'
  import Upload from './views/Upload.svelte'

  const tabs = [
    { id: 'dictee', label: 'Dictee' },
    { id: 'weken', label: 'Weken' },
    { id: 'upload', label: 'Uploaden' },
  ]

  function leesHash() {
    const h = location.hash.slice(1)
    return tabs.some((t) => t.id === h) ? h : 'dictee'
  }

  let view = $state(leesHash())

  const gezondheid = $derived.by(() => {
    const h = stand.health
    if (!h) return { klasse: '', tekst: 'Verbinden…' }
    if (h.status !== 'ok') return { klasse: 'bad', tekst: 'Backend niet bereikbaar' }
    if (!h.ai_beschikbaar) return { klasse: 'warn', tekst: 'AI niet beschikbaar' }
    return { klasse: 'ok', tekst: 'AI beschikbaar' }
  })

  onMount(() => {
    laadWeken()
    laadHealth()
    const opHash = () => (view = leesHash())
    window.addEventListener('hashchange', opHash)
    return () => window.removeEventListener('hashchange', opHash)
  })
</script>

<header class="top">
  <div class="top-inner">
    <a class="brand" href="#dictee"><span class="zh">听写</span><span class="lat">tīngxiě</span></a>
    <nav class="tabs" aria-label="Hoofdmenu">
      {#each tabs as tab (tab.id)}
        <a href={'#' + tab.id} aria-current={view === tab.id ? 'page' : undefined}>{tab.label}</a>
      {/each}
    </nav>
    <span class="health {gezondheid.klasse}" title="GET /api/health"><i></i>{gezondheid.tekst}</span>
  </div>
</header>

<main class="wrap">
  {#if view === 'dictee'}
    <Dictee />
  {:else if view === 'weken'}
    <Weken />
  {:else}
    <Upload />
  {/if}
</main>
