import { error } from '@sveltejs/kit';

import type {
  CompareMetric,
  CompareOutcome,
  CompareSpanDifference,
  CompareValueDifference,
  DashboardMetric,
  TraceCausalAnalysis,
  TraceComparePayload,
  TraceDetail,
  TraceEvaluationSummary,
  TraceListResponse,
  TraceStatus,
  TraceSummary
} from '$lib/types';

const API_BASE_URL = import.meta.env.PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';
const DEFAULT_TRACE_LIMIT = 12;

const demoMetrics: DashboardMetric[] = [
  { label: 'Traces retained', value: '128', detail: 'Local SQLite history' },
  { label: 'Median latency', value: '1.8s', detail: 'Across latest 24 runs' },
  { label: 'Eval coverage', value: '74%', detail: 'Correctness and safety checks' }
];

function buildTraceListUrl(limit: number, offset: number, search: string): URL {
  const url = new URL('/traces', API_BASE_URL);
  url.searchParams.set('limit', String(limit));
  url.searchParams.set('offset', String(offset));
  if (search.trim()) {
    url.searchParams.set('search', search.trim());
  }
  return url;
}

function deriveTraceStatus(detail: TraceDetail): TraceStatus {
  if (!detail.ended_at) {
    return 'running';
  }

  return detail.spans.some((span) => span.status.toLowerCase() === 'error') ? 'error' : 'success';
}

function mapTraceSummary(item: Record<string, unknown>): TraceSummary {
  return {
    id: String(item.trace_id),
    agent: String(item.name),
    title: String(item.name),
    status: String(item.status) as TraceStatus,
    startedAt: String(item.started_at),
    endedAt: item.ended_at ? String(item.ended_at) : null,
    durationMs: typeof item.duration_ms === 'number' ? item.duration_ms : null,
    spanCount: typeof item.span_count === 'number' ? item.span_count : 0
  };
}

function formatCompareValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '—';
  }

  return typeof value === 'string' ? value : JSON.stringify(value);
}

function impactFromScore(score: number): 'high' | 'medium' | 'low' | 'unknown' {
  if (score >= 1.4) {
    return 'high';
  }
  if (score >= 1.0) {
    return 'medium';
  }
  if (score > 0) {
    return 'low';
  }
  return 'unknown';
}

function mapCompareMetric(item: CompareMetric): CompareMetric {
  return item;
}

function mapCompareOutcome(item: CompareOutcome): CompareOutcome {
  return item;
}

function mapCompareValueDifference(item: CompareValueDifference): CompareValueDifference {
  return item;
}

function mapCompareSpanDifference(item: CompareSpanDifference): CompareSpanDifference {
  return item;
}

export async function listTraceSummaries(
  fetchFn: typeof fetch,
  options: { limit?: number; offset?: number; search?: string } = {}
): Promise<TraceListResponse> {
  const limit = options.limit ?? DEFAULT_TRACE_LIMIT;
  const offset = options.offset ?? 0;
  const search = options.search ?? '';
  const response = await fetchFn(buildTraceListUrl(limit, offset, search));

  if (!response.ok) {
    throw error(response.status, 'Failed to load traces');
  }

  const payload = (await response.json()) as {
    items: Array<Record<string, unknown>>;
    total: number;
    limit: number;
    offset: number;
  };

  return {
    items: payload.items.map(mapTraceSummary),
    total: payload.total,
    limit: payload.limit,
    offset: payload.offset
  };
}

export async function getTraceDetail(fetchFn: typeof fetch, traceId: string): Promise<TraceDetail> {
  const response = await fetchFn(new URL(`/traces/${traceId}`, API_BASE_URL));

  if (response.status === 404) {
    throw error(404, 'Trace not found');
  }

  if (!response.ok) {
    throw error(response.status, 'Failed to load trace');
  }

  const payload = (await response.json()) as TraceDetail;
  return {
    ...payload,
    duration_ms: payload.duration_ms,
    spans: payload.spans.map((span) => ({
      ...span,
      duration_ms: span.duration_ms,
      error: span.error ?? null
    }))
  };
}

export async function getTraceCausalAnalysis(fetchFn: typeof fetch, traceId: string): Promise<TraceCausalAnalysis | null> {
  const response = await fetchFn(new URL(`/traces/${traceId}/graph`, API_BASE_URL));

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw error(response.status, 'Failed to load causal analysis');
  }

  const payload = (await response.json()) as {
    trace_id: string;
    name: string;
    nodes: TraceCausalAnalysis['nodes'];
    edges: Record<string, string[]>;
    likely_causes: Array<{
      span_id: string;
      name: string;
      score: number;
      reasons: string[];
    }>;
  };

  return {
    trace_id: payload.trace_id,
    name: payload.name,
    nodes: payload.nodes,
    edges: payload.edges,
    likely_causes: payload.likely_causes.map((cause) => ({
      ...cause,
      reasons: cause.reasons ?? []
    }))
  };
}

export async function getTraceEvaluationSummary(
  fetchFn: typeof fetch,
  traceId: string
): Promise<TraceEvaluationSummary | null> {
  const response = await fetchFn(new URL(`/traces/${traceId}/evaluation`, API_BASE_URL));

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw error(response.status, 'Failed to load evaluation summary');
  }

  const payload = (await response.json()) as TraceEvaluationSummary;
  return payload;
}

export async function getTraceCompare(
  fetchFn: typeof fetch,
  leftTraceId: string,
  rightTraceId: string
): Promise<TraceComparePayload> {
  const response = await fetchFn(
    new URL(
      `/traces/compare?baseline=${encodeURIComponent(leftTraceId)}&candidate=${encodeURIComponent(rightTraceId)}`,
      API_BASE_URL
    )
  );

  if (response.status === 404) {
    throw error(404, 'One or both traces were not found');
  }

  if (!response.ok) {
    throw error(response.status, 'Failed to load trace comparison');
  }

  const payload = (await response.json()) as {
    baseline: TraceComparePayload['baseline'];
    candidate: TraceComparePayload['candidate'];
    delta: TraceComparePayload['delta'];
  };

  return {
    baseline: payload.baseline,
    candidate: payload.candidate,
    delta: payload.delta,
    metrics: [
      {
        label: 'Score',
        baseline: payload.baseline.score.toFixed(2),
        candidate: payload.candidate.score.toFixed(2),
        delta: payload.delta.score >= 0 ? `+${payload.delta.score.toFixed(2)}` : payload.delta.score.toFixed(2)
      },
      {
        label: 'Span count',
        baseline: String(payload.baseline.span_count),
        candidate: String(payload.candidate.span_count),
        delta:
          payload.delta.span_count >= 0
            ? `+${payload.delta.span_count}`
            : String(payload.delta.span_count)
      },
      {
        label: 'Duration',
        baseline: payload.baseline.duration_ms === null ? '—' : `${Math.round(payload.baseline.duration_ms)} ms`,
        candidate:
          payload.candidate.duration_ms === null ? '—' : `${Math.round(payload.candidate.duration_ms)} ms`,
        delta:
          payload.delta.duration_ms === null
            ? '—'
            : payload.delta.duration_ms >= 0
              ? `+${Math.round(payload.delta.duration_ms)} ms`
              : `${Math.round(payload.delta.duration_ms)} ms`
      }
    ].map(mapCompareMetric),
    outcomes: [
      {
        label: 'Status',
        baseline: payload.baseline.status,
        candidate: payload.candidate.status,
        changed: payload.baseline.status !== payload.candidate.status
      },
      {
        label: 'Evaluation verdict',
        baseline: payload.baseline.passed ? 'pass' : 'fail',
        candidate: payload.candidate.passed ? 'pass' : 'fail',
        changed: payload.baseline.passed !== payload.candidate.passed
      }
    ].map(mapCompareOutcome),
    metadataDifferences: [
      {
        key: 'Failed dimensions',
        baseline: payload.baseline.failed_dimensions.join(', ') || 'None',
        candidate: payload.candidate.failed_dimensions.join(', ') || 'None'
      }
    ].map(mapCompareValueDifference),
    spanDifferences: [
      {
        name: 'Trace summary',
        baselineStatus: payload.baseline.status,
        candidateStatus: payload.candidate.status,
        baselineDurationMs: payload.baseline.duration_ms,
        candidateDurationMs: payload.candidate.duration_ms,
        note: payload.delta.span_count === 0 ? 'Span counts match' : 'Span counts differ'
      }
    ].map(mapCompareSpanDifference),
    errorDifferences: [
      {
        name: 'Failed dimensions',
        baselineStatus: payload.baseline.failed_dimensions.join(', ') || 'none',
        candidateStatus: payload.candidate.failed_dimensions.join(', ') || 'none',
        baselineDurationMs: null,
        candidateDurationMs: null,
        note: payload.baseline.failed_dimensions.join('|') === payload.candidate.failed_dimensions.join('|') ? 'Evaluation failures match' : 'Evaluation failures differ'
      }
    ].map(mapCompareSpanDifference)
  };
}

export async function getDashboardMetrics(fetchFn: typeof fetch): Promise<DashboardMetric[]> {
  const traces = await listTraceSummaries(fetchFn, { limit: 100 });
  const completed = traces.items.filter((trace) => trace.status !== 'running');
  const medianIndex = Math.floor(completed.length / 2);
  const sortedDurations = completed
    .map((trace) => trace.durationMs)
    .filter((duration): duration is number => duration !== null)
    .sort((left, right) => left - right);

  return [
    {
      label: 'Traces retained',
      value: String(traces.total),
      detail: traces.total === 1 ? 'Single captured trace' : 'Indexed local trace history'
    },
    {
      label: 'Median latency',
      value: sortedDurations[medianIndex] ? `${Math.round(sortedDurations[medianIndex])} ms` : demoMetrics[1].value,
      detail: completed.length ? 'Across completed trace runs' : demoMetrics[1].detail
    },
    {
      label: 'Errors on page',
      value: `${traces.items.filter((trace) => trace.status === 'error').length}`,
      detail: traces.items.length ? 'Visible traces with failures' : 'No traces captured yet'
    }
  ];
}

export { DEFAULT_TRACE_LIMIT, deriveTraceStatus };
