/**
 * ============================================================================
 * Hela360 Enterprise Entity List Query
 * ============================================================================
 *
 * Generic hook for retrieving entity collections.
 *
 * Responsibilities
 * ----------------
 * • Standardize collection queries
 * • Eliminate duplicated useQuery() implementations
 * • Support filtering
 * • Support searching
 * • Support sorting
 * • Support pagination
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers all entity list pages throughout the application.
 *
 * Example
 * -------
 *
 * const products = useEntityList(
 *   QUERY_KEYS.products.list(),
 *   () => productService.findAll(),
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
 * Retrieves an entity collection.
 */
export function useEntityList<
  TEntity,
  TData = TEntity[],
  TKey extends QueryKey = QueryKey,
>(
  queryKey: TKey,
  queryFn: () => Promise<TEntity[]>,
  options?: Omit<
    UseQueryOptions<
      TEntity[],
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
      TEntity[],
      TData,
      TKey
    >(
      queryKey,
      queryFn,
      options,
    ),
  );
}

export default useEntityList;