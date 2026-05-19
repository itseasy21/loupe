<script lang="ts">
  import type { TraceEvaluationDimension } from '$lib';
  import type { PageData } from './$types';

  export let data: PageData;

  const trace = data.trace;
  const causalAnalysis = data.causalAnalysis;
  const evaluationSummary = data.evaluationSummary;

  const status = !trace.ended_at
    ? 'running'
    : trace.spans.some((span) => span.status.toLowerCase() === 'error')
      ? 'error'
      : 'success';

  const statusClasses: Record<string, string> = {
    success: 'bg-signal/15 text-signal',
    running: 'bg-gold/15 text-amber-700',
    error: 'bg-ember/15 text-rose-700'
  };

  const evaluationStatusClasses: Record<'pass' | 'fail', string> = {
    pass: 'bg-signal/15 text-signal',
    fail: 'bg-ember/15 text-rose-700'
  };

  const formatDate = (value: string | null) =>
    value
      ? new Intl.DateTimeFormat('en', {
          dateStyle: 'medium',
          timeStyle: 'short'
        }).format(new Date(value))
      : 'Still running';

  const formatDuration = (value: number | null) => (value === null ? 'In progress' : `${Math.round(value)} ms`);
  const formatScore = (value: number | null) => (value === null ? 'Pending' : `${Math.round(value * 100)}%`);
  const stringify = (value: unknown) => JSON.stringify(value, null, 2);
  const compareHref = '/traces';

  const errorSpans = trace.spans.filter((span) => span.error || span.status.toLowerCase() === 'error');
  const outputSpans = trace.spans.filter((span) => Object.keys(span.outputs).length > 0);
</script>

<svelte:head>
  <title>Loupe | {trace.name}</title>
</svelte:head>

<section class="space-y-6">
  <a href="/traces" class="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-ink">
    <span aria-hidden="true">&larr;</span>
    Back to traces
  </a>

  <div class="rounded-[2rem] border border-white/70 bg-white/80 p-8 shadow-halo backdrop-blur">
    <div class="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
      <div class="space-y-4">
        <div class="flex flex-wrap items-center gap-3">
          <span class={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${statusClasses[status]}`}>
            {status}
          </span>
          <span class="text-xs uppercase tracking-[0.2em] text-slate-500">{trace.trace_id}</span>
        </div>
        <div>
          <p class="text-sm uppercase tracking-[0.24em] text-signal">Trace detail</p>
          <h1 class="mt-3 text-4xl font-bold text-ink sm:text-5xl">{trace.name}</h1>
          <p class="mt-3 max-w-3xl text-base leading-7 text-slate-600">
            Review metadata, inspect span-level execution, and compare structured outputs with the stored raw trace payload.
          </p>
        </div>
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:min-w-[26rem]">
        <a
          href={compareHref}
          class="rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-600 transition hover:border-signal/30 hover:text-ink sm:col-span-2"
        >
          Choose another trace to compare
        </a>
        <div class="rounded-[1.25rem] bg-mist px-4 py-3">
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Started</p>
          <p class="mt-2 font-semibold text-ink">{formatDate(trace.started_at)}</p>
        </div>
        <div class="rounded-[1.25rem] bg-mist px-4 py-3">
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Finished</p>
          <p class="mt-2 font-semibold text-ink">{formatDate(trace.ended_at)}</p>
        </div>
        <div class="rounded-[1.25rem] bg-mist px-4 py-3">
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Duration</p>
          <p class="mt-2 font-semibold text-ink">{formatDuration(trace.duration_ms)}</p>
        </div>
        <div class="rounded-[1.25rem] bg-mist px-4 py-3">
          <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Spans</p>
          <p class="mt-2 font-semibold text-ink">{trace.spans.length}</p>
        </div>
      </div>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
    <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Metadata</p>
      {#if Object.keys(trace.metadata).length === 0}
        <p class="mt-4 text-sm leading-6 text-slate-600">No trace metadata was captured for this run.</p>
      {:else}
        <dl class="mt-4 space-y-4">
          {#each Object.entries(trace.metadata) as [key, value]}
            <div class="rounded-[1.25rem] bg-mist px-4 py-3">
              <dt class="text-xs uppercase tracking-[0.18em] text-slate-500">{key}</dt>
              <dd class="mt-2 break-all text-sm font-medium text-ink">{typeof value === 'string' ? value : stringify(value)}</dd>
            </div>
          {/each}
        </dl>
      {/if}
    </article>

    <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Evaluation summary</p>
          <h2 class="mt-2 text-2xl font-bold text-ink">Quality verdict</h2>
        </div>
        {#if evaluationSummary}
          <span class={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${evaluationStatusClasses[evaluationSummary.passed ? 'pass' : 'fail']}`}>
            {evaluationSummary.passed ? 'pass' : 'fail'}
          </span>
        {/if}
      </div>

      {#if !evaluationSummary}
        <p class="mt-4 text-sm leading-6 text-slate-600">No evaluation summary is available for this trace yet.</p>
      {:else}
        <div class="mt-5 grid gap-4 sm:grid-cols-3">
          <div class="rounded-[1.25rem] bg-mist px-4 py-3">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Overall score</p>
            <p class="mt-2 text-2xl font-bold text-ink">{formatScore(evaluationSummary.score)}</p>
          </div>
          <div class="rounded-[1.25rem] bg-mist px-4 py-3">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Result</p>
            <p class="mt-2 font-semibold text-ink">{evaluationSummary.reason}</p>
          </div>
          <div class="rounded-[1.25rem] bg-mist px-4 py-3">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Dimensions</p>
            <p class="mt-2 text-2xl font-bold text-ink">{Object.keys(evaluationSummary.dimensions).length}</p>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          {#each Object.entries(evaluationSummary.dimensions) as [dimension, payload]}
            <div class="rounded-[1.25rem] border border-slate-200 bg-white px-4 py-4">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div class="flex flex-wrap items-center gap-3">
                    <p class="font-semibold capitalize text-ink">{dimension}</p>
                    <span class={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] ${evaluationStatusClasses[payload.passed ? 'pass' : 'fail']}`}>
                      {payload.passed ? 'pass' : 'fail'}
                    </span>
                  </div>
                  <p class="mt-2 text-sm leading-6 text-slate-600">{payload.reason}</p>
                </div>
                <div class="rounded-[1rem] bg-mist px-3 py-2 text-right">
                  <p class="text-[11px] uppercase tracking-[0.18em] text-slate-500">Score</p>
                  <p class="mt-1 font-semibold text-ink">{formatScore(payload.score)}</p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </article>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
    <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Causal analysis</p>
          <h2 class="mt-2 text-2xl font-bold text-ink">Likely drivers</h2>
        </div>
      </div>

      {#if !causalAnalysis}
        <p class="mt-4 text-sm leading-6 text-slate-600">No causal analysis is available for this trace yet.</p>
      {:else}
        <div class="mt-5 grid gap-4 sm:grid-cols-3">
          <div class="rounded-[1.25rem] bg-mist px-4 py-3">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Nodes</p>
            <p class="mt-2 text-2xl font-bold text-ink">{causalAnalysis.nodes.length}</p>
          </div>
          <div class="rounded-[1.25rem] bg-mist px-4 py-3">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Edges</p>
            <p class="mt-2 text-2xl font-bold text-ink">{Object.values(causalAnalysis.edges).reduce((count, entries) => count + entries.length, 0)}</p>
          </div>
          <div class="rounded-[1.25rem] bg-mist px-4 py-3">
            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Likely causes</p>
            <p class="mt-2 text-2xl font-bold text-ink">{causalAnalysis.likely_causes.length}</p>
          </div>
        </div>

        <div class="mt-5 grid gap-3 rounded-[1.5rem] border border-slate-200 bg-white p-5 sm:grid-cols-2 xl:grid-cols-3">
          {#each causalAnalysis.nodes as node}
            <div class="rounded-[1.2rem] bg-mist px-4 py-3">
              <div class="flex items-center justify-between gap-3">
                <p class="font-semibold text-ink">{node.name}</p>
                <span class={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] ${statusClasses[node.status === 'ok' ? 'success' : node.status === 'unset' ? 'running' : 'error']}`}>
                  {node.status}
                </span>
              </div>
              <p class="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">{node.kind}</p>
              <p class="mt-2 text-xs text-slate-500">Parent {node.parent_id ?? 'root'}</p>
            </div>
          {/each}
        </div>

        <div class="mt-5 space-y-4">
          {#each causalAnalysis.likely_causes as cause}
            <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div class="flex flex-wrap items-center gap-3">
                    <h3 class="text-lg font-bold text-ink">{cause.name}</h3>
                    <span class="rounded-full bg-ember/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-rose-700">
                      score {cause.score.toFixed(3)}
                    </span>
                  </div>
                  <p class="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">Span {cause.span_id}</p>
                </div>
              </div>

              {#if cause.reasons.length > 0}
                <ul class="mt-4 space-y-2 text-sm leading-6 text-slate-700">
                  {#each cause.reasons as reason}
                    <li>{reason}</li>
                  {/each}
                </ul>
              {/if}
            </article>
          {/each}
        </div>
      {/if}
    </article>

    <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
      <div class="flex items-center justify-between gap-4">
        <div>
          <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Span timeline</p>
          <h2 class="mt-2 text-2xl font-bold text-ink">Execution path</h2>
        </div>
      </div>

      <div class="mt-5 space-y-4">
        {#each trace.spans as span}
          <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5">
            <div class="flex flex-col gap-4">
              <div>
                <div class="flex flex-wrap items-center gap-3">
                  <span class={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${statusClasses[span.status.toLowerCase()] ?? 'bg-slate-200 text-slate-700'}`}>
                    {span.status}
                  </span>
                  <span class="text-xs uppercase tracking-[0.2em] text-slate-500">{span.kind}</span>
                </div>
                <h3 class="mt-3 text-xl font-bold text-ink">{span.name}</h3>
                <p class="mt-2 text-sm text-slate-500">Span ID {span.span_id}{span.parent_id ? ` · Parent ${span.parent_id}` : ''}</p>
              </div>
              <div class="grid gap-3 text-sm text-slate-600 sm:grid-cols-3">
                <div class="rounded-[1rem] bg-mist px-3 py-2">
                  <p class="uppercase tracking-[0.16em] text-slate-500">Started</p>
                  <p class="mt-2 font-semibold text-ink">{formatDate(span.started_at)}</p>
                </div>
                <div class="rounded-[1rem] bg-mist px-3 py-2">
                  <p class="uppercase tracking-[0.16em] text-slate-500">Finished</p>
                  <p class="mt-2 font-semibold text-ink">{formatDate(span.ended_at)}</p>
                </div>
                <div class="rounded-[1rem] bg-mist px-3 py-2">
                  <p class="uppercase tracking-[0.16em] text-slate-500">Duration</p>
                  <p class="mt-2 font-semibold text-ink">{formatDuration(span.duration_ms)}</p>
                </div>
              </div>
            </div>

            <div class="mt-4 grid gap-4 xl:grid-cols-3">
              <div class="rounded-[1rem] bg-mist px-4 py-3">
                <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Attributes</p>
                <pre class="mt-3 overflow-x-auto text-xs leading-6 text-slate-700">{stringify(span.attributes)}</pre>
              </div>
              <div class="rounded-[1rem] bg-mist px-4 py-3">
                <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Inputs</p>
                <pre class="mt-3 overflow-x-auto text-xs leading-6 text-slate-700">{stringify(span.inputs)}</pre>
              </div>
              <div class="rounded-[1rem] bg-mist px-4 py-3">
                <p class="text-xs uppercase tracking-[0.18em] text-slate-500">Outputs</p>
                <pre class="mt-3 overflow-x-auto text-xs leading-6 text-slate-700">{stringify(span.outputs)}</pre>
              </div>
            </div>
          </article>
        {/each}
      </div>
    </article>
  </div>

  <div class="grid gap-6 lg:grid-cols-2">
    <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Error spans</p>
      {#if errorSpans.length === 0}
        <p class="mt-4 text-sm leading-6 text-slate-600">No span errors were recorded for this trace.</p>
      {:else}
        <div class="mt-4 space-y-4">
          {#each errorSpans as span}
            <div class="rounded-[1.25rem] border border-ember/20 bg-ember/5 px-4 py-3">
              <p class="font-semibold text-ink">{span.name}</p>
              <p class="mt-2 text-sm leading-6 text-rose-700">{span.error ?? 'Span status marked as error without a message.'}</p>
            </div>
          {/each}
        </div>
      {/if}
    </article>

    <article class="rounded-[1.75rem] border border-white/70 bg-white/75 p-6 shadow-halo backdrop-blur">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-500">Structured outputs</p>
      {#if outputSpans.length === 0}
        <p class="mt-4 text-sm leading-6 text-slate-600">No span outputs were stored for this trace.</p>
      {:else}
        <div class="mt-4 space-y-4">
          {#each outputSpans as span}
            <div class="rounded-[1.25rem] bg-mist px-4 py-3">
              <p class="font-semibold text-ink">{span.name}</p>
              <pre class="mt-3 overflow-x-auto text-xs leading-6 text-slate-700">{stringify(span.outputs)}</pre>
            </div>
          {/each}
        </div>
      {/if}
    </article>
  </div>

  <article class="rounded-[1.75rem] border border-ink/10 bg-ink p-6 text-mist shadow-halo">
    <p class="text-sm uppercase tracking-[0.2em] text-slate-300">Raw JSON</p>
    <pre class="mt-4 overflow-x-auto text-xs leading-6 text-slate-100">{stringify({ trace, causalAnalysis, evaluationSummary })}</pre>
  </article>
</section>
