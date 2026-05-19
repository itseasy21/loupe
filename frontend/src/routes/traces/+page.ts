import { listTraceSummaries } from '$lib';

import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
  const search = url.searchParams.get('search') ?? '';
  const page = Math.max(Number(url.searchParams.get('page') ?? '1') || 1, 1);
  const limit = 12;
  const offset = (page - 1) * limit;
  const traces = await listTraceSummaries(fetch, { limit, offset, search });

  return {
    traces,
    search,
    page,
    pageCount: Math.max(Math.ceil(traces.total / traces.limit), 1)
  };
};
