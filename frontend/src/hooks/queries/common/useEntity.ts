/**
 * ============================================================================
 * Hela360 Enterprise Entity Query
 * ============================================================================
 *
 * Generic hook for retrieving a single entity.
 *
 * Responsibilities
 * ----------------
 * • Standardize entity retrieval
 * • Eliminate duplicated useQuery() boilerplate
 * • Preserve full TanStack Query flexibility
 * • Support query selection
 * • Support placeholder data
 * • Support initial data
 * • Support conditional execution
 * • Preserve strong typing
 *
 * This hook powers every entity "detail" query throughout Hela360.
 *
 * Examples
 * --------
 *
 * Product
 * -------
 *
 * const product = useEntity(
 *     QUERY_KEYS.products.detail(id),
 *     () => productService.findById(id),
 * );
 *
 * Customer
 * --------
 *
 * const customer = useEntity(
 *     QUERY_KEYS.customers.detail(id),
 *     () => customerService.findById(id),
 * );
 *
 * Supplier
 * --------
 *
 * const supplier = useEntity(
 *     QUERY_KEYS.suppliers.detail(id),
 *     () => supplierService.findById(id),
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
 * Types
 * ============================================================================
 */

/**
 * Query options accepted by useEntity().
 *
 * queryKey and queryFn are intentionally omitted because they are supplied
 * directly to the hook.
 */
export type UseEntityOptions<
  TQueryFnData,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> = Pick<
  Omit<
    UseQueryOptions<
      TQueryFnData,
      DefaultError,
      TData,
      TQueryKey
    >,
    "queryKey" | "queryFn"
  >,
  | "enabled"
  | "staleTime"
  | "gcTime"
  | "retry"
  | "refetchOnWindowFocus"
  | "refetchOnMount"
  | "refetchOnReconnect"
  | "select"
  | "placeholderData"
  | "initialData"
>;

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Retrieves a single entity.
 *
 * The hook intentionally contains no business logic and simply standardizes
 * the useQuery configuration used throughout the application.
 */
export function useEntity<
  TQueryFnData,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(
  queryKey: TQueryKey,

  queryFn: () => Promise<TQueryFnData>,

  options?: UseEntityOptions<
    TQueryFnData,
    TData,
    TQueryKey
  >,
): UseQueryResult<
  TData,
  DefaultError
> {
  return useQuery(
    createQueryOptions<
      TQueryFnData,
      TData,
      TQueryKey
    >(
      queryKey,
      queryFn,
      options,
    ),
  );
}

/* ============================================================================
 * Export
 * ============================================================================
 */

export default useEntity;
