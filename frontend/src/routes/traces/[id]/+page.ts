import { error } from '@sveltejs/kit';

import { getTraceCausalAnalysis, getTraceDetail, getTraceEvaluationSummary } from '$lib';

import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, params }) => {
  const [trace, causalAnalysis, evaluationSummary] = await Promise.all([
    getTraceDetail(fetch, params.id),
    getTraceCausalAnalysis(fetch, params.id),
    getTraceEvaluationSummary(fetch, params.id)
  ]);

  if (!trace) {
    throw error(404, 'Trace not found');
  }

  return {
    trace,
    causalAnalysis,
    evaluationSummary
  };
};
