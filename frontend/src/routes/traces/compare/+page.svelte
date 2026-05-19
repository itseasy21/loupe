<script lang="ts">
  import type { PageData } from './$types';

  export let data: PageData;

  const { comparison } = data;
  const incompleteSelection = comparison === null;

  const statusClasses: Record<string, string> = {
    success: 'bg-signal/15 text-signal',
    running: 'bg-gold/15 text-amber-700',
    error: 'bg-ember/15 text-rose-700'
  };

  const formatDate = (value: string | null) =>
    value
      ? new Intl.DateTimeFormat('en', {
          dateStyle: 'medium',
          timeStyle: 'short'
        }).format(new Date(value))
      : 'Still running';

  const formatDuration = (value: number | null) => (value === null ? 'In progress' : `${Math.round(value)} ms`);

  const statusFor = (status: string) => (status === 'ok' ? 'success' : status === 'unset' ? 'running' : 'error');

  const traceCards = incompleteSelection
    ? []
    : [
        { label: 'Baseline trace', trace: comparison.baseline, status: statusFor(comparison.baseline.status) },
        { label: 'Candidate trace', trace: comparison.candidate, status: statusFor(comparison.candidate.status) }
      ];
</script>

<svelte:head>
  <title>Loupe | Compare traces</title>
</svelte:head>

<section class="space-y-6">
  <a href="/traces" class="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-ink">
    <span aria-hidden="true">&larr;</span>
    Back to traces
  </a>

  <div class="rounded-[2rem] border border-white/70 bg-white/80 p-8 shadow-halo backdrop-blur">
    <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
      <div class="space-y-3">
        <p class="text-sm font-semibold uppercase tracking-[0.3em] text-signal">Trace compare</p>
        <h1 class="text-4xl font-bold leading-none text-ink sm:text-5xl">See where two runs diverged.</h1>
        <p class="max-w-3xl text-base leading-7 text-slate-600">
          Compare summary metrics, evaluation outcomes, metadata, and span behavior side by side without leaving the explorer.
        </p>
      </div>
      <div class="rounded-[1.5rem] bg-mist px-5 py-4 text-sm text-slate-600">
        <p class="uppercase tracking-[0.18em] text-slate-500">Pair</p>
        <p class="mt-2 font-semibold text-ink">{data.left} vs {data.right}</p>
      </div>
    </div>
  </div>

  {#if incompleteSelection}
    <article class="rounded-[1.75rem] border border-dashed border-slate-300 bg-white/75 p-6 shadow-halo backdrop-blur">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Comparison setup</p>
      <h2 class="mt-2 text-2xl font-bold text-ink">Choose two different traces</h2>
      <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
        The compare view needs a baseline and a candidate trace. Start from the trace explorer and choose a compare action on a different run.
      </p>
      <a
        href="/traces"
        class="mt-5 inline-flex rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-400 hover:text-ink"
      >
        Back to trace explorer
      </a>
    </article>
  {:else}
    <div class="grid gap-6 lg:grid-cols-2">
      {#each traceCards as card}
        <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
          <div class="flex flex-wrap items-center gap-3">
            <span class={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${statusClasses[card.status]}`}>
              {card.status}
            </span>
            <span class="text-xs uppercase tracking-[0.2em] text-slate-500">{card.label}</span>
          </div>
          <h2 class="mt-4 text-3xl font-bold text-ink">{card.trace.name}</h2>
          <p class="mt-2 break-all text-sm text-slate-500">{card.trace.trace_id}</p>

          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <div class="rounded-[1.2rem] bg-mist px-4 py-3">
              <p class="text-xs uppercase tracking-[0.16em] text-slate-500">Status</p>
              <p class="mt-2 font-semibold text-ink">{card.trace.status}</p>
            </div>
            <div class="rounded-[1.2rem] bg-mist px-4 py-3">
              <p class="text-xs uppercase tracking-[0.16em] text-slate-500">Duration</p>
              <p class="mt-2 font-semibold text-ink">{formatDuration(card.trace.duration_ms)}</p>
            </div>
            <div class="rounded-[1.2rem] bg-mist px-4 py-3">
              <p class="text-xs uppercase tracking-[0.16em] text-slate-500">Spans</p>
              <p class="mt-2 font-semibold text-ink">{card.trace.span_count}</p>
            </div>
            <div class="rounded-[1.2rem] bg-mist px-4 py-3">
              <p class="text-xs uppercase tracking-[0.16em] text-slate-500">Score</p>
              <p class="mt-2 font-semibold text-ink">{card.trace.score.toFixed(2)}</p>
            </div>
          </div>
        </article>
      {/each}
    </div>

    <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
      <div class="flex items-center justify-between gap-4">
        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Summary metrics</p>
          <h2 class="mt-2 text-2xl font-bold text-ink">Key deltas</h2>
        </div>
      </div>

      {#if comparison.metrics.length === 0}
        <p class="mt-5 text-sm leading-6 text-slate-600">No summary metrics are available for this pair yet.</p>
      {:else}
        <div class="mt-5 overflow-x-auto">
          <table class="min-w-full text-left text-sm text-slate-600">
            <thead>
              <tr class="border-b border-slate-200 text-xs uppercase tracking-[0.18em] text-slate-500">
                <th class="px-4 py-3">Metric</th>
                <th class="px-4 py-3">Baseline</th>
                <th class="px-4 py-3">Candidate</th>
                <th class="px-4 py-3">Delta</th>
              </tr>
            </thead>
            <tbody>
              {#each comparison.metrics as metric}
                <tr class="border-b border-slate-100 last:border-0">
                  <td class="px-4 py-3 font-semibold text-ink">{metric.label}</td>
                  <td class="px-4 py-3">{metric.baseline}</td>
                  <td class="px-4 py-3">{metric.candidate}</td>
                  <td class="px-4 py-3">{metric.delta}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </article>

    <div class="grid gap-6 lg:grid-cols-2">
      <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
        <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Evaluation outcomes</p>
        {#if comparison.outcomes.length === 0}
          <p class="mt-4 text-sm leading-6 text-slate-600">No evaluation outcomes are available for this pair yet.</p>
        {:else}
          <div class="mt-4 space-y-3">
            {#each comparison.outcomes as outcome}
              <div class="rounded-[1.25rem] border px-4 py-3 {outcome.changed ? 'border-amber-200 bg-amber-50/70' : 'border-slate-200 bg-mist'}">
                <div class="flex items-center justify-between gap-4">
                  <p class="font-semibold text-ink">{outcome.label}</p>
                  <span class="text-xs uppercase tracking-[0.18em] text-slate-500">{outcome.changed ? 'Changed' : 'Same'}</span>
                </div>
                <div class="mt-3 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
                  <p><span class="font-medium text-ink">Baseline:</span> {outcome.baseline}</p>
                  <p><span class="font-medium text-ink">Candidate:</span> {outcome.candidate}</p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </article>

      <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
        <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Metadata differences</p>
        {#if comparison.metadataDifferences.length === 0}
          <p class="mt-4 text-sm leading-6 text-slate-600">Metadata matches across both traces.</p>
        {:else}
          <div class="mt-4 space-y-3">
            {#each comparison.metadataDifferences as difference}
              <div class="rounded-[1.25rem] bg-mist px-4 py-3">
                <p class="text-xs uppercase tracking-[0.18em] text-slate-500">{difference.key}</p>
                <div class="mt-3 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
                  <p><span class="font-medium text-ink">Baseline:</span> {difference.baseline}</p>
                  <p><span class="font-medium text-ink">Candidate:</span> {difference.candidate}</p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </article>
    </div>

    <div class="grid gap-6 lg:grid-cols-2">
      <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
        <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Span differences</p>
        {#if comparison.spanDifferences.length === 0}
          <p class="mt-4 text-sm leading-6 text-slate-600">No notable span differences were reported.</p>
        {:else}
          <div class="mt-4 space-y-3">
            {#each comparison.spanDifferences as difference}
              <div class="rounded-[1.25rem] bg-mist px-4 py-3">
                <div class="flex items-center justify-between gap-4">
                  <p class="font-semibold text-ink">{difference.name}</p>
                  <p class="text-xs uppercase tracking-[0.18em] text-slate-500">{difference.note}</p>
                </div>
                <div class="mt-3 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
                  <p>
                    <span class="font-medium text-ink">Baseline:</span>
                    {difference.baselineStatus ?? 'missing'} · {formatDuration(difference.baselineDurationMs)}
                  </p>
                  <p>
                    <span class="font-medium text-ink">Candidate:</span>
                    {difference.candidateStatus ?? 'missing'} · {formatDuration(difference.candidateDurationMs)}
                  </p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </article>

      <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
        <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Error differences</p>
        {#if comparison.errorDifferences.length === 0}
          <p class="mt-4 text-sm leading-6 text-slate-600">No error-specific differences were reported.</p>
        {:else}
          <div class="mt-4 space-y-3">
            {#each comparison.errorDifferences as difference}
              <div class="rounded-[1.25rem] border border-ember/20 bg-ember/5 px-4 py-3">
                <div class="flex items-center justify-between gap-4">
                  <p class="font-semibold text-ink">{difference.name}</p>
                  <p class="text-xs uppercase tracking-[0.18em] text-rose-700">{difference.note}</p>
                </div>
                <div class="mt-3 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
                  <p>
                    <span class="font-medium text-ink">Baseline:</span>
                    {difference.baselineStatus ?? 'missing'} · {formatDuration(difference.baselineDurationMs)}
                  </p>
                  <p>
                    <span class="font-medium text-ink">Candidate:</span>
                    {difference.candidateStatus ?? 'missing'} · {formatDuration(difference.candidateDurationMs)}
                  </p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </article>
    </div>
  {/if}
</section>
