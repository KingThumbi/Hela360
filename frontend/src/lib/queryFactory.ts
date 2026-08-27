/**
 * ============================================================================
 * Hela360 Enterprise Query Factory
 * ============================================================================
 *
 * Reusable builders for TanStack Query options.
 *
 * Responsibilities
 * ----------------
 * • Standardize query configuration
 * • Standardize mutation configuration
 * • Eliminate duplicated boilerplate
 * • Preserve full TanStack Query flexibility
 * • Provide strong typing
 *
 * Query hooks should build upon these helpers instead of manually repeating
 * queryFn, mutationFn and common options.
 *
 * ============================================================================
 */

import type {
  DefaultError,
  MutationFunction,
  QueryFunction,
  QueryKey,
  UseMutationOptions,
  UseQueryOptions,
} from "@tanstack/react-query";

/* ============================================================================
 * Query Builder
 * ============================================================================
 */

/**
 * Creates strongly typed query options.
 */
export function createQueryOptions<
  TQueryFnData,
  TData = TQueryFnData,
  TKey extends QueryKey = QueryKey,
>(
  queryKey: TKey,
  queryFn: QueryFunction<TQueryFnData, TKey>,
  options?: Omit<
    UseQueryOptions<
      TQueryFnData,
      DefaultError,
      TData,
      TKey
    >,
    "queryKey" | "queryFn"
  >,
): UseQueryOptions<
  TQueryFnData,
  DefaultError,
  TData,
  TKey
> {
  return {
    queryKey,
    queryFn,
    ...options,
  };
}

/* ============================================================================
 * Mutation Builder
 * ============================================================================
 */

/**
 * Creates strongly typed mutation options.
 */
export function createMutationOptions<
  TData,
  TVariables = void,
  TOnMutateResult = unknown,
>(
  mutationFn: MutationFunction<
    TData,
    TVariables
  >,
  options?: Omit<
    UseMutationOptions<
      TData,
      DefaultError,
      TVariables,
      TOnMutateResult
    >,
    "mutationFn"
  >,
): UseMutationOptions<
  TData,
  DefaultError,
  TVariables,
  TOnMutateResult
> {
  return {
    mutationFn,
    ...options,
  };
}

/* ============================================================================
 * Infinite Query Builder
 * ============================================================================
 */

/**
 * Shared configuration for infinite queries.
 */
export function createInfiniteQueryOptions<
  TQueryFnData,
  TKey extends QueryKey = QueryKey,
>(
  queryKey: TKey,
  queryFn: QueryFunction<TQueryFnData, TKey>,
  options?: Record<string, unknown>,
) {
  return {
    queryKey,
    queryFn,
    ...options,
  };
}

/* ============================================================================
 * Utility
 * ============================================================================
 */

/**
 * Creates a disabled query.
 */
export function createDisabledQuery<
  TQueryFnData,
  TData = TQueryFnData,
  TKey extends QueryKey = QueryKey,
>(
  queryKey: TKey,
  queryFn: QueryFunction<TQueryFnData, TKey>,
): UseQueryOptions<
  TQueryFnData,
  DefaultError,
  TData,
  TKey
> {
  return {
    queryKey,
    queryFn,
    enabled: false,
  };
}
