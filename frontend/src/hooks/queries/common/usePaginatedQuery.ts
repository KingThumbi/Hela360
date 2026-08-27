/**
 * ============================================================================
 * Hela360 Enterprise Paginated Query
 * ============================================================================
 *
 * Generic hook for retrieving paginated resources.
 *
 * Responsibilities
 * ----------------
 * • Standardize paginated queries
 * • Support server-side pagination
 * • Support searching
 * • Support filtering
 * • Support sorting
 * • Preserve previous page data
 * • Preserve full TanStack Query flexibility
 *
 * This hook powers every paginated data table throughout Hela360.
 *
 * Example
 * -------
 *
 * const products = usePaginatedQuery(
 *   QUERY_KEYS.products.list(params),
 *   () => productService.paginate(params),
 * );
 *
 * ============================================================================
 */

import {
  useQuery,
  keepPreviousData,
  type DefaultError,
  type QueryKey,
  type UseQueryOptions,
  type UseQueryResult,
} from "@tanstack/react-query";

import { createQueryOptions } from "@/lib/queryFactory";

import type {
  PaginatedResponse,
} from "@/types/api";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a paginated collection.
 */
export function usePaginatedQuery<
  TEntity,
  TData = PaginatedResponse<TEntity>,
  TKey extends QueryKey = QueryKey,
>(
  queryKey: TKey,
  queryFn: () => Promise<
    PaginatedResponse<TEntity>
  >,
  options?: Omit<
    UseQueryOptions<
      PaginatedResponse<TEntity>,
      DefaultError,
      TData,
      TKey
    >,
    | "queryKey"
    | "queryFn"
    | "placeholderData"
  >,
): UseQueryResult<
  TData,
  DefaultError
> {
  return useQuery(
    createQueryOptions<
      PaginatedResponse<TEntity>,
      TData,
      TKey
    >(
      queryKey,
      queryFn,
      {
        placeholderData:
          keepPreviousData,

        ...options,
      },
    ),
  );
}

export default usePaginatedQuery;