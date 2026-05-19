<script lang="ts">
  import type { PageData } from './$types';

  export let data: PageData;

  const statusClasses: Record<string, string> = {
    success: 'bg-signal/15 text-signal',
    running: 'bg-gold/15 text-amber-700',
    error: 'bg-ember/15 text-rose-700'
  };

  const formatDate = (value: string) =>
    new Intl.DateTimeFormat('en', {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(new Date(value));

  const formatDuration = (value: number | null) => (value === null ? 'In progress' : `${Math.round(value)} ms`);

  const createPageHref = (page: number) => {
    const params = new URLSearchParams();
    if (data.search) {
      params.set('search', data.search);
    }
    params.set('page', String(page));
    return `/traces?${params.toString()}`;
  };
</script>

<svelte:head>
  <title>Loupe | Trace Explorer</title>
</svelte:head>

<section class="space-y-6">
  <div class="rounded-[2rem] border border-white/70 bg-white/80 p-8 shadow-halo backdrop-blur">
    <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
      <div class="space-y-3">
        <p class="text-sm font-semibold uppercase tracking-[0.3em] text-signal">Trace explorer</p>
        <h1 class="text-4xl font-bold leading-none text-ink sm:text-5xl">Find the run you need without leaving the timeline.</h1>
        <p class="max-w-2xl text-base leading-7 text-slate-600">
          Search recorded traces, scan status at a glance, and jump from the queue into full execution detail.
        </p>
      </div>

      <form method="GET" class="flex w-full max-w-xl flex-col gap-3 sm:flex-row">
        <input
          type="search"
          name="search"
          value={data.search}
          placeholder="Search by trace name, span input, or metadata"
          class="min-w-0 flex-1 rounded-full border border-slate-200 bg-mist px-5 py-3 text-sm text-ink outline-none transition focus:border-signal"
        />
        <button type="submit" class="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-mist transition hover:bg-slate-800">
          Search
        </button>
      </form>
    </div>
  </div>

  <div class="grid gap-4 sm:grid-cols-3">
    <article class="rounded-[1.5rem] border border-white/70 bg-white/75 p-5 shadow-halo backdrop-blur">
      <p class="text-sm uppercase tracking-[0.18em] text-slate-500">Matching traces</p>
      <p class="mt-3 text-3xl font-bold text-ink">{data.traces.total}</p>
      <p class="mt-2 text-sm text-slate-600">Across the current search query.</p>
    </article>
    <article class="rounded-[1.5rem] border border-white/70 bg-white/75 p-5 shadow-halo backdrop-blur">
      <p class="text-sm uppercase tracking-[0.18em] text-slate-500">Current page</p>
      <p class="mt-3 text-3xl font-bold text-ink">{data.page}</p>
      <p class="mt-2 text-sm text-slate-600">Showing up to {data.traces.limit} traces at a time.</p>
    </article>
    <article class="rounded-[1.5rem] border border-white/70 bg-white/75 p-5 shadow-halo backdrop-blur">
      <p class="text-sm uppercase tracking-[0.18em] text-slate-500">Errors in view</p>
      <p class="mt-3 text-3xl font-bold text-ink">{data.traces.items.filter((trace) => trace.status === 'error').length}</p>
      <p class="mt-2 text-sm text-slate-600">Use detail pages to inspect failed spans and raw payloads.</p>
    </article>
  </div>

  {#if data.traces.items.length === 0}
    <div class="rounded-[2rem] border border-dashed border-slate-300 bg-white/70 p-10 text-center shadow-halo backdrop-blur">
      <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">No traces found</p>
      <h2 class="mt-3 text-2xl font-bold text-ink">Try a broader search query.</h2>
      <p class="mt-3 text-sm leading-6 text-slate-600">
        Loupe searched the current trace index but did not find any matches for this filter.
      </p>
    </div>
  {:else}
    <div class="space-y-4">
      {#each data.traces.items as trace}
        <div class="rounded-[1.75rem] border border-white/70 bg-white/80 p-6 shadow-halo backdrop-blur transition hover:-translate-y-0.5 hover:border-signal/30">
          <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <a href={`/traces/${trace.id}`} class="block space-y-3 lg:flex-1">
              <div class="flex flex-wrap items-center gap-3">
                <span class={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${statusClasses[trace.status]}`}>
                  {trace.status}
                </span>
                <span class="text-xs uppercase tracking-[0.2em] text-slate-500">{trace.id}</span>
              </div>
              <div>
                <p class="text-sm text-slate-500">{trace.agent}</p>
                <h2 class="mt-1 text-2xl font-bold text-ink">{trace.title}</h2>
              </div>
            </a>

            <div class="grid gap-3 text-sm text-slate-600 sm:grid-cols-3 lg:min-w-[23rem]">
              <div class="rounded-[1.2rem] bg-mist px-4 py-3">
                <p class="uppercase tracking-[0.16em] text-slate-500">Started</p>
                <p class="mt-2 font-semibold text-ink">{formatDate(trace.startedAt)}</p>
              </div>
              <div class="rounded-[1.2rem] bg-mist px-4 py-3">
                <p class="uppercase tracking-[0.16em] text-slate-500">Duration</p>
                <p class="mt-2 font-semibold text-ink">{formatDuration(trace.durationMs)}</p>
              </div>
              <div class="rounded-[1.2rem] bg-mist px-4 py-3">
                <p class="uppercase tracking-[0.16em] text-slate-500">Spans</p>
                <p class="mt-2 font-semibold text-ink">{trace.spanCount}</p>
              </div>
            </div>
          </div>

          <div class="mt-5 flex flex-wrap gap-3 border-t border-slate-200 pt-4">
            {#if data.traces.items.some((candidate) => candidate.id !== trace.id)}
              <a
                href={`/traces/compare?left=${trace.id}&right=${data.traces.items.find((candidate) => candidate.id !== trace.id)?.id}`}
                class="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-400 hover:text-ink"
              >
                Compare from here
              </a>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <div class="flex items-center justify-between rounded-[1.5rem] border border-white/70 bg-white/75 px-5 py-4 shadow-halo backdrop-blur">
      <a
        href={data.page > 1 ? createPageHref(data.page - 1) : '#'}
        aria-disabled={data.page === 1}
        class="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-400 hover:text-ink disabled:pointer-events-none"
        class:pointer-events-none={data.page === 1}
        class:text-slate-300={data.page === 1}
      >
        Previous
      </a>
      <p class="text-sm text-slate-600">Page {data.page} of {data.pageCount}</p>
      <a
        href={data.page < data.pageCount ? createPageHref(data.page + 1) : '#'}
        aria-disabled={data.page === data.pageCount}
        class="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-400 hover:text-ink"
        class:pointer-events-none={data.page === data.pageCount}
        class:text-slate-300={data.page === data.pageCount}
      >
        Next
      </a>
    </div>
  {/if}
</section>
