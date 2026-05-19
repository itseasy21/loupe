<script lang="ts">
  import '../app.css';

  const nav = [
    { label: 'Home', href: '/', enabled: true },
    { label: 'Traces', href: '/traces', enabled: true },
    { label: 'Replay', href: '/replay', enabled: false },
    { label: 'Dashboard', href: '/dashboard', enabled: false }
  ];
</script>

<svelte:head>
  <title>Loupe</title>
  <meta
    name="description"
    content="Loupe is the open-source debugger for AI agents, built for trace exploration, replay, and causal analysis."
  />
</svelte:head>

<div class="min-h-screen text-ink">
  <div class="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-6 sm:px-10 lg:px-12">
    <header class="flex flex-col gap-6 rounded-[2rem] border border-white/70 bg-white/75 px-6 py-5 shadow-halo backdrop-blur md:flex-row md:items-center md:justify-between">
      <div class="space-y-2">
        <div class="inline-flex items-center gap-2 rounded-full border border-signal/20 bg-signal/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-signal">
          Self-hosted AI debugging
        </div>
        <a href="/" class="inline-flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-2xl bg-ink text-lg font-bold text-mist">L</span>
          <div>
            <p class="text-2xl font-bold leading-none">Loupe</p>
            <p class="text-sm text-slate-600">Trace every branch, replay every decision.</p>
          </div>
        </a>
      </div>

      <nav class="flex flex-wrap items-center gap-3 text-sm font-medium text-slate-600">
        {#each nav as item}
          <a
            href={item.href}
            aria-disabled={!item.enabled}
            class:text-slate-400={!item.enabled}
            class:pointer-events-none={!item.enabled}
            class="rounded-full border border-slate-200 bg-white px-4 py-2 transition hover:border-slate-300 hover:text-ink"
          >
            {item.label}
            {#if !item.enabled}
              <span class="ml-2 text-[0.65rem] uppercase tracking-[0.2em]">Soon</span>
            {/if}
          </a>
        {/each}
      </nav>
    </header>

    <main class="flex-1 py-8">
      <slot />
    </main>
  </div>
</div>
