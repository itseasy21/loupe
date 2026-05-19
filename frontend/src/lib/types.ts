export type TraceStatus = 'success' | 'error' | 'running';

export interface TraceSummary {
  id: string;
  agent: string;
  title: string;
  status: TraceStatus;
  startedAt: string;
  endedAt: string | null;
  durationMs: number | null;
  spanCount: number;
}

export interface TraceListResponse {
  items: TraceSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface TraceSpan {
  span_id: string;
  parent_id: string | null;
  name: string;
  kind: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  attributes: Record<string, unknown>;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  events: Array<Record<string, unknown>>;
  error: string | null;
}

export interface TraceDetail {
  trace_id: string;
  name: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  metadata: Record<string, unknown>;
  spans: TraceSpan[];
}

export interface TraceLikelyCause {
  span_id: string;
  name: string;
  score: number;
  reasons: string[];
}

export interface TraceCausalNode {
  span_id: string;
  parent_id: string | null;
  name: string;
  kind: string;
  status: string;
}

export interface TraceCausalAnalysis {
  trace_id: string;
  name: string;
  nodes: TraceCausalNode[];
  edges: Record<string, string[]>;
  likely_causes: TraceLikelyCause[];
}

export interface TraceEvaluationDimension {
  passed: boolean;
  score: number;
  reason: string;
}

export interface TraceEvaluationSummary {
  trace_id: string;
  name: string;
  passed: boolean;
  score: number;
  reason: string;
  dimensions: Record<string, TraceEvaluationDimension>;
}

export interface CompareMetric {
  label: string;
  baseline: string;
  candidate: string;
  delta: string;
}

export interface CompareOutcome {
  label: string;
  baseline: string;
  candidate: string;
  changed: boolean;
}

export interface CompareValueDifference {
  key: string;
  baseline: string;
  candidate: string;
}

export interface CompareSpanDifference {
  name: string;
  baselineStatus: string | null;
  candidateStatus: string | null;
  baselineDurationMs: number | null;
  candidateDurationMs: number | null;
  note: string;
}

export interface TraceCompareSummary {
  trace_id: string;
  name: string;
  status: string;
  duration_ms: number | null;
  span_count: number;
  score: number;
  passed: boolean;
  failed_dimensions: string[];
}

export interface TraceComparePayload {
  baseline: TraceCompareSummary;
  candidate: TraceCompareSummary;
  delta: {
    score: number;
    span_count: number;
    duration_ms: number | null;
  };
  metrics: CompareMetric[];
  outcomes: CompareOutcome[];
  metadataDifferences: CompareValueDifference[];
  spanDifferences: CompareSpanDifference[];
  errorDifferences: CompareSpanDifference[];
}

export interface DashboardMetric {
  label: string;
  value: string;
  detail: string;
}

export interface NavLink {
  label: string;
  href: string;
  enabled: boolean;
}
