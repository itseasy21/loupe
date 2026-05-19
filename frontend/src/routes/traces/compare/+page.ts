import { error } from '@sveltejs/kit';

import { getTraceCompare } from '$lib';

import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
  const left = url.searchParams.get('left')?.trim() ?? '';
  const right = url.searchParams.get('right')?.trim() ?? '';

  if (!left || !right) {
    throw error(400, 'Choose two trace ids to compare');
  }

  if (left === right) {
    return {
      comparison: null,
      left,
      right
    };
  }

  const comparison = await getTraceCompare(fetch, left, right);

  return {
    comparison,
    left,
    right
  };
};
