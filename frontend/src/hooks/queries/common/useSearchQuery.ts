/**
 * ============================================================================
 * Hela360 Enterprise Search Query
 * ============================================================================
 *
 * Generic hook for executing entity searches.
 *
 * Responsibilities
 * ----------------
 * • Standardize search queries
 * • Support search-driven interfaces
 * • Preserve full TanStack Query flexibility
 * • Eliminate duplicated search hooks
 *
 * This hook powers searchable dropdowns, lookup dialogs, autocomplete
 * components and global search throughout Hela360.
 *
 * Example
 * -------
 *
 * const products = useSearchQuery(
 *   QUERY_KEYS.products.search(searchTerm),
 *   () => productService.search(searchTerm),
 *   {
 *     enabled: searchTerm.length >= 2,
 *   },
 * );
 *
 * ============================================================================
 */

import {
  useQuery,
  type DefaultError,
  type QueryKey,
  type UseQueryOptions,
  type UseQueryResult,
} from "@tanstack/react-query";

import { createQueryOptions } from "@/lib/queryFactory";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Executes a search query.
 */
export function useSearchQuery<
  TResult,
  TData = TResult,
  TKey extends QueryKey = QueryKey,
>(
  queryKey: TKey,
  queryFn: () => Promise<TResult>,
  options?: Omit<
    UseQueryOptions<
      TResult,
      DefaultError,
      TData,
      TKey
    >,
    "queryKey" | "queryFn"
  >,
): UseQueryResult<
  TData,
  DefaultError
> {
  return useQuery(
    createQueryOptions<
      TResult,
      TData,
      TKey
    >(
      queryKey,
      queryFn,
      {
        enabled: true,
        ...options,
      },
    ),
  );
}

export default useSearchQuery;