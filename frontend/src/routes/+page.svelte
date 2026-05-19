<script lang="ts">
  import type { PageData } from './$types';

  export let data: PageData;

  const statusClasses: Record<string, string> = {
    success: 'bg-signal/15 text-signal',
    running: 'bg-gold/15 text-amber-700',
    error: 'bg-ember/15 text-rose-700'
  };
</script>

<svelte:head>
  <title>Loupe | Agent Trace Studio</title>
</svelte:head>

<section class="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
  <div class="space-y-6 rounded-[2rem] border border-white/70 bg-white/80 p-8 shadow-halo backdrop-blur">
    <div class="space-y-5">
      <p class="text-sm font-semibold uppercase tracking-[0.3em] text-signal">Frontend scaffold</p>
      <h1 class="max-w-2xl text-5xl font-bold leading-[0.95] text-ink sm:text-6xl">
        Inspect what your agent actually did.
      </h1>
      <p class="max-w-xl text-base leading-7 text-slate-600 sm:text-lg">
        Loupe pairs local trace storage with a focused dashboard for replay, causal analysis,
        and evaluation. This scaffold sets the tone for upcoming explorer and detail views
        without pretending the whole product is already here.
      </p>
    </div>

    <div class="grid gap-4 sm:grid-cols-3">
      {#each data.metrics as metric}
        <article class="rounded-[1.5rem] border border-slate-200/80 bg-mist px-5 py-4">
          <p class="text-sm uppercase tracking-[0.18em] text-slate-500">{metric.label}</p>
          <p class="mt-3 text-3xl font-bold text-ink">{metric.value}</p>
          <p class="mt-2 text-sm text-slate-600">{metric.detail}</p>
        </article>
      {/each}
    </div>

    <div class="flex flex-wrap gap-3 text-sm font-medium">
      <a href="https://github.com/loupe/loupe" class="rounded-full bg-ink px-5 py-3 text-mist transition hover:bg-slate-800">
        View repository
      </a>
      <a href="/traces" class="rounded-full border border-slate-300 px-5 py-3 text-slate-500">
        Trace explorer coming next
      </a>
    </div>
  </div>

  <aside class="space-y-5 rounded-[2rem] border border-ink/10 bg-ink p-6 text-mist shadow-halo">
    <div>
      <p class="text-sm uppercase tracking-[0.2em] text-slate-300">Launch queue</p>
      <h2 class="mt-3 text-2xl font-bold">Recent traces</h2>
    </div>

    <div class="space-y-4">
      {#each data.traces as trace}
        <article class="rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm text-slate-300">{trace.agent}</p>
              <h3 class="mt-1 text-lg font-semibold">{trace.title}</h3>
            </div>
            <span class={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${statusClasses[trace.status]}`}>
              {trace.status}
            </span>
          </div>

          <dl class="mt-4 grid grid-cols-3 gap-3 text-sm text-slate-300">
            <div>
              <dt>Duration</dt>
              <dd class="mt-1 font-semibold text-mist">{trace.durationMs === null ? 'Running' : `${Math.round(trace.durationMs)} ms`}</dd>
            </div>
            <div>
              <dt>Spans</dt>
              <dd class="mt-1 font-semibold text-mist">{trace.spanCount}</dd>
            </div>
            <div>
              <dt>State</dt>
              <dd class="mt-1 font-semibold text-mist">{trace.endedAt ? 'Complete' : 'Pending'}</dd>
            </div>
          </dl>
        </article>
      {/each}
    </div>
  </aside>
</section>

<section class="mt-6 grid gap-6 lg:grid-cols-3">
  <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
    <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Ready for T-057</p>
    <h2 class="mt-3 text-2xl font-bold text-ink">Trace explorer foundation</h2>
    <p class="mt-3 text-sm leading-6 text-slate-600">
      Typed helpers already expose summary and dashboard data so the next pass can switch from
      demo values to FastAPI responses with minimal churn.
    </p>
  </article>

  <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
    <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Ready for T-058</p>
    <h2 class="mt-3 text-2xl font-bold text-ink">Detail page patterns</h2>
    <p class="mt-3 text-sm leading-6 text-slate-600">
      The shell keeps navigation, metadata, and visual language in place so trace detail work can
      focus on data-rich panels instead of redoing layout setup.
    </p>
  </article>

  <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
    <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Ready for API wiring</p>
    <h2 class="mt-3 text-2xl font-bold text-ink">Local-first client layer</h2>
    <p class="mt-3 text-sm leading-6 text-slate-600">
      `src/lib/api.ts` and `src/lib/types.ts` provide a small typed seam for future dashboard and
      trace endpoints without adding abstractions the scaffold does not need yet.
    </p>
  </article>
</section>
