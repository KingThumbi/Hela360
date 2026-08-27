/**
 * ============================================================================
 * Hela360 Enterprise Create Entity Mutation
 * ============================================================================
 *
 * Generic mutation hook for creating entities.
 *
 * Responsibilities
 * ----------------
 * • Standardize create mutations
 * • Eliminate duplicated mutation logic
 * • Support cache invalidation
 * • Preserve full TanStack Query flexibility
 * • Support optimistic workflows
 *
 * This hook powers every create operation throughout Hela360.
 *
 * Example
 * -------
 *
 * const createProduct = useCreateEntity(
 *   (payload) => productService.create(payload),
 *   invalidateProducts,
 * );
 *
 * ============================================================================
 */

import {
  useMutation,
  useQueryClient,
  type DefaultError,
  type UseMutationOptions,
  type UseMutationResult,
  type QueryClient,
} from "@tanstack/react-query";

import { createMutationOptions } from "@/lib/queryFactory";

/* ============================================================================
 * Types
 * ============================================================================
 */

export type InvalidateCallback = (
  queryClient: QueryClient,
) => Promise<void> | void;

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Generic create mutation.
 */
export function useCreateEntity<
  TResult,
  TCreate,
  TOnMutateResult = unknown,
>(
  mutationFn: (
    payload: TCreate,
  ) => Promise<TResult>,

  invalidate?: InvalidateCallback,

  options?: Omit<
    UseMutationOptions<
      TResult,
      DefaultError,
      TCreate,
      TOnMutateResult
    >,
    "mutationFn"
  >,
): UseMutationResult<
  TResult,
  DefaultError,
  TCreate,
  TOnMutateResult
> {
  const queryClient = useQueryClient();

  return useMutation(
    createMutationOptions<
      TResult,
      TCreate,
      TOnMutateResult
    >(
      mutationFn,
      {
        ...options,

        onSuccess: async (
          data,
          variables,
          onMutateResult,
          context,
        ) => {
          if (invalidate) {
            await invalidate(queryClient);
          }

          await options?.onSuccess?.(
            data,
            variables,
            onMutateResult,
            context,
          );
        },
      },
    ),
  );
}

export default useCreateEntity;
