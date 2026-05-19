import { getDashboardMetrics, listTraceSummaries } from '$lib';

export async function load({ fetch }) {
  const [metrics, traceResponse] = await Promise.all([
    getDashboardMetrics(fetch),
    listTraceSummaries(fetch, { limit: 3 })
  ]);

  return {
    metrics,
    traces: traceResponse.items
  };
}
